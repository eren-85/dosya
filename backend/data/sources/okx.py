"""
OKX exchange data source
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import ccxt.async_support as ccxt
import asyncio
from .base import ExchangeDataSource, OHLCVData, OrderBookData, TradeData
from ...core.config import settings


class OKXSource(ExchangeDataSource):
    """OKX exchange data provider"""

    def __init__(self):
        super().__init__(name="okx")
        self.exchange: Optional[ccxt.okx] = None
        self._rate_limiter = asyncio.Semaphore(10)

    async def connect(self) -> bool:
        try:
            self.exchange = ccxt.okx({
                'apiKey': settings.okx_api_key,
                'secret': settings.okx_api_secret,
                'password': settings.okx_passphrase,
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}
            })
            await self.exchange.load_markets()
            self._connected = True
            return True
        except Exception as e:
            print(f"OKX connection error: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        if self.exchange:
            await self.exchange.close()
            self._connected = False
        return True

    async def health_check(self) -> bool:
        try:
            if not self.exchange:
                return False
            await self.exchange.fetch_status()
            return True
        except Exception:
            return False

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500,
                          since: Optional[datetime] = None) -> List[OHLCVData]:
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol)
                since_ms = int(since.timestamp() * 1000) if since else None

                ohlcv = await self.exchange.fetch_ohlcv(formatted_symbol, timeframe, since_ms, limit)

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
                print(f"Error fetching OHLCV from OKX: {e}")
                return []

    async def fetch_orderbook(self, symbol: str, depth: int = 20) -> OrderBookData:
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
                print(f"Error fetching orderbook from OKX: {e}")
                raise

    async def fetch_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
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
                print(f"Error fetching trades from OKX: {e}")
                return []

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
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
                print(f"Error fetching ticker from OKX: {e}")
                raise

    async def fetch_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol)
                funding = await self.exchange.fetch_funding_rate(formatted_symbol)

                return {
                    'symbol': symbol,
                    'funding_rate': float(funding['fundingRate']),
                    'next_funding_time': datetime.fromtimestamp(funding['fundingTimestamp'] / 1000),
                    'timestamp': datetime.fromtimestamp(funding['timestamp'] / 1000),
                    'mark_price': float(funding.get('markPrice', 0))
                }
            except Exception as e:
                print(f"Error fetching funding rate from OKX: {e}")
                return None

    async def fetch_open_interest(self, symbol: str) -> Optional[Dict[str, Any]]:
        async with self._rate_limiter:
            try:
                formatted_symbol = self._format_symbol(symbol)
                oi = await self.exchange.fetch_open_interest(formatted_symbol)

                return {
                    'symbol': symbol,
                    'open_interest': float(oi['openInterest']),
                    'timestamp': datetime.fromtimestamp(oi['timestamp'] / 1000),
                    'source': self.name
                }
            except Exception as e:
                print(f"Error fetching open interest from OKX: {e}")
                return None

    def _format_symbol(self, symbol: str) -> str:
        """Convert BTCUSDT -> BTC/USDT:USDT (OKX swap format)"""
        if '/' in symbol:
            return symbol
        if symbol.endswith('USDT'):
            base = symbol[:-4]
            return f"{base}/USDT:USDT"
        return symbol
