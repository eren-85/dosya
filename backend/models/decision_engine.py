"""
Unified Decision Engine
Combines: PPO + Ensemble + LSTM + Technical Analysis

Usage:
    from backend.models.decision_engine import DecisionEngine

    engine = DecisionEngine()
    decision = engine.decide(symbol='BTCUSDT', timeframe='1d')

    print(decision)
    # {
    #     'action': 'LONG',
    #     'confidence': 0.85,
    #     'entry': 68500,
    #     'stop_loss': 67000,
    #     'take_profit': 72000,
    #     'position_size': 0.5,
    #     'reasoning': 'PPO: LONG (0.9), Ensemble: +2.5%, LSTM: bullish, RSI oversold'
    # }
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import pickle
import logging
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Unified trading decision engine

    Models used:
    - PPO Agent (Reinforcement Learning)
    - XGBoost/LightGBM/CatBoost Ensemble
    - LSTM (Trend prediction)
    - Technical Analysis
    """

    def __init__(self, models_dir: str = "/home/user/dosya/backend/models/saved"):
        self.models_dir = Path(models_dir)

        logger.info("🧠 Initializing Decision Engine...")

        # Load models
        self.ppo_model = self._load_ppo()
        self.ensemble_models = self._load_ensemble()
        self.lstm_model = self._load_lstm()

        logger.info("✅ Decision Engine ready!")

    def _load_ppo(self):
        """Load PPO agent"""
        try:
            from stable_baselines3 import PPO

            ppo_path = self.models_dir / "ppo_btcusdt_1d.zip"

            if ppo_path.exists():
                model = PPO.load(str(ppo_path))
                logger.info(f"   ✅ PPO loaded")
                return model
            else:
                logger.warning(f"   ⚠️  PPO not found (train with quick_train_ppo.py)")
                return None

        except Exception as e:
            logger.warning(f"   ⚠️  PPO load error: {e}")
            return None

    def _load_ensemble(self):
        """Load ensemble models"""
        models = {}

        try:
            # XGBoost
            xgb_path = self.models_dir / "xgboost_btcusdt_1d.pkl"
            if xgb_path.exists():
                with open(xgb_path, 'rb') as f:
                    models['xgboost'] = pickle.load(f)
                logger.info(f"   ✅ XGBoost loaded")

            # LightGBM
            lgb_path = self.models_dir / "lightgbm_btcusdt_1d.pkl"
            if lgb_path.exists():
                with open(lgb_path, 'rb') as f:
                    models['lightgbm'] = pickle.load(f)
                logger.info(f"   ✅ LightGBM loaded")

            # CatBoost
            cat_path = self.models_dir / "catboost_btcusdt_1d.pkl"
            if cat_path.exists():
                with open(cat_path, 'rb') as f:
                    models['catboost'] = pickle.load(f)
                logger.info(f"   ✅ CatBoost loaded")

            # Weights
            weights_path = self.models_dir / "ensemble_weights.pkl"
            if weights_path.exists():
                with open(weights_path, 'rb') as f:
                    models['weights'] = pickle.load(f)
                logger.info(f"   ✅ Ensemble weights loaded")

            # Feature names
            features_path = self.models_dir / "feature_names.pkl"
            if features_path.exists():
                with open(features_path, 'rb') as f:
                    models['feature_names'] = pickle.load(f)

        except Exception as e:
            logger.warning(f"   ⚠️  Ensemble load error: {e}")

        if not models:
            logger.warning(f"   ⚠️  No ensemble models found (train with train_ensemble_quick.py)")

        return models if models else None

    def _load_lstm(self):
        """Load LSTM model"""
        try:
            import torch

            lstm_path = self.models_dir / "lstm_btcusdt_1d.pth"

            if lstm_path.exists():
                checkpoint = torch.load(lstm_path, map_location='cpu')
                logger.info(f"   ✅ LSTM loaded")
                return checkpoint
            else:
                logger.warning(f"   ⚠️  LSTM not found (train with train_lstm_quick.py)")
                return None

        except Exception as e:
            logger.warning(f"   ⚠️  LSTM load error: {e}")
            return None

    def _get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Get latest market data with indicators"""
        try:
            # Try to load prepared data
            data_path = Path("/home/user/dosya/backend/data/prepared")
            filename = f"{symbol}_{timeframe}_futures_prepared.parquet"

            df = pd.read_parquet(data_path / filename)

            # Return last 100 candles
            return df.tail(100)

        except Exception as e:
            logger.warning(f"   ⚠️  Data load error: {e}")
            return None

    def _technical_analysis(self, df: pd.DataFrame) -> Dict:
        """Perform technical analysis"""
        latest = df.iloc[-1]

        signals = []

        # RSI
        if 'rsi' in df.columns:
            rsi = latest['rsi']
            if rsi < 30:
                signals.append("RSI oversold (bullish)")
            elif rsi > 70:
                signals.append("RSI overbought (bearish)")

        # MACD
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            if latest['macd'] > latest['macd_signal']:
                signals.append("MACD bullish crossover")
            else:
                signals.append("MACD bearish crossover")

        # EMA
        if 'ema_21' in df.columns and 'ema_50' in df.columns:
            if latest['close'] > latest['ema_21'] > latest['ema_50']:
                signals.append("Price above EMA21/50 (bullish)")
            elif latest['close'] < latest['ema_21'] < latest['ema_50']:
                signals.append("Price below EMA21/50 (bearish)")

        # Bollinger Bands
        if 'bb_position' in df.columns:
            bb_pos = latest['bb_position']
            if bb_pos < 0.2:
                signals.append("Near lower BB (oversold)")
            elif bb_pos > 0.8:
                signals.append("Near upper BB (overbought)")

        return {
            'signals': signals,
            'rsi': latest.get('rsi', None),
            'macd': latest.get('macd', None),
            'close': latest['close']
        }

    def decide(self, symbol: str = 'BTCUSDT', timeframe: str = '1d') -> Dict:
        """
        Make trading decision

        Returns:
            {
                'action': 'LONG' | 'SHORT' | 'WAIT',
                'confidence': 0.0-1.0,
                'entry': float,
                'stop_loss': float,
                'take_profit': float,
                'position_size': 0.0-1.0,
                'reasoning': str,
                'details': {...}
            }
        """
        logger.info(f"🎯 Deciding: {symbol} {timeframe}")

        # Get data
        df = self._get_market_data(symbol, timeframe)

        if df is None or len(df) == 0:
            return self._fallback_decision(symbol)

        # Technical Analysis
        ta = self._technical_analysis(df)

        # Ensemble prediction
        ensemble_pred = None
        if self.ensemble_models and 'feature_names' in self.ensemble_models:
            try:
                features = df.iloc[-1][self.ensemble_models['feature_names']].values.reshape(1, -1)

                weights = self.ensemble_models.get('weights', {})

                pred = 0
                for name, model in self.ensemble_models.items():
                    if name in ['xgboost', 'lightgbm', 'catboost']:
                        pred += model.predict(features)[0] * weights.get(name, 0.33)

                ensemble_pred = pred
                logger.info(f"   Ensemble: {ensemble_pred:+.4f} price change")

            except Exception as e:
                logger.warning(f"   ⚠️  Ensemble prediction error: {e}")

        # PPO prediction
        ppo_action = None
        if self.ppo_model:
            try:
                # TODO: Prepare observation for PPO
                # ppo_action = self.ppo_model.predict(obs)[0]
                pass
            except Exception as e:
                logger.warning(f"   ⚠️  PPO prediction error: {e}")

        # Combine signals
        action = 'WAIT'
        confidence = 0.5

        # Rules-based combination
        bullish_score = 0
        bearish_score = 0

        # Ensemble
        if ensemble_pred:
            if ensemble_pred > 0.01:  # > 1% predicted gain
                bullish_score += 1
            elif ensemble_pred < -0.01:
                bearish_score += 1

        # Technical
        bullish_keywords = ['bullish', 'oversold', 'above']
        bearish_keywords = ['bearish', 'overbought', 'below']

        for signal in ta['signals']:
            if any(kw in signal.lower() for kw in bullish_keywords):
                bullish_score += 0.5
            if any(kw in signal.lower() for kw in bearish_keywords):
                bearish_score += 0.5

        # Decision
        if bullish_score > bearish_score and bullish_score >= 1.5:
            action = 'LONG'
            confidence = min(bullish_score / 3, 0.95)
        elif bearish_score > bullish_score and bearish_score >= 1.5:
            action = 'SHORT'
            confidence = min(bearish_score / 3, 0.95)

        # Price levels
        current_price = ta['close']
        atr = df.iloc[-1].get('atr', current_price * 0.02)  # 2% default

        if action == 'LONG':
            entry = current_price
            stop_loss = entry - (atr * 1.5)
            take_profit = entry + (atr * 3)
        elif action == 'SHORT':
            entry = current_price
            stop_loss = entry + (atr * 1.5)
            take_profit = entry - (atr * 3)
        else:
            entry = current_price
            stop_loss = None
            take_profit = None

        # Position size (based on confidence)
        position_size = confidence * 0.5  # Max 50% of capital

        # Reasoning
        reasoning_parts = []
        if ensemble_pred:
            reasoning_parts.append(f"Ensemble: {ensemble_pred:+.2%}")
        reasoning_parts.extend(ta['signals'][:3])  # Top 3 signals

        reasoning = ", ".join(reasoning_parts) if reasoning_parts else "Insufficient signals"

        return {
            'action': action,
            'confidence': round(confidence, 2),
            'entry': round(entry, 2),
            'stop_loss': round(stop_loss, 2) if stop_loss else None,
            'take_profit': round(take_profit, 2) if take_profit else None,
            'position_size': round(position_size, 2),
            'reasoning': reasoning,
            'details': {
                'bullish_score': bullish_score,
                'bearish_score': bearish_score,
                'ensemble_prediction': ensemble_pred,
                'technical_signals': ta['signals']
            }
        }

    def _fallback_decision(self, symbol: str) -> Dict:
        """Fallback decision when no data/models available"""
        return {
            'action': 'WAIT',
            'confidence': 0.0,
            'entry': 0,
            'stop_loss': None,
            'take_profit': None,
            'position_size': 0.0,
            'reasoning': 'No data or models available',
            'details': {}
        }


# Test
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, default='BTCUSDT')
    parser.add_argument('--timeframe', type=str, default='1d')
    parser.add_argument('--test', action='store_true', help='Run test')
    args = parser.parse_args()

    engine = DecisionEngine()

    decision = engine.decide(symbol=args.symbol, timeframe=args.timeframe)

    print("\n" + "="*60)
    print(f"🎯 DECISION: {args.symbol} {args.timeframe}")
    print("="*60)
    print(f"Action:        {decision['action']}")
    print(f"Confidence:    {decision['confidence'] * 100:.0f}%")
    print(f"Entry:         ${decision['entry']:,.2f}")
    print(f"Stop Loss:     ${decision['stop_loss']:,.2f}" if decision['stop_loss'] else "Stop Loss:     N/A")
    print(f"Take Profit:   ${decision['take_profit']:,.2f}" if decision['take_profit'] else "Take Profit:   N/A")
    print(f"Position Size: {decision['position_size'] * 100:.0f}%")
    print(f"\nReasoning: {decision['reasoning']}")
    print("="*60)
