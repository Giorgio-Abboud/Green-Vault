import logging
import re
import uuid
from typing import Dict, Tuple, Any
from zoneinfo import ZoneInfo
from datetime import datetime

import pandas as pd
import numpy as np

from .metric import Window, compute_all_metrics, _tp_lookup, prepare_bars_df
from .twelve_client import build_one_minute_window, get_time_series
from reviewer.axes import axis_band
from reviewer.conclusion import choose_conclusion
from reviewer.formatter import build_feedback, bps_to_pct_str

# ---- user fills data frame creation ----
def _create_fills_df(timestamp, price: float, quantity: int, side: str) -> tuple[pd.DataFrame, int]:
    """Create a dataframe containing the user given inputs"""
    side_val = 1 if side.upper() == "BUY" else -1
    fill_ts = pd.Timestamp(timestamp)

    fills_df = pd.DataFrame(
        [{"ts": fill_ts, "price": float(price), "qty": int(quantity)}],
        columns=["ts", "price", "qty"],
    )

    return fills_df, side_val


NY = ZoneInfo("America/New_York")

# Normalize estimate metrics so missing values read as "undeterminable" instead of None/unavailable.
def _normalize_estimate_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    core_keys = ("vwap_slippage", "shortfall", "effective_spread", "drift")

    for key in core_keys:
        val = metrics.get(key)
        if isinstance(val, (int, float)) and not np.isfinite(val):
            clean[key] = "undeterminable"
        elif isinstance(val, str) and val.strip().lower() == "unavailable":
            clean[key] = "undeterminable"
        elif val is None:
            clean[key] = "undeterminable"
        else:
            clean[key] = val

    # Future-dependent metrics are not available in estimate mode.
    clean["realized_spread"] = "undeterminable"
    clean["market_impact"] = "undeterminable"
    return clean

# ---- metric calculators (stubs) ----
def analyze(timestamp: datetime, price: float, quantity: int, side: str, symbol: str) -> Dict:
    logging.info("Starting ANALYSIS...")

    # Execution window (±1 minute) in market time
    start_date, end_date = build_one_minute_window(str(timestamp))
    window_start_ts = pd.Timestamp(start_date)
    window_end_ts = pd.Timestamp(end_date)

    # Metrics need bars beyond the execution window (for realized spread, etc.)
    realized_horizon = pd.Timedelta(minutes=1)

    fetch_start = window_start_ts.floor("min")
    fetch_end = (window_end_ts + realized_horizon).ceil("min")

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
        window_start = window_start.tz_convert(bars_tz)
        window_end = window_end.tz_convert(bars_tz)

    # Retain bars needed for the execution window *and* the realized horizon
    horizon_end = window_end + realized_horizon
    bars_df = bars_df[
        (bars_df["end"] > window_start) & (bars_df["start"] < horizon_end)
    ].reset_index(drop=True)

    if bars_df.empty:
        logging.warning(
            "No bars overlap execution window for %s between %s and %s",
            symbol,
            window_start,
            window_end,
        )
        return {
            "vwap_slippage_bps": None,
            "effective_spread_bps": None,
            "realized_spread_1m_bps": None,
            "impact_bps": None,
            "implementation_shortfall_bps": None,
            "timing_drift_bps": None,
        }

    trade_window = Window(
        start=window_start,
        end=window_end,
    )

    # Create the user fills data frame and use the correct side format
    fills_df, fill_side = _create_fills_df(timestamp, price, quantity, side)

    # Send all required fields to compute all metrics
    metrics = compute_all_metrics(
        fill_side,
        fills_df,
        bars_df,
        trade_window,
        order_qty=quantity,
        realized_horizon=realized_horizon,
    )

    return metrics


