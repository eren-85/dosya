# -*- coding: utf-8 -*-
"""
Append-only Binance OHLCV synchronizer with ASCII progress bar (PowerShell-friendly).

Place this file at: backend/sync/historical_sync.py
Then import from CLI:
  from backend.sync.historical_sync import run_sync

Example usage integrated into CLI:
  python -m backend.cli sync -s BTCUSDT,ETHUSDT -i 4h -m spot --parquet
"""

from __future__ import annotations
import os, sys, math, csv, time, json, io
import pathlib
import typing as T
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

try:
    import pandas as pd  # optional
except Exception:
    pd = None

import requests

BINANCE_SPOT = "https://api.binance.com"
BINANCE_FUT  = "https://fapi.binance.com"

INTERVAL_TO_MS = {
    "1m": 60_000,
    "3m": 3*60_000,
    "5m": 5*60_000,
    "15m": 15*60_000,
    "30m": 30*60_000,
    "1h": 60*60_000,
    "2h": 2*60*60_000,
    "4h": 4*60*60_000,
    "6h": 6*60*60_000,
    "8h": 8*60*60_000,
    "12h": 12*60*60_000,
    "1d": 24*60*60_000,
    "3d": 3*24*60*60_000,
    "1w": 7*24*60*60_000,
    "1M": 30*24*60*60_000,  # Binance's monthly is variable; treat as 30d for progress estimation only
}

CSV_COLUMNS = [
    "open_time","open","high","low","close","volume",
    "close_time","quote_asset_volume","number_of_trades",
    "taker_buy_base","taker_buy_quote","ignore"
]

@dataclass
class SyncOptions:
    symbols: T.List[str]
    interval: str
    market: str             # 'spot' | 'futures'
    out_dir: str            # e.g. 'data/historical'
    parquet: bool = False   # if True, also write Parquet
    only_parquet: bool = False  # if True, skip CSV and only write Parquet
    batch_limit: int = 1000
    request_pause: float = 0.2   # seconds between requests (stay polite)
    timeout: int = 30            # http timeout per request

def _bn_base(market: str) -> str:
    return BINANCE_FUT if market.lower() == "futures" else BINANCE_SPOT

def _klines_url(market: str) -> str:
    base = _bn_base(market)
    path = "/fapi/v1/klines" if market.lower()=="futures" else "/api/v3/klines"
    return base + path

def _now_ms() -> int:
    return int(time.time()*1000)

def _ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).isoformat()

def _normalize_interval(iv: str) -> str:
    iv = iv.strip()
    if iv not in INTERVAL_TO_MS:
        raise ValueError(f"Unsupported interval: {iv}")
    return iv

def _full_path(out_dir: str, sym: str, interval: str, market: str, suffix: str) -> str:
    return os.path.join(out_dir, f"{sym}_{interval}_{market}.{suffix}")

def _read_last_close_ms(path_csv: str, path_parquet: str) -> T.Optional[int]:
    """
    Return last close_time (ms) from existing CSV or Parquet.
    Preference order: Parquet > CSV (because of speed).
    """
    if os.path.exists(path_parquet) and pd is not None:
        try:
            df = pd.read_parquet(path_parquet, columns=["close_time"])
            if len(df):
                return int(df["close_time"].iloc[-1])
        except Exception:
            pass
    if os.path.exists(path_csv):
        try:
            last = None
            with open(path_csv, "r", newline="") as f:
                # read last non-empty line
                for row in csv.DictReader(f):
                    last = row
            if last and "close_time" in last:
                return int(float(last["close_time"]))
        except Exception:
            pass
    return None

def _estimate_total_batches(start_ms: int, interval: str, market: str, limit: int) -> int:
    end_ms = _now_ms()
    step = INTERVAL_TO_MS[interval]
    if end_ms <= start_ms:
        return 1
    candles = (end_ms - start_ms) // step
    # batches = ceil(candles/1000) but ensure at least 1
    return max(1, math.ceil(candles / max(1, limit)))

def _ascii_bar(pct: float, width: int=28) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(round(width * pct / 100.0))
    return "[" + "█"*filled + "░"*(width - filled) + f"] {pct:5.1f}%"

def _progress_print(done_batches: int, total_batches: int) -> None:
    pct = (done_batches/total_batches)*100.0 if total_batches>0 else 100.0
    bar = _ascii_bar(pct)
    # ONE SINGLE LINE, carriage-return; avoid printing newline until finished
    sys.stdout.write("\r  " + bar + f"  ({done_batches}/{total_batches} batches)")
    sys.stdout.flush()

def _fetch_klines(symbol: str, interval: str, market: str, start_ms: int, limit: int=1000, timeout: int=30):
    url = _klines_url(market)
    params = {"symbol": symbol, "interval": interval, "limit": limit, "startTime": start_ms}
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    # Each kline: [ openTime, open, high, low, close, volume, closeTime, quoteAssetVolume, numTrades, takerBuyBase, takerBuyQuote, ignore ]
    return data

