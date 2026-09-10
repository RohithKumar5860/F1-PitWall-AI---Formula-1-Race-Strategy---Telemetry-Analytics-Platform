"""
frontend/components/sidebar.py

Sidebar navigation component.
"""

import streamlit as st

def render_sidebar() -> str:
    """Render sidebar and return selected page name."""
    with st.sidebar:
        st.markdown(
            """
            <div style="font-weight: 900; font-size: 1.3rem; color: #E10600; margin-bottom: 0.2rem;">
                🏎️ F1 PITWALL AI
            </div>
            <div style="font-size: 0.75rem; color: #888888; margin-bottom: 1rem;">
                AI-Assisted Decision Support System
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown("**NAVIGATION**")

        pages = [
            ("📊 Dashboard", "Dashboard"),
            ("🏎️ Driver Classification", "Drivers"),
            ("⏱️ Lap Time Analysis", "Lap Time Analysis"),
            ("🛞 Tire Strategy", "Tire Strategy"),
            ("🔧 Pit Stops", "Pit Stops"),
            ("⛅ Track Conditions", "Track Conditions"),
            ("⚔️ Driver Comparison", "Driver Comparison"),
            ("🤖 Strategy AI", "Strategy AI"),
            ("🎮 What-If Simulator", "What-If Simulator"),
            ("🔐 User Auth", "Auth"),
            ("🛠️ System Diagnostics", "Diagnostics"),
            ("ℹ️ About", "About"),
        ]

        if "active_page" not in st.session_state:
            st.session_state["active_page"] = "Dashboard"

        for label, page_id in pages:
            if st.button(label, key=f"btn_{page_id}", use_container_width=True):
                st.session_state["active_page"] = page_id

        st.markdown("---")
        st.caption("F1 PitWall AI v1.0.0 · Historical Data Analytics")
        return st.session_state["active_page"]

