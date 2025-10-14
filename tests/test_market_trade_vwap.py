from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from analyzer.src.metric import Window, market_vwap, trade_vwap, vwap_slippage_bps


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
    assert result == pytest.approx(-17.27574750698, abs=1e-8)


def test_market_vwap_partial_overlap():
    tz = ZoneInfo("America/New_York")
    bars = pd.DataFrame(
        [
            {
                "start": pd.Timestamp("2025-10-10 10:14:00", tz=tz),
                "end": pd.Timestamp("2025-10-10 10:15:00", tz=tz),
                "open": 255.33099,
                "high": 255.36501,
                "low": 255.03999,
                "close": 255.06500,
                "volume": 64377,
            },
            {
                "start": pd.Timestamp("2025-10-10 10:15:00", tz=tz),
                "end": pd.Timestamp("2025-10-10 10:16:00", tz=tz),
                "open": 255.08501,
                "high": 255.08501,
                "low": 254.89000,
                "close": 254.89000,
                "volume": 58938,
            },
            {
                "start": pd.Timestamp("2025-10-10 10:16:00", tz=tz),
                "end": pd.Timestamp("2025-10-10 10:17:00", tz=tz),
                "open": 254.88000,
                "high": 254.88000,
                "low": 254.88000,
                "close": 254.88000,
                "volume": 70574,
            },
        ]
    )

    window = Window(
        start=pd.Timestamp("2025-10-10 10:14:37", tz=tz),
        end=pd.Timestamp("2025-10-10 10:16:37", tz=tz),
    )

    result = market_vwap(bars, window)

    tp_1014 = (255.36501 + 255.03999 + 255.06500) / 3.0
    tp_1015 = (255.08501 + 254.89000 + 254.89000) / 3.0
    tp_1016 = (254.88000 + 254.88000 + 254.88000) / 3.0

    frac_1014 = 23 / 60
    frac_1015 = 60 / 60
    frac_1016 = 37 / 60

    eff_1014 = 64377 * frac_1014
    eff_1015 = 58938 * frac_1015
    eff_1016 = 70574 * frac_1016

    expected = (
        tp_1014 * eff_1014 + tp_1015 * eff_1015 + tp_1016 * eff_1016
    ) / (eff_1014 + eff_1015 + eff_1016)

    assert result == pytest.approx(expected, rel=1e-12)
