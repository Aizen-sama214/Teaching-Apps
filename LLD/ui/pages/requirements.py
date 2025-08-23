"""Requirements input page."""

import streamlit as st


def render() -> None:
    """Render the Requirements step UI."""

    st.markdown('<div class="section-header">📋 System Requirements</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Teacher Input: Define the system requirements**")
        requirements = st.text_area(
            "Enter system requirements:",
            value=st.session_state.get("requirements", ""),
            height=300,
            placeholder=(
                """Example: Design a Parking Lot System
- The parking lot has multiple levels
- Each level has parking spots of different types (compact, large, handicapped)
- Vehicles can be cars, motorcycles, or trucks
- The system should track availability and manage parking/unparking
- Payment processing for parking fees
- Real-time spot availability display"""
            ),
        )

        if st.button("Save Requirements", type="primary"):
            st.session_state.requirements = requirements
            st.success("Requirements saved! Move to Class Design step.")

    with col2:
        if st.session_state.get("requirements"):
            st.markdown("**Current Requirements:**")
            req = st.session_state.requirements
            st.info(req[:300] + "..." if len(req) > 300 else req)
