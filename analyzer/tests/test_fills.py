import pytest, json
from datetime import datetime
from copy import deepcopy
from analyzer.src.validate import validate_user_fills

@pytest.mark.parametrize(
    "fills",
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-15 07:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "timestamp": "Inputted timestamp cannot be before 9:30 AM or after 4:00 PM."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-18 12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "timestamp": "Inputted timestamp cannot be on a weekend."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2024-12-25 12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "timestamp": "Inputted timestamp cannot be on a holiday."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": "256",
            "quantity": 1000,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "price": "Inputted price must be valid."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": -256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "price": "Inputted price must have a value larger than 0."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": 256.123456789,
            "quantity": 1000,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "price": "Inputted price must have at most 8 decimal places."
                }
            }
        }
    ],
    [  # SPEAK WITH RODRIGO ABOUT CONVERTING THIS INTO A FLOAT FOR FRACTIONAL STOCKS
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000.2,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "quantity": "Inputted quantity must be a whole number."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": 256.70,
            "quantity": -1000,
            "side": "buy",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "quantity": "Inputted quantity must be larger than 0."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "other",
            "symbol": "AAPL",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "side": "Inputted side must be 'buy' or 'sell'."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "TMPLR",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "symbol": "Inputted symbol must exist."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "symbol": "Inputted symbol must have a length between 1 and 5 characters."
                }
            }
        }
    ],
    [
        {
            "timestamp": datetime.fromisoformat("2025-10-20 12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "4ppl:",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "symbol": "Inputted symbol must be written in all caps (A-Z) and may include digits (0-9)."
                }
            }
        }
    ],
)
def test_user_fills(fills) -> None:
    json_output = validate_user_fills(
        fills["timestamp"], 
        fills["price"], 
        fills["quantity"], 
        fills["side"], 
        fills["symbol"]
    )
    
    # TODO: Switch to JSON once the validation function is setup

    # output = json.loads(json_output)
    expected = deepcopy(fills["expected"])
    # expected["request_id"] = output["request_id"]
    expected["request_id"] = json_output["request_id"]

    assert json_output == expected
