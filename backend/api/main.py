# backend/api/main.py
from __future__ import annotations

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging to ensure it outputs to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("sigma.api")

app = FastAPI(
    title="Sigma Analyst API",
    version="1.0.0",
    # root_path tanımlamıyoruz; reverse proxy varsa uvicorn --root-path ile verilmeli
)

# CORS (gerekirse domainlerini ekle)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prod'da daralt
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health/Ready --------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    # burada gerekirse Redis/DB ping eklenebilir
    return {"status": "ready"}

# --- Routers -------------------------------------------------------------------
# ops router
try:
    from .routes import ops as ops_router  # type: ignore
    app.include_router(ops_router.router)
    log.info("Router mounted: ops -> /api/ops/*")
except Exception as e:
    log.exception("Failed to mount ops router: %s", e)

# analysis router (varsayılsa da yoksa sessizce geç)
try:
    from .routes import analysis as analysis_router  # type: ignore
    app.include_router(analysis_router.router)
    log.info("Router mounted: analysis")
except Exception:
    pass

# data router (OHLCV, symbols, timeframes)
try:
    from .routes import data as data_router  # type: ignore
    app.include_router(data_router.router)
    log.info("Router mounted: data -> /api/data/*")
except Exception as e:
    log.exception("Failed to mount data router: %s", e)

# Root bilgi
@app.get("/")
def root():
    return {
        "name": "Sigma Analyst API",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "ops": "/api/ops/ping",
        "data": "/api/data/ohlcv?symbol=BTCUSDT&timeframe=1H&limit=10"
    }

# Startup event to log all routes
@app.on_event("startup")
async def startup_event():
    log.info("=" * 60)
    log.info("Sigma Analyst API Starting Up")
    log.info("=" * 60)
    log.info("Available routes:")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = ",".join(route.methods)
            log.info(f"  [{methods:6}] {route.path}")
    log.info("=" * 60)
