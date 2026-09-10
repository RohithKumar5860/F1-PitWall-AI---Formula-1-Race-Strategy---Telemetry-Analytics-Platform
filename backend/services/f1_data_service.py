"""
backend/services/f1_data_service.py

FastF1 Integration & Data Extraction Service for F1 PitWall AI.

Handles session loading, disk caching configuration, schedule retrieval,
and JSON-serialisable data extraction for drivers, lap times, tire stints,
pit stops, and weather telemetry.
"""

import os
import math
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

import fastf1

from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# FastF1 Cache Initialization                                          #
# ------------------------------------------------------------------ #

_fastf1_cache_initialized: bool = False

def _init_fastf1_cache() -> None:
    """Initialize FastF1 cache directory if configured."""
    global _fastf1_cache_initialized
    cache_dir = os.path.abspath(settings.FASTF1_CACHE_DIR)
    try:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            logger.info("Created FastF1 cache directory: %s", cache_dir)
        fastf1.Cache.enable_cache(cache_dir)
        _fastf1_cache_initialized = True
        logger.info("FastF1 cache initialized: %s", cache_dir)
    except Exception as e:
        _fastf1_cache_initialized = False
        logger.warning("Failed to initialize FastF1 cache at %s: %s", cache_dir, str(e))

_init_fastf1_cache()


def get_fastf1_status() -> str:
    """Return FastF1 cache operational status."""
    cache_dir = os.path.abspath(settings.FASTF1_CACHE_DIR)
    if _fastf1_cache_initialized or os.path.exists(cache_dir):
        return "ready"
    return "unavailable"


# ------------------------------------------------------------------ #
# Serialization Helpers                                                #
# ------------------------------------------------------------------ #

def _clean_val(val: Any) -> Any:
    """Convert pandas/numpy NaN, NaT, Timedelta, and int64/float64 types to JSON-safe Python types."""
    if val is None:
        return None
    # Guard: pd.isna() can raise ValueError on array-like objects
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, (pd.Timedelta, np.timedelta64)):
        total_sec = val.total_seconds()
        return round(total_sec, 3) if not math.isnan(total_sec) else None
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return val.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32)):
        val_float = float(val)
        return None if math.isnan(val_float) or math.isinf(val_float) else round(val_float, 3)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    return val


