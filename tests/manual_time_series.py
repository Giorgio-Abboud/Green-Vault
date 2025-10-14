import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analyzer.src.twelve_client import build_one_minute_window, get_time_series  # noqa: E402


def main():
    symbol = "AAPL"
    timestamp = "2025-10-10T10:15:37-04:00"  # Known in-session bar (EDT)

    start_dt, end_dt = build_one_minute_window(timestamp)
    df = get_time_series(symbol, "1min", start_dt, end_dt)

    print(f"Requested symbol: {symbol}")
    print(f"Window start: {start_dt}")
    print(f"Window end:   {end_dt}")
    print()

    if df.empty:
        print("No data returned for the requested window.")
        return

    print("DataFrame preview:")
    print(df)
    print()
    print("DataFrame info:")
    df.info(memory_usage=False)


if __name__ == "__main__":
    main()
