"""
scripts/train_models.py

CLI tool to train and serialize all F1 PitWall AI machine learning models.

Usage:
    python scripts/train_models.py
"""

import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.ml_service import train_all_models
from backend.utils.logger import get_logger

logger = get_logger("scripts.train_models")


def main():
    print("\n==============================================")
    print("F1 PitWall AI — Model Training Manager")
    print("==============================================")
    print("Training LapTimeModel (XGBoost)...")
    print("Training TireDegradationModel (GradientBoosting)...")
    print("Training PitWindowModel (RandomForest)...\n")

    try:
        metrics = train_all_models()
        print("----------------------------------------------")
        print("TRAINING METRICS SUMMARY")
        print("----------------------------------------------")
        for m_name, m_val in metrics.items():
            print(f"[{m_name}]")
            for k, v in m_val.items():
                print(f"  {k}: {v}")
        print("----------------------------------------------")
        print("All models successfully trained and serialized into trained_models/\n")

    except Exception as e:
        logger.error("Training script error: %s", str(e))
        print(f"[ERROR] Training failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
