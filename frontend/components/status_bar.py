"""
frontend/components/status_bar.py

System status indicators for FastAPI Backend, FastF1 cache, and Session state.
"""

from typing import Dict, Any, Optional
import streamlit as st

def render_status_bar(
    status_info: Dict[str, Any],
    session_loaded: bool,
    summary: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render horizontal status badges matching expected production requirements.

    Expected format:
        Backend: ● Connected / ● Disconnected
        FastF1: ● Ready / ● Unavailable
        Session Data: ● 2024 Bahrain Grand Prix — Race / ● No Session Selected
    """
    is_connected = status_info.get("connected", False)
    fastf1_state = status_info.get("fastf1", "unavailable")

    if is_connected:
        backend_badge = '<span style="color:#00e676; font-weight: bold;">● Connected</span>'
    else:
        backend_badge = '<span style="color:#ff5252; font-weight: bold;">● Disconnected</span>'

    if is_connected and fastf1_state in ("ready", "cache_ready"):
        fastf1_badge = '<span style="color:#00e676; font-weight: bold;">● Ready</span>'
    else:
        fastf1_badge = '<span style="color:#888888; font-weight: bold;">● Unavailable</span>'

    if session_loaded and summary:
        year = summary.get("Year", "")
        race = summary.get("EventName", "Grand Prix")
        sess_name = summary.get("SessionName", summary.get("SessionType", "Race"))
        label = f"{year} {race} — {sess_name}".strip()
        session_badge = f'<span style="color:#00e676; font-weight: bold;">● {label}</span>'
    else:
        session_badge = '<span style="color:#ffb300; font-weight: bold;">● No Session Selected</span>'

    st.markdown(
        f"""
        <div style="background: #111; border: 1px solid #222; border-radius: 6px; padding: 0.6rem 1.2rem;
                    display: flex; gap: 2.5rem; font-size: 0.85rem; font-family: 'Inter', monospace; margin-bottom: 1rem; align-items: center;">
            <div>Backend: {backend_badge}</div>
            <div>FastF1: {fastf1_badge}</div>
            <div>Session Data: {session_badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
