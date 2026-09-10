"""
backend/models/user.py

SQLAlchemy ORM model for the User table.
Supports JWT authentication with hashed passwords.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone

from backend.database.connection import Base
from backend.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """Application user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
