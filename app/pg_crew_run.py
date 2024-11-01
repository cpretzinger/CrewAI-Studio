# pg_crew_run.py

import re
import streamlit as st
from streamlit import session_state as ss
import threading
import queue
import time
import traceback
import os

from my_crew import MyCrew  # Ensure MyCrew is imported correctly
from datetime import datetime

class PageCrewRun:
    def __init__(self):
        self.name = "Kickoff!"
        self.maintain_session_state()

    @staticmethod
    def maintain_session_state():
        """Initialize default session state variables if they don't exist."""
        defaults = {
            'crew_thread': None,
            'result': None,
            'running': False,
            'message_queue': queue.Queue(),
            'selected_crew_name': None,
            'placeholders': {}
        }
        for key, value in defaults.items():
            if key not in ss:
                ss[key] = value

    @staticmethod
    def extract_placeholders(text):
        """Extract placeholders enclosed in curly braces from the given text."""
        return re.findall(r'\{(.*?)\}', text)

    def get_placeholders_from_crew(self, crew: MyCrew):
        """
        Extract all unique placeholders from the crew's tasks and agents.

        Args:
            crew (MyCrew): The crew from which to extract placeholders.

        Returns:
            set: A set of unique placeholder strings.
        """
        placeholders = set()
        attributes = ['description', 'expected_output', 'role', 'backstory', 'goal']

        for task in crew.tasks:
            placeholders.update(self.extract_placeholders(task.description))
            placeholders.update(self.extract_placeholders(task.expected_output))

        for agent in crew.agents:
            for attr in attributes:
                attr_value = getattr(agent, attr, "")
                if isinstance(attr_value, str):
                    placeholders.update(self.extract_placeholders(attr_value))

        return placeholders

    def run_crew(self, crewai_crew, inputs, message_queue):
        """
        Execute the crew's kickoff method in a separate thread and handle results.

        Args:
            crewai_crew (Crew): The crew instance to run.
            inputs (dict): Inputs to pass to the crew.
            message_queue (queue.Queue): Queue to communicate results back to the main thread.
        """
        try:
            result = crewai_crew.kickoff(inputs=inputs)
            message_queue.put({"result": result})
        except Exception as e:
            stack_trace = traceback.format_exc()
            message_queue.put({"result": f"Error running crew: {str(e)}", "stack_trace": stack_trace})

    def get_mycrew_by_name(self, crewname: str) -> MyCrew:
        """
        Retrieve a crew by its name.

        Args:
            crewname (str): The name of the crew to retrieve.

        Returns:
            MyCrew: The corresponding crew instance.
        """
        return next((crew for crew in ss.crews if crew.name == crewname), None)

    def draw_placeholders(self, crew: MyCrew):
        """
        Render input fields for all placeholders identified in the crew.

        Args:
            crew (MyCrew): The crew whose placeholders are to be rendered.
        """
        placeholders = self.get_placeholders_from_crew(crew)
        if placeholders:
            st.write('**Placeholders to fill in:**')
            for placeholder in placeholders:
                placeholder_key = f'placeholder_{placeholder}'
                ss.placeholders[placeholder_key] = st.text_input(
                    label=placeholder,
                    key=placeholder_key,
                    value=ss.placeholders.get(placeholder_key, ''),
                    disabled=ss.running
                )

    def draw_crews(self):
        """
        Render the UI components for selecting and managing crews to run.
        """
        if 'crews' not in ss or not ss.crews:
            st.warning("No crews defined yet.")
            ss.selected_crew_name = None  # Reset selected crew name if there are no crews
            return

        # Check if the selected crew name still exists
        if ss.selected_crew_name not in [crew.name for crew in ss.crews]:
            ss.selected_crew_name = None

        selected_crew_name = st.selectbox(
            label="Select crew to run",
            options=[crew.name for crew in ss.crews],
            index=0 if ss.selected_crew_name is None else [crew.name for crew in ss.crews].index(ss.selected_crew_name) if ss.selected_crew_name in [crew.name for crew in ss.crews] else 0,
            disabled=ss.running
        )

        if selected_crew_name != ss.selected_crew_name:
            ss.selected_crew_name = selected_crew_name
            st.experimental_rerun()

        selected_crew = self.get_mycrew_by_name(ss.selected_crew_name)

        if selected_crew:
            selected_crew.draw(expanded=False, buttons=False)
            self.draw_placeholders(selected_crew)

            if not selected_crew.is_valid(show_warning=True):
                st.error("Selected crew is not valid. Please fix the issues.")
            self.control_buttons(selected_crew)

    def control_buttons(self, selected_crew: MyCrew):
        """
        Render and handle the Run and Stop buttons for the selected crew.

        Args:
            selected_crew (MyCrew): The crew to be run or stopped.
        """
        col1, col2 = st.columns(2)

        with col1:
            if st.button('Run crew!', disabled=not selected_crew.is_valid() or ss.running):
                inputs = {key.split('_')[1]: value for key, value in ss.placeholders.items()}
                ss.result = None
                try:
                    crew = selected_crew.get_crewai_crew(full_output=True)
                except Exception as e:
                    st.exception(e)
                    traceback.print_exc()
                    return

                ss.running = True
                ss.crew_thread = threading.Thread(
                    target=self.run_crew,
                    kwargs={
                        "crewai_crew": crew,
                        "inputs": inputs,
                        "message_queue": ss.message_queue
                    },
                    daemon=True  # Ensure thread exits when main program does
                )
                ss.crew_thread.start()
                st.experimental_rerun()

        with col2:
            if st.button('Stop crew!', disabled=not ss.running):
                self.request_stop_thread()
                ss.message_queue.queue.clear()
                ss.running = False
                ss.crew_thread = None
                ss.result = None
                st.success("Crew stopped successfully.")
                st.experimental_rerun()

    def display_result(self):
        """
        Display the result of the crew's execution.
        """
        if ss.result is not None:
            if isinstance(ss.result, dict):
                if 'final_output' in ss.result.get("result", {}):  # Old version of crewai
                    st.expander("Final output", expanded=True).write(ss.result["result"]['final_output'])
                elif hasattr(ss.result.get("result", {}), 'raw'):  # New version of crewai
                    st.expander("Final output", expanded=True).write(ss.result['result'].raw)
                st.expander("Full output", expanded=False).write(ss.result)
            else:
                st.error(ss.result)
        elif ss.running and ss.crew_thread is not None:
            with st.spinner("Running crew..."):
                while ss.running:
                    time.sleep(1)
                    if not ss.message_queue.empty():
                        ss.result = ss.message_queue.get()
                        ss.running = False
                        st.experimental_rerun()

    def request_stop_thread(self):
        """
        Request the running thread to stop gracefully.
        """
        # Note: Python does not support killing threads. Implement a stop mechanism if possible.
        # For example, using a threading.Event to signal the thread to exit.
        st.warning("Stopping threads forcefully is not supported. Implement a cooperative stopping mechanism.")
        # Implement a proper stopping mechanism here if your crewai library supports it.

    def draw(self):
        """
        Render the entire Crew Run page.
        """
        st.subheader(self.name)
        self.draw_crews()
        self.display_result()