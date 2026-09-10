"""
backend/models/base.py

Shared base class and common mixins for SQLAlchemy ORM models.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime
from backend.database.connection import Base


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns to a model."""
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
