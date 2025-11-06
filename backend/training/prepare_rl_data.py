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


def add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features from advanced data (multi-exchange)

    Features:
    - Funding spread (Binance vs Bybit)
    - OI divergence (Binance vs Bybit)
    - Consensus signals (average across exchanges)
    - CVD momentum
    - Volatility ratios

    Args:
        df: DataFrame with advanced columns

    Returns:
        DataFrame with derived features
    """
    logger.info("Adding advanced derived features...")

    # Funding spread (if both exchanges have funding data)
    if 'funding_rate_binance' in df.columns and 'funding_rate_bybit' in df.columns:
        df['funding_spread'] = df['funding_rate_binance'] - df['funding_rate_bybit']
        df['funding_avg'] = (df['funding_rate_binance'] + df['funding_rate_bybit']) / 2
        logger.info("   ✅ Funding spread & average")

    # OI divergence
    if 'oi_binance' in df.columns and 'oi_bybit' in df.columns:
        df['oi_ratio'] = df['oi_binance'] / (df['oi_bybit'] + 1e-8)  # Avoid div by zero
        df['oi_divergence'] = (df['oi_binance'] - df['oi_bybit']) / (df['oi_binance'] + df['oi_bybit'] + 1e-8)
        logger.info("   ✅ OI divergence & ratio")

    # Order Book consensus (if both exchanges have OB data)
    if 'ob_imbalance' in df.columns and 'ob_imbalance_bybit' in df.columns:
        df['ob_consensus'] = (df['ob_imbalance'] + df['ob_imbalance_bybit']) / 2
        df['ob_divergence'] = df['ob_imbalance'] - df['ob_imbalance_bybit']
        logger.info("   ✅ Order Book consensus & divergence")

    # CVD momentum (if CVD exists)
    if 'cvd' in df.columns:
        df['cvd_change'] = df['cvd'].diff()
        df['cvd_momentum'] = df['cvd'].rolling(window=14).mean()
        df['cvd_acceleration'] = df['cvd_change'].rolling(window=7).mean()
        logger.info("   ✅ CVD momentum & acceleration")

    # Volatility features (if advanced volatility exists)
    if 'vol_parkinson' in df.columns and 'vol_rs' in df.columns:
        df['vol_avg'] = (df['vol_parkinson'] + df['vol_rs']) / 2
        df['vol_ratio'] = df['vol_parkinson'] / (df['vol_rs'] + 1e-8)
        logger.info("   ✅ Volatility average & ratio")

    # ICT session one-hot encoding (if exists)
    if 'session_label' in df.columns:
        session_dummies = pd.get_dummies(df['session_label'], prefix='session')
        df = pd.concat([df, session_dummies], axis=1)
        logger.info(f"   ✅ Session one-hot: {list(session_dummies.columns)}")

    logger.info(f"✅ Advanced features added. Total columns: {len(df.columns)}")

    return df


def prepare_training_data(
    symbol: str = "BTCUSDT",
    timeframe: str = "1d",
    market_type: str = "futures",
    data_dir: str = "/home/user/dosya/data/historical",
    use_advanced: bool = True
) -> pd.DataFrame:
    """
    Load historical data and prepare for RL training

    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        market_type: 'spot' or 'futures'
        data_dir: Data directory path
        use_advanced: Try to load advanced multi-exchange data first

    Returns:
        DataFrame with OHLCV + indicators + advanced features
    """
    logger.info(f"📊 Preparing training data for {symbol} {timeframe} {market_type}")

    # Priority 1: Advanced multi-exchange data (if enabled)
    advanced_file = Path("/home/user/dosya/data/advanced") / f"{symbol}_{timeframe}_multi.parquet"
    if use_advanced and advanced_file.exists():
        logger.info(f"🚀 Loading ADVANCED data: {advanced_file}")
        df = pd.read_parquet(advanced_file)
        is_advanced = True
    else:
        # Priority 2: Basic historical data
        parquet_file = Path(data_dir) / f"{symbol}_{timeframe}_{market_type}.parquet"
        csv_file = Path(data_dir) / f"{symbol}_{timeframe}_{market_type}.csv"

        if parquet_file.exists():
            logger.info(f"Loading from Parquet: {parquet_file}")
            df = pd.read_parquet(parquet_file)
            is_advanced = False
        elif csv_file.exists():
            logger.info(f"Loading from CSV: {csv_file}")
            df = pd.read_csv(csv_file)
            is_advanced = False
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
    if 'open_time' in df.columns:
        df['timestamp'] = pd.to_datetime(df['open_time'])
        df = df.set_index('timestamp')
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')

    # Add technical indicators (if not already present)
    if 'ema_21' not in df.columns:
        df = add_technical_indicators(df)
    else:
        logger.info("Technical indicators already present, skipping...")

    # Add advanced derived features (if using advanced data)
    if is_advanced:
        df = add_advanced_features(df)
        logger.info("✅ Using ADVANCED multi-exchange features for training")
    else:
        logger.info("ℹ️  Using basic OHLCV + technical indicators")

    logger.info(f"✅ Training data prepared: {len(df)} candles with {len(df.columns)} features")

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Prepare RL training data')
    parser.add_argument('--symbol', type=str, default='BTCUSDT')
    parser.add_argument('--timeframe', type=str, default='1d')
    parser.add_argument('--market', type=str, default='futures')
    parser.add_argument('--no-advanced', action='store_true', help='Disable advanced features')
    args = parser.parse_args()

    # Test data preparation
    df = prepare_training_data(
        symbol=args.symbol,
        timeframe=args.timeframe,
        market_type=args.market,
        use_advanced=not args.no_advanced
    )

    print(f"\n📊 Data Summary:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Date range: {df.index[0]} to {df.index[-1]}")

    # Show all columns organized by category
    print(f"\n📋 Feature Categories:")
    basic_cols = ['open', 'high', 'low', 'close', 'volume']
    ta_cols = [c for c in df.columns if c in ['ema_21', 'ema_50', 'ema_200', 'rsi', 'macd', 'atr', 'bb_upper', 'bb_lower']]
    advanced_cols = [c for c in df.columns if any(x in c for x in ['funding', 'oi_', 'cvd', 'ob_', 'vol_parkinson', 'session'])]

    print(f"   Basic OHLCV: {len(basic_cols)} → {basic_cols}")
    print(f"   Technical Indicators: {len(ta_cols)} → {ta_cols}")
    print(f"   Advanced Features: {len(advanced_cols)}")

    print(f"\n📈 Key Feature Statistics:")
    display_cols = ['close', 'ema_21', 'ema_200', 'rsi', 'macd', 'atr']
    # Add advanced features if present
    if 'cvd' in df.columns:
        display_cols.append('cvd')
    if 'funding_spread' in df.columns:
        display_cols.append('funding_spread')
    if 'oi_divergence' in df.columns:
        display_cols.append('oi_divergence')

    print(df[display_cols].describe())

    # Save prepared data
    suffix = 'advanced' if 'cvd' in df.columns or 'funding_spread' in df.columns else 'prepared'
    output_file = f"/home/user/dosya/backend/data/prepared/{args.symbol}_{args.timeframe}_{args.market}_{suffix}.parquet"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file)
    print(f"\n💾 Prepared data saved: {output_file}")
