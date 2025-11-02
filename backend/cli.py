#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sigma Analyst command line interface (full + sync, 2025-10-30)

Adds:
- sync: resume/append OHLCV to existing CSV/Parquet without redownloading full history.
- Parquet save path fixes and optional dependency handling.
- Explicit queue routing for Celery tasks (market vs analysis).
- Robust JSON outputs for machine parsing.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import sys
import time
import typing as T

# Optional deps
try:
    import requests
except Exception:
    requests = None

try:
    import pandas as pd  # optional (for Parquet)
except Exception:
    pd = None

UTC = dt.timezone.utc
BINANCE_SPOT = "https://api.binance.com"
BINANCE_FUT  = "https://fapi.binance.com"

ALLOWED_INTERVALS = {
    "1m","3m","5m","15m","30m",
    "1h","2h","4h","6h","8h","12h",
    "1d","3d","1w","1M"
}

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.getcwd(), "data", "historical"))


def _log(msg: str) -> None:
    now = dt.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def parse_symbols(arg: str) -> T.List[str]:
    return [s.strip().upper() for s in arg.split(",") if s.strip()]


def _normalize_timeframe(tf: str) -> str:
    s = tf.strip().replace(" ", "")
    if not s:
        return s
    s = s.lower()
    s = s.replace("hr", "h").replace("hrs", "h").replace("hour", "h").replace("day", "d")
    if s.isdigit():
        s = f"{s}h"
    m = re.fullmatch(r"(\d+)m", s)
    if m:
        mins = int(m.group(1))
        if mins % 1440 == 0:
            s = f"{mins // 1440}d"
        elif mins % 60 == 0:
            s = f"{mins // 60}h"
    return s


def parse_timeframes(arg: str | None) -> T.List[str]:
    if not arg:
        return ["1h"]
    raw = re.split(r"[,\s]+", arg.strip())
    tfs: T.List[str] = []
    for token in raw:
        if not token:
            continue
        norm = _normalize_timeframe(token)
        if norm not in ALLOWED_INTERVALS:
            raise SystemExit(f"Unsupported timeframe: {token}. Normalized='{norm}'. Allowed: {sorted(ALLOWED_INTERVALS)}")
        tfs.append(norm)
    return tfs


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def to_iso_utc(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000.0, tz=dt.timezone.utc).isoformat()


# -------------------- Binance download --------------------

@dataclasses.dataclass
class DownloadOptions:
    symbols: T.List[str]
    interval: str
    market: str
    start: T.Optional[str] = None
    end: T.Optional[str] = None
    all_time: bool = False
    parquet: bool = False


def _binance_base(market: str) -> str:
    m = market.lower()
    if m not in ("spot", "futures"):
        raise SystemExit("market must be 'spot' or 'futures'")
    return BINANCE_SPOT if m == "spot" else BINANCE_FUT


def _binance_klines_endpoint(market: str) -> str:
    return "/api/v3/klines" if market == "spot" else "/fapi/v1/klines"


def _req_get_json(url: str, params: dict, retries: int = 3, timeout: float = 15.0) -> T.List:
    if requests is None:
        raise SystemExit("requests module not available. Please add it to requirements.txt")
    last_ex = None
    for _ in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                time.sleep(1.0)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as ex:
            last_ex = ex
            time.sleep(0.5)
    if last_ex:
        raise last_ex
    return []


def _iterate_klines(symbol: str, interval: str, market: str, start_ms: int, end_ms: int | None) -> T.Iterable[T.List]:
    base = _binance_base(market)
    ep = _binance_klines_endpoint(market)
    url = f"{base}{ep}"
    limit = 1000
    cur = start_ms
    while True:
        params = {"symbol": symbol, "interval": interval, "limit": limit, "startTime": cur}
        if end_ms is not None:
            params["endTime"] = end_ms
        batch = _req_get_json(url, params=params)
        if not batch:
            break
        yield batch
        last_close = batch[-1][6]
        nxt = last_close + 1
        if end_ms is not None and nxt > end_ms:
            break
        if len(batch) < limit:
            break
        cur = nxt
        time.sleep(0.06)


