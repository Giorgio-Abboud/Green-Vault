import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from src.service import make_calculation

logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Input & Output Models --------------------
class CalcIn(BaseModel):
    timestamp: str
    price: float
    quantity: int
    side: str
    symbol: str
    request: str

class Fill(BaseModel):
    timestamp: str
    price: float
    quantity: int
    side: str
    symbol: str
    mode: str

class Metric(BaseModel):
    vwap_slippage: float
    shortfall: float
    effective_spread: float
    realized_spread: float
    market_impact: float
    drift: float

class CalcOut(BaseModel):
    ok: bool
    request_id: str = Field(..., description="Trace ID for the calculation")
    fills: Fill
    metrics: Metric

# -------------------- Endpoint --------------------
@app.post("/calculate", response_model=CalcOut)
def calculate(body: CalcIn):
    logging.info("Received /calculate")
    try:
        # Map request -> normalized mode
        req = (body.request or "").strip().lower()
        if req == "analyze":
            mode = "analyze"
        elif req == "estimate":
            mode = "estimate"
        else:
            logging.warning("Unknown request %r; defaulting to analyze", body.request)
            mode = "analyze"

        ok, req_id, fills, metrics = make_calculation(
            timestamp=body.timestamp,
            price=body.price,
            quantity=body.quantity,
            side=body.side,
            symbol=body.symbol,
            mode=mode,
        )

        return {"ok": ok, "request_id": req_id, "fills": fills, "metrics": metrics}

    except Exception as e:
        logging.exception("Error in /calculate")
        return {
            "ok": False,
            "request_id": "",
            "fills": None,
            "metrics": {"error": str(e)},
        }
