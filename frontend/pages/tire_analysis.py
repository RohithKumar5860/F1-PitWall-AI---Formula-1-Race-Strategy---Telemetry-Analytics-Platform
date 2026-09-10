"""
frontend/pages/tire_analysis.py

Tire Analysis page — stint timeline, compound usage, avg lap by compound,
tire life distribution.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any

from frontend.utils.formatting import format_laptime, COMPOUND_COLORS


def render_tire_analysis_page(
    laps: List[Dict[str, Any]],
    tires: List[Dict[str, Any]],
) -> None:
    """Render tire strategy and degradation analysis."""
    st.markdown("### 🛞 Tire Analysis")

    laps_df = pd.DataFrame(laps) if laps else pd.DataFrame()

    if laps_df.empty:
        st.info("No lap data available. Load a session first.")
        return

    # ── Stint Timeline ─────────────────────────────────────────────
    st.markdown("#### Stint Timeline")

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
                "Stint": f"Stint {int(stint_id)}" if pd.notna(stint_id) else "Stint 1",
                "Compound": compound if pd.notna(compound) else "UNKNOWN",
                "StartLap": start_lap,
                "EndLap": end_lap,
                "StintLength": stint_length,
            })

    stints_df = pd.DataFrame(stint_records)

    if not stints_df.empty:
        fig_stints = px.bar(
            stints_df,
            x="StintLength", y="Driver", color="Compound",
            base="StartLap", orientation="h",
            title="Tire Stint Timeline by Driver",
            labels={"StintLength": "Laps on Compound", "StartLap": "Starting Lap"},
            color_discrete_map=COMPOUND_COLORS,
            template="plotly_dark",
            hover_data=["Compound", "StartLap", "EndLap", "StintLength"],
        )
        fig_stints.update_layout(
            paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
            barmode="stack", font=dict(family="Inter"),
            yaxis=dict(categoryorder="category ascending"),
        )
        st.plotly_chart(fig_stints, use_container_width=True)

    st.markdown("---")

    # ── Compound Usage Distribution ────────────────────────────────
    st.markdown("#### Compound Usage Distribution")
    valid_compound = laps_df[laps_df["Compound"].notna() & (laps_df["Compound"] != "UNKNOWN")]

    if not valid_compound.empty:
        compound_counts = valid_compound.groupby("Compound").size().reset_index(name="TotalLaps")

        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                compound_counts, values="TotalLaps", names="Compound",
                title="Compound Distribution (Total Laps)",
                color="Compound", color_discrete_map=COMPOUND_COLORS,
                template="plotly_dark",
            )
            fig_pie.update_layout(
                paper_bgcolor="#0d0d0d", font=dict(family="Inter"),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            fig_bar = px.bar(
                compound_counts, x="Compound", y="TotalLaps",
                title="Laps per Compound",
                color="Compound", color_discrete_map=COMPOUND_COLORS,
                template="plotly_dark",
            )
            fig_bar.update_layout(
                paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                font=dict(family="Inter"), showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ── Average Lap Time by Compound ───────────────────────────────
    st.markdown("#### Average Lap Time by Compound")
    valid_laps = laps_df[
        laps_df["LapTimeSeconds"].notna() &
        (laps_df["LapTimeSeconds"] > 30) &
        laps_df["Compound"].notna() &
        (laps_df["Compound"] != "UNKNOWN")
    ]

    if not valid_laps.empty:
        comp_stats = valid_laps.groupby("Compound").agg(
            TotalLaps=("LapNumber", "count"),
            AvgLapTimeSeconds=("LapTimeSeconds", "mean"),
            MinLapTimeSeconds=("LapTimeSeconds", "min"),
            MaxLapTimeSeconds=("LapTimeSeconds", "max"),
        ).reset_index()

        comp_stats["AvgLapTime"] = comp_stats["AvgLapTimeSeconds"].apply(format_laptime)
        comp_stats["BestLapTime"] = comp_stats["MinLapTimeSeconds"].apply(format_laptime)
        comp_stats = comp_stats.round(3)

        st.dataframe(
            comp_stats[["Compound", "TotalLaps", "AvgLapTime", "BestLapTime"]],
            use_container_width=True, hide_index=True,
        )
        st.caption("Note: Average lap times are descriptive and unadjusted for fuel load and track evolution.")

    st.markdown("---")

    # ── Tire Life Distribution ─────────────────────────────────────
    st.markdown("#### Tire Life Distribution")
    if not stints_df.empty:
        fig_box = px.box(
            stints_df, x="Compound", y="StintLength",
            color="Compound", color_discrete_map=COMPOUND_COLORS,
            title="Stint Length Distribution by Compound",
            labels={"StintLength": "Stint Length (Laps)"},
            template="plotly_dark",
        )
        fig_box.update_layout(
            paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
            font=dict(family="Inter"), showlegend=False,
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Degradation Curves ─────────────────────────────────────────
    st.markdown("#### Tire Degradation Curves")
    if not valid_laps.empty and "TyreLife" in valid_laps.columns:
        deg_data = valid_laps[valid_laps["TyreLife"].notna()].copy()
        if not deg_data.empty:
            fig_deg = px.scatter(
                deg_data, x="TyreLife", y="LapTimeSeconds",
                color="Compound", color_discrete_map=COMPOUND_COLORS,
                title="Lap Time vs Tire Age",
                labels={"TyreLife": "Tire Age (Laps)", "LapTimeSeconds": "Lap Time (s)"},
                template="plotly_dark", opacity=0.5,
                trendline="lowess",
            )
            fig_deg.update_layout(
                paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig_deg, use_container_width=True)
