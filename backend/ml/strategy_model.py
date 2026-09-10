"""
backend/ml/strategy_model.py

Strategy Model for F1 PitWall AI.

Combines outputs from lap time, tire degradation, and pit window models
to produce an integrated strategy recommendation.
"""

from typing import Dict, Any, Optional
import numpy as np

from backend.ml.base_model import BaseMLModel
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class StrategyModel(BaseMLModel):
    """
    Ensemble strategy model that combines sub-model outputs.

    This model orchestrates the lap_time, tire_degradation, and pit_window
    models to produce a unified strategy recommendation. It can also be
    trained independently as a meta-learner on strategy outcome data.
    """

    model_name = "strategy_model"
    model_version = "0.1.0"

    FEATURE_COLUMNS = [
        "predicted_lap_time", "predicted_degradation",
        "predicted_pit_window", "compound_encoded",
        "current_lap", "total_laps", "tire_age", "position",
    ]

    def __init__(self):
        super().__init__()
        self.feature_columns = self.FEATURE_COLUMNS.copy()
        self.sub_models_loaded = False

    def train(self, X, y, **kwargs) -> Dict[str, float]:
        """
        Train the strategy meta-model.

        Parameters
        ----------
        X : array-like
            Combined features including sub-model predictions.
        y : array-like
            Target strategy quality score or race outcome metric.

        Returns
        -------
        dict
            Training metrics.
        """
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        except ImportError as e:
            raise RuntimeError(f"Required ML libraries not installed: {e}")

        test_size = kwargs.get("test_size", 0.2)
        random_state = kwargs.get("random_state", 42)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state,
        )

        self.model = GradientBoostingRegressor(
            n_estimators=kwargs.get("n_estimators", 100),
            max_depth=kwargs.get("max_depth", 4),
            learning_rate=kwargs.get("learning_rate", 0.1),
            random_state=random_state,
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
            "StrategyModel trained — MAE=%.4f RMSE=%.4f R²=%.4f",
            self.metrics["mae"], self.metrics["rmse"], self.metrics["r2"],
        )
        return self.metrics

    def predict(self, X) -> np.ndarray:
        """Predict strategy quality score."""
        if not self.is_trained or self.model is None:
            raise RuntimeError("StrategyModel not trained. Call train() first.")
        return self.model.predict(X)
