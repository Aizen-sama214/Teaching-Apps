"""Requirements input page."""

from __future__ import annotations

import streamlit as st
from typing import Dict, Optional

# Local imports
from LLD.persistence import database as db_helpers


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

    # ------------------------------------------------------------------
    # Problem selector / creator
    # ------------------------------------------------------------------

    new_problem_name: str = ""

    if predefined:
        # Add a special option to let users opt-in for creating a new problem.
        problem_names = ["-- Select --", "-- New Problem --"] + sorted(predefined.keys())
        selected = st.selectbox(
            "Choose a predefined design problem:", problem_names, index=0
        )

        # Existing problem chosen → load its requirements.
        if selected not in ("", "-- Select --", "-- New Problem --") and st.button(
            "Load Problem"
        ):
            st.session_state.requirements = predefined[selected]
            st.session_state.current_problem = selected
            st.success(f"Loaded requirements for '{selected}'. You can edit below.")

        # If the user opted for a *new* problem we display a text_input for its name.
        if selected == "-- New Problem --":
            new_problem_name = st.text_input(
                "Enter a name for the new problem:",
                value=st.session_state.get("current_problem", ""),
            )
    else:
        # No predefined problems available → always ask for a name.
        new_problem_name = st.text_input(
            "Enter a name for the design problem:",
            value=st.session_state.get("current_problem", ""),
        )

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
            # Determine the problem name: either an existing selection or the new one.
            problem_name = (
                st.session_state.get("current_problem")
                if st.session_state.get("current_problem") and st.session_state.get("current_problem") not in ("-- Select --", "-- New Problem --")
                else new_problem_name.strip()
            )

            if not problem_name:
                st.error("Please provide a problem name before saving.")
            else:
                # Persist to session-state and DB
                st.session_state.requirements = requirements_text
                st.session_state.current_problem = problem_name

                try:
                    db_helpers.save_problem(problem_name, requirements_text)

                    # Update the in-memory cache so that the dropdown refreshes immediately
                    if predefined is not None:
                        predefined[problem_name] = requirements_text

                    st.success(
                        f"Requirements for '{problem_name}' saved! Move to Class Design step."
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed to save problem: {exc}")

    with col2:
        if st.session_state.get("requirements"):
            st.markdown("**Current Requirements:**")
            req = st.session_state.requirements
            st.info(req[:300] + "..." if len(req) > 300 else req)
