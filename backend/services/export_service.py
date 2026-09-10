"""
backend/services/export_service.py

Raw Dataset Export Service for F1 PitWall AI.

Saves collected FastF1 session datasets (laps, results, weather, tires, pit stops)
into structured CSV files under data/raw/{year}/{race_clean}/.
"""

import os
import re
from typing import Dict, Any, List
import pandas as pd

from backend.services.f1_data_service import (
    get_driver_classification,
    get_lap_data,
    get_tire_data,
    get_pitstop_data,
    get_weather_data,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _sanitize_filename(name: str) -> str:
    """Remove special characters and replace spaces with underscores for clean file/folder names."""
    clean = re.sub(r"[^\w\s-]", "", name).strip()
    return re.sub(r"[-\s]+", "_", clean)


def export_session_raw_data(year: int, race: str, session_type: str, base_dir: str = "data/raw") -> Dict[str, Any]:
    """
    Load FastF1 session datasets and export them into data/raw/{year}/{race_clean}/ as CSV files.

    Returns dict summarizing the export operation.
    """
    race_clean = _sanitize_filename(race)
    target_dir = os.path.join(base_dir, str(year), race_clean)
    os.makedirs(target_dir, exist_ok=True)

    logger.info("Exporting session raw data to: %s", target_dir)

    # 1. Driver classification / results
    drivers = get_driver_classification(year, race, session_type)
    drivers_df = pd.DataFrame(drivers)
    results_path = os.path.join(target_dir, f"{session_type.lower()}_results.csv")
    drivers_df.to_csv(results_path, index=False)

    # 2. Lap data
    laps = get_lap_data(year, race, session_type)
    laps_df = pd.DataFrame(laps)
    laps_path = os.path.join(target_dir, f"{session_type.lower()}_laps.csv")
    laps_df.to_csv(laps_path, index=False)

    # 3. Tire data
    tires = get_tire_data(year, race, session_type)
    tires_df = pd.DataFrame(tires)
    tires_path = os.path.join(target_dir, f"{session_type.lower()}_tires.csv")
    tires_df.to_csv(tires_path, index=False)

    # 4. Pit stops
    pitstops = get_pitstop_data(year, race, session_type)
    pitstops_df = pd.DataFrame(pitstops)
    pitstops_path = os.path.join(target_dir, f"{session_type.lower()}_pitstops.csv")
    pitstops_df.to_csv(pitstops_path, index=False)

    # 5. Weather data
    weather = get_weather_data(year, race, session_type)
    weather_df = pd.DataFrame(weather)
    weather_path = os.path.join(target_dir, f"{session_type.lower()}_weather.csv")
    weather_df.to_csv(weather_path, index=False)

    logger.info("Successfully exported raw datasets to %s", target_dir)

    return {
        "TargetDirectory": target_dir,
        "DriverCount": len(drivers),
        "LapCount": len(laps),
        "TireRecordCount": len(tires),
        "PitStopCount": len(pitstops),
        "WeatherRecordCount": len(weather),
    }
