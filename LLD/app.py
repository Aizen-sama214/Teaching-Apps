import sys, pathlib
from dotenv import load_dotenv
import os
# Ensure project root is on sys.path for imports
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load environment variables from .env at project root
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)

import streamlit as st
import json
import re
# Database & typing imports
from typing import Dict, List, Any
import logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Configure a basic handler if the application hasn't configured logging yet
    logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO"))

# --- SQLite helpers ---
from LLD import db as db_helpers

# Initialize DB (creates tables on first run)
db_helpers.init_db()

# --- Load problem statements from DB ---
PREDEFINED_REQUIREMENTS: Dict[str, str] = db_helpers.fetch_problems()

from LLD.models import DesignPrinciple, ClassDesign
from LLD.evaluator import DesignEvaluator
from LLD.ui import styling
from LLD.ui import navigation
from LLD.ui.pages import code_impl, demo as demo_page

# Configure page
st.set_page_config(
    page_title="LLD Learning Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
styling.inject_css()

# Initialize session state
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

# Main header
st.markdown('<h1 class="main-header">🏗️ Low Level Design Learning Platform</h1>', unsafe_allow_html=True)

# Sidebar navigation
st.session_state.current_step = navigation.select_step()

# Requirements Section
if st.session_state.current_step == "requirements":
    st.markdown('<div class="section-header">📋 Requirements</div>', unsafe_allow_html=True)
    st.write("Select a predefined design problem or input your own requirements.")

    # Predefined problem selection
    selected_problem = ""
    if PREDEFINED_REQUIREMENTS:
        problem_names = ["-- Select --"] + list(PREDEFINED_REQUIREMENTS.keys())
        selected_problem = st.selectbox("Choose a predefined design problem:", problem_names, index=0)

        if selected_problem not in ("", "-- Select --"):
            if st.button("Load Predefined Requirements"):
                st.session_state.requirements = PREDEFINED_REQUIREMENTS[selected_problem]
                st.success(f"Loaded requirements for '{selected_problem}'! You can edit them below or proceed to the next step.")

# Input field for problem name (for new or existing problems)
    problem_name_input = st.text_input(
        "Problem Name (for saving/updating in library):",
        value=selected_problem if 'selected_problem' in locals() and selected_problem not in ("", "-- Select --") else "",
        placeholder="e.g., Food Delivery App",
    )

    # Manual requirements input / edit area
    st.session_state.requirements = st.text_area(
        "Define Requirements:",
        value=st.session_state.requirements,
        height=300,
    )

    # --- Save & Continue Button ---
    if st.button("Save & Continue", type="primary"):
        name = problem_name_input.strip()
        if name:
            try:
                db_helpers.save_problem(name, st.session_state.requirements)
                st.success(f"Requirements for '{name}' saved to library.")
                PREDEFINED_REQUIREMENTS[name] = st.session_state.requirements
                st.session_state.current_problem = name
            except Exception as e:
                st.error(f"Failed to save to DB: {e}")

        # Navigate to class design
        st.session_state.current_step = "design"
        st.rerun()

# Class Design Section
elif st.session_state.current_step == "design":
    st.markdown('<div class="section-header">🎨 Class Design Phase</div>', unsafe_allow_html=True)
    
    if not st.session_state.requirements:
        st.warning("Please define requirements first!")
        st.stop()
    
    # Display requirements
    with st.expander("📋 View Requirements"):
        st.write(st.session_state.requirements)
    
    # Class design input – give "Design Classes" only 20% width and Evaluation 80%
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown("**Design Your Classes:**")
        
        # Class selection/creation
        # Refresh class designs from DB when entering design step
        if st.session_state.current_problem:
            st.session_state.class_designs = db_helpers.fetch_class_designs(st.session_state.current_problem)
            st.session_state.evaluations = db_helpers.fetch_evaluations(st.session_state.current_problem)

        existing_classes = list(st.session_state.class_designs.keys())
        
        class_option = st.radio("Choose option:", ["Create New Class", "Edit Existing Class"])
        
        if class_option == "Create New Class":
            class_name = st.text_input("Class Name:", placeholder="e.g., ParkingSpot")
        else:
            if existing_classes:
                class_name = st.selectbox("Select Class to Edit:", existing_classes)
            else:
                st.warning("No existing classes found. Create a new class first.")
                st.stop()
        
        if class_name:
            # Load existing design if editing
            if class_option == "Edit Existing Class" and class_name in st.session_state.class_designs:
                existing_design = st.session_state.class_designs[class_name]
                default_resp = existing_design.responsibilities
                default_attrs = existing_design.attributes
                default_methods = existing_design.methods
                default_rels = existing_design.relationships
            else:
                default_resp = []
                default_attrs = []
                default_methods = []
                default_rels = []
            
            # Input fields
            responsibilities = st.text_area(
                "Responsibilities (one per line):",
                value="\n".join(default_resp),
                placeholder="Represent a parking space in the lot\nManage spot availability",
                height=100
            )
            
            attributes = st.text_area(
                "Attributes (one per line):",
                value="\n".join(default_attrs),
                placeholder="spotId\nspotType\nisAvailable\ncurrentVehicle",
                height=100
            )
            
            methods = st.text_area(
                "Methods (one per line):",
                value="\n".join(default_methods),
                placeholder="parkVehicle(vehicle)\nremoveVehicle()\nisAvailable()",
                height=100
            )
            
            relationships = st.text_area(
                "Relationships (one per line):",
                value="\n".join(default_rels),
                placeholder="Has-a Vehicle\nBelongs to ParkingLot",
                height=100
            )
            
            if st.button("Save Class Design", type="primary"):
                class_design = ClassDesign(
                    name=class_name,
                    responsibilities=[r.strip() for r in responsibilities.split('\n') if r.strip()],
                    attributes=[a.strip() for a in attributes.split('\n') if a.strip()],
                    methods=[m.strip() for m in methods.split('\n') if m.strip()],
                    relationships=[r.strip() for r in relationships.split('\n') if r.strip()]
                )
                st.session_state.class_designs[class_name] = class_design
                # Persist to DB
                try:
                    db_helpers.save_class_design(st.session_state.current_problem, class_design)
                except Exception as e:
                    st.error(f"Failed to save to DB: {e}")
                st.success(f"Class '{class_name}' saved successfully!")
                st.rerun()
    
    with col2:
        st.markdown("**Design Evaluation:**")

        if st.session_state.class_designs:
            if st.button("Evaluate All Designs"):
                if not st.session_state.requirements.strip():
                    st.warning("⚠️ Requirements have not been selected. Please define/select requirements first.")
                    st.stop()

                # Attempt batch evaluation (requires updated evaluator)
                try:
                    evaluations = st.session_state.evaluator.evaluate_class_designs(
                        st.session_state.class_designs,
                        requirements=st.session_state.requirements,
                    )
                except AttributeError:
                    # Fallback for older evaluator versions – evaluate individually
                    evaluations = {}
                    for cls_name, cls_design in st.session_state.class_designs.items():
                        evaluations[cls_name] = st.session_state.evaluator.evaluate_class_design(
                            cls_design,
                            requirements=st.session_state.requirements,
                        )
                # Persist and update session state
                st.session_state.evaluations = evaluations
                try:
                    for cls_name, eval_dict in evaluations.items():
                        db_helpers.save_evaluation(st.session_state.current_problem, cls_name, eval_dict)
                except Exception as e:
                    st.error(f"Failed to save evaluations: {e}")

        # After evaluation (or if evaluations already exist), render results
        if st.session_state.get("evaluations"):
            eval_items = list(st.session_state.evaluations.items())
            eval_cols = st.columns(len(eval_items))
            for (cls_name, evaluation), col in zip(eval_items, eval_cols):
                with col:
                    display_name = evaluation.get("class_name", cls_name) if isinstance(evaluation, dict) else cls_name
                    st.markdown(f"### 📦 **{display_name}**")
                    st.metric("Design Score", f"{evaluation['overall_score']:.1f}/10")
                    # Feedback, suggestions, patterns as earlier code (refactor into function?)
                    with st.expander("📝 Detailed Feedback", expanded=False):
                        for fb in evaluation["feedback"]:
                            if isinstance(fb, dict):
                                level = fb.get("level", "info"); message = fb.get("message", "")
                            elif hasattr(fb, "level") and hasattr(fb, "message"):
                                level = getattr(fb, "level"); message = getattr(fb, "message")
                            elif isinstance(fb, (list, tuple)) and len(fb) >= 2:
                                level, message = fb[0], fb[1]
                            else:
                                level, message = "info", str(fb)
                            level_lower = str(level).lower()
                            if level_lower in {"good", "info", "success"}:
                                css = "evaluation-good"
                            elif level_lower in {"warning", "recommendation"}:
                                css = "evaluation-warning"
                            else:
                                css = "evaluation-error"
                            st.markdown(f'<div class="{css}">{message}</div>', unsafe_allow_html=True)
                    if evaluation["suggestions"]:
                        with st.expander("💡 Suggestions", expanded=False):
                            for suggestion in evaluation["suggestions"]:
                                st.write(f"💡 {suggestion}")
                    if evaluation["design_patterns"]:
                        with st.expander("🔧 Identified Patterns", expanded=False):
                            for pattern in evaluation["design_patterns"]:
                                st.write(f"🔧 {pattern}")
        
        # Display existing classes
        if st.session_state.class_designs:
            st.markdown("**Designed Classes:**")
            class_items = list(st.session_state.class_designs.items())
            class_cols = st.columns(len(class_items))
            for (name, design), col in zip(class_items, class_cols):
                with col:
                    with st.expander(f"📦 {name}"):
                        st.write(f"**Responsibilities:** {len(design.responsibilities)}")
                        st.write(f"**Attributes:** {len(design.attributes)}")
                        st.write(f"**Methods:** {len(design.methods)}")
                        st.write(f"**Relationships:** {len(design.relationships)}")

                    # Delete button
                    if st.button(f"Delete '{name}'", key=f"del_{name}"):
                        try:
                            db_helpers.delete_class_design(st.session_state.current_problem, name)
                            st.session_state.class_designs.pop(name, None)
                            st.success(f"Deleted class '{name}'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")

# Code Implementation Section
elif st.session_state.current_step == "code":
    code_impl.render()

# Demo Section
elif st.session_state.current_step == "demo":
    demo_page.render()

# Footer
st.markdown("---")
st.markdown("**💡 Tips:**")
st.markdown("""
- Follow SOLID principles in your design
- Keep classes focused on single responsibilities  
- Use composition over inheritance when possible
- Add proper validation and error handling
- Write clear, descriptive method names
- Consider edge cases in your implementation
""")

# Progress indicator
progress = 0
if st.session_state.requirements: progress += 25
if st.session_state.class_designs: progress += 25
if any(design.code for design in st.session_state.class_designs.values()): progress += 25
if progress == 75: progress = 100  # Complete when demo is accessible

st.sidebar.markdown("---")
st.sidebar.markdown("**Overall Progress:**")
st.sidebar.progress(progress / 100)
st.sidebar.markdown(f"{progress}% Complete")