"""
backend/main.py

Entry point for the F1 PitWall AI FastAPI application.

Run with:
    uvicorn backend.main:app --reload

Swagger UI : http://127.0.0.1:8000/docs
ReDoc      : http://127.0.0.1:8000/redoc
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.f1 import router as f1_router
from backend.api.analytics import router as analytics_router
from backend.api.strategy import router as strategy_router
from backend.api.simulation import router as simulation_router
from backend.api.auth import router as auth_router
from backend.api.db import router as db_router
from backend.api.ml import router as ml_router
from backend.api.export import router as export_router
from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log key configuration on startup and handle graceful shutdown."""
    logger.info(
        "%s API started | env=%s | debug=%s | host=%s:%s",
        settings.APP_NAME,
        settings.APP_ENV,
        settings.DEBUG,
        settings.BACKEND_HOST,
        settings.BACKEND_PORT,
    )
    yield
    logger.info("%s API shutting down.", settings.APP_NAME)


# ------------------------------------------------------------------ #
# Application factory                                                  #
# ------------------------------------------------------------------ #

app = FastAPI(
    title="F1 PitWall AI API",
    description=(
        "Intelligent Race Strategy and Decision Support System. "
        "Provides endpoints for race analytics, tire performance, "
        "pit-stop strategy, AI predictions, and what-if simulations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ------------------------------------------------------------------ #
# Routers                                                              #
# ------------------------------------------------------------------ #

app.include_router(f1_router)
app.include_router(analytics_router)
app.include_router(strategy_router)
app.include_router(simulation_router)
app.include_router(auth_router)
app.include_router(db_router)
app.include_router(ml_router)
app.include_router(export_router)

# Allow the Streamlit frontend (running on a different port) to reach the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Tighten in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #

@app.get("/", tags=["Root"], summary="Welcome message")
async def root() -> dict:
    """
    Root endpoint.

    Returns a welcome message and the current running status of the API.
    """
    return {
        "message": "Welcome to F1 PitWall AI API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict:
    """
    Health-check endpoint.

    Called by the Streamlit frontend to confirm the backend is reachable.
    Returns ``"healthy"`` when the service is up and able to respond.
    """
    logger.debug("Health check requested.")
    return {
        "status": "healthy",
        "service": "F1 PitWall AI API",
        "version": "1.0.0",
    }


@app.get("/status", tags=["Status"], summary="System component status")
async def system_status() -> dict:
    """
    System status endpoint.

    Returns operational status of backend, FastF1 cache, and database connectivity.
    """
    from backend.services.f1_data_service import get_fastf1_status
    from backend.database.connection import is_database_available

    db_connected = is_database_available()
    return {
        "backend": "connected",
        "fastf1": get_fastf1_status(),
        "database": "connected" if db_connected else "disconnected",
        "version": "1.0.0",
    }