def _save_csv_parquet(rows: T.List[dict], csv_path: str, parquet: bool):
    """Write data to Parquet format ONLY. CSV support removed."""
    ensure_dir(os.path.dirname(csv_path))

    # Parquet ONLY - no CSV fallback
    parquet_path = csv_path.replace(".csv", ".parquet")

    if pd is None:
        raise RuntimeError(
            "⚠️  pandas (and pyarrow/fastparquet) not installed.\n"
            "Install with: pip install pandas pyarrow\n"
            "Parquet is required - CSV support has been removed."
        )

    try:
        df = pd.DataFrame(rows)
        df.to_parquet(parquet_path, index=False)
        print(f"💾 Saved Parquet: {parquet_path}")
    except Exception as ex:
        raise RuntimeError(f"⚠️  Parquet save failed: {ex}\nCannot save data - CSV fallback has been removed.")


def cmd_download(args: argparse.Namespace) -> None:
    interval = _normalize_timeframe(args.interval)
    if interval not in ALLOWED_INTERVALS:
        raise SystemExit(f"Unsupported interval: {args.interval}. Normalized='{interval}'. Allowed: {sorted(ALLOWED_INTERVALS)}")

    opts = DownloadOptions(
        symbols=parse_symbols(args.symbols),
        interval=interval,
        market=args.market.lower(),
        start=args.start,
        end=args.end,
        all_time=args.all_time,
        parquet=args.parquet,
    )

    ensure_dir(DATA_DIR)

    if opts.all_time:
        start_ms = 0
        end_ms = None
    else:
        if not opts.start:
            raise SystemExit("--start required unless --all-time is given")
        start_dt = dt.datetime.fromisoformat(opts.start).replace(tzinfo=dt.timezone.utc)
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = None
        if opts.end:
            end_dt = dt.datetime.fromisoformat(opts.end).replace(tzinfo=dt.timezone.utc)
            end_ms = int(end_dt.timestamp() * 1000)

    print("\n📊 Binance Historical Data Download")
    print(f"Market:   {opts.market}")
    print(f"Symbols:  {', '.join(opts.symbols)}")
    print(f"Interval: {opts.interval}")
    if opts.all_time:
        print(f"Period:   ALL-TIME\n")
    else:
        print(f"Period:   {opts.start} → {opts.end or 'NOW'}\n")

    for sym in opts.symbols:
        print(f"⏳ Downloading {sym} ...")
        all_rows: T.List[dict] = []
        total = 0
        first_iso = None
        last_iso = None
        for batch in _iterate_klines(sym, opts.interval, opts.market, start_ms, end_ms):
            total += len(batch)
            if first_iso is None and batch:
                first_iso = to_iso_utc(batch[0][0])
            if batch:
                last_iso = to_iso_utc(batch[-1][6])
            for k in batch:
                all_rows.append({
                    "open_time": to_iso_utc(k[0]),
                    "open": k[1],
                    "high": k[2],
                    "low": k[3],
                    "close": k[4],
                    "volume": k[5],
                    "close_time": to_iso_utc(k[6]),
                    "quote_volume": k[7],
                    "n_trades": k[8],
                    "taker_buy_base": k[9],
                    "taker_buy_quote": k[10],
                    "market": opts.market,
                })
        first_iso = first_iso or "N/A"
        last_iso = last_iso or "N/A"
        print(f"✅ {sym}: {total} candles  |  {first_iso} → {last_iso}")
        out_csv = os.path.join(DATA_DIR, f"{sym}_{opts.interval}_{opts.market}.csv")
        _save_csv_parquet(all_rows, out_csv, parquet=opts.parquet)


# -------------------- Celery helpers --------------------

def _get_celery_app():
    from backend.tasks.celery_app import celery_app  # type: ignore
    return celery_app


def _redis_url_from_env() -> str:
    return os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")


# -------------------- Celery-driven commands --------------------

def cmd_collect(args: argparse.Namespace) -> None:
    symbols = parse_symbols(args.symbols)
    timeframes = parse_timeframes(args.timeframes)
    app = _get_celery_app()
    for tf in timeframes:
        r = app.send_task(
            "backend.tasks.tasks.collect_market_data",
            kwargs={"symbols": symbols, "interval": tf},
            queue=args.queue,
        )
        print(f"ENQUEUED collect_market_data [{tf}]: {r.id}")


def cmd_daily(args: argparse.Namespace) -> None:
    symbols = parse_symbols(args.symbols)
    app = _get_celery_app()
    r = app.send_task("backend.tasks.tasks.run_daily_analysis", kwargs={"symbols": symbols}, queue=args.queue)
    print(f"ENQUEUED run_daily_analysis: {r.id}")


