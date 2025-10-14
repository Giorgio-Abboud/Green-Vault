import logging
from datetime import datetime
from typing import Any, Dict, Optional, Literal, Annotated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, BeforeValidator
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
Ticker = Annotated[str, Field(pattern=r"^[A-Z]+$", strip_whitespace=True)]
RequestMode = Annotated[
    Literal["analyze", "estimate"],
    BeforeValidator(lambda v: v.strip().lower() if isinstance(v, str) else v),
]

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

# =============================================================================
# Metrics Output Schema — Examples & Conventions
#
# All fields are optional numeric values (float) and may be null when
# a metric is not computable for the given input/window/data.
#
# Units:
# - trade_vwap, market_vwap: PRICE (e.g., USD/share)
# - All *_bps fields: basis points (bps). 1 bps = 0.01% = 0.0001 in ratio terms
#
# Missing values:
# - Use JSON `null` (Python None) when a metric cannot be computed
#   (e.g., no overlapping bars, zero effective volume, missing side, etc.).
#
# Rounding (suggested for presentation; store full precision if you like):
# - Prices: 4–6 decimals
# - BPS metrics: 2 decimals
#
# --------------------------
# Example JSON (full set)
# --------------------------
# {
#   "trade_vwap": 190.1200,
#   "market_vwap": 190.0854,
#   "vwap_slippage_bps": 18.20,
#   "effective_spread_bps": 5.40,
#   "realized_spread_5m_bps": -7.10,
#   "impact_bps": 12.30,
#   "implementation_shortfall_bps": 22.55,
#   "timing_drift_bps": 3.90
# }

# =============================================================================

MetricValue = Annotated[float | None, Field(default=None)]

class Metric(BaseModel):
    trade_vwap: MetricValue
    market_vwap: MetricValue
    vwap_slippage_bps: MetricValue
    effective_spread_bps: MetricValue
    realized_spread_1m_bps: MetricValue
    impact_bps: MetricValue
    implementation_shortfall_bps: MetricValue
    timing_drift_bps: MetricValue

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
