"""
frontend/pages/strategy_ai.py

AI Strategy Engine page — interactive pit-stop recommendation interface.
Calls FastAPI backend POST /strategy/recommend endpoint.
"""

import os
import streamlit as st
import requests
from typing import Dict, Any

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


def render_strategy_ai_page() -> None:
    """Render interactive AI Strategy Recommendation page."""
    st.markdown("### 🤖 AI Strategy Engine")
    st.caption("Rule-based AI decision support system trained on historical F1 compound performance data.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### ⚙️ Input Race State")

        driver = st.text_input("Driver Code:", value="VER", max_chars=3).upper()
        circuit = st.selectbox("Circuit:", options=[
            "Monaco Grand Prix", "Bahrain Grand Prix", "Silverstone Circuit",
            "Spa-Francorchamps", "Monza", "Suzuka Circuit"
        ])

        current_lap = st.number_input("Current Lap:", min_value=1, max_value=70, value=20)
        total_laps = st.number_input("Total Scheduled Laps:", min_value=10, max_value=80, value=57)

        current_compound = st.selectbox("Current Compound:", options=["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"])
        tire_age = st.number_input("Current Tire Age (Laps):", min_value=1, max_value=50, value=18)

        position = st.number_input("Current Position:", min_value=1, max_value=20, value=1)
        track_temp = st.slider("Track Temperature (°C):", min_value=15.0, max_value=60.0, value=38.0)
        rainfall = st.checkbox("Rainfall Occurring", value=False)

        submit = st.button("⚡ GENERATE RECOMMENDATION", type="primary", use_container_width=True)

    with col2:
        st.markdown("#### 🎯 Strategy Recommendation")

        if submit:
            payload = {
                "driver": driver,
                "circuit": circuit,
                "current_lap": int(current_lap),
                "total_laps": int(total_laps),
                "current_compound": current_compound,
                "tire_age": int(tire_age),
                "position": int(position),
                "track_temp": float(track_temp),
                "rainfall": rainfall,
            }

            try:
                res = requests.post(f"{BASE_URL}/strategy/recommend", json=payload, timeout=10)
                if res.status_code == 200:
                    data = res.json()

                    st.success(f"**Recommended Pit Window:** {data.get('recommended_pit_window', 'N/A')}")

                    c_m1, c_m2, c_m3 = st.columns(3)
                    c_m1.metric("Suggested Compound", data.get("suggested_compound", "N/A"))
                    c_m2.metric("Est. Stint Length", f"{data.get('estimated_stint_length', 'N/A')} Laps")
                    c_m3.metric("Urgency", data.get("urgency", "N/A"))

                    st.markdown("##### 📝 Strategy Rationale")
                    st.info(data.get("explanation", "No explanation provided."))

                    alt = data.get("alternative_strategy")
                    if alt:
                        st.warning(f"**Alternative Strategy:** {alt}")

                    disclaimer = data.get("disclaimer", "")
                    if disclaimer:
                        st.caption(f"⚠️ *{disclaimer}*")
                else:
                    detail = "Unknown error"
                    if "application/json" in res.headers.get("content-type", ""):
                        detail = res.json().get("detail", detail)
                    st.error(f"Strategy Engine Error: {detail}")
            except Exception as e:
                st.error(f"Failed to connect to FastAPI Strategy API: {str(e)}")
        else:
            st.info("👈 Enter current race conditions on the left and click **GENERATE RECOMMENDATION**.")