def cmd_train(args: argparse.Namespace) -> None:
    symbols = parse_symbols(args.symbols)
    timeframes = parse_timeframes(args.timeframes)
    model_type = getattr(args, 'model_type', 'ensemble')
    epochs = getattr(args, 'epochs', 100)
    device = getattr(args, 'device', 'cpu')

    app = _get_celery_app()
    for sym in symbols:
        for tf in timeframes:
            r = app.send_task(
                "backend.tasks.tasks.train_ensemble_model",
                kwargs={
                    "symbol": sym,
                    "timeframe": tf,
                    "model_type": model_type,
                    "epochs": epochs,
                    "device": device
                },
                queue=args.queue,
            )
            print(f"ENQUEUED {model_type} model training [{sym} {tf}] epochs={epochs} device={device}: {r.id}")


def cmd_backtest(args: argparse.Namespace) -> None:
    symbols = parse_symbols(args.symbols)
    strategy = args.strategy
    start_date = args.start_date
    end_date = args.end_date
    app = _get_celery_app()
    for sym in symbols:
        r = app.send_task(
            "backend.tasks.tasks.run_backtest",
            kwargs={"symbol": sym, "strategy": strategy, "start_date": start_date, "end_date": end_date},
            queue=args.queue,
        )
        print(f"ENQUEUED run_backtest [{sym}]: {r.id}")


def cmd_analyze(args: argparse.Namespace) -> None:
    symbols = parse_symbols(args.symbols)
    timeframes = parse_timeframes(args.timeframes)
    app = _get_celery_app()
    collect_ids = []
    for tf in timeframes:
        r = app.send_task(
            "backend.tasks.tasks.collect_market_data",
            kwargs={"symbols": symbols, "interval": tf},
            queue=args.collect_queue,
        )
        print(f"ENQUEUED collect_market_data [{tf}]: {r.id}")
        collect_ids.append(r.id)
    r_daily = app.send_task("backend.tasks.tasks.run_daily_analysis", kwargs={"symbols": symbols}, queue=args.daily_queue)
    print(f"ENQUEUED run_daily_analysis: {r_daily.id}")
    if args.json:
        print(json.dumps({"collect_task_ids": collect_ids, "run_daily_analysis_id": r_daily.id}))


def _await_task(app, tid: str, interval: float = 1.0, timeout: float | None = None):
    from celery.result import AsyncResult
    res = AsyncResult(tid, app=app)
    start = time.time()
    while True:
        state = res.state
        stamp = dt.datetime.now().strftime("%H:%M:%S")
        print(f"[{stamp}] {tid}: {state}")
        if state in ("SUCCESS", "FAILURE"):
            try:
                payload = res.get(timeout=1)
            except Exception:
                payload = res.result
            return state, payload
        if timeout is not None and (time.time() - start) > timeout:
            return "TIMEOUT", None
        time.sleep(interval)


def cmd_oneshot(args: argparse.Namespace) -> None:
    symbols = parse_symbols(args.symbols)
    timeframes = parse_timeframes(args.timeframes)
    app = _get_celery_app()

    collect_ids = []
    if not args.skip_collect:
        for tf in timeframes:
            r = app.send_task(
                "backend.tasks.tasks.collect_market_data",
                kwargs={"symbols": symbols, "interval": tf},
                queue=args.collect_queue,
            )
            print(f"ENQUEUED collect_market_data [{tf}]: {r.id}")
            collect_ids.append(r.id)
        for tid in collect_ids:
            state, _ = _await_task(app, tid, interval=args.interval, timeout=args.timeout)
            if state != "SUCCESS":
                print(f"❌ collect task failed or timed out: {tid} ({state})")
                return

    r_daily = app.send_task("backend.tasks.tasks.run_daily_analysis", kwargs={"symbols": symbols}, queue=args.daily_queue)
    print(f"ENQUEUED run_daily_analysis: {r_daily.id}")
    state, payload = _await_task(app, r_daily.id, interval=args.interval, timeout=args.timeout)
    if state != "SUCCESS":
        print(f"❌ daily analysis failed or timed out: {r_daily.id} ({state})")
        return

    if args.json:
        print(json.dumps({"symbols": symbols, "timeframes": timeframes, "result": payload}, ensure_ascii=False, indent=2))
        return

    banner = "🤖 Sigma Analyst - Market Analysis\n" + ("="*35)
    print(banner)
    print(f"\n📊 Symbols: {', '.join(symbols)}")
    print(f"⏰ Timeframes: {', '.join(timeframes)}")
    ts = payload.get("timestamp") if isinstance(payload, dict) else None
    print(f"🕒 Completed: {ts or 'N/A'}")
    print(f"✅ Status: {payload.get('status','unknown') if isinstance(payload, dict) else state}")
    ac = payload.get("analyses_count") if isinstance(payload, dict) else None
    if ac is not None:
        print(f"📦 Analyses: {ac}")
    print("")


