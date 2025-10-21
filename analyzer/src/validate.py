from datetime import datetime, time, date
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException
import holidays, uuid, re
from analyzer.src.twelve_client import check_symbol

def validate_user_fills(timestamp: datetime, price: float, quantity: int, side: str, symbol: str) -> dict:
    field_errors = {}
    
    RFC3339_RE = re.compile(
        r"^\d{4}-\d{2}-\d{2}T"
        r"\d{2}:\d{2}:\d{2}"
        r"(?:\.\d+)?"
        r"(?:Z|[+-]\d{2}:\d{2})$"
    )
    us_holidays = holidays.country_holidays('US')

    if not RFC3339_RE.match(timestamp.isoformat()):
        field_errors["timestamp"] = "Inputted timestamp must be of RFC3339 format."
    elif timestamp.time() < time(9, 30) or timestamp.time() > time(16):
        field_errors["timestamp"] = "Inputted timestamp cannot be before 9:30 AM or after 4:00 PM."
    elif timestamp.weekday() >= 5:
        field_errors["timestamp"] = "Inputted timestamp cannot be on a weekend."
    elif date(timestamp.year, timestamp.month, timestamp.day) in us_holidays:
        field_errors["timestamp"] = "Inputted timestamp cannot be on a holiday."

    try:
        decimal_price = Decimal(str(price))
    except (ValueError, TypeError, InvalidOperation):
        field_errors["price"] = "Inputted price must be valid."
    else:
        if decimal_price <= 0:
            field_errors["price"] = "Inputted price must have a value larger than 0."
        elif decimal_price.as_tuple().exponent < -8:
            field_errors["price"] = "Inputted price must have at most 8 decimal places."

    if not isinstance(quantity, int):
        field_errors["quantity"] = "Inputted quantity must be a whole number."
    elif quantity <= 0:
        field_errors["quantity"] = "Inputted quantity must be larger than 0."

    if side.lower() != "buy" or side.lower() != "sell":
        field_errors["side"] = "Inputted side must be 'buy' or 'sell'."

    SYMBOL_RE = re.compile(r"^[A-Z0-9]+$")

    if not SYMBOL_RE.match(symbol):
        field_errors["symbol"] = "Inputted symbol must be written in all caps (A-Z) and may include digits (0-9)."
    elif len(symbol) == 0 or len(symbol) > 5:
        field_errors["symbol"] = "Inputted symbol must have a length between 1 and 5 characters."
    elif not check_symbol(symbol):
        field_errors["symbol"] = "Inputted symbol must exist."

    # This is failing in purpose, make implementation for validation
    payload = {
        "ok": True,
        "request_id": uuid.uuid4(),
        "fills": None,
        "error": "Validation failed",
        "field_errors": field_errors
        } if field_errors else {}
    
    return payload
