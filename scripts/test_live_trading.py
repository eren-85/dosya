"""
Test Live Trading
Quick test script for live trading engine with aggr.trade
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.trading import LiveTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main test function"""

    print("\n" + "="*80)
    print("🧪 LIVE TRADING TEST")
    print("="*80)
    print()
    print("Configuration:")
    print("  Symbol: BTCUSDT")
    print("  Timeframe: 5m")
    print("  aggr server: ws://localhost:3000 (D:\\aggr-server)")
    print("  Paper trading: YES (no real money)")
    print()
    print("Prerequisites:")
    print("  ✅ aggr-server running on D:\\aggr-server")
    print("  ✅ Model trained (will use latest XGBoost model)")
    print()
    print("="*80)
    print()

    # Find latest model
    models_dir = Path("data/models")
    if not models_dir.exists():
        print("❌ No models directory found. Train a model first:")
        print("   python -m backend.cli train --symbol BTCUSDT --timeframe 5m --market futures")
        return

    # Look for XGBoost models
    xgb_models = list(models_dir.glob("*BTCUSDT*5m*xgb*.json"))
    if not xgb_models:
        print("❌ No XGBoost models found for BTCUSDT 5m. Train one first:")
        print("   python -m backend.cli train --symbol BTCUSDT --timeframe 5m --market futures")
        return

    # Use latest model
    latest_model = sorted(xgb_models, key=lambda p: p.stat().st_mtime)[-1]
    print(f"📊 Using model: {latest_model.name}")
    print()

    # Create trader
    trader = LiveTrader(
        symbol='BTCUSDT',
        timeframe='5m',
        model_path=str(latest_model),
        aggr_url='ws://localhost:3000',  # Local aggr-server
        paper_trading=True,
        config={
            'risk_per_trade': 0.01,      # 1% risk
            'max_positions': 1,           # 1 position at a time
            'position_size_usd': 100,     # $100 per trade
            'stop_loss_pct': 0.02,        # 2% stop loss
            'take_profit_pct': 0.04,      # 4% take profit
            'min_confidence': 0.6,        # 60% minimum confidence
        }
    )

    try:
        # Initialize
        print("🚀 Initializing live trader...")
        await trader.initialize()
        print()

        # Start trading
        print("✅ Initialization complete!")
        print()
        print("="*80)
        print("🎯 STARTING LIVE TRADING (Paper Mode)")
        print("="*80)
        print()
        print("Press Ctrl+C to stop")
        print()

        await trader.start()

    except KeyboardInterrupt:
        print("\n")
        print("="*80)
        print("⚠️  KEYBOARD INTERRUPT - STOPPING TRADER")
        print("="*80)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        print("\n🛑 Stopping trader...")
        await trader.stop()

        # Print final stats
        if trader.position_manager:
            trader.position_manager.print_stats()

        print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
