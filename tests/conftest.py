import pandas as pd
import pytest

from analyzer.src.service import Window

TZ = "America/New_York"


@pytest.fixture(scope="module")
def base_timestamps():
    t0 = pd.Timestamp("2025-09-02 10:01:00", tz=TZ)
    t1 = t0 + pd.Timedelta(minutes=1)
    t2 = t0 + pd.Timedelta(minutes=2)
    t3 = t0 + pd.Timedelta(minutes=3)
    t5 = t0 + pd.Timedelta(minutes=5)
    t6 = t0 + pd.Timedelta(minutes=6)
    t7 = t0 + pd.Timedelta(minutes=7)
    return {"t0": t0, "t1": t1, "t2": t2, "t3": t3, "t5": t5, "t6": t6, "t7": t7}


@pytest.fixture(scope="module")
def bars_df(base_timestamps):
    data = [
        {
            "start": base_timestamps["t0"],
            "end": base_timestamps["t1"],
            "open": 99.8,
            "high": 100.6,
            "low": 99.4,
            "close": 100.0,
            "volume": 10_000,
        },
        {
            "start": base_timestamps["t1"],
            "end": base_timestamps["t2"],
            "open": 100.1,
            "high": 100.9,
            "low": 99.7,
            "close": 100.3,
            "volume": 8_000,
        },
        {
            "start": base_timestamps["t2"],
            "end": base_timestamps["t3"],
            "open": 100.5,
            "high": 101.2,
            "low": 100.0,
            "close": 100.7,
            "volume": 12_000,
        },
    ]
    return pd.DataFrame(data)


@pytest.fixture(scope="module")
def bars_with_future_df(bars_df, base_timestamps):
    future_row = {
        "start": base_timestamps["t5"],
        "end": base_timestamps["t7"],
        "open": 100.2,
        "high": 100.2,
        "low": 100.2,
        "close": 100.2,
        "volume": 1.0,
    }
    combined = pd.concat([bars_df, pd.DataFrame([future_row])], ignore_index=True)
    return combined


@pytest.fixture(scope="module")
def fills_df(base_timestamps):
    data = [
        {
            "ts": base_timestamps["t0"] + pd.Timedelta(seconds=12),
            "price": 100.10,
            "qty": 300,
        },
        {
            "ts": base_timestamps["t1"] + pd.Timedelta(seconds=5),
            "price": 100.25,
            "qty": 200,
        },
    ]
    return pd.DataFrame(data)


@pytest.fixture(scope="module")
def window_exact(base_timestamps):
    return Window(start=base_timestamps["t0"], end=base_timestamps["t3"])


@pytest.fixture(scope="module")
def window_small(base_timestamps):
    return Window(
        start=base_timestamps["t0"] - pd.Timedelta(minutes=1),
        end=base_timestamps["t3"] + pd.Timedelta(minutes=1),
    )


@pytest.fixture(scope="module")
def order_qty():
    return 1_000.0

