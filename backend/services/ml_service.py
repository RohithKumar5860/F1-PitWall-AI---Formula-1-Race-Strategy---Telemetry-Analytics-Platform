"""
backend/services/ml_service.py

Machine Learning Service Manager for F1 PitWall AI.

Manages training, inference, and serialization for:
- LapTimeModel (XGBoost)
- TireDegradationModel (GradientBoosting)
- PitWindowModel (RandomForest)
"""

import os
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from backend.ml.lap_time_model import LapTimeModel
from backend.ml.tire_degradation_model import TireDegradationModel
from backend.ml.pit_window_model import PitWindowModel
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Global model instances
_lap_time_model = LapTimeModel()
_tire_deg_model = TireDegradationModel()
_pit_window_model = PitWindowModel()


def generate_synthetic_training_data(n_samples: int = 500) -> Dict[str, pd.DataFrame]:
    """
    Generate realistic F1 training datasets based on historical distributions.
    Used for model training when historical FastF1 dataset is not locally cached.
    """
    np.random.seed(42)

    # 1. Lap Time Dataset
    compounds = np.random.choice([1, 2, 3], size=n_samples, p=[0.4, 0.4, 0.2])
    tyre_life = np.random.randint(1, 35, size=n_samples)
    lap_number = np.random.randint(1, 57, size=n_samples)
    fuel_corr = lap_number / 57.0
    stint = np.random.randint(1, 4, size=n_samples)

    # Base lap time ~90s, softs faster (-0.8s), hards slower (+0.6s), degradation +0.05s/lap, fuel benefit -1.5s over race
    base_time = 90.0
    comp_offset = np.where(compounds == 1, -0.8, np.where(compounds == 2, 0.0, 0.6))
    deg_effect = tyre_life * 0.05
    fuel_effect = (1.0 - fuel_corr) * 1.8
    noise = np.random.normal(0, 0.3, size=n_samples)

    lap_time_y = base_time + comp_offset + deg_effect + fuel_effect + noise

    lap_time_X = pd.DataFrame({
        "TyreLife": tyre_life,
        "Compound_encoded": compounds,
        "LapNumber": lap_number,
        "FuelCorrectedLap": fuel_corr,
        "Stint": stint,
    })

    # 2. Tire Degradation Dataset
    deg_y = np.maximum(0.0, tyre_life * 0.045 + comp_offset * 0.02 + np.random.normal(0, 0.05, size=n_samples))
    tire_deg_X = pd.DataFrame({
        "Compound_encoded": compounds,
        "TyreLife": tyre_life,
        "Stint": stint,
        "LapNumber": lap_number,
    })

    # 3. Pit Window Dataset
    current_lap = np.random.randint(5, 50, size=n_samples)
    total_laps = 57
    remaining_laps = total_laps - current_lap
    avg_recent_pace = 90.0 + (tyre_life * 0.05)
    pace_dropoff = np.maximum(0.0, tyre_life * 0.04 - 0.2)
    target_laps_until_pit = np.maximum(1, 22 - tyre_life + np.random.randint(-2, 3, size=n_samples))

    pit_window_X = pd.DataFrame({
        "Compound_encoded": compounds,
        "TyreLife": tyre_life,
        "Stint": stint,
        "CurrentLap": current_lap,
        "TotalLaps": np.full(n_samples, total_laps),
        "RemainingLaps": remaining_laps,
        "AvgRecentPace": avg_recent_pace,
        "PaceDropoff": pace_dropoff,
    })

    return {
        "lap_time": (lap_time_X, lap_time_y),
        "tire_deg": (tire_deg_X, deg_y),
        "pit_window": (pit_window_X, target_laps_until_pit),
    }


