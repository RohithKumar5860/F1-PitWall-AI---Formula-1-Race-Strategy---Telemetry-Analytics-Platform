"""
backend/strategy/engine.py

Rule-Based Strategy Engine for F1 PitWall AI.

Provides pit-stop timing recommendations based on historical compound
performance characteristics, tire age, race progress, and weather conditions.

DISCLAIMER: This is a public-data decision-support system using historical
averages. It is NOT a real F1 team strategy tool.
"""

from typing import Dict, Any, Optional
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# Historical Compound Performance Reference Data                       #
# ------------------------------------------------------------------ #

# Average optimal stint lengths (laps) by compound, derived from
# 2022-2024 season historical averages across all circuits.
COMPOUND_STINT_REFERENCE = {
    "SOFT": {"avg_stint": 18, "min_stint": 10, "max_stint": 25, "deg_rate": 0.065},
    "MEDIUM": {"avg_stint": 28, "min_stint": 18, "max_stint": 38, "deg_rate": 0.040},
    "HARD": {"avg_stint": 38, "min_stint": 25, "max_stint": 50, "deg_rate": 0.025},
    "INTERMEDIATE": {"avg_stint": 30, "min_stint": 5, "max_stint": 45, "deg_rate": 0.035},
    "WET": {"avg_stint": 25, "min_stint": 5, "max_stint": 40, "deg_rate": 0.045},
}

# Compound transition preferences (from -> recommended next)
COMPOUND_TRANSITIONS = {
    "SOFT": ["MEDIUM", "HARD"],
    "MEDIUM": ["HARD", "SOFT"],
    "HARD": ["MEDIUM", "SOFT"],
    "INTERMEDIATE": ["INTERMEDIATE", "SOFT", "MEDIUM"],
    "WET": ["WET", "INTERMEDIATE"],
}

# Temperature thresholds affecting strategy
TRACK_TEMP_THRESHOLDS = {
    "cold": 25.0,    # Below this: harder compounds degrade less
    "optimal": 40.0, # Sweet spot
    "hot": 50.0,     # Above this: softer compounds degrade faster
}


