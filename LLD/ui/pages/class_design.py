"""Class Design step page."""

import streamlit as st
from LLD.models import ClassDesign


def render() -> None:
    if not st.session_state.get("requirements"):
        st.warning("Please define requirements first!")
        st.stop()

    st.markdown('<div class="section-header">🎨 Class Design Phase</div>', unsafe_allow_html=True)

    # Display requirements
    with st.expander("📋 View Requirements"):
        st.write(st.session_state.requirements)

    # Class design input
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("**Design Your Classes:**")
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

            responsibilities = st.text_area(
                "Responsibilities (one per line):",
                value="\n".join(default_resp),
                placeholder="Represent a parking space in the lot\nManage spot availability",
                height=100,
            )
            attributes = st.text_area(
                "Attributes (one per line):",
                value="\n".join(default_attrs),
                placeholder="spotId\nspotType\nisAvailable\ncurrentVehicle",
                height=100,
            )
            methods = st.text_area(
                "Methods (one per line):",
                value="\n".join(default_methods),
                placeholder="parkVehicle(vehicle)\nremoveVehicle()\nisAvailable()",
                height=100,
            )
            relationships = st.text_area(
                "Relationships (one per line):",
                value="\n".join(default_rels),
                placeholder="Has-a Vehicle\nBelongs to ParkingLot",
                height=100,
            )
            if st.button("Save Class Design", type="primary"):
                class_design = ClassDesign(
                    name=class_name,
                    responsibilities=[r.strip() for r in responsibilities.split("\n") if r.strip()],
                    attributes=[a.strip() for a in attributes.split("\n") if a.strip()],
                    methods=[m.strip() for m in methods.split("\n") if m.strip()],
                    relationships=[r.strip() for r in relationships.split("\n") if r.strip()],
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
                st.metric("Design Score", f"{evaluation['overall_score']:.1f}/10")
                for feedback_type, message in evaluation["feedback"]:
                    css = {
                        "good": "evaluation-good",
                        "warning": "evaluation-warning",
                        "error": "evaluation-error",
                    }[feedback_type]
                    st.markdown(f'<div class="{css}">{message}</div>', unsafe_allow_html=True)
                if evaluation["suggestions"]:
                    st.markdown("**Suggestions:**")
                    for suggestion in evaluation["suggestions"]:
                        st.write(f"💡 {suggestion}")
                if evaluation["design_patterns"]:
                    st.markdown("**Identified Patterns:**")
                    for pattern in evaluation["design_patterns"]:
                        st.write(f"🔧 {pattern}")

        if st.session_state.class_designs:
            st.markdown("**Designed Classes:**")
            for name, design in st.session_state.class_designs.items():
                with st.expander(f"📦 {name}"):
                    st.write(f"**Responsibilities:** {len(design.responsibilities)}")
                    st.write(f"**Attributes:** {len(design.attributes)}")
                    st.write(f"**Methods:** {len(design.methods)}")
                    st.write(f"**Relationships:** {len(design.relationships)}")
