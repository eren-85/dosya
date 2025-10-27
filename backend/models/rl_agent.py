"""
Reinforcement Learning Agent - PPO with GPU Support
Optimized for RTX 4060
"""

import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import logging

# Stable Baselines3
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor

import torch

# Compute config
import sys
sys.path.append('..')
from backend.config.compute_config import get_compute

logger = logging.getLogger(__name__)


@dataclass
class TradingState:
    """Current trading state"""
    position: float  # -1 (short), 0 (neutral), 1 (long)
    cash: float
    holdings: float
    portfolio_value: float
    step: int


class TradingEnvironment(gym.Env):
    """
    Custom Trading Environment for RL

    Features:
        - Long/Short trading
        - Transaction costs
        - Risk management
        - Multi-asset support (future)
    """

    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 100000.0,
        commission: float = 0.001,
        max_position: float = 1.0,
        lookback_window: int = 60,
    ):
        """
        Initialize trading environment

        Args:
            df: Market data (OHLCV + indicators)
            initial_balance: Starting cash
            commission: Trading commission (0.001 = 0.1%)
            max_position: Maximum position size (1.0 = 100% of portfolio)
            lookback_window: Number of historical bars in observation
        """
        super(TradingEnvironment, self).__init__()

        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.commission = commission
        self.max_position = max_position
        self.lookback_window = lookback_window

        # Feature columns (exclude OHLCV, keep indicators)
        self.feature_columns = [
            col for col in df.columns
            if col not in ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        ]
        self.n_features = len(self.feature_columns)

        # Action space: [-1, 1] continuous
        # -1 = full short, 0 = neutral, 1 = full long
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(1,),
            dtype=np.float32
        )

        # Observation space: lookback_window x n_features
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(lookback_window, self.n_features),
            dtype=np.float32
        )

        # State
        self.current_step = 0
        self.cash = initial_balance
        self.holdings = 0.0
        self.position = 0.0

        self.history = []

    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, dict]:
        """Reset environment"""
        super().reset(seed=seed)

        self.current_step = self.lookback_window
        self.cash = self.initial_balance
        self.holdings = 0.0
        self.position = 0.0
        self.history = []

        return self._get_observation(), {}

    def _get_observation(self) -> np.ndarray:
        """Get current observation (lookback window of features)"""
        start = self.current_step - self.lookback_window
        end = self.current_step

        obs = self.df[self.feature_columns].iloc[start:end].values
        obs = obs.astype(np.float32)

        # Normalize (simple scaling)
        obs = np.nan_to_num(obs, nan=0.0, posinf=0.0, neginf=0.0)

        return obs

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        Execute one trading step

        Args:
            action: Trading action [-1, 1]

        Returns:
            observation, reward, terminated, truncated, info
        """
        current_price = self.df['close'].iloc[self.current_step]
        target_position = float(action[0])

        # Calculate position change
        position_change = target_position - self.position

        # Execute trade if position changed
        reward = 0.0
        if abs(position_change) > 0.01:  # Threshold to avoid tiny trades
            trade_value = abs(position_change) * self.cash
            trade_cost = trade_value * self.commission

            # Update holdings
            self.holdings += position_change * (self.cash / current_price)
            self.cash -= trade_cost
            self.position = target_position

        # Calculate portfolio value
        portfolio_value = self.cash + (self.holdings * current_price)

        # Reward = portfolio value change
        if self.history:
            prev_value = self.history[-1]['portfolio_value']
            reward = (portfolio_value - prev_value) / prev_value
        else:
            reward = 0.0

        # Penalty for holding too long
        reward -= 0.0001

        # Store history
        self.history.append({
            'step': self.current_step,
            'position': self.position,
            'cash': self.cash,
            'holdings': self.holdings,
            'portfolio_value': portfolio_value,
            'price': current_price,
        })

        # Move to next step
        self.current_step += 1

        # Check if episode is done
        terminated = self.current_step >= len(self.df) - 1
        truncated = portfolio_value < self.initial_balance * 0.5  # Stop loss at 50%

        # Info
        info = {
            'portfolio_value': portfolio_value,
            'position': self.position,
            'step': self.current_step,
        }

        return self._get_observation(), reward, terminated, truncated, info


class TensorboardCallback(BaseCallback):
    """Custom callback for logging to TensorBoard"""

    def __init__(self, verbose=0):
        super(TensorboardCallback, self).__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []

    def _on_step(self) -> bool:
        # Log episode stats
        if 'episode' in self.locals.get('infos', [{}])[0]:
            info = self.locals['infos'][0]['episode']
            self.logger.record('rollout/ep_rew_mean', info['r'])
            self.logger.record('rollout/ep_len_mean', info['l'])

        return True


class RLAgent:
    """
    Reinforcement Learning Agent with GPU Support

    Features:
        - PPO algorithm (Stable-Baselines3)
        - GPU training for faster convergence
        - Parallel environments
        - Automatic hyperparameter tuning
    """

    def __init__(
        self,
        env_config: dict,
        n_envs: int = None,
        learning_rate: float = 3e-4,
        n_steps: int = 2048,
        batch_size: int = 64,
        n_epochs: int = 10,
    ):
        """
        Initialize RL agent

        Args:
            env_config: Environment configuration (df, initial_balance, etc.)
            n_envs: Number of parallel environments (auto-detect if None)
            learning_rate: PPO learning rate
            n_steps: Steps per environment per update
            batch_size: Minibatch size
            n_epochs: Number of epochs per update
        """
        self.env_config = env_config

        # Get compute configuration
        self.compute = get_compute()
        self.device = self.compute.get_sb3_device()

        # Number of parallel environments
        if n_envs is None:
            n_envs = self.compute.config.rl_n_envs if hasattr(self.compute.config, 'rl_n_envs') else 8

        self.n_envs = n_envs

        logger.info(f"🤖 RL Agent (PPO)")
        logger.info(f"   Device: {self.device.upper()}")
        logger.info(f"   Parallel Environments: {n_envs}")

        # Create vectorized environment
        self.env = self._create_env()

        # PPO model
        self.model = PPO(
            policy='MlpPolicy',
            env=self.env,
            learning_rate=learning_rate,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            device=self.device,
            verbose=1,
            tensorboard_log='./logs/tensorboard/',
        )

        logger.info(f"   Policy: MlpPolicy")
        logger.info(f"   Learning Rate: {learning_rate}")

    def _create_env(self):
        """Create vectorized environment"""

        def make_env():
            def _init():
                env = TradingEnvironment(**self.env_config)
                env = Monitor(env)
                return env
            return _init

        # Use SubprocVecEnv for better parallelization
        if self.n_envs > 1:
            env = SubprocVecEnv([make_env() for _ in range(self.n_envs)])
        else:
            env = DummyVecEnv([make_env()])

        return env

    def train(
        self,
        total_timesteps: int = 100000,
        eval_freq: int = 10000,
        eval_env: Optional[gym.Env] = None,
    ):
        """
        Train RL agent

        Args:
            total_timesteps: Total training timesteps
            eval_freq: Evaluation frequency
            eval_env: Optional evaluation environment
        """
        logger.info(f"\n🏋️  Training RL Agent")
        logger.info(f"   Total Timesteps: {total_timesteps:,}")

        # Callbacks
        callbacks = []

        # TensorBoard callback
        callbacks.append(TensorboardCallback())

        # Evaluation callback
        if eval_env is not None:
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path='./logs/best_model/',
                log_path='./logs/eval/',
                eval_freq=eval_freq,
                deterministic=True,
                render=False,
            )
            callbacks.append(eval_callback)

        # Train
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True,
        )

        logger.info("✅ Training completed")

        # Memory cleanup
        if self.device == 'cuda':
            self.compute.optimize_memory()

    def predict(self, observation: np.ndarray, deterministic: bool = True) -> np.ndarray:
        """
        Predict action

        Args:
            observation: Current observation
            deterministic: Use deterministic policy

        Returns:
            Action
        """
        action, _ = self.model.predict(observation, deterministic=deterministic)
        return action

    def evaluate(self, eval_env: gym.Env, n_episodes: int = 10) -> Dict[str, float]:
        """
        Evaluate agent performance

        Args:
            eval_env: Evaluation environment
            n_episodes: Number of episodes

        Returns:
            Performance metrics
        """
        logger.info(f"\n📊 Evaluating Agent ({n_episodes} episodes)")

        episode_rewards = []
        episode_lengths = []

        for episode in range(n_episodes):
            obs, _ = eval_env.reset()
            done = False
            episode_reward = 0.0
            episode_length = 0

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = eval_env.step(action)
                done = terminated or truncated

                episode_reward += reward
                episode_length += 1

            episode_rewards.append(episode_reward)
            episode_lengths.append(episode_length)

            logger.info(f"   Episode {episode+1}: Reward={episode_reward:.4f}, Length={episode_length}")

        metrics = {
            'mean_reward': np.mean(episode_rewards),
            'std_reward': np.std(episode_rewards),
            'mean_length': np.mean(episode_lengths),
        }

        logger.info(f"\n📈 Evaluation Results:")
        logger.info(f"   Mean Reward: {metrics['mean_reward']:.4f} ± {metrics['std_reward']:.4f}")
        logger.info(f"   Mean Episode Length: {metrics['mean_length']:.1f}")

        return metrics

    def save(self, path: str):
        """Save model"""
        self.model.save(path)
        logger.info(f"💾 Model saved to {path}")

    def load(self, path: str):
        """Load model"""
        self.model = PPO.load(path, env=self.env, device=self.device)
        logger.info(f"📂 Model loaded from {path}")


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Initialize compute
    from backend.config.compute_config import initialize_compute
    initialize_compute(mode='hybrid')

    # Generate sample market data
    np.random.seed(42)
    n_samples = 5000

    dates = pd.date_range('2020-01-01', periods=n_samples, freq='1h')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': 50000 + np.cumsum(np.random.randn(n_samples) * 100),
        'high': 50000 + np.cumsum(np.random.randn(n_samples) * 100),
        'low': 50000 + np.cumsum(np.random.randn(n_samples) * 100),
        'close': 50000 + np.cumsum(np.random.randn(n_samples) * 100),
        'volume': np.random.randint(100, 1000, n_samples),
    })

    # Add dummy indicators
    df['rsi'] = np.random.rand(n_samples) * 100
    df['macd'] = np.random.randn(n_samples)
    df['bb_upper'] = df['close'] * 1.02
    df['bb_lower'] = df['close'] * 0.98

    # Environment config
    env_config = {
        'df': df,
        'initial_balance': 100000.0,
        'commission': 0.001,
        'lookback_window': 60,
    }

    # Create agent
    agent = RLAgent(env_config, n_envs=4)

    # Train
    agent.train(total_timesteps=50000, eval_freq=5000)

    print("\n✅ RL Agent training completed")
