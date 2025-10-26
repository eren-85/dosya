"""
Backtest engine for strategy testing
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class Order:
    symbol: str
    side: str  # 'buy' / 'sell'
    quantity: float
    price: float
    timestamp: datetime
    order_type: str = 'market'


@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float


class BacktestEngine:
    """
    Event-driven backtest engine with realistic simulation
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.0004,
        slippage_pct: float = 0.0001
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_pct = slippage_pct

        self.positions: Dict[str, Position] = {}
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []

        self.current_time: Optional[datetime] = None

    def execute_order(self, order: Order) -> bool:
        """Execute order with commission and slippage"""

        # Apply slippage
        if order.side == 'buy':
            execution_price = order.price * (1 + self.slippage_pct)
        else:
            execution_price = order.price * (1 - self.slippage_pct)

        # Calculate commission
        commission = order.quantity * execution_price * self.commission_rate
        total_cost = (order.quantity * execution_price) + commission

        # Check capital
        if order.side == 'buy' and total_cost > self.capital:
            return False

        # Update position
        if order.side == 'buy':
            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                new_qty = pos.quantity + order.quantity
                new_entry = (pos.entry_price * pos.quantity + execution_price * order.quantity) / new_qty
                pos.quantity = new_qty
                pos.entry_price = new_entry
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    entry_price=execution_price,
                    current_price=execution_price,
                    unrealized_pnl=0
                )

            self.capital -= total_cost

        else:  # sell
            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                sell_qty = min(order.quantity, pos.quantity)

                realized_pnl = (execution_price - pos.entry_price) * sell_qty - commission
                self.capital += sell_qty * execution_price - commission

                pos.quantity -= sell_qty
                if pos.quantity <= 0:
                    del self.positions[order.symbol]

                self.trades.append({
                    'timestamp': self.current_time,
                    'symbol': order.symbol,
                    'side': 'sell',
                    'quantity': sell_qty,
                    'price': execution_price,
                    'pnl': realized_pnl
                })

        return True

    def get_equity(self) -> float:
        """Calculate total equity"""
        positions_value = sum(pos.quantity * pos.current_price for pos in self.positions.values())
        return self.capital + positions_value

    def get_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not self.equity_curve:
            return {}

        equity_df = pd.DataFrame(self.equity_curve)
        returns = equity_df['equity'].pct_change().dropna()

        total_return = (equity_df['equity'].iloc[-1] / self.initial_capital - 1) * 100

        if len(returns) > 0 and returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24 * 60)  # Annualized
        else:
            sharpe = 0

        max_dd = self._calculate_max_drawdown(equity_df['equity'])

        win_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        win_rate = len(win_trades) / len(self.trades) if self.trades else 0

        return {
            'total_return_pct': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd,
            'win_rate': win_rate * 100,
            'total_trades': len(self.trades),
            'final_equity': equity_df['equity'].iloc[-1]
        }

    def _calculate_max_drawdown(self, equity_series: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        return drawdown.min()
