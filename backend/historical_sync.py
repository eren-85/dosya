# -*- coding: utf-8 -*-
"""
Historical sync utilities.
- Spot & Futures Binance kline indirici
- CSV ve opsiyonel Parquet yazma
- Mevcut dosyadan "kaldığı yerden devam" (resume)
- Global tek progress bar (çok sembol/çok batch)
"""

from __future__ import annotations
import os
import csv
import math
import time
import json
import pathlib
import datetime as dt
from typing import Iterable, List, Optional, Tuple

try:
    import requests
except Exception as _:
    requests = None

# Parquet/CSV yazımı için opsiyonel pandas
def _lazy_pd():
    try:
        import pandas as pd  # type: ignore
        return pd
    except Exception:
        return None

# Progress bar: tqdm yoksa basit fallback
class _Bar:
    def __init__(self, total: int, desc: str = ""):
        self.total = max(int(total), 0)
        self.n = 0
        self.desc = desc
        self._use_tqdm = False
        try:
            from tqdm import tqdm  # type: ignore
            self._use_tqdm = True
            self._bar = tqdm(total=self.total, desc=self.desc, dynamic_ncols=True, leave=False)
        except Exception:
            self._bar = None
            print(f"{self.desc} 0/{self.total}")

    def update(self, inc: int = 1):
        self.n += inc
        if self._use_tqdm:
            self._bar.update(inc)
        else:
            # tek satır güncelleme
            done = min(self.n, self.total)
            print(f"\r{self.desc} {done}/{self.total}", end="")

    def close(self):
        if self._use_tqdm:
            self._bar.close()
        else:
            print()

# ---- Helpers ----

INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
    "1M": 2_592_000_000,  # approx (30d)
}

def _ensure_dir(p: str) -> None:
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)

def _utc_iso(ms: int) -> str:
    return dt.datetime.utcfromtimestamp(ms / 1000.0).replace(tzinfo=dt.timezone.utc).isoformat()

def _now_ms() -> int:
    return int(time.time() * 1000)

def _binance_base(market: str) -> str:
    if market == "futures":
        return "https://fapi.binance.com"
    return "https://api.binance.com"

def _klines_endpoint(market: str) -> str:
    return "/fapi/v1/klines" if market == "futures" else "/api/v3/klines"

def _fetch_klines(symbol: str, interval: str, start_ms: int, end_ms: int, market: str, limit: int = 1000) -> List[list]:
    if requests is None:
        raise RuntimeError("requests gereklidir.")
    base = _binance_base(market)
    url = base + _klines_endpoint(market)
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": start_ms,
        "endTime": end_ms,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def _csv_path(base_dir: str, symbol: str, interval: str, market: str) -> str:
    return os.path.join(base_dir, f"{symbol}_{interval}_{market}.csv")

def _parquet_path(base_dir: str, symbol: str, interval: str, market: str) -> str:
    return os.path.join(base_dir, f"{symbol}_{interval}_{market}.parquet")

def _last_close_ms_from_csv(path: str) -> Optional[int]:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    last = None
    with open(path, "r", newline="", encoding="utf-8") as f:
        rd = csv.reader(f)
        header = next(rd, None)
        # CSV formatı: open_time,open,high,low,close,volume,close_time, ...
        for row in rd:
            if not row:
                continue
            # close_time = row[6]
            try:
                close_ms = int(float(row[6]))
                last = close_ms
            except Exception:
                # fallback: open_time
                try:
                    last = int(float(row[0])) + (INTERVAL_MS.get(row[1], 0))
                except Exception:
                    pass
    return last

def _last_close_ms_from_parquet(path: str) -> Optional[int]:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    pd = _lazy_pd()
    if pd is None:
        return None
    try:
        df = pd.read_parquet(path, engine="pyarrow")
        # varsa 'close_time' sütunu tercih et, yoksa open_time + interval
        if "close_time" in df.columns:
            return int(df["close_time"].iloc[-1])
        elif "open_time" in df.columns:
            return int(df["open_time"].iloc[-1])
    except Exception:
        return None
    return None

def _read_resume_point(base_dir: str, symbol: str, interval: str, market: str) -> Optional[int]:
    p_parq = _parquet_path(base_dir, symbol, interval, market)
    p_csv = _csv_path(base_dir, symbol, interval, market)
    last = _last_close_ms_from_parquet(p_parq)
    if last is None:
        last = _last_close_ms_from_csv(p_csv)
    return last

def _append_csv(path: str, rows: List[list]) -> int:
    if not rows:
        return 0
    _ensure_dir(path)
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        if write_header:
            wr.writerow(["open_time","open","high","low","close","volume","close_time","quote_asset_volume","trades","taker_base","taker_quote","ignore"])
        for k in rows:
            wr.writerow(k[:12])
    return len(rows)

