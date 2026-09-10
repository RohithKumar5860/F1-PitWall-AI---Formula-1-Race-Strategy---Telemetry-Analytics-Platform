"""
backend/api/analytics.py

FastAPI router for advanced race analytics endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from backend.services.f1_data_service import get_lap_data, get_driver_classification
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/lap-comparison", summary="Compare lap times between drivers")
async def lap_comparison(
    year: int = Query(..., description="Season year"),
    race: str = Query(..., description="Event name"),
    session: str = Query("R", description="Session type code"),
    drivers: str = Query(..., description="Comma-separated driver codes (e.g. VER,HAM,LEC)"),
) -> Dict[str, Any]:
    """Compare lap-by-lap timing data for specified drivers."""
    try:
        driver_list = [d.strip().upper() for d in drivers.split(",") if d.strip()]
        if len(driver_list) < 1:
            raise HTTPException(status_code=400, detail="Provide at least one driver code.")

        all_laps = get_lap_data(year, race, session)
        if not all_laps:
            return {"drivers": driver_list, "comparison": []}

        filtered = [l for l in all_laps if l.get("Driver") in driver_list]
        return {
            "year": year,
            "race": race,
            "session": session,
            "drivers": driver_list,
            "total_laps": len(filtered),
            "comparison": filtered,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Lap comparison error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sector-analysis", summary="Sector time breakdown by driver")
async def sector_analysis(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return sector-level analysis for all drivers."""
    try:
        laps = get_lap_data(year, race, session)
        if not laps:
            return {"sectors": []}

        # Aggregate sector times per driver
        from collections import defaultdict
        driver_sectors: Dict[str, Dict] = defaultdict(lambda: {
            "s1_times": [], "s2_times": [], "s3_times": [], "lap_count": 0
        })

        for lap in laps:
            drv = lap.get("Driver", "")
            s1 = lap.get("Sector1Seconds")
            s2 = lap.get("Sector2Seconds")
            s3 = lap.get("Sector3Seconds")
            if s1 and s2 and s3 and s1 > 0 and s2 > 0 and s3 > 0:
                driver_sectors[drv]["s1_times"].append(s1)
                driver_sectors[drv]["s2_times"].append(s2)
                driver_sectors[drv]["s3_times"].append(s3)
                driver_sectors[drv]["lap_count"] += 1

        result = []
        for drv, data in driver_sectors.items():
            if data["lap_count"] > 0:
                result.append({
                    "Driver": drv,
                    "BestS1": round(min(data["s1_times"]), 3),
                    "BestS2": round(min(data["s2_times"]), 3),
                    "BestS3": round(min(data["s3_times"]), 3),
                    "AvgS1": round(sum(data["s1_times"]) / len(data["s1_times"]), 3),
                    "AvgS2": round(sum(data["s2_times"]) / len(data["s2_times"]), 3),
                    "AvgS3": round(sum(data["s3_times"]) / len(data["s3_times"]), 3),
                    "LapCount": data["lap_count"],
                })

        result.sort(key=lambda x: x["BestS1"] + x["BestS2"] + x["BestS3"])
        return {"year": year, "race": race, "session": session, "sectors": result}

    except Exception as e:
        logger.error("Sector analysis error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/position-changes", summary="Position evolution data")
