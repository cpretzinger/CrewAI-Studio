# utils.py
from streamlit import markdown

def escape_quotes(s: str) -> str:
    """
    Escapes single and double quotes in a string.

    Args:
        s (str): The input string.

    Returns:
        str: The escaped string.
    """
    return s.replace('"', '\\"').replace("'", "\\'")

def fix_columns_width():
    """
    Injects custom CSS into the Streamlit app to adjust column widths.

    This function modifies the width of Streamlit columns to fit their content,
    overriding the default styling.
    """
    markdown("""
        <style>
            /* Adjust column width to fit content */
            div[data-testid="column"] {
                width: fit-content !important;
                flex: unset;
            }
            div[data-testid="column"] * {
                width: fit-content !important;
            }
        </style>
        """, unsafe_allow_html=True)
