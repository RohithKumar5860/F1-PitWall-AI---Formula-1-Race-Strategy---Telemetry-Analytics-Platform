"""
backend/services/db_service.py

Database Persistence Service for F1 PitWall AI.

Handles database synchronization and querying for race events, driver classifications,
lap times, tire records, pit stops, and weather telemetry. Supports both PostgreSQL
and SQLite in-memory fallback.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.database.connection import get_session_factory, is_database_available
from backend.models.f1_models import Race, Driver, Team, Circuit, LapTime, TireDataRecord, PitStop, WeatherRecord
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def sync_session_to_db(
    db: Session,
    year: int,
    race_name: str,
    session_type: str,
    drivers_data: List[Dict[str, Any]],
    laps_data: List[Dict[str, Any]],
    tires_data: Optional[List[Dict[str, Any]]] = None,
    pitstops_data: Optional[List[Dict[str, Any]]] = None,
    weather_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Persist session telemetry and results into database tables.

    Returns dict summarizing synced entity counts.
    """
    logger.info("Syncing session data to DB: %d %s (%s)", year, race_name, session_type)

    # 1. Get or create Race entity
    race = db.query(Race).filter(Race.year == year, Race.event_name == race_name, Race.session_type == session_type).first()
    if not race:
        race = Race(year=year, round_number=1, event_name=race_name, session_type=session_type)
        db.add(race)
        db.flush()

    synced_drivers = 0
    synced_laps = 0
    synced_tires = 0
    synced_pits = 0
    synced_weather = 0

    # 2. Drivers
    driver_map = {}  # code -> Driver model
    for d in drivers_data:
        code = d.get("DriverCode") or d.get("Abbreviation") or d.get("Driver")
        if not code:
            continue
        driver = db.query(Driver).filter(Driver.code == code).first()
        if not driver:
            driver = Driver(
                code=code,
                number=d.get("DriverNumber"),
                full_name=d.get("FullName") or code,
                nationality=d.get("CountryCode"),
            )
            db.add(driver)
            db.flush()
        driver_map[code] = driver
        synced_drivers += 1

    # 3. Lap Times
    for lap in laps_data:
        drv_code = lap.get("Driver")
        driver_obj = driver_map.get(drv_code)
        if not driver_obj:
            continue

        lap_num = lap.get("LapNumber")
        if lap_num is None:
            continue

        # Check existing lap
        existing = db.query(LapTime).filter(
            LapTime.race_id == race.id,
            LapTime.driver_id == driver_obj.id,
            LapTime.lap_number == lap_num,
        ).first()

        if not existing:
            lap_record = LapTime(
                race_id=race.id,
                driver_id=driver_obj.id,
                lap_number=lap_num,
                lap_time_seconds=lap.get("LapTimeSeconds"),
                sector1_seconds=lap.get("Sector1Seconds"),
                sector2_seconds=lap.get("Sector2Seconds"),
                sector3_seconds=lap.get("Sector3Seconds"),
                compound=lap.get("Compound"),
                tyre_life=lap.get("TyreLife"),
                stint=lap.get("Stint"),
                position=lap.get("Position"),
            )
            db.add(lap_record)
            synced_laps += 1

    # 4. Tire Data
    if tires_data:
        for t in tires_data:
            drv = t.get("Driver")
            lap_n = t.get("LapNumber")
            if not drv or lap_n is None:
                continue
            tire_rec = TireDataRecord(
                race_id=race.id,
                driver_code=drv,
                lap_number=lap_n,
                stint=t.get("Stint"),
                compound=t.get("Compound"),
                tyre_life=t.get("TyreLife"),
            )
            db.add(tire_rec)
            synced_tires += 1

    # 5. Pit Stops
    if pitstops_data:
        for p in pitstops_data:
            drv = p.get("Driver")
            pit_l = p.get("LapNumber") or p.get("PitLap", 1)
            if not drv:
                continue
            pit_rec = PitStop(
                race_id=race.id,
                driver_code=drv,
                pit_lap=pit_l,
                stint=p.get("Stint"),
                incoming_compound=p.get("Compound"),
            )
            db.add(pit_rec)
            synced_pits += 1

    # 6. Weather
    if weather_data:
        for w in weather_data:
            w_rec = WeatherRecord(
                race_id=race.id,
                air_temp=w.get("AirTemp"),
                track_temp=w.get("TrackTemp"),
                humidity=w.get("Humidity"),
                pressure=w.get("Pressure"),
                rainfall=w.get("Rainfall"),
                wind_speed=w.get("WindSpeed"),
            )
            db.add(w_rec)
            synced_weather += 1

    db.commit()
    logger.info("Successfully synced session entities to DB (Race ID: %d)", race.id)

    return {
        "race_id": race.id,
        "synced_drivers": synced_drivers,
        "synced_laps": synced_laps,
        "synced_tires": synced_tires,
        "synced_pitstops": synced_pits,
        "synced_weather": synced_weather,
    }


def get_stored_races(db: Session) -> List[Dict[str, Any]]:
    """Retrieve list of race events stored in the database."""
    races = db.query(Race).order_by(Race.year.desc(), Race.round_number).all()
    return [
        {
            "id": r.id,
            "year": r.year,
            "round_number": r.round_number,
            "event_name": r.event_name,
            "session_type": r.session_type,
        }
        for r in races
    ]
