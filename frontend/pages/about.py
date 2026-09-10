"""
frontend/pages/about.py

About page for F1 PitWall AI.
"""

import streamlit as st

def render_about_page() -> None:
    """Render project description and architecture roadmap."""
    st.markdown("## 🏎️ About F1 PitWall AI")
    st.markdown(
        """
        **F1 PitWall AI** is an intelligent Formula One race strategy and decision support system.
        It uses real historical race telemetry, tire degradation analytics, and machine learning
        to assist engineers and strategy enthusiasts.

        ---

        ### Phase Roadmap

        - **Phase 1 — Project Setup & Architecture**: Clean FastAPI + Streamlit foundation. *(Complete)*
        - **Phase 2 — FastF1 Data & Dashboard**: Historical data collection, caching, and visualization. *(Current)*
        - **Phase 3 — Data Processing & Storage**: PostgreSQL schema and SQLAlchemy pipeline. *(Next)*
        - **Phase 4 — ML Model Development**: Tire degradation and lap time prediction models.
        - **Phase 5 — Strategy Engine**: AI pit-stop recommendation algorithm.
        - **Phase 6 — What-If Simulator**: Interactive race replay and scenario simulation.
        - **Phase 7 — Multi-Page Dashboard & Reporting**: Advanced reporting and automated insights.

        ---

        ### Tech Stack

        - **Backend**: FastAPI, Uvicorn, Python 3.11+
        - **Frontend**: Streamlit, Plotly
        - **Data Pipeline**: FastF1, Pandas, NumPy
        - **Machine Learning**: Scikit-learn, XGBoost, Joblib
        - **Database**: PostgreSQL, SQLAlchemy
        """
    )
