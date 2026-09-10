"""
backend/ml/tire_degradation_model.py

Tire Degradation Prediction Model for F1 PitWall AI.

Predicts tire performance loss per lap based on compound type,
stint length, track conditions, and historical degradation patterns.
"""

from typing import Dict, Any
import numpy as np

from backend.ml.base_model import BaseMLModel
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TireDegradationModel(BaseMLModel):
    """
    Regression model predicting tire degradation rate.

    Features:
        - Compound_encoded (int)
        - TyreLife (int)
        - Stint (int)
        - LapNumber (int)
        - TrackTemp (float, optional)

    Target:
        - DegradationRate (float): seconds lost compared to stint-start pace
    """

    model_name = "tire_degradation_model"
    model_version = "0.1.0"

    FEATURE_COLUMNS = [
        "Compound_encoded", "TyreLife", "Stint", "LapNumber",
    ]

    def __init__(self):
        super().__init__()
        self.feature_columns = self.FEATURE_COLUMNS.copy()

    def train(self, X, y, **kwargs) -> Dict[str, float]:
        """
        Train the tire degradation model using scikit-learn GradientBoosting.

        Parameters
        ----------
        X : array-like
            Training features.
        y : array-like
            Target degradation values.

        Returns
        -------
        dict
            Training metrics (MAE, RMSE, R²).
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
            n_estimators=kwargs.get("n_estimators", 150),
            max_depth=kwargs.get("max_depth", 5),
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
            "TireDegradationModel trained — MAE=%.4f RMSE=%.4f R²=%.4f",
            self.metrics["mae"], self.metrics["rmse"], self.metrics["r2"],
        )
        return self.metrics

    def predict(self, X) -> np.ndarray:
        """Predict tire degradation for given features."""
        if not self.is_trained or self.model is None:
            raise RuntimeError("TireDegradationModel not trained. Call train() first.")
        return self.model.predict(X)
