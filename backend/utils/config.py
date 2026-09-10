"""
backend/utils/config.py

Centralised configuration management for F1 PitWall AI.
All settings are loaded from environment variables (via a .env file in
development).  The Settings object is instantiated once at module level and
imported wherever configuration is needed.
"""

import os
from typing import Optional

from dotenv import load_dotenv

# Load .env file from the project root (two levels up from this file).
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=_env_path, override=False)


class Settings:
    """
    Application-wide settings resolved from environment variables.

    All attributes have sensible defaults so the application can start
    even when some variables are absent (e.g. during testing).
    """

    # ------------------------------------------------------------------ #
    # Application                                                          #
    # ------------------------------------------------------------------ #
    APP_NAME: str = os.getenv("APP_NAME", "F1 PitWall AI")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # ------------------------------------------------------------------ #
    # Security & JWT                                                       #
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-use-32-plus-bytes!!")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # ------------------------------------------------------------------ #
    # FastF1 / Data                                                        #
    # ------------------------------------------------------------------ #
    FASTF1_CACHE_DIR: str = os.getenv("FASTF1_CACHE_DIR", "data/cache")

    # ------------------------------------------------------------------ #
    # Backend server                                                       #
    # ------------------------------------------------------------------ #
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    BACKEND_URL: str = os.getenv(
        "BACKEND_URL",
        f"http://{os.getenv('BACKEND_HOST', '127.0.0.1')}:{os.getenv('BACKEND_PORT', '8000')}",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Settings app={self.APP_NAME!r} env={self.APP_ENV!r} "
            f"debug={self.DEBUG} host={self.BACKEND_HOST}:{self.BACKEND_PORT}>"
        )


# Single shared instance — import this everywhere.
settings = Settings()
