"""
backend/tests/test_export.py

Unit tests for export and PDF strategy report generation endpoints.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.pdf_report_service import generate_race_report_html

client = TestClient(app)


def test_generate_race_report_html():
    summary = {"Year": 2024, "EventName": "Monaco Grand Prix", "SessionType": "R", "Circuit": "Monaco"}
    drivers = [{"Position": 1, "DriverCode": "VER", "FullName": "Max Verstappen", "TeamName": "Red Bull", "Points": 25}]
    html = generate_race_report_html(summary, drivers)
    assert "F1 PITWALL AI" in html
    assert "Monaco Grand Prix" in html
    assert "Max Verstappen" in html


@patch("backend.api.export.get_session_summary")
@patch("backend.api.export.get_driver_classification")
@patch("backend.api.export.recommend_strategy")
def test_export_report_endpoint(mock_strat, mock_drivers, mock_summary):
    mock_summary.return_value = {"Year": 2024, "EventName": "Bahrain", "SessionType": "R", "Circuit": "Sakhir"}
    mock_drivers.return_value = [{"Position": 1, "DriverCode": "VER", "FullName": "Max Verstappen"}]
    mock_strat.return_value = {"recommended_pit_window": "Lap 20-24", "suggested_compound": "HARD", "urgency": "LOW", "explanation": "Test"}

    res = client.get("/export/report?year=2024&race=Bahrain&session=R")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "F1 PITWALL AI" in res.text
