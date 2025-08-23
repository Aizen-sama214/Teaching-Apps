# noqa: D100
# Streamlit entry-point for the LLD learning platform.
# NOTE: This file was extracted from ``LLD.app`` to improve package structure.

# Standard library
import sys
import pathlib
import os
from typing import Dict

# Third-party
from dotenv import load_dotenv
import streamlit as st

# -----------------------------------------------------------------------------
# Environment & path setup (MUST run before importing the "LLD" package)
# -----------------------------------------------------------------------------
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Now that the workspace root is on PYTHONPATH we can safely import internal pkgs

# Local packages
from LLD.persistence import database as db_helpers
from LLD.core.models import ClassDesign, DesignPrinciple
from LLD.core.evaluator import DesignEvaluator
from LLD.ui import navigation, styling
from LLD.ui.pages import code_impl, demo as demo_page

# -----------------------------------------------------------------------------
# DB bootstrap & problem cache
# -----------------------------------------------------------------------------
db_helpers.init_db()
PREDEFINED_REQUIREMENTS: Dict[str, str] = db_helpers.fetch_problems()

# -----------------------------------------------------------------------------
# Streamlit page configuration & styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LLD Learning Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

styling.inject_css()

# -----------------------------------------------------------------------------
# Session-state defaults
# -----------------------------------------------------------------------------
if "requirements" not in st.session_state:
    st.session_state.requirements = ""
if "class_designs" not in st.session_state:
    st.session_state.class_designs = {}
if "current_problem" not in st.session_state:
    st.session_state.current_problem = ""
if "evaluator" not in st.session_state:
    st.session_state.evaluator = DesignEvaluator()
if "current_step" not in st.session_state:
    st.session_state.current_step = "requirements"
if "evaluations" not in st.session_state:
    st.session_state.evaluations = {}
if "impl_evaluations" not in st.session_state:
    st.session_state.impl_evaluations = {}

# -----------------------------------------------------------------------------
# UI flow
# -----------------------------------------------------------------------------

st.markdown('<h1 class="main-header">🏗️ Low Level Design Learning Platform</h1>', unsafe_allow_html=True)

st.session_state.current_step = navigation.select_step()

# Dynamically render the selected page
if st.session_state.current_step == "requirements":
    from LLD.ui.pages import requirements as req_page  # local import to avoid circulars

    req_page.render(PREDEFINED_REQUIREMENTS)
elif st.session_state.current_step == "design":
    from LLD.ui.pages import class_design as design_page

    design_page.render()
elif st.session_state.current_step == "code":
    code_impl.render()
elif st.session_state.current_step == "demo":
    demo_page.render()

# -----------------------------------------------------------------------------
# Footer & progress indicator
# -----------------------------------------------------------------------------

st.markdown("---")
st.markdown("**💡 Tips:**")
st.markdown(
    """
- Follow SOLID principles in your design
- Keep classes focused on single responsibilities  
- Use composition over inheritance when possible
- Add proper validation and error handling
- Write clear, descriptive method names
- Consider edge cases in your implementation
"""
)

progress = 0
if st.session_state.requirements:
    progress += 25
if st.session_state.class_designs:
    progress += 25
if any(cd.code for cd in st.session_state.class_designs.values()):
    progress += 25
if progress == 75:
    progress = 100

st.sidebar.markdown("---")
st.sidebar.markdown("**Overall Progress:**")
st.sidebar.progress(progress / 100)
st.sidebar.markdown(f"{progress}% Complete")
