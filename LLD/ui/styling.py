"""UI styling helpers for Streamlit pages."""

import streamlit as st

# Centralised CSS used across the app.
_CSS = r"""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    font-size: 1.5rem;
    color: #ff7f0e;
    border-bottom: 2px solid #ff7f0e;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}
.class-card {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
.evaluation-good {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 0.5rem 0;
}
.evaluation-warning {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 0.5rem 0;
}
.evaluation-error {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 0.5rem 0;
}
</style>
"""

def inject_css() -> None:
    """Inject the shared CSS into the Streamlit app."""
    st.markdown(_CSS, unsafe_allow_html=True)
