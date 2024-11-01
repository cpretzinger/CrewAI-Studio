# pg_tasks.py

import streamlit as st
from streamlit import session_state as ss
import db_utils  # Ensure it has both export_to_json and import_from_json functions
from agentops import record_action, record, ActionEvent

from my_task import MyTask  # Ensure MyTask is imported correctly
from my_crew import MyCrew  # Ensure MyCrew is imported correctly
from typing import Optional, List


class PageTasks:
    def __init__(self):
        self.name = "Tasks"
        self.maintain_session_state()

    @staticmethod
    def maintain_session_state():
        """Initialize default session state variables if they don't exist."""
        if 'tasks' not in ss:
            ss.tasks = db_utils.load_tasks()  # Ensure this loads a list of MyTask instances
        if 'crews' not in ss:
            ss.crews = db_utils.load_crews()  # Ensure this loads a list of MyCrew instances

    def load_tasks(self):
        """Load tasks from the database into session state."""
        ss.tasks = db_utils.load_tasks()

    def save_task(self, task: MyTask):
        """Save a task to the database."""
        db_utils.save_task(task)

    @record_action('Creating Task in Database')
    def create_task(self, crew: Optional[MyCrew] = None):
        """
        Create a new task and optionally assign it to a crew.

        Args:
            crew (MyCrew, optional): The crew to assign the task to.
        """
        # Log task creation action
        record(ActionEvent("task_creation_requested"))

        # Create a new task and save to DB
        task = MyTask()
        ss.tasks.append(task)
        task.edit = True
        self.save_task(task)

        # Optionally, link task to crew and save to DB
        if crew:
            crew.tasks.append(task)
            db_utils.save_crew(crew)

        return task

    @record_action('Loading Tasks from Database')
    def draw(self):
        """
        Render the Tasks page with tabs for All Tasks, Unassigned Tasks, and Crew-specific Tasks.
        """
        # Log viewing of the tasks list
        record(ActionEvent("user_viewed_tasks_list"))

        with st.container():
            st.subheader(self.name)
            editing = False

            # Ensure tasks and crews are loaded in session state
            if 'tasks' not in ss:
                self.load_tasks()
            if 'crews' not in ss:
                ss.crews = db_utils.load_crews()

            # Dictionary to track task assignments
            task_assignment = {task.id: [] for task in ss.tasks}

            # Assign tasks to crews
            for crew in ss.crews:
                for task in crew.tasks:
                    task_assignment[task.id].append(crew.name)

            # Define tabs: All Tasks, Unassigned Tasks, and one for each crew
            tabs = ["All Tasks", "Unassigned Tasks"] + [crew.name for crew in ss.crews]
            tab_objects = st.tabs(tabs)

            # All Tasks Tab
            with tab_objects[0]:
                st.markdown("#### All Tasks")
                for task in ss.tasks:
                    task.draw()
                    if task.edit:
                        editing = True
                st.button(
                    'Create Task',
                    on_click=self.create_task,
                    disabled=editing,
                    key="create_task_all"
                )

            # Unassigned Tasks Tab
            with tab_objects[1]:
                st.markdown("#### Unassigned Tasks")
                unassigned_tasks = [task for task in ss.tasks if not task_assignment[task.id]]
                for task in unassigned_tasks:
                    unique_key = f"{task.id}_unassigned"
                    task.draw(key=unique_key)
                    if task.edit:
                        editing = True
                st.button(
                    'Create Task',
                    on_click=self.create_task,
                    disabled=editing,
                    key="create_task_unassigned"
                )

            # Crew-specific Tabs
            for i, crew in enumerate(ss.crews, start=2):
                with tab_objects[i]:
                    st.markdown(f"#### {crew.name}")
                    assigned_tasks = crew.tasks
                    for task in assigned_tasks:
                        unique_key = f"{task.id}_{crew.name}"
                        task.draw(key=unique_key)
                        if task.edit:
                            editing = True
                    st.button(
                        'Create Task',
                        on_click=lambda c=crew: self.create_task(crew=c),
                        disabled=editing,
                        key=f"create_task_{crew.id}_button"
                    )

            # If there are no tasks, show a message and a button to create one
            if len(ss.tasks) == 0:
                st.warning("No tasks defined yet.")
                st.button(
                    'Create Task',
                    on_click=self.create_task,
                    disabled=editing,
                    key="create_task_no_tasks"
                )

            st.write("---")
            st.write("### Current Tasks Overview")
            self.display_tasks_overview()

    def display_tasks_overview(self):
        """
        Display a summary of tasks and their assignments.
        """
        if ss.tasks:
            total_tasks = len(ss.tasks)
            assigned_tasks = len([t for t in ss.tasks if any(t.id in [task.id for task in crew.tasks] for crew in ss.crews)])
            unassigned_tasks = total_tasks - assigned_tasks

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tasks", total_tasks)
            col2.metric("Assigned Tasks", assigned_tasks)
            col3.metric("Unassigned Tasks", unassigned_tasks)
        else:
            st.info("No tasks available to display.")

    @staticmethod
    def handle_create_task_button(crew: Optional[MyCrew] = None):
        """
        Callback function for creating a task. This is used to pass the crew parameter correctly.

        Args:
            crew (MyCrew, optional): The crew to assign the task to.
        """
        page = PageTasks()
        page.create_task(crew=crew)