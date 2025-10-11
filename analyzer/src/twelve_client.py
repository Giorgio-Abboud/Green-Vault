import os
from datetime import datetime
from twelvedata import TDClient

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

def get_latest_price(symbol: str):
    return client().price(symbol=symbol).as_json()

def get_time_series(symbol: str, interval: str, start_dt: datetime, end_dt: datetime, timezone: str = "America/New_York"):
    return client().time_series(
        symbol=symbol,
        interval=interval,                     # e.g., "5min"
        start_date=start_dt.strftime(_FMT),    # "YYYY-MM-DD HH:MM:SS"
        end_date=end_dt.strftime(_FMT),
        timezone=timezone
    ).as_json()
