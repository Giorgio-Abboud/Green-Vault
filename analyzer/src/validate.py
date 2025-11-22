from datetime import datetime, time, date
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException, status
import holidays, uuid, re
from typing import Any
from src.data_client import check_symbol

def validate_user_fills(timestamp: datetime, price: float, quantity: int, side: str, symbol: str) -> dict:
    field_errors = {}
    
    RFC3339_RE = re.compile(
        r"^\d{4}-\d{2}-\d{2}T"
        r"\d{2}:\d{2}:\d{2}"
        r"(?:\.\d+)?"
        r"-04:00$"
    )
    us_holidays = holidays.country_holidays('US')

    if not RFC3339_RE.match(timestamp.isoformat()):
        field_errors["timestamp"] = "Inputted timestamp must be RFC3339 with a -04:00 offset."
    elif timestamp > datetime.now(timestamp.tzinfo):
        field_errors["timestamp"] = "Inputted timestamp must not be in the future."
    elif timestamp.time() < time(10, 30) or timestamp.time() > time(17):
        field_errors["timestamp"] = "Inputted timestamp cannot be before 10:30 AM or after 5:00 PM."
    elif timestamp.weekday() >= 5:
        field_errors["timestamp"] = "Inputted timestamp cannot be on a weekend."
    elif date(timestamp.year, timestamp.month, timestamp.day) in us_holidays:
        field_errors["timestamp"] = "Inputted timestamp cannot be on a holiday."

    if isinstance(price, bool) or not isinstance(price, (int, float, Decimal)):
        field_errors["price"] = "Inputted price must be valid."
    else:
        try:
            decimal_price = Decimal(str(price))
        except (ValueError, TypeError, InvalidOperation):
            field_errors["price"] = "Inputted price must be valid."
        else:
            if not decimal_price.is_finite() or decimal_price <= 0:
                field_errors["price"] = "Inputted price must have a value larger than 0."
            elif decimal_price.as_tuple().exponent < -8:
                field_errors["price"] = "Inputted price must have at most 8 decimal places."

    if not isinstance(quantity, int):
        field_errors["quantity"] = "Inputted quantity must be a whole number."
    elif quantity <= 0:
        field_errors["quantity"] = "Inputted quantity must be larger than 0."

    if side.lower() not in {"buy", "sell"}:
        field_errors["side"] = "Inputted side must be 'buy' or 'sell'."

    SYMBOL_RE = re.compile(r"^[A-Z0-9]+$")

    if not SYMBOL_RE.match(symbol):
        field_errors["symbol"] = "Inputted symbol must be written in all caps (A-Z) and may include digits (0-9)."
    elif len(symbol) == 0 or len(symbol) > 5:
        field_errors["symbol"] = "Inputted symbol must have a length between 1 and 5 characters."
    elif not check_symbol(symbol):
        field_errors["symbol"] = "Inputted symbol must exist."


    if field_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "ok": False,
                "request_id": str(uuid.uuid4()),
                "fills": None,
                "error": "Validation failed",
                "field_errors": field_errors
            }
        )
    
    return {
        "ok": True,
        "request_id": str(uuid.uuid4())
        }

def validate_twelve_data(payload: Any) -> dict:
    field_errors: dict[str, str] = {}
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # No response at all
    if payload is None:
        field_errors["twelve_data"] = "No response received from Twelve Data."
    # Dict response (common for error or normal data)
    elif isinstance(payload, dict):
        status_val = payload.get("status")

        # Twelve Data error envelope, e.g. {"status": "error", "code": 429, "message": "..."}
        if status_val == "error":
            code = payload.get("code")
            message = str(payload.get("message") or "Unknown error from data provider.")

            # Rate limit / too many requests
            if code == 429 or "limit" in message.lower():
                field_errors["twelve_data"] = (
                    "Too many API calls to Twelve Data. Please wait a moment and try again."
                )
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            else:
                field_errors["twelve_data"] = f"Twelve Data returned an error: {message}"

        # Normal payload: check for empty values/data
        if not field_errors:
            values = payload.get("values") or payload.get("data")
            if isinstance(values, list) and len(values) == 0:
                field_errors["twelve_data"] = (
                    "Twelve Data returned no intraday bars for this symbol and time window."
                )

    # List/tuple response (some TDClient variants can return a list of rows)
    elif isinstance(payload, (list, tuple)):
        if len(payload) == 0:
            field_errors["twelve_data"] = "Twelve Data returned an empty result set."

    # Anything else is unexpected
    else:
        field_errors["twelve_data"] = "Unexpected response format from Twelve Data."

    # If anything went wrong, throw a 500 in the same shape as your existing validator
    if field_errors:
        raise HTTPException(
            status_code=status_code,
            detail={
                "ok": False,
                "request_id": str(uuid.uuid4()),
                "fills": None,
                "error": "Market data error",
                "field_errors": field_errors,
            },
        )

    # If we got here, payload looks usable
    return {
        "ok": True,
        "request_id": str(uuid.uuid4()),
    }
