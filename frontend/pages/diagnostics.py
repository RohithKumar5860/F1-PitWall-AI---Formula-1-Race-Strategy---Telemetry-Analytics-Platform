"""
frontend/pages/diagnostics.py

System Diagnostics and Network Connectivity Inspector.
Provides real-time telemetry on backend connectivity, response times, FastF1 cache state,
database connection, and API error tracebacks.
"""

import streamlit as st
import time

from frontend.utils.api_client import get_backend_status, get_backend_url, get_last_error


def render_diagnostics_page() -> None:
    """Render live system diagnostics dashboard."""
    st.markdown("### 🛠️ System Diagnostics & Connectivity")
    st.caption("Inspect live backend API health, FastF1 caching state, database connection, and response latency.")

    status_info = get_backend_status()
    last_err = get_last_error()

    st.markdown("---")
    st.markdown("#### ⚡ Connection Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Backend Status", status_info["backend"].capitalize())
    with col2:
        st.metric("FastF1 Cache", status_info["fastf1"].capitalize())
    with col3:
        st.metric("Database Status", status_info["database"].capitalize())
    with col4:
        st.metric("Response Time", f"{status_info['latency_ms']} ms")

    st.markdown("---")
    st.markdown("#### ⚙️ Configuration Details")

    diag_data = {
        "Target Backend URL": get_backend_url(),
        "Backend Connected": status_info["connected"],
        "API Version": status_info["version"],
        "FastF1 Status": status_info["fastf1"],
        "Database Engine": status_info["database"],
        "Last Recorded Error": last_err if last_err else "None (All systems nominal)",
    }

    for k, v in diag_data.items():
        st.text(f"{k:<25}: {v}")

    st.markdown("---")
    st.markdown("#### 🔄 Live Ping Test")
    if st.button("PING BACKEND AGAIN", type="primary"):
        with st.spinner("Pinging FastAPI backend..."):
            t0 = time.time()
            st_info = get_backend_status()
            t_el = round((time.time() - t0) * 1000, 1)
            st.success(f"Ping successful! Received response in {t_el} ms.")
            st.json(st_info)
