"""
Binance exchange data source
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
import asyncio
from .base import (
    ExchangeDataSource, OHLCVData, OrderBookData,
    TradeData
)
from ...core.config import settings


class BinanceSource(ExchangeDataSource):
    """Binance exchange data provider"""

    def __init__(self):
        super().__init__(name="binance")
        self.exchange: Optional[ccxt.binance] = None
        self._rate_limiter = asyncio.Semaphore(10)  # Max 10 concurrent requests

    async def connect(self) -> bool:
        """Initialize Binance client"""
        try:
            self.exchange = ccxt.binance({
                'apiKey': settings.binance_api_key,
                'secret': settings.binance_api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures by default
                }
            })
            await self.exchange.load_markets()
            self._connected = True
            return True
        except Exception as e:
            print(f"Binance connection error: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        """Close Binance client"""
        if self.exchange:
            await self.exchange.close()
            self._connected = False
        return True

    async def health_check(self) -> bool:
        """Check Binance API status"""
        try:
            if not self.exchange:
                return False
            await self.exchange.fetch_status()
            return True
        except Exception:
            return False

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None
    ) -> List[OHLCVData]:
        """Fetch OHLCV from Binance"""
        async with self._rate_limiter:
            try:
                # Convert symbol format: BTCUSDT -> BTC/USDT
                formatted_symbol = self._format_symbol(symbol)

                since_ms = int(since.timestamp() * 1000) if since else None

                ohlcv = await self.exchange.fetch_ohlcv(
                    formatted_symbol,
                    timeframe=timeframe,
                    since=since_ms,
                    limit=limit
                )

                return [
                    OHLCVData(
                        timestamp=datetime.fromtimestamp(candle[0] / 1000),
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        volume=float(candle[5]),
                        symbol=symbol,
                        timeframe=timeframe,
                        source=self.name
                    )
                    for candle in ohlcv
                ]
            except Exception as e:
                print(f"Error fetching OHLCV from Binance: {e}")
                return []

    async def fetch_orderbook(self, symbol: str, depth: int = 20) -> OrderBookData:
        """Fetch order book from Binance"""
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol)
                orderbook = await self.exchange.fetch_order_book(formatted_symbol, limit=depth)

                return OrderBookData(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    bids=[(float(bid[0]), float(bid[1])) for bid in orderbook['bids']],
                    asks=[(float(ask[0]), float(ask[1])) for ask in orderbook['asks']],
                    source=self.name
                )
            except Exception as e:
                print(f"Error fetching orderbook from Binance: {e}")
                raise

    async def fetch_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
        """Fetch recent trades from Binance"""
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol)
                trades = await self.exchange.fetch_trades(formatted_symbol, limit=limit)

                return [
                    TradeData(
                        timestamp=datetime.fromtimestamp(trade['timestamp'] / 1000),
                        symbol=symbol,
                        price=float(trade['price']),
                        size=float(trade['amount']),
                        side=trade['side'],
                        source=self.name
                    )
                    for trade in trades
                ]
            except Exception as e:
                print(f"Error fetching trades from Binance: {e}")
                return []

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch ticker from Binance"""
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol)
                ticker = await self.exchange.fetch_ticker(formatted_symbol)

                return {
                    'symbol': symbol,
                    'last': float(ticker['last']),
                    'bid': float(ticker['bid']) if ticker['bid'] else None,
                    'ask': float(ticker['ask']) if ticker['ask'] else None,
                    'high': float(ticker['high']) if ticker['high'] else None,
                    'low': float(ticker['low']) if ticker['low'] else None,
                    'volume': float(ticker['quoteVolume']) if ticker['quoteVolume'] else 0,
                    'change_24h': float(ticker['percentage']) if ticker['percentage'] else 0,
                    'timestamp': datetime.now()
                }
            except Exception as e:
                print(f"Error fetching ticker from Binance: {e}")
                raise

    async def fetch_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch funding rate from Binance futures"""
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol)

                # Fetch current funding rate
                funding_rate = await self.exchange.fapiPublicGetPremiumIndex({
                    'symbol': formatted_symbol.replace('/', '')
                })

                return {
                    'symbol': symbol,
                    'funding_rate': float(funding_rate['lastFundingRate']),
                    'next_funding_time': datetime.fromtimestamp(
                        int(funding_rate['nextFundingTime']) / 1000
                    ),
                    'timestamp': datetime.fromtimestamp(int(funding_rate['time']) / 1000),
                    'mark_price': float(funding_rate['markPrice']),
                    'index_price': float(funding_rate['indexPrice'])
                }
            except Exception as e:
                print(f"Error fetching funding rate from Binance: {e}")
                return None

    async def fetch_open_interest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch open interest from Binance futures"""
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol).replace('/', '')

                # Fetch open interest
                oi = await self.exchange.fapiPublicGetOpenInterest({'symbol': formatted_symbol})

                return {
                    'symbol': symbol,
                    'open_interest': float(oi['openInterest']),
                    'timestamp': datetime.fromtimestamp(int(oi['time']) / 1000),
                    'source': self.name
                }
            except Exception as e:
                print(f"Error fetching open interest from Binance: {e}")
                return None

    def _format_symbol(self, symbol: str) -> str:
        """Convert BTCUSDT -> BTC/USDT"""
        if '/' in symbol:
            return symbol
        # Simple heuristic: assume USDT quote
        if symbol.endswith('USDT'):
            base = symbol[:-4]
            return f"{base}/USDT"
        return symbol

    async def fetch_long_short_ratio(self, symbol: str, period: str = "5m") -> Dict[str, Any]:
        """
        Fetch long/short ratio from Binance
        (top trader account ratio)
        """
        try:
            formatted_symbol = self._format_symbol(symbol).replace('/', '')

            # Top trader long/short ratio
            ratio = await self.exchange.fapiDataGetTopLongShortAccountRatio({
                'symbol': formatted_symbol,
                'period': period,
                'limit': 1
            })

            if ratio:
                latest = ratio[-1]
                return {
                    'symbol': symbol,
                    'long_ratio': float(latest['longAccount']),
                    'short_ratio': float(latest['shortAccount']),
                    'long_short_ratio': float(latest['longAccount']) / float(latest['shortAccount'])
                        if float(latest['shortAccount']) > 0 else 0,
                    'timestamp': datetime.fromtimestamp(int(latest['timestamp']) / 1000)
                }

            return {}
        except Exception as e:
            print(f"Error fetching long/short ratio: {e}")
            return {}
