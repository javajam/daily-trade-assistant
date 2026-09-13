"""Compose AND/OR conditions and emit explained trade decisions."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from dta_bot.config import (
    AnyCondition,
    BotConfig,
    GroupCond,
    MaCond,
    MaCrossCond,
    PatternCond,
    RsiCond,
    RuleSpec,
    VolumeCond,
)
from dta_bot.indicators import average_volume, ema, last_two_ma, rsi, sma
from dta_bot.models import Bar, ConditionResult, EvalResult
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
