"""
frontend/pages/race_analytics.py

Advanced Race Analytics Page for F1 PitWall AI.

Includes interactive Plotly visualization for position evolution, sector delta heatmaps,
team pace box plots, stint long-run degradation curves, pit-stop timeline, and pace consistency metrics.
"""

from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from frontend.utils.formatting import format_laptime, COMPOUND_COLORS


def render_race_analytics_page(
    laps: List[Dict[str, Any]],
    drivers: List[Dict[str, Any]],
    pitstops: List[Dict[str, Any]] = None,
) -> None:
    """Render comprehensive interactive race analytics suite."""
    st.markdown("### ⏱️ Advanced Race Analytics")
    st.caption("In-depth telemetry analysis, sector heatmaps, team pace distribution, stint degradation, and consistency metrics.")

    laps_df = pd.DataFrame(laps) if laps else pd.DataFrame()
    drivers_df = pd.DataFrame(drivers) if drivers else pd.DataFrame()
    pitstops_df = pd.DataFrame(pitstops) if pitstops else pd.DataFrame()

    if laps_df.empty:
        st.info("ℹ️ No session lap data loaded. Select a season and Grand Prix above, then click **LOAD SESSION**.")
        return

    # Filter valid racing laps
    valid_laps = laps_df[
        laps_df["LapTimeSeconds"].notna() & (laps_df["LapTimeSeconds"] > 30)
    ].copy()

    if valid_laps.empty:
        st.warning("⚠️ No valid lap time records found for this session.")
        return

    # Map team names if present
    if "TeamName" not in valid_laps.columns and not drivers_df.empty and "TeamName" in drivers_df.columns:
        team_map = dict(zip(drivers_df["DriverCode"], drivers_df["TeamName"]))
        valid_laps["TeamName"] = valid_laps["Driver"].map(team_map)

    # ── Interactive Filter Controls ────────────────────────────────
    st.markdown("#### ⚙️ Filters & Selection")
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

    all_drivers = sorted(valid_laps["Driver"].unique().tolist())
    all_teams = sorted(valid_laps["TeamName"].dropna().unique().tolist()) if "TeamName" in valid_laps.columns else []
    all_stints = sorted([int(s) for s in valid_laps["Stint"].dropna().unique()]) if "Stint" in valid_laps.columns else []

    with col_f1:
        selected_drivers = st.multiselect(
            "Filter Drivers:",
            options=all_drivers,
            default=all_drivers[:6] if len(all_drivers) >= 6 else all_drivers,
            key="race_analytics_driver_filter",
        )

    with col_f2:
        selected_teams = st.multiselect(
            "Filter Constructors / Teams:",
            options=all_teams,
            default=all_teams,
            key="race_analytics_team_filter",
        )

    with col_f3:
        selected_stints = st.multiselect(
            "Filter Stints:",
            options=all_stints,
            default=all_stints,
            key="race_analytics_stint_filter",
        )

    # Apply filters
    filtered_laps = valid_laps.copy()
    if selected_drivers:
        filtered_laps = filtered_laps[filtered_laps["Driver"].isin(selected_drivers)]
    if selected_teams and "TeamName" in filtered_laps.columns:
        filtered_laps = filtered_laps[filtered_laps["TeamName"].isin(selected_teams)]
    if selected_stints and "Stint" in filtered_laps.columns:
        filtered_laps = filtered_laps[filtered_laps["Stint"].isin(selected_stints)]

    if filtered_laps.empty:
        st.warning("No lap data matches the selected filters.")
        return

    # ── KPI Summary Cards ──────────────────────────────────────────
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    fastest_lap_row = filtered_laps.sort_values("LapTimeSeconds").iloc[0]
    avg_pace_sec = filtered_laps["LapTimeSeconds"].mean()
    median_pace_sec = filtered_laps["LapTimeSeconds"].median()
    total_analyzed_laps = len(filtered_laps)

    with kpi1:
        st.metric("Fastest Lap", format_laptime(fastest_lap_row["LapTimeSeconds"]), delta=f"Driver: {fastest_lap_row['Driver']}")
    with kpi2:
        st.metric("Mean Session Pace", format_laptime(avg_pace_sec))
    with kpi3:
        st.metric("Median Pace", format_laptime(median_pace_sec))
    with kpi4:
        st.metric("Analyzed Laps", total_analyzed_laps)

    st.markdown("---")

    # ── Analytics Tabs ──────────────────────────────────────────────
    tab_prog, tab_pos, tab_teams, tab_degradation, tab_stints, tab_consistency, tab_sectors = st.tabs([
        "📈 Pace Progression",
        "🔀 Position Evolution",
        "🏎️ Team Comparison",
        "🛞 Tire Degradation",
        "📊 Long-Run Analysis",
        "🎯 Consistency Analysis",
        "🏁 Sector Heatmap",
    ])

    # 1. Pace Progression
    with tab_prog:
        st.markdown("#### Lap Time Progression & Stint Transitions")
        filtered_laps["FormattedTime"] = filtered_laps["LapTimeSeconds"].apply(format_laptime)
        fig_laps = px.line(
            filtered_laps,
            x="LapNumber", y="LapTimeSeconds", color="Driver",
            hover_data=["Driver", "LapNumber", "FormattedTime", "Compound", "TyreLife"],
            title="Lap-by-Lap Timing (Seconds)",
            labels={"LapNumber": "Lap", "LapTimeSeconds": "Lap Time (s)"},
            template="plotly_dark",
        )
        fig_laps.update_traces(mode="lines+markers", marker=dict(size=4))
        fig_laps.update_layout(
            paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
            font=dict(family="Inter"), hovermode="x unified",
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_laps, use_container_width=True)

        # Export table data
        st.download_button(
            label="💾 Export Lap Timing CSV",
            data=filtered_laps[["Driver", "LapNumber", "LapTimeSeconds", "Compound", "TyreLife", "Stint"]].to_csv(index=False),
            file_name="race_lap_times.csv",
            mime="text/csv",
        )

    # 2. Position Evolution
    with tab_pos:
        st.markdown("#### Position Evolution Throughout Race")
        pos_df = laps_df[laps_df["Position"].notna()].copy()
        if selected_drivers and not pos_df.empty:
            pos_df = pos_df[pos_df["Driver"].isin(selected_drivers)]
        if not pos_df.empty:
            fig_pos = px.line(
                pos_df,
                x="LapNumber", y="Position", color="Driver",
                title="Position Trajectory (Inverted Y-Axis)",
                labels={"LapNumber": "Lap", "Position": "Race Position"},
                template="plotly_dark",
            )
            fig_pos.update_yaxes(autorange="reversed", dtick=1)
            fig_pos.update_layout(
                paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                font=dict(family="Inter"),
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(fig_pos, use_container_width=True)
        else:
            st.info("No position telemetry available for the current selection.")

    # 3. Team Comparison
    with tab_teams:
        st.markdown("#### Team Pace Distribution & IQR Comparison")
        if "TeamName" in filtered_laps.columns and filtered_laps["TeamName"].notna().any():
            fig_team = px.box(
                filtered_laps,
                x="TeamName", y="LapTimeSeconds", color="TeamName",
                points="outliers",
                title="Constructor Pace Spread (Boxplot)",
                labels={"TeamName": "Constructor", "LapTimeSeconds": "Lap Time (s)"},
                template="plotly_dark",
            )
            fig_team.update_layout(
                paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                font=dict(family="Inter"), showlegend=False,
            )
            st.plotly_chart(fig_team, use_container_width=True)

            # Team Summary Stats Table
            team_stats = filtered_laps.groupby("TeamName").agg(
                Laps=("LapTimeSeconds", "count"),
                BestLap=("LapTimeSeconds", "min"),
                MedianPace=("LapTimeSeconds", "median"),
                MeanPace=("LapTimeSeconds", "mean"),
                StdDev=("LapTimeSeconds", "std"),
            ).reset_index()
            team_stats["BestLap"] = team_stats["BestLap"].apply(format_laptime)
            team_stats["MedianPace"] = team_stats["MedianPace"].apply(format_laptime)
            team_stats["MeanPace"] = team_stats["MeanPace"].apply(format_laptime)
            st.dataframe(team_stats.sort_values("Laps", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Constructor data not present in telemetry.")

    # 4. Tire Degradation Curves
    with tab_degradation:
        st.markdown("#### Tire Compound Degradation Curves")
        if "Compound" in filtered_laps.columns and "TyreLife" in filtered_laps.columns:
            deg_laps = filtered_laps[
                filtered_laps["Compound"].isin(["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]) &
                (filtered_laps["TyreLife"] > 0)
            ].copy()
            if not deg_laps.empty:
                comp_deg = deg_laps.groupby(["Compound", "TyreLife"])["LapTimeSeconds"].mean().reset_index()
                fig_deg = px.line(
                    comp_deg,
                    x="TyreLife", y="LapTimeSeconds", color="Compound",
                    color_discrete_map=COMPOUND_COLORS,
                    title="Average Lap Time vs Tire Life (Laps)",
                    labels={"TyreLife": "Tire Life (Laps)", "LapTimeSeconds": "Mean Lap Time (s)"},
                    template="plotly_dark",
                )
                fig_deg.update_traces(mode="lines+markers")
                fig_deg.update_layout(
                    paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                    font=dict(family="Inter"),
                )
                st.plotly_chart(fig_deg, use_container_width=True)
            else:
                st.info("Insufficient tire life telemetry for degradation curves.")
        else:
            st.info("Tire compound telemetry unavailable.")

    # 5. Long-Run Stint Analysis
    with tab_stints:
        st.markdown("#### Stint Pace & Long-Run Breakdown")
        if "Stint" in filtered_laps.columns:
            stint_summary = filtered_laps.groupby(["Driver", "Stint", "Compound"]).agg(
                StintLaps=("LapNumber", "count"),
                StartLap=("LapNumber", "min"),
                EndLap=("LapNumber", "max"),
                AvgPace=("LapTimeSeconds", "mean"),
                BestLap=("LapTimeSeconds", "min"),
            ).reset_index()

            stint_summary["AvgPaceFormatted"] = stint_summary["AvgPace"].apply(format_laptime)
            stint_summary["BestLapFormatted"] = stint_summary["BestLap"].apply(format_laptime)

            fig_stint = px.bar(
                stint_summary,
                x="Driver", y="StintLaps", color="Compound",
                color_discrete_map=COMPOUND_COLORS,
                title="Stint Lengths & Compound Usage",
                labels={"StintLaps": "Laps Completed"},
                template="plotly_dark",
            )
            fig_stint.update_layout(
                paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig_stint, use_container_width=True)

            display_cols = ["Driver", "Stint", "Compound", "StintLaps", "StartLap", "EndLap", "AvgPaceFormatted", "BestLapFormatted"]
            st.dataframe(stint_summary[display_cols].sort_values(["Driver", "Stint"]), use_container_width=True, hide_index=True)
        else:
            st.info("Stint telemetry unavailable.")

    # 6. Driver Consistency Analysis
    with tab_consistency:
        st.markdown("#### Driver Lap Time Consistency & Variance")
        cons_list = []
        for drv, group in filtered_laps.groupby("Driver"):
            times = group["LapTimeSeconds"].values
            if len(times) >= 3:
                med = np.median(times)
                std = np.std(times)
                within_half_sec = np.sum(np.abs(times - med) <= 0.5) / len(times) * 100
                cons_list.append({
                    "Driver": drv,
                    "TotalLaps": len(times),
                    "MedianPace": round(med, 3),
                    "StdDev (s)": round(std, 3),
                    "Consistency Rating (%)": round(within_half_sec, 1),
                })

        if cons_list:
            cons_df = pd.DataFrame(cons_list).sort_values("StdDev (s)")
            fig_cons = px.bar(
                cons_df,
                x="Driver", y="Consistency Rating (%)",
                color="StdDev (s)",
                color_continuous_scale="Reds_r",
                title="Driver Lap Time Consistency (% Laps within ±0.5s of Median)",
                template="plotly_dark",
            )
            fig_cons.update_layout(
                paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                font=dict(family="Inter"), coloraxis_showscale=False,
            )
            st.plotly_chart(fig_cons, use_container_width=True)
            st.dataframe(cons_df, use_container_width=True, hide_index=True)
        else:
            st.info("Insufficient lap data for consistency analysis.")

    # 7. Sector Delta Heatmap
    with tab_sectors:
        st.markdown("#### Sector Time Analysis & Best Sector Deltas")
        sec_laps = filtered_laps[
            filtered_laps["Sector1Seconds"].notna() &
            filtered_laps["Sector2Seconds"].notna() &
            filtered_laps["Sector3Seconds"].notna()
        ].copy()

        if not sec_laps.empty:
            sec_agg = sec_laps.groupby("Driver").agg(
                BestS1=("Sector1Seconds", "min"),
                BestS2=("Sector2Seconds", "min"),
                BestS3=("Sector3Seconds", "min"),
            ).reset_index()

            min_s1 = sec_agg["BestS1"].min()
            min_s2 = sec_agg["BestS2"].min()
            min_s3 = sec_agg["BestS3"].min()

            sec_agg["DeltaS1"] = (sec_agg["BestS1"] - min_s1).round(3)
            sec_agg["DeltaS2"] = (sec_agg["BestS2"] - min_s2).round(3)
            sec_agg["DeltaS3"] = (sec_agg["BestS3"] - min_s3).round(3)
            sec_agg["TheoreticalBest"] = (sec_agg["BestS1"] + sec_agg["BestS2"] + sec_agg["BestS3"]).round(3)

            # Heatmap of sector deltas
            z_data = sec_agg[["DeltaS1", "DeltaS2", "DeltaS3"]].values
            fig_heat = go.Figure(data=go.Heatmap(
                z=z_data,
                x=["Sector 1 Delta (s)", "Sector 2 Delta (s)", "Sector 3 Delta (s)"],
                y=sec_agg["Driver"],
                colorscale="Reds",
                reversescale=True,
                text=z_data,
                texttemplate="%{text:.3f}",
            ))
            fig_heat.update_layout(
                title="Best Sector Time Deltas Relative to Session Fastest (Heatmap)",
                template="plotly_dark",
                paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig_heat, use_container_width=True)
            st.dataframe(sec_agg.sort_values("TheoreticalBest"), use_container_width=True, hide_index=True)
        else:
            st.info("Sector timing data not available for this session.")
