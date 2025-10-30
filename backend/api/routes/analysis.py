from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["analysis"])

class AnalyzeRequest(BaseModel):
    symbols: list[str]
    timeframes: list[str] = ["1H","4H","1D"]
    mode: str = "oneshot"

@router.post("/analysis")
def analyze(req: AnalyzeRequest):
    return {
        "status": "ok",
        "received": req.model_dump(),
        "note": "Stub endpoint: gerçek pipeline’a bağlanacak."
    }
