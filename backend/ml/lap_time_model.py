"""
backend/ml/lap_time_model.py

Lap Time Prediction Model for F1 PitWall AI.

Uses XGBoost regression to predict lap times based on features such as
tire compound, tire age, fuel-corrected lap number, and track conditions.
"""

from typing import Dict, Any, Optional
import numpy as np

from backend.ml.base_model import BaseMLModel
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LapTimeModel(BaseMLModel):
    """
    XGBoost-based lap time prediction model.

    Features:
        - TyreLife (int): laps on current tire set
        - Compound_encoded (int): tire compound as ordinal
        - LapNumber (int): lap number in session
        - FuelCorrectedLap (float): normalized lap progress (0-1)
        - TrackTemp (float): track temperature if available
        - AirTemp (float): air temperature if available

    Target:
        - LapTimeSeconds (float)
    """

    model_name = "lap_time_model"
    model_version = "0.1.0"

    COMPOUND_ENCODING = {
        "SOFT": 1, "MEDIUM": 2, "HARD": 3,
        "INTERMEDIATE": 4, "WET": 5, "UNKNOWN": 0,
    }

    FEATURE_COLUMNS = [
        "TyreLife", "Compound_encoded", "LapNumber",
        "FuelCorrectedLap", "Stint",
    ]

    def __init__(self):
        super().__init__()
        self.feature_columns = self.FEATURE_COLUMNS.copy()

    def train(self, X, y, **kwargs) -> Dict[str, float]:
        """
        Train the XGBoost lap time model.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            Training features.
        y : array-like, shape (n_samples,)
            Target lap times in seconds.

        Returns
        -------
        dict
            Metrics: MAE, RMSE, R².
        """
        try:
            from xgboost import XGBRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        except ImportError as e:
            raise RuntimeError(f"Required ML libraries not installed: {e}")

        test_size = kwargs.get("test_size", 0.2)
        random_state = kwargs.get("random_state", 42)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state,
        )

        self.model = XGBRegressor(
            n_estimators=kwargs.get("n_estimators", 200),
            max_depth=kwargs.get("max_depth", 6),
            learning_rate=kwargs.get("learning_rate", 0.1),
            random_state=random_state,
            n_jobs=-1,
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        y_pred = self.model.predict(X_test)

        self.metrics = {
            "mae": float(round(mean_absolute_error(y_test, y_pred), 4)),
            "rmse": float(round(np.sqrt(mean_squared_error(y_test, y_pred)), 4)),
            "r2": float(round(r2_score(y_test, y_pred), 4)),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        self.is_trained = True
        logger.info("LapTimeModel trained — MAE=%.4f RMSE=%.4f R²=%.4f",
                     self.metrics["mae"], self.metrics["rmse"], self.metrics["r2"])
        return self.metrics

    def predict(self, X) -> np.ndarray:
        """Predict lap times for input features."""
        if not self.is_trained or self.model is None:
            raise RuntimeError("LapTimeModel has not been trained. Call train() first.")
        return self.model.predict(X)

    @staticmethod
    def encode_compound(compound: str) -> int:
        """Convert compound string to numerical encoding."""
        return LapTimeModel.COMPOUND_ENCODING.get(
            compound.upper() if compound else "UNKNOWN", 0
        )
