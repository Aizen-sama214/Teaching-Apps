"""Sidebar navigation for the Streamlit LLD app."""

import streamlit as st

_STEPS = [
    "📋 Requirements",
    "🎨 Class Design",
    "💻 Code Implementation",
    "🧪 Demo & Testing",
]

_STEP_MAPPING = {
    "📋 Requirements": "requirements",
    "🎨 Class Design": "design",
    "💻 Code Implementation": "code",
    "🧪 Demo & Testing": "demo",
}


def select_step() -> str:
    """Render sidebar navigation and return the selected step key."""
    st.sidebar.title("Navigation")
    current_label = st.sidebar.radio("Current Step:", _STEPS)
    return _STEP_MAPPING[current_label]
