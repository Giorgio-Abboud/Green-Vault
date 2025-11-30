import math
from typing import Dict
from .axes import axis_band
from .conclusion import choose_conclusion


PRICE_STRONG_THRESHOLD = 10.0
PRICE_INLINE_THRESHOLD = 2.0
IMPACT_MOVE_THRESHOLD = 5.0
DRIFT_NEUTRAL_THRESHOLD = 3.0


def bps_to_pct_str(bps: float) -> str:
    """
    Convert basis points to a simple, rounded percentage string for users.
    Always uses the absolute value; direction is expressed in the text.
    """
    pct = abs(bps) / 100.0  # 1 bps = 0.01%
    if pct >= 1:
        return f"{pct:.0f}%"
    if pct >= 0.1:
        return f"{pct:.1f}%"
    return f"{pct:.2f}%"


def _is_valid_number(val: float) -> bool:
    return isinstance(val, (int, float)) and math.isfinite(val)


def _price_headline(vwap: float, shortfall: float) -> str:
    """
    High-level take on execution price vs market/arrival.
    """
    if not (_is_valid_number(vwap) or _is_valid_number(shortfall)):
        return "Price results were mixed versus the market."

    # Use whichever price metric had the bigger move.
    primary = vwap if abs(vwap) >= abs(shortfall) else shortfall
    pct = bps_to_pct_str(primary)

    if primary >= PRICE_STRONG_THRESHOLD:
        # Positive = worse for both buys and sells (by your metric convention).
        return f"You overpaid (or sold too low) by about {pct} versus the market."
    if primary <= -PRICE_STRONG_THRESHOLD:
        # Negative = better.
        return f"You got a better price than the market by about {pct} overall."
    if abs(primary) <= PRICE_INLINE_THRESHOLD:
        return "Your price was roughly in line with where the market was trading."
    return f"Your price was about {pct} away from the market level."


def _drift_headline(drift: float) -> str:
    """
    Short headline about timing: was the tape helping or hurting you?
    """
    if not _is_valid_number(drift):
        return ""
    if abs(drift) < DRIFT_NEUTRAL_THRESHOLD:
        return "The market was mostly flat while you traded."
    if drift > 0:
        return "You were trading into a move against you."
    return "The market move was leaning in your favor while you traded."


def _impact_headline(impact: float) -> str:
    """
    Short headline about permanent price impact.
    """
    if not _is_valid_number(impact):
        return ""
    if impact >= IMPACT_MOVE_THRESHOLD:
        return "Your trading nudged the market in your direction."
    if impact <= -IMPACT_MOVE_THRESHOLD:
        return "Prices later moved back in your favor."
    return ""


def _spread_detail(effective: float, realized: float) -> str:
    """
    Explain spread-related metrics in plain language.
    effective_spread ≈ total spread cost vs mid.
    realized_spread ≈ how much of that cost remained after prices settled.
    """
    eff_ok = _is_valid_number(effective)
    real_ok = _is_valid_number(realized)

    if not (eff_ok or real_ok):
        return ""

    parts = []

    if eff_ok:
        eff_pct = bps_to_pct_str(effective)
        if effective > PRICE_INLINE_THRESHOLD:
            parts.append(
                f"On average you paid about {eff_pct} of spread cost versus the mid price on each share."
            )
        elif effective < -PRICE_INLINE_THRESHOLD:
            parts.append(
                f"On average you captured about {eff_pct} of price improvement relative to the mid price."
            )
        else:
            parts.append("You stayed close to the mid price on most of your fills.")

    if real_ok:
        real_pct = bps_to_pct_str(realized)
        if realized > PRICE_INLINE_THRESHOLD:
            parts.append(
                f"Roughly {real_pct} of that cost was still there after prices settled, so little of it washed out."
            )
        elif realized < -PRICE_INLINE_THRESHOLD:
            parts.append(
                f"Prices later moved in your favor by about {real_pct}, undoing part of the initial spread cost."
            )
        else:
            parts.append("Most of the short-term spread move washed out after your trade.")

    return " ".join(parts)


def _price_detail(vwap: float, shortfall: float) -> str:
    """
    Explain execution price in terms of:
      - market average over the window (VWAP slippage)
      - starting price when you decided to trade (shortfall)
    Always speak in 'better/worse' language, not just 'off'.
    """
    vwap_ok = _is_valid_number(vwap)
    short_ok = _is_valid_number(shortfall)

    def _dir_phrase(val: float, what: str) -> str:
        if not _is_valid_number(val):
            return ""
        pct = bps_to_pct_str(val)
        if val > 0:
            return f"about {pct} worse than the {what}"
        elif val < 0:
            return f"about {pct} better than the {what}"
        else:
            return f"right in line with the {what}"

    if vwap_ok and short_ok:
        part1 = _dir_phrase(vwap, "average market price during your trading window")
        part2 = _dir_phrase(shortfall, "price when you started the order")
        return f"Your fills were {part1} and {part2}."
    if vwap_ok:
        return (
            f"Your fills were {_dir_phrase(vwap, 'average market price during your trading window')}."
        )
    if short_ok:
        return f"Your price was {_dir_phrase(shortfall, 'price when you started the order')}."
    return "Price comparisons were unclear because some data was missing."


