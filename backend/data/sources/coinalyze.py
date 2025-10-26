"""
Coinalyze derivatives data source
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import pandas as pd
from .base import DataSource


class CoinalyzeSource(DataSource):
    """
    Coinalyze derivatives and aggregated data provider
    Provides: funding rates, open interest, long/short ratios, liquidations
    """

    BASE_URL = "https://api.coinalyze.net/v1"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="coinalyze")
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        self.session = aiohttp.ClientSession()
        self._connected = True
        return True

    async def disconnect(self) -> bool:
        if self.session:
            await self.session.close()
            self._connected = False
        return True

    async def health_check(self) -> bool:
        try:
            if not self.session:
                return False

            url = f"{self.BASE_URL}/ping"
            async with self.session.get(url) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def fetch_aggregated_open_interest(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 168  # 1 week
    ) -> pd.DataFrame:
        """
        Fetch aggregated open interest across exchanges

        Args:
            symbol: Trading pair
            interval: Time interval (1h, 4h, 1d)
            limit: Number of data points

        Returns:
            DataFrame with columns: [timestamp, open_interest, oi_change_pct]
        """
        url = f"{self.BASE_URL}/futures/open-interest/aggregated"
        params = {
            'symbols': symbol.upper(),
            'interval': interval,
            'limit': limit
        }

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            async with self.session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    # Parse response
                    history = data.get('history', [])

                    df = pd.DataFrame([
                        {
                            'timestamp': datetime.fromtimestamp(point['t'] / 1000),
                            'open_interest': point['o'],
                            'oi_change_pct': point.get('change', 0)
                        }
                        for point in history
                    ])

                    return df
                else:
                    print(f"Coinalyze API error {resp.status}")
                    return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching aggregated OI from Coinalyze: {e}")
            return pd.DataFrame()

    async def fetch_funding_rates_history(
        self,
        symbol: str = "BTCUSDT",
        exchanges: Optional[List[str]] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch funding rates history across exchanges

        Returns:
            DataFrame with columns: [timestamp, exchange, funding_rate, funding_rate_annualized]
        """
        url = f"{self.BASE_URL}/futures/funding-rate/history"
        params = {
            'symbols': symbol.upper(),
            'limit': limit
        }

        if exchanges:
            params['exchanges'] = ','.join(exchanges)

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            async with self.session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    records = []
                    for item in data.get('history', []):
                        records.append({
                            'timestamp': datetime.fromtimestamp(item['t'] / 1000),
                            'exchange': item['e'],
                            'funding_rate': item['r'],
                            'funding_rate_annualized_pct': item['r'] * 3 * 365 * 100  # 8h → annual
                        })

                    return pd.DataFrame(records)
                else:
                    return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching funding rates from Coinalyze: {e}")
            return pd.DataFrame()

    async def fetch_long_short_ratio(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 168
    ) -> pd.DataFrame:
        """
        Fetch long/short ratio (aggregated across exchanges)

        Returns:
            DataFrame with columns: [timestamp, long_ratio, short_ratio, long_short_ratio]
        """
        url = f"{self.BASE_URL}/futures/long-short-ratio"
        params = {
            'symbols': symbol.upper(),
            'interval': interval,
            'limit': limit
        }

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            async with self.session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    df = pd.DataFrame([
                        {
                            'timestamp': datetime.fromtimestamp(point['t'] / 1000),
                            'long_ratio': point['l'],
                            'short_ratio': point['s'],
                            'long_short_ratio': point['l'] / point['s'] if point['s'] > 0 else 0
                        }
                        for point in data.get('history', [])
                    ])

                    return df
                else:
                    return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching long/short ratio from Coinalyze: {e}")
            return pd.DataFrame()

    async def fetch_liquidations(
        self,
        symbol: str = "BTCUSDT",
        window: str = "24h"
    ) -> Dict[str, Any]:
        """
        Fetch recent liquidations summary

        Returns:
            {
                'long_liquidations_usd': float,
                'short_liquidations_usd': float,
                'total_liquidations_usd': float,
                'long_liq_count': int,
                'short_liq_count': int,
                'timestamp': datetime
            }
        """
        url = f"{self.BASE_URL}/futures/liquidations/summary"
        params = {
            'symbols': symbol.upper(),
            'window': window
        }

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            async with self.session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    summary = data.get('summary', {})

                    return {
                        'symbol': symbol,
                        'long_liquidations_usd': summary.get('long_liq_usd', 0),
                        'short_liquidations_usd': summary.get('short_liq_usd', 0),
                        'total_liquidations_usd': summary.get('total_liq_usd', 0),
                        'long_liq_count': summary.get('long_liq_count', 0),
                        'short_liq_count': summary.get('short_liq_count', 0),
                        'window': window,
                        'timestamp': datetime.now(),
                        'source': self.name
                    }
                else:
                    return {}

        except Exception as e:
            print(f"Error fetching liquidations from Coinalyze: {e}")
            return {}

    async def fetch_aggregated_volume(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 168
    ) -> pd.DataFrame:
        """
        Fetch aggregated trading volume across exchanges

        Returns:
            DataFrame with columns: [timestamp, volume_spot, volume_futures, volume_total]
        """
        url = f"{self.BASE_URL}/markets/volume/aggregated"
        params = {
            'symbols': symbol.upper(),
            'interval': interval,
            'limit': limit
        }

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            async with self.session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    df = pd.DataFrame([
                        {
                            'timestamp': datetime.fromtimestamp(point['t'] / 1000),
                            'volume_spot': point.get('v_spot', 0),
                            'volume_futures': point.get('v_futures', 0),
                            'volume_total': point.get('v_total', 0)
                        }
                        for point in data.get('history', [])
                    ])

                    return df
                else:
                    return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching aggregated volume from Coinalyze: {e}")
            return pd.DataFrame()
