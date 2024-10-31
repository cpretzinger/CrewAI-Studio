import streamlit as st
from streamlit import session_state as ss
from my_agent import MyAgent
import db_utils  # Import your database utility functions
from agentops import record_action, record, ActionEvent
class PageAgents:
    def __init__(self):
        self.name = "Agents"

    @record_action('Creating Agent in Database')
    def create_agent(self, crew=None):
        # Log agent creation action manually
        record(ActionEvent("agent_creation_requested"))
        
        # Create a new agent and save to DB
        agent = MyAgent()
        if 'agents' not in ss:
            ss.agents = db_utils.load_agents()  # Load existing agents from the database
        ss.agents.append(agent)
        agent.edit = True
        db_utils.save_agent(agent)  # Save agent to database

        # Optional: Link agent to crew and save to DB
        if crew:
            crew.agents.append(agent)
            db_utils.save_crew(crew)

        return agent
    
    @record_action('Loading Agents from Database')
    def draw(self):
        # Log viewing of the agent list
        record(ActionEvent("user_viewed_agent_list"))
        
        with st.container():
            st.subheader(self.name)
            editing = False
            if 'agents' not in ss:
                ss.agents = db_utils.load_agents()  # Load agents from database at start
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
                st.button('Create agent', on_click=self.create_agent, disabled=editing)

            with tab_objects[1]:  # Unassigned Agents tab
                unassigned_agents = [agent for agent in ss.agents if not agent_assignment[agent.id]]
                for agent in unassigned_agents:
                    unique_key = f"{agent.id}_unassigned"
                    agent.draw(key=unique_key)
                    if agent.edit:
                        editing = True
                st.button('Create agent', on_click=self.create_agent, disabled=editing)

            for i, crew in enumerate(ss.crews, 2):
                with tab_objects[i]:  # Crew-specific tabs
                    st.markdown(f"#### {crew.name}")
                    for agent in crew.agents:
                        unique_key = f"{agent.id}_{crew.name}"
                        agent.draw(key=unique_key)
                        if agent.edit:
                            editing = True
                    st.button('Create agent', on_click=self.create_agent, disabled=editing, kwargs={'crew': crew})

            if not ss.agents:
                st.write("No agents defined yet.")
                st.button('Create agent', on_click=self.create_agent, disabled=editing)
