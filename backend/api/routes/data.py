# backend/api/routes/data.py
"""
Data API endpoints for charts and market data
"""
from __future__ import annotations

import os
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pandas as pd
import requests
from fastapi import APIRouter, Query, HTTPException

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data", tags=["data"])

# Data directory
DATA_DIR = Path("/app/data/historical") if os.path.exists("/app/data/historical") else Path("data/historical")


def read_historical_data(
    symbol: str,
    timeframe: str,
    market_type: str = "futures",
    limit: int = 500
) -> Optional[List[Dict[str, Any]]]:
    """
    Read historical OHLCV data from parquet files

    File naming: {SYMBOL}_{TIMEFRAME}_{MARKET_TYPE}.parquet
    Example: BTCUSDT_1d_futures.parquet
    """
    # Normalize timeframe
    tf_map = {
        "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "1H": "1h", "2h": "2h", "4h": "4h", "4H": "4h",
        "6h": "6h", "12h": "12h", "1d": "1d", "1D": "1d",
        "3d": "3d", "1w": "1w", "1W": "1w", "1M": "1M"
    }

    normalized_tf = tf_map.get(timeframe, timeframe.lower())

    # Try to find the file
    filename = f"{symbol}_{normalized_tf}_{market_type}.parquet"
    filepath = DATA_DIR / filename

    log.info(f"Attempting to read Parquet: {filepath}")

    if not filepath.exists():
        # Try CSV as fallback
        csv_filename = f"{symbol}_{normalized_tf}_{market_type}.csv"
        csv_filepath = DATA_DIR / csv_filename
        log.info(f"Parquet not found, trying CSV: {csv_filepath}")

        if not csv_filepath.exists():
            log.warning(f"Neither Parquet nor CSV found for {symbol} {normalized_tf}")
            return None

        # Read CSV file
        try:
            df = pd.read_csv(csv_filepath)
            log.info(f"Reading from CSV: {csv_filepath}")
        except Exception as e:
            log.error(f"Error reading CSV {csv_filepath}: {e}")
            return None
    else:
        # Read Parquet file
        try:
            df = pd.read_parquet(filepath)
            log.info(f"Reading from Parquet: {filepath}")
        except Exception as e:
            log.error(f"Error reading Parquet {filepath}: {e}")
            return None

    # Get last N candles (or all if limit=0)
    if limit > 0:
        df = df.tail(limit)
    # else: return all candles

    log.info(f"Returning {len(df)} candles (limit={limit})")

    # Convert to list of dicts for API response
    candles = []
    for idx, row in df.iterrows():
        # Handle datetime index
        if isinstance(idx, pd.Timestamp):
            timestamp = int(idx.timestamp())
        else:
            # If not datetime index, check for timestamp column
            timestamp = int(row.get('timestamp', row.get('open_time', pd.Timestamp.now().timestamp())))

        candles.append({
            "time": timestamp,
            "open": float(row.get('open', row.get('Open', 0))),
            "high": float(row.get('high', row.get('High', 0))),
            "low": float(row.get('low', row.get('Low', 0))),
            "close": float(row.get('close', row.get('Close', 0))),
            "volume": float(row.get('volume', row.get('Volume', 0))),
        })

    log.info(f"Successfully read {len(candles)} candles")
    return candles


def fetch_binance_live_data(
    symbol: str,
    timeframe: str,
    market_type: str = "futures",
    limit: int = 500
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch live data from Binance API as fallback
    """
    try:
        # Binance API endpoint
        if market_type == "futures":
            base_url = "https://fapi.binance.com/fapi/v1/klines"
        else:
            base_url = "https://api.binance.com/api/v3/klines"

        # Binance interval format
        interval_map = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "1H": "1h", "2h": "2h", "4h": "4h", "4H": "4h",
            "6h": "6h", "8h": "8h", "12h": "12h",
            "1d": "1d", "1D": "1d", "3d": "3d",
            "1w": "1w", "1W": "1w", "1M": "1M"
        }

        interval = interval_map.get(timeframe, "1h")

        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000)  # Binance max is 1000
        }

        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        candles = []
        for item in data:
            candles.append({
                "time": int(item[0] / 1000),  # Binance returns ms
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
            })

        log.info(f"Fetched {len(candles)} candles from Binance API")
        return candles

    except Exception as e:
        log.error(f"Error fetching from Binance: {e}")
        return None


def generate_mock_ohlcv(
    symbol: str,
    timeframe: str,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """
    Generate mock OHLCV data for testing UI
    FALLBACK ONLY - Used when no historical data available
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
    market_type: str = Query("futures", description="Market type: futures or spot"),
    limit: int = Query(0, ge=0, le=50000, description="Number of candles (0 = all available)")
) -> Dict[str, Any]:
    """
    Get OHLCV candlestick data for charts

    Priority:
    1. Read from local parquet files (data/historical/*.parquet)
    2. Fetch live data from Binance API
    3. Generate mock data (ALWAYS WORKS as fallback)
    """

    # Set a reasonable limit if 0 (all data)
    actual_limit = limit
    if limit == 0:
        actual_limit = 50000  # Return all data (up to 50k candles)

    log.info(f"Requesting {symbol} {timeframe} {market_type} (limit={actual_limit})")

    # Try to read from historical files first
    candles = read_historical_data(symbol, timeframe, market_type, actual_limit)

    if candles and len(candles) > 0:
        log.info(f"✅ Returning {len(candles)} candles from historical file")
        return {
            "status": "success",
            "symbol": symbol,
            "timeframe": timeframe,
            "market_type": market_type,
            "data": candles,
            "count": len(candles),
            "source": "historical_file"
        }

    # Try to fetch live data from Binance
    log.info(f"Historical file not found, trying Binance API...")
    candles = fetch_binance_live_data(symbol, timeframe, market_type, min(actual_limit, 1000))

    if candles and len(candles) > 0:
        log.info(f"✅ Returning {len(candles)} candles from Binance API")
        return {
            "status": "success",
            "symbol": symbol,
            "timeframe": timeframe,
            "market_type": market_type,
            "data": candles,
            "count": len(candles),
            "source": "binance_api"
        }

    # Generate mock data as fallback (ALWAYS works)
    log.warning(f"Both historical file and Binance API failed, using mock data")
    candles = generate_mock_ohlcv(symbol, timeframe, min(actual_limit, 500))

    log.info(f"✅ Returning {len(candles)} mock candles")
    return {
        "status": "success",
        "symbol": symbol,
        "timeframe": timeframe,
        "market_type": market_type,
        "data": candles,
        "count": len(candles),
        "source": "mock_data"
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
    """
    return {
        "status": "success",
        "timeframes": [
            "1m", "3m", "5m", "15m", "30m",
            "1h", "2h", "4h", "6h", "12h",
            "1d", "3d", "1w", "1M"
        ]
    }
