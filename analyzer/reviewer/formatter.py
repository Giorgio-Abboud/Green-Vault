from typing import Dict
from .axes import axis_band
from .conclusion import choose_conclusion

def bps_to_pct_str(bps: float) -> str:
    pct = bps / 10000.0
    return f"{pct:.2%}"

def build_feedback(metrics_bps: Dict[str, float]) -> Dict[str, str]:
    """
    metrics_bps keys:
      vwap_slippage, shortfall, effective_spread,
      realized_spread, market_impact, drift
    Returns a dict you can return from your API.
    """
    exec_band   = axis_band("execution", metrics_bps)
    impact_band = axis_band("impact", metrics_bps)
    timing_band = axis_band("timing", metrics_bps)

    conclusion = choose_conclusion(exec_band, impact_band, timing_band)

    vwap = metrics_bps["vwap_slippage"]
    short = metrics_bps["shortfall"]
    eff = metrics_bps["effective_spread"]
    real = metrics_bps["realized_spread"]
    impact = metrics_bps["market_impact"]
    drift = metrics_bps["drift"]

    why_lines = [
        f"Your price was about {bps_to_pct_str(vwap)} away from the market average during your trade window.",
        f"It was about {bps_to_pct_str(short)} away from the price when you started the trade.",
        f"Your trades were roughly {bps_to_pct_str(eff)} off the midpoint, "
        f"with realized spread of {bps_to_pct_str(real)} and impact of {bps_to_pct_str(impact)}.",
        f"The market drifted around {bps_to_pct_str(drift)} during your window.",
    ]

    improve_text = conclusion.get("improve") or conclusion.get("keep", "")
    axis_summary = f"Execution {exec_band} | Impact {impact_band} | Timing {timing_band}"

    result = {
        "conclusion_key": conclusion["key"],
        "conclusion": conclusion["conclusion"],
        "scores": axis_summary,
        "why": " ".join(why_lines),
        "improve": improve_text,
        "axis_summary": axis_summary,
        "summary": f"{conclusion['conclusion']} {improve_text}".strip(),
    }
    return result
