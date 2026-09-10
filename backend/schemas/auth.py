"""
backend/schemas/auth.py

Pydantic v2 models for authentication endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """Request body for user registration."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="Full display name")


class UserLogin(BaseModel):
    """Request body for user login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """JWT token response after successful login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")


class UserProfile(BaseModel):
    """Public-facing user profile response."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
