import uuid
from datetime import datetime, timezone

def make_calculation(
    timestamp: str,
    price: str,
    quantity: str,
    side: str,
):
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
        "ok": ok,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return ok, req_id, payload
