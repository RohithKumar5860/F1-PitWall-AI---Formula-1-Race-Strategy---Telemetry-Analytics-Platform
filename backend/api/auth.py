"""
backend/api/auth.py

FastAPI router for authentication endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional

from backend.schemas.auth import UserCreate, UserLogin, TokenResponse, UserProfile
from backend.services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_user_by_username,
)
from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and validate user from JWT Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header. Use 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    return user


@router.post(
    "/register",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(request: UserCreate) -> UserProfile:
    """Register a new user account."""
    try:
        user_data = register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )
        return UserProfile(**user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error("Registration error: %s", str(e))
        raise HTTPException(status_code=500, detail="Registration failed.")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT token",
)
async def login(request: UserLogin) -> TokenResponse:
    """Authenticate user and return a JWT access token."""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(data={"sub": user["username"], "user_id": user["id"]})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
)
async def get_profile(current_user: dict = Depends(get_current_user)) -> UserProfile:
    """Return the authenticated user's profile."""
    return UserProfile(**current_user)
