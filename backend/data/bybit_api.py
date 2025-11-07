"""
Bybit API Helper
Historical data fetching for Bybit exchange
"""

import pandas as pd
import numpy as np
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BybitAPI:
    """Bybit V5 API for historical data"""

    BASE_URL = "https://api.bybit.com"

    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe

        # Timeframe mapping
        self.tf_map = {
            '1m': '1', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '4h': '240', '1d': 'D', '1w': 'W'
        }

    def fetch_ohlcv(self, start_time: int, end_time: int, limit: int = 1000) -> pd.DataFrame:
        """
        Fetch OHLCV from Bybit
        Endpoint: /v5/market/kline
        """
        url = f"{self.BASE_URL}/v5/market/kline"

        params = {
            'category': 'linear',  # USDT perpetual
            'symbol': self.symbol,
            'interval': self.tf_map[self.timeframe],
            'start': start_time,
            'end': end_time,
            'limit': limit
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data['retCode'] != 0:
                logger.warning(f"Bybit OHLCV error: {data['retMsg']}")
                return pd.DataFrame()

            rows = data['result']['list']

            df = pd.DataFrame(rows, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])

            # Convert types
            df['open_time'] = pd.to_datetime(pd.to_numeric(df['open_time']), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])

            df['has_bybit'] = True

            return df

        except Exception as e:
            logger.warning(f"Bybit OHLCV fetch error: {e}")
            return pd.DataFrame()

    def fetch_open_interest(self, start_time: int, end_time: int) -> pd.DataFrame:
        """
        Fetch Open Interest from Bybit
        Endpoint: /v5/market/open-interest
        """
        url = f"{self.BASE_URL}/v5/market/open-interest"

        params = {
            'category': 'linear',
            'symbol': self.symbol,
            'intervalTime': self.tf_map[self.timeframe],
            'startTime': start_time,
            'endTime': end_time,
            'limit': 200
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data['retCode'] != 0:
                logger.warning(f"Bybit OI error: {data['retMsg']}")
                return pd.DataFrame()

            rows = data['result']['list']

            if not rows:
                return pd.DataFrame()

            df = pd.DataFrame(rows)

            # Bybit may return different field names - handle flexibly
            # Common fields: 'timestamp', 'openInterest' OR 'time', 'openInterest'
            timestamp_field = None
            if 'timestamp' in df.columns:
                timestamp_field = 'timestamp'
            elif 'time' in df.columns:
                timestamp_field = 'time'
            else:
                logger.warning(f"Bybit OI: no timestamp field found. Available: {df.columns.tolist()}")
                return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(pd.to_numeric(df[timestamp_field]), unit='ms')
            df['oi_bybit'] = pd.to_numeric(df['openInterest'])

            return df[['timestamp', 'oi_bybit']]

        except KeyError as e:
            logger.warning(f"Bybit OI field error: {e}. Response fields: {df.columns.tolist() if 'df' in locals() else 'N/A'}")
            return pd.DataFrame()
        except Exception as e:
            logger.warning(f"Bybit OI fetch error: {e}")
            return pd.DataFrame()

    def fetch_funding_rate(self, start_time: int, end_time: int) -> pd.DataFrame:
        """
        Fetch Funding Rate from Bybit
        Endpoint: /v5/market/funding/history
        """
        url = f"{self.BASE_URL}/v5/market/funding/history"

        params = {
            'category': 'linear',
            'symbol': self.symbol,
            'startTime': start_time,
            'endTime': end_time,
            'limit': 200
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data['retCode'] != 0:
                logger.warning(f"Bybit funding error: {data['retMsg']}")
                return pd.DataFrame()

            rows = data['result']['list']

            df = pd.DataFrame(rows)
            df['funding_ts'] = pd.to_datetime(pd.to_numeric(df['fundingRateTimestamp']), unit='ms')
            df['funding_rate_bybit'] = pd.to_numeric(df['fundingRate'])

            return df[['funding_ts', 'funding_rate_bybit']]

        except Exception as e:
            logger.warning(f"Bybit funding fetch error: {e}")
            return pd.DataFrame()

    def fetch_order_book_snapshot(self) -> Dict:
        """
        Fetch current Order Book snapshot from Bybit
        Endpoint: /v5/market/orderbook
        """
        url = f"{self.BASE_URL}/v5/market/orderbook"

        params = {
            'category': 'linear',
            'symbol': self.symbol,
            'limit': 20
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data['retCode'] != 0:
                logger.warning(f"Bybit OB error: {data['retMsg']}")
                return {}

            result = data['result']

            bids = pd.DataFrame(result['b'], columns=['price', 'qty']).astype(float)
            asks = pd.DataFrame(result['a'], columns=['price', 'qty']).astype(float)

            best_bid = bids.iloc[0]['price']
            best_ask = asks.iloc[0]['price']

            # Spread
            spread = best_ask - best_bid
            spread_bps = (spread / best_bid) * 10000

            # Depth
            depth5_bid = bids.head(5)['qty'].sum()
            depth5_ask = asks.head(5)['qty'].sum()
            depth10_bid = bids.head(10)['qty'].sum()
            depth10_ask = asks.head(10)['qty'].sum()

            # Imbalance
            imbalance_10 = (depth10_bid - depth10_ask) / (depth10_bid + depth10_ask)

            return {
                'best_bid_bybit': best_bid,
                'best_ask_bybit': best_ask,
                'spread_bybit': spread,
                'spread_bps_bybit': spread_bps,
                'depth10_bybit': depth10_bid + depth10_ask,
                'ob_imbalance_bybit': imbalance_10
            }

        except Exception as e:
            logger.warning(f"Bybit OB fetch error: {e}")
            return {}
