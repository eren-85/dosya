
# backend/derived_timeframes.py
# Incremental resampling to build derived timeframes (e.g., 2h, 3h, 12h, 3d)
from __future__ import annotations

import os
from typing import Iterable, List, Dict, Optional, Tuple

import pandas as pd

# ---- Helpers -----------------------------------------------------------------

_RULES = {
    "5m": "5T",
    "15m": "15T",
    "30m": "30T",
    "1h": "1H",
    "2h": "2H",
    "3h": "3H",
    "4h": "4H",
    "12h": "12H",
    "1d": "1D",
    "3d": "3D",
    # Weekly ends on Sunday 00:00 UTC (Pandas default W-SUN)
    "1w": "1W-SUN",
    # Month-end frequency
    "1M": "M",
}

def _rule(tf: str) -> str:
    if tf not in _RULES:
        raise ValueError(f"Unsupported timeframe: {tf}")
    return _RULES[tf]

def _fname(base_dir: str, symbol: str, tf: str, market: str, ext: str) -> str:
    return os.path.join(base_dir, f"{symbol}_{tf}_{market}.{ext}")

def _read_any(base_dir: str, symbol: str, tf: str, market: str) -> Optional[pd.DataFrame]:
    """Read OHLCV from parquet if exists, else CSV; returns UTC-indexed DataFrame or None."""
    pq = _fname(base_dir, symbol, tf, market, "parquet")
    cs = _fname(base_dir, symbol, tf, market, "csv")
    if os.path.exists(pq):
        df = pd.read_parquet(pq)
    elif os.path.exists(cs):
        df = pd.read_csv(cs)
    else:
        return None
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp").sort_index()
    elif df.index.name != "timestamp":
        # Try to coerce index
        df.index = pd.to_datetime(df.index, utc=True)
        df.index.name = "timestamp"
        df = df.sort_index()
    # Ensure expected columns exist (at least ohlc + volume if available)
    return df

def _save(df: pd.DataFrame, base_dir: str, symbol: str, tf: str, market: str, parquet: bool = True) -> None:
    path_csv = _fname(base_dir, symbol, tf, market, "csv")
    path_pq  = _fname(base_dir, symbol, tf, market, "parquet")
    out = df.reset_index()
    out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    out.to_csv(path_csv, index=False)
    if parquet:
        df.to_parquet(path_pq)

def _agg_spec(columns: Iterable[str]) -> Dict[str, str]:
    cols = set(map(str.lower, columns))
    spec = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in cols:
        spec["volume"] = "sum"
    if "quote_volume" in cols:
        spec["quote_volume"] = "sum"
    if "trades" in cols or "number_of_trades" in cols:
        # map both to 'trades' on output if present
        if "trades" in cols:
            spec["trades"] = "sum"
        else:
            spec["number_of_trades"] = "sum"
    # Keep extra numeric columns by sum (optional)
    for c in columns:
        lc = str(c).lower()
        if lc not in spec and lc not in {"timestamp"}:
            # try to sum numeric extras
            spec[lc] = "sum"
    return spec

def _resample_ohlcv(df: pd.DataFrame, to_tf: str) -> pd.DataFrame:
    rule = _RULES[to_tf]
    # Normalize known columns casing
    rename_map = {}
    for c in df.columns:
        lc = c.lower()
        if lc in {"open","high","low","close","volume","quote_volume","trades","number_of_trades"} and c != lc:
            rename_map[c] = lc
    if rename_map:
        df = df.rename(columns=rename_map)

    agg = _agg_spec(df.columns)
    r = df.resample(rule, label="right", closed="right").agg(agg)
    # If both trades/number_of_trades existed, unify to trades
    if "number_of_trades" in r.columns and "trades" not in r.columns:
        r = r.rename(columns={"number_of_trades":"trades"})
    # Drop empty bars
    r = r.dropna(subset=["open","high","low","close"], how="any")
    r.index.name = "timestamp"
    return r

def _validate_divisibility(src_tf: str, dst_tf: str) -> None:
    ok = {
        "1h": {"2h","3h","12h"},
        "1d": {"3d"},
    }
    if dst_tf not in ok.get(src_tf, set()):
        raise ValueError(f"Unsupported conversion {src_tf} -> {dst_tf}. Supported: 1h→(2h,3h,12h), 1d→(3d).")

# ---- Public API ---------------------------------------------------------------

def derive_timeframes_for_symbol(
    base_dir: str,
    symbol: str,
    market: str,
    src_tf: str,
    dst_tfs: Iterable[str],
    parquet: bool = True,
) -> Dict[str, int]:
    """
    Incrementally derive dst_tfs from src_tf for a single symbol.
    Returns a dict of {dst_tf: rows_appended}.
    """
    # Read base (source) timeframe (required)
    src = _read_any(base_dir, symbol, src_tf, market)
    if src is None or src.empty:
        raise FileNotFoundError(f"No base file for {symbol} {src_tf} {market} under {base_dir}")

    results: Dict[str, int] = {}

    for dst_tf in dst_tfs:
        _validate_divisibility(src_tf, dst_tf)

        # Read existing derived (if any)
        existing = _read_any(base_dir, symbol, dst_tf, market)
        last_ts = None
        if existing is not None and not existing.empty:
            last_ts = existing.index.max()

        # Compute new aggregate
        if last_ts is None:
            candidate = _resample_ohlcv(src, dst_tf)
        else:
            # resample only after the last derived timestamp
            subset = src.loc[src.index > last_ts]
            if subset.empty:
                results[dst_tf] = 0
                continue
            candidate = _resample_ohlcv(subset, dst_tf)
            # Safety: ensure we don't create a partial bar that equals last_ts
            candidate = candidate.loc[candidate.index > last_ts]

        if candidate.empty:
            results[dst_tf] = 0
            continue

        if existing is not None and not existing.empty:
            out = pd.concat([existing, candidate], axis=0)
            out = out[~out.index.duplicated(keep="last")]
        else:
            out = candidate

        _save(out, base_dir, symbol, dst_tf, market, parquet=parquet)
        results[dst_tf] = int(candidate.shape[0])

    return results


def derive_timeframes(
    base_dir: str,
    symbols: Iterable[str],
    market: str,
    src_to_dst_map: Dict[str, Iterable[str]],
    parquet: bool = True,
) -> Dict[str, Dict[str, int]]:
    """
    Derive multiple target timeframes per source timeframe for many symbols.
    src_to_dst_map example: {"1h": ["2h","3h","12h"], "1d": ["3d"]}
    Returns nested dict: {symbol: {dst_tf: rows_appended}}
    """
    symbols = list(symbols)
    summary: Dict[str, Dict[str, int]] = {}
    for sym in symbols:
        per_symbol: Dict[str, int] = {}
        for src_tf, dst_list in src_to_dst_map.items():
            added = derive_timeframes_for_symbol(base_dir, sym, market, src_tf, dst_list, parquet=parquet)
            per_symbol.update(added)
        summary[sym] = per_symbol
    return summary
