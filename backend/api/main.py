"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..core.config import settings

app = FastAPI(
    title="Sigma Analyst API",
    description="AI-powered Crypto Market Analysis System",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "Sigma Analyst API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-10-26T22:00:00Z"
    }


# TODO: Add routers
# from .routers import analysis, backtest, data
# app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
# app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
# app.include_router(data.router, prefix="/api/data", tags=["data"])
