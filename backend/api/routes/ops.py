# backend/api/routes/ops.py
from __future__ import annotations

import os
import shlex
import subprocess
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/ops", tags=["ops"])


# ---------- Schemas ----------
class DownloadReq(BaseModel):
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT"]])
    interval: str = Field(..., examples=["1h"])
    market: str = Field(..., pattern="^(spot|futures)$", examples=["futures"])
    all_time: bool = False
    start_date: Optional[str] = None  # "YYYY-MM-DD"
    end_date: Optional[str] = None    # "YYYY-MM-DD"
    parquet: bool = True  # Default to Parquet (CSV is deprecated)


class SyncReq(BaseModel):
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT"]])
    interval: str = Field(..., examples=["4h"])
    market: str = Field(..., pattern="^(spot|futures)$", examples=["spot"])
    parquet: bool = True  # Default to Parquet (CSV is deprecated)


class TrainReq(BaseModel):
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT", "XRPUSDT"]])
    timeframes: str = Field(..., examples=["1h,4h,1d"])  # CLI beklediği biçimde
    model_type: str = Field("ensemble", examples=["ensemble", "lstm", "transformer", "ppo"])
    epochs: int = Field(100, ge=1, le=1000, examples=[100])
    device: str = Field("cpu", pattern="^(cpu|cuda)$", examples=["cuda"])


class BacktestReq(BaseModel):
    strategy: str = Field(..., examples=["trend_following"])
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT"]])
    timeframe: str = Field(..., examples=["1h"])
    start_date: str = Field(..., examples=["2023-01-01"])
    end_date: str = Field(..., examples=["2024-01-01"])
    initial_capital: float = Field(10000.0, gt=0, examples=[10000.0])
    position_size_pct: float = Field(10.0, gt=0, le=100, examples=[10.0])
    commission_pct: float = Field(0.1, ge=0, le=5, examples=[0.1])


class OneShotReq(BaseModel):
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT"]])
    timeframes: str = Field(..., examples=["1h,4h,1d"])
    collect_queue: str = Field("market", examples=["market"])
    daily_queue: str = Field("analysis", examples=["analysis"])
    interval: int = Field(1, ge=1, le=10, examples=[1])
    timeout: int = Field(600, ge=10, le=3600, examples=[600])


# ---------- Helpers ----------
def _run(args: list[str], timeout: int = 300) -> dict:
    """
    Run subprocess with timeout

    Args:
        args: Command arguments to run
        timeout: Timeout in seconds (default 5 minutes)
                 - Quick operations: 300s (5 min)
                 - Data sync/download: 1800s (30 min)
                 - Training: 3600s+ (1 hour+)

    Returns:
        dict with ok, returncode, args, stdout, stderr
    """
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "args": args,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": -1,
            "args": args,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
        }
    except Exception as e:
        return {
            "ok": False,
            "returncode": -1,
            "args": args,
            "stdout": "",
            "stderr": f"Error: {str(e)}",
        }


# ---------- Endpoints ----------
@router.get("/ping")
def ping():
    return {"status": "ok", "service": "ops"}


@router.post("/download")
def download(req: DownloadReq):
    args = [
        "python", "-m", "backend.cli",
        "download",
        "-s", ",".join(req.symbols),
        "-i", req.interval,
        "-m", req.market,
    ]
    if req.all_time:
        args.append("--all-time")
    if req.start_date:
        args.extend(["--start-date", req.start_date])
    if req.end_date:
        args.extend(["--end-date", req.end_date])
    if req.parquet:
        args.append("--parquet")

    # Use longer timeout for download operations (30 minutes)
    # ALL-TIME downloads can take a while for multiple symbols
    return _run(args, timeout=1800)


@router.post("/sync")
def sync(req: SyncReq):
    args = [
        "python", "-m", "backend.cli",
        "sync",
        "-s", ",".join(req.symbols),
        "-i", req.interval,
        "-m", req.market,
    ]
    if req.parquet:
        args.append("--parquet")

    # Use longer timeout for sync operations (30 minutes)
    # Syncing multiple symbols can take a while
    return _run(args, timeout=1800)


@router.post("/train")
def train(req: TrainReq):
    args = [
        "python", "-m", "backend.cli",
        "train",
        "-s", ",".join(req.symbols),
        "-t", req.timeframes,
    ]
    # Model type ve epochs parametreleri (CLI destekliyorsa)
    if hasattr(req, 'model_type') and req.model_type:
        args.extend(["--model-type", req.model_type])
    if hasattr(req, 'epochs') and req.epochs:
        args.extend(["--epochs", str(req.epochs)])
    if hasattr(req, 'device') and req.device:
        args.extend(["--device", req.device])
    return _run(args)


@router.post("/oneshot")
def oneshot(req: OneShotReq):
    args = [
        "python", "-m", "backend.cli",
        "oneshot",
        "-s", ",".join(req.symbols),
        "-t", req.timeframes,
        "--collect-queue", req.collect_queue,
        "--daily-queue", req.daily_queue,
        "--interval", str(req.interval),
        "--timeout", str(req.timeout),
    ]
    return _run(args)


@router.post("/backtest")
def backtest(req: BacktestReq):
    """
    Backtest a trading strategy on historical data.

    Returns mock results for now. Real backtest engine will be implemented.
    """
    # TODO: Gerçek backtest engine eklenecek
    # Şimdilik mock data dönüyoruz ki UI test edilebilsin

    import random
    from datetime import datetime

    results = []
    for symbol in req.symbols:
        # Use seed for consistent results per symbol/strategy combination
        seed_str = f"{symbol}_{req.strategy}_{req.timeframe}_{req.start_date}_{req.end_date}"
        seed_value = hash(seed_str) % (2**32)
        random.seed(seed_value)

        # Mock backtest results (deterministic based on seed)
        total_return = random.uniform(-20, 80)
        sharpe_ratio = random.uniform(0.5, 3.0)
        max_drawdown = random.uniform(-25, -5)
        total_trades = random.randint(50, 200)
        winning_trades = int(total_trades * random.uniform(0.45, 0.65))
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100

        result = {
            "status": "success",
            "strategy": req.strategy,
            "symbol": symbol,
            "timeframe": req.timeframe,
            "metrics": {
                "total_return": round(total_return, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 2),
                "win_rate": round(win_rate, 1),
                "profit_factor": round(random.uniform(1.1, 2.5), 2),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "avg_win": round(random.uniform(1.5, 4.0), 2),
                "avg_loss": round(random.uniform(-3.0, -1.0), 2),
                "best_trade": round(random.uniform(8.0, 15.0), 2),
                "worst_trade": round(random.uniform(-12.0, -5.0), 2),
                "avg_trade_duration": f"{random.randint(2, 8)} hours",
            },
            "trades": [],  # Trade history can be added later
        }
        results.append(result)

        # Reset random seed
        random.seed()

    return {
        "status": "completed",
        "results": results,
        "note": "Mock backtest results (deterministic). Real backtest engine will be implemented."
    }
