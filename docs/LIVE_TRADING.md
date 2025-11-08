# Live Trading System

Real-time trading engine with aggr.trade WebSocket integration and trained ML models.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LIVE TRADING ENGINE                       │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ aggr.trade   │───▶│  Feature     │───▶│   Signal     │  │
│  │  WebSocket   │    │  Calculator  │    │  Generator   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                    │          │
│                                                    ▼          │
│                                           ┌──────────────┐  │
│                                           │  Position    │  │
│                                           │  Manager     │  │
│                                           └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. LiveTrader (`backend/trading/live_trader.py`)
Main trading engine that orchestrates all components:
- Connects to aggr.trade WebSocket
- Manages data flow
- Coordinates signal generation and execution
- Handles lifecycle (start/stop)

### 2. RealtimeFeatureCalculator (`backend/trading/realtime_features.py`)
Calculates same features as training data in real-time:
- Maintains rolling window of OHLCV data
- Technical indicators (RSI, MACD, Bollinger Bands, MAs)
- CVD from aggr.trade tick data
- Volatility metrics

**Important:** Features must match training data exactly!

### 3. SignalGenerator (`backend/trading/signal_generator.py`)
Loads trained models and generates trading signals:
- Supports XGBoost, LSTM, PPO, Ensemble
- Returns direction (long/short/neutral) and confidence
- Provides probability scores

### 4. PositionManager (`backend/trading/position_manager.py`)
Manages positions, risk, and order execution:
- Paper trading mode (simulated)
- Real trading mode (TODO: Binance API)
- Stop loss / Take profit management
- Risk controls (max positions, position sizing)
- Performance tracking

## Setup

### Prerequisites

1. **aggr-server running** (D:\aggr-server):
   ```bash
   cd D:\aggr-server
   npm start
   # Should be accessible at ws://localhost:3000
   ```

2. **Trained model** (see `backend/cli.py train`):
   ```bash
   python -m backend.cli train --symbol BTCUSDT --timeframe 5m --market futures
   ```

3. **Historical data** for warmup:
   ```bash
   python scripts/download_all.py
   ```

## Usage

### Quick Test (Paper Trading)

```bash
python scripts/test_live_trading.py
```

This will:
1. Find the latest XGBoost model for BTCUSDT 5m
2. Connect to aggr-server (ws://localhost:3000)
3. Load 500 historical candles for feature warmup
4. Start live trading in paper mode
5. Generate signals when confidence > 60%
6. Execute simulated trades with $100 position size

### Custom Configuration

```python
from backend.trading import LiveTrader

trader = LiveTrader(
    symbol='BTCUSDT',
    timeframe='5m',
    model_path='data/models/BTCUSDT_5m_futures_xgb_latest.json',
    aggr_url='ws://localhost:3000',
    paper_trading=True,
    config={
        'risk_per_trade': 0.01,       # 1% risk per trade
        'max_positions': 1,            # Max concurrent positions
        'position_size_usd': 100,      # Position size in USD
        'stop_loss_pct': 0.02,         # 2% stop loss
        'take_profit_pct': 0.04,       # 4% take profit
        'min_confidence': 0.6,         # Min confidence to trade (60%)
    }
)

# Initialize and start
await trader.initialize()
await trader.start()
```

## aggr.trade Integration

### Local Server Setup

The system expects aggr-server running locally on `ws://localhost:3000`.

**Start aggr-server:**
```bash
cd D:\aggr-server
npm start
```

**Default port:** 3000 (configurable in aggr-server/config)

### Data Flow

1. **aggr.trade sends trades:**
   ```json
   {
     "type": "trade",
     "exchange": "BINANCE",
     "symbol": "BTCUSDT",
     "price": 67234.5,
     "size": 0.5,
     "side": "buy",
     "timestamp": 1698765432000
   }
   ```

2. **LiveTrader processes:**
   - Updates current OHLCV candle
   - Updates real-time CVD
   - Logs large trades (>$100k)

3. **On candle close:**
   - Adds candle to feature buffer
   - Calculates all features
   - Generates signal from model
   - Executes trade if confidence met

### Liquidation Tracking

aggr.trade also sends liquidations:
```json
{
  "type": "liquidation",
  "exchange": "BINANCE",
  "symbol": "BTCUSDT",
  "price": 67234.5,
  "size": 10.0,
  "side": "long",
  "timestamp": 1698765432000
}
```

Large liquidations (>$500k) trigger warnings.

## Feature Consistency

**Critical:** Real-time features MUST match training features exactly!

### Training Features
From `backend/data/advanced_collector.py`:
- OHLCV (open, high, low, close, volume)
- RSI (14, 21)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2)
- SMA (20, 50, 200)
- EMA (9, 21, 50)
- CVD (cumulative volume delta)
- Volatility (5, 20 period)
- Volume features (sma_20, ratio, momentum)
- ATR (14)

