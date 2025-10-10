import logging
import uuid
from typing import Dict, Tuple

# ---- metric calculators (stubs) ----
def analyze(timestamp: str, price: str, quantity: str, side: str) -> Dict:
    logging.info("Starting ANALYSIS...")
    # TODO real implementation of analysis
    # example
    return {
        "vwap_slippage": "0.15",
        "shortfall": "0.04",
        "effective_spread": "0.02",
        "realized_spread": "0.01",
        "market_impact": "0.05",
        "drift": "0.03",
    }

def estimate(timestamp: str, price: str, quantity: str, side: str) -> Dict:
    logging.info("Starting ESTIMATION...")
    # TODO real implementation of estimation
    # example
    return {
        "vwap_slippage": "0.20",
        "shortfall": "0.05",
        "effective_spread": "0.03",
        "realized_spread": "0.02",
        "market_impact": "0.06",
        "drift": "0.04",
    }

# ---- orchestration ----
def make_calculation(
    *,
    timestamp: str,
    price: str,
    quantity: str,
    side: str,
    symbol: str,
    mode: str,
) -> Tuple[bool, str, Dict, Dict]:
    """
    Returns: (ok, request_id, fills_dict, metrics_dict)
    """
    # normalized mode expected here
    m = (mode or "").strip().lower()

    fills = {
        "timestamp": timestamp,
        "price": price,
        "quantity": quantity,
        "side": side,
        "symbol": symbol,
        "mode": m,
    }

    if m == "analyze":
        metrics = analyze(timestamp, price, quantity, side)
    elif m == "estimate":
        metrics = estimate(timestamp, price, quantity, side)
    else:
        logging.warning("Unknown mode %r; defaulting to analyze", mode)
        metrics = analyze(timestamp, price, quantity, side)
        
    ok = True
    req_id = str(uuid.uuid4())

    return ok, req_id, fills, metrics
