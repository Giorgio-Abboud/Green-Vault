import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.service import make_calculation
from broker.broker import publish_success_event

logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CalcIn(BaseModel):
    timestamp: str
    price: str
    quantity: str
    side: str
    symbol: str
    request: str

class CalcOut(BaseModel):
    ok: bool
    request_id: str

@app.post("/calculate", response_model=CalcOut)
def calculate(body: CalcIn):
    logging.info("Received!")
    ok, req_id, payload = make_calculation(
        timestamp=body.timestamp,
        price=body.price,
        quantity=body.quantity,
        side=body.side,
        symbol=body.symbol,
        request=body.request,
    )
    if ok:
        publish_success_event(payload)
    return {"ok": ok, "request_id": req_id}
