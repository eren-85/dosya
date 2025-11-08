"""
Live Trading Engine
Real-time trading with aggr.trade WebSocket + trained models
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.data.sources.aggr import AggrWebSocketClient
from backend.trading.realtime_features import RealtimeFeatureCalculator
from backend.trading.signal_generator import SignalGenerator
from backend.trading.position_manager import PositionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiveTrader:
    """
    Live trading engine that combines:
    - aggr.trade real-time data
    - Feature calculation
    - Model inference
    - Position management
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str = '5m',
        model_path: str = None,
        aggr_url: str = "ws://localhost:3000",  # Local aggr server
        paper_trading: bool = True,
        config: Dict = None
    ):
        """
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Trading timeframe (e.g., '5m', '1h')
            model_path: Path to trained model
            aggr_url: aggr.trade WebSocket URL (local server: ws://localhost:3000)
            paper_trading: If True, no real orders (default: True)
            config: Trading config (risk params, position size, etc.)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.model_path = model_path
        self.aggr_url = aggr_url
        self.paper_trading = paper_trading
        self.config = config or self._default_config()

        # Components
        self.aggr_client: Optional[AggrWebSocketClient] = None
        self.feature_calculator: Optional[RealtimeFeatureCalculator] = None
        self.signal_generator: Optional[SignalGenerator] = None
        self.position_manager: Optional[PositionManager] = None

        # State
        self.running = False
        self.current_candle: Dict = {}
        self.candle_start_time: int = 0

        # Metrics
        self.trade_count = 0
        self.last_signal_time = None

        logger.info(f"🤖 LiveTrader initialized: {symbol} {timeframe}")
        logger.info(f"   📊 Model: {model_path}")
        logger.info(f"   🌐 aggr server: {aggr_url}")
        logger.info(f"   💰 Paper trading: {paper_trading}")

    def _default_config(self) -> Dict:
        """Default trading configuration"""
        return {
            'risk_per_trade': 0.01,  # 1% risk per trade
            'max_positions': 1,       # Max concurrent positions
            'position_size_usd': 100, # Position size in USD
            'stop_loss_pct': 0.02,    # 2% stop loss
            'take_profit_pct': 0.04,  # 4% take profit
            'min_confidence': 0.6,    # Minimum model confidence to trade
        }

    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing live trader components...")

        # 1. Feature calculator
        self.feature_calculator = RealtimeFeatureCalculator(
            symbol=self.symbol,
            timeframe=self.timeframe,
            window_size=500
        )
        logger.info("   ✅ Feature calculator initialized")

        # 2. Signal generator (loads trained model)
        self.signal_generator = SignalGenerator(model_path=self.model_path)
        await self.signal_generator.load_model()
        logger.info("   ✅ Signal generator initialized")

        # 3. Position manager
        self.position_manager = PositionManager(
            symbol=self.symbol,
            paper_trading=self.paper_trading,
            config=self.config
        )
        logger.info("   ✅ Position manager initialized")

        # 4. aggr.trade WebSocket client
        self.aggr_client = AggrWebSocketClient(url=self.aggr_url)

        # Register callbacks
        self.aggr_client.on_trade(self._handle_aggr_trade)
        self.aggr_client.on_liquidation(self._handle_liquidation)
        self.aggr_client.on_error(self._handle_error)

        # Subscribe to symbol
        self.aggr_client.subscribe([f'BINANCE:{self.symbol}'])
        logger.info("   ✅ aggr.trade client initialized")

        # 5. Load historical data to warm up feature calculator
        await self._warmup_features()

        logger.info("✅ All components initialized successfully!")

    async def _warmup_features(self):
        """Load recent historical data to initialize feature buffer"""
        logger.info("🔥 Warming up feature calculator with historical data...")

        from backend.data.advanced_collector import AdvancedDataCollector

        # Fetch last 500 candles
        collector = AdvancedDataCollector(
            symbol=self.symbol,
            timeframe=self.timeframe,
            market='futures',
            exchanges=['binance']
        )

        # Get recent data
        df = collector.fetch_ohlcv_binance(
            start_time=int((datetime.now().timestamp() - 86400 * 5) * 1000),  # Last 5 days
            end_time=int(datetime.now().timestamp() * 1000)
        )

        # Add to feature calculator buffer
        for _, row in df.iterrows():
            candle = {
                'open_time': row['open_time'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
            }
            self.feature_calculator.add_candle(candle)

        logger.info(f"   ✅ Loaded {len(df)} historical candles")
        logger.info(f"   📊 Feature buffer size: {len(self.feature_calculator.ohlcv_buffer)}")

    async def start(self):
        """Start live trading"""
        if self.running:
            logger.warning("⚠️  Live trader already running")
            return

        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING LIVE TRADING")
        logger.info("="*80)
        logger.info(f"   Symbol: {self.symbol}")
        logger.info(f"   Timeframe: {self.timeframe}")
        logger.info(f"   Paper trading: {self.paper_trading}")
        logger.info("="*80 + "\n")

        self.running = True

        # Connect to aggr.trade
        self.aggr_client.connect()

        # Start main loop
        await self._main_loop()

    async def stop(self):
        """Stop live trading"""
        logger.info("🛑 Stopping live trader...")
        self.running = False

        # Disconnect aggr.trade
        if self.aggr_client:
            self.aggr_client.disconnect()

        # Close all positions
        if self.position_manager:
            await self.position_manager.close_all_positions()

        logger.info("✅ Live trader stopped")

    async def _main_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                # Check for signals every timeframe
                await asyncio.sleep(self._timeframe_to_seconds())

                # Generate signal
                await self._check_and_generate_signal()

                # Update positions
                if self.position_manager:
                    await self.position_manager.update_positions()

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    def _timeframe_to_seconds(self) -> int:
        """Convert timeframe to seconds"""
        tf_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
        }
        return tf_map.get(self.timeframe, 300)

    async def _check_and_generate_signal(self):
        """Check if we should generate a signal"""
        # Get latest features
        features = self.feature_calculator.get_latest_features()

        if features is None:
            logger.warning("⚠️  Not enough data for features")
            return

        # Generate signal from model
        signal = await self.signal_generator.generate_signal(features)

        if signal is None:
            return

        logger.info(f"📡 Signal: {signal['direction']} | Confidence: {signal['confidence']:.2%}")

        # Check minimum confidence
        if signal['confidence'] < self.config['min_confidence']:
            logger.info(f"   ⏭️  Skipping (confidence {signal['confidence']:.2%} < {self.config['min_confidence']:.2%})")
            return

        # Execute trade
        await self.position_manager.execute_signal(signal)

        self.last_signal_time = datetime.now()
        self.trade_count += 1

    def _handle_aggr_trade(self, trade: Dict):
        """Handle incoming trade from aggr.trade"""
        try:
            # Update real-time CVD
            self.feature_calculator.update_from_aggr_trade(trade)

            # Update current candle
            self._update_current_candle(trade)

            # Log large trades
            if trade['value_usd'] > 100000:  # >100k USD
                logger.info(f"🐋 Large {trade['side'].upper()}: ${trade['value_usd']:,.0f} @ {trade['price']}")

        except Exception as e:
            logger.error(f"Error handling trade: {e}")

    def _update_current_candle(self, trade: Dict):
        """Update current OHLCV candle from trades"""
        ts = trade['timestamp']
        price = trade['price']
        volume = trade['size']

        # Get candle start time (round down to timeframe)
        candle_seconds = self._timeframe_to_seconds()
        candle_start = (ts // (candle_seconds * 1000)) * (candle_seconds * 1000)

        # New candle?
        if candle_start != self.candle_start_time:
            # Save previous candle
            if self.current_candle and self.candle_start_time > 0:
                self.feature_calculator.add_candle(self.current_candle)
                logger.info(f"✅ Candle closed: {datetime.fromtimestamp(self.candle_start_time/1000)} | Close: {self.current_candle['close']:.2f}")

            # Start new candle
            self.candle_start_time = candle_start
            self.current_candle = {
                'open_time': candle_start,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume,
            }
        else:
            # Update current candle
            self.current_candle['high'] = max(self.current_candle['high'], price)
            self.current_candle['low'] = min(self.current_candle['low'], price)
            self.current_candle['close'] = price
            self.current_candle['volume'] += volume

    def _handle_liquidation(self, liq: Dict):
        """Handle liquidation event"""
        logger.info(f"🔥 LIQUIDATION: {liq['side'].upper()} ${liq['value_usd']:,.0f} @ {liq['price']} on {liq['exchange']}")

        # Large liquidations can be signals
        if liq['value_usd'] > 500000:  # >500k liquidation
            logger.warning(f"   ⚠️  LARGE LIQUIDATION DETECTED!")

    def _handle_error(self, error):
        """Handle WebSocket error"""
        logger.error(f"❌ aggr.trade error: {error}")

    def get_status(self) -> Dict:
        """Get current trading status"""
        return {
            'running': self.running,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'trade_count': self.trade_count,
            'last_signal': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'positions': self.position_manager.get_positions() if self.position_manager else [],
            'current_cvd': self.feature_calculator.get_current_cvd() if self.feature_calculator else 0,
        }


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize trader
        trader = LiveTrader(
            symbol='BTCUSDT',
            timeframe='5m',
            model_path='data/models/BTCUSDT_5m_futures_xgb_latest.json',
            aggr_url='ws://localhost:3000',  # D:\aggr-server
            paper_trading=True
        )

        try:
            # Initialize
            await trader.initialize()

            # Start trading
            await trader.start()

        except KeyboardInterrupt:
            logger.info("\n⚠️  Keyboard interrupt detected")
        finally:
            await trader.stop()

    # Run
    asyncio.run(main())
