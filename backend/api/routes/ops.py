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
    parquet: bool = False


class SyncReq(BaseModel):
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT"]])
    interval: str = Field(..., examples=["4h"])
    market: str = Field(..., pattern="^(spot|futures)$", examples=["spot"])
    parquet: bool = False


class TrainReq(BaseModel):
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT", "XRPUSDT"]])
    timeframes: str = Field(..., examples=["1h,4h,1d"])  # CLI beklediği biçimde


class OneShotReq(BaseModel):
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT"]])
    timeframes: str = Field(..., examples=["1h,4h,1d"])
    collect_queue: str = Field("market", examples=["market"])
    daily_queue: str = Field("analysis", examples=["analysis"])
    interval: int = Field(1, ge=1, le=10, examples=[1])
    timeout: int = Field(600, ge=10, le=3600, examples=[600])


# ---------- Helpers ----------
def _run(args: list[str]) -> dict:
    # Metin çıktı + UTF-8; emojiler PowerShell'de "garip" görünebilir ama JSON UTF-8 döner.
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.run(args, capture_output=True, text=True, env=env)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "args": args,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
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
    return _run(args)


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
    return _run(args)


@router.post("/train")
def train(req: TrainReq):
    args = [
        "python", "-m", "backend.cli",
        "train",
        "-s", ",".join(req.symbols),
        "-t", req.timeframes,
    ]
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
