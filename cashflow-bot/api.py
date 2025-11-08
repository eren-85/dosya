"""
FastAPI Server - Market Cash Flow

REST API sunucusu (opsiyonel)

Başlatma:
    uvicorn api:app --host 0.0.0.0 --port 8000

Endpoints:
    GET /health - Sağlık kontrolü
    POST /analyze - Market analizi
    GET /risk - Risk değerlendirmesi
    GET /top/{n} - Top N coin
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from cashflow_analyzer import CashFlowAnalyzer
import config

app = FastAPI(
    title="Market Cash Flow API",
    version="1.0.0",
    description="Binance'den canlı veri ile market nakit akışı analizi"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = CashFlowAnalyzer()


class AnalyzeRequest(BaseModel):
    """Analiz isteği"""
    symbols: Optional[List[str]] = Field(None, description="Coinler (None=otomatik)")
    timeframe: str = Field("15m", description="Zaman dilimi: 15m, 1h, 4h, 1d")
    top_n: int = Field(30, ge=5, le=50, description="Top N coin")
    limit: int = Field(500, ge=100, le=1000, description="Candle sayısı")
    format: str = Field("json", pattern="^(json|text)$", description="Çıktı formatı")


@app.get("/")
def root():
    """Ana sayfa"""
    return {
        "name": "Market Cash Flow API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "analyze": "POST /analyze",
            "risk": "GET /risk",
            "top": "GET /top/{n}"
        }
    }


@app.get("/health")
def health():
    """Sağlık kontrolü"""
    return {"status": "ok", "service": "cashflow-api"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Market analizi yap

    Example:
        POST /analyze
        {
            "top_n": 30,
            "timeframe": "15m",
            "format": "text"
        }
    """
    try:
        report = analyzer.analyze(
            symbols=req.symbols,
            timeframe=req.timeframe,
            top_n=req.top_n,
            limit=req.limit
        )

        if report['status'] == 'error':
            raise HTTPException(status_code=500, detail=report.get('message'))

        if req.format == 'text':
            return {
                "status": "success",
                "format": "text",
                "report": report['text_report'],
                "timestamp": report['timestamp']
            }

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risk")
def get_risk():
    """
    Sadece risk değerlendirmesi

    Example:
        GET /risk
    """
    try:
        report = analyzer.analyze(top_n=10, timeframe='15m', limit=300)

        if report['status'] == 'error':
            raise HTTPException(status_code=500, detail=report.get('message'))

        return {
            "status": "success",
            "risk_assessment": report['risk_assessment'],
            "market_metrics": report['market_metrics'],
            "timestamp": report['timestamp']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/top/{n}")
def get_top(n: int = 10):
    """
    Top N coin analizi

    Example:
        GET /top/10
    """
    try:
        if n < 5 or n > 50:
            raise HTTPException(status_code=400, detail="n must be between 5 and 50")

        report = analyzer.analyze(top_n=n, timeframe='15m')

        if report['status'] == 'error':
            raise HTTPException(status_code=500, detail=report.get('message'))

        return {
            "status": "success",
            "top_flows": report['top_flows'][:n],
            "risk_assessment": report['risk_assessment'],
            "timestamp": report['timestamp']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    print("🚀 Starting Cash Flow API...")
    print(f"📍 http://{config.API_HOST}:{config.API_PORT}")
    print(f"📚 Docs: http://{config.API_HOST}:{config.API_PORT}/docs")
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