def recommend_strategy(
    driver: str,
    circuit: str,
    current_lap: int,
    total_laps: int,
    current_compound: str,
    tire_age: int,
    position: Optional[int] = None,
    air_temp: Optional[float] = None,
    track_temp: Optional[float] = None,
    rainfall: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Generate a pit-stop strategy recommendation.

    Uses rule-based logic derived from historical F1 compound performance
    data. Factors in tire age, race progress, weather, and compound
    characteristics.

    Parameters
    ----------
    driver : str
        Driver 3-letter code.
    circuit : str
        Circuit name.
    current_lap : int
        Current race lap.
    total_laps : int
        Total scheduled laps.
    current_compound : str
        Current tire compound.
    tire_age : int
        Laps on current tires.
    position : int, optional
        Current race position.
    air_temp : float, optional
        Air temperature °C.
    track_temp : float, optional
        Track temperature °C.
    rainfall : bool, optional
        Whether rain is occurring.

    Returns
    -------
    dict
        Strategy recommendation with pit window, compound, and explanation.
    """
    logger.info(
        "Strategy request: driver=%s circuit=%s lap=%d/%d compound=%s age=%d",
        driver, circuit, current_lap, total_laps, current_compound, tire_age,
    )

    compound_upper = current_compound.upper()
    remaining_laps = total_laps - current_lap

    # ── Handle wet weather ─────────────────────────────────────────
    if rainfall:
        return _wet_weather_strategy(
            driver, circuit, current_lap, total_laps,
            compound_upper, tire_age, remaining_laps,
        )

    # ── Get compound reference data ────────────────────────────────
    ref = COMPOUND_STINT_REFERENCE.get(compound_upper, COMPOUND_STINT_REFERENCE["MEDIUM"])

    # ── Adjust stint length for temperature ────────────────────────
    adjusted_max = ref["max_stint"]
    if track_temp is not None:
        if track_temp > TRACK_TEMP_THRESHOLDS["hot"]:
            adjusted_max = int(ref["max_stint"] * 0.85)
        elif track_temp < TRACK_TEMP_THRESHOLDS["cold"]:
            adjusted_max = int(ref["max_stint"] * 1.10)

    # ── Calculate optimal pit window ───────────────────────────────
    remaining_tire_life = max(0, adjusted_max - tire_age)
    optimal_pit_lap = current_lap + max(1, remaining_tire_life - 3)
    pit_window_start = max(current_lap + 1, optimal_pit_lap - 3)
    pit_window_end = min(total_laps - 1, optimal_pit_lap + 3)

    # ── Determine urgency ──────────────────────────────────────────
    life_ratio = tire_age / adjusted_max if adjusted_max > 0 else 1.0
    if life_ratio >= 0.90:
        urgency = "HIGH"
    elif life_ratio >= 0.70:
        urgency = "MEDIUM"
    else:
        urgency = "LOW"

    # ── Select next compound ───────────────────────────────────────
    next_compounds = COMPOUND_TRANSITIONS.get(compound_upper, ["MEDIUM"])
    suggested_compound = _select_optimal_compound(
        next_compounds, remaining_laps, track_temp,
    )

    # ── Estimate next stint length ─────────────────────────────────
    next_ref = COMPOUND_STINT_REFERENCE.get(suggested_compound, COMPOUND_STINT_REFERENCE["MEDIUM"])
    estimated_stint = min(remaining_laps, next_ref["avg_stint"])

    # ── Check if no-stop to end is viable ──────────────────────────
    can_finish_no_stop = remaining_tire_life >= remaining_laps
    alternative = None
    if can_finish_no_stop and urgency != "HIGH":
        alternative = (
            f"No-stop strategy possible: {remaining_laps} laps remaining, "
            f"estimated {remaining_tire_life} laps of tire life left on {compound_upper}. "
            f"Consider staying out if pace remains competitive."
        )

    # ── Build explanation ──────────────────────────────────────────
    explanation = _build_explanation(
        driver, compound_upper, tire_age, adjusted_max,
        pit_window_start, pit_window_end, suggested_compound,
        urgency, track_temp, remaining_laps,
    )

    return {
        "recommended_pit_window": f"Lap {pit_window_start}-{pit_window_end}",
        "suggested_compound": suggested_compound,
        "estimated_stint_length": estimated_stint,
        "urgency": urgency,
        "explanation": explanation,
        "alternative_strategy": alternative,
        "disclaimer": (
            "Rule-based estimate using historical averages from public F1 data. "
            "Not a real-time race prediction or professional strategy tool."
        ),
    }


def _wet_weather_strategy(
    driver: str, circuit: str, current_lap: int, total_laps: int,
    compound: str, tire_age: int, remaining_laps: int,
) -> Dict[str, Any]:
    """Handle wet weather strategy with immediate pit recommendation."""
    if compound not in ("INTERMEDIATE", "WET"):
        return {
            "recommended_pit_window": f"Lap {current_lap}-{current_lap + 1}",
            "suggested_compound": "INTERMEDIATE",
            "estimated_stint_length": min(remaining_laps, 30),
            "urgency": "HIGH",
            "explanation": (
                f"Rain detected. {driver} is currently on {compound} (dry compound). "
                f"Immediate pit stop recommended to switch to INTERMEDIATE tires. "
                f"Staying on slick tires in wet conditions is extremely dangerous and slow."
            ),
            "alternative_strategy": "Switch to FULL WET if rain intensity is very high.",
            "disclaimer": (
                "Rule-based estimate using historical averages. "
                "Not a real-time race prediction."
            ),
        }

    ref = COMPOUND_STINT_REFERENCE.get(compound, COMPOUND_STINT_REFERENCE["INTERMEDIATE"])
    remaining_life = max(0, ref["avg_stint"] - tire_age)

    return {
        "recommended_pit_window": f"Lap {current_lap + remaining_life - 3}-{current_lap + remaining_life + 3}",
        "suggested_compound": "INTERMEDIATE" if compound == "WET" else "WET",
        "estimated_stint_length": min(remaining_laps, ref["avg_stint"]),
        "urgency": "MEDIUM" if remaining_life > 5 else "HIGH",
        "explanation": (
            f"{driver} is on {compound} tires (lap {tire_age}). "
            f"Monitor track conditions for potential switch to "
            f"{'INTERMEDIATE' if compound == 'WET' else 'slick tires if track dries'}."
        ),
        "alternative_strategy": "If track begins to dry, consider early switch to SOFT or MEDIUM.",
        "disclaimer": (
            "Rule-based estimate using historical averages. "
            "Not a real-time race prediction."
        ),
    }


def _select_optimal_compound(
    candidates: list, remaining_laps: int, track_temp: Optional[float],
) -> str:
    """Pick the best compound from candidates based on remaining laps and conditions."""
    if remaining_laps <= 15:
        # Short stint: prefer softer compound for pace
        for c in candidates:
            if c == "SOFT":
                return c
        return candidates[0]

    if remaining_laps >= 35:
        # Long stint: prefer harder compound for durability
        for c in candidates:
            if c == "HARD":
                return c
        for c in candidates:
            if c == "MEDIUM":
                return c

    # Default: medium for balanced performance
    for c in candidates:
        if c == "MEDIUM":
            return c

    return candidates[0]


def _build_explanation(
    driver: str, compound: str, tire_age: int, max_stint: int,
    pit_start: int, pit_end: int, next_compound: str,
    urgency: str, track_temp: Optional[float], remaining: int,
) -> str:
    """Construct a human-readable strategy explanation."""
    parts = [
        f"{driver} has completed {tire_age} laps on {compound} tires "
        f"(historical max ~{max_stint} laps for this compound).",
    ]

    if urgency == "HIGH":
        parts.append(
            f"Tire life is critically depleted. Recommend pitting in the "
            f"window Lap {pit_start}-{pit_end}."
        )
    elif urgency == "MEDIUM":
        parts.append(
            f"Tires are approaching their performance limit. Pit window "
            f"Lap {pit_start}-{pit_end} is recommended."
        )
    else:
        parts.append(
            f"Tires are in good condition. Pit window Lap {pit_start}-{pit_end} "
            f"offers an optimal switch point."
        )

    parts.append(f"Suggested next compound: {next_compound}.")

    if track_temp is not None:
        if track_temp > TRACK_TEMP_THRESHOLDS["hot"]:
            parts.append(f"Track temperature is high ({track_temp}°C) — softer compounds will degrade faster.")
        elif track_temp < TRACK_TEMP_THRESHOLDS["cold"]:
            parts.append(f"Track temperature is cool ({track_temp}°C) — harder compounds may struggle for grip.")

    return " ".join(parts)
