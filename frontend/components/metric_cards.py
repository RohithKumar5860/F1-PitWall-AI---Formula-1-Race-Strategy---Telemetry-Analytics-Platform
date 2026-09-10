"""
frontend/components/metric_cards.py

KPI Metric cards component displaying real session statistics.
"""

import streamlit as st
from typing import Dict, Any, List
from frontend.utils.formatting import format_laptime


def render_metric_cards(summary: Dict[str, Any], drivers: List[Dict[str, Any]], laps: List[Dict[str, Any]], weather: List[Dict[str, Any]]) -> None:
    """Render top KPI metric cards calculated from actual session data."""
    driver_count = summary.get("DriverCount", len(drivers))
    lap_count = summary.get("LapCount", len(laps))

    # Find fastest valid lap
    fastest_lap_sec = None
    fastest_driver = "N/A"
    available_compounds = set()

    for lap in laps:
        comp = lap.get("Compound")
        if comp and comp != "UNKNOWN":
            available_compounds.add(comp)
        
        l_sec = lap.get("LapTimeSeconds")
        if l_sec and l_sec > 0:
            if fastest_lap_sec is None or l_sec < fastest_lap_sec:
                fastest_lap_sec = l_sec
                fastest_driver = lap.get("Driver", "N/A")

    fastest_str = format_laptime(fastest_lap_sec)
    compounds_str = " / ".join(sorted(list(available_compounds))) if available_compounds else "N/A"

    # Latest weather observation
    track_temp = "N/A"
    if weather and len(weather) > 0:
        last_w = weather[-1]
        if last_w.get("TrackTemp") is not None:
            track_temp = f"{last_w.get('TrackTemp')} °C"

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("DRIVERS", driver_count)
    with c2:
        st.metric("TOTAL LAPS", lap_count)
    with c3:
        st.metric("FASTEST LAP", fastest_str)
    with c4:
        st.metric("FASTEST DRIVER", fastest_driver)
    with c5:
        st.metric("TRACK TEMP", track_temp)
