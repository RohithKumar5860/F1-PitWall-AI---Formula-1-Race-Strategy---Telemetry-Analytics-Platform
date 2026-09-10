"""
frontend/components/header.py

Header component for F1 PitWall AI.
"""

import streamlit as st

def render_header(summary_data: dict = None) -> None:
    """Render motorsport header banner."""
    st.markdown(
        """
        <div style="padding: 1.2rem 0; border-bottom: 1px solid #2a2a2a; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h1 style="margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: -0.5px;
                               background: linear-gradient(90deg, #E10600 0%, #FF5252 100%);
                               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        F1 PITWALL AI
                    </h1>
                    <div style="font-size: 0.95rem; color: #aaaaaa; font-weight: 400; margin-top: 2px;">
                        Intelligent Race Strategy & Decision Support
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if summary_data:
        event = summary_data.get("EventName", "F1 Grand Prix")
        circuit = summary_data.get("Circuit", "Circuit")
        country = summary_data.get("Country", "")
        session = summary_data.get("SessionName", "Session")
        year = summary_data.get("Year", "")

        st.markdown(
            f"""
            <div style="background: #141414; border: 1px solid #2a2a2a; border-left: 4px solid #E10600;
                        border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 1.5rem; display: flex; gap: 2rem;">
                <div><span style="color:#777; font-size:0.75rem; text-transform:uppercase;">SEASON</span><br><strong>{year}</strong></div>
                <div><span style="color:#777; font-size:0.75rem; text-transform:uppercase;">GRAND PRIX</span><br><strong>{event}</strong></div>
                <div><span style="color:#777; font-size:0.75rem; text-transform:uppercase;">SESSION</span><br><strong>{session}</strong></div>
                <div><span style="color:#777; font-size:0.75rem; text-transform:uppercase;">LOCATION</span><br><strong>{circuit}, {country}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