def _df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert pandas DataFrame to a list of dicts with JSON-safe types."""
    records = df.to_dict(orient="records")
    cleaned_records = []
    for row in records:
        cleaned_row = {col: _clean_val(val) for col, val in row.items()}
        cleaned_records.append(cleaned_row)
    return cleaned_records


# ------------------------------------------------------------------ #
# Season Schedule & Available Seasons                                  #
# ------------------------------------------------------------------ #

def get_available_seasons() -> List[int]:
    """
    Return a list of available F1 seasons supported by the application.
    FastF1 full timing data coverage is robust from 2018 onwards.
    """
    from datetime import datetime
    current_year = datetime.now().year
    return list(range(2018, current_year + 1))


def get_season_schedule(year: int) -> List[Dict[str, Any]]:
    """
    Retrieve the F1 event schedule for a specific year.

    Returns list of dicts with fields:
        RoundNumber, EventName, Country, Location, EventDate, EventFormat
    """
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        if schedule is None or schedule.empty:
            logger.warning("No schedule records found for season %d", year)
            return []

        schedule_data = []
        for _, row in schedule.iterrows():
            event_date = row.get("EventDate")
            date_str = _clean_val(event_date)

            schedule_data.append({
                "RoundNumber": _clean_val(row.get("RoundNumber")),
                "EventName": str(row.get("EventName", "")),
                "Country": str(row.get("Country", "")),
                "Location": str(row.get("Location", "")),
                "EventDate": date_str,
                "EventFormat": str(row.get("EventFormat", "conventional")),
            })
        return schedule_data
    except Exception as e:
        logger.error("Error loading schedule for year %d: %s", year, str(e))
        raise ValueError(f"Could not load schedule for season {year}: {str(e)}")


# ------------------------------------------------------------------ #
# Session Loader                                                       #
# ------------------------------------------------------------------ #

SESSION_TYPE_MAP = {
    "FP1": "Practice 1",
    "FP2": "Practice 2",
    "FP3": "Practice 3",
    "Q": "Qualifying",
    "SQ": "Sprint Qualifying",
    "S": "Sprint",
    "R": "Race",
}

def load_session_object(year: int, race: str, session_type: str) -> fastf1.core.Session:
    """
    Load a FastF1 session object with laps, results, and weather.
    Does NOT load full telemetry by default to keep response times fast.
    """
    # Map short code to full name if applicable
    s_identifier = SESSION_TYPE_MAP.get(session_type.upper(), session_type)
    
    try:
        logger.info("Loading FastF1 session: year=%d, race=%s, session=%s", year, race, s_identifier)
        session = fastf1.get_session(year, race, s_identifier)
        session.load(laps=True, telemetry=False, weather=True)
        return session
    except Exception as e:
        logger.error("Failed to load session (%d, %s, %s): %s", year, race, session_type, str(e))
        raise ValueError(f"Unable to load session '{session_type}' for '{race}' ({year}): {str(e)}")


# ------------------------------------------------------------------ #
# Session Summary                                                      #
# ------------------------------------------------------------------ #

def get_session_summary(year: int, race: str, session_type: str) -> Dict[str, Any]:
    """Return summary metadata for a session."""
    session = load_session_object(year, race, session_type)
    
    num_drivers = len(session.results) if session.results is not None else 0
    num_laps = len(session.laps) if session.laps is not None else 0
    has_weather = session.weather_data is not None and (
        getattr(session.weather_data, "empty", False) is False if hasattr(session.weather_data, "empty") else len(session.weather_data) > 0
    )

    return {
        "EventName": session.event.get("EventName", race),
        "Circuit": session.event.get("Location", ""),
        "Country": session.event.get("Country", ""),
        "Date": _clean_val(session.event.get("EventDate")),
        "SessionName": session.name,
        "Year": year,
        "WeatherAvailable": has_weather,
        "DriverCount": num_drivers,
        "LapCount": num_laps,
    }


# ------------------------------------------------------------------ #
# Driver Data                                                          #
# ------------------------------------------------------------------ #

def get_driver_classification(year: int, race: str, session_type: str) -> List[Dict[str, Any]]:
    """Return driver results/classification table."""
    session = load_session_object(year, race, session_type)
    if session.results is None or session.results.empty:
        return []

    drivers = []
    for _, row in session.results.iterrows():
        drivers.append({
            "DriverCode": str(row.get("Abbreviation", "")),
            "DriverNumber": str(row.get("DriverNumber", "")),
            "FullName": str(row.get("FullName", "")),
            "TeamName": str(row.get("TeamName", "")),
            "Position": _clean_val(row.get("Position")),
            "GridPosition": _clean_val(row.get("GridPosition")),
            "Status": str(row.get("Status", "")),
            "Points": _clean_val(row.get("Points")),
        })
    return drivers


# ------------------------------------------------------------------ #
# Lap Data                                                             #
# ------------------------------------------------------------------ #

def get_lap_data(year: int, race: str, session_type: str, driver: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return lap-by-lap timing data with numerical seconds for timedelta fields."""
    session = load_session_object(year, race, session_type)
    if session.laps is None or session.laps.empty:
        return []

    laps_df = session.laps
    if driver:
        laps_df = laps_df[laps_df["Driver"] == driver.upper()]

    extracted = []
    for _, row in laps_df.iterrows():
        lap_sec = _clean_val(row.get("LapTime"))
        s1_sec = _clean_val(row.get("Sector1Time"))
        s2_sec = _clean_val(row.get("Sector2Time"))
        s3_sec = _clean_val(row.get("Sector3Time"))
        p_in = _clean_val(row.get("PitInTime"))
        p_out = _clean_val(row.get("PitOutTime"))

        extracted.append({
            "Driver": str(row.get("Driver", "")),
            "DriverNumber": str(row.get("DriverNumber", "")),
            "LapNumber": _clean_val(row.get("LapNumber")),
            "LapTimeSeconds": lap_sec,
            "Sector1Seconds": s1_sec,
            "Sector2Seconds": s2_sec,
            "Sector3Seconds": s3_sec,
            "Stint": _clean_val(row.get("Stint")),
            "Compound": str(row.get("Compound", "")) if pd.notna(row.get("Compound")) else "UNKNOWN",
            "TyreLife": _clean_val(row.get("TyreLife")),
            "FreshTyre": _clean_val(row.get("FreshTyre")),
            "PitInTime": p_in,
            "PitOutTime": p_out,
            "TrackStatus": str(row.get("TrackStatus", "")),
            "Position": _clean_val(row.get("Position")),
            "Deleted": _clean_val(row.get("Deleted")),
        })
    return extracted


