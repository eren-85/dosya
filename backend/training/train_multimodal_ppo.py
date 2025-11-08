"""
Multi-Modal PPO Training - Visual + Numerical Features

Combines:
1. Numerical features (62 technical indicators)
2. Ensemble predictions
3. Visual features from VLM (chart understanding)
4. Pattern detection from YOLO

This creates the most powerful trading agent:
- Sees charts like humans do
- Uses numerical precision
- Learns optimal timing with RL

RTX 4060 optimized
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
import torch
from typing import Dict, Tuple, Optional
from datetime import datetime
import argparse
import json
import logging

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback

from backend.vision import ChartVLM, ChartPatternDetector, ChartImageGenerator
import xgboost as xgb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiModalTradingEnvironment(gym.Env):
    """
    Multi-modal trading environment combining:
    - Numerical features (OHLCV + indicators)
    - Ensemble predictions
    - VLM visual analysis
    - YOLO pattern detection

    State Space (79 features):
        - 62: Technical indicators
        - 3: Ensemble features (prob, confidence, signal)
        - 5: VLM features (bullish_score, bearish_score, pattern_count, avg_confidence, trend_score)
        - 5: YOLO features (pattern_detected, pattern_confidence, pattern_type_encoded, bbox_size, position)
        - 2: Position & equity
        - 2: Visual embedding (compressed from VLM)

    Action Space:
        - 0: Hold
        - 1: Long
        - 2: Short
    """

    def __init__(
        self,
        df: pd.DataFrame,
        ensemble_model: xgb.Booster,
        ensemble_feature_names: list,
        vlm: Optional[ChartVLM] = None,
        yolo: Optional[ChartPatternDetector] = None,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        use_visual_features: bool = True,
        visual_update_frequency: int = 20  # Update visual features every N steps (for speed)
    ):
        super().__init__()

        self.df = df.reset_index(drop=True)
        self.ensemble_model = ensemble_model
        self.ensemble_feature_names = ensemble_feature_names
        self.vlm = vlm
        self.yolo = yolo
        self.initial_capital = initial_capital
        self.commission = commission
        self.use_visual_features = use_visual_features
        self.visual_update_frequency = visual_update_frequency

        # Chart image generator
        self.chart_generator = ChartImageGenerator()

        # Add Ensemble predictions
        self._add_ensemble_predictions()

        # Clean data BEFORE feature selection
        # 1. Drop object columns explicitly
        object_cols = self.df.select_dtypes(include=['object']).columns.tolist()
        if object_cols:
            self.df = self.df.drop(columns=object_cols)

        # 2. Drop columns that are 100% NaN
        self.df = self.df.dropna(axis=1, how='all')

        # 3. Fill remaining NaN with forward/backward fill
        self.df = self.df.ffill().bfill().fillna(0)

        # Feature columns - only numeric columns
        excluded_cols = ['open', 'high', 'low', 'close', 'volume', 'open_time', 'close_time', 'timestamp', 'target']
        self.feature_cols = [
            col for col in self.df.columns
            if col not in excluded_cols
            and pd.api.types.is_numeric_dtype(self.df[col])
        ]

        if not self.feature_cols:
            raise ValueError("No numeric features found after cleaning! Check your data.")

        # Normalize features
        self.feature_means = self.df[self.feature_cols].mean()
        self.feature_stds = self.df[self.feature_cols].std()
        self.df[self.feature_cols] = (self.df[self.feature_cols] - self.feature_means) / (self.feature_stds + 1e-8)

        # State space: numerical + visual + position + equity
        base_features = len(self.feature_cols)  # ~65 (62 + 3 ensemble)
        visual_features = 12 if use_visual_features else 0  # VLM (5) + YOLO (5) + embedding (2)
        state_size = base_features + visual_features + 2  # +2 for position & equity

        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(state_size,), dtype=np.float32
        )

        # Action space
        self.action_space = spaces.Discrete(3)

        # Visual feature cache
        self.visual_features_cache = {}
        self.last_visual_update = 0

        # Initialize state
        self.reset()

        logger.info(f"🎯 MultiModalTradingEnvironment initialized")
        logger.info(f"   Observation space: {self.observation_space.shape}")
        logger.info(f"   Numerical features: {base_features}")
        logger.info(f"   Visual features: {visual_features}")
        logger.info(f"   Use visual: {use_visual_features}")

    def _add_ensemble_predictions(self):
        """Add Ensemble predictions to dataframe"""
        logger.info("   🧠 Generating Ensemble predictions...")

        X_values = []
        for fname in self.ensemble_feature_names:
            if fname in self.df.columns:
                X_values.append(self.df[fname].values)
            else:
                X_values.append(np.zeros(len(self.df)))

        X = np.array(X_values).T
        dmatrix = xgb.DMatrix(X, feature_names=self.ensemble_feature_names)
        ensemble_probs = self.ensemble_model.predict(dmatrix)

        self.df['ensemble_prob'] = ensemble_probs
        self.df['ensemble_confidence'] = np.abs(ensemble_probs - 0.5) * 2
        self.df['ensemble_signal'] = (ensemble_probs > 0.5).astype(int)

        logger.info(f"      ✅ Ensemble predictions added")

    def reset(self, seed=None, options=None):
        """Reset environment"""
        super().reset(seed=seed)

        self.current_step = 0
        self.equity = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.max_equity = self.initial_capital

        # Visual tracking
        self.visual_features_cache = {}
        self.last_visual_update = 0

        return self._get_observation(), {}

    def _get_observation(self):
        """Get current observation (multi-modal)"""
        if self.current_step >= len(self.df):
            self.current_step = len(self.df) - 1

        # 1. Numerical features
        numerical_features = self.df.iloc[self.current_step][self.feature_cols].values

        # 2. Position & equity
        position_feature = float(self.position)
        equity_feature = (self.equity - self.initial_capital) / self.initial_capital

        # Combine
        obs = np.concatenate([
            numerical_features,
            [position_feature, equity_feature]
        ])

        # 3. Visual features (optional, updated less frequently for speed)
        if self.use_visual_features:
            # Update visual features periodically
            if (self.current_step - self.last_visual_update) >= self.visual_update_frequency:
                visual_feats = self._get_visual_features()
                self.visual_features_cache[self.current_step] = visual_feats
                self.last_visual_update = self.current_step
            else:
                # Use cached or nearest cached visual features
                nearest_key = max([k for k in self.visual_features_cache.keys() if k <= self.current_step], default=0)
                visual_feats = self.visual_features_cache.get(nearest_key, np.zeros(12))

            obs = np.concatenate([obs, visual_feats])

        return obs.astype(np.float32)

    def _get_visual_features(self) -> np.ndarray:
        """
        Extract visual features from chart

        Returns:
            [12 features]:
            - VLM: bullish_score, bearish_score, pattern_count, avg_confidence, trend_score
            - YOLO: pattern_detected, pattern_confidence, pattern_type, bbox_size, position_x
            - Embedding: visual_emb_1, visual_emb_2 (compressed)
        """
        # Get recent window for chart
        window_start = max(0, self.current_step - 100)
        window_df = self.df.iloc[window_start:self.current_step + 1]

        if len(window_df) < 10:
            return np.zeros(12)

        try:
            # Generate chart image
            chart_img = self.chart_generator.generate_candlestick_chart(
                window_df,
                indicators=['sma_20', 'sma_50']
            )

            # VLM analysis (if available)
            vlm_features = np.zeros(5)
            if self.vlm is not None:
                vlm_result = self.vlm.analyze_chart(
                    chart_img,
                    question="Analyze trend and patterns briefly.",
                    max_tokens=128
                )

                # Parse VLM result
                analysis = vlm_result['analysis'].lower()

                bullish_score = 1.0 if 'bullish' in analysis or 'up' in analysis else 0.0
                bearish_score = 1.0 if 'bearish' in analysis or 'down' in analysis else 0.0
                pattern_count = len(vlm_result.get('patterns_detected', []))
                avg_confidence = vlm_result.get('confidence', 0.5)
                trend_score = 1.0 if 'strong' in analysis else 0.5

                vlm_features = np.array([
                    bullish_score,
                    bearish_score,
                    pattern_count / 5.0,  # Normalize
                    avg_confidence,
                    trend_score
                ])

            # YOLO pattern detection (if available)
            yolo_features = np.zeros(5)
            if self.yolo is not None:
                detections = self.yolo.detect_patterns(chart_img)

                if detections:
                    # Use strongest detection
                    strongest = max(detections, key=lambda d: d['confidence'])

                    pattern_detected = 1.0
                    pattern_confidence = strongest['confidence']
                    pattern_type = hash(strongest['pattern']) % 100 / 100.0  # Encode pattern type
                    bbox_size = strongest['area'] / (chart_img.width * chart_img.height)
                    position_x = strongest['center'][0] / chart_img.width

                    yolo_features = np.array([
                        pattern_detected,
                        pattern_confidence,
                        pattern_type,
                        bbox_size,
                        position_x
                    ])

            # Visual embedding (simplified - can use actual image embeddings)
            visual_emb = np.array([
                np.mean(vlm_features),
                np.mean(yolo_features)
            ])

            # Combine all visual features
            return np.concatenate([vlm_features, yolo_features, visual_emb])

        except Exception as e:
            logger.warning(f"Error extracting visual features: {e}")
            return np.zeros(12)

    def step(self, action):
        """Execute action"""
        current_price = self.df.iloc[self.current_step]['close']
        prev_equity = self.equity

        # Execute action (same as hybrid PPO)
        reward = 0
        if action == 1:  # Long
            reward = self._execute_long(current_price)
        elif action == 2:  # Short
            reward = self._execute_short(current_price)

        # Update equity
        if self.position != 0:
            unrealized_pnl = self._calculate_unrealized_pnl(current_price)
            self.equity = self.initial_capital + unrealized_pnl

        # Move to next step
        self.current_step += 1
        self.equity_curve.append(self.equity)

        if self.equity > self.max_equity:
            self.max_equity = self.equity

        # Done?
        done = self.current_step >= len(self.df) - 1

        # Calculate reward
        reward = self._calculate_reward(prev_equity, self.equity)

        # Info
        info = {
            'equity': self.equity,
            'position': self.position,
            'trades': len(self.trades),
            'total_return': (self.equity - self.initial_capital) / self.initial_capital
        }

        return self._get_observation(), reward, done, False, info

    def _execute_long(self, price):
        """Execute long (same as hybrid PPO)"""
        if self.position == 0:
            self.position = 1
            self.entry_price = price
            commission = self.equity * self.commission
            self.equity -= commission
            return 0
        elif self.position == -1:
            pnl = (self.entry_price - price) / self.entry_price * self.equity
            commission = abs(pnl) * self.commission
            self.equity += pnl - commission
            self.trades.append({'type': 'short', 'pnl': pnl})
            self.position = 1
            self.entry_price = price
            return pnl / self.initial_capital
        else:
            return 0

    def _execute_short(self, price):
        """Execute short"""
        if self.position == 0:
            self.position = -1
            self.entry_price = price
            commission = self.equity * self.commission
            self.equity -= commission
            return 0
        elif self.position == 1:
            pnl = (price - self.entry_price) / self.entry_price * self.equity
            commission = abs(pnl) * self.commission
            self.equity += pnl - commission
            self.trades.append({'type': 'long', 'pnl': pnl})
            self.position = -1
            self.entry_price = price
            return pnl / self.initial_capital
        else:
            return 0

    def _calculate_unrealized_pnl(self, current_price):
        """Calculate unrealized PnL"""
        if self.position == 0:
            return 0
        if self.position == 1:
            return (current_price - self.entry_price) / self.entry_price * self.equity
        else:
            return (self.entry_price - current_price) / self.entry_price * self.equity

    def _calculate_reward(self, prev_equity, curr_equity):
        """Calculate reward (same as hybrid PPO)"""
        pnl = (curr_equity - prev_equity) / self.initial_capital
        pnl_reward = pnl * 100

        # Risk penalty
        drawdown = (self.max_equity - curr_equity) / self.max_equity
        risk_penalty = -10 if drawdown > 0.15 else (-5 if drawdown > 0.10 else 0)

        # Sharpe bonus
        sharpe_bonus = 0
        if len(self.equity_curve) > 30:
            returns = np.diff(self.equity_curve[-30:]) / (np.array(self.equity_curve[-31:-1]) + 1e-8)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)
            sharpe_bonus = 5 if sharpe > 2.0 else (2 if sharpe > 1.0 else 0)

        return pnl_reward + risk_penalty + sharpe_bonus

    def render(self):
        pass


def load_models(symbol, timeframe, market, data_dir):
    """Load Ensemble, VLM, YOLO models"""
    logger.info("📥 Loading models...")

    # 1. Ensemble
    ensemble_pattern = f"{symbol}_{timeframe}_{market}_xgb*.json"
    ensemble_files = list(Path("data/models").glob(ensemble_pattern))

    if not ensemble_files:
        raise FileNotFoundError(f"No Ensemble model found: {ensemble_pattern}")

    ensemble_path = sorted(ensemble_files, key=lambda p: p.stat().st_mtime)[-1]
    ensemble_model = xgb.Booster()
    ensemble_model.load_model(str(ensemble_path))
    feature_names = ensemble_model.feature_names

    logger.info(f"   ✅ Ensemble: {ensemble_path.name}")

    # 2. VLM (optional)
    vlm = None
    try:
        vlm = ChartVLM(device="cuda")
        vlm.load_model()
        logger.info(f"   ✅ VLM: Qwen2.5-VL-7B loaded")
    except Exception as e:
        logger.warning(f"   ⚠️  VLM not available: {e}")

    # 3. YOLO (optional)
    yolo = None
    try:
        yolo = ChartPatternDetector(device="cuda")
        yolo.load_model()
        logger.info(f"   ✅ YOLO: Pattern detector loaded")
    except Exception as e:
        logger.warning(f"   ⚠️  YOLO not available: {e}")

    return ensemble_model, feature_names, vlm, yolo


def main():
    parser = argparse.ArgumentParser(description='Train Multi-Modal PPO')
    parser.add_argument('--symbol', type=str, default='BTCUSDT')
    parser.add_argument('--timeframe', type=str, default='5m')
    parser.add_argument('--market', type=str, default='futures')
    parser.add_argument('--data-dir', type=str, default='data/advanced')
    parser.add_argument('--total-timesteps', type=int, default=100000)
    parser.add_argument('--use-visual', action='store_true', help='Use visual features (slower)')
    parser.add_argument('--output-dir', type=str, default='data/models')

    args = parser.parse_args()

    print("="*80)
    print("🤖 MULTI-MODAL PPO TRAINING")
    print("="*80)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Market: {args.market}")
    print(f"Use visual features: {args.use_visual}")
    print("="*80)

    # Load models
    ensemble_model, feature_names, vlm, yolo = load_models(
        args.symbol, args.timeframe, args.market, args.data_dir
    )

    # Load data
    data_file = Path(args.data_dir) / f"{args.symbol}_{args.timeframe}_{args.market}_binance.parquet"
    df = pd.read_parquet(data_file)

    logger.info(f"✅ Loaded {len(df)} candles")

    # Split
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()

    # Create environment
    env = MultiModalTradingEnvironment(
        df=train_df,
        ensemble_model=ensemble_model,
        ensemble_feature_names=feature_names,
        vlm=vlm if args.use_visual else None,
        yolo=yolo if args.use_visual else None,
        use_visual_features=args.use_visual
    )
    env = DummyVecEnv([lambda: env])

    # Create PPO
    model = PPO(
        'MlpPolicy',
        env,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=1
    )

    # Train
    logger.info("🚀 Starting training...")
    model.learn(total_timesteps=args.total_timesteps)

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = f"{args.symbol}_{args.timeframe}_{args.market}_ppo_multimodal_{timestamp}"
    model_path = Path(args.output_dir) / f"{model_name}.zip"

    model.save(str(model_path))
    logger.info(f"💾 Model saved: {model_path}")


if __name__ == '__main__':
    main()
