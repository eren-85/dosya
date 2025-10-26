"""
tucsky/aggr WebSocket client for aggregated trades and liquidations
"""

import websocket
import json
import asyncio
from typing import Dict, List, Callable, Optional
from datetime import datetime
import threading


class AggrWebSocketClient:
    """
    tucsky/aggr WebSocket client
    Real-time aggregated trade data from multiple exchanges
    """

    def __init__(self, url: str = "wss://api.aggr.trade"):
        self.url = url
        self.ws: Optional[websocket.WebSocketApp] = None
        self.subscriptions: List[str] = []
        self.callbacks: Dict[str, List[Callable]] = {
            'trade': [],
            'liquidation': [],
            'error': []
        }
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def subscribe(self, symbols: List[str]):
        """
        Subscribe to symbols

        Args:
            symbols: List of exchange:symbol pairs
                     e.g., ['BINANCE:BTCUSDT', 'OKEX:BTC-USDT']
        """
        self.subscriptions.extend(symbols)

    def on_trade(self, callback: Callable):
        """Register callback for trade events"""
        self.callbacks['trade'].append(callback)

    def on_liquidation(self, callback: Callable):
        """Register callback for liquidation events"""
        self.callbacks['liquidation'].append(callback)

    def on_error(self, callback: Callable):
        """Register callback for errors"""
        self.callbacks['error'].append(callback)

    def connect(self):
        """Start WebSocket connection"""
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )

        self._running = True
        self._thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self._thread.start()

        print(f"✅ Aggr WebSocket connecting to {self.url}")

    def disconnect(self):
        """Close WebSocket connection"""
        self._running = False
        if self.ws:
            self.ws.close()
        print("✅ Aggr WebSocket disconnected")

    def _on_open(self, ws):
        """Handle connection open"""
        print("✅ Aggr WebSocket connected")

        # Subscribe to symbols
        if self.subscriptions:
            subscribe_msg = {
                "op": "subscribe",
                "args": self.subscriptions
            }
            ws.send(json.dumps(subscribe_msg))
            print(f"📡 Subscribed to: {', '.join(self.subscriptions)}")

    def _on_message(self, ws, message):
        """Handle incoming messages"""
        try:
            data = json.loads(message)

            # Determine message type
            if 'type' in data:
                msg_type = data['type']

                if msg_type == 'trade':
                    self._handle_trade(data)
                elif msg_type == 'liquidation':
                    self._handle_liquidation(data)

        except json.JSONDecodeError as e:
            print(f"Error decoding message: {e}")
        except Exception as e:
            print(f"Error handling message: {e}")

    def _handle_trade(self, trade_data: Dict):
        """
        Handle aggregated trade data

        Trade data format:
        {
            "type": "trade",
            "exchange": "BINANCE",
            "symbol": "BTCUSDT",
            "price": 67234.5,
            "size": 0.5,
            "side": "buy",  # or "sell"
            "timestamp": 1698765432000
        }
        """
        # Enrich trade data
        enriched = {
            **trade_data,
            'timestamp_dt': datetime.fromtimestamp(trade_data['timestamp'] / 1000),
            'value_usd': trade_data['price'] * trade_data['size']
        }

        # Call registered callbacks
        for callback in self.callbacks['trade']:
            try:
                callback(enriched)
            except Exception as e:
                print(f"Error in trade callback: {e}")

    def _handle_liquidation(self, liq_data: Dict):
        """
        Handle liquidation data

        Liquidation data format:
        {
            "type": "liquidation",
            "exchange": "BINANCE",
            "symbol": "BTCUSDT",
            "price": 67234.5,
            "size": 10.0,
            "side": "long",  # or "short"
            "timestamp": 1698765432000
        }
        """
        # Enrich liquidation data
        enriched = {
            **liq_data,
            'timestamp_dt': datetime.fromtimestamp(liq_data['timestamp'] / 1000),
            'value_usd': liq_data['price'] * liq_data['size']
        }

        # Call registered callbacks
        for callback in self.callbacks['liquidation']:
            try:
                callback(enriched)
            except Exception as e:
                print(f"Error in liquidation callback: {e}")

    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"⚠️  Aggr WebSocket error: {error}")

        for callback in self.callbacks['error']:
            try:
                callback(error)
            except Exception:
                pass

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle connection close"""
        print(f"❌ Aggr WebSocket closed: {close_status_code} - {close_msg}")

        # Auto-reconnect if still running
        if self._running:
            print("🔄 Reconnecting in 5 seconds...")
            threading.Timer(5.0, self.connect).start()


# Example usage integration with memory manager
class AggrDataCollector:
    """
    Collector that processes Aggr data and stores to memory manager
    """

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.client = AggrWebSocketClient()

        # Register callbacks
        self.client.on_trade(self.handle_trade)
        self.client.on_liquidation(self.handle_liquidation)

        # Cumulative Volume Delta (CVD) tracking
        self.cvd = {}

    def start(self, symbols: List[str]):
        """Start collecting data"""
        self.client.subscribe(symbols)
        self.client.connect()

    def stop(self):
        """Stop collecting"""
        self.client.disconnect()

    def handle_trade(self, trade: Dict):
        """Process aggregated trade"""
        symbol = trade['symbol']

        # Store to Redis
        self.memory_manager.add_recent_trade(
            symbol=symbol,
            trade={
                'price': trade['price'],
                'size': trade['size'],
                'side': trade['side'],
                'exchange': trade['exchange'],
                'timestamp': trade['timestamp_dt'].isoformat()
            }
        )

        # Update CVD
        if symbol not in self.cvd:
            self.cvd[symbol] = 0

        if trade['side'] == 'buy':
            self.cvd[symbol] += trade['size']
        else:
            self.cvd[symbol] -= trade['size']

        # Cache CVD
        self.memory_manager.redis.setex(
            f"cvd:{symbol}",
            3600,  # 1 hour TTL
            str(self.cvd[symbol])
        )

    def handle_liquidation(self, liq: Dict):
        """Process liquidation event"""
        symbol = liq['symbol']

        # Store liquidation alert
        self.memory_manager.add_alert({
            'type': 'liquidation',
            'symbol': symbol,
            'exchange': liq['exchange'],
            'side': liq['side'],
            'size': liq['size'],
            'value_usd': liq['value_usd'],
            'price': liq['price']
        })

        print(f"🔥 LIQUIDATION: {liq['side'].upper()} {liq['size']} {symbol} @ {liq['price']} on {liq['exchange']}")
