"""
backend/models/f1_models.py

SQLAlchemy ORM models for Formula One data entities.

Models:
    Driver, Team, Circuit, Race, LapTime, TireData, PitStop, Weather, Prediction
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from backend.database.connection import Base
from backend.models.base import TimestampMixin


# ------------------------------------------------------------------ #
# Team                                                                 #
# ------------------------------------------------------------------ #

class Team(Base, TimestampMixin):
    """F1 constructor / team."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    nationality = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code

    drivers = relationship("Driver", back_populates="team", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name!r}>"


# ------------------------------------------------------------------ #
# Driver                                                               #
# ------------------------------------------------------------------ #

class Driver(Base, TimestampMixin):
    """F1 driver."""
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(3), unique=True, nullable=False, index=True)
    number = Column(Integer, nullable=True)
    full_name = Column(String(100), nullable=False)
    nationality = Column(String(50), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    team = relationship("Team", back_populates="drivers", lazy="selectin")
    lap_times = relationship("LapTime", back_populates="driver", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Driver id={self.id} code={self.code!r} name={self.full_name!r}>"


# ------------------------------------------------------------------ #
# Circuit                                                              #
# ------------------------------------------------------------------ #

class Circuit(Base, TimestampMixin):
    """F1 circuit / track."""
    __tablename__ = "circuits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    location = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)
    length_km = Column(Float, nullable=True)
    lap_count = Column(Integer, nullable=True)

    races = relationship("Race", back_populates="circuit", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Circuit id={self.id} name={self.name!r}>"


# ------------------------------------------------------------------ #
# Race                                                                 #
# ------------------------------------------------------------------ #

class Race(Base, TimestampMixin):
    """F1 race event."""
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    event_name = Column(String(200), nullable=False, index=True)
    circuit_id = Column(Integer, ForeignKey("circuits.id"), nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=True)
    session_type = Column(String(20), nullable=False, default="Race")

    circuit = relationship("Circuit", back_populates="races", lazy="selectin")
    lap_times = relationship("LapTime", back_populates="race", lazy="dynamic")
    tire_data = relationship("TireDataRecord", back_populates="race", lazy="dynamic")
    pit_stops = relationship("PitStop", back_populates="race", lazy="dynamic")
    weather_records = relationship("WeatherRecord", back_populates="race", lazy="dynamic")

    __table_args__ = (
        Index("ix_race_year_round", "year", "round_number"),
    )

    def __repr__(self) -> str:
        return f"<Race id={self.id} year={self.year} event={self.event_name!r}>"


# ------------------------------------------------------------------ #
# LapTime                                                              #
# ------------------------------------------------------------------ #

class LapTime(Base, TimestampMixin):
    """Individual lap timing record."""
    __tablename__ = "lap_times"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    lap_number = Column(Integer, nullable=False)
    lap_time_seconds = Column(Float, nullable=True)
    sector1_seconds = Column(Float, nullable=True)
    sector2_seconds = Column(Float, nullable=True)
    sector3_seconds = Column(Float, nullable=True)
    compound = Column(String(20), nullable=True)
    tyre_life = Column(Integer, nullable=True)
    stint = Column(Integer, nullable=True)
    position = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False)

    race = relationship("Race", back_populates="lap_times")
    driver = relationship("Driver", back_populates="lap_times")

    __table_args__ = (
        Index("ix_laptime_race_driver", "race_id", "driver_id"),
    )

    def __repr__(self) -> str:
        return f"<LapTime race_id={self.race_id} driver_id={self.driver_id} lap={self.lap_number}>"


# ------------------------------------------------------------------ #
# TireData                                                             #
# ------------------------------------------------------------------ #

class TireDataRecord(Base, TimestampMixin):
    """Tire compound and stint tracking record."""
    __tablename__ = "tire_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_code = Column(String(3), nullable=False)
    lap_number = Column(Integer, nullable=False)
    stint = Column(Integer, nullable=True)
    compound = Column(String(20), nullable=True)
    tyre_life = Column(Integer, nullable=True)
    fresh_tyre = Column(Boolean, nullable=True)

    race = relationship("Race", back_populates="tire_data")

    def __repr__(self) -> str:
        return f"<TireDataRecord race_id={self.race_id} driver={self.driver_code!r} lap={self.lap_number}>"


# ------------------------------------------------------------------ #
# PitStop                                                              #
# ------------------------------------------------------------------ #

class PitStop(Base, TimestampMixin):
    """Pit stop event / stint transition."""
    __tablename__ = "pit_stops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_code = Column(String(3), nullable=False)
    pit_lap = Column(Integer, nullable=False)
    stint = Column(Integer, nullable=True)
    incoming_compound = Column(String(20), nullable=True)
    outgoing_compound = Column(String(20), nullable=True)
    pit_in_time = Column(Float, nullable=True)
    pit_out_time = Column(Float, nullable=True)

    race = relationship("Race", back_populates="pit_stops")

    def __repr__(self) -> str:
        return f"<PitStop race_id={self.race_id} driver={self.driver_code!r} lap={self.pit_lap}>"


# ------------------------------------------------------------------ #
# Weather                                                              #
# ------------------------------------------------------------------ #

class WeatherRecord(Base, TimestampMixin):
    """Weather observation during a session."""
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    time_offset = Column(Float, nullable=True)
    air_temp = Column(Float, nullable=True)
    track_temp = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    rainfall = Column(Boolean, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)

    race = relationship("Race", back_populates="weather_records")

    def __repr__(self) -> str:
        return f"<WeatherRecord race_id={self.race_id} time={self.time_offset}>"


# ------------------------------------------------------------------ #
# Prediction                                                           #
# ------------------------------------------------------------------ #

class Prediction(Base, TimestampMixin):
    """Stored ML model prediction."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=True, index=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=True)
    prediction_type = Column(String(50), nullable=False)  # e.g. "lap_time", "pit_window", "tire_deg"
    input_data = Column(Text, nullable=True)  # JSON serialized input
    output_data = Column(Text, nullable=True)  # JSON serialized output
    confidence = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} model={self.model_name!r} type={self.prediction_type!r}>"
