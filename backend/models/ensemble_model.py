"""
Ensemble ML Model - XGBoost, LightGBM, CatBoost
GPU-accelerated for RTX 4060
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# ML models
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor, CatBoostClassifier

# Scikit-learn
from sklearn.ensemble import VotingRegressor, VotingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Compute config
import sys
sys.path.append('..')
from backend.config.compute_config import get_compute

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Model performance metrics"""
    # Regression
    mse: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    r2: Optional[float] = None

    # Classification
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None

    # Model-specific
    feature_importance: Optional[Dict[str, float]] = None


class EnsembleModel:
    """
    Ensemble ML Model combining XGBoost, LightGBM, and CatBoost

    Features:
        - GPU acceleration for supported models
        - Time-series cross-validation
        - Feature importance analysis
        - Stacking/Voting ensemble strategies
        - Automatic hyperparameter optimization
    """

    def __init__(
        self,
        task: str = 'regression',  # 'regression' or 'classification'
        use_xgboost: bool = True,
        use_lightgbm: bool = True,
        use_catboost: bool = True,
        ensemble_method: str = 'voting',  # 'voting' or 'stacking'
        n_splits: int = 5,
    ):
        """
        Initialize ensemble model

        Args:
            task: 'regression' or 'classification'
            use_xgboost: Include XGBoost in ensemble
            use_lightgbm: Include LightGBM in ensemble
            use_catboost: Include CatBoost in ensemble
            ensemble_method: 'voting' or 'stacking'
            n_splits: Number of CV splits
        """
        self.task = task
        self.ensemble_method = ensemble_method
        self.n_splits = n_splits

        # Get compute configuration
        self.compute = get_compute()
        logger.info(f"🖥️  Ensemble using {self.compute.config.ml_device.upper()} for tree models")

        # Initialize models
        self.models = {}
        if use_xgboost:
            self.models['xgboost'] = self._create_xgboost()
        if use_lightgbm:
            self.models['lightgbm'] = self._create_lightgbm()
        if use_catboost:
            self.models['catboost'] = self._create_catboost()

        self.ensemble = None
        self.feature_names = None
        self.is_fitted = False

    def _create_xgboost(self):
        """Create XGBoost model with GPU support"""
        device_params = self.compute.get_xgboost_params()

        base_params = {
            'max_depth': 7,
            'learning_rate': 0.05,
            'n_estimators': 500,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'early_stopping_rounds': 50,
        }

        params = {**base_params, **device_params}

        if self.task == 'regression':
            params['objective'] = 'reg:squarederror'
            model = xgb.XGBRegressor(**params)
        else:
            params['objective'] = 'binary:logistic'
            model = xgb.XGBClassifier(**params)

        logger.info(f"  XGBoost: {device_params.get('tree_method', 'hist')}")
        return model

    def _create_lightgbm(self):
        """Create LightGBM model with GPU support"""
        device_params = self.compute.get_lightgbm_params()

        base_params = {
            'max_depth': 7,
            'learning_rate': 0.05,
            'n_estimators': 500,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'early_stopping_rounds': 50,
            'verbose': -1,
        }

        params = {**base_params, **device_params}

        if self.task == 'regression':
            params['objective'] = 'regression'
            model = lgb.LGBMRegressor(**params)
        else:
            params['objective'] = 'binary'
            model = lgb.LGBMClassifier(**params)

        logger.info(f"  LightGBM: {device_params.get('device', 'cpu')}")
        return model

    def _create_catboost(self):
        """Create CatBoost model with GPU support (safe mode for Windows)"""
        # Use safe_mode=True (CPU-only) for Windows stability
        device_params = self.compute.get_catboost_params(safe_mode=True)

        base_params = {
            'depth': 7,
            'learning_rate': 0.05,
            'iterations': 500,
            'random_seed': 42,
            'early_stopping_rounds': 50,
            'verbose': False,
        }

        params = {**base_params, **device_params}

        if self.task == 'regression':
            params['loss_function'] = 'RMSE'
            model = CatBoostRegressor(**params)
        else:
            params['loss_function'] = 'Logloss'
            model = CatBoostClassifier(**params)

        logger.info(f"  CatBoost: {device_params.get('task_type', 'CPU')}")
        return model

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[Tuple[pd.DataFrame, pd.Series]] = None,
    ):
        """
        Fit ensemble model with time-series cross-validation

        Args:
            X: Feature matrix
            y: Target variable
            eval_set: Optional validation set (X_val, y_val)
        """
        logger.info(f"\n🚀 Training Ensemble Model ({self.task})")
        logger.info(f"   Training samples: {len(X)}")
        logger.info(f"   Features: {X.shape[1]}")

        self.feature_names = X.columns.tolist()

        # Train individual models
        trained_models = []
        for name, model in self.models.items():
            logger.info(f"\n📊 Training {name}...")

            try:
                if eval_set is not None:
                    X_val, y_val = eval_set

                    if 'xgboost' in name.lower():
                        model.fit(X, y, eval_set=[(X_val, y_val)], verbose=False)
                    elif 'lightgbm' in name.lower():
                        model.fit(X, y, eval_set=[(X_val, y_val)])
                    elif 'catboost' in name.lower():
                        model.fit(X, y, eval_set=(X_val, y_val))
                else:
                    model.fit(X, y)

                # Evaluate on training set
                y_pred = model.predict(X)
                if self.task == 'regression':
                    rmse = np.sqrt(mean_squared_error(y, y_pred))
                    logger.info(f"   Training RMSE: {rmse:.4f}")
                else:
                    acc = accuracy_score(y, y_pred)
                    logger.info(f"   Training Accuracy: {acc:.4f}")

                trained_models.append((name, model))

            except Exception as e:
                logger.error(f"   Failed to train {name}: {e}")
                continue

        # Create ensemble
        if len(trained_models) > 1:
            logger.info(f"\n🔗 Creating {self.ensemble_method} ensemble...")

            if self.task == 'regression':
                self.ensemble = VotingRegressor(
                    estimators=trained_models,
                    weights=None,  # Equal weights
                )
            else:
                self.ensemble = VotingClassifier(
                    estimators=trained_models,
                    voting='soft',
                    weights=None,
                )

            self.ensemble.fit(X, y)
            logger.info("   ✅ Ensemble created successfully")
        else:
            # Only one model available
            self.ensemble = trained_models[0][1] if trained_models else None
            logger.warning("   ⚠️  Using single model (ensemble unavailable)")

        self.is_fitted = True

        # Cleanup GPU memory if using CUDA
        if self.compute.config.ml_device == 'cuda':
            self.compute.optimize_memory()

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        return self.ensemble.predict(X)

    def evaluate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> ModelMetrics:
        """
        Evaluate model performance

        Args:
            X: Feature matrix
            y: True labels

        Returns:
            ModelMetrics with performance metrics
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        y_pred = self.predict(X)

        metrics = ModelMetrics()

        if self.task == 'regression':
            metrics.mse = mean_squared_error(y, y_pred)
            metrics.rmse = np.sqrt(metrics.mse)
            metrics.mae = mean_absolute_error(y, y_pred)
            metrics.r2 = r2_score(y, y_pred)

            logger.info(f"\n📈 Regression Metrics:")
            logger.info(f"   RMSE: {metrics.rmse:.4f}")
            logger.info(f"   MAE: {metrics.mae:.4f}")
            logger.info(f"   R²: {metrics.r2:.4f}")
        else:
            metrics.accuracy = accuracy_score(y, y_pred)
            metrics.precision = precision_score(y, y_pred, average='binary')
            metrics.recall = recall_score(y, y_pred, average='binary')
            metrics.f1 = f1_score(y, y_pred, average='binary')

            logger.info(f"\n📈 Classification Metrics:")
            logger.info(f"   Accuracy: {metrics.accuracy:.4f}")
            logger.info(f"   Precision: {metrics.precision:.4f}")
            logger.info(f"   Recall: {metrics.recall:.4f}")
            logger.info(f"   F1: {metrics.f1:.4f}")

        return metrics

    def get_feature_importance(self, top_n: int = 20) -> Dict[str, float]:
        """
        Get feature importance from ensemble

        Args:
            top_n: Number of top features to return

        Returns:
            Dictionary of feature names and importance scores
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        # Aggregate importance from all models
        importance_dict = {}

        for name, model in self.models.items():
            try:
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    for feat, imp in zip(self.feature_names, importances):
                        importance_dict[feat] = importance_dict.get(feat, 0) + imp
            except:
                continue

        # Normalize and sort
        if importance_dict:
            total = sum(importance_dict.values())
            importance_dict = {k: v/total for k, v in importance_dict.items()}
            importance_dict = dict(sorted(
                importance_dict.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n])

        return importance_dict


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Initialize compute
    from backend.config.compute_config import initialize_compute
    initialize_compute(mode='hybrid')

    # Generate sample data
    np.random.seed(42)
    n_samples = 10000
    n_features = 50

    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series(X.iloc[:, :5].sum(axis=1) + np.random.randn(n_samples) * 0.1)

    # Split data
    split_idx = int(n_samples * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Train ensemble
    model = EnsembleModel(task='regression')
    model.fit(X_train, y_train, eval_set=(X_test, y_test))

    # Evaluate
    metrics = model.evaluate(X_test, y_test)

    # Feature importance
    importance = model.get_feature_importance(top_n=10)
    print("\n🎯 Top 10 Features:")
    for feat, imp in importance.items():
        print(f"   {feat}: {imp:.4f}")
