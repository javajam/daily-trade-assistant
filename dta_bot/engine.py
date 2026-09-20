"""Compose AND/OR conditions and emit explained trade decisions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from dta_bot.config import (
    AnyCondition,
    BotConfig,
    GroupCond,
    MaCond,
    MaCrossCond,
    MaPairCrossCond,
    PatternCond,
    RsiCond,
    RuleSpec,
    VolumeCond,
    VolumePrevCond,
)
from dta_bot.indicators import average_volume, ema, last_two_ma, last_two_ma_pair, ma_pair_cross, rsi, sma
from dta_bot.models import Bar, ConditionResult, EvalResult, Position
from dta_bot.patterns import detect
from dta_bot.state import BotState, fmt_ts

log = logging.getLogger("dta_bot.engine")

BarMap = dict[tuple[str, str], list[Bar]]


def _closes(bars: list[Bar]) -> list[float]:
    return [b.close for b in bars]


def _vols(bars: list[Bar]) -> list[float]:
    return [b.volume for b in bars]


def eval_leaf(cond: AnyCondition, symbol: str, bars_by_key: BarMap) -> ConditionResult:
    if isinstance(cond, PatternCond):
        bars = bars_by_key.get((symbol, cond.timeframe), [])
        result = detect(cond.name, bars)
        result.reason = f"pattern {cond.name} @ {cond.timeframe}: {result.reason}"
        return result

    if isinstance(cond, MaCond):
        bars = bars_by_key.get((symbol, cond.timeframe), [])
        closes = _closes(bars)
        value = sma(closes, cond.period) if cond.ma == "sma" else ema(closes, cond.period)
        if value is None:
            return ConditionResult(
                False,
                f"{cond.ma.upper()}{cond.period} @{cond.timeframe}: need {cond.period} closes, have {len(closes)}",
            )
        price = closes[-1]
        ok = price > value if cond.compare == "above" else price < value
        cmp = ">" if cond.compare == "above" else "<"
        return ConditionResult(
            ok,
            f"close {price:.4f} {cmp} {cond.ma.upper()}{cond.period} {value:.4f} @{cond.timeframe} → {ok}",
            {"price": price, "ma": value},
        )

    if isinstance(cond, MaCrossCond):
        bars = bars_by_key.get((symbol, cond.timeframe), [])
        closes = _closes(bars)
        pair = last_two_ma(closes, cond.period, cond.ma)
        need = cond.period + 1
        if pair is None:
            return ConditionResult(
                False,
                f"{cond.ma}_cross {cond.direction} @{cond.timeframe}: "
                f"need {need} closes, have {len(closes)}",
            )
        prev_close, prev_ma, curr_close, curr_ma = pair
        if cond.direction == "bearish":
            ok = prev_close >= prev_ma and curr_close < curr_ma
        else:
            ok = prev_close <= prev_ma and curr_close > curr_ma
        verb = "matched" if ok else "not found"
        return ConditionResult(
            ok,
            f"{cond.ma}_cross {verb} ({cond.direction}): "
            f"prev close {prev_close:.4f} vs {cond.ma.upper()}{cond.period} {prev_ma:.4f}, "
            f"close {curr_close:.4f} vs {curr_ma:.4f} @{cond.timeframe} → {ok}",
            {
                "prev_close": prev_close,
                "prev_ma": prev_ma,
                "price": curr_close,
                "ma": curr_ma,
                "direction": cond.direction,
            },
        )

    if isinstance(cond, MaPairCrossCond):
        bars = bars_by_key.get((symbol, cond.timeframe), [])
        closes = _closes(bars)
        pair = last_two_ma_pair(closes, cond.ema_period, cond.sma_period)
        need = max(cond.ema_period, cond.sma_period) + 1
        if pair is None:
            return ConditionResult(
                False,
                f"ema_sma_cross {cond.direction} @{cond.timeframe}: "
                f"need {need} closes, have {len(closes)}",
            )
        prev_ema, prev_sma, curr_ema, curr_sma = pair
        if cond.direction == "bearish":
            ok = prev_ema >= prev_sma and curr_ema < curr_sma
        else:
            ok = prev_ema <= prev_sma and curr_ema > curr_sma
        verb = "matched" if ok else "not found"
        return ConditionResult(
            ok,
            f"ema_sma_cross {verb} ({cond.direction}): "
            f"prev EMA{cond.ema_period} {prev_ema:.4f} vs SMA{cond.sma_period} {prev_sma:.4f}, "
            f"EMA {curr_ema:.4f} vs SMA {curr_sma:.4f} @{cond.timeframe} → {ok}",
            {
                "prev_ema": prev_ema,
                "prev_sma": prev_sma,
                "ema": curr_ema,
                "sma": curr_sma,
                "direction": cond.direction,
                "ema_period": cond.ema_period,
                "sma_period": cond.sma_period,
            },
        )

    if isinstance(cond, RsiCond):
        bars = bars_by_key.get((symbol, cond.timeframe), [])
        value = rsi(_closes(bars), cond.period)
        if value is None:
            return ConditionResult(
                False,
                f"RSI{cond.period} @{cond.timeframe}: need {cond.period + 1} closes, have {len(bars)}",
            )
        parts = [f"RSI{cond.period}={value:.2f} @{cond.timeframe}"]
        ok = True
        if cond.below is not None:
            hit = value < cond.below
            parts.append(f"< {cond.below} → {hit}")
            ok = ok and hit
        if cond.above is not None:
            hit = value > cond.above
            parts.append(f"> {cond.above} → {hit}")
            ok = ok and hit
        return ConditionResult(ok, " ".join(parts), {"rsi": value})

    if isinstance(cond, VolumeCond):
        bars = bars_by_key.get((symbol, cond.timeframe), [])
        if len(bars) < cond.period + 1:
            return ConditionResult(
                False,
                f"volume @{cond.timeframe}: need {cond.period + 1} bars, have {len(bars)}",
            )
        # Compare last bar vs average of the prior `period` bars (exclude current).
        avg = average_volume(_vols(bars[:-1]), cond.period)
        last = bars[-1].volume
        if avg is None or avg == 0:
            return ConditionResult(False, f"volume @{cond.timeframe}: cannot compute avg")
        threshold = avg * cond.multiplier
        ok = last > threshold if cond.compare == "above" else last < threshold
        cmp = ">" if cond.compare == "above" else "<"
        return ConditionResult(
            ok,
            f"volume {last:.0f} {cmp} {cond.multiplier}×avg{cond.period} {threshold:.0f} @{cond.timeframe} → {ok}",
            {"volume": last, "avg": avg},
        )

    if isinstance(cond, VolumePrevCond):
        bars = bars_by_key.get((symbol, cond.timeframe), [])
        if len(bars) < 2:
            return ConditionResult(
                False,
                f"volume_vs_prev @{cond.timeframe}: need 2 bars, have {len(bars)}",
            )
        last = bars[-1].volume
        prev = bars[-2].volume
        ok = last > prev if cond.compare == "above" else last < prev
        cmp = ">" if cond.compare == "above" else "<"
        return ConditionResult(
            ok,
            f"volume {last:.0f} {cmp} prev {prev:.0f} @{cond.timeframe} → {ok}",
            {"volume": last, "prev_volume": prev},
        )

    raise TypeError(f"Unknown condition type {type(cond)}")


def eval_condition(cond: AnyCondition, symbol: str, bars_by_key: BarMap) -> ConditionResult:
    if isinstance(cond, GroupCond):
        results = [eval_condition(child, symbol, bars_by_key) for child in cond.conditions]
        if cond.kind == "all":
            ok = all(r.matched for r in results)
            joiner = " AND "
        else:
            ok = any(r.matched for r in results)
            joiner = " OR "
        reason = f"({cond.kind.upper()}: " + joiner.join(r.reason for r in results) + f") → {ok}"
        return ConditionResult(ok, reason, {"children": [r.details for r in results]})
    return eval_leaf(cond, symbol, bars_by_key)


def _aware_ts(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ma_pair_cross_flatten_bar(
    position: Position,
    signal_bars: list[Bar],
    *,
    after: Optional[datetime],
    ema_period: int = 9,
    sma_period: int = 20,
) -> Optional[Bar]:
    """Latest closed bar after entry where EMA crossed SMA against the position.

    Long exits on a bearish pair-cross (EMA under SMA); short on a bullish
    pair-cross. If we cannot prove the bar closed after entry, do not flatten.
    """
    if after is None or not signal_bars:
        return None
    later = [b for b in signal_bars if _aware_ts(b.timestamp) > _aware_ts(after)]
    if not later:
        return None
    last = max(later, key=lambda b: _aware_ts(b.timestamp))
    window = [b for b in signal_bars if _aware_ts(b.timestamp) <= _aware_ts(last.timestamp)]
    closes = [b.close for b in window]
    side = "buy" if str(position.side).lower() in {"buy", "long"} else "sell"
    direction = "bearish" if side == "buy" else "bullish"
    if ma_pair_cross(closes, ema_period, sma_period, direction=direction):
        return last
    return None


def lower_high_exit(side: str, curr: Bar, prev: Bar) -> bool:
    """Long: current high < previous high. Short: current low > previous low."""
    key = "buy" if str(side).lower() in {"buy", "long"} else "sell"
    if key == "buy":
        return curr.high < prev.high
    return curr.low > prev.low


def lower_high_flatten_bar(
    position: Position,
    signal_bars: list[Bar],
    *,
    after: Optional[datetime],
) -> Optional[Bar]:
    """Latest closed bar after entry that prints a lower high (long) / higher low (short).

    ``after`` is the signal timestamp (entry is the next bar). Exit fills at
    that completed bar's close — the same convention as ``ema_invalid``.
    Equal highs (or lows on shorts) stay valid.
    """
    if after is None or not signal_bars:
        return None
    later = [b for b in signal_bars if _aware_ts(b.timestamp) > _aware_ts(after)]
    if not later:
        return None
    last = max(later, key=lambda b: _aware_ts(b.timestamp))
    window = [b for b in signal_bars if _aware_ts(b.timestamp) <= _aware_ts(last.timestamp)]
    if len(window) < 2:
        return None
    prev = window[-2]
    side = "buy" if str(position.side).lower() in {"buy", "long"} else "sell"
    if lower_high_exit(side, last, prev):
        return last
    return None


def bar_range(bar: Bar) -> float:
    """High − low. Used by the range-expansion exit."""
    return bar.high - bar.low


def range_expansion_exit(curr: Bar, prior: list[Bar]) -> bool:
    """True when curr range is strictly greater than max(range of prior bars)."""
    if not prior:
        return False
    ceiling = max(bar_range(b) for b in prior)
    return bar_range(curr) > ceiling


def range_expansion_flatten_bar(
    position: Position,
    signal_bars: list[Bar],
    *,
    after: Optional[datetime],
    lookback: int = 3,
) -> Optional[Bar]:
    """Latest closed bar after the entry bar whose range > max of the prior ``lookback`` bars.

    ``after`` is the signal timestamp (entry is the next bar). The entry/fill
    bar is never an exit bar. Fill at that completed bar's close — the same
    convention as ``ema_invalid`` / ``lower_high``. Equal range stays valid.
    ``position`` is unused (range is side-agnostic) but kept for the same
    signature as the other flatten helpers.
    """
    del position
    if after is None or not signal_bars or lookback < 1:
        return None
    later = [b for b in signal_bars if _aware_ts(b.timestamp) > _aware_ts(after)]
    if len(later) < 2:
        return None
    last = max(later, key=lambda b: _aware_ts(b.timestamp))
    entry = min(later, key=lambda b: _aware_ts(b.timestamp))
    if _aware_ts(last.timestamp) == _aware_ts(entry.timestamp):
        return None
    window = [b for b in signal_bars if _aware_ts(b.timestamp) <= _aware_ts(last.timestamp)]
    if len(window) < lookback + 1:
        return None
    prior = window[-(lookback + 1) : -1]
    if range_expansion_exit(last, prior):
        return last
    return None


def fire_key(rule_id: str, symbol: str, signal_ts: datetime) -> str:
    return f"{rule_id}:{symbol}:{fmt_ts(signal_ts)}"


def cooldown_key(rule_id: str, symbol: str) -> str:
    return f"{rule_id}:{symbol}"


def _signal_ts(rule: RuleSpec, symbol: str, bars_by_key: BarMap) -> Optional[datetime]:
    """Use the latest closed bar among timeframes referenced by the rule."""

    def tfs(cond: AnyCondition) -> list[str]:
        if isinstance(cond, GroupCond):
            out: list[str] = []
            for child in cond.conditions:
                out.extend(tfs(child))
            return out
        return [cond.timeframe]

    latest: Optional[datetime] = None
    for tf in tfs(rule.when):
        bars = bars_by_key.get((symbol, tf), [])
        if bars:
            ts = bars[-1].timestamp
            if latest is None or ts > latest:
                latest = ts
    return latest


def evaluate_rule(
    rule: RuleSpec,
    symbol: str,
    bars_by_key: BarMap,
    state: BotState,
    now: Optional[datetime] = None,
) -> EvalResult:
    if not rule.enabled:
        return EvalResult(rule.id, symbol, False, ["rule disabled"], skipped="disabled")

    cd_until = state.on_cooldown(cooldown_key(rule.id, symbol), now=now)
    if cd_until:
        return EvalResult(
            rule.id,
            symbol,
            False,
            [f"cooldown until {fmt_ts(cd_until)}"],
            skipped="cooldown",
        )

    result = eval_condition(rule.when, symbol, bars_by_key)
    sig = _signal_ts(rule, symbol, bars_by_key)
    if result.matched and sig and state.already_fired(fire_key(rule.id, symbol, sig)):
        return EvalResult(
            rule.id,
            symbol,
            False,
            [result.reason, "already fired on this bar (idempotent skip)"],
            action_type=rule.action.type,
            signal_bar_ts=sig,
            skipped="already_fired",
        )
    return EvalResult(
        rule.id,
        symbol,
        result.matched,
        [result.reason],
        action_type=rule.action.type if result.matched else None,
        signal_bar_ts=sig,
    )


def evaluate_all(
    config: BotConfig,
    bars_by_key: BarMap,
    state: BotState,
    now: Optional[datetime] = None,
) -> list[EvalResult]:
    results: list[EvalResult] = []
    for rule in config.rules:
        for symbol in config.symbols_for(rule):
            ev = evaluate_rule(rule, symbol, bars_by_key, state, now=now)
            log.info("%s", ev.explain())
            results.append(ev)
    return results
