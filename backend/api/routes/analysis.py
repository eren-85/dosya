"""
Analysis endpoints - Market analysis with OpenAI

Features:
- Real-time market analysis
- Technical indicator calculation
- OpenAI-powered insights
- Multiple symbols and timeframes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# OpenAI client
try:
    from backend.llm.openai_client import get_openai_client
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


# ============================================
# Request/Response Models
# ============================================

class AnalyzeRequest(BaseModel):
    """Market analysis request"""
    symbols: List[str] = Field(..., min_length=1, examples=[["BTCUSDT", "ETHUSDT"]])
    timeframes: List[str] = Field(["1H", "4H", "1D"], examples=[["1H", "4H", "1D"]])
    mode: str = Field("oneshot", pattern="^(oneshot|continuous)$")
    use_openai: bool = Field(True, description="Use OpenAI for analysis")
    model: Optional[str] = Field(None, description="Override OpenAI model")


class QuickAnalysisRequest(BaseModel):
    """Quick analysis request"""
    symbol: str = Field(..., examples=["BTCUSDT"])
    question: Optional[str] = Field(None, examples=["Is this a good entry point?"])


class AnalysisResponse(BaseModel):
    """Analysis response"""
    status: str
    symbol: str
    timeframe: str
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


# ============================================
# Endpoints
# ============================================

@router.post("/analysis", response_model=Dict[str, Any])
async def analyze(req: AnalyzeRequest):
    """
    Generate comprehensive market analysis

    This endpoint:
    1. Fetches latest market data
    2. Calculates technical indicators
    3. Gathers on-chain data (if available)
    4. Generates AI-powered analysis with OpenAI
    5. Returns actionable trading insights

    **Note:** This is a demo implementation. In production:
    - Add real market data fetching
    - Calculate actual technical indicators
    - Implement caching for rate limit protection
    - Add authentication/rate limiting
    """
    logger.info(f"📊 Analysis request: {req.symbols} ({req.timeframes})")

    if not OPENAI_AVAILABLE and req.use_openai:
        raise HTTPException(
            status_code=503,
            detail="OpenAI client not available. Install: pip install openai"
        )

    results = []

    for symbol in req.symbols:
        for timeframe in req.timeframes:
            try:
                # TODO: Replace with real market data
                market_data = _get_mock_market_data(symbol, timeframe)
                technical_indicators = _get_mock_technical_indicators()
                on_chain_data = _get_mock_on_chain_data(symbol)

                if req.use_openai:
                    # Use OpenAI for analysis
                    client = get_openai_client(model=req.model)
                    analysis_result = client.analyze_market(
                        symbol=symbol,
                        timeframe=timeframe,
                        market_data=market_data,
                        technical_indicators=technical_indicators,
                        on_chain_data=on_chain_data,
                    )

                    # Check if analysis_result is an error
                    if "error" in analysis_result and analysis_result.get("status") == "error":
                        results.append({
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "status": "error",
                            "error": analysis_result.get("message", str(analysis_result.get("error", "Unknown error"))),
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                    else:
                        results.append({
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "status": "success",
                            "analysis": analysis_result,
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                else:
                    # Return raw data without AI analysis
                    results.append({
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "status": "success",
                        "market_data": market_data,
                        "technical_indicators": technical_indicators,
                        "on_chain_data": on_chain_data,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            except Exception as e:
                logger.error(f"❌ Analysis failed for {symbol}/{timeframe}: {e}")
                results.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })

    return {
        "status": "completed",
        "mode": req.mode,
        "total_analyses": len(results),
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/analysis/extended")
async def get_extended_analysis(symbol: str, interval: str = "1h"):
    """
    Get extended analysis for a symbol (GET endpoint for frontend)

    Returns comprehensive analysis including:
    - Market data
    - Technical indicators
    - AI-powered insights
    - Trading scenarios
    """
    logger.info(f"📊 Extended analysis: {symbol} ({interval})")

    try:
        # Get mock market data
        market_data = _get_mock_market_data(symbol, interval)
        technical_indicators = _get_mock_technical_indicators()
        on_chain_data = _get_mock_on_chain_data(symbol)

        # Generate analysis scenarios
        current_price = market_data["current_price"]

        return {
            "status": "success",
            "symbol": symbol,
            "interval": interval,
            "current_price": current_price,
            "market_data": market_data,
            "indicators": technical_indicators,
            "on_chain": on_chain_data,
            "scenarios": {
                "bullish": {
                    "probability": 65,
                    "target": current_price * 1.15,
                    "reasoning": "Strong momentum, RSI healthy, volume increasing"
                },
                "bearish": {
                    "probability": 35,
                    "target": current_price * 0.92,
                    "reasoning": "Resistance at current level, potential correction"
                },
                "neutral": {
                    "probability": 45,
                    "range": [current_price * 0.97, current_price * 1.03],
                    "reasoning": "Consolidation phase, waiting for breakout"
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"❌ Extended analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/quick")
async def quick_analysis(req: QuickAnalysisRequest):
    """
    Get a quick text analysis for a symbol

    Faster than full analysis, returns simple text insights.
    Useful for chat-style interactions.
    """
    logger.info(f"⚡ Quick analysis: {req.symbol}")

    if not OPENAI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OpenAI client not available"
        )

    try:
        # TODO: Replace with real data
        current_price = 67500.0  # Mock price
        indicators = {
            "RSI_14": 58.3,
            "MACD": "bullish_cross",
            "MA_50": 66800,
            "MA_200": 65200,
            "Volume_24h": "Above average",
        }

        client = get_openai_client()
        analysis_text = client.quick_analysis(
            symbol=req.symbol,
            current_price=current_price,
            indicators=indicators,
            question=req.question,
        )

        return {
            "status": "success",
            "symbol": req.symbol,
            "analysis": analysis_text,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Quick analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Mock Data Functions (Replace in Production)
# ============================================

def _get_mock_market_data(symbol: str, timeframe: str) -> Dict[str, Any]:
    """
    Mock market data (replace with real Binance/exchange data)

    In production:
    - Use backend.data.collectors.binance_collector
    - Fetch from local database
    - Or use ccxt for multi-exchange support
    """
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "current_price": 67500.0,
        "24h_change": 2.3,
        "24h_high": 68200.0,
        "24h_low": 66100.0,
        "24h_volume": 42000000.0,
        "bid": 67498.0,
        "ask": 67502.0,
        "spread": 4.0,
    }


def _get_mock_technical_indicators() -> Dict[str, Any]:
    """
    Mock technical indicators (replace with real calculations)

    In production:
    - Use backend.data.processors.feature_engineering
    - Calculate from historical data
    - Use pandas_ta, ta-lib, or custom functions
    """
    return {
        "trend": {
            "MA_50": 66800,
            "MA_200": 65200,
            "EMA_21": 67100,
            "trend_direction": "uptrend",
        },
        "momentum": {
            "RSI_14": 58.3,
            "MACD": 120.5,
            "MACD_signal": 95.3,
            "MACD_histogram": 25.2,
            "Stochastic_K": 62.1,
            "Stochastic_D": 58.7,
        },
        "volatility": {
            "BB_upper": 69500,
            "BB_middle": 67500,
            "BB_lower": 65500,
            "ATR_14": 1250.0,
        },
        "volume": {
            "volume_24h": 42000000,
            "volume_MA_20": 38500000,
            "volume_ratio": 1.09,
            "OBV": "increasing",
        },
    }


def _get_mock_on_chain_data(symbol: str) -> Dict[str, Any]:
    """
    Mock on-chain data (replace with real Glassnode/CryptoQuant data)

    In production:
    - Use Glassnode API
    - Use CryptoQuant API
    - Store in database for historical analysis
    """
    if "BTC" not in symbol:
        return {}

    return {
        "exchange_netflow": {
            "24h": -2500,  # BTC
            "7d": -8200,
            "trend": "outflow",
        },
        "whale_transactions": {
            "count_24h": 15,
            "volume_24h": 125000000,  # USD
            "largest": 25000000,
        },
        "stablecoin_inflow": {
            "24h": 450000000,  # USD
            "source": "USDT",
        },
        "active_addresses": {
            "24h": 890000,
            "7d_avg": 850000,
            "trend": "increasing",
        },
        "miner_behavior": {
            "hashrate": "stable",
            "selling_pressure": "low",
        },
    }

