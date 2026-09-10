"""
scripts/collect_f1_data.py

Command-line tool to load FastF1 race session data and export raw CSV files.

Usage
-----
    python scripts/collect_f1_data.py --year 2024 --race "Bahrain Grand Prix" --session R
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
from backend.services.export_service import export_session_raw_data
from backend.services.f1_data_service import get_session_summary
from backend.utils.logger import get_logger

logger = get_logger("scripts.collect_f1_data")


def main():
    parser = argparse.ArgumentParser(description="F1 PitWall AI — Command-line Data Collector")
    parser.add_argument("--year", type=int, required=True, help="Season year (e.g. 2024)")
    parser.add_argument("--race", type=str, required=True, help="Event / Grand Prix name (e.g. 'Monaco Grand Prix' or 'Monaco')")
    parser.add_argument("--session", type=str, default="R", help="Session code (FP1, FP2, FP3, Q, SQ, S, R). Default is 'R'")
    parser.add_argument("--preprocess", action="store_true", help="Run data cleaning and feature engineering after export")
    args = parser.parse_args()

    print("\n==============================================")
    print("F1 PitWall AI — Data Collection")
    print("==============================================")
    print(f"Season: {args.year}")
    print(f"Race:   {args.race}")
    print(f"Session: {args.session}\n")

    try:
        print("Loading FastF1 session data (this may take a moment on first download)...")
        summary = get_session_summary(args.year, args.race, args.session)
        
        print("\nExtracting and exporting raw datasets...")
        result = export_session_raw_data(args.year, args.race, args.session)

        processed_path = None
        if args.preprocess:
            print("\nRunning feature engineering & preprocessing pipeline...")
            from backend.services.f1_data_service import get_lap_data
            from backend.services.preprocessing_service import preprocess_laps, save_processed_data
            laps = get_lap_data(args.year, args.race, args.session)
            df_proc = preprocess_laps(laps)
            processed_path = save_processed_data(df_proc, args.year, args.race, args.session, label="laps")
            print(f"Processed dataset saved: {processed_path}")

        print("\n----------------------------------------------")
        print("COLLECTION SUMMARY")
        print("----------------------------------------------")
        print(f"Event:            {summary['EventName']}")
        print(f"Circuit/Location: {summary['Circuit']}")
        print(f"Drivers:          {result['DriverCount']}")
        print(f"Lap records:      {result['LapCount']}")
        print(f"Pit stop records: {result['PitStopCount']}")
        print(f"Weather records:  {result['WeatherRecordCount']}")
        print(f"Raw Export:       {result['TargetDirectory']}")
        if processed_path:
            print(f"Processed Export: {processed_path}")
        print("----------------------------------------------")
        print("Data saved successfully.\n")

    except Exception as e:
        logger.error("Data collection failed: %s", str(e))
        print(f"\n[ERROR] Data collection failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
