"""
Advanced Data Collector
Comprehensive market data aggregation for ML training

Features:
- OHLCV (multi-exchange aggregation)
- Volatility: ATR, Parkinson, Rogers-Satchell
- CVD: Binance taker_buy based + fallback
- Open Interest: Binance/Bybit/OKX per exchange
- Funding Rate: per exchange
- Liquidations: notional + count
- Order Book: snapshot (imbalance, spread, microprice, depth)
- ICT Sessions: Asia/London/NY kill-zones
- Meta: resume cursor, contracts, schema versioning

Usage:
    python backend/data/advanced_collector.py \\
        --symbol BTCUSDT \\
        --timeframe 1h \\
        --market futures \\
        --start-date 2024-01-01 \\
        --exchanges binance,bybit,okx \\
        --features all
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional
import requests
import time
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Bybit API helper (import after path setup)
try:
    from backend.data.bybit_api import BybitAPI
except ImportError:
    logger.warning("⚠️  BybitAPI not found, multi-exchange disabled")
    BybitAPI = None


class AdvancedDataCollector:
    """
    Comprehensive market data collector

    Layers:
    1. OHLCV + Aggregation (multi-exchange)
    2. Volatility (ATR, Parkinson, Rogers-Satchell)
    3. CVD (Cumulative Volume Delta)
    4. Open Interest (per exchange)
    5. Funding Rate (per exchange)
    6. Liquidations (notional + count)
    7. Order Book (snapshot)
    8. ICT Sessions (Asia/London/NY)
    """

    BINANCE_BASE = "https://fapi.binance.com"
    BYBIT_BASE = "https://api.bybit.com"

    def __init__(self, symbol: str, timeframe: str, market: str = 'futures', exchanges: List[str] = None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.market = market
        self.exchanges = exchanges or ['binance', 'bybit']  # Default: Binance + Bybit

        # Timeframe mapping
        self.tf_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w'
        }

        # Bybit timeframe mapping
        self.bybit_tf_map = {
            '1m': '1', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '4h': '240', '1d': 'D', '1w': 'W'
        }

        logger.info(f"📊 Collector initialized: {symbol} {timeframe} {market}")
        logger.info(f"   Exchanges: {', '.join(self.exchanges)}")

    # ============================================
    # 1. OHLCV (Binance primary)
    # ============================================

    def fetch_ohlcv_binance(self, start_time: int, end_time: int, limit: int = 1500) -> pd.DataFrame:
        """
        Fetch OHLCV from Binance with taker_buy_base_volume
        Loops to fetch all data from start_time to end_time (handles Binance 1500 limit)
        Supports both spot and futures markets
        """
        # Select API endpoint based on market type
        if self.market == 'futures':
            url = f"{self.BINANCE_BASE}/fapi/v1/klines"
        else:  # spot
            url = "https://api.binance.com/api/v3/klines"

        all_data = []
        current_start = start_time

        # Timeframe to milliseconds mapping
        tf_to_ms = {
            '1m': 60_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000,
            '1h': 3_600_000, '4h': 14_400_000, '1d': 86_400_000, '1w': 604_800_000, '1M': 2_592_000_000
        }

        tf_ms = tf_to_ms.get(self.timeframe, 3_600_000)  # Default 1h

        # Calculate estimated total candles for progress
        estimated_candles = int((end_time - start_time) / tf_ms)

        # Progress tracking (simple print-based, works in Docker)
        last_log_count = 0
        log_interval = max(5000, estimated_candles // 20)  # Log every 5% or 5000 candles
        start_fetch_time = time.time()

        # Use print + flush for immediate output (logger is buffered)
        print(f"      📥 {self.symbol}: Starting download (~{estimated_candles:,} candles estimated)...", flush=True)

        # Probe for first available data (in case coin listed later than start_time)
        QUARTER_MS = 90 * 24 * 60 * 60 * 1000  # 3 months
        found_first_data = False
        probe_start = current_start

        while probe_start < end_time and not found_first_data:
            params = {
                'symbol': self.symbol,
                'interval': self.tf_map[self.timeframe],
                'startTime': probe_start,
                'endTime': end_time,
                'limit': 10  # Small limit for probe
            }

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data:
                    # Found first data! Update start time
                    found_first_data = True
                    current_start = probe_start
                    first_candle_time = datetime.fromtimestamp(int(data[0][0])/1000, tz=timezone.utc)
                    print(f"         📅 First candle found: {first_candle_time.strftime('%Y-%m-%d %H:%M:%S UTC')}", flush=True)
                    break
                else:
                    # No data yet, advance 3 months
                    probe_start += QUARTER_MS
                    time.sleep(0.1)  # Light rate limit

            except Exception as e:
                logger.warning(f"Probe error at {probe_start}: {e}")
                probe_start += QUARTER_MS

        if not found_first_data:
            print(f"         ⚠️  No data found for {self.symbol} in date range", flush=True)
            return pd.DataFrame()

        # Now fetch all data from actual start
        while current_start < end_time:
            params = {
                'symbol': self.symbol,
                'interval': self.tf_map[self.timeframe],
                'startTime': current_start,
                'endTime': end_time,
                'limit': limit
            }

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if not data:
                    break

                all_data.extend(data)

                # Update progress (print + flush for immediate visibility)
                if len(all_data) - last_log_count >= log_interval:
                    percent = (len(all_data) / estimated_candles * 100) if estimated_candles > 0 else 0
                    elapsed = time.time() - start_fetch_time
                    rate = len(all_data) / elapsed if elapsed > 0 else 0
                    print(f"         ⏳ {len(all_data):,}/{estimated_candles:,} candles ({percent:.1f}%) [{rate:.1f} candles/s]", flush=True)
                    last_log_count = len(all_data)

                # Move to next batch (last candle timestamp + 1ms)
                last_timestamp = int(data[-1][0])

                if last_timestamp >= end_time:
                    break

                current_start = last_timestamp + tf_ms

                # Rate limiting
                time.sleep(0.2)

            except Exception as e:
                logger.warning(f"OHLCV fetch error at {current_start}: {e}")
                break

        # Final progress (print + flush)
        if all_data:
            elapsed = time.time() - start_fetch_time
            rate = len(all_data) / elapsed if elapsed > 0 else 0
            print(f"         ✅ {len(all_data):,} candles complete! [{elapsed:.1f}s, {rate:.1f} candles/s]", flush=True)

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])

        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base']:
            df[col] = pd.to_numeric(df[col])

        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['has_binance'] = True

        # Remove duplicates (can happen at batch boundaries)
        df = df.drop_duplicates(subset=['open_time'], keep='first')

        return df

    # ============================================
    # 2. Volatility Metrics
    # ============================================

    def calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate volatility metrics:
        - ATR (Average True Range)
        - Parkinson volatility
        - Rogers-Satchell volatility
        """
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(14).mean()

        # Parkinson volatility (high-low based)
        df['vol_parkinson'] = np.sqrt(
            (1 / (4 * np.log(2))) * ((np.log(df['high'] / df['low'])) ** 2)
        ).rolling(14).mean()

        # Rogers-Satchell volatility (OHLC based)
        rs = np.sqrt(
            np.log(df['high'] / df['close']) * np.log(df['high'] / df['open']) +
            np.log(df['low'] / df['close']) * np.log(df['low'] / df['open'])
        )
        df['vol_rs'] = rs.rolling(14).mean()

        return df

    # ============================================
    # 3. CVD (Cumulative Volume Delta)
    # ============================================

    def calculate_cvd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        CVD from Binance taker_buy_base_volume
        delta_vol = 2 * taker_buy_base - volume_base
        cvd = cumsum(delta_vol)
        """
        if 'taker_buy_base' in df.columns:
            df['delta_vol'] = 2 * df['taker_buy_base'] - df['volume']
            df['cvd'] = df['delta_vol'].cumsum()
            df['cvd_src'] = 'binance'
        else:
            # Fallback: sign(ret) * volume
            df['ret'] = df['close'].pct_change()
            df['delta_vol'] = np.sign(df['ret']) * df['volume']
            df['cvd'] = df['delta_vol'].cumsum()
            df['cvd_src'] = 'fallback'

        return df

    # ============================================
    # 4. Open Interest (Binance)
    # ============================================

    def fetch_open_interest_binance(self, start_time: int, end_time: int) -> pd.DataFrame:
        """
        Fetch Open Interest from Binance
        Loops to fetch all historical OI data (Binance limit: 500 per request)

        Note: OI data availability varies by symbol. The caller should use the
        actual OHLCV start timestamp to avoid requesting data before the symbol existed.

        If OI data doesn't exist at start_time, automatically advances 30 days forward
        until finding the first valid OI record.
        """
        url = f"{self.BINANCE_BASE}/futures/data/openInterestHist"

        # Ensure endTime is not in the future
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        end_time = min(end_time, now_ms)

        all_data = []
        current_start = start_time

        # Timeframe to milliseconds
        tf_to_ms = {
            '1m': 60_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000,
            '1h': 3_600_000, '4h': 14_400_000, '1d': 86_400_000, '1w': 604_800_000
        }
        tf_ms = tf_to_ms.get(self.timeframe, 3_600_000)

        # STEP 1: Find first valid OI timestamp (handle coins with late OI data)
        # Try advancing 30 days at a time until we get a valid response
        MONTH_MS = 30 * 24 * 60 * 60 * 1000  # 30 days
        probe_start = current_start
        found_start = False

        while probe_start < end_time and not found_start:
            params = {
                'symbol': self.symbol,
                'period': self.tf_map[self.timeframe],
                'startTime': probe_start,
                'endTime': end_time,
                'limit': 500
            }

            try:
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 400:
                    # OI data doesn't exist at this time, advance forward
                    probe_start += MONTH_MS
                    continue

                response.raise_for_status()
                data = response.json()

                if data:
                    # Found first valid OI record!
                    found_start = True
                    current_start = probe_start
                    all_data.extend(data)

                    # Move to next batch
                    last_timestamp = int(data[-1]['timestamp'])
                    current_start = last_timestamp + tf_ms
                    break
                else:
                    # Empty response, try next month
                    probe_start += MONTH_MS

            except Exception as e:
                # Other errors, try next month
                probe_start += MONTH_MS
                continue

        if not found_start:
            # No OI data available for this symbol in the requested range
            return pd.DataFrame()

        # STEP 2: Normal pagination from first valid timestamp
        while current_start < end_time:
            params = {
                'symbol': self.symbol,
                'period': self.tf_map[self.timeframe],
                'startTime': current_start,
                'endTime': end_time,
                'limit': 500
            }

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if not data:
                    break

                all_data.extend(data)

                # Move to next batch
                last_timestamp = int(data[-1]['timestamp'])

                if last_timestamp >= end_time:
                    break

                current_start = last_timestamp + tf_ms

                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                logger.warning(f"OI fetch error at {current_start}: {e}")
                break

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(pd.to_numeric(df['timestamp']), unit='ms')
        df['oi_binance'] = pd.to_numeric(df['sumOpenInterest'])

        # Remove duplicates
        df = df.drop_duplicates(subset=['timestamp'], keep='first')

        return df[['timestamp', 'oi_binance']]

    # ============================================
    # 5. Funding Rate (Binance)
    # ============================================

    def fetch_funding_rate_binance(self, start_time: int, end_time: int) -> pd.DataFrame:
        """
        Fetch Funding Rate from Binance
        Loops to fetch all historical funding data (Binance limit: 1000 per request)

        If funding data doesn't exist at start_time, automatically advances 30 days forward
        until finding the first valid funding record.
        """
        url = f"{self.BINANCE_BASE}/fapi/v1/fundingRate"

        # Ensure endTime is not in the future
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        end_time = min(end_time, now_ms)

        all_data = []
        current_start = start_time

        # Funding happens every 8 hours (28800000 ms)
        FUNDING_INTERVAL_MS = 28_800_000

        # STEP 1: Find first valid funding timestamp
        MONTH_MS = 30 * 24 * 60 * 60 * 1000  # 30 days
        probe_start = current_start
        found_start = False

        while probe_start < end_time and not found_start:
            params = {
                'symbol': self.symbol,
                'startTime': probe_start,
                'endTime': end_time,
                'limit': 1000
            }

            try:
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 400:
                    # Funding data doesn't exist at this time, advance forward
                    probe_start += MONTH_MS
                    continue

                response.raise_for_status()
                data = response.json()

                if data:
                    # Found first valid funding record!
                    found_start = True
                    current_start = probe_start
                    all_data.extend(data)

                    # Move to next batch
                    last_timestamp = int(data[-1]['fundingTime'])
                    current_start = last_timestamp + FUNDING_INTERVAL_MS
                    break
                else:
                    # Empty response, try next month
                    probe_start += MONTH_MS

            except Exception as e:
                # Other errors, try next month
                probe_start += MONTH_MS
                continue

        if not found_start:
            # No funding data available for this symbol in the requested range
            return pd.DataFrame()

        # STEP 2: Normal pagination from first valid timestamp
        while current_start < end_time:
            params = {
                'symbol': self.symbol,
                'startTime': current_start,
                'endTime': end_time,
                'limit': 1000
            }

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if not data:
                    break

                all_data.extend(data)

                # Move to next batch (last funding timestamp + interval)
                last_timestamp = int(data[-1]['fundingTime'])

                if last_timestamp >= end_time:
                    break

                current_start = last_timestamp + FUNDING_INTERVAL_MS

                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                logger.warning(f"Funding fetch error at {current_start}: {e}")
                break

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df['funding_ts'] = pd.to_datetime(pd.to_numeric(df['fundingTime']), unit='ms')
        df['funding_rate_binance'] = pd.to_numeric(df['fundingRate'])

        # Remove duplicates
        df = df.drop_duplicates(subset=['fundingTime'], keep='first')

        return df[['funding_ts', 'funding_rate_binance']]

    # ============================================
    # 6. Liquidations (Binance)
    # ============================================

    def fetch_liquidations_binance(self, start_time: int, end_time: int) -> pd.DataFrame:
        """
        Fetch Liquidations from Binance
        Returns: long_notional, short_notional, long_count, short_count
        """
        url = f"{self.BINANCE_BASE}/fapi/v1/allForceOrders"

        params = {
            'symbol': self.symbol,
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1000
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            df = pd.DataFrame(data)

            if df.empty:
                return pd.DataFrame()

            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df['price'] = pd.to_numeric(df['price'])
            df['origQty'] = pd.to_numeric(df['origQty'])
            df['notional'] = df['price'] * df['origQty']

            # Separate long/short
            df_long = df[df['side'] == 'SELL']  # Long liquidation = sell
            df_short = df[df['side'] == 'BUY']  # Short liquidation = buy

            # Aggregate by timeframe
            # (Group by open_time bins)
            # Simplified: return raw for now
            return df[['time', 'side', 'notional']]

        except Exception as e:
            logger.warning(f"Liquidations fetch error: {e}")
            return pd.DataFrame()

    # ============================================
    # 7. Order Book Snapshot (Binance)
    # ============================================

    def attach_ob_to_nearest_bar(self, df: pd.DataFrame, ob_snapshot: Dict) -> pd.DataFrame:
        """
        Attach OB snapshot to the nearest bar with age/phase tracking

        Logic:
        - Find nearest bar to ob_ts (using close_time_ms)
        - Calculate age = |ob_ts - bar_close_ms|
        - Determine phase: 'pre' if ob before bar close, 'post' if after
        - Only attach if age <= max_age (TF-dependent threshold)
        - Add has_ob flag for filtering
        """
        if not ob_snapshot or df.empty:
            return df

        # Timeframe-based threshold
        TF_MS = {'1m': 60_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000,
                 '1h': 3_600_000, '4h': 14_400_000, '1d': 86_400_000, '1w': 604_800_000, '1M': 2_592_000_000}
        tf_ms = TF_MS.get(self.timeframe, 300_000)
        max_age = min(180_000, tf_ms // 2)  # e.g., 5m → 150 sec

        ob_ts = ob_snapshot.get('ob_ts')
        if not ob_ts:
            return df

        # Ensure close_time_ms exists
        if 'close_time_ms' not in df.columns:
            if 'close_time' in df.columns:
                # Convert close_time to ms
                if pd.api.types.is_datetime64_any_dtype(df['close_time']):
                    df['close_time_ms'] = (df['close_time'].astype('int64') // 10**6).astype('Int64')
                else:
                    df['close_time_ms'] = pd.to_numeric(df['close_time'], errors='coerce').astype('Int64')
            else:
                logger.warning("Cannot attach OB: close_time(_ms) column missing")
                return df

        # Find nearest bar using binary search
        close_times = df['close_time_ms'].to_numpy()
        import numpy as np

        pos = np.searchsorted(close_times, ob_ts, side='left')
        candidates = []

        if pos < len(close_times):
            age = abs(close_times[pos] - ob_ts)
            candidates.append((age, pos))
        if pos > 0:
            age = abs(close_times[pos-1] - ob_ts)
            candidates.append((age, pos-1))

        if not candidates:
            return df

        best_age, best_idx = min(candidates)
        bar_close_ms = close_times[best_idx]
        delta = ob_ts - bar_close_ms
        phase = 'pre' if delta < 0 else 'post'

        # Initialize OB columns with NaN
        for key in ob_snapshot.keys():
            if key not in df.columns:
                df[key] = pd.NA

        df['has_ob'] = False
        df['ob_age_ms'] = pd.NA
        df['ob_phase'] = pd.NA

        # Attach OB to nearest bar if within threshold
        if best_age <= max_age:
            for key, val in ob_snapshot.items():
                df.at[best_idx, key] = val
            df.at[best_idx, 'has_ob'] = True
            df.at[best_idx, 'ob_age_ms'] = int(best_age)
            df.at[best_idx, 'ob_phase'] = phase
            logger.info(f"   ✅ OB attached to bar #{best_idx}: age={best_age}ms ({phase}), within threshold ({max_age}ms)")
        else:
            logger.info(f"   ⚠️  OB snapshot too old: age={best_age}ms ({phase}), threshold={max_age}ms - not attached")

        return df

    def fetch_order_book_snapshot(self) -> Dict:
        """
        Fetch current Order Book snapshot
        Returns 11 metrics (ML-ready schema):
        - best_bid, best_ask, spread, microprice
        - ob_depth5_bid, ob_depth5_ask, ob_depth10_bid, ob_depth10_ask
        - ob_imbalance, ob_ts, ob_source
        """
        # Market-aware URL
        if self.market == 'futures':
            url = f"{self.BINANCE_BASE}/fapi/v1/depth"
        else:  # spot
            url = "https://api.binance.com/api/v3/depth"

        params = {
            'symbol': self.symbol,
            'limit': 20
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            now_ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

            bids = pd.DataFrame(data['bids'], columns=['price', 'qty']).astype(float)
            asks = pd.DataFrame(data['asks'], columns=['price', 'qty']).astype(float)

            best_bid = bids.iloc[0]['price']
            best_ask = asks.iloc[0]['price']

            # Spread
            spread = best_ask - best_bid

            # Microprice (volume-weighted mid)
            bid_qty = bids.iloc[0]['qty']
            ask_qty = asks.iloc[0]['qty']
            microprice = (best_bid * ask_qty + best_ask * bid_qty) / (bid_qty + ask_qty)

            # Depth (separate bid/ask for ML features)
            ob_depth5_bid = bids.head(5)['qty'].sum()
            ob_depth5_ask = asks.head(5)['qty'].sum()
            ob_depth10_bid = bids.head(10)['qty'].sum()
            ob_depth10_ask = asks.head(10)['qty'].sum()

            # Imbalance (using depth10)
            denom = ob_depth10_bid + ob_depth10_ask
            ob_imbalance = (ob_depth10_bid - ob_depth10_ask) / denom if denom > 0 else 0.0

            return {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': spread,
                'microprice': microprice,
                'ob_depth5_bid': ob_depth5_bid,
                'ob_depth5_ask': ob_depth5_ask,
                'ob_depth10_bid': ob_depth10_bid,
                'ob_depth10_ask': ob_depth10_ask,
                'ob_imbalance': ob_imbalance,
                'ob_ts': now_ts_ms,
                'ob_source': 'binance'
            }

        except Exception as e:
            logger.warning(f"Order book fetch error: {e}")
            return {}

    # ============================================
    # 8. ICT Session Labels
    # ============================================

    def add_ict_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add ICT kill-zone labels
        Based on Europe/Istanbul timezone, converted to UTC

        Sessions:
        - Asia: 00:00-04:00 UTC
        - London: 08:00-12:00 UTC
        - NY AM: 13:00-17:00 UTC
        - NY PM: 17:00-21:00 UTC
        """
        df['hour_utc'] = df['open_time'].dt.hour

        df['is_kz_asia'] = (df['hour_utc'] >= 0) & (df['hour_utc'] < 4)
        df['is_kz_london'] = (df['hour_utc'] >= 8) & (df['hour_utc'] < 12)
        df['is_kz_ny_am'] = (df['hour_utc'] >= 13) & (df['hour_utc'] < 17)
        df['is_kz_ny_pm'] = (df['hour_utc'] >= 17) & (df['hour_utc'] < 21)

        # Session label
        df['session_label'] = 'other'
        df.loc[df['is_kz_asia'], 'session_label'] = 'asia'
        df.loc[df['is_kz_london'], 'session_label'] = 'london'
        df.loc[df['is_kz_ny_am'], 'session_label'] = 'ny_am'
        df.loc[df['is_kz_ny_pm'], 'session_label'] = 'ny_pm'

        return df

    # ============================================
    # Main Collection
    # ============================================

    def collect_all(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Collect all data layers

        Supports incremental downloads:
        - If output_path exists, loads existing data
        - Downloads only new data from the last timestamp
        - Merges old and new data
        - Removes duplicates and sorts by time

        Returns comprehensive DataFrame with all features
        """
        logger.info(f"🚀 Starting comprehensive data collection...")

        # ============================================
        # INCREMENTAL DOWNLOAD: Check existing data
        # ============================================
        existing_df = None
        original_start_date = start_date

        if output_path and Path(output_path).exists():
            logger.info(f"📂 Found existing data: {output_path}")
            try:
                existing_df = pd.read_parquet(output_path)

                if not existing_df.empty and 'open_time' in existing_df.columns:
                    # Convert to datetime if needed
                    if not pd.api.types.is_datetime64_any_dtype(existing_df['open_time']):
                        existing_df['open_time'] = pd.to_datetime(existing_df['open_time'])

                    last_timestamp = existing_df['open_time'].max()
                    logger.info(f"   📅 Existing data: {len(existing_df)} rows")
                    logger.info(f"   📅 Last timestamp: {last_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                    # Resume from the next candle after the last one
                    # Add 1 millisecond to avoid duplicate
                    resume_ts = int(last_timestamp.timestamp() * 1000) + 1
                    resume_date = datetime.fromtimestamp(resume_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d')

                    logger.info(f"   ♻️  Resuming from: {resume_date}")
                    start_date = resume_date
                else:
                    logger.info(f"   ⚠️  Existing file is empty or malformed, re-downloading all data")
                    existing_df = None
            except Exception as e:
                logger.warning(f"   ⚠️  Could not read existing file: {e}")
                logger.info(f"   🔄 Re-downloading all data from {original_start_date}")
                existing_df = None

        # Parse dates
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)

        if end_date:
            end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)
        else:
            end_ts = int(datetime.now(timezone.utc).timestamp() * 1000)

        # Check if we need to download anything
        if existing_df is not None and start_ts >= end_ts:
            logger.info(f"   ✅ Data is already up-to-date!")
            logger.info(f"   📊 Using existing data: {len(existing_df)} rows")
            return existing_df

        # 1. Fetch OHLCV
        logger.info("   📈 Fetching OHLCV...")
        df = self.fetch_ohlcv_binance(start_ts, end_ts)

        if df.empty:
            logger.error("   ❌ No OHLCV data")
            return pd.DataFrame()

        logger.info(f"   ✅ OHLCV: {len(df)} candles")

        # Get actual data start time (use first candle timestamp for OI/Funding)
        # This ensures we don't request OI/Funding for dates before the coin existed
        actual_start_ts = int(df['open_time'].min().timestamp() * 1000)
        logger.info(f"   📅 Data starts: {df['open_time'].min().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # 2. Order Book (snapshot attached to nearest bar with age/phase tracking)
        logger.info("   📖 Fetching Order Book snapshot...")
        ob = self.fetch_order_book_snapshot()
        if ob:
            df = self.attach_ob_to_nearest_bar(df, ob)

        # 3. Volatility
        logger.info("   📊 Calculating volatility...")
        df = self.calculate_volatility(df)

        # 4. CVD
        logger.info("   💹 Calculating CVD...")
        df = self.calculate_cvd(df)

        # 5. Open Interest (Futures only)
        if self.market == 'futures':
            logger.info("   🔓 Fetching Open Interest...")

            # Binance OI - use actual_start_ts (from first OHLCV candle)
            oi_df = self.fetch_open_interest_binance(actual_start_ts, end_ts)
            if not oi_df.empty:
                df = df.merge(oi_df, left_on='open_time', right_on='timestamp', how='left')
                logger.info(f"   ✅ OI Binance: {oi_df['oi_binance'].notna().sum()} records")

            # Bybit OI
            if 'bybit' in self.exchanges and BybitAPI:
                bybit_api = BybitAPI(self.symbol, self.timeframe)
                oi_bybit_df = bybit_api.fetch_open_interest(actual_start_ts, end_ts)
                if not oi_bybit_df.empty:
                    df = df.merge(oi_bybit_df, left_on='open_time', right_on='timestamp', how='left', suffixes=('', '_bybit'))
                    logger.info(f"   ✅ OI Bybit: {oi_bybit_df['oi_bybit'].notna().sum()} records")
        else:
            logger.info("   ⏭️  Skipping Open Interest (spot market)")

        # 6. Funding Rate (Futures only)
        if self.market == 'futures':
            logger.info("   💰 Fetching Funding Rate...")

            # Binance Funding
            funding_df = self.fetch_funding_rate_binance(actual_start_ts, end_ts)
            if not funding_df.empty:
                df = pd.merge_asof(
                    df.sort_values('open_time'),
                    funding_df.sort_values('funding_ts'),
                    left_on='open_time',
                    right_on='funding_ts',
                    direction='backward'
                )
                logger.info(f"   ✅ Funding Binance: {funding_df['funding_rate_binance'].notna().sum()} records")

            # Bybit Funding
            if 'bybit' in self.exchanges and BybitAPI:
                bybit_api = BybitAPI(self.symbol, self.timeframe)
                funding_bybit_df = bybit_api.fetch_funding_rate(actual_start_ts, end_ts)
                if not funding_bybit_df.empty:
                    df = pd.merge_asof(
                        df.sort_values('open_time'),
                        funding_bybit_df.sort_values('funding_ts'),
                        left_on='open_time',
                        right_on='funding_ts',
                        direction='backward',
                        suffixes=('', '_bybit')
                    )
                    logger.info(f"   ✅ Funding Bybit: {funding_bybit_df['funding_rate_bybit'].notna().sum()} records")
        else:
            logger.info("   ⏭️  Skipping Funding Rate (spot market)")

        # 7. ICT Sessions
        logger.info("   ⏰ Adding ICT sessions...")
        df = self.add_ict_sessions(df)

        # ============================================
        # INCREMENTAL DOWNLOAD: Merge with existing data
        # ============================================
        if existing_df is not None and not existing_df.empty:
            logger.info(f"\n🔀 Merging with existing data...")
            logger.info(f"   Old data: {len(existing_df)} rows")
            logger.info(f"   New data: {len(df)} rows")

            # Combine old and new data
            df_combined = pd.concat([existing_df, df], ignore_index=True)

            # Remove duplicates (keep last occurrence = newer data)
            # Convert to datetime if needed for comparison
            if not pd.api.types.is_datetime64_any_dtype(df_combined['open_time']):
                df_combined['open_time'] = pd.to_datetime(df_combined['open_time'])

            df_combined = df_combined.drop_duplicates(subset=['open_time'], keep='last')

            # Sort by time
            df_combined = df_combined.sort_values('open_time').reset_index(drop=True)

            logger.info(f"   Combined: {len(df_combined)} rows (removed {len(existing_df) + len(df) - len(df_combined)} duplicates)")

            df = df_combined

        # Save
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"\n💾 Saved: {output_path}")

        logger.info(f"\n✅ Collection complete!")
        logger.info(f"   Total columns: {len(df.columns)}")
        logger.info(f"   Total rows: {len(df)}")

        return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Advanced Multi-Exchange Data Collector')
    parser.add_argument('--symbols', type=str, default='BTCUSDT',
                        help='Comma-separated symbols (e.g., BTCUSDT,ETHUSDT)')
    parser.add_argument('--timeframe', type=str, default='1h')
    parser.add_argument('--market', type=str, default='futures', choices=['spot', 'futures'],
                        help='Market type: spot or futures (default: futures)')
    parser.add_argument('--exchanges', type=str, default='binance,bybit',
                        help='Comma-separated exchanges (e.g., binance,bybit)')
    parser.add_argument('--start-date', type=str, default='auto',
                        help='Start date (YYYY-MM-DD) or "auto" for earliest available data')
    parser.add_argument('--end-date', type=str, default=None)
    parser.add_argument('--output-dir', type=str, default='data/advanced')

    # Feature toggles (not implemented yet but for future use)
    parser.add_argument('--no-volatility', action='store_true', help='Skip volatility features')
    parser.add_argument('--no-cvd', action='store_true', help='Skip CVD features')
    parser.add_argument('--no-oi', action='store_true', help='Skip Open Interest')
    parser.add_argument('--no-funding', action='store_true', help='Skip Funding Rate')
    parser.add_argument('--include-liquidations', action='store_true', help='Include liquidations')
    parser.add_argument('--no-orderbook', action='store_true', help='Skip Order Book')
    parser.add_argument('--no-sessions', action='store_true', help='Skip ICT sessions')
    parser.add_argument('--parallel', action='store_true', help='Enable parallel download (faster)')
    parser.add_argument('--max-workers', type=int, default=3, help='Max parallel workers (default: 3)')

    args = parser.parse_args()

    # Parse symbols and exchanges
    symbols_list = [s.strip().upper() for s in args.symbols.split(',')]
    exchanges_list = [e.strip().lower() for e in args.exchanges.split(',')]

    # Auto start date detection (market and exchange aware)
    if args.start_date == 'auto':
        # Different markets have different launch dates
        # Use earliest date for selected market, API will find actual first candle
        if args.market == 'spot':
            # Binance SPOT launched 2017-07-14
            # Most altcoins listed much later, but BTC/ETH available from start
            start_date_resolved = '2017-07-01'
            logger.info(f"🔍 Auto mode: Using earliest SPOT date (2017-07-01, Binance launch)")
        else:  # futures
            # Binance USDT Futures launched 2019-09-09
            # Most coins listed later, but we use early date for safety
            start_date_resolved = '2019-01-01'
            logger.info(f"🔍 Auto mode: Using earliest FUTURES date (2019-01-01, before Binance Futures launch)")

        logger.info(f"   💡 Note: Actual start will be from first available candle for each coin")
    else:
        start_date_resolved = args.start_date

    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 Advanced Data Collection Starting")
    logger.info(f"{'='*60}")
    logger.info(f"   Symbols: {', '.join(symbols_list)}")
    logger.info(f"   Timeframe: {args.timeframe}")
    logger.info(f"   Market: {args.market.upper()}")
    logger.info(f"   Exchanges: {', '.join(exchanges_list)}")
    logger.info(f"   Date range: {start_date_resolved} → {args.end_date or 'today'}")
    logger.info(f"   Parallel: {'✅ Enabled (' + str(args.max_workers) + ' workers)' if args.parallel else '❌ Disabled (sequential)'}")
    logger.info(f"{'='*60}\n")

    # Worker function for parallel processing
    def process_symbol(symbol: str, idx: int, total: int):
        """Process single symbol (runs in thread)"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 [{idx}/{total}] Processing {symbol} ({args.market.upper()})")
        logger.info(f"{'='*60}\n")

        try:
            collector = AdvancedDataCollector(
                symbol=symbol,
                timeframe=args.timeframe,
                market=args.market,
                exchanges=exchanges_list
            )

            output_path = f"{args.output_dir}/{symbol}_{args.timeframe}_{args.market}_multi.parquet"

            df = collector.collect_all(
                start_date=start_date_resolved,  # Use resolved date (auto → 2019-01-01)
                end_date=args.end_date,
                output_path=output_path
            )

            logger.info(f"\n✅ {symbol} complete!")
            logger.info(f"   Rows: {len(df):,}")
            logger.info(f"   Columns: {len(df.columns)}")
            logger.info(f"   File: {output_path}")

            return {"symbol": symbol, "status": "success", "rows": len(df), "path": output_path}

        except Exception as e:
            logger.error(f"\n❌ {symbol} failed: {e}")
            import traceback
            traceback.print_exc()
            return {"symbol": symbol, "status": "failed", "error": str(e)}

    # Process symbols
    results = []

    if args.parallel:
        # Parallel processing (even for 1 symbol, it's consistent behavior)
        logger.info(f"⚡ Parallel mode enabled ({args.max_workers} workers)...\n")

        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(process_symbol, symbol, idx+1, len(symbols_list)): symbol
                for idx, symbol in enumerate(symbols_list)
            }

            # Wait for completion
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
    else:
        # Sequential processing
        logger.info(f"🐌 Sequential download (use --parallel for faster processing)...\n")

        for idx, symbol in enumerate(symbols_list):
            result = process_symbol(symbol, idx+1, len(symbols_list))
            results.append(result)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ All downloads complete!")
    logger.info(f"{'='*60}")

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count

    logger.info(f"   Success: {success_count}/{len(results)}")
    if failed_count > 0:
        logger.info(f"   Failed: {failed_count}")
        logger.info(f"   Failed symbols: {', '.join([r['symbol'] for r in results if r['status'] == 'failed'])}")

    logger.info(f"{'='*60}\n")
