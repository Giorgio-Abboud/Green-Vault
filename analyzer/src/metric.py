from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ========================================
# Pre-Processing Functions
# ========================================

@dataclass(frozen=True)
class Window:
    """Inclusive/exclusive window with timezone-aware boundaries."""

    start: pd.Timestamp
    end: pd.Timestamp

    def __post_init__(self) -> None:
        def _ensure_ts(value: Any, name: str) -> pd.Timestamp:
            ts = pd.Timestamp(value)
            if ts.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
            return ts

        start = _ensure_ts(self.start, "start")
        end = _ensure_ts(self.end, "end")
        if end <= start:
            raise ValueError("end must be greater than start")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)


def _ensure_dataframe(df: Any, name: str) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame")
    return df


def _ensure_side(side: int) -> int:
    if side not in (-1, 1):
        raise ValueError("side must be +1 for BUY or -1 for SELL")
    return side


def prepare_bars_df(bars: pd.DataFrame) -> pd.DataFrame:
    """Normalise OHLCV bars and add HLC3 midpoint."""

    df = _ensure_dataframe(bars, "bars").copy()
    required = ["start", "end", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"bars missing required columns: {missing}")

    df["start"] = pd.to_datetime(df["start"], utc=False)
    df["end"] = pd.to_datetime(df["end"], utc=False)
    if df["start"].isna().any() or df["end"].isna().any():
        raise ValueError("start/end must be valid timestamps")
    if df["start"].dt.tz is None or df["end"].dt.tz is None:
        raise ValueError("start/end must be timezone-aware")
    if (df["end"] <= df["start"]).any():
        raise ValueError("bar end must be greater than start")

    float_cols = ["open", "high", "low", "close", "volume"]
    for col in float_cols:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(float)

    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3.0
    df.sort_values("start", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def prepare_fills_df(fills: pd.DataFrame) -> pd.DataFrame:
    """Normalise trade fills and ensure numeric fields."""

    df = _ensure_dataframe(fills, "fills").copy()
    required = ["ts", "price", "qty"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"fills missing required columns: {missing}")

    df["ts"] = pd.to_datetime(df["ts"], utc=False)
    if df["ts"].isna().any():
        raise ValueError("ts must be valid timestamps")
    if df["ts"].dt.tz is None:
        raise ValueError("ts must be timezone-aware")

    for col in ["price", "qty"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(float)

    df.sort_values("ts", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def overlap_fraction(bar_start: pd.Timestamp, bar_end: pd.Timestamp, win: Window) -> float:
    """Fraction of a bar that overlaps a window, bounded to [0, 1]."""

    start = pd.Timestamp(bar_start)
    end = pd.Timestamp(bar_end)
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("bar_start and bar_end must be timezone-aware")
    if end <= start:
        raise ValueError("bar_end must be greater than bar_start")
    if start.tzinfo != win.start.tzinfo or end.tzinfo != win.end.tzinfo:
        raise ValueError("bar and window must share timezone")

    overlap_start = max(start, win.start)
    overlap_end = min(end, win.end)
    overlap = (overlap_end - overlap_start).total_seconds()
    length = (end - start).total_seconds()
    if overlap <= 0 or length <= 0:
        return 0.0
    frac = overlap / length
    return float(max(0.0, min(1.0, frac)))


def add_overlap_volume(bars: pd.DataFrame, win: Window) -> pd.DataFrame:
    """Annotate bars with overlap fraction and effective volume."""

    df = prepare_bars_df(bars)
    fractions: List[float] = []
    for start, end in zip(df["start"], df["end"]):
        fractions.append(overlap_fraction(start, end, win))
    df["overlap_frac"] = fractions
    df["vol_eff"] = df["overlap_frac"] * df["volume"]
    return df


def _tp_lookup(df: pd.DataFrame, timestamp: pd.Timestamp) -> float:
    "Mid point of a specific instant."
    
    mask = (df["start"] <= timestamp) & (timestamp < df["end"])
    if not mask.any():
        return float(np.nan)
    value = df.loc[mask, "tp"].iloc[0]
    return float(value)


def _tp_at_offset_prepared(df: pd.DataFrame, timestamp: pd.Timestamp, offset: pd.Timedelta) -> float:
    "Mid point of an instant including the offset (5 minute bars)."

    target = timestamp + offset
    first_start = df["start"].min()
    last_end = df["end"].max()
    epsilon = pd.Timedelta(microseconds=1)
    if target >= last_end:
        target = last_end - epsilon
    if target < first_start:
        target = first_start
    return _tp_lookup(df, target)


# ========================================
# Metric Calculation Functions
# ========================================

def market_vwap(bars: pd.DataFrame, win: Window) -> float:
    """Overlap-weighted market VWAP using HLC3 mid as price."""

    df = add_overlap_volume(bars, win)
    df = df[df["overlap_frac"] > 0]
    if df.empty:
        return float(np.nan)
    
    # effective volume beloning to your window of purchase
    # ex. first fill 10:01:12 to last fill 10:06:12
    total_vol = df["vol_eff"].sum()
    if total_vol <= 0 or not np.isfinite(total_vol):
        return float(np.nan)

    tp = df["tp"]
    vwap = (tp * df["vol_eff"]).sum() / total_vol
    return float(vwap)


def trade_vwap(fills: pd.DataFrame) -> float:
    """Quantity-weighted average price of the executed fills."""

    df = prepare_fills_df(fills)
    total_qty = df["qty"].sum()
    if total_qty <= 0 or not np.isfinite(total_qty):
        return float(np.nan)
    
    vwap = (df["price"] * df["qty"]).sum() / total_qty
    return float(vwap)


def vwap_slippage_bps(side: int, trade_vwap: float, mkt_vwap: float) -> float:
    """Signed VWAP slippage in basis points."""

    _ensure_side(side)
    if not np.isfinite(trade_vwap) or not np.isfinite(mkt_vwap) or mkt_vwap <= 0:
        return float(np.nan)
    
    # Represents the user's perfomance
    # Positive = worse (buying above / selling below market) and Negative = better
    slippage = side * (trade_vwap - mkt_vwap) / mkt_vwap * 10_000.0
    return float(slippage)


def _qty_weighted_average(values: List[float], weights: List[float]) -> float:
    """Averge effective spread proxy bps based on the total number of user fills."""

    total_weight = float(np.sum(weights))
    if total_weight <= 0 or not np.isfinite(total_weight):
        return float(np.nan)
    
    # Account for varying user fills
    weighted = float(np.sum(np.array(values) * np.array(weights)) / total_weight)
    return weighted


def effective_spread_proxy_bps(side: int, fills: pd.DataFrame, bars: pd.DataFrame) -> float:
    """Qty-weighted effective spread proxy in bps."""

    _ensure_side(side)
    fills_df = prepare_fills_df(fills)
    bars_df = prepare_bars_df(bars)

    spreads: List[float] = []
    qtys: List[float] = []

    for row in fills_df.itertuples(index=False):
        tp_fill = _tp_lookup(bars_df, row.ts)
        if not np.isfinite(tp_fill) or tp_fill <= 0:
            continue
        price = float(row.price)
        qty = float(row.qty)
        if qty <= 0:
            continue

        # Calculate the spread of a fill, and store its value
        # and its volume to average it out
        spread = 2.0 * side * (price - tp_fill) / tp_fill * 10_000.0
        spreads.append(spread)
        qtys.append(qty)

    return _qty_weighted_average(spreads, qtys)


def realized_spread_proxy_bps(
    side: int,
    fills: pd.DataFrame,
    bars: pd.DataFrame,
    horizon: pd.Timedelta = pd.Timedelta(minutes=5),
) -> float:
    """Qty-weighted realized spread proxy in bps."""

    _ensure_side(side)
    if not isinstance(horizon, pd.Timedelta):
        raise TypeError("horizon must be a pandas Timedelta")

    fills_df = prepare_fills_df(fills)
    bars_df = prepare_bars_df(bars)

    spreads: List[float] = []
    qtys: List[float] = []
    for row in fills_df.itertuples(index=False):
        tp_fill = _tp_lookup(bars_df, row.ts)
        tp_future = _tp_at_offset_prepared(bars_df, row.ts, horizon)
        if not np.isfinite(tp_fill) or tp_fill <= 0:
            continue
        if not np.isfinite(tp_future):
            continue
        price = float(row.price)
        qty = float(row.qty)
        if qty <= 0:
            continue
        spread = 2.0 * side * (price - tp_future) / tp_fill * 10_000.0
        spreads.append(spread)
        qtys.append(qty)

    return _qty_weighted_average(spreads, qtys)


def price_impact_bps(effective_bps: float, realized_bps: float) -> float:
    """Estimate of price impact as effective minus realized spreads."""

    if not np.isfinite(effective_bps) or not np.isfinite(realized_bps):
        return float(np.nan)
    return float(effective_bps - realized_bps)


def implementation_shortfall_bps(
    side: int,
    fills: pd.DataFrame,
    bars: pd.DataFrame,
    arrival_ts: Optional[pd.Timestamp] = None,
) -> float:
    """Implementation shortfall in bps versus arrival benchmark."""

    _ensure_side(side)
    fills_df = prepare_fills_df(fills)
    if fills_df.empty:
        return float(np.nan)

    bars_df = prepare_bars_df(bars)
    trade_v = trade_vwap(fills_df)
    if not np.isfinite(trade_v):
        return float(np.nan)

    if arrival_ts is not None:
        arrival_ts = pd.Timestamp(arrival_ts)
        if arrival_ts.tzinfo is None:
            raise ValueError("arrival_ts must be timezone-aware")
    else:
        arrival_ts = fills_df.loc[0, "ts"]

    arrival_tp = _tp_lookup(bars_df, arrival_ts)
    if not np.isfinite(arrival_tp) or arrival_tp <= 0:
        return float(np.nan)

    shortfall = side * (trade_v - arrival_tp) / arrival_tp * 10_000.0
    return float(shortfall)


def timing_drift_bps(side: int, bars: pd.DataFrame, win: Window) -> float:
    """Side-signed TP drift across a window in bps."""

    _ensure_side(side)
    bars_df = prepare_bars_df(bars)
    start_tp = _tp_lookup(bars_df, win.start)
    end_probe = win.end - pd.Timedelta(microseconds=1)
    end_tp = _tp_lookup(bars_df, end_probe)

    if not np.isfinite(start_tp) or not np.isfinite(end_tp) or start_tp <= 0:
        return float(np.nan)

    drift = side * (end_tp - start_tp) / start_tp * 10_000.0
    return float(drift)


def compute_all_metrics(
    side: int,
    fills: pd.DataFrame,
    bars: pd.DataFrame,
    window: Window,
    order_qty: float,
    *,
    arrival_ts: Optional[pd.Timestamp] = None,
    realized_horizon: pd.Timedelta = pd.Timedelta(minutes=5),
    ref_horizon: pd.Timedelta = pd.Timedelta(minutes=5),
    interval_minutes: int = 1,
    now: Optional[pd.Timestamp] = None,
) -> Dict[str, Any]:
    """Compute the complete metric suite."""

    _ensure_side(side)
    bars_df = prepare_bars_df(bars)
    fills_df = prepare_fills_df(fills) if not fills.empty else pd.DataFrame(columns=["ts", "price", "qty"])

    trade_v = trade_vwap(fills_df) if not fills_df.empty else float(np.nan)
    market_v = market_vwap(bars_df, window)
    vwap_slip = vwap_slippage_bps(side, trade_v, market_v)
    eff_spread = effective_spread_proxy_bps(side, fills_df, bars_df)
    realized_spread = realized_spread_proxy_bps(side, fills_df, bars_df, realized_horizon)
    impact = price_impact_bps(eff_spread, realized_spread)
    impl_short = implementation_shortfall_bps(side, fills_df, bars_df, arrival_ts)
    timing = timing_drift_bps(side, bars_df, window)
    now_ts = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz=bars_df["start"].dt.tz)

    metrics: Dict[str, Any] = {
        "trade_vwap": float(trade_v) if np.isfinite(trade_v) else float(np.nan),
        "market_vwap": float(market_v) if np.isfinite(market_v) else float(np.nan),
        "vwap_slippage_bps": float(vwap_slip) if np.isfinite(vwap_slip) else float(np.nan),
        "effective_spread_bps": float(eff_spread) if np.isfinite(eff_spread) else float(np.nan),
        "realized_spread_5m_bps": float(realized_spread) if np.isfinite(realized_spread) else float(np.nan),
        "impact_bps": float(impact) if np.isfinite(impact) else float(np.nan),
        "implementation_shortfall_bps": float(impl_short) if np.isfinite(impl_short) else float(np.nan),
        "timing_drift_bps": float(timing) if np.isfinite(timing) else float(np.nan),
        "notes": ["OHLCV-only; TP(HLC3) as mid proxy; overlap-weighted volume"], 
    }
    return metrics
