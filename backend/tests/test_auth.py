"""
backend/tests/test_auth.py

Unit tests for user registration, authentication, JWT generation, and profile endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_register_and_login_user():
    username = "testdriver99"
    email = "testdriver99@f1pitwall.ai"
    password = "SuperSecretPassword123!"

    # 1. Register
    reg_payload = {
        "username": username,
        "email": email,
        "full_name": "Test Driver",
        "password": password,
    }
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["username"] == username

    # 2. Login
    login_payload = {
        "username": username,
        "password": password,
    }
    login_res = client.post("/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Get profile (/auth/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == username
