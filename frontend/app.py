"""
frontend/app.py

F1 PitWall AI — Main Streamlit Application Entry Point.

Run with:
    streamlit run frontend/app.py
"""

import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from frontend.utils.api_client import (
    get_backend_status,
    get_seasons,
    get_schedule,
    get_session_summary,
    get_drivers,
    get_laps,
    get_tires,
    get_pitstops,
    get_weather,
)
from frontend.components.sidebar import render_sidebar
from frontend.components.status_bar import render_status_bar
from frontend.pages.dashboard import render_dashboard_page
from frontend.pages.race_analytics import render_race_analytics_page
from frontend.pages.about import render_about_page
from frontend.pages.strategy_ai import render_strategy_ai_page
from frontend.pages.simulator import render_simulator_page
from frontend.pages.auth_ui import render_auth_page
from frontend.pages.diagnostics import render_diagnostics_page

# Pages that use the race analytics renderer
RACE_ANALYTICS_PAGES = {
    "Lap Time Analysis",
    "Tire Strategy",
    "Pit Stops",
    "Track Conditions",
    "Driver Comparison",
    "Drivers",
}

# ------------------------------------------------------------------ #
# Page configuration & Styling                                         #
# ------------------------------------------------------------------ #

st.set_page_config(
    page_title="F1 PitWall AI",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: #0d0d0d;
        color: #f0f0f0;
    }
    hr { border-color: #2a2a2a; }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #E10600 !important;
    }
    section[data-testid="stSidebar"] {
        background: #0a0a0a;
        border-right: 1px solid #222;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ #
# Session State Initialization                                         #
# ------------------------------------------------------------------ #

if "loaded_session" not in st.session_state:
    st.session_state["loaded_session"] = False
    st.session_state["summary"] = {}
    st.session_state["drivers"] = []
    st.session_state["laps"] = []
    st.session_state["tires"] = []
    st.session_state["pitstops"] = []
    st.session_state["weather"] = []


# ------------------------------------------------------------------ #
# Sidebar & Navigation                                                 #
# ------------------------------------------------------------------ #

active_page = render_sidebar()
status_info = get_backend_status()
backend_online = status_info["connected"]

# ------------------------------------------------------------------ #
# Global Race Selector Header                                          #
# ------------------------------------------------------------------ #

st.markdown("### 🔍 Session Selector")

col_s1, col_s2, col_s3, col_s4 = st.columns([1, 2, 1, 1])

with col_s1:
    available_seasons = get_seasons() if backend_online else list(range(2018, 2026))
    selected_year = st.selectbox("Season:", options=sorted(available_seasons, reverse=True), index=1 if len(available_seasons) > 1 else 0)

with col_s2:
    schedule = get_schedule(selected_year) if backend_online else []
    event_names = [e["EventName"] for e in schedule] if schedule else ["Monaco Grand Prix", "Bahrain Grand Prix", "British Grand Prix"]
    selected_race = st.selectbox("Grand Prix:", options=event_names)

with col_s3:
    session_options = ["R", "Q", "FP1", "FP2", "FP3", "S", "SQ"]
    selected_session = st.selectbox("Session:", options=session_options, index=0)

with col_s4:
    st.markdown("<br>", unsafe_allow_html=True)
    load_btn = st.button("🚀 LOAD SESSION", type="primary", use_container_width=True)

# Status indicators
render_status_bar(
    status_info=status_info,
    session_loaded=st.session_state["loaded_session"],
    summary=st.session_state.get("summary"),
)

# ------------------------------------------------------------------ #
# Data Loading Handler                                                 #
# ------------------------------------------------------------------ #

if load_btn:
    if not backend_online:
        st.error("❌ FastAPI backend is offline. Please start the backend service first (`uvicorn backend.main:app --reload`).")
    else:
        with st.spinner(f"Loading {selected_year} {selected_race} ({selected_session}) data from FastF1..."):
            try:
                summary = get_session_summary(selected_year, selected_race, selected_session)
                drivers = get_drivers(selected_year, selected_race, selected_session)
                laps = get_laps(selected_year, selected_race, selected_session)
                tires = get_tires(selected_year, selected_race, selected_session)
                pitstops = get_pitstops(selected_year, selected_race, selected_session)
                weather = get_weather(selected_year, selected_race, selected_session)

                st.session_state["summary"] = summary
                st.session_state["drivers"] = drivers
                st.session_state["laps"] = laps
                st.session_state["tires"] = tires
                st.session_state["pitstops"] = pitstops
                st.session_state["weather"] = weather
                st.session_state["loaded_session"] = True

                st.success(f"Successfully loaded {selected_race} ({selected_session}) session!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load session: {str(e)}")

# ------------------------------------------------------------------ #
# Page Content Renderer                                                #
# ------------------------------------------------------------------ #

st.markdown("---")

if active_page == "About":
    render_about_page()
elif active_page == "Strategy AI":
    render_strategy_ai_page()
elif active_page == "What-If Simulator":
    render_simulator_page()
elif active_page == "Auth":
    render_auth_page()
elif active_page == "Diagnostics":
    render_diagnostics_page()
elif active_page in RACE_ANALYTICS_PAGES:
    # Dedicated race analytics pages (Lap Time Analysis, Tire Strategy, etc.)
    if st.session_state["loaded_session"]:
        render_race_analytics_page(
            laps=st.session_state["laps"],
            drivers=st.session_state["drivers"],
            pitstops=st.session_state["pitstops"],
        )
    else:
        st.info("👈 Select a Season, Grand Prix, and Session above, then click **LOAD SESSION** to view analytics.")
else:
    # Dashboard (default) and any unmatched pages
    if st.session_state["loaded_session"]:
        render_dashboard_page(
            summary=st.session_state["summary"],
            drivers=st.session_state["drivers"],
            laps=st.session_state["laps"],
            tires=st.session_state["tires"],
            pitstops=st.session_state["pitstops"],
            weather=st.session_state["weather"],
            active_tab=active_page,
        )
    else:
        st.info("👈 Select a Season, Grand Prix, and Session above, then click **LOAD SESSION** to view race analytics.")