def cmd_health(args: argparse.Namespace) -> None:
    app = _get_celery_app()
    r = app.send_task("backend.tasks.tasks.health_check", kwargs={}, queue=args.queue)
    print(f"ENQUEUED health_check: {r.id}")


def cmd_result(args: argparse.Namespace) -> None:
    ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    from celery.result import AsyncResult
    app = _get_celery_app()
    for tid in ids:
        res = AsyncResult(tid, app=app)
        try:
            state = res.state
            if state == "SUCCESS":
                print(f"Task {tid}: {state}")
                try:
                    payload = res.get(timeout=1)
                except Exception:
                    payload = res.result
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(f"Task {tid}: {state}")
        except Exception as ex:
            print(f"Task {tid}: ERROR {ex}")


def cmd_ls(args: argparse.Namespace) -> None:
    try:
        import redis  # type: ignore
    except Exception:
        return print("redis-py is not installed. Add 'redis' to requirements.txt")

    rurl = _redis_url_from_env()
    import redis as _redis
    r = _redis.from_url(rurl)
    pattern = "celery-task-meta-*"
    cur = 0
    seen = 0
    limit = args.limit
    while True:
        cur, keys = r.scan(cur, match=pattern, count=200)
        for k in keys:
            print(k.decode() if isinstance(k, (bytes, bytearray)) else str(k))
            seen += 1
            if seen >= limit:
                return
        if cur == 0:
            break


def cmd_watch(args: argparse.Namespace) -> None:
    ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    from celery.result import AsyncResult
    app = _get_celery_app()
    remaining = set(ids)
    while remaining:
        for tid in list(remaining):
            res = AsyncResult(tid, app=app)
            state = res.state
            stamp = dt.datetime.now().strftime("%H:%M:%S")
            if state in ("PENDING", "RECEIVED", "STARTED", "RETRY"):
                print(f"[{stamp}] {tid}: {state}")
            elif state in ("SUCCESS", "FAILURE"):
                print(f"[{stamp}] {tid}: {state}")
                if args.print_result:
                    try:
                        payload = res.get(timeout=1)
                    except Exception:
                        payload = res.result
                    try:
                        print(json.dumps(payload, ensure_ascii=False, indent=2))
                    except TypeError:
                        print(str(payload))
                remaining.discard(tid)
        if remaining:
            try:
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("Interrupted.")
                break


