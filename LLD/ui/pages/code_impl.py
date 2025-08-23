"""Code Implementation step page."""

import streamlit as st
from LLD.persistence import database as db_helpers
import json


def render() -> None:
    # Ensure we have an evals container even before any evaluation happens
    if "impl_evaluations" not in st.session_state:
        st.session_state.impl_evaluations = {}

    # --------------------------------------------------------------
    # Refresh data from DB when a problem is active (page switching)
    # --------------------------------------------------------------
    if st.session_state.get("current_problem"):
        # Always fetch the freshest class designs and implementation evaluations
        st.session_state.class_designs = db_helpers.fetch_class_designs(
            st.session_state.current_problem
        )
        st.session_state.impl_evaluations = db_helpers.fetch_implementation_evaluations(
            st.session_state.current_problem
        )

    if not st.session_state.class_designs:
        st.warning("Please design classes first!")
        st.stop()

    st.markdown('<div class="section-header">💻 Code Implementation</div>', unsafe_allow_html=True)

    class_to_code = st.selectbox("Select Class to Implement:", list(st.session_state.class_designs.keys()))
    if not class_to_code:
        return

    design = st.session_state.class_designs[class_to_code]
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(f"**Implement: {class_to_code}**")
        with st.expander("📋 View Design Details"):
            st.write("**Responsibilities:**")
            for resp in design.responsibilities:
                st.write(f"• {resp}")
            st.write("**Attributes:**")
            for attr in design.attributes:
                st.write(f"• {attr}")
            st.write("**Methods:**")
            for method in design.methods:
                st.write(f"• {method}")
            st.write("**Relationships:**")
            for rel in design.relationships:
                st.write(f"• {rel}")

        # Prepare code template components
        attr_lines = "\n".join([
            f"        self.{(attr.split()[0] if attr else 'attribute')} = None" for attr in design.attributes[:5]
        ])
        method_lines = "\n\n".join([
            f"    def {(method.split('(')[0] if '(' in method else method)}(self):\n        # TODO: Implement this method\n        pass" for method in design.methods[:3]
        ])

        code_template = f'''class {class_to_code}:
    """{design.responsibilities[0] if design.responsibilities else 'Class description'}"""

    def __init__(self):
        # Initialize attributes
{attr_lines}
        pass

{method_lines}
'''

        code = st.text_area(
            "Write your code:",
            value=design.code if design.code else code_template,
            height=400,
            help="Implement the class based on your design",
        )
        if st.button("Save Code", type="primary"):
            st.session_state.class_designs[class_to_code].code = code
            # Persist both class code and code implementation analysis to DB if problem loaded
            if st.session_state.get("current_problem"):
                # Update code column in classes table
                db_helpers.save_class_design(
                    st.session_state.current_problem,
                    st.session_state.class_designs[class_to_code],
                )
                # Prepare analysis payload similar to metrics shown in sidebar
                analysis_dict = {
                    "lines": len([ln for ln in code.split("\n") if ln.strip()]),
                    "methods": len([ln for ln in code.split("\n") if 'def ' in ln]),
                    "issues": [
                        issue for issue in (
                            (
                                "contains_pass" if "pass" in code else None,
                                "contains_todo" if "TODO" in code else None,
                                "contains_print" if "print(" in code else None,
                            )
                        ) if issue
                    ],
                }
                db_helpers.save_code_implementation(
                    st.session_state.current_problem,
                    class_to_code,
                    code,
                    analysis_dict,
                )
            st.success(f"Code for '{class_to_code}' saved!")

    with col2:
        st.markdown("**Code Analysis:**")
        if design.code:
            lines = len([ln for ln in design.code.split("\n") if ln.strip()])
            methods_in_code = len([ln for ln in design.code.split("\n") if 'def ' in ln])
            st.metric("Lines of Code", lines)
            st.metric("Methods Implemented", methods_in_code)
            issues = []
            if "pass" in design.code:
                issues.append("⚠️ Contains placeholder 'pass' statements")
            if "TODO" in design.code:
                issues.append("⚠️ Contains TODO comments")
            if "print(" in design.code:
                issues.append("ℹ️ Contains print statements (consider logging)")
            if issues:
                st.markdown("**Code Issues:**")
                for issue in issues:
                    st.write(issue)
            else:
                st.success("✅ No obvious issues detected")

    st.markdown("**Implementation Progress:**")
    progress_data = []
    for name, dsgn in st.session_state.class_designs.items():
        status = "✅ Implemented" if dsgn.code else "❌ Not Implemented"
        progress_data.append({"Class": name, "Status": status, "Lines": len(dsgn.code.split('\n')) if dsgn.code else 0})
    if progress_data:
        st.table(progress_data)

    # ----------------------------------
    # Evaluation of Implementations
    # ----------------------------------

    st.markdown("### 📊 Implementation Evaluation")
    if any(cd.code for cd in st.session_state.class_designs.values()):
        if st.button("Evaluate ALL Implementations", type="primary"):
            # Prepare mapping name -> code
            impl_map = {
                name: cd.code
                for name, cd in st.session_state.class_designs.items()
                if cd.code.strip()
            }
            batch_eval = st.session_state.evaluator.evaluate_class_implementations(
                impl_map,
                requirements=st.session_state.requirements,
            )
            # Persist evaluations
            if st.session_state.get("current_problem"):
                for cls_name, eval_dict in batch_eval.items():
                    db_helpers.save_implementation_evaluation(
                        st.session_state.current_problem,
                        cls_name,
                        eval_dict,
                    )
            st.session_state.impl_evaluations = batch_eval

    # Display evaluations if present
    if st.session_state.impl_evaluations:
        eval_items = list(st.session_state.impl_evaluations.items())
        cols = st.columns(len(eval_items))
        for (cls_name, evaluation), col in zip(eval_items, cols):
            with col:
                st.markdown(f"### 🧩 {cls_name}")
                st.metric("Score", f"{evaluation['overall_score']:.1f}/10")
                feedback_blob = evaluation.get("feedback", [])
                # Normalise feedback into list of (level,message)
                if isinstance(feedback_blob, str):
                    try:
                        feedback_blob = json.loads(feedback_blob)
                    except Exception:
                        feedback_blob = [("info", ln.strip()) for ln in feedback_blob.split("\n") if ln.strip()]

                with st.expander("📝 Feedback"):
                    for item in feedback_blob:
                        if isinstance(item, dict):
                            level = item.get("level", "info"); message = item.get("message", "")
                        elif isinstance(item, (list, tuple)) and len(item) >= 2:
                            level, message = item[0], item[1]
                        else:
                            level, message = "info", str(item)

                        level_lower = str(level).lower()
                        if level_lower in {"good", "success", "info"}:
                            css = "evaluation-good"
                        elif level_lower in {"warning", "recommendation"}:
                            css = "evaluation-warning"
                        else:
                            css = "evaluation-error"

                        st.markdown(f'<div class="{css}">{message}</div>', unsafe_allow_html=True)
                # ---------------- Suggestions ----------------
                suggestions = evaluation.get("suggestions")
                if isinstance(suggestions, str):
                    try:
                        suggestions = json.loads(suggestions)
                    except Exception:
                        suggestions = [s.strip() for s in suggestions.split("\n") if s.strip()]

                if suggestions:
                    with st.expander("💡 Suggestions"):
                        for suggestion in suggestions:
                            st.write(f"• {suggestion}")
                patterns = evaluation.get("design_patterns")
                if isinstance(patterns, str):
                    try:
                        patterns = json.loads(patterns)
                    except Exception:
                        patterns = [p.strip() for p in patterns.split("\n") if p.strip()]

                if patterns:
                    with st.expander("🔧 Patterns"):
                        for pattern in patterns:
                            st.write(f"• {pattern}")