def _append_rows_csv(path_csv: str, rows: T.List[T.List[T.Any]]) -> None:
    exists = os.path.exists(path_csv)
    with open(path_csv, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(CSV_COLUMNS)
        for r in rows:
            w.writerow(r)

def _write_parquet(path_parquet: str, rows: T.List[T.List[T.Any]]) -> None:
    if pd is None:
        return
    cols = list(zip(*rows)) if rows else [[] for _ in range(len(CSV_COLUMNS))]
    # Build DataFrame column by column
    data = {col: list(vals) for col, vals in zip(CSV_COLUMNS, cols)}
    df = pd.DataFrame(data)
    if os.path.exists(path_parquet):
        # append by concat then write (fast enough for batch sizes)
        old = pd.read_parquet(path_parquet)
        df = pd.concat([old, df], ignore_index=True)
    df.to_parquet(path_parquet, index=False)

def _sync_one_symbol(opts: SyncOptions, symbol: str) -> None:
    out_dir = opts.out_dir
    os.makedirs(out_dir, exist_ok=True)
    csv_path = _full_path(out_dir, symbol, opts.interval, opts.market, "csv")
    pq_path  = _full_path(out_dir, symbol, opts.interval, opts.market, "parquet")

    last_close = _read_last_close_ms(csv_path, pq_path)
    if last_close is None:
        # ALL-TIME download: start from t=0; Binance will clamp to earliest available
        start_ms = 0
        action = "no local file; downloading ALL-TIME…"
    else:
        start_ms = last_close + 1
        action = f"resuming from {_ms_to_iso(start_ms)}"

    print(f"⏳ {symbol}: {action}")

    total_batches = _estimate_total_batches(start_ms, opts.interval, opts.market, opts.batch_limit)
    done = 0
    appended_rows = 0
    step = INTERVAL_TO_MS[opts.interval]

    cur_start = start_ms
    final_end_ms = _now_ms()

    while True:
        if cur_start >= final_end_ms:
            break
        batch = _fetch_klines(symbol, opts.interval, opts.market, cur_start, limit=opts.batch_limit, timeout=opts.timeout)
        if not batch:
            break
        # ensure strictly increasing
        rows = []
        max_close = None
        for k in batch:
            # k[6] is close_time
            if max_close is None or int(k[6]) > max_close:
                max_close = int(k[6])
            rows.append([
                int(k[0]), str(k[1]), str(k[2]), str(k[3]), str(k[4]), str(k[5]),
                int(k[6]), str(k[7]), int(k[8]), str(k[9]), str(k[10]), str(k[11])
            ])
        if rows:
            if not opts.only_parquet:
                _append_rows_csv(csv_path, rows)
            if opts.parquet or opts.only_parquet:
                _write_parquet(pq_path, rows)
            appended_rows += len(rows)
            cur_start = max_close + 1
        else:
            break

        done += 1
        # Progress bar
        _progress_print(done, total_batches)
        time.sleep(opts.request_pause)

        # update end horizon to "now" periodically to keep estimation honest
        if done % 10 == 0:
            final_end_ms = _now_ms()
            # Re-estimate total if we were far off (e.g., huge lag shrank)
            total_batches = max(done+1, _estimate_total_batches(cur_start, opts.interval, opts.market, opts.batch_limit))

        if done >= total_batches:
            # If our estimate was too low, stretch gracefully
            total_batches = done + 1

    # finalize progress line with newline
    if done:
        _progress_print(done, max(done, total_batches))
        sys.stdout.write("\n")

    if appended_rows == 0:
        print(f"✅ {symbol}: up to date. Nothing to append.")
    else:
        first_ms = None
        if os.path.exists(csv_path):
            try:
                # read first open_time quickly
                with open(csv_path, "r", newline="") as f:
                    rdr = csv.DictReader(f)
                    for r in rdr:
                        first_ms = int(float(r.get("open_time", 0)))
                        break
            except Exception:
                pass
        first_iso = _ms_to_iso(first_ms) if first_ms else "?"
        last_iso  = _ms_to_iso(cur_start) if cur_start else "?"
        dest = "Parquet only" if opts.only_parquet else ("CSV + Parquet" if opts.parquet else "CSV")
        print(f"💾 {dest} updated: {os.path.abspath(csv_path if not opts.only_parquet else pq_path)} (+{appended_rows} rows)")
        print(f"✅ {symbol}: {first_iso} → {last_iso} | +{appended_rows} rows")

def run_sync(options: SyncOptions) -> None:
    print("\\n🧭 Historical Sync")
    print(f"Market:   {options.market}")
    print(f"Symbols:  {', '.join(options.symbols)}")
    print(f"Interval: {options.interval}")
    print(f"Output:   {'Parquet only' if options.only_parquet else ('CSV + Parquet' if options.parquet else 'CSV')}")
    print("")
    for sym in options.symbols:
        _sync_one_symbol(options, sym)

# Simple adapter for CLI layer
def sync_from_cli(symbols: str, interval: str, market: str, out_dir: str, parquet: bool, only_parquet: bool) -> None:
    opts = SyncOptions(
        symbols=[s.strip() for s in symbols.split(",") if s.strip()],
        interval=_normalize_interval(interval),
        market=market.lower(),
        out_dir=out_dir,
        parquet=parquet,
        only_parquet=only_parquet,
    )
    run_sync(opts)
