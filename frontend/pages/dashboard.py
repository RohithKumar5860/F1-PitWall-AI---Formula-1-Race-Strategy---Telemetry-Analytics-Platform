"""
frontend/pages/dashboard.py

Main interactive motorsport analytics dashboard view.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List

from frontend.components.header import render_header
from frontend.components.metric_cards import render_metric_cards
from frontend.utils.formatting import format_laptime, get_compound_color


def render_dashboard_page(
    summary: Dict[str, Any],
    drivers: List[Dict[str, Any]],
    laps: List[Dict[str, Any]],
    tires: List[Dict[str, Any]],
    pitstops: List[Dict[str, Any]],
    weather: List[Dict[str, Any]],
    active_tab: str = "Dashboard",
) -> None:
    """Render full telemetry and strategy analysis dashboard."""
    render_header(summary)
    render_metric_cards(summary, drivers, laps, weather)

    st.markdown("<br>", unsafe_allow_html=True)

    # Convert laps to DataFrame for charting
    laps_df = pd.DataFrame(laps) if laps else pd.DataFrame()
    drivers_df = pd.DataFrame(drivers) if drivers else pd.DataFrame()
    weather_df = pd.DataFrame(weather) if weather else pd.DataFrame()

    # ------------------------------------------------------------------ #
    # Section: Race Overview & Classification                            #
    # ------------------------------------------------------------------ #
    if active_tab in ("Dashboard", "Drivers"):
        st.markdown("### 🏎️ Driver Classification")
        if not drivers_df.empty:
            display_cols = ["Position", "DriverCode", "FullName", "TeamName", "GridPosition", "Status", "Points"]
            valid_cols = [c for c in display_cols if c in drivers_df.columns]
            st.dataframe(
                drivers_df[valid_cols].sort_values("Position"),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No driver classification data available.")

        st.markdown("---")

    # ------------------------------------------------------------------ #
    # Section: Lap Time Analysis                                         #
    # ------------------------------------------------------------------ #
    if active_tab in ("Dashboard", "Lap Time Analysis") and not laps_df.empty:
        st.markdown("### ⏱️ Lap Time Analysis")

        # Filter out obvious outliers/in-out laps for visual clarity
        valid_laps = laps_df[laps_df["LapTimeSeconds"].notna() & (laps_df["LapTimeSeconds"] > 30)].copy()

        if not valid_laps.empty:
            all_drivers = sorted(valid_laps["Driver"].unique().tolist())
            selected_drivers = st.multiselect(
                "Select Drivers to Compare:",
                options=all_drivers,
                default=all_drivers[:5] if len(all_drivers) >= 5 else all_drivers,
            )

            filtered_laps = valid_laps[valid_laps["Driver"].isin(selected_drivers)]

            if not filtered_laps.empty:
                filtered_laps["FormattedTime"] = filtered_laps["LapTimeSeconds"].apply(format_laptime)
                fig_laps = px.line(
                    filtered_laps,
                    x="LapNumber",
                    y="LapTimeSeconds",
                    color="Driver",
                    hover_data=["Driver", "LapNumber", "FormattedTime", "Compound", "TyreLife"],
                    title="Lap Time Progression across Session",
                    labels={"LapNumber": "Lap Number", "LapTimeSeconds": "Lap Time (Seconds)"},
                    template="plotly_dark",
                )
                fig_laps.update_traces(mode="lines+markers")
                fig_laps.update_layout(
                    paper_bgcolor="#111",
                    plot_bgcolor="#161616",
                    hovermode="x unified",
                )
                st.plotly_chart(fig_laps, use_container_width=True)
            else:
                st.info("Select at least one driver to plot lap times.")

        st.markdown("---")

    # ------------------------------------------------------------------ #
    # Section: Tire Strategy Stints                                      #
    # ------------------------------------------------------------------ #
    if active_tab in ("Dashboard", "Tire Strategy") and not laps_df.empty:
        st.markdown("### 🛞 Tire Stint Timeline")

        # Calculate stint boundaries per driver
        stint_records = []
        for driver_code, d_laps in laps_df.groupby("Driver"):
            d_laps = d_laps.sort_values("LapNumber")
            for stint_id, stint_df in d_laps.groupby("Stint"):
                compound = stint_df["Compound"].iloc[0] if "Compound" in stint_df.columns else "UNKNOWN"
                start_lap = stint_df["LapNumber"].min()
                end_lap = stint_df["LapNumber"].max()
                stint_length = end_lap - start_lap + 1

                stint_records.append({
                    "Driver": driver_code,
                    "Stint": f"Stint {stint_id}",
                    "Compound": compound,
                    "StartLap": start_lap,
                    "EndLap": end_lap,
                    "StintLength": stint_length,
                })

        stints_df = pd.DataFrame(stint_records)
        if not stints_df.empty:
            fig_stints = px.bar(
                stints_df,
                x="StintLength",
                y="Driver",
                color="Compound",
                base="StartLap",
                orientation="h",
                title="Tire Stint Timeline by Driver",
                labels={"StintLength": "Laps on Compound", "StartLap": "Starting Lap"},
                color_discrete_map={
                    "SOFT": "#FF3333",
                    "MEDIUM": "#FFF000",
                    "HARD": "#FFFFFF",
                    "INTERMEDIATE": "#39B54A",
                    "WET": "#00AEEF",
                    "UNKNOWN": "#888888",
                },
                template="plotly_dark",
            )
            fig_stints.update_layout(
                paper_bgcolor="#111",
                plot_bgcolor="#161616",
                barmode="stack",
            )
            st.plotly_chart(fig_stints, use_container_width=True)

            st.markdown("#### Tire Compound Overview")
            valid_compound_laps = laps_df[laps_df["LapTimeSeconds"].notna() & (laps_df["Compound"] != "UNKNOWN")]
            if not valid_compound_laps.empty:
                comp_stats = valid_compound_laps.groupby("Compound").agg(
                    TotalLaps=("LapNumber", "count"),
                    AvgLapTimeSeconds=("LapTimeSeconds", "mean"),
                ).reset_index()

                comp_stats["AvgLapTime"] = comp_stats["AvgLapTimeSeconds"].apply(format_laptime)
                comp_stats["AvgLapTimeSeconds"] = comp_stats["AvgLapTimeSeconds"].round(3)
                st.dataframe(comp_stats[["Compound", "TotalLaps", "AvgLapTime"]], use_container_width=True, hide_index=True)
                st.caption("Note: Average lap times are descriptive and unadjusted for fuel load and track evolution.")

        st.markdown("---")

    # ------------------------------------------------------------------ #
    # Section: Pit Stops                                                 #
    # ------------------------------------------------------------------ #
    if active_tab in ("Dashboard", "Pit Stops"):
        st.markdown("### 🔧 Pit Stops & Stint Transitions")
        pitstops_df = pd.DataFrame(pitstops) if pitstops else pd.DataFrame()
        if not pitstops_df.empty:
            st.dataframe(pitstops_df, use_container_width=True, hide_index=True)
        else:
            st.info("No pit stop transitions detected for this session.")

        st.markdown("---")

    # ------------------------------------------------------------------ #
    # Section: Weather                                                   #
    # ------------------------------------------------------------------ #
    if active_tab in ("Dashboard", "Track Conditions") and not weather_df.empty:
        st.markdown("### ⛅ Track Conditions")
        c_w1, c_w2 = st.columns(2)
        with c_w1:
            fig_temp = px.line(
                weather_df,
                x="Time",
                y=["AirTemp", "TrackTemp"],
                title="Air vs Track Temperature",
                labels={"value": "Temperature (°C)", "Time": "Session Time"},
                template="plotly_dark",
            )
            fig_temp.update_layout(paper_bgcolor="#111", plot_bgcolor="#161616")
            st.plotly_chart(fig_temp, use_container_width=True)

        with c_w2:
            fig_wind = px.line(
                weather_df,
                x="Time",
                y="WindSpeed",
                title="Wind Speed Evolution",
                labels={"WindSpeed": "Wind Speed (m/s)", "Time": "Session Time"},
                template="plotly_dark",
            )
            fig_wind.update_layout(paper_bgcolor="#111", plot_bgcolor="#161616")
            st.plotly_chart(fig_wind, use_container_width=True)

        st.markdown("---")

    # ------------------------------------------------------------------ #
    # Section: Fastest Laps                                              #
    # ------------------------------------------------------------------ #
    if active_tab in ("Dashboard",) and not laps_df.empty:
        st.markdown("### ⚡ Top 10 Fastest Laps")
        valid_fastest = laps_df[laps_df["LapTimeSeconds"].notna() & (laps_df["LapTimeSeconds"] > 30)].sort_values("LapTimeSeconds").head(10).copy()
        if not valid_fastest.empty:
            valid_fastest["Rank"] = range(1, len(valid_fastest) + 1)
            valid_fastest["LapTime"] = valid_fastest["LapTimeSeconds"].apply(format_laptime)
            display_fastest = valid_fastest[["Rank", "Driver", "LapNumber", "LapTime", "Compound", "TyreLife"]]
            st.dataframe(display_fastest, use_container_width=True, hide_index=True)

        st.markdown("---")

    # ------------------------------------------------------------------ #
    # Section: Driver Comparison                                         #
    # ------------------------------------------------------------------ #
    if active_tab in ("Dashboard", "Driver Comparison") and not laps_df.empty:
        st.markdown("### ⚔️ Driver Comparison")
        all_drivers = sorted(laps_df["Driver"].unique().tolist())
        if len(all_drivers) >= 2:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                driver_a = st.selectbox("Driver A:", options=all_drivers, index=0)
            with col_d2:
                driver_b = st.selectbox("Driver B:", options=all_drivers, index=min(1, len(all_drivers)-1))

            if driver_a and driver_b:
                d_a_laps = laps_df[(laps_df["Driver"] == driver_a) & laps_df["LapTimeSeconds"].notna() & (laps_df["LapTimeSeconds"] > 30)]
                d_b_laps = laps_df[(laps_df["Driver"] == driver_b) & laps_df["LapTimeSeconds"].notna() & (laps_df["LapTimeSeconds"] > 30)]

                comp_data = {
                    "Metric": ["Fastest Lap", "Average Lap", "Total Laps", "Compounds Used"],
                    driver_a: [
                        format_laptime(d_a_laps["LapTimeSeconds"].min()) if not d_a_laps.empty else "N/A",
                        format_laptime(d_a_laps["LapTimeSeconds"].mean()) if not d_a_laps.empty else "N/A",
                        len(d_a_laps),
                        ", ".join(d_a_laps["Compound"].unique().tolist()) if not d_a_laps.empty else "N/A",
                    ],
                    driver_b: [
                        format_laptime(d_b_laps["LapTimeSeconds"].min()) if not d_b_laps.empty else "N/A",
                        format_laptime(d_b_laps["LapTimeSeconds"].mean()) if not d_b_laps.empty else "N/A",
                        len(d_b_laps),
                        ", ".join(d_b_laps["Compound"].unique().tolist()) if not d_b_laps.empty else "N/A",
                    ],
                }
                st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
