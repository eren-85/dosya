"""
Hybrid memory management system
- Short-term: Redis (TTL-based cache)
- Medium-term: PostgreSQL/TimescaleDB (time-series)
- Long-term: Pinecone (vector DB for RAG)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import pandas as pd
from redis import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ...core.config import settings


class MemoryManager:
    """
    Hybrid multi-tier memory system
    """

    def __init__(self):
        # Short-term: Redis
        self.redis = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            db=settings.redis_db,
            decode_responses=True
        )

        # Medium-term: TimescaleDB (PostgreSQL extension)
        self.timescale_engine = create_engine(settings.database_url)
        self.Session = sessionmaker(bind=self.timescale_engine)

        # Long-term: Vector DB (will be initialized separately)
        self.vector_db = None  # Initialized in PDF learning module

        # In-memory working memory
        self.working_memory: Dict[str, Any] = {
            'current_state': {},
            'active_positions': {},
            'pending_orders': [],
            'alerts': []
        }

        # Initialize database schema
        self._init_database()

    def _init_database(self):
        """Initialize TimescaleDB tables"""
        with self.timescale_engine.connect() as conn:
            # Create candles table (hypertable)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS candles (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open DOUBLE PRECISION,
                    high DOUBLE PRECISION,
                    low DOUBLE PRECISION,
                    close DOUBLE PRECISION,
                    volume DOUBLE PRECISION,
                    source TEXT,
                    PRIMARY KEY (time, symbol, timeframe)
                );
            """))

            # Create hypertable if not exists
            conn.execute(text("""
                SELECT create_hypertable('candles', 'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """))

            # Create indicators table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS indicators (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    indicator_name TEXT NOT NULL,
                    value DOUBLE PRECISION,
                    metadata JSONB,
                    PRIMARY KEY (time, symbol, timeframe, indicator_name)
                );
            """))

            conn.execute(text("""
                SELECT create_hypertable('indicators', 'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """))

            # Create trade_history table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,  -- 'buy' or 'sell'
                    price DOUBLE PRECISION,
                    quantity DOUBLE PRECISION,
                    pnl DOUBLE PRECISION,
                    strategy TEXT,
                    metadata JSONB,
                    PRIMARY KEY (time, symbol, side)
                );
            """))

            conn.execute(text("""
                SELECT create_hypertable('trade_history', 'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '7 days'
                );
            """))

            # Create model_predictions table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS model_predictions (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    prediction_type TEXT,  -- 'price', 'trend', 'volatility'
                    predicted_value DOUBLE PRECISION,
                    confidence DOUBLE PRECISION,
                    metadata JSONB,
                    PRIMARY KEY (time, symbol, model_name, prediction_type)
                );
            """))

            conn.execute(text("""
                SELECT create_hypertable('model_predictions', 'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """))

            conn.commit()

        print("✅ Database schema initialized")

    # ===== SHORT-TERM MEMORY (Redis) =====

    def cache_price(self, symbol: str, price: float, ttl: int = 60):
        """Cache current price with TTL"""
        key = f"price:{symbol}"
        self.redis.setex(key, ttl, str(price))

    def get_cached_price(self, symbol: str) -> Optional[float]:
        """Get cached price"""
        value = self.redis.get(f"price:{symbol}")
        return float(value) if value else None

    def cache_ticker(self, symbol: str, ticker: Dict[str, Any], ttl: int = 60):
        """Cache ticker data"""
        key = f"ticker:{symbol}"
        self.redis.setex(key, ttl, json.dumps(ticker))

    def get_cached_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached ticker"""
        value = self.redis.get(f"ticker:{symbol}")
        return json.loads(value) if value else None

    def add_recent_trade(self, symbol: str, trade: Dict[str, Any], max_size: int = 1000):
        """Add trade to recent trades list (FIFO queue)"""
        key = f"trades:{symbol}"
        self.redis.lpush(key, json.dumps(trade))
        self.redis.ltrim(key, 0, max_size - 1)  # Keep only last N trades

    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades"""
        key = f"trades:{symbol}"
        trades_json = self.redis.lrange(key, 0, limit - 1)
        return [json.loads(t) for t in trades_json]

    def cache_orderbook(self, symbol: str, orderbook: Dict[str, Any], ttl: int = 5):
        """Cache order book (very short TTL)"""
        key = f"orderbook:{symbol}"
        self.redis.setex(key, ttl, json.dumps(orderbook))

    def get_cached_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached order book"""
        value = self.redis.get(f"orderbook:{symbol}")
        return json.loads(value) if value else None

    # ===== MEDIUM-TERM MEMORY (TimescaleDB) =====

    def store_candle(self, symbol: str, timeframe: str, candle: Dict[str, Any]):
        """Store OHLCV candle"""
        with self.Session() as session:
            session.execute(text("""
                INSERT INTO candles (time, symbol, timeframe, open, high, low, close, volume, source)
                VALUES (:time, :symbol, :timeframe, :open, :high, :low, :close, :volume, :source)
                ON CONFLICT (time, symbol, timeframe) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    source = EXCLUDED.source
            """), {
                'time': candle['timestamp'],
                'symbol': symbol,
                'timeframe': timeframe,
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle['volume'],
                'source': candle.get('source', 'unknown')
            })
            session.commit()

    def store_candles_bulk(self, candles_df: pd.DataFrame):
        """Store multiple candles efficiently"""
        candles_df.to_sql(
            'candles',
            self.timescale_engine,
            if_exists='append',
            index=False,
            method='multi'
        )

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime
    ) -> pd.DataFrame:
        """Retrieve historical candles"""
        query = text("""
            SELECT time, open, high, low, close, volume
            FROM candles
            WHERE symbol = :symbol
              AND timeframe = :timeframe
              AND time >= :start
              AND time <= :end
            ORDER BY time ASC
        """)

        with self.Session() as session:
            result = session.execute(query, {
                'symbol': symbol,
                'timeframe': timeframe,
                'start': start,
                'end': end
            })

            df = pd.DataFrame(result.fetchall(), columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            return df

    def store_indicator(
        self,
        symbol: str,
        timeframe: str,
        indicator_name: str,
        timestamp: datetime,
        value: float,
        metadata: Optional[Dict] = None
    ):
        """Store technical indicator value"""
        with self.Session() as session:
            session.execute(text("""
                INSERT INTO indicators (time, symbol, timeframe, indicator_name, value, metadata)
                VALUES (:time, :symbol, :timeframe, :indicator_name, :value, :metadata)
                ON CONFLICT (time, symbol, timeframe, indicator_name) DO UPDATE SET
                    value = EXCLUDED.value,
                    metadata = EXCLUDED.metadata
            """), {
                'time': timestamp,
                'symbol': symbol,
                'timeframe': timeframe,
                'indicator_name': indicator_name,
                'value': value,
                'metadata': json.dumps(metadata) if metadata else None
            })
            session.commit()

    def get_indicator(
        self,
        symbol: str,
        timeframe: str,
        indicator_name: str,
        start: datetime,
        end: datetime
    ) -> pd.DataFrame:
        """Retrieve indicator values"""
        query = text("""
            SELECT time, value, metadata
            FROM indicators
            WHERE symbol = :symbol
              AND timeframe = :timeframe
              AND indicator_name = :indicator_name
              AND time >= :start
              AND time <= :end
            ORDER BY time ASC
        """)

        with self.Session() as session:
            result = session.execute(query, {
                'symbol': symbol,
                'timeframe': timeframe,
                'indicator_name': indicator_name,
                'start': start,
                'end': end
            })

            df = pd.DataFrame(result.fetchall(), columns=['time', 'value', 'metadata'])
            return df

    def store_trade(self, trade: Dict[str, Any]):
        """Store executed trade"""
        with self.Session() as session:
            session.execute(text("""
                INSERT INTO trade_history (time, symbol, side, price, quantity, pnl, strategy, metadata)
                VALUES (:time, :symbol, :side, :price, :quantity, :pnl, :strategy, :metadata)
            """), {
                'time': trade['timestamp'],
                'symbol': trade['symbol'],
                'side': trade['side'],
                'price': trade['price'],
                'quantity': trade['quantity'],
                'pnl': trade.get('pnl', 0),
                'strategy': trade.get('strategy', 'unknown'),
                'metadata': json.dumps(trade.get('metadata', {}))
            })
            session.commit()

    def get_trade_history(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """Retrieve trade history"""
        query_parts = ["SELECT * FROM trade_history WHERE 1=1"]
        params = {}

        if symbol:
            query_parts.append("AND symbol = :symbol")
            params['symbol'] = symbol

        if start:
            query_parts.append("AND time >= :start")
            params['start'] = start

        if end:
            query_parts.append("AND time <= :end")
            params['end'] = end

        query_parts.append("ORDER BY time DESC")
        query_parts.append(f"LIMIT {limit}")

        query = text(" ".join(query_parts))

        with self.Session() as session:
            result = session.execute(query, params)
            df = pd.DataFrame(result.fetchall())
            return df

    def store_prediction(
        self,
        symbol: str,
        model_name: str,
        prediction_type: str,
        predicted_value: float,
        confidence: float,
        metadata: Optional[Dict] = None
    ):
        """Store model prediction"""
        with self.Session() as session:
            session.execute(text("""
                INSERT INTO model_predictions
                (time, symbol, model_name, prediction_type, predicted_value, confidence, metadata)
                VALUES (:time, :symbol, :model_name, :prediction_type, :predicted_value, :confidence, :metadata)
            """), {
                'time': datetime.now(),
                'symbol': symbol,
                'model_name': model_name,
                'prediction_type': prediction_type,
                'predicted_value': predicted_value,
                'confidence': confidence,
                'metadata': json.dumps(metadata) if metadata else None
            })
            session.commit()

    # ===== WORKING MEMORY (In-Memory) =====

    def update_state(self, key: str, value: Any):
        """Update current agent state"""
        self.working_memory['current_state'][key] = value

    def get_state(self, key: Optional[str] = None) -> Any:
        """Get agent state"""
        if key:
            return self.working_memory['current_state'].get(key)
        return self.working_memory['current_state']

    def add_position(self, symbol: str, position: Dict[str, Any]):
        """Add/update active position"""
        self.working_memory['active_positions'][symbol] = position

    def remove_position(self, symbol: str):
        """Remove position"""
        if symbol in self.working_memory['active_positions']:
            del self.working_memory['active_positions'][symbol]

    def get_positions(self) -> Dict[str, Any]:
        """Get all active positions"""
        return self.working_memory['active_positions']

    def add_alert(self, alert: Dict[str, Any]):
        """Add alert to working memory"""
        alert['timestamp'] = datetime.now()
        self.working_memory['alerts'].insert(0, alert)
        # Keep only last 100 alerts
        self.working_memory['alerts'] = self.working_memory['alerts'][:100]

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.working_memory['alerts'][:limit]

    def clear_working_memory(self):
        """Clear in-memory state"""
        self.working_memory = {
            'current_state': {},
            'active_positions': {},
            'pending_orders': [],
            'alerts': []
        }

    # ===== COMPRESSION & MAINTENANCE =====

    def compress_old_data(self, days_threshold: int = 30):
        """Compress old candle data (TimescaleDB compression)"""
        cutoff = datetime.now() - timedelta(days=days_threshold)

        with self.timescale_engine.connect() as conn:
            conn.execute(text(f"""
                SELECT compress_chunk(i)
                FROM show_chunks('candles', older_than => :cutoff) i;
            """), {'cutoff': cutoff})

            conn.commit()

        print(f"✅ Compressed candles older than {days_threshold} days")

    def cleanup_old_predictions(self, days_to_keep: int = 90):
        """Delete old predictions"""
        cutoff = datetime.now() - timedelta(days=days_to_keep)

        with self.Session() as session:
            session.execute(text("""
                DELETE FROM model_predictions WHERE time < :cutoff
            """), {'cutoff': cutoff})
            session.commit()

        print(f"✅ Cleaned predictions older than {days_to_keep} days")
