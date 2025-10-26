"""
Proximal Policy Optimization (PPO) for fine-tuning Decision Transformer
"""

import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple
import numpy as np


class PPOTrainer:
    """
    PPO algorithm for fine-tuning RL agents
    Optimizes policy with clipped surrogate objective
    """

    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 3e-5,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 1.0,
        ppo_epochs: int = 4,
        batch_size: int = 256
    ):
        """
        Args:
            model: Policy network (Decision Transformer)
            learning_rate: Learning rate
            clip_epsilon: PPO clipping parameter
            value_coef: Value loss coefficient
            entropy_coef: Entropy bonus coefficient
            max_grad_norm: Gradient clipping threshold
            ppo_epochs: Number of PPO update epochs per batch
            batch_size: Mini-batch size
        """
        self.model = model
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.ppo_epochs = ppo_epochs
        self.batch_size = batch_size

        self.optimizer = optim.AdamW(model.parameters(), lr=learning_rate)

        # Value network (if not part of main model)
        self.value_net = nn.Sequential(
            nn.Linear(model.state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

        # Training statistics
        self.train_stats = {
            'policy_loss': [],
            'value_loss': [],
            'entropy': [],
            'total_loss': [],
            'kl_div': []
        }

    def compute_gae(
        self,
        rewards: torch.Tensor,
        values: torch.Tensor,
        dones: torch.Tensor,
        gamma: float = 0.99,
        lambda_: float = 0.95
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute Generalized Advantage Estimation (GAE)

        Args:
            rewards: Rewards (T,)
            values: Value estimates (T,)
            dones: Done flags (T,)
            gamma: Discount factor
            lambda_: GAE lambda parameter

        Returns:
            advantages, returns
        """
        advantages = torch.zeros_like(rewards)
        returns = torch.zeros_like(rewards)

        gae = 0
        next_value = 0

        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
                next_non_terminal = 1.0 - dones[t]
            else:
                next_value = values[t + 1]
                next_non_terminal = 1.0 - dones[t]

            delta = rewards[t] + gamma * next_value * next_non_terminal - values[t]
            gae = delta + gamma * lambda_ * next_non_terminal * gae

            advantages[t] = gae
            returns[t] = gae + values[t]

        return advantages, returns

    def update(
        self,
        trajectories: List[Dict[str, torch.Tensor]],
        gamma: float = 0.99,
        lambda_: float = 0.95
    ) -> Dict[str, float]:
        """
        PPO update step

        Args:
            trajectories: List of trajectory dictionaries with keys:
                          'states', 'actions', 'rewards', 'log_probs', 'dones'
            gamma: Discount factor
            lambda_: GAE lambda

        Returns:
            Training statistics
        """

        # Concatenate all trajectories
        all_states = torch.cat([traj['states'] for traj in trajectories], dim=0)
        all_actions = torch.cat([traj['actions'] for traj in trajectories], dim=0)
        all_rewards = torch.cat([traj['rewards'] for traj in trajectories], dim=0)
        all_old_log_probs = torch.cat([traj['log_probs'] for traj in trajectories], dim=0)
        all_dones = torch.cat([traj['dones'] for traj in trajectories], dim=0)

        # Compute values
        with torch.no_grad():
            all_values = self.value_net(all_states).squeeze(-1)

        # Compute GAE
        advantages, returns = self.compute_gae(all_rewards, all_values, all_dones, gamma, lambda_)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO update epochs
        epoch_stats = {
            'policy_loss': [],
            'value_loss': [],
            'entropy': [],
            'total_loss': [],
            'kl_div': []
        }

        for epoch in range(self.ppo_epochs):
            # Mini-batch training
            indices = torch.randperm(len(all_states))

            for start in range(0, len(all_states), self.batch_size):
                end = start + self.batch_size
                batch_indices = indices[start:end]

                batch_states = all_states[batch_indices]
                batch_actions = all_actions[batch_indices]
                batch_old_log_probs = all_old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]

                # Forward pass
                # Note: This is simplified - actual DT forward needs proper sequence handling
                action_logits = self.model(
                    batch_states.unsqueeze(1),  # Add sequence dimension
                    batch_actions.unsqueeze(1),
                    torch.zeros_like(batch_states[:, :1]),  # Dummy returns-to-go
                    torch.zeros(batch_states.size(0), 1, dtype=torch.long)  # Dummy timesteps
                ).squeeze(1)

                # Compute log probs and entropy
                action_dist = torch.distributions.Categorical(logits=action_logits)
                new_log_probs = action_dist.log_prob(batch_actions)
                entropy = action_dist.entropy().mean()

                # Policy loss (PPO clipped objective)
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value loss
                batch_values = self.value_net(batch_states).squeeze(-1)
                value_loss = nn.functional.mse_loss(batch_values, batch_returns)

                # Total loss
                total_loss = (
                    policy_loss +
                    self.value_coef * value_loss -
                    self.entropy_coef * entropy
                )

                # Backward pass
                self.optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
                self.optimizer.step()

                # KL divergence (for monitoring)
                with torch.no_grad():
                    kl_div = (batch_old_log_probs - new_log_probs).mean()

                # Store stats
                epoch_stats['policy_loss'].append(policy_loss.item())
                epoch_stats['value_loss'].append(value_loss.item())
                epoch_stats['entropy'].append(entropy.item())
                epoch_stats['total_loss'].append(total_loss.item())
                epoch_stats['kl_div'].append(kl_div.item())

        # Average stats
        avg_stats = {k: np.mean(v) for k, v in epoch_stats.items()}

        # Store for logging
        for k, v in avg_stats.items():
            self.train_stats[k].append(v)

        return avg_stats

    def save(self, path: str):
        """Save PPO trainer state"""
        torch.save({
            'model_state': self.model.state_dict(),
            'value_net_state': self.value_net.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'train_stats': self.train_stats
        }, path)

    def load(self, path: str):
        """Load PPO trainer state"""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state'])
        self.value_net.load_state_dict(checkpoint['value_net_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        self.train_stats = checkpoint['train_stats']


class PPORewardShaper:
    """
    Reward shaping for trading RL
    Transforms raw PnL into more informative reward signals
    """

    @staticmethod
    def shape_reward(
        pnl: float,
        risk_adjusted: bool = True,
        drawdown_penalty: float = 0.1,
        volatility: float = 0.0,
        position_holding_penalty: float = 0.0001
    ) -> float:
        """
        Shape reward for better learning

        Args:
            pnl: Raw profit/loss
            risk_adjusted: Use Sharpe-like adjustment
            drawdown_penalty: Penalty for drawdowns
            volatility: Current volatility (for risk adjustment)
            position_holding_penalty: Small penalty for holding (encourage action)

        Returns:
            Shaped reward
        """

        reward = pnl

        # Risk adjustment
        if risk_adjusted and volatility > 0:
            reward = reward / (volatility + 1e-8)

        # Drawdown penalty
        if pnl < 0:
            reward = reward * (1 + drawdown_penalty)

        # Position holding cost (prevent infinite holding)
        reward -= position_holding_penalty

        return reward

    @staticmethod
    def multi_objective_reward(
        pnl: float,
        sharpe: float,
        drawdown: float,
        win_rate: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Multi-objective reward combining multiple metrics

        Args:
            pnl: Profit/loss
            sharpe: Sharpe ratio
            drawdown: Max drawdown (negative)
            win_rate: Win rate (0-1)
            weights: Weight for each objective

        Returns:
            Combined reward
        """

        if weights is None:
            weights = {
                'pnl': 0.4,
                'sharpe': 0.3,
                'drawdown': 0.2,
                'win_rate': 0.1
            }

        # Normalize components
        pnl_normalized = np.tanh(pnl / 1000)  # Normalize to [-1, 1]
        sharpe_normalized = np.tanh(sharpe / 2)  # Sharpe > 2 is excellent
        drawdown_normalized = np.tanh(drawdown / 0.2)  # Cap at 20% drawdown
        win_rate_normalized = (win_rate - 0.5) * 2  # Center at 50%

        reward = (
            weights['pnl'] * pnl_normalized +
            weights['sharpe'] * sharpe_normalized +
            weights['drawdown'] * drawdown_normalized +
            weights['win_rate'] * win_rate_normalized
        )

        return reward
