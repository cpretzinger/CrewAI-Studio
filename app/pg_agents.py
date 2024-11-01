# pg_agents.py

import streamlit as st
from streamlit import session_state as ss
import db_utils  # Import database utility functions
from agentops import record_action, record, ActionEvent

from my_agent import MyAgent  # Ensure MyAgent is imported correctly


class PageAgents:
    def __init__(self):
        self.name = "Agents"

    def load_agents(self):
        """Load agents from the database into session state."""
        ss.agents = db_utils.load_agents()  # Ensure this loads a list of MyAgent instances

    def save_agent(self, agent: MyAgent):
        """Save an agent to the database."""
        db_utils.save_agent(agent)

    @record_action('Creating Agent in Database')
    def create_agent(self, crew=None):
        """
        Create a new agent and optionally assign it to a crew.

        Args:
            crew (MyCrew, optional): The crew to assign the agent to.
        """
        # Log agent creation action manually
        record(ActionEvent("agent_creation_requested"))

        # Create a new agent and save to DB
        agent = MyAgent()
        if 'agents' not in ss:
            self.load_agents()  # Load existing agents from the database if not in session
        ss.agents.append(agent)
        agent.edit = True
        self.save_agent(agent)  # Save agent to database

        # Optional: Link agent to crew and save to DB
        if crew:
            crew.agents.append(agent)
            db_utils.save_crew(crew)

        return agent

    @record_action('Loading Agents from Database')
    def draw(self):
        """Render the Agents page with tabs for All, Unassigned, and Crew-specific agents."""
        # Log viewing of the agent list
        record(ActionEvent("user_viewed_agent_list"))

        with st.container():
            st.subheader(self.name)
            editing = False
            if 'agents' not in ss:
                self.load_agents()  # Load agents from database if not in session
            if 'crews' not in ss:
                ss.crews = db_utils.load_crews()  # Load crews if applicable

            agent_assignment = {agent.id: [] for agent in ss.agents}

            # Assign agents to crews
            for crew in ss.crews:
                for agent in crew.agents:
                    agent_assignment[agent.id].append(crew.name)

            tabs = ["All Agents", "Unassigned Agents"] + [crew.name for crew in ss.crews]
            tab_objects = st.tabs(tabs)

            with tab_objects[0]:  # All Agents tab
                st.markdown("#### All Agents")
                for agent in ss.agents:
                    agent.draw()
                    if agent.edit:
                        editing = True
                st.button(
                    'Create Agent',
                    on_click=self.create_agent,
                    disabled=editing,
                    key='pg_agents_create_agent_button'
                )

            with tab_objects[1]:  # Unassigned Agents tab
                unassigned_agents = [agent for agent in ss.agents if not agent_assignment[agent.id]]
                st.markdown("#### Unassigned Agents")
                for agent in unassigned_agents:
                    unique_key = f"{agent.id}_unassigned"
                    agent.draw(key=unique_key)
                    if agent.edit:
                        editing = True
                st.button(
                    'Create Agent',
                    on_click=self.create_agent,
                    disabled=editing,
                    key='pg_agents_create_agent_unassigned_button'
                )

            for i, crew in enumerate(ss.crews, start=2):
                with tab_objects[i]:  # Crew-specific tabs
                    st.markdown(f"#### {crew.name}")
                    for agent in crew.agents:
                        unique_key = f"{agent.id}_{crew.name}"
                        agent.draw(key=unique_key)
                        if agent.edit:
                            editing = True
                    st.button(
                        'Create Agent',
                        on_click=self.create_agent,
                        disabled=editing,
                        key=f'pg_agents_create_agent_{crew.id}_button',
                        kwargs={'crew': crew}
                    )

            if not ss.agents:
                st.write("No agents defined yet.")
                st.button(
                    'Create Agent',
                    on_click=self.create_agent,
                    disabled=editing,
                    key='pg_agents_create_agent_no_agents_button'
                )