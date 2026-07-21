"""Root Streamlit entrypoint.

Keeping this file at project root avoids Python confusing `app/app.py` with the
`app` package when Streamlit executes a script directly.
"""

import streamlit as st


st.set_page_config(
    page_title="EcoSort-Search",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from app.ui import main


if __name__ == "__main__":
    main()