def _save_parquet_full(path: str, csv_path: str) -> None:
    pd = _lazy_pd()
    if pd is None:
        return
    df = pd.read_csv(csv_path)
    _ensure_dir(path)
    df.to_parquet(path, index=False)

def _append_parquet_incremental(parquet_path: str, added_csv_rows: List[list]) -> None:
    pd = _lazy_pd()
    if pd is None or not added_csv_rows:
        return
    import pandas as pd2  # not strictly needed—just alias
    cols = ["open_time","open","high","low","close","volume","close_time","quote_asset_volume","trades","taker_base","taker_quote","ignore"]
    new_df = pd.DataFrame(added_csv_rows, columns=cols)
    if os.path.exists(parquet_path) and os.path.getsize(parquet_path) > 0:
        old = pd.read_parquet(parquet_path, engine="pyarrow")
        df = pd.concat([old, new_df], ignore_index=True)
    else:
        df = new_df
    _ensure_dir(parquet_path)
    df.to_parquet(parquet_path, index=False)

def _estimate_batches(start_ms: int, end_ms: int, interval: str, limit: int = 1000) -> int:
    if start_ms >= end_ms:
        return 0
    step = INTERVAL_MS[interval]
    total_candles = max(0, (end_ms - start_ms) // step)
    return math.ceil(total_candles / limit)

# ---- Public API ----

def sync_historical(
    symbols: Iterable[str],
    interval: str,
    market: str,
    base_dir: str = "data/historical",
    parquet: bool = False,
    all_time: bool = False,
    start: Optional[str] = None,
    end: Optional[str] = None,
    global_progress: bool = True,
    request_limit: int = 1000,
) -> List[Tuple[str, int, int, int]]:
    """
    Her sembol için:
      - varsa yerel CSV/Parquet'ten son close_time alınır
      - yoksa ALL-TIME indirilir
      - CSV append + opsiyonel Parquet append
    Dönüş: [(symbol, first_ms, last_ms, added_rows), ...]
    """
    symbols = [s.strip() for s in symbols if s.strip()]
    os.makedirs(base_dir, exist_ok=True)
    now_ms = _now_ms()

    if start:
        start_ms = int(dt.datetime.fromisoformat(start).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    else:
        start_ms = 0
    if end:
        end_ms = int(dt.datetime.fromisoformat(end).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    else:
        end_ms = now_ms

    # Önce toplam batch sayısını tahmin edip tek bar açalım (global)
    total_batches = 0
    plan = []
    for sym in symbols:
        if all_time:
            s_ms = 0
        else:
            resume = _read_resume_point(base_dir, sym, interval, market)
            s_ms = resume + 1 if resume is not None else 0
        s_ms = max(s_ms, start_ms)
        e_ms = end_ms
        est = _estimate_batches(s_ms, e_ms, interval, limit=request_limit)
        total_batches += est
        plan.append((sym, s_ms, e_ms))

    bar = _Bar(total=total_batches, desc=f"Downloading {interval} {market}")

    results = []
    for sym, s_ms, e_ms in plan:
        first_seen = None
        last_seen = None
        added = 0
        csv_path = _csv_path(base_dir, sym, interval, market)
        parquet_path = _parquet_path(base_dir, sym, interval, market)

        cur = s_ms if (all_time or s_ms > 0) else 0
        if cur == 0:
            print(f"⏳ {sym}: no local file; downloading ALL-TIME…")
        else:
            print(f"⏳ {sym}: resuming from {_utc_iso(cur)}")

        step = INTERVAL_MS[interval]
        # güvenli bitiş kaydırma (Binance endTime inclusive değil)
        while cur < e_ms:
            batch_end = min(e_ms, cur + step * request_limit - 1)
            rows = _fetch_klines(sym, interval, cur, batch_end, market, limit=request_limit)
            if not rows:
                # ağ hızı/delay durumunda küçük gecikme
                time.sleep(0.2)
                bar.update(1)
                cur = batch_end + 1
                continue

            added += _append_csv(csv_path, rows)
            if parquet:
                _append_parquet_incremental(parquet_path, rows)

            if first_seen is None and rows:
                first_seen = int(rows[0][6])
            last_seen = int(rows[-1][6])

            bar.update(1)
            # sonraki batch başlangıcı
            cur = int(rows[-1][6]) + 1

            # çok hızlı istekleri biraz frenle (rate-limit dostu)
            time.sleep(0.05)

        if added > 0:
            print(f"💾 CSV updated: {os.path.abspath(csv_path)} (+{added} rows)")
            if parquet:
                print(f"💾 Parquet updated: {os.path.abspath(parquet_path)}")
        else:
            print(f"✅ {sym}: up to date. Nothing to append.")

        if first_seen is None:
            # hiçbir şey eklenmediyse mevcut aralığı hesapla
            last_local = _read_resume_point(base_dir, sym, interval, market)
            first_seen = last_local
            last_seen = last_local

        results.append((sym, first_seen or 0, last_seen or 0, added))

    bar.close()
    return results
