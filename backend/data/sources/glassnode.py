"""
Glassnode on-chain data source
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from .base import OnChainDataSource, OnChainMetric
from ...core.config import settings


class GlassnodeSource(OnChainDataSource):
    """Glassnode on-chain data provider"""

    BASE_URL = "https://api.glassnode.com/v1/metrics"

    # Common metrics mapping
    METRICS_MAP = {
        # Addresses
        'active_addresses': 'addresses/active_count',
        'new_addresses': 'addresses/new_non_zero_count',
        'whale_addresses': 'distribution/balance_1k_plus',

        # Exchange flows
        'exchange_netflow': 'transactions/transfers_volume_exchanges_net',
        'exchange_inflow': 'transactions/transfers_volume_to_exchanges',
        'exchange_outflow': 'transactions/transfers_volume_from_exchanges',
        'exchange_balance': 'distribution/balance_exchanges',

        # Mining
        'hashrate': 'mining/hash_rate_mean',
        'difficulty': 'mining/difficulty_latest',

        # Market
        'realized_cap': 'market/marketcap_realized_usd',
        'mvrv_ratio': 'market/mvrv',
        'nupl': 'indicators/net_unrealized_profit_loss',
        'sopr': 'indicators/sopr',

        # Supply
        'circulating_supply': 'supply/current',
        'illiquid_supply': 'supply/illiquid_sum',
        'liquid_supply': 'supply/liquid_sum',

        # Transactions
        'tx_count': 'transactions/count',
        'tx_volume': 'transactions/transfers_volume_sum',
        'large_tx_count': 'transactions/count_greater_1m_usd',

        # Derivatives
        'futures_open_interest': 'derivatives/futures_open_interest_sum',
        'futures_funding_rate': 'derivatives/futures_funding_rate_perpetual',

        # STH/LTH
        'sth_supply': 'supply/profit_relative_sti',
        'lth_supply': 'supply/profit_relative_lti',
    }

    def __init__(self):
        super().__init__(name="glassnode")
        self.api_key = settings.glassnode_api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """Initialize HTTP session"""
        if not self.api_key:
            print("Warning: Glassnode API key not configured")
            return False

        self.session = aiohttp.ClientSession()
        self._connected = True
        return True

    async def disconnect(self) -> bool:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self._connected = False
        return True

    async def health_check(self) -> bool:
        """Check Glassnode API availability"""
        try:
            if not self.session:
                return False

            # Simple test endpoint
            url = f"{self.BASE_URL}/market/price_usd_close"
            params = {'a': 'BTC', 'api_key': self.api_key, 'i': '24h', 's': int((datetime.now() - timedelta(days=1)).timestamp()), 'u': int(datetime.now().timestamp())}

            async with self.session.get(url, params=params) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def fetch_metric(
        self,
        metric_name: str,
        symbol: str = "BTC",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        resolution: str = "1h"
    ) -> List[OnChainMetric]:
        """Fetch on-chain metric from Glassnode"""

        if not self.session:
            await self.connect()

        # Map friendly name to Glassnode endpoint
        endpoint = self.METRICS_MAP.get(metric_name, metric_name)

        url = f"{self.BASE_URL}/{endpoint}"

        # Convert resolution: 1h -> 1h, 1d -> 24h
        interval_map = {
            '1m': '1h',  # Glassnode min resolution
            '5m': '1h',
            '15m': '1h',
            '1h': '1h',
            '4h': '1h',
            '1d': '24h',
            '1w': '1w'
        }
        interval = interval_map.get(resolution, '1h')

        params = {
            'a': symbol,
            'api_key': self.api_key,
            'i': interval
        }

        if start:
            params['s'] = int(start.timestamp())
        if end:
            params['u'] = int(end.timestamp())

        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    return [
                        OnChainMetric(
                            timestamp=datetime.fromtimestamp(point['t']),
                            metric_name=metric_name,
                            value=float(point['v']) if point['v'] is not None else 0,
                            symbol=symbol,
                            source=self.name
                        )
                        for point in data
                        if point['v'] is not None
                    ]
                elif resp.status == 429:
                    print("Glassnode rate limit exceeded")
                    return []
                else:
                    error_text = await resp.text()
                    print(f"Glassnode API error {resp.status}: {error_text}")
                    return []

        except Exception as e:
            print(f"Error fetching Glassnode metric '{metric_name}': {e}")
            return []

    async def get_available_metrics(self, symbol: str = "BTC") -> List[str]:
        """Get list of available metrics"""
        return list(self.METRICS_MAP.keys())

    async def fetch_whale_transactions(
        self,
        symbol: str = "BTC",
        threshold_usd: float = 1_000_000,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch large transactions
        Note: Glassnode doesn't provide individual tx details in free tier
        We'll use aggregated large tx count instead
        """

        metrics = await self.fetch_metric(
            'large_tx_count',
            symbol=symbol,
            start=datetime.now() - timedelta(days=1),
            end=datetime.now(),
            resolution='1h'
        )

        # Convert to transactions-like format
        transactions = []
        for metric in metrics:
            if metric.value > 0:
                transactions.append({
                    'timestamp': metric.timestamp,
                    'count': int(metric.value),
                    'symbol': symbol,
                    'threshold_usd': threshold_usd,
                    'source': self.name
                })

        return transactions[-limit:]

    async def fetch_exchange_flows(
        self,
        symbol: str = "BTC",
        exchanges: Optional[List[str]] = None,
        window: str = "24h"
    ) -> Dict[str, Any]:
        """Fetch exchange inflow/outflow"""

        end = datetime.now()
        start = end - timedelta(hours=24 if window == "24h" else 1)

        # Fetch metrics
        inflow_data = await self.fetch_metric(
            'exchange_inflow',
            symbol=symbol,
            start=start,
            end=end,
            resolution='1h'
        )

        outflow_data = await self.fetch_metric(
            'exchange_outflow',
            symbol=symbol,
            start=start,
            end=end,
            resolution='1h'
        )

        # Sum values
        total_inflow = sum(m.value for m in inflow_data)
        total_outflow = sum(m.value for m in outflow_data)

        return {
            'inflow': total_inflow,
            'outflow': total_outflow,
            'netflow': total_outflow - total_inflow,  # Positive = outflow (bullish)
            'symbol': symbol,
            'window': window,
            'timestamp': datetime.now(),
            'source': self.name
        }

    async def fetch_multiple_metrics(
        self,
        metrics: List[str],
        symbol: str = "BTC",
        resolution: str = "1h",
        lookback_hours: int = 24
    ) -> Dict[str, List[OnChainMetric]]:
        """Fetch multiple metrics in parallel"""

        end = datetime.now()
        start = end - timedelta(hours=lookback_hours)

        tasks = [
            self.fetch_metric(metric, symbol, start, end, resolution)
            for metric in metrics
        ]

        import asyncio
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for metric_name, result in zip(metrics, results):
            if isinstance(result, Exception):
                print(f"Error fetching {metric_name}: {result}")
                output[metric_name] = []
            else:
                output[metric_name] = result

        return output
