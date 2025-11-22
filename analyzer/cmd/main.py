import logging
from datetime import datetime, timedelta, timezone
from typing import Literal, Annotated
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, BeforeValidator
from src.service import make_calculation
from src.validate import validate_user_fills

logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


MetricValue = Annotated[float | str | None, Field(default=None)]

class Metric(BaseModel):
    vwap_slippage: MetricValue
    shortfall: MetricValue
    effective_spread: MetricValue
    realized_spread: MetricValue
    market_impact: MetricValue
    drift: MetricValue


class Review(BaseModel):
    conclusion_key: str | None = None
    conclusion: str | None = None
    scores: str | None = None
    why: str | None = None
    improve: str | None = None
    axis_summary: str | None = None
    summary: str | None = None

class CalcOut(BaseModel):
    ok: bool
    request_id: str = Field(..., description="Trace ID for the calculation")
    fills: Fill
    metrics: Metric
    review: Review | None = None

EST_OFFSET = timedelta(hours=-4)
EST_TZINFO = timezone(EST_OFFSET, name="EST")

def overwrite_offset(ts: datetime) -> datetime:
    if ts.utcoffset() != EST_OFFSET:
        return ts.replace(tzinfo=EST_TZINFO)
    return ts

# -------------------- Endpoint --------------------
@app.post("/calculate", response_model=CalcOut)
def calculate(body: CalcIn):
    logging.info("Received /calculate")
    try:
        logging.info(body.timestamp)
        timestamp = overwrite_offset(body.timestamp)
        logging.info(timestamp)

        req = (body.request or "").strip().lower()
        if req == "analyze":
            mode = "analyze"
        elif req == "estimate":
            mode = "estimate"
        else:
            logging.warning("Unknown request %r; defaulting to analyze", body.request)
            mode = "analyze"
        
        try:
            validate_user_fills(
                timestamp=timestamp,
                price=body.price,
                quantity=body.quantity,
                side=body.side,
                symbol=body.symbol,
            )
        except HTTPException as validate_fail:
            return JSONResponse(content=validate_fail.detail, status_code=validate_fail.status_code)

        ok, req_id, fills, metrics, review = make_calculation(
            timestamp=timestamp,
            price=body.price,
            quantity=body.quantity,
            side=body.side,
            symbol=body.symbol,
            mode=mode,
        )

        return {"ok": ok, "request_id": req_id, "fills": fills, "metrics": metrics, "review": review}

    except Exception as e:
        logging.exception("Error in /calculate")
        return {
            "ok": False,
            "request_id": "",
            "fills": None,
            "metrics": {"error": str(e)},
        }
