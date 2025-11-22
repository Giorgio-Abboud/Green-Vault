import json
import os
from typing import Any

from dotenv import load_dotenv
from twelvedata import TDClient

load_dotenv()

_td: TDClient | None = None


def client() -> TDClient:
    """
    Shared Twelve Data client singleton.
    """
    global _td
    if _td is None:
        key = os.getenv("TWELVE_DATA_API_KEY")
        if not key:
            raise RuntimeError("TWELVE_DATA_API_KEY is not set")
        _td = TDClient(apikey=key)
    return _td


def _parse_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None
    return payload


def check_symbol(symbol: str) -> bool:
    """
    Verify symbol existence using Twelve Data.
    """
    try:
        raw = client().get_stocks_list(symbol=symbol, country="United States").as_json()
        payload = _parse_payload(raw)
        if payload is None:
            return False

        rows = None
        if isinstance(payload, dict):
            rows = payload.get("data") or payload.get("symbols") or payload.get("values")
        if rows is None:
            rows = payload

        return any(isinstance(row, dict) and row.get("symbol") == symbol for row in rows)
    except Exception:
        return False
