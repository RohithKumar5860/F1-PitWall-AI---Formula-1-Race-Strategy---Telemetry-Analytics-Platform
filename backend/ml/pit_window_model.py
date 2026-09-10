"""
backend/ml/pit_window_model.py

Pit Window Prediction Model for F1 PitWall AI.

Predicts a recommended pit stop window (range of laps) based on
current tire state, pace evolution, and historical patterns.
Returns a lap range with confidence, not a single guaranteed lap.
"""

from typing import Dict, Any
import numpy as np

from backend.ml.base_model import BaseMLModel
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class PitWindowModel(BaseMLModel):
    """
    Classification/regression model predicting optimal pit window.

    Features:
        - Compound_encoded (int)
        - TyreLife (int)
        - Stint (int)
        - CurrentLap (int)
        - TotalLaps (int)
        - RemainingLaps (int)
        - AvgRecentPace (float): average pace over last 5 laps
        - PaceDropoff (float): pace difference between recent and best laps

    Target:
        - LapsUntilPit (int): laps remaining before optimal pit
    """

    model_name = "pit_window_model"
    model_version = "0.1.0"

    FEATURE_COLUMNS = [
        "Compound_encoded", "TyreLife", "Stint", "CurrentLap",
        "TotalLaps", "RemainingLaps", "AvgRecentPace", "PaceDropoff",
    ]

    def __init__(self):
        super().__init__()
        self.feature_columns = self.FEATURE_COLUMNS.copy()

    def train(self, X, y, **kwargs) -> Dict[str, float]:
        """
        Train the pit window model using RandomForest.

        Parameters
        ----------
        X : array-like
            Training features.
        y : array-like
            Target (laps until actual pit stop occurred).

        Returns
        -------
        dict
            Training metrics.
        """
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        except ImportError as e:
            raise RuntimeError(f"Required ML libraries not installed: {e}")

        test_size = kwargs.get("test_size", 0.2)
        random_state = kwargs.get("random_state", 42)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state,
        )

        self.model = RandomForestRegressor(
            n_estimators=kwargs.get("n_estimators", 200),
            max_depth=kwargs.get("max_depth", 8),
            random_state=random_state,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)

        self.metrics = {
            "mae": float(round(mean_absolute_error(y_test, y_pred), 4)),
            "rmse": float(round(np.sqrt(mean_squared_error(y_test, y_pred)), 4)),
            "r2": float(round(r2_score(y_test, y_pred), 4)),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }
        self.is_trained = True
        logger.info(
            "PitWindowModel trained — MAE=%.4f RMSE=%.4f R²=%.4f",
            self.metrics["mae"], self.metrics["rmse"], self.metrics["r2"],
        )
        return self.metrics

    def predict(self, X) -> np.ndarray:
        """Predict laps until optimal pit stop."""
        if not self.is_trained or self.model is None:
            raise RuntimeError("PitWindowModel not trained. Call train() first.")
        return self.model.predict(X)

    def predict_window(self, X, window_margin: int = 3) -> Dict[str, Any]:
        """
        Predict a pit window range with confidence.

        Returns
        -------
        dict with 'predicted_lap', 'window_start', 'window_end', 'confidence'.
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("PitWindowModel not trained.")

        predictions = self.model.predict(X)

        # Use individual tree predictions for confidence estimation
        X_arr = X.values if hasattr(X, "values") else X
        tree_predictions = np.array([
            tree.predict(X_arr) for tree in self.model.estimators_
        ])
        std_dev = np.std(tree_predictions, axis=0)

        results = []
        for i in range(len(predictions)):
            pred_laps = max(1, int(round(predictions[i])))
            confidence = max(0.0, min(1.0, 1.0 - (std_dev[i] / (pred_laps + 1))))

            results.append({
                "predicted_laps_until_pit": pred_laps,
                "window_start": max(1, pred_laps - window_margin),
                "window_end": pred_laps + window_margin,
                "confidence": round(float(confidence), 3),
            })

        return results
