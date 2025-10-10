from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


log = logging.getLogger(__name__)


# ========================================
# Pre-Processing Functions
# ========================================

@dataclass(frozen=True)
class Window:
    """
    Inclusive/exclusive time window with tz-aware bounds.
    We treat bars as half-open intervals [start, end) and windows similarly.
    This convention avoids off-by-one overlap at boundaries.
    """

    start: pd.Timestamp
    end: pd.Timestamp

    def __post_init__(self) -> None:
        def _ensure_ts(value: Any, name: str) -> pd.Timestamp:
            ts = pd.Timestamp(value)
            if ts.tzinfo is None:
                log.error("%s must be timezone-aware", name)
                raise ValueError(f"{name} must be timezone-aware")
            return ts

        start = _ensure_ts(self.start, "start")
        end = _ensure_ts(self.end, "end")
        if end <= start:
            log.error("Window end (%s) must be greater than start (%s)", end, start)
            raise ValueError("end must be greater than start")

        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        log.debug("Window created: start=%s, end=%s", self.start, self.end)


def _ensure_dataframe(df: Any, name: str) -> pd.DataFrame:
    """
    Validate that an object is a pandas DataFrame.
    """

    if not isinstance(df, pd.DataFrame):
        log.error("%s must be a pandas DataFrame", name)
        raise TypeError(f"{name} must be a pandas DataFrame")
    return df


def _ensure_side(side: int) -> int:
    """
    Validate trading side.
    We use the convention that multiplying by 'side' flips signs appropriately:
    - For BUY, costs above mid are positive (worse).
    - For SELL, prices below mid are positive (worse).
    """

    if side not in (-1, 1):
        log.error("Invalid side=%s (must be +1 for BUY or -1 for SELL)", side)
        raise ValueError("side must be +1 for BUY or -1 for SELL")
    log.debug("Order side validated: %s", side)
    return side


