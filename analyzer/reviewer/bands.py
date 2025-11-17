import math

BANDS = ["underperform", "below_avg", "neutral", "above_avg", "outperform"]

VWAP_SLIPPAGE_BANDS = {
    "underperform": (20, math.inf),
    "below_avg": (10, 20),
    "neutral": (-5, 10),
    "above_avg": (-15, -5),
    "outperform" : (-math.inf, -15)
}

SHORTFALL_BANDS = {
    "underperform": (45, math.inf),
    "below_avg": (20, 45),
    "neutral": (-10, 20),
    "above_avg": (-30, -10),
    "outperform" : (-math.inf, -30)
}

EFFECTIVE_SPREAD_BANDS = {
    "underperform": (25, math.inf),
    "below_avg": (10, 25),
    "neutral": (3, 10),
    "above_avg": (0, 3),
    "outperform" : (-math.inf, 0)
}

REALIZED_SPREAD_BANDS = {
    "underperform": (30, math.inf),
    "below_avg": (10, 30),
    "neutral": (-10, 10),
    "above_avg": (-25, -10),
    "outperform" : (-math.inf, -25)
}

MARKET_IMPACT_BANDS = {
    "underperform": (35, math.inf),
    "below_avg": (15, 35),
    "neutral": (-5, 15),
    "above_avg": (-20, -5),
    "outperform" : (-math.inf, -20)
}

DRIFT_BANDS = {
    "underperform": (45, math.inf),
    "below_avg": (20, 45),
    "neutral": (-15, 20),
    "above_avg": (-40, -15),
    "outperform" : (-math.inf, -40)
}

METRIC_BANDS = {
    "vwap_slippage": VWAP_SLIPPAGE_BANDS,
    "shortfall": SHORTFALL_BANDS,
    "effective_spread": EFFECTIVE_SPREAD_BANDS,
    "realized_spread": REALIZED_SPREAD_BANDS,
    "market_impact": MARKET_IMPACT_BANDS,
    "drift": DRIFT_BANDS
}

def band_analyzer(metric: str, value: float) -> str:
    band = METRIC_BANDS[metric]

    for name, (low, high) in band.items():
        if low <= value < high:
            return name
        
    return None
