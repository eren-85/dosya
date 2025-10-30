# backend/api/routes/data.py
"""
Data API endpoints for charts and market data
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/data", tags=["data"])


def generate_mock_ohlcv(
    symbol: str,
    timeframe: str,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """
    Generate mock OHLCV data for testing UI
    TODO: Replace with real data from database/files
    """
    # Base price for different symbols
    base_prices = {
        "BTCUSDT": 67000,
        "ETHUSDT": 3500,
        "BNBUSDT": 600,
        "SOLUSDT": 180,
    }

    base_price = base_prices.get(symbol, 1000)

    # Generate candles
    candles = []
    now = datetime.now()

    # Timeframe in minutes
    tf_minutes = {
        "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
        "1h": 60, "1H": 60, "2h": 120, "4h": 240, "4H": 240,
        "6h": 360, "12h": 720, "1d": 1440, "1D": 1440,
        "3d": 4320, "1w": 10080, "1W": 10080
    }

    minutes = tf_minutes.get(timeframe, 60)

    # Generate backwards from now
    current_price = base_price

    for i in range(limit - 1, -1, -1):
        timestamp = now - timedelta(minutes=minutes * i)

        # Random price movement
        change_pct = random.uniform(-0.02, 0.02)  # ±2%
        current_price = current_price * (1 + change_pct)

        # OHLC with realistic patterns
        open_price = current_price
        high_price = open_price * random.uniform(1.001, 1.01)
        low_price = open_price * random.uniform(0.99, 0.999)
        close_price = random.uniform(low_price, high_price)

        # Volume
        volume = random.uniform(100, 1000) * base_price / 1000

        candles.append({
            "time": int(timestamp.timestamp()),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 2),
        })

        current_price = close_price

    return candles


@router.get("/ohlcv")
async def get_ohlcv(
    symbol: str = Query(..., description="Trading symbol (e.g., BTCUSDT)"),
    timeframe: str = Query(..., description="Timeframe (e.g., 1H, 4H, 1D)"),
    limit: int = Query(500, ge=1, le=5000, description="Number of candles")
) -> Dict[str, Any]:
    """
    Get OHLCV candlestick data for charts

    Returns mock data for now. Real implementation will read from:
    - data/historical/*.parquet files
    - OR PostgreSQL database
    """

    candles = generate_mock_ohlcv(symbol, timeframe, limit)

    return {
        "status": "success",
        "symbol": symbol,
        "timeframe": timeframe,
        "data": candles,
        "count": len(candles),
        "note": "Mock data - real implementation will read from historical files"
    }


@router.get("/symbols")
async def get_symbols() -> Dict[str, Any]:
    """
    Get list of available trading symbols
    TODO: Scan data/historical directory for available symbols
    """
    return {
        "status": "success",
        "symbols": [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "ADAUSDT",
            "DOGEUSDT",
        ],
        "note": "Mock data - real implementation will scan data directory"
    }


@router.get("/timeframes")
async def get_timeframes(symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Get available timeframes for a symbol
    TODO: Check which timeframes exist in historical data
    """
    return {
        "status": "success",
        "timeframes": [
            "5m", "15m", "30m",
            "1h", "2h", "4h", "6h", "12h",
            "1d", "3d", "1w"
        ],
        "note": "Mock data - real implementation will check available files"
    }
