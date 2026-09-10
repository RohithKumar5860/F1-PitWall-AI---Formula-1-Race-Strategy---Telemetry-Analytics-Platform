"""
backend/tests/test_main.py

Phase 1 — pytest tests for the FastAPI application.

Run with (from project root, venv active):
    pytest
or for verbose output:
    pytest -v
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

# ------------------------------------------------------------------ #
# Shared test client                                                   #
# ------------------------------------------------------------------ #

@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return a FastAPI TestClient for the app (no real HTTP server needed)."""
    with TestClient(app) as c:
        yield c


# ------------------------------------------------------------------ #
# Root endpoint                                                        #
# ------------------------------------------------------------------ #

class TestRootEndpoint:
    """Tests for GET /"""

    def test_root_returns_200(self, client: TestClient) -> None:
        """GET / must return HTTP 200 OK."""
        response = client.get("/")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )

    def test_root_message(self, client: TestClient) -> None:
        """GET / body must contain the welcome message."""
        response = client.get("/")
        data = response.json()
        assert data["message"] == "Welcome to F1 PitWall AI API"

    def test_root_status(self, client: TestClient) -> None:
        """GET / body must report status as 'running'."""
        response = client.get("/")
        data = response.json()
        assert data["status"] == "running"


# ------------------------------------------------------------------ #
# Health endpoint                                                      #
# ------------------------------------------------------------------ #

class TestHealthEndpoint:
    """Tests for GET /health"""

    def test_health_returns_200(self, client: TestClient) -> None:
        """GET /health must return HTTP 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )

    def test_health_status_is_healthy(self, client: TestClient) -> None:
        """GET /health must return status == 'healthy'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy", (
            f"Expected 'healthy', got {data.get('status')!r}"
        )

    def test_health_service_name(self, client: TestClient) -> None:
        """GET /health must identify the correct service name."""
        response = client.get("/health")
        data = response.json()
        assert data["service"] == "F1 PitWall AI API"

    def test_health_response_is_json(self, client: TestClient) -> None:
        """GET /health Content-Type must be application/json."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")