# ---- sync subcommand (uses backend.historical_sync) ----
def cmd_sync(args):
    symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
    interval = args.interval.strip()
    market = args.market.strip().lower()
    parquet = bool(args.parquet)

    # lazy import so the module is only needed when using `sync`
    try:
        from backend.historical_sync import sync_historical
    except Exception as e:
        print(f"Error importing backend.historical_sync: {e}", file=sys.stderr)
        sys.exit(2)

    # Preferred: keyword arguments (new signature)
    try:
        sync_historical(symbols=symbols, interval=interval, market=market, parquet=parquet)
    except TypeError:
        # Fallback 1: old signature (symbols, interval, market, data_dir, parquet)
        data_root = os.getenv("DATA_DIR", "/app/data")
        hist_dir = os.path.join(data_root, "historical")
        try:
            sync_historical(symbols, interval, market, hist_dir, parquet)
        except TypeError:
            # Fallback 2: accepts a single 'opts' object
            from types import SimpleNamespace
            opts = SimpleNamespace(symbols=symbols, interval=interval, market=market, parquet=parquet)
            sync_historical(opts)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="backend.cli", description="Sigma Analyst CLI (full + sync)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("download", help="Download historical OHLCV from Binance (spot/futures) directly (no Celery).")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols, e.g., BTCUSDT,ETHUSDT")
    p.add_argument("-i", "--interval", required=True, help="Binance interval, e.g., 1h")
    p.add_argument("-m", "--market", default="spot", help="spot or futures (default: spot)")
    p.add_argument("--start", help="YYYY-MM-DD (UTC)")
    p.add_argument("--end", help="YYYY-MM-DD (UTC)")
    p.add_argument("--all-time", action="store_true", help="Download from earliest available to now")
    p.add_argument("--parquet", action="store_true", help="Also write Parquet next to CSV (requires pandas)")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("collect", help="Enqueue market data collection tasks per timeframe.")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols")
    p.add_argument("-t", "--timeframes", help="Comma-separated TFs (default: 1h)")
    p.add_argument("--queue", default=os.getenv("COLLECT_QUEUE", "market"), help="Queue for collect tasks (default: market)")
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("daily", help="Enqueue daily analysis task.")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols")
    p.add_argument("--queue", default=os.getenv("ANALYSIS_QUEUE", "analysis"), help="Queue for daily tasks (default: analysis)")
    p.set_defaults(func=cmd_daily)

    p = sub.add_parser("train", help="Enqueue model training tasks.")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols")
    p.add_argument("-t", "--timeframes", help="Comma-separated TFs (default: 1h)")
    p.add_argument("--model-type", default="ensemble", choices=["ensemble", "lstm", "transformer", "ppo"], help="Model type (default: ensemble)")
    p.add_argument("--epochs", type=int, default=100, help="Number of epochs (default: 100)")
    p.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Training device (default: cpu)")
    p.add_argument("--queue", default=os.getenv("ANALYSIS_QUEUE", "analysis"), help="Queue for training tasks (default: analysis)")
    p.set_defaults(func=cmd_train)

    p = sub.add_parser("backtest", help="Enqueue backtest tasks.")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols")
    p.add_argument("--strategy", required=True, help="Strategy name")
    p.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--queue", default=os.getenv("ANALYSIS_QUEUE", "analysis"), help="Queue for backtest tasks (default: analysis)")
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("analyze", help="Enqueue collect (per TF) then daily analysis.")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols")
    p.add_argument("-t", "--timeframes", help="Comma-separated TFs (default: 1h)")
    p.add_argument("--json", action="store_true", help="Print task ids as JSON (machine-friendly)")
    p.add_argument("--collect-queue", default=os.getenv("COLLECT_QUEUE", "market"), help="Queue for collect tasks (default: market)")
    p.add_argument("--daily-queue", default=os.getenv("ANALYSIS_QUEUE", "analysis"), help="Queue for daily task (default: analysis)")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("oneshot", help="Synchronous: collect (optional) → daily; wait and print pretty/JSON.")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols")
    p.add_argument("-t", "--timeframes", help="Comma-separated TFs (default: 1h)")
    p.add_argument("--skip-collect", action="store_true", help="Skip the collect step if data is already present")
    p.add_argument("--interval", type=float, default=1.0, help="Polling interval seconds (default: 1.0)")
    p.add_argument("--timeout", type=float, default=None, help="Overall timeout seconds (default: no timeout)")
    p.add_argument("--json", action="store_true", help="Print final result JSON instead of pretty text")
    p.add_argument("--collect-queue", default=os.getenv("COLLECT_QUEUE", "market"), help="Queue for collect tasks (default: market)")
    p.add_argument("--daily-queue", default=os.getenv("ANALYSIS_QUEUE", "analysis"), help="Queue for daily task (default: analysis)")
    p.set_defaults(func=cmd_oneshot)

    p = sub.add_parser("health", help="Enqueue worker health check.")
    p.add_argument("--queue", default=os.getenv("ANALYSIS_QUEUE", "analysis"), help="Queue for health task (default: analysis)")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("result", help="Fetch Celery task results from Redis backend.")
    p.add_argument("--ids", required=True, help="Comma-separated Celery task IDs")
    p.set_defaults(func=cmd_result)

    p = sub.add_parser("ls", help="List recent Celery task meta keys from Redis result backend.")
    p.add_argument("--limit", type=int, default=10, help="Max number of keys to print (default: 10)")
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser("watch", help="Poll task ids until they finish and print results.")
    p.add_argument("--ids", required=True, help="Comma-separated Celery task IDs")
    p.add_argument("--interval", type=float, default=1.0, help="Polling interval seconds (default: 1.0)")
    p.add_argument("--print-result", action="store_true", help="Print result payload on success")
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("sync", help="Incremental sync to existing CSV/Parquet without full redownload.")
    p.add_argument("-s", "--symbols", required=True, help="Comma-separated symbols, e.g., BTCUSDT,ETHUSDT")
    p.add_argument("-i", "--interval", required=True, help="Binance interval, e.g., 1h")
    p.add_argument("-m", "--market", default="spot", help="spot or futures (default: spot)")
    p.add_argument("--parquet", action="store_true", help="Also update Parquet next to CSV (requires pandas)")
    p.set_defaults(func=cmd_sync)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
