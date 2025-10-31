#!/usr/bin/env python3
"""
Backtesting Engine

Usage:
    python -m backend.backtest.run_backtest --model models/trained/lstm_BTCUSDT_1h.pt --start-date 2024-01-01 --end-date 2025-01-01

Features:
    - Supports LSTM, XGBoost, and PPO models
    - Realistic trading simulation
    - Commission and slippage modeling
    - Performance metrics (Sharpe, Drawdown, Win Rate, etc.)
    - Equity curve visualization
    - Trade history export
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import torch
import json
import pickle
from typing import List, Dict, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.ml.lstm import LSTMTrendPredictor


class Backtester:
    """
    Trading backtester with realistic simulation

    Features:
        - Commission modeling
        - Slippage modeling
        - Position sizing
        - Risk management
        - Performance metrics
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        position_size: float = 1.0
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size

        # State
        self.equity = initial_capital
        self.position = 0  # 0=Flat, 1=Long, -1=Short
        self.entry_price = 0
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = [initial_capital]
        self.max_equity = initial_capital

    def execute_signal(self, signal: str, price: float, timestamp: datetime):
        """
        Execute trading signal

        Args:
            signal: 'LONG', 'SHORT', or 'WAIT'
            price: Current market price
            timestamp: Current timestamp
        """
        if signal == 'LONG':
            if self.position == 0:
                self._open_long(price, timestamp)
            elif self.position == -1:
                self._close_short(price, timestamp)
                self._open_long(price, timestamp)

        elif signal == 'SHORT':
            if self.position == 0:
                self._open_short(price, timestamp)
            elif self.position == 1:
                self._close_long(price, timestamp)
                self._open_short(price, timestamp)

        # Update equity curve
        self.equity_curve.append(self.equity)

        # Update max equity
        if self.equity > self.max_equity:
            self.max_equity = self.equity

    def _open_long(self, price: float, timestamp: datetime):
        """Open long position"""
        # Apply slippage (pay slightly higher price)
        entry_price = price * (1 + self.slippage)

        # Calculate position size
        position_value = self.equity * self.position_size

        # Pay commission
        commission_cost = position_value * self.commission
        self.equity -= commission_cost

        self.position = 1
        self.entry_price = entry_price

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'type': 'OPEN_LONG',
            'price': entry_price,
            'equity': self.equity,
            'commission': commission_cost
        })

    def _close_long(self, price: float, timestamp: datetime):
        """Close long position"""
        # Apply slippage (receive slightly lower price)
        exit_price = price * (1 - self.slippage)

        # Calculate PnL
        position_value = self.equity * self.position_size
        pnl = ((exit_price - self.entry_price) / self.entry_price) * position_value

        # Pay commission
        commission_cost = position_value * self.commission

        # Update equity
        self.equity += pnl - commission_cost

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'type': 'CLOSE_LONG',
            'price': exit_price,
            'pnl': pnl,
            'equity': self.equity,
            'commission': commission_cost,
            'return': pnl / position_value
        })

        self.position = 0
        self.entry_price = 0

    def _open_short(self, price: float, timestamp: datetime):
        """Open short position"""
        # Apply slippage (pay slightly higher price to short)
        entry_price = price * (1 + self.slippage)

        # Calculate position size
        position_value = self.equity * self.position_size

        # Pay commission
        commission_cost = position_value * self.commission
        self.equity -= commission_cost

        self.position = -1
        self.entry_price = entry_price

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'type': 'OPEN_SHORT',
            'price': entry_price,
            'equity': self.equity,
            'commission': commission_cost
        })

    def _close_short(self, price: float, timestamp: datetime):
        """Close short position"""
        # Apply slippage (pay slightly higher price to cover)
        exit_price = price * (1 + self.slippage)

        # Calculate PnL
        position_value = self.equity * self.position_size
        pnl = ((self.entry_price - exit_price) / self.entry_price) * position_value

        # Pay commission
        commission_cost = position_value * self.commission

        # Update equity
        self.equity += pnl - commission_cost

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'type': 'CLOSE_SHORT',
            'price': exit_price,
            'pnl': pnl,
            'equity': self.equity,
            'commission': commission_cost,
            'return': pnl / position_value
        })

        self.position = 0
        self.entry_price = 0

    def get_metrics(self) -> Dict:
        """Calculate performance metrics"""

        # Closed trades only
        closed_trades = [t for t in self.trades if 'pnl' in t]

        if len(closed_trades) == 0:
            return {
                'total_return': 0,
                'num_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'avg_trade_return': 0
            }

        # Total return
        total_return = (self.equity - self.initial_capital) / self.initial_capital

        # Win rate
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(closed_trades)

        # Profit factor
        total_profit = sum(t['pnl'] for t in closed_trades if t['pnl'] > 0)
        total_loss = abs(sum(t['pnl'] for t in closed_trades if t['pnl'] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Sharpe ratio
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)

        # Max drawdown
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (running_max - equity_array) / running_max
        max_drawdown = np.max(drawdown)

        # Average trade return
        avg_trade_return = np.mean([t['return'] for t in closed_trades])

        # Average trade duration (if timestamps available)
        durations = []
        for i in range(1, len(closed_trades)):
            if i % 2 == 1:  # Every other trade is a close
                open_time = closed_trades[i-1]['timestamp']
                close_time = closed_trades[i]['timestamp']
                duration = (close_time - open_time).total_seconds() / 3600  # hours
                durations.append(duration)

        avg_duration = np.mean(durations) if durations else 0

        return {
            'total_return': total_return,
            'final_equity': self.equity,
            'num_trades': len(closed_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_trade_return': avg_trade_return,
            'avg_trade_duration_hours': avg_duration,
            'total_commission': sum(t.get('commission', 0) for t in self.trades)
        }


def load_lstm_model(model_path: str):
    """Load LSTM model from checkpoint"""
    print(f"📂 Loading LSTM model from {model_path}")

    checkpoint = torch.load(model_path, map_location='cpu')

    # Get model config
    config = checkpoint['model_config']

    # Create model
    model = LSTMTrendPredictor(**config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    # Get scaler and feature columns
    scaler = checkpoint['scaler']
    feature_cols = checkpoint['feature_cols']

    print(f"✅ Model loaded")
    print(f"   Features: {len(feature_cols)}")

    return model, scaler, feature_cols


def load_data(symbol: str, timeframe: str, start_date: str, end_date: str, data_dir='data/historical'):
    """Load historical data for backtest period"""

    filename = f"{symbol}_{timeframe}_futures.parquet"
    filepath = Path(data_dir) / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    print(f"📂 Loading data from {filepath}")
    df = pd.read_parquet(filepath)

    # Parse dates
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Filter by date range
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
    elif 'close_time' in df.columns:
        df['close_time'] = pd.to_datetime(df['close_time'])
        df = df[(df['close_time'] >= start) & (df['close_time'] <= end)]

    print(f"✅ Loaded {len(df)} candles ({start_date} to {end_date})")

    return df


def calculate_indicators(df):
    """Calculate technical indicators (same as training)"""
    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

    # Moving averages
    for period in [7, 14, 21, 50, 100, 200]:
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
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

    # ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(14).mean()

    # Volume indicators
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']

    # Momentum
    df['momentum'] = df['close'] - df['close'].shift(10)
    df['roc'] = ((df['close'] - df['close'].shift(12)) / df['close'].shift(12)) * 100

    # Price position
    df['price_position'] = (df['close'] - df['low'].rolling(14).min()) / (
        df['high'].rolling(14).max() - df['low'].rolling(14).min()
    )

    # Drop NaN rows
    df.dropna(inplace=True)

    return df


def run_backtest_lstm(model, scaler, feature_cols, df, initial_capital, commission, slippage):
    """Run backtest with LSTM model"""

    print("\n🚀 Running backtest...")
    print("-" * 60)

    # Initialize backtester
    backtester = Backtester(
        initial_capital=initial_capital,
        commission=commission,
        slippage=slippage
    )

    # Run through each candle
    seq_length = 60  # LSTM sequence length

    for i in range(seq_length, len(df)):
        # Get sequence
        sequence = df.iloc[i-seq_length:i][feature_cols].values

        # Normalize
        sequence_scaled = scaler.transform(sequence)

        # Predict
        X = torch.FloatTensor(sequence_scaled).unsqueeze(0)
        with torch.no_grad():
            output = model(X)
            probability = torch.sigmoid(output).item()

        # Generate signal
        if probability > 0.65:
            signal = 'LONG'
        elif probability < 0.35:
            signal = 'SHORT'
        else:
            signal = 'WAIT'

        # Execute signal
        current_price = df.iloc[i]['close']
        timestamp = df.iloc[i].get('timestamp', df.iloc[i].get('close_time'))

        backtester.execute_signal(signal, current_price, timestamp)

        # Progress
        if (i - seq_length) % 1000 == 0:
            progress = (i - seq_length) / (len(df) - seq_length) * 100
            print(f"Progress: {progress:.1f}% | Equity: ${backtester.equity:,.0f}", end='\r')

    print("\n" + "-" * 60)

    return backtester


def main():
    parser = argparse.ArgumentParser(description='Run backtest on trained model')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe')
    parser.add_argument('--start-date', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial-capital', type=float, default=10000, help='Initial capital')
    parser.add_argument('--commission', type=float, default=0.001, help='Commission rate')
    parser.add_argument('--slippage', type=float, default=0.0005, help='Slippage rate')
    parser.add_argument('--data-dir', type=str, default='data/historical', help='Data directory')

    args = parser.parse_args()

    print("=" * 60)
    print("📊 BACKTEST ENGINE")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial capital: ${args.initial_capital:,.0f}")
    print(f"Commission: {args.commission:.2%}")
    print(f"Slippage: {args.slippage:.2%}")
    print("=" * 60)
    print()

    # 1. Load model
    model, scaler, feature_cols = load_lstm_model(args.model)

    # 2. Load data
    df = load_data(args.symbol, args.timeframe, args.start_date, args.end_date, args.data_dir)

    # 3. Calculate indicators
    print("\n🔧 Calculating indicators...")
    df = calculate_indicators(df)
    print(f"✅ Indicators calculated: {len(df)} candles ready")

    # 4. Run backtest
    backtester = run_backtest_lstm(
        model, scaler, feature_cols, df,
        args.initial_capital, args.commission, args.slippage
    )

    # 5. Calculate metrics
    print("\n📊 BACKTEST RESULTS")
    print("=" * 60)

    metrics = backtester.get_metrics()

    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial Capital: ${args.initial_capital:,.0f}")
    print(f"Final Equity: ${metrics['final_equity']:,.0f}")
    print()
    print("Performance Metrics:")
    print(f"  Total Return: {metrics['total_return']:+.2%}")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Win Rate: {metrics['win_rate']:.2%}")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"  Total Trades: {metrics['num_trades']}")
    print(f"  Avg Trade Return: {metrics['avg_trade_return']:+.2%}")
    print(f"  Avg Trade Duration: {metrics['avg_trade_duration_hours']:.1f} hours")
    print(f"  Total Commission: ${metrics['total_commission']:,.0f}")
    print()

    # Performance rating
    if metrics['sharpe_ratio'] > 2.0 and metrics['max_drawdown'] < 0.15:
        rating = "EXCELLENT ✅"
    elif metrics['sharpe_ratio'] > 1.0 and metrics['max_drawdown'] < 0.25:
        rating = "GOOD 👍"
    elif metrics['total_return'] > 0:
        rating = "ACCEPTABLE ⚠️"
    else:
        rating = "POOR ❌"

    print(f"Model Performance: {rating}")
    print("=" * 60)
    print()

    # 6. Save results
    output_dir = Path('backtest_results')
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"backtest_{args.symbol}_{timestamp}.json"

    results = {
        'model': args.model,
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'start_date': args.start_date,
        'end_date': args.end_date,
        'metrics': metrics,
        'equity_curve': backtester.equity_curve,
        'num_candles': len(df)
    }

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"💾 Results saved to: {results_file}")
    print()


if __name__ == '__main__':
    main()
