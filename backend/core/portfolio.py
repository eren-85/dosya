"""
Portfolio tracking and paper trading system
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class Position:
    """Single position"""
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized PnL"""
        if self.side == 'long':
            return (self.current_price - self.entry_price) * self.quantity
        else:  # short
            return (self.entry_price - self.current_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        """PnL percentage"""
        return (self.unrealized_pnl / (self.entry_price * self.quantity)) * 100

    @property
    def value(self) -> float:
        """Current position value"""
        return self.current_price * self.quantity


class Portfolio:
    """
    Portfolio management for paper trading
    Tracks positions, capital, and performance
    """

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Dict] = []

        # Performance tracking
        self.equity_history: List[Dict] = []
        self.peak_equity = initial_capital
        self.max_drawdown = 0.0

    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Open new position

        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            quantity: Position size
            entry_price: Entry price
            stop_loss: Stop loss level
            take_profit: Take profit level

        Returns:
            Success boolean
        """

        # Check if position already exists
        if symbol in self.positions:
            print(f"⚠️  Position for {symbol} already exists")
            return False

        # Calculate cost
        cost = quantity * entry_price

        # Check capital
        if cost > self.capital:
            print(f"⚠️  Insufficient capital for {symbol} position")
            return False

        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.positions[symbol] = position
        self.capital -= cost

        print(f"✅ Opened {side.upper()} position: {quantity} {symbol} @ ${entry_price:.2f}")

        return True

    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """
        Close position

        Args:
            symbol: Symbol to close
            exit_price: Exit price

        Returns:
            Realized PnL or None if position doesn't exist
        """

        if symbol not in self.positions:
            print(f"⚠️  No position found for {symbol}")
            return None

        position = self.positions[symbol]

        # Calculate realized PnL
        if position.side == 'long':
            pnl = (exit_price - position.entry_price) * position.quantity
        else:  # short
            pnl = (position.entry_price - exit_price) * position.quantity

        pnl_pct = (pnl / (position.entry_price * position.quantity)) * 100

        # Update capital
        self.capital += (exit_price * position.quantity) + pnl

        # Store closed position
        self.closed_positions.append({
            'symbol': symbol,
            'side': position.side,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'entry_time': position.entry_time.isoformat(),
            'exit_time': datetime.now().isoformat(),
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })

        # Remove position
        del self.positions[symbol]

        print(f"✅ Closed {symbol} position: PnL ${pnl:.2f} ({pnl_pct:+.2f}%)")

        return pnl

    def update_prices(self, prices: Dict[str, float]):
        """Update current prices for all positions"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price

                # Check stop loss / take profit
                position = self.positions[symbol]

                if position.side == 'long':
                    if position.stop_loss and price <= position.stop_loss:
                        print(f"🛑 Stop loss triggered for {symbol}")
                        self.close_position(symbol, price)
                    elif position.take_profit and price >= position.take_profit:
                        print(f"🎯 Take profit triggered for {symbol}")
                        self.close_position(symbol, price)
                else:  # short
                    if position.stop_loss and price >= position.stop_loss:
                        print(f"🛑 Stop loss triggered for {symbol}")
                        self.close_position(symbol, price)
                    elif position.take_profit and price <= position.take_profit:
                        print(f"🎯 Take profit triggered for {symbol}")
                        self.close_position(symbol, price)

    def get_total_equity(self) -> float:
        """Calculate total equity (capital + positions value)"""
        positions_value = sum(pos.value for pos in self.positions.values())
        return self.capital + positions_value

    def get_total_pnl(self) -> float:
        """Total PnL (realized + unrealized)"""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        realized_pnl = sum(trade['pnl'] for trade in self.closed_positions)
        return realized_pnl + unrealized_pnl

    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        total_equity = self.get_total_equity()
        total_pnl = self.get_total_pnl()
        total_return_pct = (total_pnl / self.initial_capital) * 100

        # Win rate
        winning_trades = [t for t in self.closed_positions if t['pnl'] > 0]
        win_rate = (len(winning_trades) / len(self.closed_positions) * 100) if self.closed_positions else 0

        # Update drawdown
        if total_equity > self.peak_equity:
            self.peak_equity = total_equity

        current_drawdown = (self.peak_equity - total_equity) / self.peak_equity
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown

        return {
            'total_equity': total_equity,
            'capital': self.capital,
            'positions_value': sum(pos.value for pos in self.positions.values()),
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values()),
            'realized_pnl': sum(t['pnl'] for t in self.closed_positions),
            'num_positions': len(self.positions),
            'num_trades': len(self.closed_positions),
            'win_rate': win_rate,
            'max_drawdown_pct': self.max_drawdown * 100
        }

    def get_open_positions(self) -> List[Dict]:
        """Get list of open positions"""
        return [
            {
                **asdict(pos),
                'entry_time': pos.entry_time.isoformat(),
                'unrealized_pnl': pos.unrealized_pnl,
                'unrealized_pnl_pct': pos.unrealized_pnl_pct
            }
            for pos in self.positions.values()
        ]

    def record_equity(self):
        """Record current equity for tracking"""
        self.equity_history.append({
            'timestamp': datetime.now().isoformat(),
            'equity': self.get_total_equity(),
            'capital': self.capital,
            'positions_value': sum(pos.value for pos in self.positions.values())
        })

    def save_state(self, filepath: str):
        """Save portfolio state to file"""
        state = {
            'initial_capital': self.initial_capital,
            'capital': self.capital,
            'positions': self.get_open_positions(),
            'closed_positions': self.closed_positions,
            'equity_history': self.equity_history,
            'performance': self.get_performance_metrics()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"✅ Portfolio saved to {filepath}")

    def load_state(self, filepath: str):
        """Load portfolio state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)

        self.initial_capital = state['initial_capital']
        self.capital = state['capital']
        self.closed_positions = state['closed_positions']
        self.equity_history = state['equity_history']

        # Reconstruct positions
        for pos_dict in state['positions']:
            pos = Position(
                symbol=pos_dict['symbol'],
                side=pos_dict['side'],
                quantity=pos_dict['quantity'],
                entry_price=pos_dict['entry_price'],
                current_price=pos_dict['current_price'],
                entry_time=datetime.fromisoformat(pos_dict['entry_time']),
                stop_loss=pos_dict.get('stop_loss'),
                take_profit=pos_dict.get('take_profit')
            )
            self.positions[pos.symbol] = pos

        print(f"✅ Portfolio loaded from {filepath}")
