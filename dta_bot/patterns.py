"""Candlestick pattern detectors operating on the last N *closed* bars.

Each detector returns a ConditionResult explaining which bars matched
(or why the pattern did not fire). Bars must be oldest-first.
"""

from __future__ import annotations

from typing import Callable, Optional

from dta_bot.models import Bar, ConditionResult

# Default relative thresholds. Tuned for typical equity OHLC, overridable in tests.
DOJI_BODY_MAX_FRAC = 0.10
LONG_WICK_MULT = 2.0
SMALL_WICK_MAX_FRAC = 0.25
STAR_SMALL_BODY_FRAC = 0.35
SOLDIER_MIN_BODY_FRAC = 0.40


def _need(bars: list[Bar], n: int, name: str) -> Optional[ConditionResult]:
    if len(bars) < n:
        return ConditionResult(
            False,
            f"{name}: need {n} closed bars, have {len(bars)}",
            {"needed": n, "have": len(bars)},
        )
    return None


def _bar_list(bars: list[Bar]) -> str:
    return "; ".join(b.summary() for b in bars)


def detect_doji(
    bars: list[Bar],
    *,
    body_max_frac: float = DOJI_BODY_MAX_FRAC,
) -> ConditionResult:
    miss = _need(bars, 1, "doji")
    if miss:
        return miss
    bar = bars[-1]
    rng = bar.range()
    if rng <= 0:
        return ConditionResult(False, f"doji: zero-range bar {bar.summary()}", {"bar": bar.summary()})
    frac = bar.body() / rng
    if frac <= body_max_frac:
        return ConditionResult(
            True,
            f"doji matched on {bar.summary()} (body/range={frac:.3f} <= {body_max_frac})",
            {"bars": [bar.summary()], "body_frac": frac},
        )
    return ConditionResult(
        False,
        f"doji: body/range={frac:.3f} > {body_max_frac} on {bar.summary()}",
        {"bars": [bar.summary()], "body_frac": frac},
    )


def detect_bullish_engulfing(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 2, "bullish_engulfing")
    if miss:
        return miss
    prev, curr = bars[-2], bars[-1]
    ok = (
        prev.is_bearish()
        and curr.is_bullish()
        and curr.open <= prev.close
        and curr.close >= prev.open
    )
    detail = {"bars": [prev.summary(), curr.summary()]}
    if ok:
        return ConditionResult(
            True,
            f"bullish_engulfing matched on {_bar_list([prev, curr])}",
            detail,
        )
    return ConditionResult(
        False,
        (
            f"bullish_engulfing not found: prev bearish={prev.is_bearish()} "
            f"curr bullish={curr.is_bullish()} curr.open<=prev.close="
            f"{curr.open <= prev.close} curr.close>=prev.open={curr.close >= prev.open} "
            f"on {_bar_list([prev, curr])}"
        ),
        detail,
    )


def detect_bearish_engulfing(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 2, "bearish_engulfing")
    if miss:
        return miss
    prev, curr = bars[-2], bars[-1]
    ok = (
        prev.is_bullish()
        and curr.is_bearish()
        and curr.open >= prev.close
        and curr.close <= prev.open
    )
    detail = {"bars": [prev.summary(), curr.summary()]}
    if ok:
        return ConditionResult(
            True,
            f"bearish_engulfing matched on {_bar_list([prev, curr])}",
            detail,
        )
    return ConditionResult(
        False,
        (
            f"bearish_engulfing not found: prev bullish={prev.is_bullish()} "
            f"curr bearish={curr.is_bearish()} on {_bar_list([prev, curr])}"
        ),
        detail,
    )


