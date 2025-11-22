from typing import Dict

from .axes import BAND_TO_SCORE

Conclusion = Dict[str, str]


def _score(band: str) -> int:
    return BAND_TO_SCORE[band]


def choose_conclusion(exec_band: str, impact_band: str, timing_band: str) -> Conclusion:
    e = _score(exec_band)
    i = _score(impact_band)
    t = _score(timing_band)

    # 1. Everything kind of bad + headwind & costs
    if e <= 1 and i <= 1 and t <= 1:
        return {
            "key": "headwind_high_cost",
            "conclusion": "You're paying extra costs while the market is moving against you.",
            "improve": (
                "Try smaller, less aggressive orders when the market is running the wrong way. "
                "Avoid chasing after big moves; wait for the move to slow before entering."
            ),
        }

    # 2. All neutral + basically in line
    if e == 2 and i == 2 and t == 2:
        return {
            "key": "mostly_in_line",
            "conclusion": "This trade was mostly in line with the market.",
            "improve": (
                "Nothing is badly wrong here. Over time, you can shave costs by using tighter limit prices "
                "and avoiding obvious spikes or gaps."
            ),
        }

    # 3. Execution & impact good, timing good + very solid trade
    if e >= 3 and i >= 3 and t >= 3:
        return {
            "key": "strong_all_around",
            "conclusion": "Great trade: good timing, strong prices, and low trading costs.",
            "keep": (
                "Keep this approach. Your entry, order placement, and size all worked well together."
            ),
        }

    # 3b. Execution & impact good, timing neutral + very solid fills in flat market
    if e >= 3 and i >= 3 and t == 2:
        return {
            "key": "strong_flat_timing",
            "conclusion": "Strong execution and low cost in a mostly flat market.",
            "keep": (
                "Keep doing what you're doing. Your pricing and impact are controlled; just keep an eye on "
                "drift so you're ready to adjust if the market starts trending."
            ),
        }

    # 4. Execution & impact good, timing bad + good fills despite headwind
    if e >= 3 and i >= 3 and t <= 1:
        return {
            "key": "good_fills_headwind",
            "conclusion": "You got good fills even though the market moved against you.",
            "improve": (
                "Your order placement is solid, but your entries are often late. "
                "Try to start closer to the beginning of the move instead of reacting after it’s already gone."
            ),
        }

    # 4b. Benefited from drift with decent execution/impact (but not top tier)
    if t >= 3 and e >= 2 and i >= 2 and not (e >= 3 and i >= 3):
        return {
            "key": "drift_helped",
            "conclusion": "The market move helped your trade and your execution was solid.",
            "keep": (
                "This is a good combo: decent fills with friendly drift. Just don't rely on luck—keep using "
                "disciplined entries and sane size so this works even when drift isn't as friendly."
            ),
        }

    # 4c. Solid execution/impact in a flat market (mid-tier)
    if t == 2 and e >= 2 and i >= 2 and not (e == 2 and i == 2) and not (e >= 3 and i >= 3):
        return {
            "key": "solid_flat_market",
            "conclusion": "Solid pricing and cost control in a calm market.",
            "keep": (
                "Your approach works well when things are calm. Keep watching spreads and volume so you can "
                "slow down in thin markets and speed up a bit when there’s more depth."
            ),
        }

    # 5. Execution good, impact bad + price okay, but you're paying for it
    if e >= 3 and i <= 1:
        return {
            "key": "price_ok_impact_high",
            "conclusion": "Your prices are okay, but your trades are moving the market too much.",
            "improve": (
                "You’re likely trading too big or too aggressively. Break orders into smaller pieces, use more "
                "limit orders, and avoid sweeping through multiple price levels at once."
            ),
        }

    # 5b. Execution ok, impact bad (mid-tier execution)
    if e == 2 and i <= 1:
        return {
            "key": "price_ok_impact_high_mid",
            "conclusion": "Your prices are decent, but impact costs are still high.",
            "improve": (
                "Try to reduce your footprint: smaller clips, more patient limit orders, and avoid hitting large "
                "chunks in thin books. The goal is to trade without pushing the price around."
            ),
        }

    # 6. Timing good, execution bad + idea good, fill weak
    if t >= 3 and e <= 1:
        return {
            "key": "timing_good_execution_weak",
            "conclusion": "Your idea and timing were good, but you overpaid versus the market.",
            "improve": (
                "Keep your entry logic, but tighten how you execute: use better limit prices, avoid market orders "
                "when spreads are wide, and wait a bit instead of crossing the spread immediately."
            ),
        }

    # Fallback default
    return {
        "key": "mixed",
        "conclusion": "Mixed result across timing, execution, and impact.",
        "improve": (
            "No single problem dominates this trade. Check a few similar trades and see what repeats—late entries, "
            "wide spreads, or trading into strong moves—and focus on fixing that first."
        ),
    }
