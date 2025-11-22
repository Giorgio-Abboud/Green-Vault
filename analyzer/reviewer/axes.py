import math
from typing import Dict
from .band import METRIC_BANDS, BANDS

BAND_TO_SCORE = {name: i for i, name in enumerate(BANDS)}
SCORE_TO_BAND = {i: name for name, i in BAND_TO_SCORE.items()}

AXES = {
    "execution": ["vwap_slippage", "shortfall"],
    "impact": ["effective_spread", "realized_spread", "market_impact"],
    "timing": ["drift"]
}

def band_outcome(metric: str, value: float) -> str:
    bands = METRIC_BANDS[metric]
    for name, (low, high) in bands.items():
        lo_ok = (low == -math.inf) or (value >= low)
        hi_ok = (high == math.inf) or (value < high)
        if lo_ok and hi_ok:
            return name
    return None

def axis_band(axis: str, metrics: Dict[str, float]) -> str:
    metric_names = AXES[axis]
    scores = []

    for m in metric_names:
        if m not in metrics:
            continue
        b = band_outcome(m, metrics[m])
        if b is None:
            continue
        scores.append(BAND_TO_SCORE[b])

    if not scores:
        return None

    avg = sum(scores) / len(scores)
    return SCORE_TO_BAND[round(avg)]
