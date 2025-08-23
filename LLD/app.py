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
from typing import Dict, List, Any

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
if "evaluator" not in st.session_state:
    st.session_state.evaluator = DesignEvaluator()
if "current_step" not in st.session_state:
    st.session_state.current_step = "requirements"

# Main header
st.markdown('<h1 class="main-header">🏗️ Low Level Design Learning Platform</h1>', unsafe_allow_html=True)

# Sidebar navigation
st.session_state.current_step = navigation.select_step()

# Requirements Section
if st.session_state.current_step == "requirements":
    st.markdown('<div class="section-header">📋 Requirements</div>', unsafe_allow_html=True)
    st.write("This section will be dedicated to defining the requirements for the system.")
    # Placeholder for requirements input/display
    st.session_state.requirements = st.text_area("Define Requirements:", value=st.session_state.requirements, height=200)
    if st.button("Save Requirements"):
        st.session_state.current_step = "design" # Move to design phase
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
    
    # Class design input
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("**Design Your Classes:**")
        
        # Class selection/creation
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
                st.success(f"Class '{class_name}' saved successfully!")
                st.rerun()
    
    with col2:
        st.markdown("**Design Evaluation:**")
        
        if st.session_state.class_designs:
            selected_class = st.selectbox("Evaluate Class:", list(st.session_state.class_designs.keys()))
            
            if st.button("Evaluate Design"):
                evaluation = st.session_state.evaluator.evaluate_class_design(
                    st.session_state.class_designs[selected_class]
                )
                
                # Display score
                st.metric("Design Score", f"{evaluation['overall_score']:.1f}/10")
                
                # Display feedback
                for feedback_type, message in evaluation["feedback"]:
                    if feedback_type == "good":
                        st.markdown(f'<div class="evaluation-good">{message}</div>', unsafe_allow_html=True)
                    elif feedback_type == "warning":
                        st.markdown(f'<div class="evaluation-warning">{message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="evaluation-error">{message}</div>', unsafe_allow_html=True)
                
                # Suggestions
                if evaluation["suggestions"]:
                    st.markdown("**Suggestions:**")
                    for suggestion in evaluation["suggestions"]:
                        st.write(f"💡 {suggestion}")
                
                # Design patterns
                if evaluation["design_patterns"]:
                    st.markdown("**Identified Patterns:**")
                    for pattern in evaluation["design_patterns"]:
                        st.write(f"🔧 {pattern}")
        
        # Display existing classes
        if st.session_state.class_designs:
            st.markdown("**Designed Classes:**")
            for name, design in st.session_state.class_designs.items():
                with st.expander(f"📦 {name}"):
                    st.write(f"**Responsibilities:** {len(design.responsibilities)}")
                    st.write(f"**Attributes:** {len(design.attributes)}")
                    st.write(f"**Methods:** {len(design.methods)}")
                    st.write(f"**Relationships:** {len(design.relationships)}")

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