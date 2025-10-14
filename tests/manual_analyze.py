import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analyzer.src.service import analyze  # noqa: E402


def main() -> None:
    symbol = "AAPL"
    timestamp = "2025-10-10T10:15:37-04:00"
    price = "256.70"
    quantity = "1000"
    side = "BUY"

    metrics = analyze(timestamp, price, quantity, side, symbol)

    print("Analyze inputs:")
    print(f"  symbol: {symbol}")
    print(f"  timestamp: {timestamp}")
    print(f"  price: {price}")
    print(f"  quantity: {quantity}")
    print(f"  side: {side}")
    print()
    print("Analyze metrics result:")

    for name, value in metrics.items():
        print(f"  {name}: {value}")


if __name__ == "__main__":
    main()
