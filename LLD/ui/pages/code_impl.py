"""Code Implementation step page."""

import streamlit as st


def render() -> None:
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
