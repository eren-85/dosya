"""
Quick PPO Training with Prepared Data
Uses pre-calculated indicators from prepare_rl_data.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTradingEnv(gym.Env):
    """Simple trading environment with prepared data"""

    def __init__(self, df: pd.DataFrame, initial_capital: float = 10000.0):
        super().__init__()

        self.df = df.reset_index(drop=True)
        self.initial_capital = initial_capital

        # Features (exclude OHLCV and metadata)
        self.feature_cols = [col for col in df.columns if col not in [
            'open', 'high', 'low', 'close', 'volume',
            'open_time', 'close_time', 'quote_asset_volume',
            'trades', 'taker_base', 'taker_quote', 'ignore'
        ]]

        logger.info(f"Using {len(self.feature_cols)} features: {self.feature_cols[:10]}...")

        # Observation: features + position + equity
        n_obs = len(self.feature_cols) + 2
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(n_obs,), dtype=np.float32)

        # Actions: 0=Hold, 1=Long, 2=Short
        self.action_space = spaces.Discrete(3)

        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.current_step = 0
        self.position = 0  # 0=flat, 1=long, -1=short
        self.entry_price = 0
        self.capital = self.initial_capital
        self.equity = self.initial_capital
        self.trades = 0
        self.wins = 0

        return self._get_observation(), {}

    def _get_observation(self):
        """Get current state"""
        features = self.df.iloc[self.current_step][self.feature_cols].values

        # Add position and equity ratio
        position_feature = float(self.position)
        equity_ratio = self.equity / self.initial_capital

        obs = np.concatenate([features, [position_feature, equity_ratio]])
        return obs.astype(np.float32)

    def step(self, action):
        current_price = self.df.iloc[self.current_step]['close']

        # Execute action
        reward = 0

        if action == 1:  # Long
            if self.position == 0:
                self.position = 1
                self.entry_price = current_price
            elif self.position == -1:  # Close short, open long
                pnl = (self.entry_price - current_price) / self.entry_price
                self.capital *= (1 + pnl)
                reward = pnl * 100
                if pnl > 0:
                    self.wins += 1
                self.trades += 1

                self.position = 1
                self.entry_price = current_price

        elif action == 2:  # Short
            if self.position == 0:
                self.position = -1
                self.entry_price = current_price
            elif self.position == 1:  # Close long, open short
                pnl = (current_price - self.entry_price) / self.entry_price
                self.capital *= (1 + pnl)
                reward = pnl * 100
                if pnl > 0:
                    self.wins += 1
                self.trades += 1

                self.position = -1
                self.entry_price = current_price

        # Calculate equity
        if self.position == 1:
            unrealized_pnl = (current_price - self.entry_price) / self.entry_price
            self.equity = self.capital * (1 + unrealized_pnl)
        elif self.position == -1:
            unrealized_pnl = (self.entry_price - current_price) / self.entry_price
            self.equity = self.capital * (1 + unrealized_pnl)
        else:
            self.equity = self.capital

        # Reward shaping
        if self.equity > self.capital:
            reward += (self.equity - self.capital) / self.capital * 10

        # Move to next step
        self.current_step += 1

        # Check if done
        done = self.current_step >= len(self.df) - 1

        # Truncated (for Gym API)
        truncated = False

        return self._get_observation(), reward, done, truncated, {}


class TrainingCallback(BaseCallback):
    """Log training progress"""

    def __init__(self, verbose=1):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []

    def _on_step(self) -> bool:
        return True

    def _on_rollout_end(self) -> None:
        if len(self.model.ep_info_buffer) > 0:
            logger.info(f"Episode {self.num_timesteps}: Mean reward = {np.mean([ep['r'] for ep in self.model.ep_info_buffer]):.2f}")


def train_ppo(
    symbol: str = "BTCUSDT",
    timeframe: str = "1d",
    market_type: str = "futures",
    total_timesteps: int = 50000,
    save_dir: str = "/home/user/dosya/backend/models/saved",
    use_advanced: bool = True
):
    """
    Train PPO agent

    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        market_type: 'spot' or 'futures'
        total_timesteps: Number of training timesteps
        save_dir: Directory to save model
        use_advanced: Use advanced multi-exchange features if available
    """

    logger.info(f"🤖 Starting PPO Training")
    logger.info(f"   Symbol: {symbol} {timeframe} {market_type}")
    logger.info(f"   Timesteps: {total_timesteps}")
    logger.info(f"   Advanced mode: {use_advanced}")

    # Load and prepare data (will auto-detect advanced data)
    from backend.training.prepare_rl_data import prepare_training_data

    df = prepare_training_data(
        symbol=symbol,
        timeframe=timeframe,
        market_type=market_type,
        use_advanced=use_advanced
    )
    logger.info(f"   Loaded {len(df)} candles with {len(df.columns)} features")

    # Create environment
    env = DummyVecEnv([lambda: SimpleTradingEnv(df)])

    # Create PPO agent
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01
    )

    # Train
    logger.info(f"\n🚀 Training started...")
    callback = TrainingCallback()

    model.learn(total_timesteps=total_timesteps, callback=callback)

    # Save model
    save_path = Path(save_dir) / f"ppo_{symbol.lower()}_{timeframe}.zip"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(save_path))

    logger.info(f"\n✅ Training complete!")
    logger.info(f"   Model saved: {save_path}")

    return model


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Train PPO Agent (Batch Mode)')

    # Batch training parameters
    parser.add_argument('--data-files', type=str, required=True, help='Comma-separated parquet file paths')
    parser.add_argument('--epochs', type=int, default=10, help='Number of PPO epochs (n_epochs parameter)')
    parser.add_argument('--device', type=str, default='cpu', choices=['cpu', 'cuda'], help='Training device')
    parser.add_argument('--output-name', type=str, required=True, help='Output model name (e.g., spot_1h_ppo)')
    parser.add_argument('--hyperparams', type=str, required=True, help='Path to hyperparameters JSON file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--eval-config', type=str, help='Path to evaluation config JSON file')

    # Legacy parameters (for backward compatibility)
    parser.add_argument('--symbol', type=str, help='Trading symbol (legacy mode)')
    parser.add_argument('--timeframe', type=str, help='Candle timeframe (legacy mode)')
    parser.add_argument('--market', type=str, help='spot or futures (legacy mode)')
    parser.add_argument('--timesteps', type=int, help='Training timesteps (legacy mode)')
    parser.add_argument('--no-advanced', action='store_true', help='Disable advanced features (legacy mode)')

    args = parser.parse_args()

    # Set random seed
    np.random.seed(args.seed)
    import random
    import torch
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    # Load hyperparameters
    with open(args.hyperparams, 'r') as f:
        hyperparams = json.load(f)

    logger.info(f"🤖 Starting PPO Batch Training")
    logger.info(f"   Output: {args.output_name}")
    logger.info(f"   Device: {args.device}")
    logger.info(f"   Seed: {args.seed}")
    logger.info(f"   Total timesteps: {hyperparams.get('total_timesteps', 5_000_000):,}")

    # Load data files
    data_file_paths = args.data_files.split(',')
    logger.info(f"   Loading {len(data_file_paths)} data files...")

    dfs = []
    for file_path in data_file_paths:
        df = pd.read_parquet(file_path.strip())
        logger.info(f"      - {Path(file_path).name}: {len(df)} rows")
        dfs.append(df)

    # Concatenate all data
    df_combined = pd.concat(dfs, ignore_index=True).sort_values('open_time').reset_index(drop=True)
    logger.info(f"   Combined data: {len(df_combined)} rows")

    # Create environment
    env = DummyVecEnv([lambda: SimpleTradingEnv(df_combined)])

    # Create PPO agent with hyperparameters
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=hyperparams.get('learning_rate', 3e-4),
        n_steps=hyperparams.get('n_steps', 4096),
        batch_size=hyperparams.get('batch_size', 256),
        n_epochs=args.epochs,  # Use CLI epochs parameter
        gamma=hyperparams.get('gamma', 0.995),
        gae_lambda=hyperparams.get('gae_lambda', 0.97),
        clip_range=hyperparams.get('clip_range', 0.2),
        ent_coef=hyperparams.get('ent_coef', 0.001),
        vf_coef=hyperparams.get('vf_coef', 0.5),
        max_grad_norm=hyperparams.get('max_grad_norm', 0.5),
        target_kl=hyperparams.get('target_kl', 0.02),
    )

    # Train
    logger.info(f"\n🚀 Training started...")
    total_timesteps = hyperparams.get('total_timesteps', 5_000_000)

    callback = TrainingCallback()
    model.learn(total_timesteps=total_timesteps, callback=callback)

    # Save model
    save_path = Path("data/models") / f"{args.output_name}.zip"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(save_path))

    logger.info(f"\n✅ Training complete!")
    logger.info(f"   Model saved: {save_path}")
