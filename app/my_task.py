# my_task.py

from crewai import Task
import streamlit as st
from streamlit import session_state as ss
from utils import fix_columns_width
from core_utils import rnd_id
from datetime import datetime
from typing import Optional, List, Dict, Any
import db_utils

class MyTask:
    def __init__(
        self, 
        id: Optional[str] = None, 
        description: Optional[str] = None, 
        expected_output: Optional[str] = None, 
        agent: Optional['MyAgent'] = None, 
        async_execution: Optional[bool] = False, 
        created_at: Optional[str] = None, 
        context_from_async_tasks_ids: Optional[List[str]] = None, 
        context_from_sync_tasks_ids: Optional[List[str]] = None, 
        **kwargs
    ):
        self.id = id or "T_" + rnd_id()
        self.description = description or "Identify the next big trend in AI. Focus on identifying pros and cons and the overall narrative."
        self.expected_output = expected_output or "A comprehensive 3 paragraphs long report on the latest AI trends."
        self.agent = agent or ss.agents[0] if ss.agents else None
        self.async_execution = async_execution or False
        self.context_from_async_tasks_ids = context_from_async_tasks_ids or []
        self.context_from_sync_tasks_ids = context_from_sync_tasks_ids or []
        self.created_at = created_at or datetime.now().isoformat()
        self.edit_key = f'edit_{self.id}'
        if self.edit_key not in ss:
            ss[self.edit_key] = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MyTask':
        from my_agent import MyAgent  # Import here to avoid circular imports
        agent = MyAgent.from_dict(data['agent']) if data.get('agent') else None
        return cls(
            id=data.get('id'),
            description=data.get('description'),
            expected_output=data.get('expected_output'),
            agent=agent,
            async_execution=data.get('async_execution', False),
            context_from_async_tasks_ids=data.get('context_from_async_tasks_ids', []),
            context_from_sync_tasks_ids=data.get('context_from_sync_tasks_ids', []),
            created_at=data.get('created_at')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "expected_output": self.expected_output,
            "agent": self.agent.to_dict() if self.agent else None,
            "async_execution": self.async_execution,
            "context_from_async_tasks_ids": self.context_from_async_tasks_ids,
            "context_from_sync_tasks_ids": self.context_from_sync_tasks_ids,
            "created_at": self.created_at
        }

    @property
    def edit(self):
        return ss[self.edit_key]

    @edit.setter
    def edit(self, value):
        ss[self.edit_key] = value

    def get_crewai_task(self, context_from_async_tasks: Optional[List[Task]] = None, context_from_sync_tasks: Optional[List[Task]] = None) -> Task:
        context = []
        if context_from_async_tasks:
            context.extend(context_from_async_tasks)
        if context_from_sync_tasks:
            context.extend(context_from_sync_tasks)
        
        if context:
            return Task(
                description=self.description, 
                expected_output=self.expected_output, 
                async_execution=self.async_execution, 
                agent=self.agent.get_crewai_agent() if self.agent else None, 
                context=context
            )
        else:
            return Task(
                description=self.description, 
                expected_output=self.expected_output, 
                async_execution=self.async_execution, 
                agent=self.agent.get_crewai_agent() if self.agent else None
            )

    def delete(self):
        ss.tasks = [task for task in ss.tasks if task.id != self.id]
        db_utils.delete_task(self.id)

    def is_valid(self, show_warning: bool = False) -> bool:
        if not self.agent:
            if show_warning:
                st.warning(f"Task {self.description} has no agent")
            return False
        if not self.agent.is_valid(show_warning):
            return False
        return True

    def draw(self, key: Optional[str] = None):
        agent_options = [agent.role for agent in ss.agents]
        expander_title = (
            f"({self.agent.role if self.agent else 'unassigned'}) - {self.description}" 
            if self.is_valid() 
            else f"❗ ({self.agent.role if self.agent else 'unassigned'}) - {self.description}"
        )
        if self.edit:
            with st.expander(expander_title, expanded=True):
                with st.form(key=f'form_{self.id}' if key is None else key):
                    self.description = st.text_area("Description", value=self.description)
                    self.expected_output = st.text_area("Expected output", value=self.expected_output)
                    self.agent = st.selectbox(
                        "Agent", 
                        options=ss.agents, 
                        format_func=lambda x: x.role, 
                        index=0 if self.agent is None else agent_options.index(self.agent.role)
                    )
                    self.async_execution = st.checkbox("Async execution", value=self.async_execution)
                    self.context_from_async_tasks_ids = st.multiselect(
                        "Context from async tasks", 
                        options=[task.id for task in ss.tasks if task.async_execution], 
                        default=self.context_from_async_tasks_ids, 
                        format_func=lambda x: [task.description[:120] for task in ss.tasks if task.id == x][0]
                    )
                    self.context_from_sync_tasks_ids = st.multiselect(
                        "Context from sync tasks", 
                        options=[task.id for task in ss.tasks if not task.async_execution], 
                        default=self.context_from_sync_tasks_ids, 
                        format_func=lambda x: [task.description[:120] for task in ss.tasks if task.id == x][0]
                    )
                    submitted = st.form_submit_button("Save")
                    if submitted:
                        self.set_editable(False)
        else:
            fix_columns_width()
            with st.expander(expander_title):
                st.markdown(f"**Description:** {self.description}")
                st.markdown(f"**Expected output:** {self.expected_output}")
                st.markdown(f"**Agent:** {self.agent.role if self.agent else 'None'}")
                st.markdown(f"**Async execution:** {self.async_execution}")
                st.markdown(
                    f"**Context from async tasks:** {', '.join([task.description[:120] for task in ss.tasks if task.id in self.context_from_async_tasks_ids]) if self.context_from_async_tasks_ids else 'None'}"
                )
                st.markdown(
                    f"**Context from sync tasks:** {', '.join([task.description[:120] for task in ss.tasks if task.id in self.context_from_sync_tasks_ids]) if self.context_from_sync_tasks_ids else 'None'}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Edit", on_click=self.set_editable, args=(True,), key=rnd_id())
                with col2:
                    st.button("Delete", on_click=self.delete, key=rnd_id())
                self.is_valid(show_warning=True)

    def set_editable(self, edit: bool):
        self.edit = edit
        db_utils.save_task(self)
        if not edit:
            st.rerun()
