"""
backend/services/auth_service.py

Authentication service for F1 PitWall AI.
Handles password hashing, JWT token generation/verification, and user CRUD.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext

from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# Password Hashing                                                     #
# ------------------------------------------------------------------ #

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ------------------------------------------------------------------ #
# JWT Token Management                                                 #
# ------------------------------------------------------------------ #

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Parameters
    ----------
    data : dict
        Payload data to encode (must include 'sub' for subject/username).
    expires_delta : timedelta, optional
        Custom expiration. Defaults to JWT_EXPIRE_MINUTES from settings.

    Returns
    -------
    str
        Encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    logger.debug("JWT token created for subject: %s", data.get("sub"))
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.

    Returns
    -------
    dict or None
        Decoded payload if valid, None if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT token: %s", str(e))
        return None


# ------------------------------------------------------------------ #
# In-Memory User Store (fallback when DB unavailable)                  #
# ------------------------------------------------------------------ #

_in_memory_users: Dict[str, Dict[str, Any]] = {}
_user_id_counter = 0


def register_user(username: str, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a new user. Uses in-memory store when database is unavailable.

    Raises
    ------
    ValueError
        If username or email is already taken.
    """
    global _user_id_counter

    # Try database first
    try:
        from backend.database.connection import get_session_factory
        from backend.models.user import User

        factory = get_session_factory()
        if factory is not None:
            db = factory()
            try:
                existing = db.query(User).filter(
                    (User.username == username) | (User.email == email)
                ).first()
                if existing:
                    raise ValueError("Username or email already registered.")

                new_user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    hashed_password=hash_password(password),
                    is_active=True,
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                logger.info("User registered in database: %s", username)
                return {
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "full_name": new_user.full_name,
                    "is_active": new_user.is_active,
                }
            finally:
                db.close()
    except ImportError:
        pass
    except ValueError:
        raise
    except Exception as e:
        logger.debug("Database unavailable for registration, using in-memory: %s", str(e))

    # Fallback to in-memory store
    if username in _in_memory_users:
        raise ValueError("Username already registered.")
    for u in _in_memory_users.values():
        if u["email"] == email:
            raise ValueError("Email already registered.")

    _user_id_counter += 1
    user_data = {
        "id": _user_id_counter,
        "username": username,
        "email": email,
        "full_name": full_name,
        "hashed_password": hash_password(password),
        "is_active": True,
    }
    _in_memory_users[username] = user_data
    logger.info("User registered in memory: %s", username)
    return {
        "id": user_data["id"],
        "username": username,
        "email": email,
        "full_name": full_name,
        "is_active": True,
    }


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user by username and password.

    Returns user data dict if credentials are valid, None otherwise.
    """
    # Try database first
    try:
        from backend.database.connection import get_session_factory
        from backend.models.user import User

        factory = get_session_factory()
        if factory is not None:
            db = factory()
            try:
                user = db.query(User).filter(User.username == username).first()
                if user and verify_password(password, user.hashed_password):
                    logger.info("User authenticated via database: %s", username)
                    return {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "is_active": user.is_active,
                    }
                return None
            finally:
                db.close()
    except Exception as e:
        logger.debug("Database unavailable for auth, using in-memory: %s", str(e))

    # Fallback to in-memory store
    user_data = _in_memory_users.get(username)
    if user_data and verify_password(password, user_data["hashed_password"]):
        logger.info("User authenticated via memory: %s", username)
        return {
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "is_active": user_data["is_active"],
        }
    return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Look up a user by username."""
    try:
        from backend.database.connection import get_session_factory
        from backend.models.user import User

        factory = get_session_factory()
        if factory is not None:
            db = factory()
            try:
                user = db.query(User).filter(User.username == username).first()
                if user:
                    return {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "is_active": user.is_active,
                    }
            finally:
                db.close()
    except Exception:
        pass

    user_data = _in_memory_users.get(username)
    if user_data:
        return {
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "is_active": user_data["is_active"],
        }
    return None
