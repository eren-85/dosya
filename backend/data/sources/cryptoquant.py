"""
CryptoQuant on-chain data source
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from .base import OnChainDataSource, OnChainMetric
from ...core.config import settings


class CryptoQuantSource(OnChainDataSource):
    """CryptoQuant on-chain data provider"""

    BASE_URL = "https://api.cryptoquant.com/v1"

    METRICS_MAP = {
        # Exchange flows
        'exchange_reserve': 'exchange-flows/reserve',
        'exchange_inflow': 'exchange-flows/inflow',
        'exchange_outflow': 'exchange-flows/outflow',
        'exchange_netflow': 'exchange-flows/netflow',

        # Miner data
        'miner_reserve': 'miner-flows/reserve',
        'miner_outflow': 'miner-flows/outflow',
        'hash_ribbon': 'mining/hash-ribbon',

        # Network
        'active_addresses': 'network-data/active-addresses',
        'transactions_count': 'network-data/transactions-count',

        # Market
        'nupl': 'market-data/nupl',
        'mvrv': 'market-data/mvrv',
        'realized_cap': 'market-data/realized-cap',

        # Derivatives
        'open_interest': 'derivatives/open-interest',
        'funding_rates': 'derivatives/funding-rates',
        'long_short_ratio': 'derivatives/long-short-ratio',
    }

    def __init__(self):
        super().__init__(name="cryptoquant")
        self.api_key = settings.cryptoquant_api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        if not self.api_key:
            print("Warning: CryptoQuant API key not configured")
            return False

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

            url = f"{self.BASE_URL}/status"
            headers = {'Authorization': f'Bearer {self.api_key}'}

            async with self.session.get(url, headers=headers) as resp:
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
        if not self.session:
            await self.connect()

        endpoint = self.METRICS_MAP.get(metric_name, metric_name)
        url = f"{self.BASE_URL}/{endpoint}"

        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {
            'symbol': symbol.upper(),
            'window': resolution
        }

        if start:
            params['from'] = int(start.timestamp())
        if end:
            params['to'] = int(end.timestamp())

        try:
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    result = data.get('result', {}).get('data', [])

                    return [
                        OnChainMetric(
                            timestamp=datetime.fromtimestamp(point['timestamp']),
                            metric_name=metric_name,
                            value=float(point['value']),
                            symbol=symbol,
                            source=self.name
                        )
                        for point in result
                        if 'value' in point and point['value'] is not None
                    ]
                else:
                    print(f"CryptoQuant API error {resp.status}")
                    return []
        except Exception as e:
            print(f"Error fetching CryptoQuant metric '{metric_name}': {e}")
            return []

    async def get_available_metrics(self, symbol: str = "BTC") -> List[str]:
        return list(self.METRICS_MAP.keys())

    async def fetch_whale_transactions(
        self,
        symbol: str = "BTC",
        threshold_usd: float = 1_000_000,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch large transactions"""
        url = f"{self.BASE_URL}/network-data/large-transactions"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {
            'symbol': symbol.upper(),
            'threshold': threshold_usd,
            'limit': limit
        }

        try:
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('result', {}).get('data', [])
                return []
        except Exception as e:
            print(f"Error fetching whale transactions: {e}")
            return []

    async def fetch_exchange_flows(
        self,
        symbol: str = "BTC",
        exchanges: Optional[List[str]] = None,
        window: str = "24h"
    ) -> Dict[str, Any]:
        end = datetime.now()
        start = end - timedelta(hours=24 if window == "24h" else 1)

        inflow_data = await self.fetch_metric('exchange_inflow', symbol, start, end, '1h')
        outflow_data = await self.fetch_metric('exchange_outflow', symbol, start, end, '1h')

        total_inflow = sum(m.value for m in inflow_data)
        total_outflow = sum(m.value for m in outflow_data)

        return {
            'inflow': total_inflow,
            'outflow': total_outflow,
            'netflow': total_outflow - total_inflow,
            'symbol': symbol,
            'window': window,
            'timestamp': datetime.now(),
            'source': self.name
        }
