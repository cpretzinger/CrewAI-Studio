from core_utils import rnd_id
import streamlit as st
from typing import Optional, Dict, Any, List

class MyTool:
    def __init__(
        self,
        tool_id: Optional[str] = None,
        name: str = "",
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ):
        self.tool_id = tool_id or "T_" + rnd_id()
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.enabled = enabled
        self.edit_key = f'edit_{self.tool_id}'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MyTool':
        return cls(
            tool_id=data.get("tool_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            enabled=data.get("enabled", True)
        )

    def get_parameter_names(self) -> List[str]:
        return list(self.parameters.keys())

    def is_valid(self, show_warning: bool = False) -> bool:
        """
        Validate the tool's data.

        Args:
            show_warning (bool): Whether to show warnings for missing data.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not self.name:
            if show_warning:
                st.warning("Tool name is required.")
            return False
        # Add more validation rules as needed
        return True

    def create_tool(self):
        """Create and return a tool instance based on the tool's configuration."""
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement create_tool()")
