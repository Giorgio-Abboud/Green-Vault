import os, json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from twelvedata import TDClient

load_dotenv()

# Sets the timestamp to Eastern Standard Time (New York time)
def build_one_minute_window(user_ts: str) -> tuple[datetime, datetime]:
    eastern = ZoneInfo("America/New_York")

    target = datetime.fromisoformat(user_ts)
    if target.tzinfo is None:
        target = target.replace(tzinfo=eastern)

    target_eastern = target.astimezone(eastern)
    start_dt = target_eastern - timedelta(minutes=1)
    end_dt = target_eastern + timedelta(minutes=1)
    return start_dt, end_dt

_FMT = "%Y-%m-%d %H:%M:%S"  # Twelve Data expects this format for start/end

_td = None
def client() -> TDClient:
    global _td
    if _td is None:
        key = os.getenv("TWELVE_DATA_API_KEY")
        if not key:
            raise RuntimeError("TWELVE_DATA_API_KEY is not set")
        _td = TDClient(apikey=key)
    return _td


def get_time_series(
        symbol: str, 
        interval: str, 
        start_dt: datetime, 
        end_dt: datetime,
        timezone: str = "America/New_York",
    ) -> pd.DataFrame:
    """
    First calls the Twelve Data API with the given parameters.
    Turns the OHLCV data into a dataframe for the given window.
    """

    raw_payload = client().time_series(
        symbol=symbol,
        interval=interval,                     # e.g., "5min"
        start_date=start_dt.strftime(_FMT),    # "YYYY-MM-DD HH:MM:SS"
        end_date=end_dt.strftime(_FMT),
        timezone=timezone
    ).as_json()

    payload: Optional[object]
    if isinstance(raw_payload, tuple):
        payload = list(raw_payload)
    else:
        payload = raw_payload

    rows: Optional[list[dict[str, str]]]
    if isinstance(payload, dict):
        rows = payload.get("values") or payload.get("data")
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = None

    if not rows:
        return pd.DataFrame(columns=["start", "end", "open", "high", "low", "close", "volume"])

    df = pd.DataFrame(rows)
    for col in {"open", "high", "low", "close", "volume"} & set(df.columns):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    start_series = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
    interval_delta = pd.to_timedelta(interval)
    tz = ZoneInfo(timezone)

    if start_series.dt.tz is None:
        start_series = start_series.dt.tz_localize(tz)
    else:
        start_series = start_series.dt.tz_convert(tz)

    df["start"] = start_series
    df["end"] = df["start"] + interval_delta
    df.drop(columns=["datetime"], inplace=True, errors="ignore")

    ordered_cols = ["start", "end", "open", "high", "low", "close", "volume"]
    df = df.loc[:, ordered_cols]
    print(df)
    return df.sort_values("start").reset_index(drop=True)


# Check if a stock symbol exists
def check_symbol(symbol: str):
    try:
        resp = client().get_stocks_list(symbol=symbol).as_json()
        payload = json.loads(resp)
    except Exception:
        return False

    if payload.get("status") != "ok":
        return False

    items = payload.get("data", [])
    return any(item.get("symbol") == symbol for item in items)