def _drift_detail(drift: float) -> str:
    """
    Explain how much of the result came from timing / tape drift.
    """
    if not _is_valid_number(drift):
        return ""
    pct = bps_to_pct_str(drift)
    if abs(drift) < DRIFT_NEUTRAL_THRESHOLD:
        return (
            "The market stayed mostly flat around your trade, so the result mainly reflects your execution price."
        )
    if drift > 0:
        return (
            f"While you were trading, prices drifted about {pct} against you, "
            "so part of the cost came from timing rather than just the way you executed."
        )
    return (
        f"While you were trading, prices drifted about {pct} in your favor, "
        "so you had a small tailwind from the market on top of your execution."
    )


def _impact_detail(impact: float) -> str:
    """
    Explain permanent price impact in user terms.
    """
    if not _is_valid_number(impact):
        return ""
    pct = bps_to_pct_str(impact)
    if impact >= IMPACT_MOVE_THRESHOLD:
        return (
            f"By the time things settled, the market stood about {pct} away from your starting level in your trade direction, "
            "which suggests your orders left a visible footprint on the tape."
        )
    if impact <= -IMPACT_MOVE_THRESHOLD:
        return (
            f"After you finished, prices moved back in your favor by roughly {pct}, "
            "so most of the move during your trading window turned out to be temporary."
        )
    return "Prices ended up close to where they started, so your permanent impact on the market was small."


ADVICE_BY_KEY = {
    "headwind_high_cost": "Trade smaller and be patient with limit prices so you aren't chasing a moving market.",
    "mostly_in_line": "Stay the course and keep using patient limits to shave small costs.",
    "strong_all_around": "Keep this approach—your sizing, pace, and entries are working together.",
    "strong_flat_timing": "Keep doing this and stay alert so you can adjust quickly if the market starts moving.",
    "good_fills_headwind": "Keep your pricing discipline but start earlier so you're not trading into a move.",
    "drift_helped": "Stay disciplined so results hold even when the market isn't leaning your way.",
    "solid_flat_market": "Stick with this playbook and watch spreads and size if liquidity thins out.",
    "price_ok_impact_high": "Use smaller clips or wait for more liquidity so your orders don't shove the price.",
    "price_ok_impact_high_mid": "Dial back size and use more limit orders to keep your footprint light.",
    "timing_good_execution_weak": "Use firmer limit prices and avoid crossing the spread unless you must.",
    "mixed": "Pick one tweak—tighter limits, smaller clips, or earlier entries—and test it on the next trade.",
}


def _advice_text(key: str) -> str:
    return ADVICE_BY_KEY.get(
        key,
        "Pick one tweak—tighter limits, smaller clips, or earlier entries—and test it on the next trade.",
    )


def build_feedback(metrics_bps: Dict[str, float]) -> Dict[str, str]:
    """
    metrics_bps keys:
      vwap_slippage, shortfall, effective_spread,
      realized_spread, market_impact, drift
    Returns a dict you can return from your API.
    """
    exec_band = axis_band("execution", metrics_bps)
    impact_band = axis_band("impact", metrics_bps)
    timing_band = axis_band("timing", metrics_bps)

    conclusion = choose_conclusion(exec_band, impact_band, timing_band)

    vwap = metrics_bps["vwap_slippage"]
    short = metrics_bps["shortfall"]
    impact = metrics_bps["market_impact"]
    drift = metrics_bps["drift"]
    effective = metrics_bps.get("effective_spread")
    realized = metrics_bps.get("realized_spread")

    price_line = _price_headline(vwap, short)
    drift_line = _drift_headline(drift)
    impact_line = _impact_headline(impact)

    # Up to two short sentences in the headline: price + (drift or impact).
    headline = " ".join([txt for txt in (price_line, drift_line or impact_line) if txt][:2]).strip()

    why_lines = [
        _price_detail(vwap, short),
        _spread_detail(effective, realized),
        _drift_detail(drift),
        _impact_detail(impact),
    ]

    axis_summary = f"Execution {exec_band} | Impact {impact_band} | Timing {timing_band}"
    advice = _advice_text(conclusion["key"])

    return {
        "conclusion_key": conclusion["key"],
        "conclusion": headline,
        "scores": axis_summary,
        "why": " ".join([line for line in why_lines if line]),
        "improve": advice,
        "axis_summary": axis_summary,
        "summary": headline,
    }
