#!/usr/bin/env python3
"""
Hybrid PPO Training - PPO + Ensemble Integration

Features:
    - Uses pre-trained Ensemble model predictions as features
    - PPO learns optimal entry/exit timing based on Ensemble guidance
    - Combines supervised learning (Ensemble) with RL (PPO)
    - Better risk/reward optimization

Usage:
    # 1. Train Ensemble first
    python -m backend.cli train --symbol BTCUSDT --timeframe 5m --model-type ensemble --market futures

    # 2. Train hybrid PPO
    python -m backend.training.train_ppo_hybrid --symbol BTCUSDT --timeframe 5m --ensemble-model data/models/BTCUSDT_5m_futures_xgb_latest.json
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Tuple, Optional
import gymnasium as gym
from gymnasium import spaces

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import after path is set
try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import BaseCallback
    import xgboost as xgb
except ImportError as e:
    print(f"❌ Error: Missing dependency - {e}")
    print("Install with: pip install stable-baselines3 xgboost")
    sys.exit(1)


class HybridTradingEnvironment(gym.Env):
    """
    Hybrid Trading Environment for Reinforcement Learning

    Uses pre-trained Ensemble model predictions as additional features.
    This gives PPO "expert advice" to make better decisions.

    State Space:
        - Technical indicators (from training data)
        - Ensemble prediction (probability of price up)
        - Ensemble confidence (prediction certainty)
        - Current position
        - Current PnL

    Action Space:
        - 0: Do nothing
        - 1: Open/Close Long
        - 2: Open/Close Short

    Reward:
        - PnL-based with risk penalties
        - Bonus for following high-confidence Ensemble signals
    """

    def __init__(
        self,
        df: pd.DataFrame,
        ensemble_model: xgb.Booster,
        feature_names: list,
        initial_capital: float = 10000.0,
        commission: float = 0.001
    ):
        super().__init__()

        self.df = df.reset_index(drop=True)
        self.ensemble_model = ensemble_model
        self.ensemble_feature_names = feature_names
        self.initial_capital = initial_capital
        self.commission = commission

        # Add Ensemble predictions to dataframe
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

        # Feature columns (including Ensemble predictions) - only numeric columns
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

        # State space: all features + position + equity
        n_features = len(self.feature_cols) + 2
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(n_features,), dtype=np.float32
        )

        # Action space: 0=Hold, 1=Long, 2=Short
        self.action_space = spaces.Discrete(3)

        # Initialize state
        self.reset()

    def _add_ensemble_predictions(self):
        """Add Ensemble model predictions to dataframe"""
        print("   🧠 Generating Ensemble predictions...")

        # Prepare features for Ensemble
        X_values = []
        for fname in self.ensemble_feature_names:
            if fname in self.df.columns:
                X_values.append(self.df[fname].values)
            else:
                # Missing feature - use zeros
                print(f"      ⚠️  Feature not found: {fname}, using 0")
                X_values.append(np.zeros(len(self.df)))

        X = np.array(X_values).T  # (n_samples, n_features)

        # Get Ensemble predictions
        dmatrix = xgb.DMatrix(X, feature_names=self.ensemble_feature_names)
        ensemble_probs = self.ensemble_model.predict(dmatrix)

        # Add to dataframe
        self.df['ensemble_prob'] = ensemble_probs
        self.df['ensemble_confidence'] = np.abs(ensemble_probs - 0.5) * 2  # 0=uncertain, 1=certain
        self.df['ensemble_signal'] = (ensemble_probs > 0.5).astype(int)  # 0=down, 1=up

        print(f"      ✅ Ensemble predictions added")
        print(f"      📊 Avg probability: {ensemble_probs.mean():.3f}")
        print(f"      📊 Avg confidence: {self.df['ensemble_confidence'].mean():.3f}")

    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)

        self.current_step = 0
        self.equity = self.initial_capital
        self.position = 0  # 0=Flat, 1=Long, -1=Short
        self.entry_price = 0
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.max_equity = self.initial_capital
        self.trade_count = 0

        # Ensemble tracking
        self.ensemble_agreement_count = 0  # Times PPO agreed with Ensemble
        self.ensemble_disagreement_count = 0

        return self._get_observation(), {}

    def _get_observation(self):
        """Get current observation (state)"""
        if self.current_step >= len(self.df):
            self.current_step = len(self.df) - 1

        # Market features (including Ensemble predictions)
        features = self.df.iloc[self.current_step][self.feature_cols].values

        # Position and equity
        position_feature = float(self.position)
        equity_feature = (self.equity - self.initial_capital) / self.initial_capital

        # Combine all features
        obs = np.concatenate([features, [position_feature, equity_feature]])

        return obs.astype(np.float32)

    def step(self, action):
        """Execute action and return new state, reward, done, info"""
        current_price = self.df.iloc[self.current_step]['close']
        ensemble_signal = self.df.iloc[self.current_step]['ensemble_signal']
        ensemble_confidence = self.df.iloc[self.current_step]['ensemble_confidence']

        prev_equity = self.equity

        # Track Ensemble agreement
        if action == 1 and ensemble_signal == 1:  # Both bullish
            self.ensemble_agreement_count += 1
        elif action == 2 and ensemble_signal == 0:  # Both bearish
            self.ensemble_agreement_count += 1
        elif action != 0:  # PPO traded against Ensemble
            self.ensemble_disagreement_count += 1

        # Execute action
        reward = 0
        if action == 1:  # Long
            reward = self._execute_long(current_price)
        elif action == 2:  # Short
            reward = self._execute_short(current_price)
        # action == 0: Hold (do nothing)

        # Update equity based on open position
        if self.position != 0:
            unrealized_pnl = self._calculate_unrealized_pnl(current_price)
            self.equity = self.initial_capital + unrealized_pnl

        # Move to next step
        self.current_step += 1
        self.equity_curve.append(self.equity)

        # Update max equity
        if self.equity > self.max_equity:
            self.max_equity = self.equity

        # Check if done
        done = self.current_step >= len(self.df) - 1

        # Calculate final reward (with Ensemble bonus)
        reward = self._calculate_reward(
            prev_equity,
            self.equity,
            action,
            ensemble_signal,
            ensemble_confidence
        )

        # Info
        info = {
            'equity': self.equity,
            'position': self.position,
            'trades': len(self.trades),
            'total_return': (self.equity - self.initial_capital) / self.initial_capital,
            'ensemble_agreement_rate': self.ensemble_agreement_count / max(self.ensemble_agreement_count + self.ensemble_disagreement_count, 1)
        }

        return self._get_observation(), reward, done, False, info

    def _execute_long(self, price):
        """Execute long action"""
        if self.position == 0:
            # Open long
            self.position = 1
            self.entry_price = price
            self.trade_count += 1
            commission = self.equity * self.commission
            self.equity -= commission
            return 0

        elif self.position == -1:
            # Close short, open long
            pnl = (self.entry_price - price) / self.entry_price * self.equity
            commission = abs(pnl) * self.commission
            self.equity += pnl - commission
            self.trades.append({'type': 'short', 'pnl': pnl})

            self.position = 1
            self.entry_price = price
            self.trade_count += 1
            return pnl / self.initial_capital

        else:
            # Already long, hold
            return 0

    def _execute_short(self, price):
        """Execute short action"""
        if self.position == 0:
            # Open short
            self.position = -1
            self.entry_price = price
            self.trade_count += 1
            commission = self.equity * self.commission
            self.equity -= commission
            return 0

        elif self.position == 1:
            # Close long, open short
            pnl = (price - self.entry_price) / self.entry_price * self.equity
            commission = abs(pnl) * self.commission
            self.equity += pnl - commission
            self.trades.append({'type': 'long', 'pnl': pnl})

            self.position = -1
            self.entry_price = price
            self.trade_count += 1
            return pnl / self.initial_capital

        else:
            # Already short, hold
            return 0

    def _calculate_unrealized_pnl(self, current_price):
        """Calculate unrealized PnL for open position"""
        if self.position == 0:
            return 0

        if self.position == 1:
            # Long position
            pnl = (current_price - self.entry_price) / self.entry_price * self.equity
        else:
            # Short position
            pnl = (self.entry_price - current_price) / self.entry_price * self.equity

        return pnl

    def _calculate_reward(
        self,
        prev_equity,
        curr_equity,
        action,
        ensemble_signal,
        ensemble_confidence
    ):
        """
        Calculate reward with Ensemble-aware shaping

        Components:
            1. PnL reward
            2. Risk penalty (drawdown)
            3. Ensemble alignment bonus (reward following high-confidence signals)
            4. Sharpe ratio bonus
        """
        # 1. PnL reward
        pnl = (curr_equity - prev_equity) / self.initial_capital
        pnl_reward = pnl * 100

        # 2. Risk penalty (drawdown)
        drawdown = (self.max_equity - curr_equity) / self.max_equity
        if drawdown > 0.15:
            risk_penalty = -10
        elif drawdown > 0.10:
            risk_penalty = -5
        else:
            risk_penalty = 0

        # 3. Ensemble alignment bonus
        # Reward PPO for following high-confidence Ensemble signals
        ensemble_bonus = 0
        if ensemble_confidence > 0.7:  # High confidence
            if action == 1 and ensemble_signal == 1:  # Both bullish
                ensemble_bonus = 2
            elif action == 2 and ensemble_signal == 0:  # Both bearish
                ensemble_bonus = 2
            elif action != 0:  # Traded against high-confidence signal
                ensemble_bonus = -3  # Penalty

        # 4. Sharpe ratio bonus
        if len(self.equity_curve) > 30:
            returns = np.diff(self.equity_curve[-30:]) / (np.array(self.equity_curve[-31:-1]) + 1e-8)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)
            if sharpe > 2.0:
                sharpe_bonus = 5
            elif sharpe > 1.0:
                sharpe_bonus = 2
            else:
                sharpe_bonus = 0
        else:
            sharpe_bonus = 0

        # Total reward
        total_reward = pnl_reward + risk_penalty + ensemble_bonus + sharpe_bonus

        return total_reward

    def render(self):
        """Render environment (optional)"""
        pass


class HybridTrainingCallback(BaseCallback):
    """Callback for tracking hybrid training progress"""

    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_equities = []
        self.ensemble_agreement_rates = []

    def _on_step(self):
        # Check if episode is done
        if self.locals.get('dones')[0]:
            info = self.locals.get('infos')[0]
            self.episode_rewards.append(info.get('total_return', 0))
            self.episode_equities.append(info.get('equity', 0))
            self.ensemble_agreement_rates.append(info.get('ensemble_agreement_rate', 0))

            if len(self.episode_rewards) % 10 == 0:
                avg_return = np.mean(self.episode_rewards[-10:])
                avg_equity = np.mean(self.episode_equities[-10:])
                avg_agreement = np.mean(self.ensemble_agreement_rates[-10:])
                print(f"Episode {len(self.episode_rewards):4d} | "
                      f"Avg Return: {avg_return:+.2%} | "
                      f"Avg Equity: ${avg_equity:,.0f} | "
                      f"Ensemble Agreement: {avg_agreement:.1%}")

        return True


def load_ensemble_model(model_path: str) -> Tuple[xgb.Booster, list]:
    """Load pre-trained Ensemble (XGBoost) model"""
    print(f"📥 Loading Ensemble model: {model_path}")

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Ensemble model not found: {model_path}")

    model = xgb.Booster()
    model.load_model(model_path)

    feature_names = model.feature_names

    print(f"   ✅ Ensemble model loaded")
    print(f"   📊 Features: {len(feature_names)}")

    return model, feature_names


def load_data(symbol, timeframe, market='futures', data_dir='data/advanced'):
    """Load advanced historical data from Parquet"""

    filename = f"{symbol}_{timeframe}_{market}_binance.parquet"
    filepath = Path(data_dir) / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    print(f"📂 Loading data from {filepath}")
    df = pd.read_parquet(filepath)

    print(f"✅ Loaded {len(df)} candles with {len(df.columns)} features")
    return df


def main():
    parser = argparse.ArgumentParser(description='Train Hybrid PPO (PPO + Ensemble)')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='5m', help='Timeframe')
    parser.add_argument('--market', type=str, default='futures', choices=['spot', 'futures'])
    parser.add_argument('--ensemble-model', type=str, required=True, help='Path to trained Ensemble model (.json)')
    parser.add_argument('--total-timesteps', type=int, default=100000, help='Total training timesteps')
    parser.add_argument('--learning-rate', type=float, default=0.0003, help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
    parser.add_argument('--n-steps', type=int, default=2048, help='Steps per update')
    parser.add_argument('--initial-capital', type=float, default=10000, help='Initial capital')
    parser.add_argument('--commission', type=float, default=0.001, help='Commission rate')
    parser.add_argument('--data-dir', type=str, default='data/advanced', help='Data directory')
    parser.add_argument('--output-dir', type=str, default='data/models', help='Output directory')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("🤖 HYBRID PPO TRAINING - PPO + Ensemble Integration")
    print("=" * 80)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Market: {args.market}")
    print(f"Ensemble model: {args.ensemble_model}")
    print(f"Total timesteps: {args.total_timesteps:,}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Initial capital: ${args.initial_capital:,.0f}")
    print("=" * 80)
    print()

    # 1. Load Ensemble model
    ensemble_model, feature_names = load_ensemble_model(args.ensemble_model)

    # 2. Load data
    df = load_data(args.symbol, args.timeframe, args.market, args.data_dir)

    # 3. Split data
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()

    print(f"\n📊 Data split:")
    print(f"   Train: {len(train_df)} candles")
    print(f"   Val: {len(val_df)} candles")

    # 4. Create hybrid environment
    print("\n🏗️  Creating hybrid trading environment...")
    env = HybridTradingEnvironment(
        df=train_df,
        ensemble_model=ensemble_model,
        feature_names=feature_names,
        initial_capital=args.initial_capital,
        commission=args.commission
    )
    env = DummyVecEnv([lambda: env])

    print(f"✅ Hybrid environment created")
    print(f"   Observation space: {env.observation_space.shape}")
    print(f"   Action space: {env.action_space}")

    # 5. Create PPO agent
    print("\n🤖 Creating PPO agent...")
    model = PPO(
        'MlpPolicy',
        env,
        learning_rate=args.learning_rate,
        n_steps=args.n_steps,
        batch_size=args.batch_size,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        verbose=0
    )

    print(f"✅ PPO agent created")

    # 6. Train agent
    print("\n🚀 Starting hybrid training...")
    print("-" * 80)

    callback = HybridTrainingCallback()
    model.learn(total_timesteps=args.total_timesteps, callback=callback)

    print("-" * 80)
    print("✅ Training complete!")

    # 7. Evaluate on validation set
    print("\n📊 Evaluating on validation data...")
    val_env = HybridTradingEnvironment(
        df=val_df,
        ensemble_model=ensemble_model,
        feature_names=feature_names,
        initial_capital=args.initial_capital,
        commission=args.commission
    )

    obs, _ = val_env.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _, info = val_env.step(action)

    final_equity = info['equity']
    total_return = info['total_return']
    num_trades = info['trades']
    agreement_rate = info['ensemble_agreement_rate']

    print(f"\n📈 Validation Results:")
    print(f"   Initial capital: ${args.initial_capital:,.0f}")
    print(f"   Final equity: ${final_equity:,.0f}")
    print(f"   Total return: {total_return:+.2%}")
    print(f"   Number of trades: {num_trades}")
    print(f"   Ensemble agreement rate: {agreement_rate:.1%}")

    # Calculate metrics
    returns = np.diff(val_env.equity_curve) / (np.array(val_env.equity_curve[:-1]) + 1e-8)
    sharpe = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)
    max_dd = (val_env.max_equity - np.min(val_env.equity_curve)) / val_env.max_equity

    print(f"   Sharpe ratio: {sharpe:.2f}")
    print(f"   Max drawdown: {max_dd:.2%}")

    # 8. Save model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = f"{args.symbol}_{args.timeframe}_{args.market}_ppo_hybrid_{timestamp}"

    model_path = output_dir / f"{model_name}.zip"
    metadata_path = output_dir / f"{model_name}_metadata.json"

    model.save(str(model_path))

    metadata = {
        'model_name': model_name,
        'model_type': 'ppo_hybrid',
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'market': args.market,
        'ensemble_model': args.ensemble_model,
        'trained_at': timestamp,
        'total_timesteps': args.total_timesteps,
        'val_final_equity': float(final_equity),
        'val_total_return': float(total_return),
        'val_sharpe_ratio': float(sharpe),
        'val_max_drawdown': float(max_dd),
        'val_num_trades': int(num_trades),
        'val_ensemble_agreement_rate': float(agreement_rate)
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Model saved:")
    print(f"   Model: {model_path}")
    print(f"   Metadata: {metadata_path}")
    print()
    print("=" * 80)
    print("✅ HYBRID TRAINING COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
