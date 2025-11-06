"""
Basic Historical Data Downloader
Downloads OHLCV data from Binance (Spot/Futures)
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_historical_data(
    symbol: str,
    interval: str = '1d',
    market_type: str = 'spot',
    all_time: bool = False,
    start_date: str = None,
    end_date: str = None,
    use_parquet: bool = True
):
    """
    Download historical OHLCV data from Binance

    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        interval: Candle interval (1m, 5m, 1h, 1d, etc.)
        market_type: 'spot' or 'futures'
        all_time: Download all available data
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        use_parquet: Save as parquet (recommended)
    """

    logger.info(f"📥 Downloading {symbol} {interval} {market_type} data")

    # API endpoint
    if market_type == 'futures':
        base_url = "https://fapi.binance.com/fapi/v1/klines"
    else:
        base_url = "https://api.binance.com/api/v3/klines"

    # Date range
    if all_time:
        # Start from 2017-01-01
        start_time = int(datetime(2017, 1, 1).timestamp() * 1000)
        end_time = int(datetime.now().timestamp() * 1000)
    else:
        if start_date:
            start_time = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            # Default: last 1 year
            start_time = int((datetime.now() - timedelta(days=365)).timestamp() * 1000)

        if end_date:
            end_time = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            end_time = int(datetime.now().timestamp() * 1000)

    # Download in chunks
    all_data = []
    current_time = start_time
    limit = 1000  # Binance limit per request

    logger.info(f"   Date range: {datetime.fromtimestamp(start_time/1000)} → {datetime.fromtimestamp(end_time/1000)}")

    while current_time < end_time:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': current_time,
            'endTime': end_time,
            'limit': limit
        }

        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            all_data.extend(data)

            # Update current_time to last candle + 1
            current_time = data[-1][0] + 1

            logger.info(f"   Downloaded {len(all_data)} candles...")

            # Rate limiting
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"   Error: {e}")
            break

    if not all_data:
        raise ValueError("No data downloaded")

    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])

    # Convert types
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

    # Save
    output_dir = Path('data/historical')
    output_dir.mkdir(parents=True, exist_ok=True)

    if use_parquet:
        output_file = output_dir / f"{symbol}_{interval}_{market_type}.parquet"
        df.to_parquet(output_file, index=False)
    else:
        output_file = output_dir / f"{symbol}_{interval}_{market_type}.csv"
        df.to_csv(output_file, index=False)

    logger.info(f"✅ Saved {len(df)} candles to {output_file}")

    return df


if __name__ == "__main__":
    # Test
    df = download_historical_data(
        symbol='BTCUSDT',
        interval='1d',
        market_type='spot',
        all_time=True,
        use_parquet=True
    )
    print(df.head())
    print(df.tail())
