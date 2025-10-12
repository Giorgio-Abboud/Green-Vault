import logging
import uuid
from typing import Dict, Tuple

def analyze(timestamp: str, price: float, quantity: int, side: str) -> Dict[str, float]:
    logging.info("Starting ANALYSIS...")
    # TODO: Real analysis implementation

    
    # Returned values
    return {
        "vwap_slippage": 0.5,
        "shortfall": 0.1,
        "effective_spread": 0.2,
        "realized_spread": 0.3,
        "market_impact": 0.4,
        "drift": 0.5,
    }

def estimate(timestamp: str, price: float, quantity: int, side: str) -> Dict[str, float]:
    logging.info("Starting ESTIMATION...")
    # TODO: Real estimation implementation


    # Returned values
    return {
        "vwap_slippage": 0.9,
        "shortfall": 0.8,
        "effective_spread": 0.7,
        "realized_spread": 0.6,
        "market_impact": 0.5,
        "drift": 0.4,
    }

def make_calculation(
    *,
    timestamp: str,
    price: float,
    quantity: int,
    side: str,
    symbol: str,
    mode: str,
) -> Tuple[bool, str, Dict, Dict]:
    logging.info("make_calculation called (mode=%s)", mode)
    fills = {
        "timestamp": timestamp,
        "price": price,
        "quantity": quantity,
        "side": side,
        "symbol": symbol,
        "mode": mode,
    }

    if mode == "analyze":
        metrics = analyze(timestamp, price, quantity, side)
    elif mode == "estimate":
        metrics = estimate(timestamp, price, quantity, side)
    else:
        logging.warning("Unknown mode %r; defaulting to analyze", mode)
        metrics = analyze(timestamp, price, quantity, side)

    req_id = str(uuid.uuid4())
    return True, req_id, fills, metrics