def prepare_bars_df(bars: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OHLCV bars and add HLC3 typical price as mid proxy.
    Expected Columns:
    ['start', 'end', 'open', 'high', 'low', 'close', 'volume']
    'tp' (HLC3) is our mid-price proxy for OHLCV-only workflows.
    """

    df = _ensure_dataframe(bars, "bars").copy()
    required = ["start", "end", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        log.error("bars missing required columns: %s", missing)
        raise ValueError(f"bars missing required columns: {missing}")

    df["start"] = pd.to_datetime(df["start"], utc=False)
    df["end"] = pd.to_datetime(df["end"], utc=False)
    if df["start"].isna().any() or df["end"].isna().any():
        log.error("Bar start/end contain NaTs")
        raise ValueError("start/end must be valid timestamps")
    if df["start"].dt.tz is None or df["end"].dt.tz is None:
        log.error("Bar start/end must be timezone-aware")
        raise ValueError("start/end must be timezone-aware")
    if (df["end"] <= df["start"]).any():
        log.error("Found bar with end <= start")
        raise ValueError("bar end must be greater than start")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(float)

    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3.0
    df.sort_values("start", inplace=True)
    df.reset_index(drop=True, inplace=True)

    log.debug(
        "Prepared bars: rows=%d, tz=%s, first=%s, last=%s",
        len(df),
        df["start"].dt.tz.iloc[0],
        df["start"].min(),
        df["end"].max(),
    )
    return df


def prepare_fills_df(fills: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize trade fills and ensure numeric fields.
    - We do not drop zero/negative qty here; downstream metrics handle that.
    - Sorting by 'ts' is important for horizon-based lookups.
    """

    df = _ensure_dataframe(fills, "fills").copy()
    required = ["ts", "price", "qty"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        log.error("fills missing required columns: %s", missing)
        raise ValueError(f"fills missing required columns: {missing}")

    df["ts"] = pd.to_datetime(df["ts"], utc=False)
    if df["ts"].isna().any():
        log.error("Fill timestamps contain NaTs")
        raise ValueError("ts must be valid timestamps")
    if df["ts"].dt.tz is None:
        log.error("Fill timestamps must be timezone-aware")
        raise ValueError("ts must be timezone-aware")

    for col in ["price", "qty"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(float)

    df.sort_values("ts", inplace=True)
    df.reset_index(drop=True, inplace=True)

    log.debug(
        "Prepared fills: rows=%d, tz=%s, first=%s, last=%s, total_qty=%.6f",
        len(df),
        df["ts"].dt.tz.iloc[0] if len(df) else None,
        df["ts"].min() if len(df) else None,
        df["ts"].max() if len(df) else None,
        df["qty"].sum() if len(df) else 0.0,
    )
    return df


def overlap_fraction(bar_start: pd.Timestamp, bar_end: pd.Timestamp, win: Window) -> float:
    """
    Fraction of a bar that overlaps a given window, clamped to [0, 1].
    This powers the overlap-weighted volume scheme for Market VWAP.
    """

    start = pd.Timestamp(bar_start)
    end = pd.Timestamp(bar_end)
    if start.tzinfo is None or end.tzinfo is None:
        log.error("bar_start and bar_end must be timezone-aware")
        raise ValueError("bar_start and bar_end must be timezone-aware")
    if end <= start:
        log.error("bar_end must be greater than bar_start")
        raise ValueError("bar_end must be greater than bar_start")
    if start.tzinfo != win.start.tzinfo or end.tzinfo != win.end.tzinfo:
        log.error("Bar and window must share timezone")
        raise ValueError("bar and window must share timezone")

    overlap_start = max(start, win.start)
    overlap_end = min(end, win.end)
    overlap = (overlap_end - overlap_start).total_seconds()
    length = (end - start).total_seconds()
    if overlap <= 0 or length <= 0:
        return 0.0
    frac = overlap / length
    frac_clamped = float(max(0.0, min(1.0, frac)))
    log.debug(
        "overlap_fraction: bar=[%s,%s), win=[%s,%s), frac=%.6f",
        start, end, win.start, win.end, frac_clamped
    )
    return frac_clamped


def add_overlap_volume(bars: pd.DataFrame, win: Window) -> pd.DataFrame:
    """
    Annotate bars with overlap fraction and effective volume.
    'vol_eff' is used as the volume weight when computing Market VWAP restricted
    to the execution window—so partial bars contribute proportionally.
    """

    df = prepare_bars_df(bars)
    fractions: List[float] = []
    for start, end in zip(df["start"], df["end"]):
        fractions.append(overlap_fraction(start, end, win))
    df["overlap_frac"] = fractions
    df["vol_eff"] = df["overlap_frac"] * df["volume"]
    log.debug(
        "add_overlap_volume: rows=%d, sum_vol=%.6f, sum_vol_eff=%.6f",
        len(df), df["volume"].sum(), df["vol_eff"].sum()
    )
    return df


def _tp_lookup(df: pd.DataFrame, timestamp: pd.Timestamp) -> float:
    """
    Look up the HLC3 typical price that covers a given instant.
    Bars are treated as [start, end). If `timestamp` equals a bar's 'end', it
    belongs to the next bar (if any).
    """

    mask = (df["start"] <= timestamp) & (timestamp < df["end"])
    if not mask.any():
        log.debug("_tp_lookup: ts=%s not covered by any bar", timestamp)
        return float(np.nan)
    value = float(df.loc[mask, "tp"].iloc[0])
    log.debug("_tp_lookup: ts=%s -> tp=%.8f", timestamp, value)
    return value


def _tp_at_offset_prepared(df: pd.DataFrame, timestamp: pd.Timestamp, offset: pd.Timedelta) -> float:
    """
    Typical price at 'timestamp + offset', clamped into [first_start, last_end).
    Used by realized-spread to probe the mid after a horizon (e.g., +5 minutes).
    """

    target = timestamp + offset
    first_start = df["start"].min()
    last_end = df["end"].max()
    epsilon = pd.Timedelta(microseconds=1)

    if target >= last_end:
        target = last_end - epsilon
    if target < first_start:
        target = first_start

    tp = _tp_lookup(df, target)
    log.debug(
        "_tp_at_offset_prepared: base=%s offset=%s target=%s tp=%.8f",
        timestamp, offset, target, tp
    )
    return tp


# ========================================
# Metric Calculation Functions
# ========================================

def market_vwap(bars: pd.DataFrame, win: Window) -> float:
    """
    Overlap-weighted Market VWAP over 'win' using HLC3 as the price proxy.
    A proxy for the "market's average trading level" during your execution window,
    where each bar's price (TP) is weighted by the proportion of that bar which
    overlaps the window times its volume.
    """

    df = add_overlap_volume(bars, win)
    df = df[df["overlap_frac"] > 0]
    if df.empty:
        log.warning("market_vwap: no overlapping bars for window")
        return float(np.nan)

    total_vol = df["vol_eff"].sum()
    if total_vol <= 0 or not np.isfinite(total_vol):
        log.warning("market_vwap: non-positive or non-finite total effective volume")
        return float(np.nan)

    tp = df["tp"]
    vwap = float((tp * df["vol_eff"]).sum() / total_vol)
    log.debug("market_vwap: total_vol_eff=%.6f vwap=%.8f", total_vol, vwap)
    return vwap


def trade_vwap(fills: pd.DataFrame) -> float:
    """
    Quantity-weighted average execution price across your fills.
    This is *your* achieved average execution price, weighting each fill by
    executed quantity. It answers: "On average, what did I pay/receive?"
    """

    df = prepare_fills_df(fills)
    total_qty = df["qty"].sum()
    if total_qty <= 0 or not np.isfinite(total_qty):
        log.warning("trade_vwap: non-positive or non-finite total qty")
        return float(np.nan)

    vwap = float((df["price"] * df["qty"]).sum() / total_qty)
    log.debug("trade_vwap: total_qty=%.6f vwap=%.8f", total_qty, vwap)
    return vwap


def vwap_slippage_bps(side: int, trade_vwap: float, mkt_vwap: float) -> float:
    """
    Side-signed VWAP slippage in basis points: how you did vs. market VWAP.
    Formula:
    bps = side * (trade_vwap - mkt_vwap) / mkt_vwap * 10_000
    Slippage in bps. Positive = worse (BUY above / SELL below market).
    """

    _ensure_side(side)
    if not np.isfinite(trade_vwap) or not np.isfinite(mkt_vwap) or mkt_vwap <= 0:
        log.warning("vwap_slippage_bps: invalid inputs trade_vwap=%.8f mkt_vwap=%.8f", trade_vwap, mkt_vwap)
        return float(np.nan)

    slippage = float(side * (trade_vwap - mkt_vwap) / mkt_vwap * 10_000.0)
    log.debug("vwap_slippage_bps: side=%d trade=%.8f market=%.8f -> bps=%.3f", side, trade_vwap, mkt_vwap, slippage)
    return slippage


def _qty_weighted_average(values: List[float], weights: List[float]) -> float:
    """
    Quantity-weighted average of 'values' using 'weights'.
    Used to aggregate per-fill spread proxies (weights = fill quantities).
    """

    total_weight = float(np.sum(weights))
    if total_weight <= 0 or not np.isfinite(total_weight):
        log.warning("_qty_weighted_average: non-positive or non-finite total weight")
        return float(np.nan)

    weighted = float(np.sum(np.array(values) * np.array(weights)) / total_weight)
    log.debug(
        "_qty_weighted_average: n=%d total_weight=%.6f result=%.8f",
        len(values), total_weight, weighted
    )
    return weighted


def effective_spread_proxy_bps(side: int, fills: pd.DataFrame, bars: pd.DataFrame) -> float:
    """
    Qty-weighted effective spread proxy in basis points.
    Per-fill Formula:
    eff_bps_fill = 2 * side * (exec_price - mid_at_fill) / mid_at_fill * 10_000
    Quantity-weighted across fills.
    Approximates how far executions were from contemporaneous mid (HLC3).
    """

    _ensure_side(side)
    fills_df = prepare_fills_df(fills)
    bars_df = prepare_bars_df(bars)

    spreads: List[float] = []
    qtys: List[float] = []

    for row in fills_df.itertuples(index=False):
        tp_fill = _tp_lookup(bars_df, row.ts)
        if not np.isfinite(tp_fill) or tp_fill <= 0:
            log.debug("effective_spread: skip fill (no TP) ts=%s", row.ts)
            continue
        price = float(row.price)
        qty = float(row.qty)
        if qty <= 0:
            log.debug("effective_spread: skip fill (qty<=0) ts=%s qty=%.6f", row.ts, qty)
            continue

        spread = 2.0 * side * (price - tp_fill) / tp_fill * 10_000.0
        spreads.append(spread)
        qtys.append(qty)

    result = _qty_weighted_average(spreads, qtys)
    log.debug("effective_spread_proxy_bps: result=%.3f bps", result)
    return result


def realized_spread_proxy_bps(
    side: int,
    fills: pd.DataFrame,
    bars: pd.DataFrame,
    horizon: pd.Timedelta = pd.Timedelta(minutes=5),
) -> float:
    """
    Qty-weighted realized spread proxy in basis points.
    Per-fill Formula:
    real_bps_fill = 2 * side * (exec_price - future_mid) / current_mid * 10_000
    where:
      - current_mid = TP at fill time
      - future_mid  = TP at (fill time + horizon), clamped into bar range
    Captures spread that “remains” after a short horizon. If much of the
    execution deviation reverts, realized spread tends to be smaller than effective.
    """

    _ensure_side(side)
    if not isinstance(horizon, pd.Timedelta):
        log.error("horizon must be a pandas Timedelta")
        raise TypeError("horizon must be a pandas Timedelta")

    fills_df = prepare_fills_df(fills)
    bars_df = prepare_bars_df(bars)

    spreads: List[float] = []
    qtys: List[float] = []
    for row in fills_df.itertuples(index=False):
        tp_fill = _tp_lookup(bars_df, row.ts)
        tp_future = _tp_at_offset_prepared(bars_df, row.ts, horizon)
        if not np.isfinite(tp_fill) or tp_fill <= 0:
            log.debug("realized_spread: skip fill (no current TP) ts=%s", row.ts)
            continue
        if not np.isfinite(tp_future):
            log.debug("realized_spread: skip fill (no future TP) ts=%s", row.ts)
            continue

        price = float(row.price)
        qty = float(row.qty)
        if qty <= 0:
            log.debug("realized_spread: skip fill (qty<=0) ts=%s qty=%.6f", row.ts, qty)
            continue

        spread = 2.0 * side * (price - tp_future) / tp_fill * 10_000.0
        spreads.append(spread)
        qtys.append(qty)

    result = _qty_weighted_average(spreads, qtys)
    log.debug("realized_spread_proxy_bps: result=%.3f bps (horizon=%s)", result, horizon)
    return result


def price_impact_bps(effective_bps: float, realized_bps: float) -> float:
    """
    Heuristic price impact in basis points.
    Formula:
    impact_bps = effective_bps - realized_bps
    Component of execution cost that did not revert by the horizon; often
    attributed to market impact / information leakage.
    """

    if not np.isfinite(effective_bps) or not np.isfinite(realized_bps):
        log.warning("price_impact_bps: invalid inputs effective=%.8f realized=%.8f", effective_bps, realized_bps)
        return float(np.nan)
    impact = float(effective_bps - realized_bps)
    log.debug("price_impact_bps: effective=%.3f realized=%.3f -> impact=%.3f", effective_bps, realized_bps, impact)
    return impact


def implementation_shortfall_bps(
    side: int,
    fills: pd.DataFrame,
    bars: pd.DataFrame,
    arrival_ts: Optional[pd.Timestamp] = None,
) -> float:
    """
    Implementation shortfall in basis points vs. arrival benchmark.
    Formula:
    shortfall_bps = side * (TradeVWAP - ArrivalTP) / ArrivalTP * 10_000
    Classic measure vs. the price when the order arrived. Positive = worse.
    """

    _ensure_side(side)
    fills_df = prepare_fills_df(fills)
    if fills_df.empty:
        log.warning("implementation_shortfall_bps: no fills")
        return float(np.nan)

    bars_df = prepare_bars_df(bars)
    trade_v = trade_vwap(fills_df)
    if not np.isfinite(trade_v):
        log.warning("implementation_shortfall_bps: trade_vwap is NaN")
        return float(np.nan)

    if arrival_ts is not None:
        arrival_ts = pd.Timestamp(arrival_ts)
        if arrival_ts.tzinfo is None:
            log.error("arrival_ts must be timezone-aware")
            raise ValueError("arrival_ts must be timezone-aware")
    else:
        arrival_ts = fills_df.loc[0, "ts"]

    arrival_tp = _tp_lookup(bars_df, arrival_ts)
    if not np.isfinite(arrival_tp) or arrival_tp <= 0:
        log.warning("implementation_shortfall_bps: invalid arrival TP")
        return float(np.nan)

    shortfall = float(side * (trade_v - arrival_tp) / arrival_tp * 10_000.0)
    log.debug(
        "implementation_shortfall_bps: side=%d trade=%.8f arrival_tp=%.8f -> bps=%.3f",
        side, trade_v, arrival_tp, shortfall
    )
    return shortfall


def timing_drift_bps(side: int, bars: pd.DataFrame, win: Window) -> float:
    """
    Side-signed TP drift across the window in basis points.
    Formula:
    drift_bps = side * (TP_end - TP_start) / TP_start * 10_000
    Measures market movement during execution. For a BUY, rising markets
    increase drift (positive); for a SELL, the same rise becomes negative when
    signed by side.
    """
    _ensure_side(side)
    bars_df = prepare_bars_df(bars)
    start_tp = _tp_lookup(bars_df, win.start)
    end_probe = win.end - pd.Timedelta(microseconds=1)  # keep inside last bar
    end_tp = _tp_lookup(bars_df, end_probe)

    if not np.isfinite(start_tp) or not np.isfinite(end_tp) or start_tp <= 0:
        log.warning("timing_drift_bps: invalid start/end TP")
        return float(np.nan)

    drift = float(side * (end_tp - start_tp) / start_tp * 10_000.0)
    log.debug(
        "timing_drift_bps: side=%d start_tp=%.8f end_tp=%.8f -> bps=%.3f",
        side, start_tp, end_tp, drift
    )
    return drift


def compute_all_metrics(
    side: int,
    fills: pd.DataFrame,
    bars: pd.DataFrame,
    window: Window,
    order_qty: float,
    *,
    arrival_ts: Optional[pd.Timestamp] = None,
    realized_horizon: pd.Timedelta = pd.Timedelta(minutes=5),
    ref_horizon: pd.Timedelta = pd.Timedelta(minutes=5),  # reserved for future use
    interval_minutes: int = 1,                             # bar size hint for UIs
    now: Optional[pd.Timestamp] = None,
) -> Dict[str, Any]:
    """
    Compute the complete TCA metric suite from OHLCV only.
    - Price-valued metrics (Trade/Market VWAP) are in the instrument's units.
    - All "bps" metrics are basis points with side-signing: positive is worse.
    - This is an OHLCV-only estimator; mid = HLC3.
    - Market VWAP uses overlap-weighted volume within 'window'.
    - A UI can decide 'provisional' status based on latest bar completeness.
        (high/low/close/volume are not final until the bar's end time passes)
    """
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

    # Timestamp of computation (useful for UIs, provisional flags, etc.)
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
        # "computed_at": str(now_ts),  # uncomment if you want this in output
    }

    log.info(
        "compute_all_metrics: side=%d order_qty=%.6f interval=%dm realized_horizon=%s -> %s",
        side, float(order_qty), int(interval_minutes), str(realized_horizon), metrics
    )
    return metrics
