"""
frontend/utils/api_client.py

Centralized API client for communication between Streamlit and FastAPI.
Reads BACKEND_URL purely from the environment — no backend Python imports.
"""

import os
import time
from typing import Dict, Any, List, Optional
import requests


def get_backend_url() -> str:
    """Resolve backend base URL cleanly without trailing slash."""
    url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    return url.rstrip("/")


_last_api_error: Optional[str] = None


def get_last_error() -> Optional[str]:
    """Retrieve the most recent API error message for diagnostics."""
    return _last_api_error


def _parse_error(res: requests.Response) -> str:
    """Extract a readable error string from an API response."""
    content_type = res.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return res.json().get("detail", f"HTTP {res.status_code}")
        except Exception:
            pass
    return res.text[:200] if res.text else f"HTTP {res.status_code}"


def get_backend_status() -> Dict[str, Any]:
    """
    Query backend status endpoint (/status) and measure response latency.

    Returns dict with backend, fastf1, database status, latency_ms, and version.
    """
    global _last_api_error
    base = get_backend_url()
    start_time = time.time()

    try:
        res = requests.get(f"{base}/status", timeout=3)
        latency_ms = round((time.time() - start_time) * 1000, 1)
        if res.status_code == 200:
            data = res.json()
            _last_api_error = None
            return {
                "connected": True,
                "backend": data.get("backend", "connected"),
                "fastf1": data.get("fastf1", "ready"),
                "database": data.get("database", "disconnected"),
                "version": data.get("version", "1.0.0"),
                "latency_ms": latency_ms,
                "backend_url": base,
                "last_error": None,
            }
        _last_api_error = f"HTTP {res.status_code}: {res.text[:100]}"
    except Exception as e:
        _last_api_error = str(e)

    # Fallback: try /health endpoint
    try:
        res_h = requests.get(f"{base}/health", timeout=3)
        latency_ms = round((time.time() - start_time) * 1000, 1)
        if res_h.status_code == 200:
            _last_api_error = None
            return {
                "connected": True,
                "backend": "connected",
                "fastf1": "ready",
                "database": "disconnected",
                "version": "1.0.0",
                "latency_ms": latency_ms,
                "backend_url": base,
                "last_error": None,
            }
    except Exception as e:
        _last_api_error = str(e)

    return {
        "connected": False,
        "backend": "disconnected",
        "fastf1": "unavailable",
        "database": "disconnected",
        "version": "unknown",
        "latency_ms": 0.0,
        "backend_url": base,
        "last_error": _last_api_error,
    }


def check_backend() -> bool:
    """Check if the backend FastAPI service is online and reachable."""
    return get_backend_status()["connected"]


def get_seasons() -> List[int]:
    """Retrieve list of available F1 seasons."""
    global _last_api_error
    try:
        res = requests.get(f"{get_backend_url()}/f1/seasons", timeout=5)
        if res.status_code == 200:
            return res.json().get("seasons", [])
        _last_api_error = f"Seasons HTTP {res.status_code}"
    except Exception as e:
        _last_api_error = str(e)
    return list(range(2018, 2026))


def get_schedule(year: int) -> List[Dict[str, Any]]:
    """Retrieve event schedule for a season."""
    global _last_api_error
    try:
        res = requests.get(f"{get_backend_url()}/f1/seasons/{year}/schedule", timeout=10)
        if res.status_code == 200:
            return res.json().get("events", [])
        _last_api_error = f"Schedule HTTP {res.status_code}"
    except Exception as e:
        _last_api_error = str(e)
    return []


def get_session_summary(year: int, race: str, session: str = "R") -> Dict[str, Any]:
    """Retrieve high-level session summary metadata."""
    global _last_api_error
    params = {"year": year, "race": race, "session": session}
    try:
        res = requests.get(f"{get_backend_url()}/f1/session/summary", params=params, timeout=120)
        if res.status_code == 200:
            return res.json()
        err_msg = _parse_error(res)
        _last_api_error = err_msg
        raise RuntimeError(err_msg)
    except requests.RequestException as e:
        _last_api_error = str(e)
        raise RuntimeError(f"Backend connection error: {str(e)}")


def get_drivers(year: int, race: str, session: str = "R") -> List[Dict[str, Any]]:
    """Retrieve driver classification results."""
    global _last_api_error
    params = {"year": year, "race": race, "session": session}
    try:
        res = requests.get(f"{get_backend_url()}/f1/session/drivers", params=params, timeout=120)
        if res.status_code == 200:
            return res.json()
        err_msg = _parse_error(res)
        _last_api_error = err_msg
        raise RuntimeError(err_msg)
    except requests.RequestException as e:
        _last_api_error = str(e)
        raise RuntimeError(f"Backend connection error: {str(e)}")


def get_laps(year: int, race: str, session: str = "R", driver: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve lap-by-lap timing data."""
    global _last_api_error
    params = {"year": year, "race": race, "session": session}
    if driver:
        params["driver"] = driver
    try:
        res = requests.get(f"{get_backend_url()}/f1/session/laps", params=params, timeout=120)
        if res.status_code == 200:
            return res.json()
        err_msg = _parse_error(res)
        _last_api_error = err_msg
        raise RuntimeError(err_msg)
    except requests.RequestException as e:
        _last_api_error = str(e)
        raise RuntimeError(f"Backend connection error: {str(e)}")


def get_tires(year: int, race: str, session: str = "R") -> List[Dict[str, Any]]:
    """Retrieve tire compound and stint life data."""
    global _last_api_error
    params = {"year": year, "race": race, "session": session}
    try:
        res = requests.get(f"{get_backend_url()}/f1/session/tires", params=params, timeout=120)
        if res.status_code == 200:
            return res.json()
        err_msg = _parse_error(res)
        _last_api_error = err_msg
        raise RuntimeError(err_msg)
    except requests.RequestException as e:
        _last_api_error = str(e)
        raise RuntimeError(f"Backend connection error: {str(e)}")


def get_pitstops(year: int, race: str, session: str = "R") -> List[Dict[str, Any]]:
    """Retrieve pit stop stint transition records."""
    global _last_api_error
    params = {"year": year, "race": race, "session": session}
    try:
        res = requests.get(f"{get_backend_url()}/f1/session/pitstops", params=params, timeout=120)
        if res.status_code == 200:
            return res.json()
        err_msg = _parse_error(res)
        _last_api_error = err_msg
        raise RuntimeError(err_msg)
    except requests.RequestException as e:
        _last_api_error = str(e)
        raise RuntimeError(f"Backend connection error: {str(e)}")


def get_weather(year: int, race: str, session: str = "R") -> List[Dict[str, Any]]:
    """Retrieve weather observations."""
    global _last_api_error
    params = {"year": year, "race": race, "session": session}
    try:
        res = requests.get(f"{get_backend_url()}/f1/session/weather", params=params, timeout=120)
        if res.status_code == 200:
            return res.json()
        err_msg = _parse_error(res)
        _last_api_error = err_msg
        raise RuntimeError(err_msg)
    except requests.RequestException as e:
        _last_api_error = str(e)
        raise RuntimeError(f"Backend connection error: {str(e)}")
