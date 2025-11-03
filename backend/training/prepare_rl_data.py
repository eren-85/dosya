"""
Prepare historical data with technical indicators for RL training

Indicators:
- EMA (21, 50, 100, 200)
- RSI (14)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2)
- ATR (14)
- Volume indicators
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
    """Calculate Exponential Moving Average"""
    return df[column].ewm(span=period, adjust=False).mean()


def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    column: str = 'close'
) -> tuple:
    """Calculate MACD, Signal, and Histogram"""
    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line

    return macd, signal_line, histogram


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: int = 2,
    column: str = 'close'
) -> tuple:
    """Calculate Bollinger Bands"""
    sma = df[column].rolling(window=period).mean()
    std = df[column].rolling(window=period).std()

    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)

    return upper_band, sma, lower_band


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to dataframe

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with added indicator columns
    """
    logger.info(f"Adding technical indicators to {len(df)} candles...")

    # EMA
    df['ema_21'] = calculate_ema(df, 21)
    df['ema_50'] = calculate_ema(df, 50)
    df['ema_100'] = calculate_ema(df, 100)
    df['ema_200'] = calculate_ema(df, 200)

    # RSI
    df['rsi'] = calculate_rsi(df, 14)

    # MACD
    macd, signal, histogram = calculate_macd(df)
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_histogram'] = histogram

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df)
    df['bb_upper'] = bb_upper
    df['bb_middle'] = bb_middle
    df['bb_lower'] = bb_lower

    # ATR
    df['atr'] = calculate_atr(df)

    # Price-based features
    df['price_change'] = df['close'].pct_change()
    df['volume_change'] = df['volume'].pct_change()

    # High-Low range
    df['hl_range'] = (df['high'] - df['low']) / df['close']

    # Distance from EMAs
    df['dist_ema21'] = (df['close'] - df['ema_21']) / df['close']
    df['dist_ema50'] = (df['close'] - df['ema_50']) / df['close']
    df['dist_ema200'] = (df['close'] - df['ema_200']) / df['close']

    # Bollinger Band position
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # Drop NaN rows (from indicators warmup period)
    df = df.dropna()

    logger.info(f"✅ Indicators added. Final shape: {df.shape}")

    return df


def prepare_training_data(
    symbol: str = "BTCUSDT",
    timeframe: str = "1d",
    market_type: str = "futures",
    data_dir: str = "/home/user/dosya/data/historical"
) -> pd.DataFrame:
    """
    Load historical data and prepare for RL training

    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        market_type: 'spot' or 'futures'
        data_dir: Data directory path

    Returns:
        DataFrame with OHLCV + indicators
    """
    logger.info(f"📊 Preparing training data for {symbol} {timeframe} {market_type}")

    # Try Parquet first
    parquet_file = Path(data_dir) / f"{symbol}_{timeframe}_{market_type}.parquet"
    csv_file = Path(data_dir) / f"{symbol}_{timeframe}_{market_type}.csv"

    if parquet_file.exists():
        logger.info(f"Loading from Parquet: {parquet_file}")
        df = pd.read_parquet(parquet_file)
    elif csv_file.exists():
        logger.info(f"Loading from CSV: {csv_file}")
        df = pd.read_csv(csv_file)
    else:
        raise FileNotFoundError(f"No data file found for {symbol} {timeframe} {market_type}")

    # Ensure required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Convert to numeric (in case they're strings)
    for col in required_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert timestamp if exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')

    # Add technical indicators
    df = add_technical_indicators(df)

    logger.info(f"✅ Training data prepared: {len(df)} candles with {len(df.columns)} features")

    return df


if __name__ == "__main__":
    # Test data preparation
    df = prepare_training_data(
        symbol="BTCUSDT",
        timeframe="1d",
        market_type="futures"
    )

    print(f"\n📊 Data Summary:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Date range: {df.index[0]} to {df.index[-1]}")

    print(f"\n📈 Feature Statistics:")
    print(df[['close', 'ema_21', 'ema_200', 'rsi', 'macd', 'atr']].describe())

    # Save prepared data
    output_file = "/home/user/dosya/backend/data/prepared/BTCUSDT_1d_futures_prepared.parquet"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file)
    print(f"\n💾 Prepared data saved: {output_file}")
