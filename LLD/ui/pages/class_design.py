"""Class Design step page."""

import streamlit as st
from LLD.models import ClassDesign


def render() -> None:
    if not st.session_state.get("requirements"):
        st.warning("Please define requirements first!")
        st.stop()

    st.markdown('<div class="section-header">🎨 Class Design Phase</div>', unsafe_allow_html=True)

    # Force sections to stack vertically (override any global flex/grid)
    st.markdown(
        """
        <style>
        .stApp .main .block-container { display: block !important; }
        .stApp .main .block-container > div { width: 100% !important; }
        /* Ensure any accidental inline-blocks take full width */
        .stApp .block-container .stMarkdown, 
        .stApp .block-container .stTextArea, 
        .stApp .block-container .stSelectbox, 
        .stApp .block-container .stRadio, 
        .stApp .block-container .stButton, 
        .stApp .block-container .stExpander,
        .stApp .block-container .stMetric {
            display: block !important;
            width: 100% !important;
        }
        /* Add vertical rhythm between logical rows */
        .stApp .block-container h3 { margin-top: 1.25rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Display requirements
    with st.expander("📋 View Requirements"):
        st.write(st.session_state.requirements)

    # ----------------------------------
    # Row 1: Class design input (Create / Edit)
    # ----------------------------------

    st.markdown("### 🛠️ Design Your Classes")

    # Create an outer layout – 20% for class design form, 80% for evaluation.
    design_col, eval_col = st.columns([1, 4])

    with design_col:
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

        # Show class details input once a class name is provided
        if "class_name" in locals() and class_name:
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

    # ----------------------------------
    # Row 2: Evaluation
    # ----------------------------------

    with eval_col:
        st.markdown("### 📊 Design Evaluation")
        if st.session_state.class_designs:
            selected_class = st.selectbox("Evaluate Class:", list(st.session_state.class_designs.keys()))
            if st.button("Evaluate Design"):
                evaluation = st.session_state.evaluator.evaluate_class_design(
                    st.session_state.class_designs[selected_class]
                )

                # Display evaluation in a single-row layout using columns
                st.metric("Design Score", f"{evaluation['overall_score']:.1f}/10")

            for item in evaluation["feedback"]:
                # Normalize to dict-like structure regardless of type
                if isinstance(item, dict):
                    level = item.get("level", "info")
                    message = item.get("message", "")
                elif hasattr(item, "level") and hasattr(item, "message"):
                    # Pydantic BaseModel instance
                    level = getattr(item, "level")
                    message = getattr(item, "message")
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    level, message = item[0], item[1]
                else:
                    level, message = "info", str(item)

                level_lower = str(level).lower()
                if level_lower in {"good", "success", "info"}:
                    css = "evaluation-good"
                elif level_lower in {"warning", "recommendation"}:
                    css = "evaluation-warning"
                elif level_lower in {"error", "critical"}:
                    css = "evaluation-error"
                else:
                    css = "evaluation-warning"

                st.markdown(f'<div class="{css}">{message}</div>', unsafe_allow_html=True)
            if evaluation["suggestions"]:
                st.markdown("**Suggestions:**")
                for suggestion in evaluation["suggestions"]:
                    st.write(f"💡 {suggestion}")
            if evaluation["design_patterns"]:
                st.markdown("**Identified Patterns:**")
                for pattern in evaluation["design_patterns"]:
                    st.write(f"🔧 {pattern}")

    # ----------------------------------
    # Row 3: Tips and Designed Classes
    # ----------------------------------

    st.markdown("### 💡 Tips and Designed Classes")

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
