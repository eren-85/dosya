#!/usr/bin/env python3
"""
PPO (Reinforcement Learning) Training Script

Usage:
    python -m backend.training.train_ppo --symbol BTCUSDT --timeframe 1h --total-timesteps 100000

Features:
    - Custom trading environment (Gym-compatible)
    - Reward shaping (PnL, risk, Sharpe ratio)
    - PPO agent from stable-baselines3
    - Episode tracking and visualization
    - Model checkpointing
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Tuple
import gymnasium as gym
from gymnasium import spaces

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import after path is set
try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import BaseCallback
except ImportError:
    print("❌ Error: stable-baselines3 not installed")
    print("Install with: pip install stable-baselines3")
    sys.exit(1)


class TradingEnvironment(gym.Env):
    """
    Custom Trading Environment for Reinforcement Learning

    State Space:
        - Technical indicators (45+ features)
        - Current position (long/short/flat)
        - Current PnL
        - Current equity

    Action Space:
        - 0: Do nothing
        - 1: Open/Close Long
        - 2: Open/Close Short

    Reward:
        - PnL-based with risk penalties
    """

    def __init__(self, df: pd.DataFrame, initial_capital: float = 10000.0, commission: float = 0.001):
        super().__init__()

        self.df = df.reset_index(drop=True)
        self.initial_capital = initial_capital
        self.commission = commission

        # Calculate indicators
        self._calculate_indicators()

        # Feature columns
        self.feature_cols = [col for col in self.df.columns if col not in [
            'open', 'high', 'low', 'close', 'volume',
            'open_time', 'close_time', 'timestamp'
        ]]

        # Normalize features
        self.feature_means = self.df[self.feature_cols].mean()
        self.feature_stds = self.df[self.feature_cols].std()
        self.df[self.feature_cols] = (self.df[self.feature_cols] - self.feature_means) / self.feature_stds

        # State space: features + position + equity
        n_features = len(self.feature_cols) + 2
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(n_features,), dtype=np.float32
        )

        # Action space: 0=Hold, 1=Long, 2=Short
        self.action_space = spaces.Discrete(3)

        # Initialize state
        self.reset()

    def _calculate_indicators(self):
        """Calculate technical indicators"""
        df = self.df

        # Price-based
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Moving averages
        for period in [7, 14, 21, 50]:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(14).mean()

        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Momentum
        df['momentum'] = df['close'] - df['close'].shift(10)

        # Drop NaN
        df.dropna(inplace=True)

        self.df = df

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

        return self._get_observation(), {}

    def _get_observation(self):
        """Get current observation (state)"""
        if self.current_step >= len(self.df):
            self.current_step = len(self.df) - 1

        # Market features
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
        prev_equity = self.equity

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

        # Calculate final reward
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

    def _calculate_reward(self, prev_equity, curr_equity):
        """
        Calculate reward with custom shaping

        Components:
            1. PnL reward
            2. Risk penalty (drawdown)
            3. Trade frequency penalty (avoid overtrading)
            4. Sharpe ratio bonus
        """
        # 1. PnL reward
        pnl = (curr_equity - prev_equity) / self.initial_capital
        pnl_reward = pnl * 100

        # 2. Risk penalty (drawdown)
        drawdown = (self.max_equity - curr_equity) / self.max_equity
        if drawdown > 0.15:  # 15% DD threshold
            risk_penalty = -10
        elif drawdown > 0.10:
            risk_penalty = -5
        else:
            risk_penalty = 0

        # 3. Trade frequency penalty (avoid overtrading)
        trades_per_100_steps = (self.trade_count / max(self.current_step, 1)) * 100
        if trades_per_100_steps > 10:  # More than 10% of steps
            freq_penalty = -5
        else:
            freq_penalty = 0

        # 4. Sharpe ratio bonus
        if len(self.equity_curve) > 30:
            returns = np.diff(self.equity_curve[-30:]) / self.equity_curve[-31:-1]
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
        total_reward = pnl_reward + risk_penalty + freq_penalty + sharpe_bonus

        return total_reward

    def render(self):
        """Render environment (optional)"""
        pass


class TrainingCallback(BaseCallback):
    """Callback for tracking training progress"""

    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_equities = []

    def _on_step(self):
        # Check if episode is done
        if self.locals.get('dones')[0]:
            info = self.locals.get('infos')[0]
            self.episode_rewards.append(info.get('total_return', 0))
            self.episode_equities.append(info.get('equity', 0))

            if len(self.episode_rewards) % 10 == 0:
                avg_return = np.mean(self.episode_rewards[-10:])
                avg_equity = np.mean(self.episode_equities[-10:])
                print(f"Episode {len(self.episode_rewards):4d} | "
                      f"Avg Return: {avg_return:+.2%} | "
                      f"Avg Equity: ${avg_equity:,.0f}")

        return True


def load_data(symbol, timeframe, data_dir='data/historical'):
    """Load historical data from Parquet"""

    filename = f"{symbol}_{timeframe}_futures.parquet"
    filepath = Path(data_dir) / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    print(f"📂 Loading data from {filepath}")
    df = pd.read_parquet(filepath)

    # Ensure required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data must have columns: {required_cols}")

    print(f"✅ Loaded {len(df)} candles")
    return df


def main():
    parser = argparse.ArgumentParser(description='Train PPO reinforcement learning agent')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe (e.g., 1h, 4h)')
    parser.add_argument('--total-timesteps', type=int, default=100000, help='Total training timesteps')
    parser.add_argument('--learning-rate', type=float, default=0.0003, help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
    parser.add_argument('--n-steps', type=int, default=2048, help='Steps per update')
    parser.add_argument('--initial-capital', type=float, default=10000, help='Initial capital')
    parser.add_argument('--commission', type=float, default=0.001, help='Commission rate')
    parser.add_argument('--data-dir', type=str, default='data/historical', help='Data directory')
    parser.add_argument('--output-dir', type=str, default='models/trained', help='Output directory')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🤖 PPO REINFORCEMENT LEARNING - TRAINING SCRIPT")
    print("=" * 60)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Total timesteps: {args.total_timesteps:,}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Batch size: {args.batch_size}")
    print(f"Initial capital: ${args.initial_capital:,.0f}")
    print(f"Commission: {args.commission:.2%}")
    print("=" * 60)
    print()

    # 1. Load data
    df = load_data(args.symbol, args.timeframe, args.data_dir)

    # 2. Split data (train on first 80%, validate on last 20%)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()

    print(f"\n📊 Data split:")
    print(f"   Train: {len(train_df)} candles")
    print(f"   Val: {len(val_df)} candles")

    # 3. Create environment
    print("\n🏗️  Creating trading environment...")
    env = TradingEnvironment(
        df=train_df,
        initial_capital=args.initial_capital,
        commission=args.commission
    )
    env = DummyVecEnv([lambda: env])

    print(f"✅ Environment created")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")

    # 4. Create PPO agent
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
    print(f"   Policy: MlpPolicy")
    print(f"   Learning rate: {args.learning_rate}")
    print(f"   N steps: {args.n_steps}")

    # 5. Train agent
    print("\n🚀 Starting training...")
    print("-" * 60)

    callback = TrainingCallback()
    model.learn(total_timesteps=args.total_timesteps, callback=callback)

    print("-" * 60)
    print("✅ Training complete!")

    # 6. Evaluate on validation set
    print("\n📊 Evaluating on validation data...")
    val_env = TradingEnvironment(
        df=val_df,
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

    print(f"\n📈 Validation Results:")
    print(f"   Initial capital: ${args.initial_capital:,.0f}")
    print(f"   Final equity: ${final_equity:,.0f}")
    print(f"   Total return: {total_return:+.2%}")
    print(f"   Number of trades: {num_trades}")

    # Calculate Sharpe ratio
    returns = np.diff(val_env.equity_curve) / val_env.equity_curve[:-1]
    sharpe = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)
    max_dd = (val_env.max_equity - np.min(val_env.equity_curve)) / val_env.max_equity

    print(f"   Sharpe ratio: {sharpe:.2f}")
    print(f"   Max drawdown: {max_dd:.2%}")

    # 7. Save model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = f"ppo_{args.symbol}_{args.timeframe}_{timestamp}"

    model_path = output_dir / f"{model_name}.zip"
    metadata_path = output_dir / f"{model_name}_metadata.json"

    # Save model (stable-baselines3 format)
    model.save(str(model_path))

    # Save metadata
    metadata = {
        'model_name': model_name,
        'model_type': 'ppo',
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'trained_at': timestamp,
        'total_timesteps': args.total_timesteps,
        'learning_rate': args.learning_rate,
        'batch_size': args.batch_size,
        'initial_capital': args.initial_capital,
        'commission': args.commission,
        'val_final_equity': float(final_equity),
        'val_total_return': float(total_return),
        'val_sharpe_ratio': float(sharpe),
        'val_max_drawdown': float(max_dd),
        'val_num_trades': int(num_trades)
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Model saved:")
    print(f"   Model: {model_path}")
    print(f"   Metadata: {metadata_path}")
    print()
    print("=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print()
    print("🎯 Next steps:")
    print("   1. Test the agent on live data")
    print("   2. Fine-tune hyperparameters")
    print("   3. Deploy to production")
    print()


if __name__ == '__main__':
    main()
