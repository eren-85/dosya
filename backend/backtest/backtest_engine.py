"""
Backtest Engine - Vectorized with CPU Optimization
High-performance backtesting for trading strategies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Parallel processing
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

# Compute config
import sys
sys.path.append('..')
from backend.config.compute_config import get_compute

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Backtest configuration"""
    initial_capital: float = 100000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005   # 0.05%
    position_size: float = 1.0  # Fraction of capital per trade
    max_positions: int = 1      # Maximum concurrent positions
    stop_loss: Optional[float] = None  # Stop loss percentage
    take_profit: Optional[float] = None  # Take profit percentage


@dataclass
class Trade:
    """Single trade record"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    size: float
    direction: str  # 'long' or 'short'
    pnl: float
    pnl_percent: float
    commission: float
    slippage: float
    reason: str = 'signal'  # 'signal', 'stop_loss', 'take_profit'


@dataclass
class BacktestResults:
    """Backtest performance metrics"""
    # Returns
    total_return: float = 0.0
    annual_return: float = 0.0
    cumulative_returns: np.ndarray = field(default_factory=lambda: np.array([]))

    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    volatility: float = 0.0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0

    # Equity curve
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    trades: List[Trade] = field(default_factory=list)

    # Execution time
    execution_time_seconds: float = 0.0


class BacktestEngine:
    """
    High-performance backtesting engine

    Features:
        - Vectorized computations (NumPy)
        - CPU-optimized (pandas + NumPy)
        - Parallel backtesting (multiple strategies/parameters)
        - Realistic trading costs (commission + slippage)
        - Risk management (stop loss, take profit)
        - Position sizing
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtest engine

        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig()

        # Get compute configuration
        self.compute = get_compute()
        self.n_jobs = self.compute.config.backtest_n_jobs
        self.parallel = self.compute.config.backtest_parallel

        logger.info(f"📊 Backtest Engine")
        logger.info(f"   Device: {self.compute.config.backtest_device.upper()}")
        logger.info(f"   Parallel: {self.parallel}")
        if self.parallel and self.n_jobs != 1:
            logger.info(f"   Workers: {self.n_jobs if self.n_jobs > 0 else 'All CPUs'}")

    def run(
        self,
        data: pd.DataFrame,
        signals: pd.Series,  # 1 = long, -1 = short, 0 = neutral
        strategy_name: str = "Strategy",
    ) -> BacktestResults:
        """
        Run backtest on historical data

        Args:
            data: OHLCV data with indicators
            signals: Trading signals (1 = long, -1 = short, 0 = neutral)
            strategy_name: Name of strategy

        Returns:
            BacktestResults with performance metrics
        """
        start_time = pd.Timestamp.now()

        logger.info(f"\n🏁 Running Backtest: {strategy_name}")
        logger.info(f"   Period: {data.index[0]} to {data.index[-1]}")
        logger.info(f"   Bars: {len(data):,}")
        logger.info(f"   Initial Capital: ${self.config.initial_capital:,.2f}")

        # Ensure signals are aligned with data
        if len(signals) != len(data):
            raise ValueError(f"Signals length ({len(signals)}) != data length ({len(data)})")

        # Vectorized backtest
        results = self._vectorized_backtest(data, signals)

        # Calculate execution time
        results.execution_time_seconds = (pd.Timestamp.now() - start_time).total_seconds()

        # Log summary
        self._log_results(results)

        return results

    def _vectorized_backtest(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
    ) -> BacktestResults:
        """
        Vectorized backtesting (fast)

        This approach computes all trades at once using NumPy
        instead of iterating through each bar.
        """
        # Convert to numpy for speed
        prices = data['close'].values
        timestamps = data.index.values

        signals_array = signals.values

        # Detect signal changes (entries and exits)
        signal_diff = np.diff(signals_array, prepend=0)
        entries = np.where(signal_diff != 0)[0]

        trades = []
        equity = np.full(len(prices), self.config.initial_capital, dtype=float)
        position = 0  # Current position: 0, 1 (long), -1 (short)
        position_size = 0.0
        entry_price = 0.0
        entry_idx = 0

        for i in range(len(prices)):
            # Check for entry signal
            if i in entries and position == 0:
                signal = signals_array[i]

                if signal != 0:  # Long or short entry
                    direction = 'long' if signal > 0 else 'short'
                    position = signal

                    # Calculate position size
                    available_capital = equity[i-1] if i > 0 else self.config.initial_capital
                    position_value = available_capital * self.config.position_size
                    position_size = position_value / prices[i]

                    # Entry with commission and slippage
                    entry_price = prices[i] * (1 + self.config.slippage * position)
                    commission = position_value * self.config.commission
                    slippage_cost = position_value * self.config.slippage

                    equity[i] = available_capital - commission - slippage_cost
                    entry_idx = i

            # Check for exit signal or stop/take profit
            elif position != 0:
                exit_triggered = False
                exit_reason = 'signal'

                # Signal exit
                if i in entries and signals_array[i] != position:
                    exit_triggered = True
                    exit_reason = 'signal'

                # Stop loss
                if self.config.stop_loss is not None:
                    if position > 0:  # Long
                        if prices[i] < entry_price * (1 - self.config.stop_loss):
                            exit_triggered = True
                            exit_reason = 'stop_loss'
                    else:  # Short
                        if prices[i] > entry_price * (1 + self.config.stop_loss):
                            exit_triggered = True
                            exit_reason = 'stop_loss'

                # Take profit
                if self.config.take_profit is not None:
                    if position > 0:  # Long
                        if prices[i] > entry_price * (1 + self.config.take_profit):
                            exit_triggered = True
                            exit_reason = 'take_profit'
                    else:  # Short
                        if prices[i] < entry_price * (1 - self.config.take_profit):
                            exit_triggered = True
                            exit_reason = 'take_profit'

                # Execute exit
                if exit_triggered or i == len(prices) - 1:
                    exit_price = prices[i] * (1 - self.config.slippage * position)

                    # Calculate P&L
                    if position > 0:  # Long
                        pnl = (exit_price - entry_price) * position_size
                    else:  # Short
                        pnl = (entry_price - exit_price) * position_size

                    position_value = abs(position_size) * exit_price
                    commission = position_value * self.config.commission
                    slippage_cost = position_value * self.config.slippage

                    pnl -= (commission + slippage_cost)
                    pnl_percent = pnl / (abs(position_size) * entry_price) * 100

                    # Update equity
                    equity[i] = equity[entry_idx] + pnl

                    # Record trade
                    trades.append(Trade(
                        entry_time=timestamps[entry_idx],
                        exit_time=timestamps[i],
                        entry_price=entry_price,
                        exit_price=exit_price,
                        size=position_size,
                        direction='long' if position > 0 else 'short',
                        pnl=pnl,
                        pnl_percent=pnl_percent,
                        commission=commission,
                        slippage=slippage_cost,
                        reason=exit_reason,
                    ))

                    # Reset position
                    position = 0
                    position_size = 0.0

                else:
                    # No exit, carry forward equity
                    if i > 0:
                        equity[i] = equity[i-1]

            else:
                # No position, carry forward equity
                if i > 0:
                    equity[i] = equity[i-1]

        # Build equity curve
        equity_curve = pd.DataFrame({
            'timestamp': timestamps,
            'equity': equity,
        })
        equity_curve.set_index('timestamp', inplace=True)

        # Calculate metrics
        results = self._calculate_metrics(equity_curve, trades)

        return results

    def _calculate_metrics(
        self,
        equity_curve: pd.DataFrame,
        trades: List[Trade],
    ) -> BacktestResults:
        """Calculate performance metrics"""

        results = BacktestResults()
        results.equity_curve = equity_curve
        results.trades = trades

        # Returns
        final_equity = equity_curve['equity'].iloc[-1]
        initial_equity = self.config.initial_capital

        results.total_return = (final_equity - initial_equity) / initial_equity * 100

        # Cumulative returns
        results.cumulative_returns = (equity_curve['equity'] / initial_equity - 1).values

        # Annual return (assuming daily data)
        n_days = len(equity_curve)
        n_years = n_days / 365.25
        results.annual_return = ((final_equity / initial_equity) ** (1 / n_years) - 1) * 100

        # Daily returns
        daily_returns = equity_curve['equity'].pct_change().dropna()

        # Volatility
        results.volatility = daily_returns.std() * np.sqrt(365.25) * 100

        # Sharpe ratio (assuming 0% risk-free rate)
        if daily_returns.std() > 0:
            results.sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(365.25)
        else:
            results.sharpe_ratio = 0.0

        # Sortino ratio
        downside_returns = daily_returns[daily_returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            results.sortino_ratio = (daily_returns.mean() / downside_returns.std()) * np.sqrt(365.25)
        else:
            results.sortino_ratio = 0.0

        # Drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        results.max_drawdown = drawdown.min() * 100

        # Drawdown duration
        drawdown_periods = (drawdown < 0).astype(int)
        if drawdown_periods.sum() > 0:
            results.max_drawdown_duration = drawdown_periods.groupby(
                (drawdown_periods != drawdown_periods.shift()).cumsum()
            ).sum().max()
        else:
            results.max_drawdown_duration = 0

        # Trade statistics
        if trades:
            results.total_trades = len(trades)

            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl <= 0]

            results.winning_trades = len(winning_trades)
            results.losing_trades = len(losing_trades)
            results.win_rate = results.winning_trades / results.total_trades * 100

            if winning_trades:
                results.avg_win = np.mean([t.pnl for t in winning_trades])
            if losing_trades:
                results.avg_loss = np.mean([t.pnl for t in losing_trades])

            # Profit factor
            total_wins = sum(t.pnl for t in winning_trades)
            total_losses = abs(sum(t.pnl for t in losing_trades))

            if total_losses > 0:
                results.profit_factor = total_wins / total_losses
            else:
                results.profit_factor = float('inf') if total_wins > 0 else 0.0

            # Expectancy
            results.expectancy = np.mean([t.pnl for t in trades])

        return results

    def _log_results(self, results: BacktestResults):
        """Log backtest results"""
        logger.info(f"\n📈 Backtest Results:")
        logger.info(f"   Total Return: {results.total_return:.2f}%")
        logger.info(f"   Annual Return: {results.annual_return:.2f}%")
        logger.info(f"   Sharpe Ratio: {results.sharpe_ratio:.2f}")
        logger.info(f"   Sortino Ratio: {results.sortino_ratio:.2f}")
        logger.info(f"   Max Drawdown: {results.max_drawdown:.2f}%")
        logger.info(f"   Volatility: {results.volatility:.2f}%")

        logger.info(f"\n💼 Trade Statistics:")
        logger.info(f"   Total Trades: {results.total_trades}")
        logger.info(f"   Win Rate: {results.win_rate:.2f}%")
        logger.info(f"   Profit Factor: {results.profit_factor:.2f}")
        logger.info(f"   Expectancy: ${results.expectancy:.2f}")
        logger.info(f"   Avg Win: ${results.avg_win:.2f}")
        logger.info(f"   Avg Loss: ${results.avg_loss:.2f}")

        logger.info(f"\n⏱️  Execution Time: {results.execution_time_seconds:.2f}s")

    def optimize_parameters(
        self,
        data: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List],
        metric: str = 'sharpe_ratio',
    ) -> Tuple[Dict, BacktestResults]:
        """
        Optimize strategy parameters using parallel grid search

        Args:
            data: OHLCV data
            strategy_func: Function that takes params and returns signals
            param_grid: Parameter grid to search
            metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)

        Returns:
            Best parameters and results
        """
        logger.info(f"\n🔍 Parameter Optimization")
        logger.info(f"   Metric: {metric}")

        # Generate parameter combinations
        from itertools import product

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))

        logger.info(f"   Testing {len(param_combinations)} combinations...")

        # Parallel optimization
        if self.parallel and len(param_combinations) > 1:
            results_list = self._parallel_optimize(
                data, strategy_func, param_names, param_combinations
            )
        else:
            results_list = self._sequential_optimize(
                data, strategy_func, param_names, param_combinations
            )

        # Find best parameters
        best_idx = np.argmax([getattr(r[1], metric) for r in results_list])
        best_params, best_results = results_list[best_idx]

        logger.info(f"\n✅ Best Parameters:")
        for key, value in best_params.items():
            logger.info(f"   {key}: {value}")
        logger.info(f"   {metric}: {getattr(best_results, metric):.4f}")

        return best_params, best_results

    def _parallel_optimize(self, data, strategy_func, param_names, param_combinations):
        """Run optimization in parallel"""
        results = []

        with ProcessPoolExecutor(max_workers=self.n_jobs if self.n_jobs > 0 else None) as executor:
            futures = {}

            for params in param_combinations:
                param_dict = dict(zip(param_names, params))
                future = executor.submit(self._evaluate_params, data, strategy_func, param_dict)
                futures[future] = param_dict

            for future in as_completed(futures):
                param_dict = futures[future]
                try:
                    result = future.result()
                    results.append((param_dict, result))
                except Exception as e:
                    logger.error(f"   Error with params {param_dict}: {e}")

        return results

    def _sequential_optimize(self, data, strategy_func, param_names, param_combinations):
        """Run optimization sequentially"""
        results = []

        for params in param_combinations:
            param_dict = dict(zip(param_names, params))
            try:
                result = self._evaluate_params(data, strategy_func, param_dict)
                results.append((param_dict, result))
            except Exception as e:
                logger.error(f"   Error with params {param_dict}: {e}")

        return results

    def _evaluate_params(self, data, strategy_func, params):
        """Evaluate single parameter combination"""
        signals = strategy_func(data, **params)
        results = self.run(data, signals, strategy_name=f"Optimization")
        return results


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Initialize compute
    from backend.config.compute_config import initialize_compute
    initialize_compute(mode='hybrid')

    # Generate sample data
    np.random.seed(42)
    n_bars = 10000

    dates = pd.date_range('2020-01-01', periods=n_bars, freq='1h')
    prices = 50000 + np.cumsum(np.random.randn(n_bars) * 100)

    data = pd.DataFrame({
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(100, 1000, n_bars),
    }, index=dates)

    # Simple MA crossover strategy
    data['ma_fast'] = data['close'].rolling(20).mean()
    data['ma_slow'] = data['close'].rolling(50).mean()

    signals = pd.Series(0, index=data.index)
    signals[data['ma_fast'] > data['ma_slow']] = 1
    signals[data['ma_fast'] < data['ma_slow']] = -1

    # Run backtest
    config = BacktestConfig(
        initial_capital=100000.0,
        commission=0.001,
        stop_loss=0.02,  # 2% stop loss
        take_profit=0.05,  # 5% take profit
    )

    engine = BacktestEngine(config)
    results = engine.run(data, signals, strategy_name="MA Crossover")

    print(f"\n✅ Backtest completed in {results.execution_time_seconds:.2f}s")
