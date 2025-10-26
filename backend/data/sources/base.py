"""
Abstract base classes for data sources
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from dataclasses import dataclass


@dataclass
class OHLCVData:
    """OHLCV candlestick data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str
    source: str


@dataclass
class OrderBookData:
    """Order book snapshot"""
    timestamp: datetime
    symbol: str
    bids: List[tuple[float, float]]  # [(price, size), ...]
    asks: List[tuple[float, float]]
    source: str


@dataclass
class TradeData:
    """Individual trade"""
    timestamp: datetime
    symbol: str
    price: float
    size: float
    side: str  # 'buy' | 'sell'
    source: str


@dataclass
class OnChainMetric:
    """On-chain metric data point"""
    timestamp: datetime
    metric_name: str
    value: float
    symbol: str
    source: str
    metadata: Optional[Dict[str, Any]] = None


class DataSource(ABC):
    """Abstract base class for all data sources"""

    def __init__(self, name: str):
        self.name = name
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data source"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if source is available"""
        pass

    @property
    def is_connected(self) -> bool:
        return self._connected


class ExchangeDataSource(DataSource):
    """Base class for crypto exchange data sources"""

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None
    ) -> List[OHLCVData]:
        """
        Fetch OHLCV candlestick data

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle interval ('1m', '5m', '1h', '1d', etc.)
            limit: Number of candles
            since: Start time

        Returns:
            List of OHLCV data
        """
        pass

    @abstractmethod
    async def fetch_orderbook(
        self,
        symbol: str,
        depth: int = 20
    ) -> OrderBookData:
        """
        Fetch order book snapshot

        Args:
            symbol: Trading pair
            depth: Number of price levels per side

        Returns:
            OrderBook data
        """
        pass

    @abstractmethod
    async def fetch_recent_trades(
        self,
        symbol: str,
        limit: int = 100
    ) -> List[TradeData]:
        """
        Fetch recent trades

        Args:
            symbol: Trading pair
            limit: Number of trades

        Returns:
            List of trades
        """
        pass

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch 24h ticker statistics

        Returns:
            {
                'symbol': str,
                'last': float,
                'bid': float,
                'ask': float,
                'high': float,
                'low': float,
                'volume': float,
                'change_24h': float,
                'timestamp': datetime
            }
        """
        pass

    @abstractmethod
    async def fetch_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current funding rate (for perpetual futures)

        Returns:
            {
                'symbol': str,
                'funding_rate': float,
                'next_funding_time': datetime,
                'timestamp': datetime
            }
        """
        pass

    @abstractmethod
    async def fetch_open_interest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch open interest (for derivatives)

        Returns:
            {
                'symbol': str,
                'open_interest': float,
                'open_interest_value': float,
                'timestamp': datetime
            }
        """
        pass


class OnChainDataSource(DataSource):
    """Base class for on-chain data providers"""

    @abstractmethod
    async def fetch_metric(
        self,
        metric_name: str,
        symbol: str = "BTC",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        resolution: str = "1h"
    ) -> List[OnChainMetric]:
        """
        Fetch on-chain metric

        Args:
            metric_name: Name of metric (e.g., 'active_addresses', 'exchange_netflow')
            symbol: Cryptocurrency symbol
            start: Start time
            end: End time
            resolution: Data resolution

        Returns:
            List of metric data points
        """
        pass

    @abstractmethod
    async def get_available_metrics(self, symbol: str = "BTC") -> List[str]:
        """Get list of available metrics for a symbol"""
        pass

    @abstractmethod
    async def fetch_whale_transactions(
        self,
        symbol: str = "BTC",
        threshold_usd: float = 1_000_000,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch large (whale) transactions

        Args:
            symbol: Cryptocurrency
            threshold_usd: Minimum transaction value in USD
            limit: Max number of transactions

        Returns:
            List of whale transactions
        """
        pass

    @abstractmethod
    async def fetch_exchange_flows(
        self,
        symbol: str = "BTC",
        exchanges: Optional[List[str]] = None,
        window: str = "24h"
    ) -> Dict[str, Any]:
        """
        Fetch exchange inflow/outflow data

        Returns:
            {
                'inflow': float,
                'outflow': float,
                'netflow': float,
                'exchanges': {...},
                'timestamp': datetime
            }
        """
        pass


class AggregatedDataSource(DataSource):
    """Base class for aggregated/composite data sources"""

    @abstractmethod
    async def fetch_cvd(
        self,
        symbol: str,
        exchanges: Optional[List[str]] = None,
        timeframe: str = "1m",
        limit: int = 500
    ) -> pd.DataFrame:
        """
        Fetch Cumulative Volume Delta

        Returns:
            DataFrame with columns: [timestamp, cvd_spot, cvd_perp, buy_volume, sell_volume]
        """
        pass

    @abstractmethod
    async def fetch_liquidations(
        self,
        symbol: str,
        window: str = "24h"
    ) -> Dict[str, Any]:
        """
        Fetch liquidation data

        Returns:
            {
                'long_liquidations': float,
                'short_liquidations': float,
                'total_liquidations': float,
                'timestamp': datetime
            }
        """
        pass
