import math

BANDS = [
    "underperform",
    "below_avg",
    "neutral",
    "above_avg",
    "outperform",
]

METRIC_BANDS = {
    "vwap_slippage": {
        "underperform": (10, math.inf),
        "below_avg": (5, 10),
        "neutral": (2, 5),
        "above_avg": (0.5, 2),
        "outperform": (-math.inf, 0.5),
    },
    "shortfall": {
        "underperform": (15, math.inf),
        "below_avg": (7, 15),
        "neutral": (3, 7),
        "above_avg": (0, 3),
        "outperform": (-math.inf, 0),
    },
    "effective_spread": {
        "underperform": (15, math.inf),
        "below_avg": (8, 15),
        "neutral": (4, 8),
        "above_avg": (2, 4),
        "outperform": (-math.inf, 2),
    },
    "realized_spread": {
        "underperform": (10, math.inf),
        "below_avg": (4, 10),
        "neutral": (-4, 4),
        "above_avg": (-10, -4),
        "outperform": (-math.inf, -10),
    },
    "market_impact": {
        "underperform": (15, math.inf),
        "below_avg": (8, 15),
        "neutral": (3, 8),
        "above_avg": (0, 3),
        "outperform": (-math.inf, 0),
    },
    "drift": {
        "underperform": (8, math.inf),
        "below_avg": (3, 8),
        "neutral": (-3, 3),
        "above_avg": (-8, -3),
        "outperform": (-math.inf, -8),
    },
}
