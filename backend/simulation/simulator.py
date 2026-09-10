"""
backend/simulation/simulator.py

What-If Race Strategy Simulator for F1 PitWall AI.

Compares two user-defined race strategies by estimating total race time
using simplified tire degradation curves and pit stop losses.

DISCLAIMER: Model-based estimate using simplified degradation curves.
Not a real race prediction.
"""

from typing import Dict, Any, List
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# Degradation Curves (seconds per lap lost, per compound)              #
# ------------------------------------------------------------------ #

DEGRADATION_PROFILES = {
    "SOFT": {
        "base_offset": -0.8,    # Faster than baseline initially
        "deg_per_lap": 0.065,   # Seconds lost per lap of tire age
        "cliff_lap": 22,        # Lap where degradation accelerates
        "cliff_multiplier": 2.5,
    },
    "MEDIUM": {
        "base_offset": 0.0,
        "deg_per_lap": 0.040,
        "cliff_lap": 32,
        "cliff_multiplier": 2.0,
    },
    "HARD": {
        "base_offset": 0.6,
        "deg_per_lap": 0.025,
        "cliff_lap": 45,
        "cliff_multiplier": 1.8,
    },
    "INTERMEDIATE": {
        "base_offset": 2.5,
        "deg_per_lap": 0.035,
        "cliff_lap": 35,
        "cliff_multiplier": 2.0,
    },
    "WET": {
        "base_offset": 5.0,
        "deg_per_lap": 0.045,
        "cliff_lap": 28,
        "cliff_multiplier": 2.2,
    },
}


def _estimate_lap_time(base_lap_time: float, compound: str, tire_age: int) -> float:
    """
    Estimate a single lap time based on compound and tire age.

    Uses a simplified degradation model:
    - Fresh tires have a base offset (softs are faster, hards slower)
    - Linear degradation per lap
    - Cliff effect when tire age exceeds compound-specific threshold
    """
    profile = DEGRADATION_PROFILES.get(
        compound.upper(), DEGRADATION_PROFILES["MEDIUM"]
    )

    lap_time = base_lap_time + profile["base_offset"]

    if tire_age <= profile["cliff_lap"]:
        lap_time += profile["deg_per_lap"] * tire_age
    else:
        # Pre-cliff degradation
        lap_time += profile["deg_per_lap"] * profile["cliff_lap"]
        # Post-cliff accelerated degradation
        extra_laps = tire_age - profile["cliff_lap"]
        lap_time += profile["deg_per_lap"] * profile["cliff_multiplier"] * extra_laps

    return round(lap_time, 3)


def _format_race_time(total_seconds: float) -> str:
    """Convert total seconds to HH:MM:SS.sss format."""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:06.3f}"
    return f"{minutes}:{seconds:06.3f}"


def _simulate_strategy(
    strategy_name: str,
    stints: List[Dict[str, Any]],
    base_lap_time: float,
    pit_loss_seconds: float,
    total_laps: int,
) -> Dict[str, Any]:
    """
    Simulate a single race strategy.

    Parameters
    ----------
    strategy_name : str
        Label for this strategy.
    stints : list
        List of {"compound": str, "stint_length": int} dicts.
    base_lap_time : float
        Baseline lap time in seconds.
    pit_loss_seconds : float
        Time lost per pit stop in seconds.
    total_laps : int
        Total scheduled race laps.

    Returns
    -------
    dict
        SimulationStrategyResult-compatible dict.
    """
    stint_results = []
    total_time = 0.0
    pit_stops = max(0, len(stints) - 1)
    total_pit_loss = pit_stops * pit_loss_seconds
    total_time += total_pit_loss

    for idx, stint in enumerate(stints):
        compound = stint["compound"].upper()
        stint_length = stint["stint_length"]
        profile = DEGRADATION_PROFILES.get(compound, DEGRADATION_PROFILES["MEDIUM"])

        stint_lap_times = []
        for lap_in_stint in range(stint_length):
            lt = _estimate_lap_time(base_lap_time, compound, lap_in_stint)
            stint_lap_times.append(lt)

        stint_total = sum(stint_lap_times)
        stint_avg = stint_total / len(stint_lap_times) if stint_lap_times else base_lap_time

        total_time += stint_total

        stint_results.append({
            "stint_number": idx + 1,
            "compound": compound,
            "stint_length": stint_length,
            "avg_lap_time": round(stint_avg, 3),
            "total_stint_time": round(stint_total, 3),
            "degradation_per_lap": profile["deg_per_lap"],
        })

    return {
        "name": strategy_name,
        "total_race_time": round(total_time, 3),
        "total_race_time_formatted": _format_race_time(total_time),
        "pit_stops": pit_stops,
        "total_pit_loss": round(total_pit_loss, 3),
        "stints": stint_results,
    }


def compare_strategies(
    circuit: str,
    total_laps: int,
    base_lap_time: float,
    pit_loss_seconds: float,
    strategy_a_name: str,
    strategy_a_stints: List[Dict[str, Any]],
    strategy_b_name: str,
    strategy_b_stints: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare two race strategies and return side-by-side simulation results.

    Parameters
    ----------
    circuit : str
        Circuit name.
    total_laps : int
        Total scheduled race laps.
    base_lap_time : float
        Baseline lap time in seconds.
    pit_loss_seconds : float
        Time lost per pit stop.
    strategy_a_name : str
        Label for strategy A.
    strategy_a_stints : list
        Stints for strategy A.
    strategy_b_name : str
        Label for strategy B.
    strategy_b_stints : list
        Stints for strategy B.

    Returns
    -------
    dict
        SimulationResult-compatible dict with both strategies and comparison.
    """
    logger.info(
        "Simulation: circuit=%s laps=%d base=%.3f pit_loss=%.1f",
        circuit, total_laps, base_lap_time, pit_loss_seconds,
    )

    result_a = _simulate_strategy(
        strategy_a_name, strategy_a_stints, base_lap_time, pit_loss_seconds, total_laps,
    )
    result_b = _simulate_strategy(
        strategy_b_name, strategy_b_stints, base_lap_time, pit_loss_seconds, total_laps,
    )

    time_delta = result_a["total_race_time"] - result_b["total_race_time"]
    faster = strategy_a_name if time_delta <= 0 else strategy_b_name

    return {
        "circuit": circuit,
        "total_laps": total_laps,
        "strategy_a": result_a,
        "strategy_b": result_b,
        "time_delta": round(time_delta, 3),
        "time_delta_formatted": f"{abs(time_delta):.3f}s",
        "faster_strategy": faster,
        "disclaimer": (
            "Model-based estimate using simplified degradation curves. "
            "Not a real race prediction. Actual race outcomes depend on "
            "traffic, safety cars, weather changes, driver skill, and many "
            "other factors not modeled here."
        ),
    }
