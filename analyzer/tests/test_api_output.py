import math
import pandas as pd
import pytest
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")

#In real usage this would fetch from the Twelve Data API
# but here we create a sample dataframe for testing purposes.
@pytest.fixture
def sample_bars_df():
    # create 5 contiguous 1-minute bars starting at 2025-06-03 10:15:00-04:00
    start = pd.Timestamp("2025-06-03T10:15:00-04:00").tz_convert(TZ)
    starts = pd.date_range(start=start, periods=5, freq="1T", tz=TZ)
    ends = starts + pd.Timedelta(minutes=1)

    open_p = [100.0, 100.5, 101.0, 100.8, 101.2]
    high_p = [100.7, 101.1, 101.3, 101.0, 101.5]
    low_p = [99.8, 100.4, 100.9, 100.7, 101.0]
    close_p = [100.5, 101.0, 100.95, 101.0, 101.4]
    volume = [1000, 500, 200, 0, 1500]

    df = pd.DataFrame(
        {
            "start": starts,
            "end": ends,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume,
        }
    )
    # ensure typical ordering/indexing
    df = df.sort_values("start").reset_index(drop=True)
    return df


def test_required_columns(sample_bars_df):
    required = {"start", "end", "open", "high", "low", "close", "volume"}
    assert required.issubset(set(sample_bars_df.columns))


def test_timestamps_tz_aware_and_same_tz(sample_bars_df):
    tzs = {ts.tz for ts in sample_bars_df["start"]}
    # all starts should have tzinfo and same tz object
    assert all(getattr(ts, "tz", None) is not None for ts in sample_bars_df["start"])
    assert len(tzs) == 1, "All start timestamps must use the same timezone"


def test_start_before_end_and_interval(sample_bars_df):
    delta = sample_bars_df["end"] - sample_bars_df["start"]
    # each delta should equal 1 minute
    assert all(d == pd.Timedelta(minutes=1) for d in delta)


def test_starts_sorted_and_unique(sample_bars_df):
    starts = sample_bars_df["start"]
    assert starts.is_monotonic_increasing
    assert starts.is_unique


def test_bars_contiguous(sample_bars_df):
    # next start == current end for contiguous bars
    starts = sample_bars_df["start"]
    ends = sample_bars_df["end"]
    for i in range(len(sample_bars_df) - 1):
        assert starts.iloc[i + 1] == ends.iloc[i]


def test_start_aligned_to_minute_boundary(sample_bars_df):
    # For 1-minute bars the seconds and microseconds should be zero
    for ts in sample_bars_df["start"]:
        assert ts.second == 0 and ts.microsecond == 0


def test_price_columns_numeric_and_positive(sample_bars_df):
    for col in ["open", "high", "low", "close"]:
        series = sample_bars_df[col]
        assert pd.api.types.is_numeric_dtype(series)
        assert not series.isna().any()
        assert all(math.isfinite(float(v)) for v in series)
        assert (series > 0).all()


def test_high_low_relationships(sample_bars_df):
    open_ = sample_bars_df["open"]
    high = sample_bars_df["high"]
    low = sample_bars_df["low"]
    close = sample_bars_df["close"]

    assert (high >= open_).all()
    assert (high >= close).all()
    assert (high >= low).all()
    assert (low <= open_).all()
    assert (low <= close).all()
    assert (low <= high).all()


def test_volume_integer_nonnegative(sample_bars_df):
    vol = sample_bars_df["volume"]
    assert (vol >= 0).all()
    # integer-like (values equal to their integer cast)
    assert (vol.astype(int) == vol).all()


def test_no_missing_required_values(sample_bars_df):
    req = ["start", "end", "open", "high", "low", "close", "volume"]
    assert not sample_bars_df[req].isna().any().any()

def test_start_column_is_datetime_with_tz(sample_bars_df):
    # ensure dtype is datetime with timezone
    assert pd.api.types.is_datetime64tz_dtype(sample_bars_df["start"])


def test_dataframe_index_is_reset(sample_bars_df):
    # Ensure typical consumer expectation: RangeIndex after reset
    df = sample_bars_df.reset_index(drop=True)
    assert isinstance(df.index, pd.RangeIndex)
    assert list(df.index) == list(range(len(df)))


def test_empty_dict_payload_raises():
    with pytest.raises(HTTPException) as exc:
        validateAPI.validate_twelvedata_output({})
    assert exc.value.status_code == 500

def test_data_recency_check_raises():
    # build a df with an extremely old timestamp
    old_start = pd.Timestamp(datetime.now(tz=TZ) - timedelta(days=365 * 30)).tz_convert(TZ)
    starts = pd.date_range(start=old_start, periods=2, freq="1T", tz=TZ)
    ends = starts + pd.Timedelta(minutes=1)
    df = pd.DataFrame({
        "start": starts,
        "end": ends,
        "open": [1.0, 1.0],
        "high": [1.0, 1.0],
        "low": [1.0, 1.0],
        "close": [1.0, 1.0],
        "volume": [0, 0],
    })
    with pytest.raises(HTTPException) as exc:
        validateAPI.validate_twelvedata_output(df, max_age_days=365*5)  # 5 years max -> should fail for 30y old
    assert exc.value.status_code == 500


def test_excessive_api_calls_raises(sample_bars_df):
    with pytest.raises(HTTPException) as exc:
        validateAPI.validate_twelvedata_output(sample_bars_df, api_call_count=101, max_api_calls=100)
    assert exc.value.status_code == 500
