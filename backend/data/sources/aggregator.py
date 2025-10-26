"""
Data aggregator - combines multiple data sources
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import asyncio
from .base import DataSource, OHLCVData
from .binance import BinanceSource
from .glassnode import GlassnodeSource
from ...core.config import settings


class DataAggregator:
    """
    Aggregates data from multiple sources
    - Handles failures gracefully
    - Combines data intelligently
    - Removes outliers
    """

    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize all configured data sources"""
        if self._initialized:
            return

        # Initialize exchange sources
        if 'binance' in settings.data_sources:
            binance = BinanceSource()
            await binance.connect()
            self.sources['binance'] = binance

        # TODO: Add other exchanges (OKX, Bybit, etc.)

        # Initialize on-chain sources
        if 'glassnode' in settings.data_sources:
            glassnode = GlassnodeSource()
            await glassnode.connect()
            self.sources['glassnode'] = glassnode

        # TODO: Add CryptoQuant

        self._initialized = True
        print(f"✅ Initialized {len(self.sources)} data sources: {list(self.sources.keys())}")

    async def shutdown(self):
        """Disconnect all sources"""
        tasks = [source.disconnect() for source in self.sources.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        self._initialized = False

    async def fetch_ohlcv_aggregated(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV from multiple exchanges and aggregate

        Strategy:
        - Use median price (robust to outliers)
        - Sum volumes
        - Use max high, min low
        """

        # Get exchange sources only
        exchange_sources = {
            name: source for name, source in self.sources.items()
            if isinstance(source, BinanceSource)  # TODO: add other exchange types
        }

        if not exchange_sources:
            raise ValueError("No exchange sources available")

        # Fetch from all exchanges in parallel
        tasks = [
            source.fetch_ohlcv(symbol, timeframe, limit, since)
            for source in exchange_sources.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful_data = []
        for source_name, result in zip(exchange_sources.keys(), results):
            if isinstance(result, Exception):
                print(f"⚠️  Error fetching from {source_name}: {result}")
            elif result:
                successful_data.append((source_name, result))

        if not successful_data:
            raise ValueError(f"Failed to fetch OHLCV from any source for {symbol}")

        # Convert to DataFrames
        dfs = []
        for source_name, ohlcv_list in successful_data:
            df = pd.DataFrame([
                {
                    'timestamp': candle.timestamp,
                    'open': candle.open,
                    'high': candle.high,
                    'low': candle.low,
                    'close': candle.close,
                    'volume': candle.volume,
                    'source': source_name
                }
                for candle in ohlcv_list
            ])
            dfs.append(df)

        # Merge strategy
        if len(dfs) == 1:
            # Only one source, return as-is
            merged = dfs[0].copy()
        else:
            # Multiple sources: aggregate intelligently
            merged = self._merge_ohlcv_dataframes(dfs)

        # Add metadata
        merged['symbol'] = symbol
        merged['timeframe'] = timeframe

        return merged.sort_values('timestamp').reset_index(drop=True)

    def _merge_ohlcv_dataframes(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Merge OHLCV data from multiple sources

        Aggregation strategy:
        - open/close: median (robust to outliers)
        - high: max
        - low: min
        - volume: sum
        """

        # Concatenate all dataframes
        combined = pd.concat(dfs, ignore_index=True)

        # Group by timestamp and aggregate
        merged = combined.groupby('timestamp').agg({
            'open': 'median',
            'high': 'max',
            'low': 'min',
            'close': 'median',
            'volume': 'sum'
        }).reset_index()

        return merged

    async def fetch_market_overview(
        self,
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        Fetch market overview for multiple symbols

        Returns:
            {
                'BTCUSDT': {
                    'price': 67234.5,
                    'change_24h': 2.3,
                    'volume_24h': 25000000,
                    'funding_rate': 0.01,
                    'open_interest': 12000000000,
                    ...
                },
                ...
            }
        """

        overview = {}

        for symbol in symbols:
            try:
                # Use Binance as primary source (can be made configurable)
                binance = self.sources.get('binance')
                if not binance:
                    continue

                # Fetch ticker
                ticker = await binance.fetch_ticker(symbol)

                # Fetch derivatives data
                funding = await binance.fetch_funding_rate(symbol)
                oi = await binance.fetch_open_interest(symbol)

                overview[symbol] = {
                    'price': ticker['last'],
                    'change_24h_pct': ticker['change_24h'],
                    'volume_24h': ticker['volume'],
                    'high_24h': ticker['high'],
                    'low_24h': ticker['low'],
                    'funding_rate': funding['funding_rate'] if funding else None,
                    'funding_rate_annualized': funding['funding_rate'] * 3 * 365 * 100 if funding else None,
                    'open_interest': oi['open_interest'] if oi else None,
                    'timestamp': datetime.now()
                }

            except Exception as e:
                print(f"Error fetching overview for {symbol}: {e}")
                overview[symbol] = {'error': str(e)}

        return overview

    async def fetch_onchain_summary(
        self,
        symbol: str = "BTC",
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch on-chain metrics summary

        Args:
            symbol: Cryptocurrency symbol
            metrics: List of metrics to fetch (None = default set)

        Returns:
            {
                'active_addresses': 12345,
                'exchange_netflow': -1234,  # negative = outflow (bullish)
                'whale_tx_count': 23,
                ...
            }
        """

        if metrics is None:
            # Default important metrics
            metrics = [
                'active_addresses',
                'exchange_netflow',
                'exchange_balance',
                'mvrv_ratio',
                'nupl',
                'large_tx_count'
            ]

        glassnode = self.sources.get('glassnode')
        if not glassnode:
            print("⚠️  Glassnode source not available")
            return {}

        # Fetch all metrics in parallel
        results = await glassnode.fetch_multiple_metrics(
            metrics=metrics,
            symbol=symbol,
            resolution='1h',
            lookback_hours=24
        )

        # Extract latest values
        summary = {}
        for metric_name, data_points in results.items():
            if data_points:
                latest = data_points[-1]
                summary[metric_name] = {
                    'value': latest.value,
                    'timestamp': latest.timestamp,
                    'source': latest.source
                }
            else:
                summary[metric_name] = {'value': None, 'timestamp': None}

        return summary

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all sources"""
        results = {}
        for name, source in self.sources.items():
            try:
                is_healthy = await source.health_check()
                results[name] = is_healthy
            except Exception as e:
                print(f"Health check failed for {name}: {e}")
                results[name] = False
        return results

    def get_available_sources(self) -> List[str]:
        """Get list of initialized sources"""
        return list(self.sources.keys())

    def get_source(self, name: str) -> Optional[DataSource]:
        """Get specific source by name"""
        return self.sources.get(name)
