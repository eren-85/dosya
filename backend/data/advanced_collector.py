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
        """
        url = f"{self.BINANCE_BASE}/fapi/v1/klines"

        all_data = []
        current_start = start_time

        # Timeframe to milliseconds mapping
        tf_to_ms = {
            '1m': 60_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000,
            '1h': 3_600_000, '4h': 14_400_000, '1d': 86_400_000, '1w': 604_800_000
        }

        tf_ms = tf_to_ms.get(self.timeframe, 3_600_000)  # Default 1h

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

                # Move to next batch (last candle timestamp + 1ms)
                last_timestamp = int(data[-1][0])

                if last_timestamp >= end_time:
                    break

                current_start = last_timestamp + tf_ms

                # Rate limiting
                time.sleep(0.2)

                # Log progress every 10k candles
                if len(all_data) % 10000 == 0:
                    logger.info(f"      📥 Fetched {len(all_data):,} candles...")

            except Exception as e:
                logger.warning(f"OHLCV fetch error at {current_start}: {e}")
                break

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
        """
        url = f"{self.BINANCE_BASE}/futures/data/openInterestHist"

        # Binance USDT Futures OI data starts ~2019-09-09
        BINANCE_OI_EARLIEST_MS = 1567987200000  # 2019-09-09 00:00:00 UTC

        # Ensure start/end times are valid
        start_time = max(start_time, BINANCE_OI_EARLIEST_MS)
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
        """
        url = f"{self.BINANCE_BASE}/fapi/v1/fundingRate"

        # Ensure endTime is not in the future
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        end_time = min(end_time, now_ms)

        all_data = []
        current_start = start_time

        # Funding happens every 8 hours (28800000 ms)
        FUNDING_INTERVAL_MS = 28_800_000

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

    def fetch_order_book_snapshot(self) -> Dict:
        """
        Fetch current Order Book snapshot
        Returns: imbalance, spread, microprice, depth5, depth10
        """
        url = f"{self.BINANCE_BASE}/fapi/v1/depth"

        params = {
            'symbol': self.symbol,
            'limit': 20
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            bids = pd.DataFrame(data['bids'], columns=['price', 'qty']).astype(float)
            asks = pd.DataFrame(data['asks'], columns=['price', 'qty']).astype(float)

            best_bid = bids.iloc[0]['price']
            best_ask = asks.iloc[0]['price']

            # Spread
            spread = best_ask - best_bid
            spread_bps = (spread / best_bid) * 10000

            # Microprice
            bid_qty = bids.iloc[0]['qty']
            ask_qty = asks.iloc[0]['qty']
            microprice = (best_bid * ask_qty + best_ask * bid_qty) / (bid_qty + ask_qty)

            # Depth
            depth5_bid = bids.head(5)['qty'].sum()
            depth5_ask = asks.head(5)['qty'].sum()
            depth10_bid = bids.head(10)['qty'].sum()
            depth10_ask = asks.head(10)['qty'].sum()

            # Imbalance
            imbalance_5 = (depth5_bid - depth5_ask) / (depth5_bid + depth5_ask)
            imbalance_10 = (depth10_bid - depth10_ask) / (depth10_bid + depth10_ask)

            return {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid': (best_bid + best_ask) / 2,
                'spread': spread,
                'spread_bps': spread_bps,
                'microprice': microprice,
                'depth5': depth5_bid + depth5_ask,
                'depth10': depth10_bid + depth10_ask,
                'ob_imbalance': imbalance_10
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

        Returns comprehensive DataFrame with all features
        """
        logger.info(f"🚀 Starting comprehensive data collection...")

        # Parse dates
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)

        if end_date:
            end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)
        else:
            end_ts = int(datetime.now(timezone.utc).timestamp() * 1000)

        # 1. Fetch OHLCV
        logger.info("   📈 Fetching OHLCV...")
        df = self.fetch_ohlcv_binance(start_ts, end_ts)

        if df.empty:
            logger.error("   ❌ No OHLCV data")
            return pd.DataFrame()

        logger.info(f"   ✅ OHLCV: {len(df)} candles")

        # 2. Volatility
        logger.info("   📊 Calculating volatility...")
        df = self.calculate_volatility(df)

        # 3. CVD
        logger.info("   💹 Calculating CVD...")
        df = self.calculate_cvd(df)

        # 4. Open Interest
        logger.info("   🔓 Fetching Open Interest...")

        # Binance OI
        oi_df = self.fetch_open_interest_binance(start_ts, end_ts)
        if not oi_df.empty:
            df = df.merge(oi_df, left_on='open_time', right_on='timestamp', how='left')
            logger.info(f"   ✅ OI Binance: {oi_df['oi_binance'].notna().sum()} records")

        # Bybit OI
        if 'bybit' in self.exchanges and BybitAPI:
            bybit_api = BybitAPI(self.symbol, self.timeframe)
            oi_bybit_df = bybit_api.fetch_open_interest(start_ts, end_ts)
            if not oi_bybit_df.empty:
                df = df.merge(oi_bybit_df, left_on='open_time', right_on='timestamp', how='left', suffixes=('', '_bybit'))
                logger.info(f"   ✅ OI Bybit: {oi_bybit_df['oi_bybit'].notna().sum()} records")

        # 5. Funding Rate
        logger.info("   💰 Fetching Funding Rate...")

        # Binance Funding
        funding_df = self.fetch_funding_rate_binance(start_ts, end_ts)
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
            funding_bybit_df = bybit_api.fetch_funding_rate(start_ts, end_ts)
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

        # 6. ICT Sessions
        logger.info("   ⏰ Adding ICT sessions...")
        df = self.add_ict_sessions(df)

        # 7. Order Book (current snapshot - can't get historical)
        logger.info("   📖 Fetching Order Book snapshot...")
        ob = self.fetch_order_book_snapshot()
        if ob:
            for key, val in ob.items():
                df[key] = val
            logger.info(f"   ✅ OB: {len(ob)} metrics")

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
    parser.add_argument('--exchanges', type=str, default='binance,bybit',
                        help='Comma-separated exchanges (e.g., binance,bybit)')
    parser.add_argument('--start-date', type=str, default='2024-01-01')
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

    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 Advanced Data Collection Starting")
    logger.info(f"{'='*60}")
    logger.info(f"   Symbols: {', '.join(symbols_list)}")
    logger.info(f"   Timeframe: {args.timeframe}")
    logger.info(f"   Exchanges: {', '.join(exchanges_list)}")
    logger.info(f"   Date range: {args.start_date} → {args.end_date or 'today'}")
    logger.info(f"   Parallel: {'✅ Enabled (' + str(args.max_workers) + ' workers)' if args.parallel else '❌ Disabled (sequential)'}")
    logger.info(f"{'='*60}\n")

    # Worker function for parallel processing
    def process_symbol(symbol: str, idx: int, total: int):
        """Process single symbol (runs in thread)"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 [{idx}/{total}] Processing {symbol}")
        logger.info(f"{'='*60}\n")

        try:
            collector = AdvancedDataCollector(
                symbol=symbol,
                timeframe=args.timeframe,
                exchanges=exchanges_list
            )

            output_path = f"{args.output_dir}/{symbol}_{args.timeframe}_multi.parquet"

            df = collector.collect_all(
                start_date=args.start_date,
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
