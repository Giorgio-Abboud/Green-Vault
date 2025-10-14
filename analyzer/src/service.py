import logging
import uuid
from typing import Dict, Tuple
from zoneinfo import ZoneInfo

import pandas as pd

from .metric import Window, compute_all_metrics
from .twelve_client import build_one_minute_window, get_time_series

# ---- user fills data frame creation ----
def _create_fills_df(timestamp, price: float, quantity: int, side: str) -> tuple[pd.DataFrame, int]:
    """Create a dataframe containing the user given inputs"""
    side_val = 1 if side.upper() == "BUY" else -1
    fill_ts = pd.Timestamp(timestamp)  # your ISO string already carries -04:00

    if fill_ts.tzinfo is None:
        fill_ts = fill_ts.tz_localize("America/New_York")
    else:
        fill_ts = fill_ts.tz_convert("America/New_York")

    fills_df = pd.DataFrame(
        [{"ts": fill_ts, "price": float(price), "qty": int(quantity)}],
        columns=["ts", "price", "qty"],
    )

    return fills_df, side_val


NY = ZoneInfo("America/New_York")

# ---- metric calculators (stubs) ----
def analyze(timestamp: str, price: str, quantity: str, side: str, symbol: str) -> Dict:
    logging.info("Starting ANALYSIS...")

    price_float = float(price)
    quantity_int = int(quantity)

    # Create the start and end dates for the API call
    start_date, end_date = build_one_minute_window(str(timestamp))

    # Fetch a slightly expanded bar range to ensure partial minutes are included
    window_start_ts = pd.Timestamp(start_date)
    window_end_ts = pd.Timestamp(end_date)
    fetch_start = window_start_ts.floor("min")
    fetch_end = window_end_ts.ceil("min")

    # Create a dataframe containing all the stock bars between fetch_start and fetch_end
    ohlcv_df = get_time_series(symbol, "1min", fetch_start.to_pydatetime(), fetch_end.to_pydatetime())
    if ohlcv_df.empty:
        logging.warning(
            "No OHLCV data returned for %s between %s and %s",
            symbol,
            start_date,
            end_date,
        )
        return {
            "trade_vwap": float("nan"),
            "market_vwap": float("nan"),
            "vwap_slippage_bps": float("nan"),
            "effective_spread_bps": float("nan"),
            "realized_spread_1m_bps": float("nan"),
            "impact_bps": float("nan"),
            "implementation_shortfall_bps": float("nan"),
            "timing_drift_bps": float("nan"),
        }

    bars_df = ohlcv_df.copy()
    if "start" not in bars_df.columns or "end" not in bars_df.columns:
        raise ValueError("Expected start/end columns from Twelve Data adapter")

    bars_df["start"] = pd.to_datetime(bars_df["start"])
    bars_df["end"] = pd.to_datetime(bars_df["end"])

    if bars_df["start"].dt.tz is None:
        bars_df["start"] = bars_df["start"].dt.tz_localize("America/New_York")
        bars_df["end"] = bars_df["end"].dt.tz_localize("America/New_York")
    else:
        bars_df["start"] = bars_df["start"].dt.tz_convert("America/New_York")
        bars_df["end"] = bars_df["end"].dt.tz_convert("America/New_York")

    bars_df = bars_df[["start", "end", "open", "high", "low", "close", "volume"]].sort_values("start").reset_index(drop=True)

    bars_tz = bars_df["start"].dt.tz
    window_start = window_start_ts
    window_end = window_end_ts

    if bars_tz is not None and len(bars_df):
        if window_start.tzinfo is None:
            window_start = window_start.tz_localize(bars_tz)
        else:
            window_start = window_start.tz_convert(bars_tz)
        if window_end.tzinfo is None:
            window_end = window_end.tz_localize(bars_tz)
        else:
            window_end = window_end.tz_convert(bars_tz)

    # Keep only bars that overlap the execution window
    bars_df = bars_df[
        (bars_df["end"] > window_start) & (bars_df["start"] < window_end)
    ].reset_index(drop=True)

    if bars_df.empty:
        logging.warning(
            "No bars overlap execution window for %s between %s and %s",
            symbol,
            window_start,
            window_end,
        )
        return {
            "trade_vwap": float("nan"),
            "market_vwap": float("nan"),
            "vwap_slippage_bps": float("nan"),
            "effective_spread_bps": float("nan"),
            "realized_spread_1m_bps": float("nan"),
            "impact_bps": float("nan"),
            "implementation_shortfall_bps": float("nan"),
            "timing_drift_bps": float("nan"),
        }

    trade_window = Window(
        start=window_start,
        end=window_end,
    )

    # Create the user fills data frame and use the correct side format
    fills_df, fill_side = _create_fills_df(timestamp, price_float, quantity_int, side)

    # Send all required fields to compute all metrics
    metrics = compute_all_metrics(
        fill_side,
        fills_df,
        bars_df,
        trade_window,
        order_qty=quantity_int,
    )

    return metrics


def estimate(timestamp: str, price: str, quantity: str, side: str, symbol: str) -> Dict:
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
        "quantity": int(quantity),
        "side": side,
        "symbol": symbol,
        "mode": m,
    }

    if m == "analyze":
        metrics = analyze(timestamp, price, quantity, side, symbol)
    elif m == "estimate":
        metrics = estimate(timestamp, price, quantity, side, symbol)
    else:
        logging.warning("Unknown mode %r; defaulting to analyze", mode)
        metrics = analyze(timestamp, price, quantity, side, symbol)
        
    ok = True
    req_id = str(uuid.uuid4())

    return ok, req_id, fills, metrics