async def position_changes(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return lap-by-lap position data for all drivers."""
    try:
        laps = get_lap_data(year, race, session)
        if not laps:
            return {"positions": []}

        positions = []
        for lap in laps:
            pos = lap.get("Position")
            if pos is not None:
                positions.append({
                    "Driver": lap.get("Driver", ""),
                    "LapNumber": lap.get("LapNumber"),
                    "Position": pos,
                })

        return {
            "year": year,
            "race": race,
            "session": session,
            "positions": positions,
        }
    except Exception as e:
        logger.error("Position changes error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pace-distribution", summary="Driver lap pace statistics & distribution")
async def pace_distribution(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return statistical summary (median, mean, min, max, std, Q1, Q3) of lap times per driver."""
    try:
        laps = get_lap_data(year, race, session)
        if not laps:
            return {"distribution": []}

        import pandas as pd
        import numpy as np

        df = pd.DataFrame(laps)
        valid = df[df["LapTimeSeconds"].notna() & (df["LapTimeSeconds"] > 30)].copy()

        distribution = []
        for drv, group in valid.groupby("Driver"):
            times = group["LapTimeSeconds"].values
            if len(times) > 0:
                distribution.append({
                    "Driver": drv,
                    "Count": len(times),
                    "Mean": round(float(np.mean(times)), 3),
                    "Median": round(float(np.median(times)), 3),
                    "Min": round(float(np.min(times)), 3),
                    "Max": round(float(np.max(times)), 3),
                    "Std": round(float(np.std(times)), 3),
                    "Q1": round(float(np.percentile(times, 25)), 3),
                    "Q3": round(float(np.percentile(times, 75)), 3),
                })

        distribution.sort(key=lambda x: x["Median"])
        return {"year": year, "race": race, "session": session, "distribution": distribution}

    except Exception as e:
        logger.error("Pace distribution error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/degradation-summary", summary="Compound tire degradation summary")
async def degradation_summary(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Calculate empirical degradation rates per tire compound."""
    try:
        from backend.services.preprocessing_service import preprocess_laps
        laps = get_lap_data(year, race, session)
        if not laps:
            return {"compounds": []}

        df_proc = preprocess_laps(laps)
        if df_proc.empty or "StintDegradation" not in df_proc.columns:
            return {"compounds": []}

        summary = []
        for comp, group in df_proc.groupby("Compound"):
            if comp == "UNKNOWN" or len(group) < 3:
                continue
            deg_per_lap = group["StintDegradation"] / np.maximum(1, group["StintLapIndex"])
            avg_deg = float(deg_per_lap.mean())
            summary.append({
                "Compound": comp,
                "TotalLaps": len(group),
                "AvgLapTime": round(float(group["LapTimeSeconds"].mean()), 3),
                "DegradationPerLapSeconds": round(max(0.0, avg_deg), 4),
            })

        return {"year": year, "race": race, "session": session, "compounds": summary}

    except Exception as e:
        logger.error("Degradation summary error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/team-pace-comparison", summary="Compare race pace by team/constructor")
async def team_pace_comparison(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return race pace metrics aggregated by constructor/team."""
    try:
        import pandas as pd
        import numpy as np
        laps = get_lap_data(year, race, session)
        drivers = get_driver_classification(year, race, session)
        if not laps:
            return {"teams": []}

        df = pd.DataFrame(laps)
        drivers_df = pd.DataFrame(drivers)
        
        # Merge team name if missing from lap data
        if "TeamName" not in df.columns and not drivers_df.empty and "TeamName" in drivers_df.columns:
            team_map = dict(zip(drivers_df["DriverCode"], drivers_df["TeamName"]))
            df["TeamName"] = df["Driver"].map(team_map)

        valid = df[df["LapTimeSeconds"].notna() & (df["LapTimeSeconds"] > 30)].copy()
        if valid.empty:
            return {"teams": []}

        team_col = "TeamName" if "TeamName" in valid.columns else "Team"
        if team_col not in valid.columns:
            valid[team_col] = "Independent"

        result = []
        for team, group in valid.groupby(team_col):
            times = group["LapTimeSeconds"].values
            if len(times) > 0:
                q1 = float(np.percentile(times, 25))
                q3 = float(np.percentile(times, 75))
                result.append({
                    "Team": str(team),
                    "LapCount": len(times),
                    "MedianPace": round(float(np.median(times)), 3),
                    "MeanPace": round(float(np.mean(times)), 3),
                    "BestLap": round(float(np.min(times)), 3),
                    "IQR": round(q3 - q1, 3),
                    "StdDev": round(float(np.std(times)), 3),
                })

        result.sort(key=lambda x: x["MedianPace"])
        return {"year": year, "race": race, "session": session, "teams": result}
    except Exception as e:
        logger.error("Team pace comparison error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/long-run-analysis", summary="Stint pace and long-run degradation analysis")
async def long_run_analysis(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return long-run stint metrics for stints with at least 5 laps."""
    try:
        from backend.services.preprocessing_service import preprocess_laps
        laps = get_lap_data(year, race, session)
        if not laps:
            return {"stints": []}

        df_proc = preprocess_laps(laps)
        if df_proc.empty or "Stint" not in df_proc.columns:
            return {"stints": []}

        stint_data = []
        for (drv, stint), group in df_proc.groupby(["Driver", "Stint"]):
            if len(group) < 5:
                continue
            valid = group[group["LapTimeSeconds"].notna() & (group["LapTimeSeconds"] > 30)].sort_values("LapNumber")
            if len(valid) < 5:
                continue

            times = valid["LapTimeSeconds"].values
            initial_pace = float(np.mean(times[:3]))
            final_pace = float(np.mean(times[-3:]))
            compound = str(valid["Compound"].iloc[0]) if "Compound" in valid.columns else "UNKNOWN"

            stint_data.append({
                "Driver": str(drv),
                "Stint": int(stint),
                "Compound": compound,
                "LapsCount": len(valid),
                "StartLap": int(valid["LapNumber"].iloc[0]),
                "EndLap": int(valid["LapNumber"].iloc[-1]),
                "AvgPace": round(float(np.mean(times)), 3),
                "MedianPace": round(float(np.median(times)), 3),
                "InitialPace": round(initial_pace, 3),
                "FinalPace": round(final_pace, 3),
                "PaceDelta": round(final_pace - initial_pace, 3),
            })

        stint_data.sort(key=lambda x: x["AvgPace"])
        return {"year": year, "race": race, "session": session, "stints": stint_data}
    except Exception as e:
        logger.error("Long run analysis error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/consistency-analysis", summary="Driver lap time consistency and variance")
async def consistency_analysis(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Calculate driver pace variance and percentage of clean laps within threshold."""
    try:
        import pandas as pd
        import numpy as np
        laps = get_lap_data(year, race, session)
        if not laps:
            return {"consistency": []}

        df = pd.DataFrame(laps)
        valid = df[df["LapTimeSeconds"].notna() & (df["LapTimeSeconds"] > 30)].copy()
        if valid.empty:
            return {"consistency": []}

        result = []
        for drv, group in valid.groupby("Driver"):
            times = group["LapTimeSeconds"].values
            if len(times) < 5:
                continue
            med = float(np.median(times))
            within_half_sec = float(np.sum(np.abs(times - med) <= 0.5) / len(times) * 100)
            within_one_sec = float(np.sum(np.abs(times - med) <= 1.0) / len(times) * 100)

            result.append({
                "Driver": str(drv),
                "TotalLaps": len(times),
                "MedianPace": round(med, 3),
                "StdDev": round(float(np.std(times)), 3),
                "Variance": round(float(np.var(times)), 4),
                "PercentWithin05s": round(within_half_sec, 1),
                "PercentWithin1s": round(within_one_sec, 1),
            })

        result.sort(key=lambda x: x["StdDev"])
        return {"year": year, "race": race, "session": session, "consistency": result}
    except Exception as e:
        logger.error("Consistency analysis error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sector-delta-heatmap", summary="Sector time deltas relative to session best")
async def sector_delta_heatmap(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return sector time deltas relative to session fastest sectors."""
    return await sector_analysis(year, race, session)


@router.get("/tire-degradation-curves", summary="Lap-by-lap tire degradation curve data")
async def tire_degradation_curves(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return lap-by-lap tire age vs pace drop-off for plotting degradation curves."""
    try:
        from backend.services.preprocessing_service import preprocess_laps
        laps = get_lap_data(year, race, session)
        if not laps:
            return {"curves": []}

        df_proc = preprocess_laps(laps)
        if df_proc.empty or "TyreLife" not in df_proc.columns:
            return {"curves": []}

        curves = []
        for (comp, life), group in df_proc.groupby(["Compound", "TyreLife"]):
            if comp == "UNKNOWN" or pd.isna(life) or float(life) <= 0:
                continue
            valid_times = group[group["LapTimeSeconds"].notna() & (group["LapTimeSeconds"] > 30)]["LapTimeSeconds"]
            if valid_times.empty:
                continue

            curves.append({
                "Compound": str(comp),
                "TyreLife": int(life),
                "SampleCount": len(valid_times),
                "AvgLapTime": round(float(valid_times.mean()), 3),
                "MedianLapTime": round(float(valid_times.median()), 3),
            })

        curves.sort(key=lambda x: (x["Compound"], x["TyreLife"]))
        return {"year": year, "race": race, "session": session, "curves": curves}
    except Exception as e:
        logger.error("Tire degradation curves error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pit-stop-timeline", summary="Pit stop timeline and duration records")
async def pit_stop_timeline(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Return pit stop event records for timeline plotting."""
    try:
        from backend.services.f1_data_service import get_pitstop_data
        stops = get_pitstop_data(year, race, session)
        return {"year": year, "race": race, "session": session, "pitstops": stops}
    except Exception as e:
        logger.error("Pit stop timeline error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


