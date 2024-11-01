# my_agent.py

from crewai import Agent
import streamlit as st
from utils import fix_columns_width
from core_utils import rnd_id
from streamlit import session_state as ss
import db_utils
from llms import llm_providers_and_models, create_llm
from datetime import datetime
import agentops
from agentops import track_agent, record_tool, record_action, record, ActionEvent
import os
from dotenv import load_dotenv
from my_tools import MyTool 
from zep_python.client import Zep
from typing import Optional, List, Dict, Any

load_dotenv()

@track_agent(name="CrewAI_Agent")
class MyAgent:
    def __init__(
        self, 
        id: Optional[str] = None, 
        role: Optional[str] = None, 
        backstory: Optional[str] = None, 
        goal: Optional[str] = None, 
        temperature: Optional[float] = None, 
        allow_delegation: bool = False, 
        verbose: bool = False, 
        cache: Optional[bool] = None, 
        llm_provider_model: Optional[str] = None, 
        max_iter: Optional[int] = None, 
        created_at: Optional[str] = None, 
        tools: Optional[List[MyTool]] = None
    ):
        self.client = Zep(
            api_key=os.getenv('ZEP_API_KEY'),
            base_url=os.getenv('ZEP_BASE_URL'),
        )
        self.id = id or "A_" + rnd_id()
        self.role = role or "Senior Researcher"
        self.backstory = backstory or "Driven by curiosity, you're at the forefront of innovation, eager to explore and share knowledge that could change the world."
        self.goal = goal or "Uncover groundbreaking technologies in AI"
        self.temperature = temperature or 0.1
        self.allow_delegation = allow_delegation
        self.verbose = verbose
        self.llm_provider_model = llm_providers_and_models()[0] if llm_provider_model is None else llm_provider_model
        self.created_at = created_at or datetime.now().isoformat()
        self.tools = tools or []
        self.max_iter = max_iter or 25
        self.cache = cache if cache is not None else True
        self.edit_key = f'edit_{self.id}'
        self.collection = self.client.memory
        if self.edit_key not in ss:
            ss[self.edit_key] = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MyAgent':
        return cls(
            id=data.get('id'),
            role=data.get('role'),
            backstory=data.get('backstory'),
            goal=data.get('goal'),
            temperature=data.get('temperature'),
            allow_delegation=data.get('allow_delegation', False),
            verbose=data.get('verbose', False),
            cache=data.get('cache', True),
            llm_provider_model=data.get('llm_provider_model'),
            max_iter=data.get('max_iter', 25),
            created_at=data.get('created_at'),
            tools=[MyTool.from_dict(tool) for tool in data.get('tools', [])]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "backstory": self.backstory,
            "goal": self.goal,
            "temperature": self.temperature,
            "allow_delegation": self.allow_delegation,
            "verbose": self.verbose,
            "cache": self.cache,
            "llm_provider_model": self.llm_provider_model,
            "max_iter": self.max_iter,
            "created_at": self.created_at,
            "tools": [tool.to_dict() for tool in self.tools]
        }

    @property
    def edit(self):
        return ss[self.edit_key]

    @edit.setter
    def edit(self, value):
        ss[self.edit_key] = value

    @record_action("get_crewai_agent")
    def get_crewai_agent(self) -> Agent:
        llm = create_llm(self.llm_provider_model, temperature=self.temperature)
        tools = [tool.create_tool() for tool in self.tools]
        return Agent(
            role=self.role,
            backstory=self.backstory,
            goal=self.goal,
            allow_delegation=self.allow_delegation,
            verbose=self.verbose,
            max_iter=self.max_iter,
            cache=self.cache,
            tools=tools,
            llm=llm
        )

    @record_action("delete_agent")
    def delete(self):
        ss.agents = [agent for agent in ss.agents if agent.id != self.id]
        db_utils.delete_agent(self.id)

    @record_tool("validate_tool")
    def get_tool_display_name(self, tool: MyTool) -> str:
        first_param_name = tool.get_parameter_names()[0] if tool.get_parameter_names() else None
        first_param_value = tool.parameters.get(first_param_name, '') if first_param_name else ''
        return f"{tool.name} ({first_param_value if first_param_value else tool.tool_id})"

    @record_action("validate_agent")
    def is_valid(self, show_warning: bool = False) -> bool:
        for tool in self.tools:
            if not tool.is_valid(show_warning=show_warning):
                if show_warning:
                    st.warning(f"Tool {tool.name} is not valid")
                return False
        return True

    def validate_llm_provider_model(self):
        available_models = llm_providers_and_models()
        if self.llm_provider_model not in available_models:
            self.llm_provider_model = available_models[0]

    def draw(self, key: Optional[str] = None):
        self.validate_llm_provider_model()
        try:
            model_suffix = self.llm_provider_model.split(':')[1]
        except IndexError:
            model_suffix = self.llm_provider_model
        expander_title = f"{self.role[:60]} - {model_suffix}" if self.is_valid() else f"❗ {self.role[:20]} - {model_suffix}"
        if self.edit:
            with st.expander(f"Agent: {self.role}", expanded=True):
                with st.form(key=f'form_{self.id}' if key is None else key):
                    self.role = st.text_input("Role", value=self.role)
                    self.backstory = st.text_area("Backstory", value=self.backstory)
                    self.goal = st.text_area("Goal", value=self.goal)
                    self.allow_delegation = st.checkbox("Allow delegation", value=self.allow_delegation)
                    self.verbose = st.checkbox("Verbose", value=self.verbose)
                    self.cache = st.checkbox("Cache", value=self.cache)
                    self.llm_provider_model = st.selectbox(
                        "LLM Provider and Model", 
                        options=llm_providers_and_models(), 
                        index=llm_providers_and_models().index(self.llm_provider_model)
                    )
                    self.temperature = st.slider("Temperature", value=self.temperature, min_value=0.0, max_value=1.0)
                    self.max_iter = st.number_input("Max Iterations", value=self.max_iter, min_value=1, max_value=100)
                    enabled_tools = ss.tools
                    selected_tools = st.multiselect(
                        "Select Tools",
                        [self.get_tool_display_name(tool) for tool in enabled_tools],
                        default=[self.get_tool_display_name(tool) for tool in self.tools],
                        key=f"{self.id}_tools{key}"
                    )
                    submitted = st.form_submit_button("Save")
                    if submitted:
                        self.tools = [tool for tool in enabled_tools if self.get_tool_display_name(tool) in selected_tools]
                        self.set_editable(False)
        else:
            fix_columns_width()
            with st.expander(expander_title, expanded=False):
                st.markdown(f"**Role:** {self.role}")
                st.markdown(f"**Backstory:** {self.backstory}")
                st.markdown(f"**Goal:** {self.goal}")
                st.markdown(f"**Allow delegation:** {self.allow_delegation}")
                st.markdown(f"**Verbose:** {self.verbose}")
                st.markdown(f"**Cache:** {self.cache}")
                st.markdown(f"**LLM Provider and Model:** {self.llm_provider_model}")
                st.markdown(f"**Temperature:** {self.temperature}")
                st.markdown(f"**Max Iterations:** {self.max_iter}")
                st.markdown(f"**Tools:** {[self.get_tool_display_name(tool) for tool in self.tools]}")

                self.is_valid(show_warning=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.button("Edit", on_click=self.set_editable, args=(True,), key=rnd_id())
                with col2:
                    st.button("Delete", on_click=self.delete, key=rnd_id())

    def set_editable(self, edit: bool):
        self.edit = edit
        db_utils.save_agent(self)
        if not edit:
            st.rerun()

    def process_user_input(self, input_data: Any):
        record(ActionEvent("received_user_input"))
