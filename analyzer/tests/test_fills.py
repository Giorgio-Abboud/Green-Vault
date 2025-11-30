import pytest
from datetime import datetime
from copy import deepcopy
from analyzer.src.validate import validate_user_fills
from fastapi import HTTPException, status

@pytest.mark.parametrize(
    "fills",
    [
        {
            "timestamp": datetime.fromisoformat("2026-10-15T07:00:00-04:00"),
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
                    "timestamp": "Inputted timestamp must not be in the future."
                }
            }
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-15T07:00:00-04:00"),
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
                    "timestamp": "Inputted timestamp cannot be before 10:30 AM or after 5:00 PM."
                }
            }
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-18T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2024-12-25T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "AAAAAAA",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "symbol": "Inputted symbol must have a length between 1 and 5 characters."
                }
            }
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
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
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "idk",
            "symbol": "4ppl:",
            "expected": {
                "ok": False,
                "request_id": "",
                "fills": None,
                "error": "Validation failed",
                "field_errors": {
                    "side": "Inputted side must be 'buy' or 'sell'.",
                    "symbol": "Inputted symbol must be written in all caps (A-Z) and may include digits (0-9)."
                }
            }
        },
        {
            "timestamp": datetime.fromisoformat("2025-10-20T12:00:00-04:00"),
            "price": 256.70,
            "quantity": 1000,
            "side": "buy",
            "symbol": "APPL:",
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
    ]
)
def test_user_fills(fills) -> None:
    with pytest.raises(HTTPException) as validate_fail:
        output = validate_user_fills(
            fills["timestamp"], 
            fills["price"], 
            fills["quantity"], 
            fills["side"], 
            fills["symbol"]
        )

    if validate_fail:
        error = validate_fail.value
        assert error.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        details = error.detail
        expected = deepcopy(fills["expected"])
        expected["request_id"] = details["request_id"]

        assert expected == details

    else:
        expected = deepcopy(fills["expected"])
        expected["request_id"] = output["request_id"]

        assert expected == output