def train_all_models() -> Dict[str, Any]:
    """Train all 3 ML models and save serialised joblib binaries."""
    logger.info("Starting training for all ML models...")
    data = generate_synthetic_training_data()

    # Train Lap Time Model
    X_lt, y_lt = data["lap_time"]
    m_lt = _lap_time_model.train(X_lt, y_lt)
    _lap_time_model.save_model()

    # Train Tire Degradation Model
    X_td, y_td = data["tire_deg"]
    m_td = _tire_deg_model.train(X_td, y_td)
    _tire_deg_model.save_model()

    # Train Pit Window Model
    X_pw, y_pw = data["pit_window"]
    m_pw = _pit_window_model.train(X_pw, y_pw)
    _pit_window_model.save_model()

    logger.info("All ML models trained and saved successfully.")
    return {
        "lap_time_model": m_lt,
        "tire_degradation_model": m_td,
        "pit_window_model": m_pw,
    }


def get_models_status() -> Dict[str, Any]:
    """Return status and metrics for all ML models."""
    # Attempt loading if not loaded
    if not _lap_time_model.is_trained:
        _lap_time_model.load_model()
    if not _tire_deg_model.is_trained:
        _tire_deg_model.load_model()
    if not _pit_window_model.is_trained:
        _pit_window_model.load_model()

    return {
        "lap_time_model": _lap_time_model.get_info(),
        "tire_degradation_model": _tire_deg_model.get_info(),
        "pit_window_model": _pit_window_model.get_info(),
    }


def predict_lap_time(tyre_life: int, compound: str, lap_number: int, total_laps: int = 57, stint: int = 1) -> Dict[str, Any]:
    """Predict lap time in seconds."""
    if not _lap_time_model.is_trained:
        if not _lap_time_model.load_model():
            train_all_models()

    comp_enc = LapTimeModel.encode_compound(compound)
    fuel_corr = lap_number / max(1, total_laps)
    X = pd.DataFrame([{
        "TyreLife": tyre_life,
        "Compound_encoded": comp_enc,
        "LapNumber": lap_number,
        "FuelCorrectedLap": fuel_corr,
        "Stint": stint,
    }])
    pred_time = float(_lap_time_model.predict(X)[0])
    return {
        "predicted_lap_time_seconds": round(pred_time, 3),
        "compound": compound,
        "tyre_life": tyre_life,
        "lap_number": lap_number,
        "model_used": _lap_time_model.model_name,
        "metrics": _lap_time_model.metrics,
    }


def predict_tire_degradation(compound: str, tyre_life: int, stint: int = 1, lap_number: int = 10) -> Dict[str, Any]:
    """Predict tire degradation pace loss per lap."""
    if not _tire_deg_model.is_trained:
        if not _tire_deg_model.load_model():
            train_all_models()

    comp_enc = LapTimeModel.encode_compound(compound)
    X = pd.DataFrame([{
        "Compound_encoded": comp_enc,
        "TyreLife": tyre_life,
        "Stint": stint,
        "LapNumber": lap_number,
    }])
    pred_deg = float(_tire_deg_model.predict(X)[0])
    return {
        "predicted_degradation_seconds": round(max(0.0, pred_deg), 4),
        "compound": compound,
        "tyre_life": tyre_life,
        "model_used": _tire_deg_model.model_name,
    }


def predict_pit_window(compound: str, tyre_life: int, current_lap: int, total_laps: int = 57, stint: int = 1, recent_pace: float = 90.0, pace_dropoff: float = 0.5) -> Dict[str, Any]:
    """Predict optimal pit window with confidence."""
    if not _pit_window_model.is_trained:
        if not _pit_window_model.load_model():
            train_all_models()

    comp_enc = LapTimeModel.encode_compound(compound)
    remaining = total_laps - current_lap
    X = pd.DataFrame([{
        "Compound_encoded": comp_enc,
        "TyreLife": tyre_life,
        "Stint": stint,
        "CurrentLap": current_lap,
        "TotalLaps": total_laps,
        "RemainingLaps": remaining,
        "AvgRecentPace": recent_pace,
        "PaceDropoff": pace_dropoff,
    }])
    results = _pit_window_model.predict_window(X)
    res = results[0]
    return {
        "current_lap": current_lap,
        "total_laps": total_laps,
        "predicted_laps_until_pit": res["predicted_laps_until_pit"],
        "recommended_pit_lap": current_lap + res["predicted_laps_until_pit"],
        "window_start": current_lap + res["window_start"],
        "window_end": current_lap + res["window_end"],
        "confidence": res["confidence"],
    }