def _hammer_shape(
    bar: Bar,
    *,
    long_wick_mult: float = LONG_WICK_MULT,
    small_wick_max_frac: float = SMALL_WICK_MAX_FRAC,
) -> tuple[bool, str]:
    rng = bar.range()
    body = bar.body()
    if rng <= 0 or body <= 0:
        return False, "no body/range"
    if bar.lower_shadow() < long_wick_mult * body:
        return False, f"lower wick {bar.lower_shadow():.4f} < {long_wick_mult}x body {body:.4f}"
    if bar.upper_shadow() > small_wick_max_frac * rng:
        return False, f"upper wick {bar.upper_shadow():.4f} too large vs range {rng:.4f}"
    # Body sits in the upper half of the range.
    if bar.body_top() < bar.low + 0.5 * rng:
        return False, "body not in upper half of range"
    return True, "hammer-shaped"


def detect_hammer(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 1, "hammer")
    if miss:
        return miss
    bar = bars[-1]
    ok, why = _hammer_shape(bar)
    if ok:
        return ConditionResult(True, f"hammer matched on {bar.summary()}", {"bars": [bar.summary()]})
    return ConditionResult(False, f"hammer: {why} on {bar.summary()}", {"bars": [bar.summary()]})


def _inverted_hammer_shape(
    bar: Bar,
    *,
    long_wick_mult: float = LONG_WICK_MULT,
    small_wick_max_frac: float = SMALL_WICK_MAX_FRAC,
) -> tuple[bool, str]:
    rng = bar.range()
    body = bar.body()
    if rng <= 0 or body <= 0:
        return False, "no body/range"
    if bar.upper_shadow() < long_wick_mult * body:
        return False, f"upper wick {bar.upper_shadow():.4f} < {long_wick_mult}x body {body:.4f}"
    if bar.lower_shadow() > small_wick_max_frac * rng:
        return False, f"lower wick {bar.lower_shadow():.4f} too large vs range {rng:.4f}"
    if bar.body_bottom() > bar.low + 0.5 * rng:
        return False, "body not in lower half of range"
    return True, "inverted-hammer-shaped"


def detect_inverted_hammer(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 1, "inverted_hammer")
    if miss:
        return miss
    bar = bars[-1]
    ok, why = _inverted_hammer_shape(bar)
    if ok:
        return ConditionResult(
            True, f"inverted_hammer matched on {bar.summary()}", {"bars": [bar.summary()]}
        )
    return ConditionResult(
        False, f"inverted_hammer: {why} on {bar.summary()}", {"bars": [bar.summary()]}
    )


def detect_shooting_star(bars: list[Bar]) -> ConditionResult:
    """Shooting star: inverted-hammer shape after a higher close (local high)."""
    miss = _need(bars, 2, "shooting_star")
    if miss:
        return miss
    prev, curr = bars[-2], bars[-1]
    shape_ok, why = _inverted_hammer_shape(curr)
    after_rise = curr.high >= prev.high and curr.close <= prev.close + max(prev.body(), 1e-9)
    if shape_ok and (curr.high >= prev.close):
        return ConditionResult(
            True,
            f"shooting_star matched on {_bar_list([prev, curr])}",
            {"bars": [prev.summary(), curr.summary()], "after_rise": after_rise},
        )
    return ConditionResult(
        False,
        f"shooting_star: shape={why}; high vs prior close on {_bar_list([prev, curr])}",
        {"bars": [prev.summary(), curr.summary()]},
    )


def detect_morning_star(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 3, "morning_star")
    if miss:
        return miss
    a, b, c = bars[-3], bars[-2], bars[-1]
    first_long_bear = a.is_bearish() and a.body() > 0
    star_small = b.range() > 0 and b.body() <= STAR_SMALL_BODY_FRAC * max(a.body(), b.range())
    third_bull = c.is_bullish() and c.close > a.mid_body()
    ok = first_long_bear and star_small and third_bull
    detail = {"bars": [a.summary(), b.summary(), c.summary()]}
    if ok:
        return ConditionResult(
            True,
            f"morning_star matched on {_bar_list([a, b, c])}",
            detail,
        )
    return ConditionResult(
        False,
        (
            f"morning_star not found: first_bear={first_long_bear} "
            f"star_small={star_small} third_closes_into_first={third_bull} "
            f"on {_bar_list([a, b, c])}"
        ),
        detail,
    )


