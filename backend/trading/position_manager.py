"""
Position Manager
Manages trading positions, risk, and order execution
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Trading position"""
    id: str
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    size: float  # Position size (contracts/coins)
    entry_time: datetime
    stop_loss: float
    take_profit: float
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = 'open'  # 'open', 'closed'
    exit_price: float = None
    exit_time: datetime = None
    exit_reason: str = None  # 'stop_loss', 'take_profit', 'signal', 'manual'

    def update_pnl(self, current_price: float):
        """Update PnL based on current price"""
        self.current_price = current_price

        if self.side == 'long':
            self.pnl = (current_price - self.entry_price) * self.size
            self.pnl_pct = (current_price - self.entry_price) / self.entry_price
        else:  # short
            self.pnl = (self.entry_price - current_price) * self.size
            self.pnl_pct = (self.entry_price - current_price) / self.entry_price

    def should_stop_loss(self) -> bool:
        """Check if stop loss hit"""
        if self.side == 'long':
            return self.current_price <= self.stop_loss
        else:  # short
            return self.current_price >= self.stop_loss

    def should_take_profit(self) -> bool:
        """Check if take profit hit"""
        if self.side == 'long':
            return self.current_price >= self.take_profit
        else:  # short
            return self.current_price <= self.take_profit


class PositionManager:
    """
    Manages positions, risk, and order execution
    Supports both paper trading and live trading
    """

    def __init__(self, symbol: str, paper_trading: bool = True, config: Dict = None):
        """
        Args:
            symbol: Trading pair
            paper_trading: If True, simulate trades (no real orders)
            config: Trading configuration
        """
        self.symbol = symbol
        self.paper_trading = paper_trading
        self.config = config or {}

        # Positions
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []

        # Trading state
        self.balance_usd = 10000.0  # Starting paper trading balance
        self.current_price = 0.0

        # Metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0

        logger.info(f"💼 PositionManager initialized")
        logger.info(f"   Symbol: {symbol}")
        logger.info(f"   Paper trading: {paper_trading}")
        logger.info(f"   Starting balance: ${self.balance_usd:,.2f}")

    async def execute_signal(self, signal: Dict) -> Optional[Position]:
        """
        Execute trading signal

        Args:
            signal: Signal from SignalGenerator
                   {direction: 'long'|'short', confidence: 0.0-1.0, ...}

        Returns:
            New position if opened, None otherwise
        """
        direction = signal['direction']

        if direction == 'neutral':
            return None

        # Check if we already have a position
        if len(self.positions) >= self.config.get('max_positions', 1):
            logger.info("   ⏭️  Max positions reached, skipping")
            return None

        # Calculate position size
        position_size_usd = self.config.get('position_size_usd', 100)
        stop_loss_pct = self.config.get('stop_loss_pct', 0.02)
        take_profit_pct = self.config.get('take_profit_pct', 0.04)

        # Get current price (from last update)
        entry_price = self.current_price

        if entry_price == 0:
            logger.warning("⚠️  No current price, cannot open position")
            return None

        # Calculate position size in contracts/coins
        size = position_size_usd / entry_price

        # Calculate stop loss and take profit
        if direction == 'long':
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + take_profit_pct)
        else:  # short
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - take_profit_pct)

        # Create position
        position = Position(
            id=f"{self.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            symbol=self.symbol,
            side=direction,
            entry_price=entry_price,
            size=size,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        # Execute trade
        if self.paper_trading:
            success = await self._execute_paper_trade(position)
        else:
            success = await self._execute_real_trade(position)

        if success:
            self.positions.append(position)
            self.total_trades += 1

            logger.info("="*60)
            logger.info(f"🎯 POSITION OPENED")
            logger.info(f"   ID: {position.id}")
            logger.info(f"   Side: {position.side.upper()}")
            logger.info(f"   Entry: ${position.entry_price:,.2f}")
            logger.info(f"   Size: {position.size:.4f} ({position_size_usd:.2f} USD)")
            logger.info(f"   Stop Loss: ${position.stop_loss:,.2f} (-{stop_loss_pct:.1%})")
            logger.info(f"   Take Profit: ${position.take_profit:,.2f} (+{take_profit_pct:.1%})")
            logger.info(f"   Confidence: {signal['confidence']:.1%}")
            logger.info("="*60)

            return position
        else:
            logger.error(f"❌ Failed to open position")
            return None

    async def _execute_paper_trade(self, position: Position) -> bool:
        """Execute paper trade (simulated)"""
        # Paper trading always succeeds
        logger.info("   📄 Paper trade executed")
        return True

    async def _execute_real_trade(self, position: Position) -> bool:
        """Execute real trade via exchange API"""
        # TODO: Implement Binance API integration
        logger.warning("   ⚠️  Real trading not implemented yet")
        return False

    async def update_positions(self):
        """Update all open positions (check SL/TP)"""
        if not self.positions:
            return

        for position in self.positions[:]:  # Copy list to allow modification
            # Update PnL
            position.update_pnl(self.current_price)

            # Check stop loss
            if position.should_stop_loss():
                await self.close_position(position, reason='stop_loss')
                continue

            # Check take profit
            if position.should_take_profit():
                await self.close_position(position, reason='take_profit')
                continue

    async def close_position(self, position: Position, reason: str = 'manual'):
        """
        Close a position

        Args:
            position: Position to close
            reason: 'stop_loss', 'take_profit', 'signal', 'manual'
        """
        position.status = 'closed'
        position.exit_price = self.current_price
        position.exit_time = datetime.now()
        position.exit_reason = reason

        # Final PnL calculation
        position.update_pnl(self.current_price)

        # Update metrics
        self.total_pnl += position.pnl
        if position.pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Update balance (paper trading)
        if self.paper_trading:
            self.balance_usd += position.pnl

        # Move to closed positions
        self.positions.remove(position)
        self.closed_positions.append(position)

        # Log
        emoji = "✅" if position.pnl > 0 else "❌"
        logger.info("="*60)
        logger.info(f"{emoji} POSITION CLOSED")
        logger.info(f"   ID: {position.id}")
        logger.info(f"   Side: {position.side.upper()}")
        logger.info(f"   Entry: ${position.entry_price:,.2f}")
        logger.info(f"   Exit: ${position.exit_price:,.2f}")
        logger.info(f"   PnL: ${position.pnl:,.2f} ({position.pnl_pct:+.2%})")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Duration: {(position.exit_time - position.entry_time).total_seconds():.0f}s")
        if self.paper_trading:
            logger.info(f"   Balance: ${self.balance_usd:,.2f}")
        logger.info("="*60)

    async def close_all_positions(self):
        """Close all open positions"""
        for position in self.positions[:]:
            await self.close_position(position, reason='shutdown')

    def update_current_price(self, price: float):
        """Update current market price"""
        self.current_price = price

        # Update all position PnLs
        for position in self.positions:
            position.update_pnl(price)

    def get_positions(self) -> List[Dict]:
        """Get all open positions as dicts"""
        return [
            {
                'id': p.id,
                'symbol': p.symbol,
                'side': p.side,
                'entry_price': p.entry_price,
                'current_price': p.current_price,
                'size': p.size,
                'pnl': p.pnl,
                'pnl_pct': p.pnl_pct,
                'stop_loss': p.stop_loss,
                'take_profit': p.take_profit,
                'entry_time': p.entry_time.isoformat(),
            }
            for p in self.positions
        ]

    def get_stats(self) -> Dict:
        """Get trading statistics"""
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0

        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'balance': self.balance_usd,
            'open_positions': len(self.positions),
        }

    def print_stats(self):
        """Print trading statistics"""
        stats = self.get_stats()

        logger.info("\n" + "="*60)
        logger.info("📊 TRADING STATISTICS")
        logger.info("="*60)
        logger.info(f"   Total trades: {stats['total_trades']}")
        logger.info(f"   Winning: {stats['winning_trades']} | Losing: {stats['losing_trades']}")
        logger.info(f"   Win rate: {stats['win_rate']:.1%}")
        logger.info(f"   Total PnL: ${stats['total_pnl']:,.2f}")
        logger.info(f"   Balance: ${stats['balance']:,.2f}")
        logger.info(f"   Open positions: {stats['open_positions']}")
        logger.info("="*60 + "\n")
