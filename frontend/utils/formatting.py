"""
frontend/utils/formatting.py

Formatting utilities for lap times, compound colors, and display strings.
"""

from typing import Optional, Dict

COMPOUND_COLORS: Dict[str, str] = {
    "SOFT": "#FF3333",       # Red
    "MEDIUM": "#FFF000",     # Yellow
    "HARD": "#FFFFFF",       # White
    "INTERMEDIATE": "#39B54A", # Green
    "WET": "#00AEEF",        # Blue
    "UNKNOWN": "#888888",    # Gray
}


def format_laptime(seconds: Optional[float]) -> str:
    """Convert lap time in seconds to mm:ss.sss format."""
    if seconds is None or seconds <= 0:
        return "N/A"
    minutes = int(seconds // 60)
    rem_seconds = seconds % 60
    return f"{minutes}:{rem_seconds:06.3f}"


def get_compound_color(compound: Optional[str]) -> str:
    """Return hex color code for a tire compound."""
    if not compound:
        return COMPOUND_COLORS["UNKNOWN"]
    c_upper = str(compound).upper()
    return COMPOUND_COLORS.get(c_upper, COMPOUND_COLORS["UNKNOWN"])
