"""Requirements input page."""

from __future__ import annotations

import streamlit as st
from typing import Dict, Optional


def render(predefined: Optional[Dict[str, str]] = None) -> None:  # noqa: D401
    """Render the Requirements step UI.

    Parameters
    ----------
    predefined:
        Mapping of problem name → requirements loaded from the DB. When provided the
        user can pick a predefined problem and then edit/overwrite it in the text
        area.
    """

    st.markdown('<div class="section-header">📋 System Requirements</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Predefined problems selector (if available)
    # ---------------------------------------------------------------------
    if predefined:
        problem_names = ["-- Select --"] + sorted(predefined.keys())
        selected = st.selectbox("Choose a predefined design problem:", problem_names, index=0)
        if selected not in ("", "-- Select --") and st.button("Load Problem"):
            st.session_state.requirements = predefined[selected]
            st.session_state.current_problem = selected
            st.success(f"Loaded requirements for '{selected}'. You can edit below.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Define / Edit Requirements**")
        requirements_text = st.text_area(
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
            st.session_state.requirements = requirements_text
            st.success("Requirements saved! Move to Class Design step.")

    with col2:
        if st.session_state.get("requirements"):
            st.markdown("**Current Requirements:**")
            req = st.session_state.requirements
            st.info(req[:300] + "..." if len(req) > 300 else req)