def detect_evening_star(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 3, "evening_star")
    if miss:
        return miss
    a, b, c = bars[-3], bars[-2], bars[-1]
    first_long_bull = a.is_bullish() and a.body() > 0
    star_small = b.range() > 0 and b.body() <= STAR_SMALL_BODY_FRAC * max(a.body(), b.range())
    third_bear = c.is_bearish() and c.close < a.mid_body()
    ok = first_long_bull and star_small and third_bear
    detail = {"bars": [a.summary(), b.summary(), c.summary()]}
    if ok:
        return ConditionResult(
            True,
            f"evening_star matched on {_bar_list([a, b, c])}",
            detail,
        )
    return ConditionResult(
        False,
        (
            f"evening_star not found: first_bull={first_long_bull} "
            f"star_small={star_small} third_closes_into_first={third_bear} "
            f"on {_bar_list([a, b, c])}"
        ),
        detail,
    )


def detect_three_white_soldiers(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 3, "three_white_soldiers")
    if miss:
        return miss
    a, b, c = bars[-3], bars[-2], bars[-1]
    trio = [a, b, c]
    all_bull = all(x.is_bullish() for x in trio)
    rising = a.close < b.close < c.close
    decent_bodies = all(
        x.range() > 0 and x.body() >= SOLDIER_MIN_BODY_FRAC * x.range() for x in trio
    )
    # Each open is at/above prior close's body (no huge gap down).
    opens_ok = b.open >= a.body_bottom() and c.open >= b.body_bottom()
    ok = all_bull and rising and decent_bodies and opens_ok
    detail = {"bars": [x.summary() for x in trio]}
    if ok:
        return ConditionResult(
            True,
            f"three_white_soldiers matched on {_bar_list(trio)}",
            detail,
        )
    return ConditionResult(
        False,
        (
            f"three_white_soldiers not found: all_bull={all_bull} rising={rising} "
            f"bodies={decent_bodies} opens_ok={opens_ok} on {_bar_list(trio)}"
        ),
        detail,
    )


def detect_three_black_crows(bars: list[Bar]) -> ConditionResult:
    miss = _need(bars, 3, "three_black_crows")
    if miss:
        return miss
    a, b, c = bars[-3], bars[-2], bars[-1]
    trio = [a, b, c]
    all_bear = all(x.is_bearish() for x in trio)
    falling = a.close > b.close > c.close
    decent_bodies = all(
        x.range() > 0 and x.body() >= SOLDIER_MIN_BODY_FRAC * x.range() for x in trio
    )
    opens_ok = b.open <= a.body_top() and c.open <= b.body_top()
    ok = all_bear and falling and decent_bodies and opens_ok
    detail = {"bars": [x.summary() for x in trio]}
    if ok:
        return ConditionResult(
            True,
            f"three_black_crows matched on {_bar_list(trio)}",
            detail,
        )
    return ConditionResult(
        False,
        (
            f"three_black_crows not found: all_bear={all_bear} falling={falling} "
            f"bodies={decent_bodies} opens_ok={opens_ok} on {_bar_list(trio)}"
        ),
        detail,
    )


DETECTORS: dict[str, Callable[[list[Bar]], ConditionResult]] = {
    "doji": detect_doji,
    "bullish_engulfing": detect_bullish_engulfing,
    "bearish_engulfing": detect_bearish_engulfing,
    "hammer": detect_hammer,
    "inverted_hammer": detect_inverted_hammer,
    "shooting_star": detect_shooting_star,
    "morning_star": detect_morning_star,
    "evening_star": detect_evening_star,
    "three_white_soldiers": detect_three_white_soldiers,
    "three_black_crows": detect_three_black_crows,
}

PATTERN_NAMES = sorted(DETECTORS)


def detect(name: str, bars: list[Bar]) -> ConditionResult:
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    fn = DETECTORS.get(key)
    if fn is None:
        return ConditionResult(
            False,
            f"unknown pattern {name!r}; known: {', '.join(PATTERN_NAMES)}",
            {},
        )
    return fn(bars)
