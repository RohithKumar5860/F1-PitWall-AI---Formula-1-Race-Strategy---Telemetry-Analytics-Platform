"""
backend/tests/test_f1_api.py

Pytest test suite for Phase 2 Formula One FastAPI endpoints.
External FastF1 network calls are mocked to keep tests fast and offline-resilient.
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.main import app

@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return FastAPI TestClient instance."""
    with TestClient(app) as c:
        yield c


class TestF1Seasons:
    """Tests for GET /f1/seasons"""

    def test_get_seasons(self, client: TestClient) -> None:
        """GET /f1/seasons must return 200 and a list of season years."""
        response = client.get("/f1/seasons")
        assert response.status_code == 200
        data = response.json()
        assert "seasons" in data
        assert isinstance(data["seasons"], list)
        assert 2024 in data["seasons"]


class TestF1Schedule:
    """Tests for GET /f1/seasons/{year}/schedule"""

    @patch("backend.services.f1_data_service.fastf1.get_event_schedule")
    def test_get_schedule_success(self, mock_schedule: MagicMock, client: TestClient) -> None:
        """GET /f1/seasons/2024/schedule returns mocked schedule records."""
        import pandas as pd
        mock_df = pd.DataFrame([
            {
                "RoundNumber": 1,
                "EventName": "Bahrain Grand Prix",
                "Country": "Bahrain",
                "Location": "Sakhir",
                "EventDate": pd.Timestamp("2024-03-02"),
                "EventFormat": "conventional",
            }
        ])
        mock_schedule.return_value = mock_df

        response = client.get("/f1/seasons/2024/schedule")
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert len(data["events"]) == 1
        assert data["events"][0]["EventName"] == "Bahrain Grand Prix"

    def test_get_schedule_invalid_year(self, client: TestClient) -> None:
        """Out of bounds year should return 400 Bad Request."""
        response = client.get("/f1/seasons/1850/schedule")
        assert response.status_code == 400


class TestSessionSummaryMocked:
    """Tests for session summary with mocked session loader."""

    @patch("backend.services.f1_data_service.load_session_object")
    def test_session_summary_mock(self, mock_load: MagicMock, client: TestClient) -> None:
        mock_session = MagicMock()
        mock_session.event = {
            "EventName": "Monaco Grand Prix",
            "Location": "Monte Carlo",
            "Country": "Monaco",
            "EventDate": "2024-05-26",
        }
        mock_session.name = "Race"
        mock_session.results = [1, 2, 3, 4, 5]
        mock_session.laps = [1, 2, 3]
        mock_session.weather_data = [1, 2]

        mock_load.return_value = mock_session

        response = client.get("/f1/session/summary?year=2024&race=Monaco&session=R")
        assert response.status_code == 200
        data = response.json()
        assert data["EventName"] == "Monaco Grand Prix"
        assert data["Circuit"] == "Monte Carlo"
