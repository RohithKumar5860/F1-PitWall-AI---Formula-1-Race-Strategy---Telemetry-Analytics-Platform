"""
frontend/pages/drivers.py

Driver Classification page — sortable results table with team colors.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any


def render_drivers_page(
    drivers: List[Dict[str, Any]],
    laps: List[Dict[str, Any]],
) -> None:
    """Render driver classification with race statistics."""
    st.markdown("### 🏎️ Driver Classification")

    if not drivers:
        st.info("No driver data available. Load a session first.")
        return

    drivers_df = pd.DataFrame(drivers)
    laps_df = pd.DataFrame(laps) if laps else pd.DataFrame()

    # Add fastest lap per driver from laps data
    if not laps_df.empty and "LapTimeSeconds" in laps_df.columns:
        valid = laps_df[laps_df["LapTimeSeconds"].notna() & (laps_df["LapTimeSeconds"] > 30)]
        if not valid.empty:
            fastest = valid.groupby("Driver")["LapTimeSeconds"].min().reset_index()
            fastest.columns = ["DriverCode", "FastestLap"]
            from frontend.utils.formatting import format_laptime
            fastest["FastestLapFormatted"] = fastest["FastestLap"].apply(format_laptime)
            drivers_df = drivers_df.merge(fastest, on="DriverCode", how="left")

    display_cols = ["Position", "DriverCode", "FullName", "TeamName", "GridPosition", "Status", "Points"]
    if "FastestLapFormatted" in drivers_df.columns:
        display_cols.append("FastestLapFormatted")

    valid_cols = [c for c in display_cols if c in drivers_df.columns]

    if "Position" in drivers_df.columns:
        drivers_df = drivers_df.sort_values("Position")

    st.dataframe(drivers_df[valid_cols], use_container_width=True, hide_index=True)

    # Driver count and DNF summary
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    total = len(drivers_df)
    finished = len(drivers_df[drivers_df["Status"].str.contains("Finished|\\+", na=False, regex=True)]) if "Status" in drivers_df.columns else total
    dnf = total - finished

    with c1:
        st.metric("Total Drivers", total)
    with c2:
        st.metric("Finished", finished)
    with c3:
        st.metric("DNF / Retired", dnf)
