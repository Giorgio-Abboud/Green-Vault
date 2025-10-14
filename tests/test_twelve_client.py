import os

import pandas as pd
import pytest

from analyzer.src.twelve_client import build_one_minute_window, get_time_series


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TWELVE_DATA_API_KEY"),
    reason="TWELVE_DATA_API_KEY must be set to call Twelve Data",
)
def test_get_time_series_returns_populated_dataframe():
    """
    Calls the live Twelve Data API to ensure get_time_series returns OHLCV rows.
    """
    start_dt, end_dt = build_one_minute_window("2024-06-03T10:15:37-04:00")

    df = get_time_series("AAPL", "1min", start_dt, end_dt)

    assert not df.empty, "Expected at least one AAPL bar in the requested window"

    expected_cols = {"datetime", "open", "high", "low", "close", "volume"}
    assert expected_cols.issubset(df.columns)

    assert pd.api.types.is_datetime64_any_dtype(
        df["datetime"]
    ), "datetime column should be datetime64"

    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(
            df[col]
        ), f"{col} column should be numeric"

