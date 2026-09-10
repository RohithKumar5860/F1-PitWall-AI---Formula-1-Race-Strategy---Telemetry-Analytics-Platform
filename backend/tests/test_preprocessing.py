"""
backend/tests/test_preprocessing.py

Unit tests for data preprocessing and feature engineering pipeline.
"""

import pytest
import pandas as pd
import numpy as np

from backend.services.preprocessing_service import (
    remove_duplicates,
    handle_missing_values,
    filter_invalid_laps,
    create_rolling_pace_features,
    create_degradation_features,
    create_fuel_corrected_features,
    encode_compound,
    preprocess_laps,
)


@pytest.fixture
def sample_raw_laps():
    """Generate sample raw lap records for testing."""
    return [
        {"Driver": "VER", "LapNumber": 1, "LapTimeSeconds": 95.2, "Compound": "SOFT", "TyreLife": 1, "Stint": 1},
        {"Driver": "VER", "LapNumber": 2, "LapTimeSeconds": 94.8, "Compound": "SOFT", "TyreLife": 2, "Stint": 1},
        {"Driver": "VER", "LapNumber": 3, "LapTimeSeconds": 95.1, "Compound": "SOFT", "TyreLife": 3, "Stint": 1},
        {"Driver": "VER", "LapNumber": 4, "LapTimeSeconds": 95.5, "Compound": "SOFT", "TyreLife": 4, "Stint": 1},
        {"Driver": "HAM", "LapNumber": 1, "LapTimeSeconds": 95.8, "Compound": "MEDIUM", "TyreLife": 1, "Stint": 1},
        {"Driver": "HAM", "LapNumber": 2, "LapTimeSeconds": 95.4, "Compound": "MEDIUM", "TyreLife": 2, "Stint": 1},
        {"Driver": "HAM", "LapNumber": 3, "LapTimeSeconds": 95.6, "Compound": "MEDIUM", "TyreLife": 3, "Stint": 1},
        # Invalid lap (too slow)
        {"Driver": "HAM", "LapNumber": 4, "LapTimeSeconds": 140.0, "Compound": "MEDIUM", "TyreLife": 4, "Stint": 1},
        # Duplicate lap
        {"Driver": "VER", "LapNumber": 1, "LapTimeSeconds": 95.2, "Compound": "SOFT", "TyreLife": 1, "Stint": 1},
    ]


def test_remove_duplicates(sample_raw_laps):
    df = pd.DataFrame(sample_raw_laps)
    cleaned = remove_duplicates(df)
    assert len(cleaned) == 8


def test_handle_missing_values():
    raw = pd.DataFrame([
        {"Driver": "LEC", "LapNumber": 1, "Compound": None, "TyreLife": None},
        {"Driver": None, "LapNumber": 2, "Compound": "HARD", "TyreLife": 1},
    ])
    cleaned = handle_missing_values(raw)
    assert len(cleaned) == 1
    assert cleaned["Compound"].iloc[0] == "UNKNOWN"
    assert cleaned["TyreLife"].iloc[0] == 0


def test_filter_invalid_laps(sample_raw_laps):
    df = pd.DataFrame(sample_raw_laps)
    filtered = filter_invalid_laps(df)
    # The lap with 140.0s should be filtered out
    assert not (filtered["LapTimeSeconds"] == 140.0).any()


def test_feature_engineering_pipeline(sample_raw_laps):
    df = preprocess_laps(sample_raw_laps, total_laps=57)
    assert not df.empty
    assert "RollingPace_3" in df.columns
    assert "StintDegradation" in df.columns
    assert "FuelCorrectedLap" in df.columns
    assert "Compound_encoded" in df.columns
    assert df["Compound_encoded"].isin([1, 2, 3, 4, 5, 0]).all()
