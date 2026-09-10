"""
frontend/pages/pitstops.py

Pit Stops page — pit history table, compound transitions, pit timeline.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any

from frontend.utils.formatting import COMPOUND_COLORS


def render_pitstops_page(
    pitstops: List[Dict[str, Any]],
    laps: List[Dict[str, Any]],
) -> None:
    """Render pit stop analysis and stint transitions."""
    st.markdown("### 🔧 Pit Stops & Stint Transitions")

    pitstops_df = pd.DataFrame(pitstops) if pitstops else pd.DataFrame()

    if pitstops_df.empty:
        st.info("No pit stop transitions detected for this session.")
        return

    # ── Pit Stop Summary ───────────────────────────────────────────
    st.markdown("#### Pit Stop History")
    display_cols = ["Driver", "PitLap", "Stint", "IncomingCompound", "OutgoingCompound"]
    valid_cols = [c for c in display_cols if c in pitstops_df.columns]
    st.dataframe(
        pitstops_df[valid_cols].sort_values(["Driver", "PitLap"]),
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")

    # ── Pit Stop Count per Driver ──────────────────────────────────
    st.markdown("#### Pit Stop Count by Driver")
    pit_counts = pitstops_df.groupby("Driver").size().reset_index(name="PitStops")
    pit_counts = pit_counts.sort_values("PitStops", ascending=True)

    fig_counts = px.bar(
        pit_counts, x="PitStops", y="Driver", orientation="h",
        title="Number of Pit Stops per Driver",
        color="PitStops",
        color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
        template="plotly_dark",
    )
    fig_counts.update_layout(
        paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
        font=dict(family="Inter"), showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_counts, use_container_width=True)

    st.markdown("---")

    # ── Compound Transitions ───────────────────────────────────────
    st.markdown("#### Compound Transitions")
    if "IncomingCompound" in pitstops_df.columns and "OutgoingCompound" in pitstops_df.columns:
        transitions = pitstops_df.groupby(
            ["IncomingCompound", "OutgoingCompound"]
        ).size().reset_index(name="Count")

        if not transitions.empty:
            fig_sankey = go.Figure(go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=15, thickness=20,
                    line=dict(color="#333", width=0.5),
                    label=list(set(transitions["IncomingCompound"].tolist() + transitions["OutgoingCompound"].tolist())),
                    color="#E10600",
                ),
                link=dict(
                    source=[list(set(transitions["IncomingCompound"].tolist() + transitions["OutgoingCompound"].tolist())).index(x) for x in transitions["IncomingCompound"]],
                    target=[list(set(transitions["IncomingCompound"].tolist() + transitions["OutgoingCompound"].tolist())).index(x) for x in transitions["OutgoingCompound"]],
                    value=transitions["Count"].tolist(),
                    color="rgba(225, 6, 0, 0.3)",
                ),
            ))
            fig_sankey.update_layout(
                title="Compound Transition Flow",
                template="plotly_dark",
                paper_bgcolor="#0d0d0d",
                font=dict(family="Inter", color="#f0f0f0"),
            )
            st.plotly_chart(fig_sankey, use_container_width=True)

        # Transition table
        st.dataframe(transitions, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Pit Window Distribution ────────────────────────────────────
    st.markdown("#### Pit Stop Lap Distribution")
    if "PitLap" in pitstops_df.columns:
        fig_hist = px.histogram(
            pitstops_df, x="PitLap", nbins=20,
            title="When Drivers Pitted (Lap Distribution)",
            labels={"PitLap": "Pit Lap", "count": "Number of Stops"},
            template="plotly_dark",
            color_discrete_sequence=["#E10600"],
        )
        fig_hist.update_layout(
            paper_bgcolor="#0d0d0d", plot_bgcolor="#141414",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig_hist, use_container_width=True)
