"""
frontend/pages/auth_ui.py

Streamlit User Authentication & Profile page.
Calls FastAPI backend /auth/register, /auth/login, /auth/me endpoints.
"""

import streamlit as st
import requests
from typing import Dict, Any

from backend.utils.config import settings

BASE_URL = settings.BACKEND_URL


def render_auth_page() -> None:
    """Render Login, Registration, and User Profile tab."""
    st.markdown("### 🔐 User Authentication & Access Control")

    if "jwt_token" not in st.session_state:
        st.session_state["jwt_token"] = None
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = None

    if st.session_state["jwt_token"]:
        st.success(f"Logged in as **{st.session_state['user_profile']['username']}**")
        st.json(st.session_state["user_profile"])

        if st.button("🚪 LOG OUT", type="secondary"):
            st.session_state["jwt_token"] = None
            st.session_state["user_profile"] = None
            st.rerun()
        return

    tab_login, tab_reg = st.tabs(["🔑 Log In", "📝 Register Account"])

    with tab_login:
        st.markdown("#### Login to PitWall AI")
        username = st.text_input("Username:", key="login_user")
        password = st.text_input("Password:", type="password", key="login_pass")
        btn_login = st.button("LOG IN", type="primary", use_container_width=True, key="btn_login")

        if btn_login:
            if not username or not password:
                st.warning("Please enter username and password.")
            else:
                try:
                    res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password}, timeout=5)
                    if res.status_code == 200:
                        token_data = res.json()
                        token = token_data["access_token"]
                        st.session_state["jwt_token"] = token
                        
                        # Fetch profile
                        headers = {"Authorization": f"Bearer {token}"}
                        prof_res = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
                        if prof_res.status_code == 200:
                            st.session_state["user_profile"] = prof_res.json()
                            st.success("Successfully authenticated!")
                            st.rerun()
                    else:
                        st.error(f"Login failed: {res.json().get('detail', 'Invalid credentials')}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    with tab_reg:
        st.markdown("#### Create New Account")
        reg_user = st.text_input("Username:", key="reg_user")
        reg_email = st.text_input("Email Address:", key="reg_email")
        reg_name = st.text_input("Full Name:", key="reg_name")
        reg_pass = st.text_input("Password:", type="password", key="reg_pass")
        btn_reg = st.button("REGISTER ACCOUNT", type="primary", use_container_width=True, key="btn_reg")

        if btn_reg:
            if not reg_user or not reg_email or not reg_pass:
                st.warning("Username, email, and password are required.")
            else:
                payload = {
                    "username": reg_user,
                    "email": reg_email,
                    "full_name": reg_name,
                    "password": reg_pass,
                }
                try:
                    res = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=5)
                    if res.status_code in (200, 201):
                        st.success("Account created successfully! Switch to Log In tab.")
                    else:
                        st.error(f"Registration failed: {res.json().get('detail', 'Error')}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
