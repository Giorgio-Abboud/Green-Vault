import logging
import uuid
from datetime import datetime, timezone

def analyze(timestamp: str, price: str, quantity: str, side: str) -> bool:
    logging.info("Starting ANALYSIS...")
    # TODO: real analysis here
    return True

def estimate(timestamp: str, price: str, quantity: str, side: str) -> bool:
    logging.info("Starting ESTIMATION...")
    # TODO: real estimation here
    return True

def make_calculation(
    *,
    timestamp: str,
    price: str,
    quantity: str,
    side: str,
    request: str,
):
    
    if request == "Analyze":
        response = analyze(timestamp, price, quantity, side)
    elif request == "Estimate":
        response = estimate(timestamp, price, quantity, side)
    else:
        # Unknown request; default to analyze
        logging.warning("Unknown request type %r, defaulting to Analyze", request)
        response = analyze(timestamp, price, quantity, side)

    ok = True
    req_id = str(uuid.uuid4())
    payload = {
        "schema_version": 1,
        "event_type": "CALCULATION_SUCCEEDED",
        "request_id": req_id,
        "timestamp": timestamp,
        "price": price,
        "quantity": quantity,
        "side": side,
        "request": request,
        "successful": response,
        "ok": ok,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return ok, req_id, payload
