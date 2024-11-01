# pg_crews.py

import streamlit as st
from streamlit import session_state as ss  # Ensure session_state is imported
import db_utils  # Import database utility functions as needed
from agentops import record_action, record, ActionEvent

from my_crew import MyCrew  # Ensure MyCrew is imported correctly


class PageCrews:
    def __init__(self):
        self.name = "Crews"

    def load_crews(self):
        """Load crews from the database into session state."""
        ss.crews = db_utils.load_crews()  # Ensure this loads a list of MyCrew instances

    def save_crew(self, crew: MyCrew):
        """Save a crew to the database."""
        db_utils.save_crew(crew)

    @record_action('Creating Crew in Database')
    def create_crew(self):
        """
        Create a new crew and save it to the database.

        Returns:
            MyCrew: The newly created crew instance.
        """
        # Log crew creation action manually
        record(ActionEvent("crew_creation_requested"))

        # Create a new crew and save to DB
        crew = MyCrew()
        if 'crews' not in ss:
            self.load_crews()  # Load existing crews from the database if not in session
        ss.crews.append(crew)
        crew.edit = True
        self.save_crew(crew)  # Save crew to database

        return crew

    @record_action('Loading Crews from Database')
    def draw(self):
        """
        Render the Crews page with options to view and create crews.
        """
        # Log viewing of the crews list
        record(ActionEvent("user_viewed_crews_list"))

        with st.container():
            st.subheader(self.name)
            editing = False
            if 'crews' not in ss:
                self.load_crews()  # Load crews from database if not in session

            if not ss.crews:
                st.warning("No crews defined yet.")
                if st.button('Create Crew', on_click=self.create_crew, key='pg_crews_create_crew_button'):
                    st.experimental_rerun()
                return

            # Create tabs for each crew and an additional tab for creating new crews
            crew_names = [crew.name for crew in ss.crews]
            tabs = ["All Crews"] + crew_names
            tab_objects = st.tabs(tabs)

            with tab_objects[0]:  # All Crews tab
                st.markdown("#### All Crews")
                for crew in ss.crews:
                    crew.draw()
                    if crew.edit:
                        editing = True
                st.button(
                    'Create Crew',
                    on_click=self.create_crew,
                    disabled=editing,
                    key='pg_crews_create_crew_all_crews_button'
                )

            # Crew-specific tabs
            for i, crew in enumerate(ss.crews, start=1):
                with tab_objects[i]:
                    st.markdown(f"#### {crew.name}")
                    crew.draw()
                    if crew.edit:
                        editing = True
                    st.button(
                        'Create Crew',
                        on_click=self.create_crew,
                        disabled=editing,
                        key=f'pg_crews_create_crew_{crew.crew_id}_button'
                    )

    def handle_create_crew(self):
        """
        Handle the creation of a new crew and refresh the page.
        """
        self.create_crew()
        st.experimental_rerun()