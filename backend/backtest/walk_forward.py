"""
Walk-forward optimization for model validation
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .engine import BacktestEngine


class WalkForwardOptimizer:
    """
    Rolling window walk-forward optimization
    Prevents overfitting by continuously re-training and testing on out-of-sample data
    """

    def __init__(
        self,
        train_period_days: int = 180,
        test_period_days: int = 30,
        step_size_days: Optional[int] = None
    ):
        """
        Args:
            train_period_days: Training window size
            test_period_days: Testing window size
            step_size_days: Step size for rolling window (default: test_period_days)
        """
        self.train_period = train_period_days
        self.test_period = test_period_days
        self.step_size = step_size_days or test_period_days

    def run(
        self,
        agent,
        data_loader,
        start_date: str,
        end_date: str,
        optimize_hyperparams: bool = False,
        param_grid: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Run walk-forward optimization

        Args:
            agent: Trading agent
            data_loader: Function to load data for date range
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            optimize_hyperparams: If True, optimize hyperparameters on each window
            param_grid: Hyperparameter search space

        Returns:
            DataFrame with test results for each window
        """

        results = []

        current_start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        window_idx = 0

        while current_start < end:
            train_end = current_start + pd.Timedelta(days=self.train_period)
            test_start = train_end
            test_end = test_start + pd.Timedelta(days=self.test_period)

            if test_end > end:
                break

            print(f"\n{'='*60}")
            print(f"Window {window_idx + 1}")
            print(f"Training: {current_start.date()} to {train_end.date()}")
            print(f"Testing: {test_start.date()} to {test_end.date()}")
            print(f"{'='*60}")

            # Load data
            train_data = data_loader(current_start, train_end)
            test_data = data_loader(test_start, test_end)

            # Optimize hyperparameters if requested
            if optimize_hyperparams and param_grid:
                best_params = self._optimize_hyperparams(
                    agent, train_data, param_grid
                )
                agent.set_hyperparameters(best_params)
                print(f"✅ Best hyperparameters: {best_params}")

            # Train agent
            print("📚 Training agent...")
            agent.train(train_data)

            # Test agent
            print("🧪 Testing agent...")
            backtest = BacktestEngine()
            backtest.load_data_from_dataframe(test_data)
            backtest.run(agent, test_start, test_end)

            # Get metrics
            metrics = backtest.get_metrics()

            # Store results
            results.append({
                'window': window_idx,
                'train_start': current_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                **metrics
            })

            print(f"📊 Test Results:")
            print(f"   Total Return: {metrics.get('total_return_pct', 0):.2f}%")
            print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"   Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
            print(f"   Win Rate: {metrics.get('win_rate', 0):.2f}%")

            # Move to next window
            current_start += pd.Timedelta(days=self.step_size)
            window_idx += 1

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Calculate overall statistics
        print(f"\n{'='*60}")
        print("OVERALL WALK-FORWARD RESULTS")
        print(f"{'='*60}")
        print(f"Total Windows: {len(results_df)}")
        print(f"Avg Total Return: {results_df['total_return_pct'].mean():.2f}%")
        print(f"Avg Sharpe Ratio: {results_df['sharpe_ratio'].mean():.2f}")
        print(f"Avg Max Drawdown: {results_df['max_drawdown_pct'].mean():.2f}%")
        print(f"Avg Win Rate: {results_df['win_rate'].mean():.2f}%")
        print(f"Win Rate Consistency: {results_df['win_rate'].std():.2f}%")
        print(f"Positive Return Windows: {(results_df['total_return_pct'] > 0).sum()} / {len(results_df)}")

        return results_df

    def _optimize_hyperparams(
        self,
        agent,
        train_data: pd.DataFrame,
        param_grid: Dict[str, List]
    ) -> Dict[str, Any]:
        """
        Grid search hyperparameter optimization

        Args:
            agent: Trading agent
            train_data: Training data
            param_grid: Parameter grid

        Returns:
            Best hyperparameters
        """
        from itertools import product

        # Generate all combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())

        best_score = float('-inf')
        best_params = None

        for combination in product(*values):
            params = dict(zip(keys, combination))

            # Set parameters
            agent.set_hyperparameters(params)

            # Train and validate
            agent.train(train_data)

            # Use last 20% of train data for validation
            val_split = int(len(train_data) * 0.8)
            val_data = train_data.iloc[val_split:]

            # Quick backtest on validation set
            backtest = BacktestEngine()
            backtest.load_data_from_dataframe(val_data)
            backtest.run(agent, val_data.index[0], val_data.index[-1])

            metrics = backtest.get_metrics()

            # Score: weighted combination of Sharpe and return
            score = metrics.get('sharpe_ratio', 0) * 0.6 + metrics.get('total_return_pct', 0) / 100 * 0.4

            if score > best_score:
                best_score = score
                best_params = params

        return best_params


class AnchoredWalkForward(WalkForwardOptimizer):
    """
    Anchored walk-forward: Training window expands (always starts from beginning)
    More data for training, but risk of overfitting to old regime
    """

    def run(
        self,
        agent,
        data_loader,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        results = []

        anchor_date = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        test_start = anchor_date + pd.Timedelta(days=self.train_period)

        window_idx = 0

        while test_start < end:
            train_end = test_start
            test_end = test_start + pd.Timedelta(days=self.test_period)

            if test_end > end:
                break

            print(f"\nWindow {window_idx + 1} (Anchored)")
            print(f"Training: {anchor_date.date()} to {train_end.date()}")
            print(f"Testing: {test_start.date()} to {test_end.date()}")

            # Load data (train from anchor)
            train_data = data_loader(anchor_date, train_end)
            test_data = data_loader(test_start, test_end)

            # Train
            agent.train(train_data)

            # Test
            backtest = BacktestEngine()
            backtest.load_data_from_dataframe(test_data)
            backtest.run(agent, test_start, test_end)

            metrics = backtest.get_metrics()

            results.append({
                'window': window_idx,
                'train_start': anchor_date,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                **metrics
            })

            # Move test window
            test_start += pd.Timedelta(days=self.step_size)
            window_idx += 1

        return pd.DataFrame(results)