# ------------------------------------------------------------------ #
# Tire Data                                                            #
# ------------------------------------------------------------------ #

def get_tire_data(year: int, race: str, session_type: str) -> List[Dict[str, Any]]:
    """Return lap-by-lap tire compound and stint life information."""
    session = load_session_object(year, race, session_type)
    if session.laps is None or session.laps.empty:
        return []

    tires = []
    for _, row in session.laps.iterrows():
        tires.append({
            "Driver": str(row.get("Driver", "")),
            "LapNumber": _clean_val(row.get("LapNumber")),
            "Stint": _clean_val(row.get("Stint")),
            "Compound": str(row.get("Compound", "")) if pd.notna(row.get("Compound")) else "UNKNOWN",
            "TyreLife": _clean_val(row.get("TyreLife")),
            "FreshTyre": _clean_val(row.get("FreshTyre")),
        })
    return tires


# ------------------------------------------------------------------ #
# Pit Stop Information                                                 #
# ------------------------------------------------------------------ #

def get_pitstop_data(year: int, race: str, session_type: str) -> List[Dict[str, Any]]:
    """Derive pit-stop / stint transitions from lap data."""
    session = load_session_object(year, race, session_type)
    if session.laps is None or session.laps.empty:
        return []

    laps = session.laps
    pit_stops = []

    # Group by driver and identify stint boundaries
    for driver_code, driver_laps in laps.groupby("Driver"):
        driver_laps = driver_laps.sort_values("LapNumber")
        stints = driver_laps.groupby("Stint")
        
        stint_list = list(stints)
        for i in range(len(stint_list) - 1):
            stint_id, current_stint_df = stint_list[i]
            next_stint_id, next_stint_df = stint_list[i + 1]

            pit_lap = current_stint_df["LapNumber"].max()
            in_compound = current_stint_df["Compound"].iloc[-1] if "Compound" in current_stint_df.columns else "UNKNOWN"
            out_compound = next_stint_df["Compound"].iloc[0] if "Compound" in next_stint_df.columns else "UNKNOWN"

            pit_in_time = _clean_val(current_stint_df["PitInTime"].dropna().iloc[-1]) if not current_stint_df["PitInTime"].dropna().empty else None
            pit_out_time = _clean_val(next_stint_df["PitOutTime"].dropna().iloc[0]) if not next_stint_df["PitOutTime"].dropna().empty else None

            pit_stops.append({
                "Driver": str(driver_code),
                "PitLap": _clean_val(pit_lap),
                "IncomingCompound": str(in_compound) if pd.notna(in_compound) else "UNKNOWN",
                "OutgoingCompound": str(out_compound) if pd.notna(out_compound) else "UNKNOWN",
                "Stint": _clean_val(stint_id),
                "PitInTime": pit_in_time,
                "PitOutTime": pit_out_time,
            })

    return pit_stops


# ------------------------------------------------------------------ #
# Weather Data                                                         #
# ------------------------------------------------------------------ #

def get_weather_data(year: int, race: str, session_type: str) -> List[Dict[str, Any]]:
    """Return session weather timeseries observation records."""
    session = load_session_object(year, race, session_type)
    if session.weather_data is None or session.weather_data.empty:
        return []

    weather_records = []
    for _, row in session.weather_data.iterrows():
        weather_records.append({
            "Time": _clean_val(row.get("Time")),
            "AirTemp": _clean_val(row.get("AirTemp")),
            "Humidity": _clean_val(row.get("Humidity")),
            "Pressure": _clean_val(row.get("Pressure")),
            "Rainfall": _clean_val(row.get("Rainfall")),
            "TrackTemp": _clean_val(row.get("TrackTemp")),
            "WindDirection": _clean_val(row.get("WindDirection")),
            "WindSpeed": _clean_val(row.get("WindSpeed")),
        })
    return weather_records
