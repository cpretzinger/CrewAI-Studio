# my_crew.py

from crewai import Crew
import streamlit as st
from streamlit import session_state as ss
from utils import fix_columns_width
from core_utils import rnd_id
from datetime import datetime
from typing import Optional, List, Dict, Any
import db_utils

class MyCrew:
    def __init__(
        self, 
        id: Optional[str] = None, 
        name: Optional[str] = None, 
        description: Optional[str] = None, 
        goal: Optional[str] = None, 
        agents: Optional[List['MyAgent']] = None, 
        tasks: Optional[List['MyTask']] = None, 
        created_at: Optional[str] = None, 
        **kwargs
    ):
        self.id = id or "C_" + rnd_id()
        self.name = name or "Research Crew"
        self.description = description or "A crew focused on researching and analyzing AI trends."
        self.goal = goal or "Identify and analyze emerging AI trends and their potential impact."
        self.agents = agents or []
        self.tasks = tasks or []
        self.created_at = created_at or datetime.now().isoformat()
        self.edit_key = f'edit_{self.id}'
        if self.edit_key not in ss:
            ss[self.edit_key] = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MyCrew':
        from my_agent import MyAgent  # Import here to avoid circular imports
        from my_task import MyTask  # Import here to avoid circular imports
        agents = [MyAgent.from_dict(agent_data) for agent_data in data.get('agents', [])]
        tasks = [MyTask.from_dict(task_data) for task_data in data.get('tasks', [])]
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            goal=data.get('goal'),
            agents=agents,
            tasks=tasks,
            created_at=data.get('created_at')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal": self.goal,
            "agents": [agent.to_dict() for agent in self.agents],
            "tasks": [task.to_dict() for task in self.tasks],
            "created_at": self.created_at
        }

    @property
    def edit(self):
        return ss[self.edit_key]

    @edit.setter
    def edit(self, value):
        ss[self.edit_key] = value

    def get_crewai_crew(self) -> Crew:
        agents = [agent.get_crewai_agent() for agent in self.agents]
        tasks = [task.get_crewai_task() for task in self.tasks]
        return Crew(
            agents=agents,
            tasks=tasks,
            verbose=True
        )

    def delete(self):
        ss.crews = [crew for crew in ss.crews if crew.id != self.id]
        db_utils.delete_crew(self.id)

    def is_valid(self, show_warning: bool = False) -> bool:
        if not self.agents:
            if show_warning:
                st.warning(f"Crew {self.name} has no agents")
            return False
        if not self.tasks:
            if show_warning:
                st.warning(f"Crew {self.name} has no tasks")
            return False
        for agent in self.agents:
            if not agent.is_valid(show_warning):
                return False
        for task in self.tasks:
            if not task.is_valid(show_warning):
                return False
        return True

    def draw(self, key: Optional[str] = None):
        expander_title = f"{self.name}" if self.is_valid() else f"❗ {self.name}"
        if self.edit:
            with st.expander(expander_title, expanded=True):
                with st.form(key=f'form_{self.id}' if key is None else key):
                    self.name = st.text_input("Name", value=self.name)
                    self.description = st.text_area("Description", value=self.description)
                    self.goal = st.text_area("Goal", value=self.goal)
                    self.agents = st.multiselect(
                        "Agents",
                        options=ss.agents,
                        default=self.agents,
                        format_func=lambda x: x.role
                    )
                    self.tasks = st.multiselect(
                        "Tasks",
                        options=ss.tasks,
                        default=self.tasks,
                        format_func=lambda x: x.description[:120]
                    )
                    submitted = st.form_submit_button("Save")
                    if submitted:
                        self.set_editable(False)
        else:
            fix_columns_width()
            with st.expander(expander_title):
                st.markdown(f"**Name:** {self.name}")
                st.markdown(f"**Description:** {self.description}")
                st.markdown(f"**Goal:** {self.goal}")
                st.markdown(f"**Agents:** {[agent.role for agent in self.agents]}")
                st.markdown(f"**Tasks:** {[task.description[:120] for task in self.tasks]}")

                col1, col2 = st.columns(2)
                with col1:
                    st.button("Edit", on_click=self.set_editable, args=(True,), key=rnd_id())
                with col2:
                    st.button("Delete", on_click=self.delete, key=rnd_id())
                self.is_valid(show_warning=True)

    def set_editable(self, edit: bool):
        self.edit = edit
        db_utils.save_crew(self)
        if not edit:
            st.rerun()
