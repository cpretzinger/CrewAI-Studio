# pg_tools.py

import streamlit as st
from core_utils import rnd_id
from my_tools import TOOL_CLASSES
from custom_tools import MyCustomFileWriteTool
from streamlit import session_state as ss
import db_utils
from agentops import record_tool, record, ActionEvent
from typing import Optional, Dict, Any
import os

class PageTools:
    def __init__(self):
        self.name = "Tools"
        self.available_tools = TOOL_CLASSES
        self.maintain_session_state()

    @staticmethod
    def maintain_session_state():
        """Initialize default session state variables if they don't exist."""
        if 'tools' not in ss:
            ss.tools = []  # Tools will be created as needed

    @record_tool('Create Tool')
    def create_tool(self, tool_name: str):
        """
        Create a new tool instance based on the selected tool name.

        Args:
            tool_name (str): The name of the tool to create.
        """
        tool_class = self.available_tools.get(tool_name)
        if not tool_class:
            st.error(f"Tool '{tool_name}' is not recognized.")
            return

        # Instantiate the tool with a unique ID
        if tool_class == MyCustomFileWriteTool:
            tool_instance = tool_class(base_folder=os.path.abspath(os.getenv('WORKSPACE_DIR', './workspace')))
        else:
            tool_instance = tool_class()

        # Initialize tools in session state if not present
        if 'tools' not in ss:
            ss.tools = []

        # Add the new tool to session state
        ss.tools.append(tool_instance)

        st.success(f"Tool '{tool_name}' created successfully.")
        st.experimental_rerun()

    @record_tool('Remove Tool')
    def remove_tool(self, tool_id: str):
        """
        Remove a tool from the session state.

        Args:
            tool_id (str): The unique ID of the tool to remove.
        """
        initial_length = len(ss.tools)
        ss.tools = [tool for tool in ss.tools if tool.tool_id != tool_id]
        if len(ss.tools) < initial_length:
            st.success(f"Tool '{tool_id}' removed successfully.")
            st.experimental_rerun()
        else:
            st.error(f"Tool '{tool_id}' not found.")

    @record_tool('Update Tool Parameter')
    def set_tool_parameter(self, tool_id: str, param_name: str, value: Any):
        """
        Update a specific parameter of a tool.

        Args:
            tool_id (str): The unique ID of the tool.
            param_name (str): The name of the parameter to update.
            value (Any): The new value for the parameter.
        """
        for tool in ss.tools:
            if tool.tool_id == tool_id:
                # Convert empty strings to None for optional parameters
                if value == "":
                    value = None
                tool.set_parameters(**{param_name: value})
                st.success(f"Parameter '{param_name}' updated successfully for tool '{tool.name}'.")
                break
        else:
            st.error(f"Tool with ID '{tool_id}' not found.")

    def get_tool_display_name(self, tool) -> str:
        """
        Generate a display name for a tool based on its parameters.

        Args:
            tool: The tool instance.

        Returns:
            str: The display name.
        """
        first_param_name = tool.get_parameter_names()[0] if tool.get_parameter_names() else None
        first_param_value = tool.parameters.get(first_param_name, '') if first_param_name else ''
        return f"{tool.name} ({first_param_value if first_param_value else tool.tool_id})"

    def draw_available_tools(self):
        """
        Render the list of available tools that can be enabled.
        """
        st.markdown("### Available Tools")
        cols = st.columns(4)  # Adjust the number of columns based on available tools
        for idx, tool_name in enumerate(self.available_tools.keys()):
            col = cols[idx % len(cols)]
            with col:
                tool_class = self.available_tools[tool_name]
                tool_instance = tool_class()  # Instantiate without parameters for display
                tool_description = tool_instance.description
                if st.button(f"{tool_name}", key=f"enable_{tool_name}", help=tool_description):
                    self.create_tool(tool_name)

    def draw_enabled_tools(self):
        """
        Render the list of enabled tools with their parameters and removal options.
        """
        st.markdown("### Enabled Tools")
        if 'tools' not in ss or not ss.tools:
            st.info("No tools have been enabled yet.")
            return

        for tool in ss.tools:
            display_name = self.get_tool_display_name(tool)
            is_complete = tool.is_valid(show_warning=True)
            expander_title = display_name if is_complete else f"❗ {display_name}"
            with st.expander(expander_title, expanded=False):
                st.write(tool.description)
                for param_name in tool.get_parameter_names():
                    param_info = tool.parameters_metadata.get(param_name, {})
                    param_value = tool.parameters.get(param_name, "")
                    placeholder = "Required" if tool.is_parameter_mandatory(param_name) else "Optional"

                    # Determine input type based on parameter metadata (extend as needed)
                    input_type = param_info.get('type', 'text')
                    if input_type == 'text':
                        new_value = st.text_input(
                            f"{param_name}",
                            value=param_value if param_value is not None else '',
                            key=f"{tool.tool_id}_{param_name}",
                            placeholder=placeholder,
                            disabled=not is_complete
                        )
                    elif input_type == 'bool':
                        new_value = st.checkbox(
                            f"{param_name}",
                            value=bool(param_value),
                            key=f"{tool.tool_id}_{param_name}",
                            disabled=not is_complete
                        )
                    elif input_type == 'number':
                        new_value = st.number_input(
                            f"{param_name}",
                            value=float(param_value) if param_value is not None else 0.0,
                            key=f"{tool.tool_id}_{param_name}",
                            disabled=not is_complete
                        )
                    else:
                        new_value = st.text_input(
                            f"{param_name}",
                            value=param_value if param_value is not None else '',
                            key=f"{tool.tool_id}_{param_name}",
                            placeholder=placeholder,
                            disabled=not is_complete
                        )

                    # Update parameter if changed
                    if new_value != param_value:
                        self.set_tool_parameter(tool.tool_id, param_name, new_value)

                # Remove tool button
                if st.button(f"Remove {tool.name}", key=f"remove_{tool.tool_id}"):
                    self.remove_tool(tool.tool_id)

    def draw_tools(self):
        """
        Render the UI for available and enabled tools.
        """
        col1, col2 = st.columns([1, 3])

        with col1:
            self.draw_available_tools()

        with col2:
            self.draw_enabled_tools()

    def draw(self):
        """
        Render the entire Tools page.
        """
        st.subheader(self.name)
        self.draw_tools()

# Instantiate and render the page
def main():
    page = PageTools()
    page.draw()

if __name__ == "__main__":
    main()
