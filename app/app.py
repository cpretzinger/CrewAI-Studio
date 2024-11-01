import os
from dotenv import load_dotenv
from zep_python.client import Zep
import streamlit as st
from streamlit import session_state as ss
import agentops
import db_utils
from pg_export_crew import PageExportCrew
from pg_crews import PageCrews

# Load environment variables
load_dotenv()

def setup_zep_collection():
    client = Zep(api_key=os.getenv('ZEP_API_KEY'), base_url=os.getenv('ZEP_BASE_URL'))
    collection_name = "crewai_agents"

    try:
        # Check if the collection exists
        existing_collections = client.list_collections()
        if collection_name not in [col['name'] for col in existing_collections]:
            # If not, create the collection
            client.add_collection(
                name=collection_name,
                description="Collection for CrewAI agents",
                metadata={"project": "CrewAI"}
            )
            print(f"Collection '{collection_name}' created successfully.")
        else:
            print(f"Collection '{collection_name}' already exists.")
    except Exception as e:
        print(f"Error accessing Zep collections: {e}")

# Set up Zep collection
setup_zep_collection()

def main():
    from pg_crew_run import PageCrewRun
    st.set_page_config(page_title="AgencyHiveAI", page_icon="img/favicon.ico", layout="wide")
    load_data() 
    # Initialize AgentOps
    agentops.init(api_key=os.getenv('AGENTOPS_API_KEY'), auto_start_session=True)

    # Initialize database and load session data
    db_utils.initialize_db()
    load_data()
    draw_sidebar()
    PageCrewRun.maintain_session_state()
    pages()[ss.page].draw()

def pages():
    from pg_crew_run import PageCrewRun
    from pg_agents import PageAgents
    from pg_tasks import PageTasks
    from pg_crews import PageCrews
    from pg_tools import PageTools
    from pg_export_crew import PageExportCrew
    return {
        'Crews': PageCrews(),
        'Tools': PageTools(),
        'Agents': PageAgents(),
        'Tasks': PageTasks(),
        'Kickoff!': PageCrewRun(),
        'Import/export': PageExportCrew()
    }

def load_data():
    ss['agents'] = db_utils.load_agents()
    ss['tasks'] = db_utils.load_tasks()
    ss['crews'] = db_utils.load_crews()
    ss['tools'] = db_utils.load_tools()
    ss['enabled_tools'] = db_utils.load_tools_state()
    ss['crew_run'] = db_utils.load_crew_run()

def draw_sidebar():
    with st.sidebar:
        st.image("img/crewai_logo.png")
        if 'page' not in ss:
            ss.page = 'Crews'
            
        selected_page = st.radio(
            'Page',
            list(pages().keys()),
            index=list(pages().keys()).index(ss.page),
            label_visibility="collapsed")
        if selected_page != ss.page:
            
            ss.page = selected_page
            st.rerun()

if __name__ == '__main__':
    main()
