"""
frontend/pages/simulator.py

What-If Race Strategy Simulator page.
Calls FastAPI backend POST /simulation/compare endpoint to compare two strategy options.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from typing import Dict, Any

from backend.utils.config import settings

BASE_URL = settings.BACKEND_URL


def render_simulator_page() -> None:
    """Render interactive What-If Strategy Simulator page."""
    st.markdown("### 🎮 What-If Strategy Simulator")
    st.caption("Simulate and compare two race strategy scenarios side-by-side.")

    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
        circuit = st.selectbox("Circuit:", options=[
            "Monaco Grand Prix", "Bahrain Grand Prix", "Silverstone Circuit", "Spa-Francorchamps"
        ], key="sim_circuit")
    with col_cfg2:
        total_laps = st.number_input("Total Race Laps:", min_value=10, max_value=80, value=57, key="sim_laps")
    with col_cfg3:
        pit_loss = st.number_input("Pit Stop Time Loss (s):", min_value=15.0, max_value=35.0, value=22.5, key="sim_pitloss")

    st.markdown("---")

    col_sa, col_sb = st.columns(2)

    with col_sa:
        st.markdown("#### 🔴 Strategy A (Plan A)")
        strat_a_name = st.text_input("Strategy A Name:", value="1-Stop Soft-Hard")
        
        st.markdown("**Stint 1:**")
        a1_comp = st.selectbox("Compound", ["SOFT", "MEDIUM", "HARD"], key="a1_comp")
        a1_len = st.number_input("Laps", min_value=1, max_value=total_laps, value=22, key="a1_len")
        
        st.markdown("**Stint 2:**")
        a2_comp = st.selectbox("Compound", ["HARD", "MEDIUM", "SOFT"], key="a2_comp")
        a2_len = st.number_input("Laps", min_value=1, max_value=total_laps, value=total_laps - a1_len, key="a2_len")

    with col_sb:
        st.markdown("#### 🟡 Strategy B (Plan B)")
        strat_b_name = st.text_input("Strategy B Name:", value="2-Stop Soft-Medium-Soft")
        
        st.markdown("**Stint 1:**")
        b1_comp = st.selectbox("Compound", ["SOFT", "MEDIUM", "HARD"], key="b1_comp")
        b1_len = st.number_input("Laps", min_value=1, max_value=total_laps, value=15, key="b1_len")

        st.markdown("**Stint 2:**")
        b2_comp = st.selectbox("Compound", ["MEDIUM", "HARD", "SOFT"], key="b2_comp")
        b2_len = st.number_input("Laps", min_value=1, max_value=total_laps, value=25, key="b2_len")

        st.markdown("**Stint 3:**")
        b3_comp = st.selectbox("Compound", ["SOFT", "MEDIUM", "HARD"], key="b3_comp")
        b3_len = st.number_input("Laps", min_value=1, max_value=total_laps, value=max(1, total_laps - b1_len - b2_len), key="b3_len")

    st.markdown("<br>", unsafe_allow_html=True)
    run_sim = st.button("🚀 RUN WHAT-IF SIMULATION", type="primary", use_container_width=True)

    if run_sim:
        payload = {
            "circuit": circuit,
            "total_laps": int(total_laps),
            "base_lap_time": 90.0,
            "pit_loss_seconds": float(pit_loss),
            "strategy_a": {
                "name": strat_a_name,
                "stints": [
                    {"compound": a1_comp, "stint_length": int(a1_len)},
                    {"compound": a2_comp, "stint_length": int(a2_len)},
                ]
            },
            "strategy_b": {
                "name": strat_b_name,
                "stints": [
                    {"compound": b1_comp, "stint_length": int(b1_len)},
                    {"compound": b2_comp, "stint_length": int(b2_len)},
                    {"compound": b3_comp, "stint_length": int(b3_len)},
                ]
            }
        }

        try:
            res = requests.post(f"{BASE_URL}/simulation/compare", json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                st.markdown("### 📊 Simulation Results")

                res_a = data["strategy_a"]
                res_b = data["strategy_b"]
                faster = data["faster_strategy"]

                st.success(f"🏆 **Faster Strategy:** {faster} (Delta: **{data['time_delta_formatted']}**)")

                c_r1, c_r2 = st.columns(2)
                with c_r1:
                    st.metric(f"{res_a['name']} Total Time", res_a["total_race_time_formatted"], f"{res_a['pit_stops']} Pit Stop(s)")
                with c_r2:
                    st.metric(f"{res_b['name']} Total Time", res_b["total_race_time_formatted"], f"{res_b['pit_stops']} Pit Stop(s)")

                st.caption(f"⚠️ *{data['disclaimer']}*")
            else:
                st.error(f"Simulator Error: {res.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Failed to connect to FastAPI Simulator API: {str(e)}")
