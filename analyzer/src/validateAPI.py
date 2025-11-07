import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import uuid

from fastapi import HTTPException, status
import pandas as pd
import numpy as np


def validate_twelvedata_output(
    payload,
    *,
    symbol: str | None = None,
    interval: str = "1min",
    tz: str = "America/New_York",
    require_contiguous: bool = True,
    max_age_days: int = 365 * 20,
    api_call_count: int | None = None,
    max_api_calls: int | None = None,
) -> dict:
    """
    Validate the DataFrame (or parsed payload) returned by the Twelve Data parsing layer.

    - payload: expected to be a pandas.DataFrame with columns:
        ["start", "end", "open", "high", "low", "close", "volume"]
      or a dict/other object (checked and rejected if empty).
    - interval: pandas-compatible offset string (e.g., "1min").
    - tz: expected timezone name for timestamps.
    - api_call_count / max_api_calls: optional simple protection against excessive requests.
    - Returns dict {"ok": True, "request_id": ...} on success,
      otherwise raises HTTPException(status 500) with a detail dict similar to validate_user_fills.
    """

    field_errors: dict = {}
    request_id = str(uuid.uuid4())

    # Basic payload sanity checks
    if isinstance(payload, dict):
        if len(payload) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "ok": False,
                    "request_id": request_id,
                    "error": "Twelve Data response was empty (dict).",
                    "field_errors": {"payload": "Empty dictionary returned from data API"},
                },
            )
        # not a DataFrame -> attempt to coerce if it looks like tabular JSON
        try:
            df = pd.DataFrame(payload)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "ok": False,
                    "request_id": request_id,
                    "error": "Twelve Data returned non-tabular payload and cannot be parsed to DataFrame.",
                    "field_errors": {"payload": "Unparseable payload"},
                },
            )
    elif isinstance(payload, pd.DataFrame):
        df = payload.copy()
    else:
        # try to coerce other types
        try:
            df = pd.DataFrame(payload)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "ok": False,
                    "request_id": request_id,
                    "error": "Twelve Data returned unexpected payload type.",
                    "field_errors": {"payload": "Unexpected payload type"},
                },
            )

    # Excessive requests guard (caller may supply counts)
    if api_call_count is not None and max_api_calls is not None:
        if api_call_count > max_api_calls:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "ok": False,
                    "request_id": request_id,
                    "error": "Excessive API requests detected.",
                    "field_errors": {"api_calls": f"{api_call_count} > {max_api_calls}"},
                },
            )

    # Required columns
    required = {"start", "end", "open", "high", "low", "close", "volume"}
    missing = required.difference(set(df.columns))
    if missing:
        field_errors["columns"] = f"Missing required columns: {sorted(list(missing))}"
        # cannot proceed without required columns
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "ok": False,
                "request_id": request_id,
                "error": "Missing required columns in OHLCV output.",
                "field_errors": field_errors,
            },
        )

    # Ensure datetimes parseable
    try:
        starts = pd.to_datetime(df["start"])
        ends = pd.to_datetime(df["end"])
    except Exception:
        field_errors["datetime"] = "Could not parse 'start'/'end' as datetimes"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "ok": False,
                "request_id": request_id,
                "error": "Datetime parsing failed.",
                "field_errors": field_errors,
            },
        )

    # timezone-awareness and consistency
    tz_obj = ZoneInfo(tz)
    # if pandas Series is timezone-aware, .dt.tz returns tzinfo; otherwise None
    if getattr(starts.dt, "tz", None) is None:
        field_errors["timestamps"] = "Start timestamps are not timezone-aware"
    else:
        # compare string forms to allow equivalent tz objects
        tzs = {str(ts.tz) for ts in starts}
        if len(tzs) != 1 or str(tz_obj) not in tzs:
            field_errors["timestamps"] = f"Timestamps must use a single timezone '{tz}'"

    if field_errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "ok": False,
                "request_id": request_id,
                "error": "Timezone validation failed for OHLCV timestamps.",
                "field_errors": field_errors,
            },
        )

    # start < end and interval checks
    deltas = ends - starts
    try:
        expected_delta = pd.to_timedelta(interval)
    except Exception:
        expected_delta = None

    if (deltas <= pd.Timedelta(0)).any():
        field_errors["start_end"] = "Some rows have start >= end"

    if expected_delta is not None and not (deltas == expected_delta).all():
        field_errors["interval"] = f"Not all rows have delta == {expected_delta}"

    # starts sorted and unique
    if not starts.is_monotonic_increasing:
        field_errors["ordering"] = "'start' is not monotonically increasing"
    if not starts.is_unique:
        field_errors["ordering"] = "'start' values are not unique"

    # contiguity
    if require_contiguous and len(df) >= 2:
        mismatches = []
        for i in range(len(df) - 1):
            if starts.iloc[i + 1] != ends.iloc[i]:
                mismatches.append(i)
                break
        if mismatches:
            field_errors["contiguity"] = "Bars are not contiguous (next.start != current.end)"

    # alignment to interval boundary for minute-based intervals
    if expected_delta is not None and expected_delta >= pd.Timedelta(minutes=1):
        misaligned = False
        for ts in starts:
            sec = getattr(ts, "second", 0)
            usec = getattr(ts, "microsecond", 0)
            if sec != 0 or usec != 0:
                misaligned = True
                break
        if misaligned:
            field_errors["alignment"] = "Start timestamps are not aligned to minute boundary"

    # price columns numeric, finite, positive
    for col in ["open", "high", "low", "close"]:
        series = df[col]
        if not pd.api.types.is_numeric_dtype(series):
            field_errors.setdefault("types", []).append(f"{col} is not numeric")
            continue
        if series.isna().any():
            field_errors.setdefault("types", []).append(f"{col} contains NaN")
        finite_ok = series.apply(lambda v: math.isfinite(float(v))).all()
        if not finite_ok:
            field_errors.setdefault("types", []).append(f"{col} contains non-finite values")
        if not (series > 0).all():
            field_errors.setdefault("values", []).append(f"{col} must be > 0")

    # high/low relationships
    try:
        if not ((df["high"] >= df[["open", "close", "low"]].max(axis=1)).all()):
            field_errors.setdefault("bounds", []).append("Some 'high' values are less than open/close/low")
        if not ((df["low"] <= df[["open", "close", "high"]].min(axis=1)).all()):
            field_errors.setdefault("bounds", []).append("Some 'low' values are greater than open/close/high")
    except Exception:
        field_errors.setdefault("bounds", []).append("Could not evaluate high/low relationships")

    # volume checks: non-negative, integer-like
    vol = df["volume"]
    if not pd.api.types.is_numeric_dtype(vol):
        field_errors.setdefault("volume", []).append("volume column not numeric")
    else:
        if (vol < 0).any():
            field_errors.setdefault("volume", []).append("volume contains negative values")
        # integer-like test using mod 1 (works for floats that represent integers)
        try:
            if not np.all((vol % 1) == 0):
                field_errors.setdefault("volume", []).append("volume contains non-integer values")
        except Exception:
            # fallback: attempt integer cast comparison
            if not (vol.astype(int) == vol).all():
                field_errors.setdefault("volume", []).append("volume contains non-integer values")

    # DataFrame sorted and reset index expectation
    if not df.index.is_monotonic_increasing:
        field_errors.setdefault("index", []).append("DataFrame index not monotonic increasing")
    # no missing values in required columns
    if df[list(required)].isna().any().any():
        field_errors.setdefault("nulls", []).append("NaN values present in required columns")

    # check data recency
    if len(starts):
        earliest = starts.min().to_pydatetime()
        if earliest < (datetime.now(tz_obj) - timedelta(days=max_age_days)):
            field_errors.setdefault("recency", []).append(f"Data too old: earliest start {earliest.isoformat()}")

    # Final decision
    if field_errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "ok": False,
                "request_id": request_id,
                "error": "Twelve Data OHLCV validation failed.",
                "field_errors": field_errors,
            },
        )

    # success
    return {"ok": True, "request_id": request_id, "rows": len(df)}