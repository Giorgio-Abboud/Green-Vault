import pandas as pd
import pytest

from analyzer.src.service import compute_all_metrics

EXPECTED = {
    "trade_vwap": 100.160000,
    "market_vwap": 100.33333333332,
    "vwap_slippage_bps": -17.27574750698,
    "effective_spread_bps": 8.01196410768,
    "realized_spread_5m_bps": -8.01196410768,
    "impact_bps": 16.02392821536,
    "implementation_shortfall_bps": 160.000000,
    "timing_drift_bps": 633.3333333333,
}


def test_integration_compute_all(bars_with_future_df, fills_df, window_exact, order_qty, base_timestamps):
    metrics = compute_all_metrics(
        side=+1,
        fills=fills_df,
        bars=bars_with_future_df,
        window=window_exact,
        order_qty=order_qty,
        now=base_timestamps["t3"] + pd.Timedelta(seconds=5),
    )

    for key in [
        "trade_vwap",
        "market_vwap",
        "vwap_slippage_bps",
        "effective_spread_bps",
        "realized_spread_5m_bps",
        "impact_bps",
        "implementation_shortfall_bps",
        "timing_drift_bps",
    ]:
        assert metrics[key] == pytest.approx(EXPECTED[key], abs=1e-9)

