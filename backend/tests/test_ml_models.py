"""
backend/tests/test_ml_models.py

Unit tests for ML models training, prediction, joblib serialization, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.ml_service import train_all_models, predict_lap_time, predict_tire_degradation, predict_pit_window

client = TestClient(app)


def test_train_all_models():
    metrics = train_all_models()
    assert "lap_time_model" in metrics
    assert "tire_degradation_model" in metrics
    assert "pit_window_model" in metrics
    assert metrics["lap_time_model"]["mae"] >= 0


def test_predict_lap_time():
    res = predict_lap_time(tyre_life=5, compound="SOFT", lap_number=10)
    assert "predicted_lap_time_seconds" in res
    assert res["predicted_lap_time_seconds"] > 50.0


def test_predict_tire_degradation():
    res = predict_tire_degradation(compound="MEDIUM", tyre_life=15)
    assert "predicted_degradation_seconds" in res
    assert res["predicted_degradation_seconds"] >= 0.0


def test_predict_pit_window():
    res = predict_pit_window(compound="SOFT", tyre_life=18, current_lap=18)
    assert "predicted_laps_until_pit" in res
    assert res["window_start"] <= res["window_end"]


def test_ml_api_models():
    res = client.get("/ml/models")
    assert res.status_code == 200
    data = res.json()
    assert "lap_time_model" in data


def test_ml_api_lap_time_predict():
    payload = {
        "compound": "MEDIUM",
        "tyre_life": 12,
        "lap_number": 20,
        "total_laps": 57,
        "stint": 1,
    }
    res = client.post("/ml/predict/lap-time", json=payload)
    assert res.status_code == 200
    assert "predicted_lap_time_seconds" in res.json()


def test_ml_api_tire_deg_predict():
    payload = {
        "compound": "SOFT",
        "tyre_life": 10,
        "stint": 1,
        "lap_number": 10,
    }
    res = client.post("/ml/predict/tire-degradation", json=payload)
    assert res.status_code == 200
    assert "predicted_degradation_seconds" in res.json()


def test_ml_api_pit_window_predict():
    payload = {
        "compound": "MEDIUM",
        "tyre_life": 20,
        "current_lap": 20,
        "total_laps": 57,
        "stint": 1,
        "recent_pace": 91.2,
        "pace_dropoff": 0.8,
    }
    res = client.post("/ml/predict/pit-window", json=payload)
    assert res.status_code == 200
    assert "recommended_pit_lap" in res.json()