### Real-time Features
From `RealtimeFeatureCalculator`:
- Same calculations as training
- Uses OHLC proxy for CVD (consistent with training data)
- Maintains 500-candle rolling window for SMA_200

### Verification

Before live trading, verify feature consistency:
```python
# Training features
train_df = pd.read_parquet('data/advanced/BTCUSDT_5m_futures_binance.parquet')
print(train_df.columns.tolist())

# Live features
features = feature_calculator.get_latest_features()
print(features.keys())

# Should match!
```

## Paper Trading vs Real Trading

### Paper Trading (Default: True)
- Simulated trades
- No real money
- Perfect for testing
- Tracks P&L, win rate, etc.
- Starting balance: $10,000

### Real Trading (paper_trading=False)
- **TODO:** Binance API integration required
- Uses real Binance account
- Real money at risk
- Requires API keys

## Risk Management

### Position Sizing
- Default: $100 per trade
- Configurable via `position_size_usd`

### Stop Loss
- Default: 2% from entry
- Long: SL below entry
- Short: SL above entry

### Take Profit
- Default: 4% from entry
- 2:1 risk/reward ratio

### Max Positions
- Default: 1 concurrent position
- Prevents over-exposure

### Min Confidence
- Default: 60%
- Only trade when model is confident

## Monitoring

### Console Output

```
================================================================================
🚀 STARTING LIVE TRADING
================================================================================
   Symbol: BTCUSDT
   Timeframe: 5m
   Paper trading: True
================================================================================

✅ Candle closed: 2025-11-07 22:35:00 | Close: 67234.50
📡 Signal: long | Confidence: 72%

============================================================
🎯 POSITION OPENED
============================================================
   ID: BTCUSDT_20251107_223500
   Side: LONG
   Entry: $67,234.50
   Size: 0.0015 (100.00 USD)
   Stop Loss: $65,889.81 (-2.0%)
   Take Profit: $69,923.88 (+4.0%)
   Confidence: 72.0%
============================================================

✅ POSITION CLOSED
============================================================
   ID: BTCUSDT_20251107_223500
   Side: LONG
   Entry: $67,234.50
   Exit: $69,980.23
   PnL: $4.12 (+4.08%)
   Reason: take_profit
   Duration: 1200s
   Balance: $10,004.12
============================================================
```

### Trading Statistics

```
============================================================
📊 TRADING STATISTICS
============================================================
   Total trades: 10
   Winning: 6 | Losing: 4
   Win rate: 60.0%
   Total PnL: $45.23
   Balance: $10,045.23
   Open positions: 0
============================================================
```

## Troubleshooting

### aggr-server connection failed
```
❌ aggr.trade WebSocket closed: Connection refused
```

**Solution:**
1. Check aggr-server is running: `http://localhost:3000`
2. Verify port (default: 3000)
3. Check firewall settings

### Model not found
```
❌ No XGBoost models found for BTCUSDT 5m
```

**Solution:**
Train a model first:
```bash
python -m backend.cli train --symbol BTCUSDT --timeframe 5m --market futures
```

### Not enough historical data
```
⚠️  Only 150 candles in buffer, need 200+ for all features
```

**Solution:**
Download more historical data:
```bash
python scripts/download_all.py
```

### Feature mismatch
```
⚠️  Missing feature: sma_200, using 0
```

**Solution:**
- Ensure feature calculator matches training data
- Check column names in parquet files
- Verify technical indicator calculations

## Next Steps

1. **Test in paper mode** - Run for several days, monitor performance
2. **Tune parameters** - Adjust stop loss, take profit, min confidence
3. **Multi-symbol** - Run multiple traders for different pairs
4. **Model updates** - Retrain models periodically with new data
5. **Real trading** - Implement Binance API integration (when ready)

## Safety Notes

⚠️ **Important:**
- Always start with paper trading
- Test thoroughly before using real money
- Monitor positions actively
- Use appropriate position sizing
- Don't risk more than you can afford to lose
- Past performance != future results

## Support

For issues or questions:
- Check logs in console output
- Review position history
- Verify aggr-server connectivity
- Test with known-good models
