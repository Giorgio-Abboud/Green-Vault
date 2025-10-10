import pytest

from analyzer.src.service import (
    implementation_shortfall_bps,
    timing_drift_bps,
)


def test_implementation_shortfall_buy(fills_df, bars_df):
    result = implementation_shortfall_bps(+1, fills_df, bars_df)
    assert result == pytest.approx(160.000000, abs=1e-9)


def test_timing_drift_buy(bars_df, window_exact):
    result = timing_drift_bps(+1, bars_df, window_exact)
    assert result == pytest.approx(633.3333333333, abs=1e-9)
    
