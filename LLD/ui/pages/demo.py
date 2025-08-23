"""Demo & Testing step page."""

import streamlit as st
import textwrap


def render() -> None:
    if not st.session_state.class_designs:
        st.warning("Please design and implement classes first!")
        st.stop()

    implemented_classes = {
        name: design
        for name, design in st.session_state.class_designs.items()
        if design.code
    }
    if not implemented_classes:
        st.warning("No classes have been implemented yet!")
        st.stop()

    st.markdown('<div class="section-header">🧪 Demo & Testing</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("**Create Demo Class:**")
        demo_code_template = textwrap.dedent('''\
            class Demo:
                """Demonstration class to show how all classes interact"""

                def __init__(self):
                    # Initialize demo environment
                    pass

                def run_demo(self):
                    """Main demo method - shows class interactions"""
                    print("=== System Demo ===")
                    # TODO: Create instances of your classes
                    # TODO: Demonstrate their interactions
                    # TODO: Show the system working end-to-end
                    print("Demo completed!")

                def test_individual_classes(self):
                    """Test each class individually"""
                    print("=== Individual Class Tests ===")
                    # TODO: Test each class's methods
                    print("All tests completed!")

            # Uncomment to run the demo
            # if __name__ == "__main__":
            #     demo = Demo()
            #     demo.run_demo()
            #     demo.test_individual_classes()
            ''')
        demo_code = st.text_area(
            "Demo Implementation:",
            value=demo_code_template,
            height=400,
            help="Create a demo class that shows how all your classes work together",
        )
        if st.button("Run Demo", type="primary"):
            try:
                exec_globals = {}
                for name, design in implemented_classes.items():
                    exec(design.code, exec_globals)
                exec(demo_code, exec_globals)
                if "Demo" in exec_globals:
                    demo_instance = exec_globals["Demo"]()
                    st.success("✅ Demo code executed successfully!")
                    st.code("Demo would run here - output would be displayed", language="text")
                else:
                    st.warning("Demo class not found in code")
            except Exception as e:
                st.error(f"Error executing demo: {str(e)}")

    with col2:
        st.markdown("**Class Summary:**")
        for name, design in implemented_classes.items():
            with st.expander(f"📦 {name}"):
                st.write(f"**Methods:** {len(design.methods)}")
                st.write(f"**Attributes:** {len(design.attributes)}")
                st.write(f"**Code Lines:** {len(design.code.split(chr(10)))}")

        st.markdown("**System Metrics:**")
        total_classes = len(st.session_state.class_designs)
        implemented = len(implemented_classes)
        total_methods = sum(len(d.methods) for d in st.session_state.class_designs.values())
        st.metric("Total Classes Designed", total_classes)
        st.metric("Classes Implemented", f"{implemented}/{total_classes}")
        st.metric("Total Methods", total_methods)
        if implemented == total_classes:
            st.success("🎉 All classes implemented!")
        else:
            st.warning(f"{total_classes - implemented} classes still need implementation")
