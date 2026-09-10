"""
backend/tests/test_analytics.py

Unit tests for advanced race analytics endpoints.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

MOCK_LAPS = [
    {"Driver": "VER", "LapNumber": 1, "LapTimeSeconds": 94.5, "Sector1Seconds": 28.1, "Sector2Seconds": 36.2, "Sector3Seconds": 30.2, "Position": 1, "Compound": "SOFT", "Stint": 1},
    {"Driver": "VER", "LapNumber": 2, "LapTimeSeconds": 94.8, "Sector1Seconds": 28.2, "Sector2Seconds": 36.3, "Sector3Seconds": 30.3, "Position": 1, "Compound": "SOFT", "Stint": 1},
    {"Driver": "HAM", "LapNumber": 1, "LapTimeSeconds": 95.1, "Sector1Seconds": 28.4, "Sector2Seconds": 36.4, "Sector3Seconds": 30.3, "Position": 2, "Compound": "MEDIUM", "Stint": 1},
    {"Driver": "HAM", "LapNumber": 2, "LapTimeSeconds": 95.3, "Sector1Seconds": 28.5, "Sector2Seconds": 36.5, "Sector3Seconds": 30.3, "Position": 2, "Compound": "MEDIUM", "Stint": 1},
]


@patch("backend.api.analytics.get_lap_data", return_value=MOCK_LAPS)
def test_lap_comparison(mock_laps):
    res = client.get("/analytics/lap-comparison?year=2024&race=Monaco&session=R&drivers=VER,HAM")
    assert res.status_code == 200
    data = res.json()
    assert data["drivers"] == ["VER", "HAM"]
    assert len(data["comparison"]) == 4


@patch("backend.api.analytics.get_lap_data", return_value=MOCK_LAPS)
def test_sector_analysis(mock_laps):
    res = client.get("/analytics/sector-analysis?year=2024&race=Monaco&session=R")
    assert res.status_code == 200
    data = res.json()
    assert len(data["sectors"]) == 2
    assert data["sectors"][0]["Driver"] in ["VER", "HAM"]


@patch("backend.api.analytics.get_lap_data", return_value=MOCK_LAPS)
def test_position_changes(mock_laps):
    res = client.get("/analytics/position-changes?year=2024&race=Monaco&session=R")
    assert res.status_code == 200
    data = res.json()
    assert len(data["positions"]) == 4


@patch("backend.api.analytics.get_lap_data", return_value=MOCK_LAPS)
def test_pace_distribution(mock_laps):
    res = client.get("/analytics/pace-distribution?year=2024&race=Monaco&session=R")
    assert res.status_code == 200
    data = res.json()
    assert len(data["distribution"]) == 2
    assert "Median" in data["distribution"][0]


@patch("backend.api.analytics.get_lap_data", return_value=MOCK_LAPS)
def test_team_pace_comparison(mock_laps):
    res = client.get("/analytics/team-pace-comparison?year=2024&race=Monaco&session=R")
    assert res.status_code == 200
    data = res.json()
    assert "teams" in data


@patch("backend.api.analytics.get_lap_data", return_value=MOCK_LAPS)
def test_consistency_analysis(mock_laps):
    res = client.get("/analytics/consistency-analysis?year=2024&race=Monaco&session=R")
    assert res.status_code == 200
    data = res.json()
    assert "consistency" in data
