"""
Signal Generator
Loads trained models and generates trading signals from features
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import json
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generates trading signals using trained models
    Supports: XGBoost, LSTM, PPO, Ensemble
    """

    def __init__(self, model_path: str):
        """
        Args:
            model_path: Path to trained model file
                       (.json for XGBoost, .pth for LSTM, .zip for PPO)
        """
        self.model_path = Path(model_path)
        self.model = None
        self.model_type = self._detect_model_type()
        self.feature_names = []

        logger.info(f"📊 SignalGenerator initialized")
        logger.info(f"   Model: {self.model_path.name}")
        logger.info(f"   Type: {self.model_type}")

    def _detect_model_type(self) -> str:
        """Detect model type from file extension"""
        suffix = self.model_path.suffix.lower()

        if suffix == '.json':
            return 'xgboost'
        elif suffix == '.pth':
            return 'lstm'
        elif suffix == '.zip':
            return 'ppo'
        elif suffix == '.pkl':
            return 'ensemble'
        else:
            raise ValueError(f"Unknown model type: {suffix}")

    async def load_model(self):
        """Load the trained model"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        logger.info(f"📥 Loading model: {self.model_path}")

        if self.model_type == 'xgboost':
            import xgboost as xgb
            self.model = xgb.Booster()
            self.model.load_model(str(self.model_path))

            # Load feature names from model
            self.feature_names = self.model.feature_names
            logger.info(f"   ✅ XGBoost model loaded ({len(self.feature_names)} features)")

        elif self.model_type == 'lstm':
            import torch
            self.model = torch.load(str(self.model_path))
            self.model.eval()
            logger.info(f"   ✅ LSTM model loaded")

        elif self.model_type == 'ppo':
            from stable_baselines3 import PPO
            self.model = PPO.load(str(self.model_path))
            logger.info(f"   ✅ PPO model loaded")

        elif self.model_type == 'ensemble':
            import pickle
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"   ✅ Ensemble model loaded")

        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    async def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Generate trading signal from features

        Args:
            features: Dict of feature values (from RealtimeFeatureCalculator)

        Returns:
            Signal dict:
            {
                'direction': 'long' | 'short' | 'neutral',
                'confidence': 0.0-1.0,
                'probability': 0.0-1.0,
                'metadata': {...}
            }
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            if self.model_type == 'xgboost':
                return await self._generate_xgboost_signal(features)
            elif self.model_type == 'lstm':
                return await self._generate_lstm_signal(features)
            elif self.model_type == 'ppo':
                return await self._generate_ppo_signal(features)
            elif self.model_type == 'ensemble':
                return await self._generate_ensemble_signal(features)
        except Exception as e:
            logger.error(f"Error generating signal: {e}", exc_info=True)
            return None

    async def _generate_xgboost_signal(self, features: Dict) -> Dict:
        """Generate signal from XGBoost model"""
        import xgboost as xgb

        # Prepare features in correct order
        feature_values = []
        for fname in self.feature_names:
            if fname in features:
                feature_values.append(features[fname])
            else:
                logger.warning(f"Missing feature: {fname}, using 0")
                feature_values.append(0.0)

        # Convert to DMatrix
        X = np.array([feature_values])
        dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)

        # Predict
        pred_proba = self.model.predict(dmatrix)[0]

        # XGBoost binary classification: pred_proba is probability of class 1 (price up)
        direction = 'long' if pred_proba > 0.5 else 'short'
        confidence = abs(pred_proba - 0.5) * 2  # Scale to 0-1

        return {
            'direction': direction,
            'confidence': confidence,
            'probability': pred_proba,
            'metadata': {
                'model_type': 'xgboost',
                'raw_prediction': float(pred_proba)
            }
        }

    async def _generate_lstm_signal(self, features: Dict) -> Dict:
        """Generate signal from LSTM model"""
        import torch

        # Prepare sequence (LSTM needs sequence of candles)
        # For now, use single candle (you may want to keep a sequence buffer)
        feature_values = list(features.values())
        X = torch.FloatTensor([feature_values]).unsqueeze(0)  # (1, 1, n_features)

        # Predict
        with torch.no_grad():
            output = self.model(X)
            pred_proba = torch.sigmoid(output).item()

        direction = 'long' if pred_proba > 0.5 else 'short'
        confidence = abs(pred_proba - 0.5) * 2

        return {
            'direction': direction,
            'confidence': confidence,
            'probability': pred_proba,
            'metadata': {
                'model_type': 'lstm',
                'raw_prediction': float(pred_proba)
            }
        }

    async def _generate_ppo_signal(self, features: Dict) -> Dict:
        """Generate signal from PPO RL model"""
        # PPO takes observation and returns action
        obs = np.array(list(features.values()), dtype=np.float32)

        # Predict action
        action, _states = self.model.predict(obs, deterministic=True)

        # PPO action space: 0=hold, 1=buy, 2=sell (depends on your env)
        direction_map = {0: 'neutral', 1: 'long', 2: 'short'}
        direction = direction_map.get(int(action), 'neutral')

        # PPO doesn't give confidence easily, use value function
        confidence = 0.7  # Default confidence

        return {
            'direction': direction,
            'confidence': confidence,
            'probability': None,
            'metadata': {
                'model_type': 'ppo',
                'action': int(action)
            }
        }

    async def _generate_ensemble_signal(self, features: Dict) -> Dict:
        """Generate signal from ensemble model"""
        # Prepare features
        X = pd.DataFrame([features])

        # Predict with ensemble
        pred_proba = self.model.predict_proba(X)[0, 1]  # Probability of class 1

        direction = 'long' if pred_proba > 0.5 else 'short'
        confidence = abs(pred_proba - 0.5) * 2

        return {
            'direction': direction,
            'confidence': confidence,
            'probability': pred_proba,
            'metadata': {
                'model_type': 'ensemble',
                'raw_prediction': float(pred_proba)
            }
        }

    def get_feature_importance(self) -> Optional[Dict]:
        """Get feature importance from model (XGBoost only for now)"""
        if self.model_type != 'xgboost':
            return None

        importance = self.model.get_score(importance_type='gain')
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
