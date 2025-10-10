import pytest

from analyzer.src.service import (
    market_vwap,
    trade_vwap,
    vwap_slippage_bps,
)


def test_trade_vwap_buy(fills_df):
    result = trade_vwap(fills_df)
    assert result == pytest.approx(100.160000, abs=1e-9)


def test_market_vwap_window(bars_df, window_exact):
    result = market_vwap(bars_df, window_exact)
    assert result == pytest.approx(100.33333333332, abs=1e-9)


def test_vwap_slippage_buy(bars_df, fills_df, window_exact):
    trade_price = trade_vwap(fills_df)
    market_price = market_vwap(bars_df, window_exact)
    result = vwap_slippage_bps(+1, trade_price, market_price)
    assert result == pytest.approx(-17.27574750698, abs=1e-9)
