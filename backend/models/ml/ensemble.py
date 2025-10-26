"""
Ensemble ML models (GradBoost, XGBoost, LightGBM)
"""

from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib


class EnsembleModel:
    """
    Ensemble of gradient boosting models
    - GradientBoosting (sklearn)
    - XGBoost
    - LightGBM
    """

    def __init__(self, weights: Optional[List[float]] = None):
        """
        Args:
            weights: Ensemble weights [gradboost, xgboost, lightgbm]
                     Default: [0.4, 0.35, 0.25]
        """
        self.weights = weights or [0.4, 0.35, 0.25]

        # Initialize models
        self.models = {
            'gradboost': GradientBoostingRegressor(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=5,
                min_samples_split=20,
                min_samples_leaf=10,
                subsample=0.8,
                random_state=42
            ),
            'xgboost': XGBRegressor(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=5,
                min_child_weight=5,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            ),
            'lightgbm': LGBMRegressor(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=5,
                num_leaves=31,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
        }

        self.feature_names: List[str] = []
        self._fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Train all models"""
        print("Training Ensemble Models...")

        self.feature_names = list(X.columns)

        # Train each model
        for name, model in self.models.items():
            print(f"  Training {name}...")
            model.fit(X, y)

        self._fitted = True
        print("✅ Ensemble training complete")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Weighted ensemble prediction"""
        if not self._fitted:
            raise ValueError("Model not fitted")

        predictions = []
        for name, model in self.models.items():
            pred = model.predict(X)
            predictions.append(pred)

        # Weighted average
        ensemble_pred = (
            predictions[0] * self.weights[0] +
            predictions[1] * self.weights[1] +
            predictions[2] * self.weights[2]
        )

        return ensemble_pred

    def predict_individual(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Get predictions from each model"""
        if not self._fitted:
            raise ValueError("Model not fitted")

        return {
            name: model.predict(X)
            for name, model in self.models.items()
        }

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Evaluate ensemble and individual models"""
        ensemble_pred = self.predict(X)
        individual_preds = self.predict_individual(X)

        metrics = {
            'ensemble': {
                'mae': mean_absolute_error(y, ensemble_pred),
                'r2': r2_score(y, ensemble_pred)
            }
        }

        for name, pred in individual_preds.items():
            metrics[name] = {
                'mae': mean_absolute_error(y, pred),
                'r2': r2_score(y, pred)
            }

        return metrics

    def feature_importance(self) -> pd.DataFrame:
        """Get average feature importance across models"""
        importance_dict = {}

        # GradBoost importance
        importance_dict['gradboost'] = self.models['gradboost'].feature_importances_

        # XGBoost importance
        importance_dict['xgboost'] = self.models['xgboost'].feature_importances_

        # LightGBM importance
        importance_dict['lightgbm'] = self.models['lightgbm'].feature_importances_

        # Average importance
        avg_importance = np.mean(list(importance_dict.values()), axis=0)

        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': avg_importance,
            **importance_dict
        }).sort_values('importance', ascending=False)

        return importance_df

    def save(self, path: str):
        """Save ensemble models"""
        joblib.dump({
            'models': self.models,
            'weights': self.weights,
            'feature_names': self.feature_names,
            'fitted': self._fitted
        }, path)
        print(f"✅ Ensemble saved to {path}")

    def load(self, path: str):
        """Load ensemble models"""
        data = joblib.load(path)
        self.models = data['models']
        self.weights = data['weights']
        self.feature_names = data['feature_names']
        self._fitted = data['fitted']
        print(f"✅ Ensemble loaded from {path}")
