"""
backend/services/preprocessing_service.py

Data Preprocessing & Feature Engineering Pipeline for F1 PitWall AI.

Transforms raw FastF1 session data into clean, feature-rich datasets
suitable for ML training and analytics. Saves to Parquet format under
data/processed/.
"""

import os
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

from backend.utils.logger import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")


# ------------------------------------------------------------------ #
# Cleaning Functions                                                   #
# ------------------------------------------------------------------ #

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed > 0:
        logger.info("Removed %d duplicate rows.", removed)
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values safely without data leakage."""
    df = df.copy()
    # Drop rows where critical fields are entirely null
    critical_cols = ["Driver", "LapNumber"]
    existing_critical = [c for c in critical_cols if c in df.columns]
    if existing_critical:
        df = df.dropna(subset=existing_critical)

    # Fill compound with UNKNOWN
    if "Compound" in df.columns:
        df["Compound"] = df["Compound"].fillna("UNKNOWN")

    # Fill tyre life with 0
    if "TyreLife" in df.columns:
        df["TyreLife"] = df["TyreLife"].fillna(0)

    # Fill stint with 1
    if "Stint" in df.columns:
        df["Stint"] = df["Stint"].fillna(1)

    return df


def filter_invalid_laps(df: pd.DataFrame, min_time: float = 30.0, max_mult: float = 1.30) -> pd.DataFrame:
    """Filter out invalid laps (pit in/out, safety car, extremely slow)."""
    if "LapTimeSeconds" not in df.columns:
        return df

    df = df.copy()
    before = len(df)
    # Remove laps with no time recorded
    df = df[df["LapTimeSeconds"].notna()]
    # Remove obviously invalid laps (too fast or too slow)
    df = df[df["LapTimeSeconds"] > min_time]

    # Remove outlier laps (laps > max_mult * driver median lap time)
    if not df.empty and "Driver" in df.columns:
        driver_medians = df.groupby("Driver")["LapTimeSeconds"].transform("median")
        df = df[df["LapTimeSeconds"] <= driver_medians * max_mult]

    removed = before - len(df)
    if removed > 0:
        logger.info("Filtered %d invalid laps.", removed)
    return df


# ------------------------------------------------------------------ #
# Feature Engineering                                                  #
# ------------------------------------------------------------------ #

def create_rolling_pace_features(df: pd.DataFrame, windows: list = None) -> pd.DataFrame:
    """
    Create rolling average pace features per driver.
    Uses only past laps (no data leakage).
    """
    if windows is None:
        windows = [3, 5, 10]

    if "LapTimeSeconds" not in df.columns or "Driver" not in df.columns:
        return df

    df = df.sort_values(["Driver", "LapNumber"]).copy()

    for w in windows:
        col_name = f"RollingPace_{w}"
        # shift(1) ensures only past laps are used — prevents data leakage
        df[col_name] = df.groupby("Driver")["LapTimeSeconds"].transform(
            lambda x: x.rolling(window=w, min_periods=1).mean().shift(1)
        )

    return df


def create_degradation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create tire degradation features per driver per stint."""
    if "LapTimeSeconds" not in df.columns:
        return df

    df = df.sort_values(["Driver", "LapNumber"]).copy()

    # Lap time delta from previous lap
    df["LapTimeDelta"] = df.groupby(["Driver", "Stint"])["LapTimeSeconds"].diff()

    # Cumulative degradation within stint (difference from stint start)
    stint_start_times = df.groupby(["Driver", "Stint"])["LapTimeSeconds"].transform("first")
    df["StintDegradation"] = df["LapTimeSeconds"] - stint_start_times

    # Stint lap index (lap within the current stint)
    df["StintLapIndex"] = df.groupby(["Driver", "Stint"]).cumcount() + 1

    return df


def create_fuel_corrected_features(df: pd.DataFrame, total_laps: int = 57) -> pd.DataFrame:
    """Create fuel-load-normalized lap number (0 to 1 range)."""
    if "LapNumber" in df.columns:
        df["FuelCorrectedLap"] = df["LapNumber"] / max(total_laps, 1)

    return df


def create_pit_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create pit-stop-related features."""
    if "PitInTime" in df.columns:
        df["IsPitLap"] = df["PitInTime"].notna().astype(int)
    if "PitOutTime" in df.columns:
        df["IsOutLap"] = df["PitOutTime"].notna().astype(int)

    # Flag fresh tire laps
    if "FreshTyre" in df.columns:
        df["FreshTyre"] = df["FreshTyre"].fillna(False).astype(int)

    return df


def encode_compound(df: pd.DataFrame) -> pd.DataFrame:
    """Encode tire compound as ordinal integer."""
    compound_map = {
        "SOFT": 1, "MEDIUM": 2, "HARD": 3,
        "INTERMEDIATE": 4, "WET": 5, "UNKNOWN": 0,
    }
    if "Compound" in df.columns:
        df["Compound_encoded"] = df["Compound"].map(
            lambda x: compound_map.get(str(x).upper(), 0)
        )
    return df


# ------------------------------------------------------------------ #
# Full Pipeline                                                        #
# ------------------------------------------------------------------ #

def preprocess_laps(
    laps: List[Dict[str, Any]],
    total_laps: int = 57,
) -> pd.DataFrame:
    """
    Full preprocessing pipeline for lap data.

    Parameters
    ----------
    laps : list of dict
        Raw lap data from FastF1 (via f1_data_service).
    total_laps : int
        Total scheduled race laps for fuel correction.

    Returns
    -------
    pd.DataFrame
        Cleaned, feature-engineered DataFrame.
    """
    if not laps:
        logger.warning("No lap data to preprocess.")
        return pd.DataFrame()

    df = pd.DataFrame(laps)
    logger.info("Preprocessing %d raw lap records.", len(df))

    # Step 1: Remove duplicates
    df = remove_duplicates(df)

    # Step 2: Handle missing values
    df = handle_missing_values(df)

    # Step 3: Filter invalid laps
    df = filter_invalid_laps(df)

    # Step 4: Encode compound
    df = encode_compound(df)

    # Step 5: Create features
    df = create_rolling_pace_features(df)
    df = create_degradation_features(df)
    df = create_fuel_corrected_features(df, total_laps)
    df = create_pit_features(df)

    logger.info("Preprocessing complete: %d clean records, %d features.",
                len(df), len(df.columns))
    return df


def save_processed_data(
    df: pd.DataFrame,
    year: int,
    race: str,
    session_type: str,
    label: str = "laps",
) -> str:
    """
    Save processed DataFrame to Parquet format.

    Returns the file path.
    """
    import re
    race_clean = re.sub(r"[^\w\s-]", "", race).strip()
    race_clean = re.sub(r"[-\s]+", "_", race_clean)

    target_dir = os.path.join(PROCESSED_DIR, str(year), race_clean)
    os.makedirs(target_dir, exist_ok=True)

    filename = f"{session_type.lower()}_{label}_processed.parquet"
    filepath = os.path.join(target_dir, filename)

    df.to_parquet(filepath, index=False, engine="pyarrow" if _has_pyarrow() else "fastparquet")
    logger.info("Saved processed data: %s (%d rows)", filepath, len(df))
    return filepath


def _has_pyarrow() -> bool:
    """Check if pyarrow is available."""
    try:
        import pyarrow
        return True
    except ImportError:
        return False
