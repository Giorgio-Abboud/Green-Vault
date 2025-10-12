import logging
from datetime import datetime
from typing import Any, Dict, Optional, Literal, Annotated
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
# =============================================================================
# API Input Schema — Examples & Formatting Guide
#
# Timestamp (REQUIRED, tz-aware ISO-8601)
# - Always include a timezone offset or 'Z' for UTC.
# - Examples:
#   "2025-06-03T10:15:37-04:00"   # Eastern Daylight Time (UTC-04:00)
#   "2025-12-12T14:03:00-05:00"   # Eastern Standard Time (UTC-05:00)
#   "2025-06-03T14:15:37Z"        # UTC
#
# Price (PositivePrice)
# - Positive float. e.g., 190.12, 0.01, 425.2501
#
# Quantity (StrictPosInt)
# - Positive integer (strict). e.g., 1, 100, 2500
#
# Side (TradeSide)
# - Literal "buy" or "sell"
#
# Symbol (Ticker)
# - UPPERCASE ticker, letters only (regex ^[A-Z]+$). e.g., "AAPL", "MSFT", "TSLA"
#
# Request (RequestMode)
# - Literal "analyze" or "estimate"
#   - "analyze": run full metric computation (e.g., trade vs. market VWAP)
#   - "estimate": lightweight/approximate calculation
#
# --------------------------
# Valid JSON examples
# --------------------------
# 1) Single-fill BUY in ET (with offset):
# {
#   "timestamp": "2025-06-03T10:15:37-04:00",
#   "price": 190.12,
#   "quantity": 150,
#   "side": "buy",
#   "symbol": "AAPL",
#   "request": "analyze"
# }
#
# 2) Single-fill SELL in UTC:
# {
#   "timestamp": "2025-06-03T14:15:37Z",
#   "price": 425.25,
#   "quantity": 75,
#   "side": "sell",
#   "symbol": "MSFT",
#   "request": "estimate"
# }
#
# --------------------------
# Common mistakes to avoid
# --------------------------
# - Naive timestamps (no offset): "2025-06-03T10:15:37"   ❌ (must include offset or Z)
# - Lower/mixed case tickers: "aapl", "MsFt"              ❌ (must match ^[A-Z]+$)
# - Non-positive price/quantity: 0, -1, -3.5              ❌
# - Invalid side/request strings: "BUY", "hold", "calc"   ❌
# =============================================================================

PositivePrice = Annotated[float, Field(gt=0)]
StrictPosInt = Annotated[int, Field(strict=True, gt=0)]
TradeSide = Literal["buy", "sell"]
Ticker = Annotated[str, Field(regex=r"^[A-Z]+$", strip_whitespace=True)]
RequestMode = Annotated[Literal["analyze", "estimate"], Field(default="analyze")]

class CalcIn(BaseModel):
    timestamp: datetime
    price: PositivePrice
    quantity: StrictPosInt
    side: TradeSide
    symbol: Ticker
    request: RequestMode

class Fill(BaseModel):
    timestamp: datetime
    price: PositivePrice
    quantity: StrictPosInt
    side: TradeSide
    symbol: Ticker
    mode: RequestMode

class Metric(BaseModel):
    vwap_slippage: str
    shortfall: str
    effective_spread: str
    realized_spread: str
    market_impact: str
    drift: str

class CalcOut(BaseModel):
    ok: bool
    request_id: str = Field(..., description="Trace ID for the calculation")
    fills: Fill
    metrics: Metric

# -------------------- Endpoint --------------------
@app.post("/calculate", response_model=CalcOut)
def calculate(body: CalcIn):
    """
    Accept input from the UI (which sends `request`), map to `mode`,
    and return { ok, request_id, fills, metrics }.
    """
    logging.info("Received /calculate")

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
