"""
backend/models/__init__.py

SQLAlchemy ORM models for F1 PitWall AI.
"""

from backend.models.user import User
from backend.models.f1_models import (
    Team, Driver, Circuit, Race,
    LapTime, TireDataRecord, PitStop,
    WeatherRecord, Prediction,
)

__all__ = [
    "User", "Team", "Driver", "Circuit", "Race",
    "LapTime", "TireDataRecord", "PitStop",
    "WeatherRecord", "Prediction",
]