def estimate(timestamp: datetime, price: float, quantity: int, side: str, symbol: str) -> Dict:
    logging.info("Starting ESTIMATION...")

    side_val = 1 if side.upper() == "BUY" else -1
    realized_horizon = pd.Timedelta(0)

    fill_ts = pd.Timestamp(timestamp)
    if fill_ts.tzinfo is None:
        fill_ts = fill_ts.tz_localize("America/New_York")
    else:
        fill_ts = fill_ts.tz_convert("America/New_York")

    # Build the same 1-minute window
    start_date, end_date = build_one_minute_window(fill_ts.isoformat())
    window_start_ts = pd.Timestamp(start_date)
    window_end_ts = pd.Timestamp(end_date)

    fetch_start = window_start_ts.floor("min")
    fetch_end = window_end_ts.ceil("min")

    ohlcv_df = get_time_series(symbol, "1min", fetch_start.to_pydatetime(), fetch_end.to_pydatetime())
    if ohlcv_df.empty:
        logging.warning("No OHLCV data returned for %s between %s and %s", symbol, fetch_start, fetch_end)
        return _normalize_estimate_metrics({k: None for k in ("vwap_slippage", "shortfall", "effective_spread", "realized_spread", "market_impact", "drift")})

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

    window_start = window_start_ts.tz_convert(bars_df["start"].dt.tz)
    window_end = window_end_ts.tz_convert(bars_df["start"].dt.tz)
    trade_window = Window(start=window_start, end=window_end)

    bars_prepped = prepare_bars_df(bars_df)
    mid_at_fill = _tp_lookup(bars_prepped, fill_ts)
    if not np.isfinite(mid_at_fill):
        mid_at_fill = float(price)
    spread_guess = max(0.01, 0.0005 * mid_at_fill)  # replace with live spread if you have it
    assumed_fill = mid_at_fill + (0.5 * spread_guess * side_val)

    fills_df = pd.DataFrame([{"ts": fill_ts, "price": assumed_fill, "qty": int(quantity)}], columns=["ts", "price", "qty"])

    metrics = compute_all_metrics(
        side_val,
        fills_df,
        bars_df,
        trade_window,
        order_qty=int(quantity),
        realized_horizon=realized_horizon,
    )

    return _normalize_estimate_metrics(metrics)


def make_calculation(
    *,
    timestamp: datetime,
    price: float,
    quantity: int,
    side: str,
    symbol: str,
    mode: str,
) -> Tuple[bool, str, Dict, Dict, Dict | None]:
    logging.info("make_calculation called (mode=%s)", mode)

    fills = {
        "timestamp": timestamp,
        "price": price,
        "quantity": int(quantity),
        "side": side,
        "symbol": symbol,
        "mode": mode,
    }

    if mode == "analyze":
        metrics = analyze(timestamp, price, quantity, side, symbol)
    elif mode == "estimate":
        metrics = estimate(timestamp, price, quantity, side, symbol)
    else:
        logging.warning("Unknown mode %r; defaulting to analyze", mode)
        metrics = analyze(timestamp, price, quantity, side, symbol)

    review = None
    try:
        numeric = _extract_numeric_metrics(metrics)
        if mode == "estimate":
            review = _build_estimate_review(metrics, numeric)
        else:
            # Need all six keys to build feedback; skip if incomplete
            required_keys = {"vwap_slippage", "shortfall", "effective_spread", "realized_spread", "market_impact", "drift"}
            if required_keys.issubset(numeric.keys()):
                review = build_feedback(numeric)
    except Exception:
        logging.exception("Failed to build reviewer feedback")

    req_id = str(uuid.uuid4())
    return True, req_id, fills, metrics, review


def _extract_numeric_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """
    Pull float values out of the metrics dict (which may contain strings like '12.3 bps ...').
    """
    out: Dict[str, float] = {}
    for key, val in metrics.items():
        if isinstance(val, (int, float)):
            out[key] = float(val)
            continue
        if isinstance(val, str):
            m = re.search(r"-?\d+(?:\.\d+)?", val)
            if m:
                try:
                    out[key] = float(m.group(0))
                    continue
                except ValueError:
                    pass

    return out


def _build_estimate_review(metrics: Dict[str, Any], numeric: Dict[str, float] | None = None) -> Dict[str, str]:
    """
    Build a feedback payload for estimate mode, mirroring analyze-style output
    but using only the metrics we can calculate without future data.
    """
    numeric_values = numeric if numeric is not None else _extract_numeric_metrics(metrics)

    def _axis(name: str, default: str = "neutral") -> str:
        try:
            band = axis_band(name, numeric_values)
        except Exception:
            band = None
        return band or default

    execution = _axis("execution")
    impact = _axis("impact")
    timing = _axis("timing")
    axis_summary = f"Execution {execution} | Impact {impact} | Timing {timing}"

    conclusion = choose_conclusion(execution, impact, timing)
    improve_text = conclusion.get("improve") or conclusion.get("keep", "")

    def _fmt_pct(key: str, label: str) -> str:
        if key not in numeric_values:
            return f"{label} is undeterminable."
        return f"{label} was about {bps_to_pct_str(numeric_values[key])}."

    why_lines = [
        _fmt_pct("vwap_slippage", "Your price versus VWAP"),
        _fmt_pct("shortfall", "Compared to arrival price"),
        _fmt_pct("effective_spread", "Your midpoint distance"),
        _fmt_pct("drift", "Market drift"),
    ]

    return {
        "conclusion_key": conclusion.get("key", "estimate"),
        "conclusion": conclusion.get("conclusion", "Provisional estimate based on current data."),
        "scores": axis_summary,
        "why": " ".join(why_lines),
        "improve": improve_text or "Future-dependent metrics are marked undeterminable; rerun analyze for a full review.",
        "axis_summary": axis_summary,
        "summary": f"{conclusion.get('conclusion', 'Estimate')} {improve_text}".strip(),
    }
