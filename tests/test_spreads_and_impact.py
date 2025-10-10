import pandas as pd
import pytest

from analyzer.src.service import (
    effective_spread_proxy_bps,
    price_impact_bps,
    realized_spread_proxy_bps,
)


def test_effective_spread_buy(fills_df, bars_df):
    result = effective_spread_proxy_bps(+1, fills_df, bars_df)
    assert result == pytest.approx(8.01196410768, abs=1e-9)


def test_realized_spread_buy_and_impact(fills_df, bars_with_future_df):
    realized = realized_spread_proxy_bps(
        +1,
        fills_df,
        bars_with_future_df,
        horizon=pd.Timedelta(minutes=5),
    )
    effective = effective_spread_proxy_bps(+1, fills_df, bars_with_future_df)
    impact = price_impact_bps(effective, realized)
    assert realized == pytest.approx(-8.01196410768, abs=1e-9)
    assert impact == pytest.approx(16.02392821536, abs=1e-9)
