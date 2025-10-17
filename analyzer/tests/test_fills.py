import pytest, json
from datetime import datetime
from copy import deepcopy
from analyzer.cmd.main import validate_user_fills

# TODO: Create the validation functions which this test parametrization will call

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
                    "timestamp": "Inputted timestamp cannot be before 9:30 AM or after 4:00 PM"
                }
            }
        }
    ],
    # TODO: Create more test cases based on constraints
)
def test_user_fills(fills) -> None:
    json_output = validate_user_fills(
        fills["timestamp"], 
        fills["price"], 
        fills["quantity"], 
        fills["side"], 
        fills["symbol"]
    )
    
    # output = json.loads(json_output)

    expected = deepcopy(fills["expected"])
    # expected["request_id"] = output["request_id"]
    expected["request_id"] = json_output["request_id"]

    assert json_output == expected
