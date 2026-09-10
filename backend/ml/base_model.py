"""
backend/ml/base_model.py

Abstract base class for all F1 PitWall AI machine learning models.
Defines the standard interface: train, predict, save_model, load_model.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import joblib

from backend.utils.logger import get_logger

logger = get_logger(__name__)

TRAINED_MODELS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "trained_models"
)


class BaseMLModel(ABC):
    """
    Abstract base class for ML models.

    All models must implement train(), predict(), and define a model_name.
    Serialization (save/load) is handled by the base class using joblib.
    """

    model_name: str = "base_model"
    model_version: str = "0.1.0"

    def __init__(self):
        self.model = None
        self.is_trained = False
        self.metrics: Dict[str, float] = {}
        self.feature_columns: list = []

    @abstractmethod
    def train(self, X, y, **kwargs) -> Dict[str, float]:
        """
        Train the model on features X and target y.

        Returns
        -------
        dict
            Training metrics (e.g. MAE, RMSE, R²).
        """
        pass

    @abstractmethod
    def predict(self, X) -> Any:
        """
        Generate predictions for input features X.

        Returns
        -------
        Predictions (array-like or dict).
        """
        pass

    def save_model(self, directory: Optional[str] = None) -> str:
        """
        Save the trained model to disk using joblib.

        Returns the file path where the model was saved.
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError(f"Model '{self.model_name}' has not been trained yet.")

        save_dir = directory or TRAINED_MODELS_DIR
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"{self.model_name}.joblib")

        model_data = {
            "model": self.model,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "metrics": self.metrics,
            "feature_columns": self.feature_columns,
            "is_trained": self.is_trained,
        }

        joblib.dump(model_data, filepath)
        logger.info("Model saved: %s → %s", self.model_name, filepath)
        return filepath

    def load_model(self, directory: Optional[str] = None) -> bool:
        """
        Load a trained model from disk.

        Returns True if loaded successfully, False otherwise.
        """
        load_dir = directory or TRAINED_MODELS_DIR
        filepath = os.path.join(load_dir, f"{self.model_name}.joblib")

        if not os.path.exists(filepath):
            logger.warning("Model file not found: %s", filepath)
            return False

        try:
            model_data = joblib.load(filepath)
            self.model = model_data["model"]
            self.model_name = model_data.get("model_name", self.model_name)
            self.model_version = model_data.get("model_version", self.model_version)
            self.metrics = model_data.get("metrics", {})
            self.feature_columns = model_data.get("feature_columns", [])
            self.is_trained = model_data.get("is_trained", True)
            logger.info("Model loaded: %s (v%s)", self.model_name, self.model_version)
            return True
        except Exception as e:
            logger.error("Failed to load model %s: %s", self.model_name, str(e))
            return False

    def get_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "is_trained": self.is_trained,
            "metrics": self.metrics,
            "feature_count": len(self.feature_columns),
            "feature_columns": self.feature_columns,
        }
