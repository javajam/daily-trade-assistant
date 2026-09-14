"""Load and validate human-editable YAML/JSON rule files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from dta_bot.patterns import PATTERN_NAMES
from dta_bot.session import parse_optional_hhmm, parse_timezone
from dta_bot.timeframes import normalize


class SizeSpec(BaseModel):
    type: Literal["shares", "percent_equity", "risk_pct"] = "shares"
    # shares / percent_equity: share count or percent of equity (2 = 2%).
    # risk_pct may omit value and use equity_risk / stop_pct instead.
    value: Optional[float] = Field(default=None, gt=0)
    # Fraction of current equity to risk (0.01 = 1%). Used when type is risk_pct.
    equity_risk: Optional[float] = Field(default=None, gt=0)
    # Stop distance in percent (1.5 = 1.5%). Used when type is risk_pct.
    # If omitted, shares_for falls back to action.stop_loss_pct.
    stop_pct: Optional[float] = Field(default=None, gt=0)

    @field_validator("type")
    @classmethod
    def _type(cls, v: str) -> str:
        return v.lower()

    @model_validator(mode="after")
    def _fields(self) -> "SizeSpec":
        if self.type in {"shares", "percent_equity"}:
            if self.value is None:
                raise ValueError(f"{self.type} sizing requires value")
        elif self.type == "risk_pct":
            risk = self.equity_risk if self.equity_risk is not None else self.value
            if risk is None:
                raise ValueError("risk_pct sizing requires equity_risk (e.g. 0.01 for 1%)")
            if risk > 1:
                raise ValueError("equity_risk is a fraction of equity (0.01 = 1%), not a percent")
            self.equity_risk = risk
        return self


EXIT_MODES = ("fixed_bracket", "ema_invalid", "ma_cross", "ma_cross_close", "lower_high")
EXIT_ALIASES = {
    "ema_invalid": "ema_invalid",
    "ema_invalidation": "ema_invalid",
    "ema9_invalid": "ema_invalid",
    "hold_ema": "ema_invalid",
    "invalid": "ema_invalid",
    "fixed_bracket": "fixed_bracket",
    "bracket": "fixed_bracket",
    "fixed": "fixed_bracket",
    "ma_cross": "ma_cross",
    "ema_sma_cross": "ma_cross",
    "ma_pair_cross": "ma_cross",
    "cross_under": "ma_cross",
    "ma_cross_under": "ma_cross",
    "ma_cross_close": "ma_cross_close",
    "ma_cross_at_close": "ma_cross_close",
    "ema_sma_cross_close": "ma_cross_close",
    "cross_under_close": "ma_cross_close",
    "ema_cross_close": "ma_cross_close",
    "lower_high": "lower_high",
    "lowerhigh": "lower_high",
    "lh": "lower_high",
    "lower_high_exit": "lower_high",
}


BREAKEVEN_VALID_MODES = ("above_ema", "always")
TAKE_ANCHORS = ("signal", "entry")
TAKE_ANCHOR_ALIASES = {
    "signal": "signal",
    "signal_close": "signal",
    "close": "signal",
    "entry": "entry",
    "fill": "entry",
    "entry_fill": "entry",
}
STOP_MODES = ("percent", "sma20", "entry_pct", "lock_plus", "trail")
# entry_pct / lock_plus / trail rebase the protective stop to the fill
# (next-bar open). percent stays on the signal-bar close (legacy).
ENTRY_STOP_MODES = frozenset({"entry_pct", "lock_plus", "trail"})
STOP_MODE_ALIASES = {
    "percent": "percent",
    "pct": "percent",
    "fixed_pct": "percent",
    "sma20": "sma20",
    "sma_20": "sma20",
    "sma": "sma20",
    "at_sma20": "sma20",
    "entry_pct": "entry_pct",
    "entry": "entry_pct",
    "fixed_entry": "entry_pct",
    "fixed_1pct": "entry_pct",
    "lock_plus": "lock_plus",
    "lock": "lock_plus",
    "lock_1pct": "lock_plus",
    "lock_plus_1pct": "lock_plus",
    "trail": "trail",
    "trail_pct": "trail",
    "trail_1pct": "trail",
    "trailing": "trail",
}


class ActionSpec(BaseModel):
    type: Literal["buy", "sell", "close"]
    size: Optional[SizeSpec] = None
    order: Literal["market", "limit"] = "market"
    limit_offset_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = Field(default=None, gt=0)
    take_profit_pct: Optional[float] = Field(default=None, gt=0)
    # percent = stop_loss_pct from the signal-bar close (legacy).
    # sma20 = protective stop at SMA(stop_sma_period) of the signal bar (fixed
    # level, not trailed). Longs skip when that SMA is at/above the signal close
    # or the next-bar fill. take_profit_pct is unchanged (omit for stop-only).
    # entry_pct = stop_loss_pct below the *fill* (next-bar open); never moves.
    # lock_plus = entry_pct initial stop; first trade/touch of the lock
    #   trigger moves the stop to the lock level and leaves it (live next bar).
    #   Long: initial fill×(1 − stop/100); trigger/lock fill×(1 + lock/100).
    #   Short: initial fill×(1 + stop/100); trigger/lock fill×(1 − lock/100).
    # trail = stop = peak_price_since_entry * (1 - trail_pct/100), ratchets
    #   up only; peak updates from each bar high after the stop check.
    stop_mode: Literal["percent", "sma20", "entry_pct", "lock_plus", "trail"] = "percent"
    stop_sma_period: int = Field(default=20, ge=2)
    # lock_plus: trigger and locked-stop distance in percent from entry.
    # Omit to use stop_loss_pct (1.0 → first touch of entry*1.01, lock there).
    lock_trigger_pct: Optional[float] = Field(default=None, gt=0)
    lock_stop_pct: Optional[float] = Field(default=None, gt=0)
    # trail: distance in percent from the peak (omit to use stop_loss_pct).
    trail_pct: Optional[float] = Field(default=None, gt=0)
    # When true (lock_plus only): on the lock-arm bar, add the same share
    # count as the open lot. Stop stays at original fill × (1+lock_stop/100)
    # on the full (doubled) position. Take is fill-anchored. Cash for the
    # add is not reserved at entry — if cash cannot cover it, lock still
    # arms and the add is skipped. Backtest-only (live does not auto-add).
    pyramid_on_lock: bool = False
    # lock_plus only: add the same share count on first trade/touch of
    # original fill × (1 + pyramid_add_pct/100), which may be *before* the
    # +lock (e.g. 0.5 then lock at 1.0). No take required. Cash is not
    # reserved. If a bar gaps through both prints, add first then lock;
    # the locked stop is live next bar. Backtest-only.
    pyramid_add_pct: Optional[float] = Field(default=None, gt=0)
    # lock_plus only: on the lock-arm print, sell half the open shares
    # (floor; leave ≥1 when size ≥ 2) at the lock-trigger fill convention
    # and lock the remainder at original fill × (1+lock_stop/100). Size 1
    # skips the partial and still locks. No pyramid. No hard full take.
    # Backtest-only (live does not auto scale-out).
    partial_take_on_lock: bool = False
    # lock_plus only: same half-take as partial_take_on_lock, but the
    # remainder stop rests at original fill × 1.00 (break-even), not at
    # fill × (1+lock_stop/100). Size 1 skips the partial and still arms
    # BE. BE stop is live next bar. Cannot combine with partial_take_on_lock
    # or pyramid. Backtest-only.
    partial_take_be: bool = False
    # signal = take_profit_pct from the signal-bar close (legacy).
    # entry = take_profit_pct from the fill (next-bar open). Forced to
    # entry when pyramid_on_lock is true.
    take_anchor: Literal["signal", "entry"] = "signal"
    # fixed_bracket = optional % stop/take. ema_invalid = hold until a
    # signal-timeframe close is on the wrong side of EMA (long: close < EMA).
    # Optional stop_loss_pct is then a catastrophic stop only; take is ignored.
    # ma_cross = hold until EMA crosses SMA against the position and flatten
    # at the next bar open. Long: EMA under SMA. Short: EMA above SMA (cover).
    # Optional stop_loss_pct is a catastrophic stop only (off when omitted).
    # The default noon short omits it. Percent take-profit is ignored.
    # ma_cross_close = same EMA-vs-SMA close-to-close pair-cross as ma_cross
    # (long: prev EMA >= prev SMA and curr EMA < curr SMA) but fill at that
    # completed bar's close — same convention as ema_invalid / lower_high.
    # If that bar is also the flatten bar, the close-fill wins over
    # session_flatten. Optional stop is catastrophic only (off when omitted).
    # Percent take is ignored. Do not change ma_cross next-open fill.
    # lower_high = hold until a completed signal-timeframe bar after entry
    # prints a lower high (long: curr high < prev high) and exit at that
    # close — same fill convention as ema_invalid. Shorts use the symmetric
    # higher low (curr low > prev low). Optional stop_loss_pct is
    # catastrophic only (off when omitted). Percent take is ignored.
    exit: Literal["fixed_bracket", "ema_invalid", "ma_cross", "ma_cross_close", "lower_high"] = "fixed_bracket"
    exit_ema_period: int = Field(default=9, ge=2)
    exit_sma_period: int = Field(default=20, ge=2)
    # After this many complete signal-timeframe bars *after the entry bar*,
    # move the stop to entry (break-even). 0 / omitted = off. 1 = next full
    # candle after fill (e.g. the next 15m bar after a 15m fill).
    breakeven_after_bars: int = Field(default=0, ge=0)
    # When true, only arm BE if the evaluation bar is still "valid".
    breakeven_requires_valid: bool = True
    # above_ema = long close > EMA(period); always = arm regardless of EMA.
    breakeven_valid: Literal["above_ema", "always"] = "above_ema"
    breakeven_ema_period: int = Field(default=9, ge=2)
    time_in_force: str = "day"

    @field_validator("exit", mode="before")
    @classmethod
    def _exit(cls, v: Any) -> str:
        if v is None or str(v).strip() == "":
            return "fixed_bracket"
        key = str(v).strip().lower().replace("-", "_").replace(" ", "_")
        if key not in EXIT_ALIASES:
            raise ValueError(
                "exit must be 'ema_invalid', 'ma_cross', 'ma_cross_close', "
                "'lower_high', or 'fixed_bracket'"
            )
        return EXIT_ALIASES[key]

    @field_validator("breakeven_after_bars", mode="before")
    @classmethod
    def _be_bars(cls, v: Any) -> int:
        if v is None or str(v).strip() == "":
            return 0
        return v

    @field_validator("breakeven_valid", mode="before")
    @classmethod
    def _be_valid(cls, v: Any) -> str:
        if v is None or str(v).strip() == "":
            return "above_ema"
        key = str(v).strip().lower().replace("-", "_").replace(" ", "_")
        if key not in BREAKEVEN_VALID_MODES:
            raise ValueError("breakeven_valid must be 'above_ema' or 'always'")
        return key

    @field_validator("stop_mode", mode="before")
    @classmethod
    def _stop_mode(cls, v: Any) -> str:
        if v is None or str(v).strip() == "":
            return "percent"
        key = str(v).strip().lower().replace("-", "_").replace(" ", "_")
        if key not in STOP_MODE_ALIASES:
            raise ValueError(
                "stop_mode must be 'percent', 'sma20', 'entry_pct', 'lock_plus', or 'trail'"
            )
        return STOP_MODE_ALIASES[key]

    @field_validator("take_anchor", mode="before")
    @classmethod
    def _take_anchor(cls, v: Any) -> str:
        if v is None or str(v).strip() == "":
            return "signal"
        key = str(v).strip().lower().replace("-", "_").replace(" ", "_")
        if key not in TAKE_ANCHOR_ALIASES:
            raise ValueError("take_anchor must be 'signal' or 'entry'")
        return TAKE_ANCHOR_ALIASES[key]

    @model_validator(mode="after")
    def _size_required(self) -> "ActionSpec":
        if self.type in {"buy", "sell"} and self.size is None:
            raise ValueError("buy/sell actions require size (shares, percent_equity, or risk_pct)")
        if self.pyramid_on_lock:
            if self.stop_mode != "lock_plus":
                raise ValueError("pyramid_on_lock requires stop_mode: lock_plus")
            if self.take_profit_pct is None:
                raise ValueError("pyramid_on_lock requires take_profit_pct")
            self.take_anchor = "entry"
        if self.pyramid_add_pct is not None:
            if self.stop_mode != "lock_plus":
                raise ValueError("pyramid_add_pct requires stop_mode: lock_plus")
        if self.partial_take_on_lock:
            if self.stop_mode != "lock_plus":
                raise ValueError("partial_take_on_lock requires stop_mode: lock_plus")
            if self.pyramid_on_lock or self.pyramid_add_pct is not None:
                raise ValueError("partial_take_on_lock cannot combine with pyramid adds")
        if self.partial_take_be:
            if self.stop_mode != "lock_plus":
                raise ValueError("partial_take_be requires stop_mode: lock_plus")
            if self.pyramid_on_lock or self.pyramid_add_pct is not None:
                raise ValueError("partial_take_be cannot combine with pyramid adds")
            if self.partial_take_on_lock:
                raise ValueError("partial_take_be cannot combine with partial_take_on_lock")
        return self

    def has_pyramid_add(self) -> bool:
        return self.pyramid_on_lock or self.pyramid_add_pct is not None

    def resolved_pyramid_add_pct(self) -> Optional[float]:
        if self.pyramid_add_pct is not None:
            return self.pyramid_add_pct
        if self.pyramid_on_lock:
            return self.resolved_lock_trigger_pct()
        return None

    def resolved_lock_trigger_pct(self) -> Optional[float]:
        if self.lock_trigger_pct is not None:
            return self.lock_trigger_pct
        return self.stop_loss_pct

    def resolved_lock_stop_pct(self) -> Optional[float]:
        if self.lock_stop_pct is not None:
            return self.lock_stop_pct
        return self.stop_loss_pct

    def resolved_trail_pct(self) -> Optional[float]:
        if self.trail_pct is not None:
            return self.trail_pct
        return self.stop_loss_pct


class PatternCond(BaseModel):
    kind: Literal["pattern"] = "pattern"
    name: str
    timeframe: str

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        key = v.strip().lower().replace("-", "_").replace(" ", "_")
        if key not in PATTERN_NAMES:
            raise ValueError(f"unknown pattern {v!r}; known: {', '.join(PATTERN_NAMES)}")
        return key

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)


class MaCond(BaseModel):
    kind: Literal["ma"] = "ma"
    ma: Literal["sma", "ema"] = "sma"
    period: int = Field(..., ge=2)
    timeframe: str
    compare: Literal["above", "below"] = "above"

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)


class RsiCond(BaseModel):
    kind: Literal["rsi"] = "rsi"
    period: int = Field(default=14, ge=2)
    timeframe: str
    above: Optional[float] = None
    below: Optional[float] = None

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)

    @model_validator(mode="after")
    def _bound(self) -> "RsiCond":
        if self.above is None and self.below is None:
            raise ValueError("rsi condition needs above and/or below")
        return self


class VolumeCond(BaseModel):
    kind: Literal["volume"] = "volume"
    timeframe: str
    period: int = Field(default=20, ge=2)
    multiplier: float = Field(default=1.0, gt=0)
    compare: Literal["above", "below"] = "above"

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)


class VolumePrevCond(BaseModel):
    """Last (signal) bar volume vs the immediately previous bar."""

    kind: Literal["volume_prev"] = "volume_prev"
    timeframe: str
    compare: Literal["above", "below"] = "above"

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)


class MaCrossCond(BaseModel):
    """Close crossing an SMA/EMA: prev close vs prev MA, curr close vs curr MA."""

    kind: Literal["ma_cross"] = "ma_cross"
    ma: Literal["sma", "ema"] = "ema"
    period: int = Field(..., ge=2)
    timeframe: str
    direction: Literal["bullish", "bearish"] = "bullish"

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)


class MaPairCrossCond(BaseModel):
    """EMA crossing SMA: prev EMA vs prev SMA, curr EMA vs curr SMA."""

    kind: Literal["ma_pair_cross"] = "ma_pair_cross"
    ema_period: int = Field(default=9, ge=2)
    sma_period: int = Field(default=20, ge=2)
    timeframe: str
    direction: Literal["bullish", "bearish"] = "bullish"

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)


LeafCondition = Union[
    PatternCond, MaCond, RsiCond, VolumeCond, VolumePrevCond, MaCrossCond, MaPairCrossCond
]


class GroupCond(BaseModel):
    kind: Literal["all", "any"]
    conditions: list["AnyCondition"]


AnyCondition = Union[GroupCond, LeafCondition]


class RuleSpec(BaseModel):
    id: str
    enabled: bool = True
    symbols: Optional[list[str]] = None
    cooldown_minutes: int = Field(default=60, ge=0)
    when: AnyCondition
    action: ActionSpec
    notes: Optional[str] = None

    @field_validator("symbols")
    @classmethod
    def _syms(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        return [s.strip().upper() for s in v if s.strip()]


class Settings(BaseModel):
    paper: bool = True
    allow_live: bool = False
    dry_run: bool = True
    poll_interval_seconds: int = Field(default=60, ge=5)
    kill_switch_file: str = "data/KILL"
    state_file: str = "data/state.json"
    max_open_positions: int = Field(default=10, ge=1)
    data_feed: str = "iex"
    lookback_bars: int = Field(default=80, ge=20)
    # If set, every rule condition is rewritten to this bar size on load.
    # Per-condition timeframe still documents the default; cooldown stays minutes.
    timeframe: Optional[str] = None
    # Session clock (product gates for ema9_trend). Null/off disables that gate.
    # entry_cutoff: reject signals whose fill (next-bar open) is at/after this clock.
    # flatten_by: force-flat at the close of the bar containing this clock
    #   (15m + 15:55 → 15:45 ET bar close; 5m + 15:55 → 15:50 ET bar close).
    session_timezone: str = "America/New_York"
    entry_cutoff: Optional[str] = None
    flatten_by: Optional[str] = None

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return None
        return normalize(v)

    @field_validator("session_timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        return parse_timezone(v)

    @field_validator("entry_cutoff", "flatten_by")
    @classmethod
    def _hhmm(cls, v: Optional[str]) -> Optional[str]:
        return parse_optional_hhmm(v)


class BotConfig(BaseModel):
    settings: Settings = Field(default_factory=Settings)
    universe: list[str] = Field(default_factory=list)
    rules: list[RuleSpec]

    @field_validator("universe")
    @classmethod
    def _uni(cls, v: list[str]) -> list[str]:
        return [s.strip().upper() for s in v if s.strip()]

    def symbols_for(self, rule: RuleSpec) -> list[str]:
        if rule.symbols:
            return rule.symbols
        return list(self.universe)

    def all_symbol_timeframes(self) -> set[tuple[str, str]]:
        pairs: set[tuple[str, str]] = set()

        def walk(cond: AnyCondition, symbols: list[str]) -> None:
            if isinstance(cond, GroupCond):
                for child in cond.conditions:
                    walk(child, symbols)
                return
            tf = cond.timeframe
            for sym in symbols:
                pairs.add((sym, tf))

        for rule in self.rules:
            if not rule.enabled:
                continue
            walk(rule.when, self.symbols_for(rule))
        return pairs


def _condition_timeframe(*sources: Any, default: Optional[str] = None) -> str:
    for src in sources:
        if isinstance(src, dict) and src.get("timeframe"):
            return str(src["timeframe"])
    if default:
        return default
    raise ValueError(
        "condition needs timeframe (set settings.timeframe or a per-condition timeframe)"
    )


def condition_timeframes(cond: AnyCondition) -> set[str]:
    if isinstance(cond, GroupCond):
        out: set[str] = set()
        for child in cond.conditions:
            out |= condition_timeframes(child)
        return out
    return {cond.timeframe}


def rewrite_condition_timeframe(cond: AnyCondition, timeframe: str) -> AnyCondition:
    tf = normalize(timeframe)
    if isinstance(cond, GroupCond):
        return GroupCond(
            kind=cond.kind,
            conditions=[rewrite_condition_timeframe(child, tf) for child in cond.conditions],
        )
    return cond.model_copy(update={"timeframe": tf})


def with_timeframe(config: BotConfig, timeframe: str) -> BotConfig:
    """Rewrite every rule condition to ``timeframe``. Cooldown stays wall-clock minutes."""
    tf = normalize(timeframe)
    settings = config.settings.model_copy(update={"timeframe": tf})
    rules = [
        rule.model_copy(update={"when": rewrite_condition_timeframe(rule.when, tf)})
        for rule in config.rules
    ]
    return BotConfig(settings=settings, universe=list(config.universe), rules=rules)


def restrict_universe(config: BotConfig, symbols: Optional[list[str]]) -> BotConfig:
    """Keep only ``symbols`` in the universe and on each rule's symbol list."""
    if not symbols:
        return config
    wanted = [s.strip().upper() for s in symbols if s and str(s).strip()]
    wanted_set = set(wanted)
    if not wanted_set:
        return config
    rules: list[RuleSpec] = []
    for rule in config.rules:
        if rule.symbols:
            kept = [s for s in rule.symbols if s in wanted_set]
            if not kept:
                continue
            rules.append(rule.model_copy(update={"symbols": kept}))
        else:
            rules.append(rule)
    if not rules:
        raise ValueError(f"No rules remain after restricting universe to {wanted}")
    return BotConfig(settings=config.settings, universe=wanted, rules=rules)


def timeframe_label(config: BotConfig) -> str:
    """Short bar-size tag for book labels (15m / 5m). Empty if unset."""
    tf = config.settings.timeframe
    if not tf:
        return ""
    aliases = {"15Min": "15m", "5Min": "5m", "1Min": "1m", "30Min": "30m", "1Hour": "1h", "1Day": "1d"}
    return aliases.get(tf, tf)


def _normalize_cross_direction(raw: Any, default: str = "bullish") -> str:
    if raw is None:
        return default
    direction = str(raw).strip().lower()
    if direction in {"above", "up", "long", "over", "cross_over", "cross-over"}:
        return "bullish"
    if direction in {"below", "down", "short", "under", "cross_under", "cross-under"}:
        return "bearish"
    return direction


_PAIR_CROSS_KEYS = ("ema_sma_cross", "ma_pair_cross", "ema_cross_sma")
_RSI_LEAF_KEYS = ("rsi", "rsi_below", "rsi_above")
_VOLUME_PREV_KEYS = ("volume_gt_prev", "volume_vs_prev", "volume_above_prev")
_VOLUME_PREV_VS = frozenset({"prev", "previous", "prior", "last"})


def _volume_prev_compare(raw: dict[str, Any], default: str = "above") -> str:
    compare = str(raw.get("compare") or default).strip().lower()
    if compare in {"above", "gt", "greater", "over"}:
        return "above"
    if compare in {"below", "lt", "less", "under"}:
        return "below"
    return default


def _is_volume_prev(raw: dict[str, Any]) -> bool:
    if any(key in raw for key in _VOLUME_PREV_KEYS):
        return True
    block = raw.get("volume") if isinstance(raw.get("volume"), dict) else {}
    vs = str(block.get("vs") or raw.get("vs") or "").strip().lower()
    return vs in _VOLUME_PREV_VS


def _parse_volume_prev(raw: dict[str, Any], default_timeframe: Optional[str] = None) -> VolumePrevCond:
    block: dict[str, Any] = {}
    for key in _VOLUME_PREV_KEYS:
        val = raw.get(key)
        if isinstance(val, dict):
            block = val
            break
    volume_block = raw.get("volume") if isinstance(raw.get("volume"), dict) else {}
    merged = {**volume_block, **block, **{k: v for k, v in raw.items() if k not in {"volume", *_VOLUME_PREV_KEYS}}}
    return VolumePrevCond(
        timeframe=_condition_timeframe(merged, raw, default=default_timeframe),
        compare=_volume_prev_compare(merged),
    )


def find_volume_prev_condition(cond: AnyCondition) -> Optional[VolumePrevCond]:
    """First previous-bar volume leaf in a condition tree, if any."""
    if isinstance(cond, VolumePrevCond):
        return cond
    if isinstance(cond, GroupCond):
        for child in cond.conditions:
            found = find_volume_prev_condition(child)
            if found is not None:
                return found
    return None


def has_volume_gt_prev(cond: AnyCondition) -> bool:
    """True when the tree requires signal-bar volume > previous-bar volume."""
    found = find_volume_prev_condition(cond)
    return found is not None and found.compare == "above"


def find_rsi_condition(cond: AnyCondition) -> Optional[RsiCond]:
    """First RSI leaf in a condition tree, if any."""
    if isinstance(cond, RsiCond):
        return cond
    if isinstance(cond, GroupCond):
        for child in cond.conditions:
            found = find_rsi_condition(child)
            if found is not None:
                return found
    return None


def has_pair_cross(cond: AnyCondition) -> bool:
    if isinstance(cond, MaPairCrossCond):
        return True
    if isinstance(cond, GroupCond):
        return any(has_pair_cross(child) for child in cond.conditions)
    return False


def _flatten_conditions(cond: AnyCondition) -> list[AnyCondition]:
    if isinstance(cond, GroupCond):
        out: list[AnyCondition] = []
        for child in cond.conditions:
            out.extend(_flatten_conditions(child))
        return out
    return [cond]


def has_noon_stack(cond: AnyCondition) -> bool:
    """Price EMA-cross + SMA-above + RSI — the default ema9_trend long entry."""
    leaves = _flatten_conditions(cond)
    has_cross = any(
        isinstance(leaf, MaCrossCond) and leaf.ma == "ema" and leaf.direction == "bullish"
        for leaf in leaves
    )
    has_sma = any(
        isinstance(leaf, MaCond) and leaf.ma == "sma" and leaf.compare == "above"
        for leaf in leaves
    )
    has_rsi = any(isinstance(leaf, RsiCond) for leaf in leaves)
    return has_cross and has_sma and has_rsi


def has_noon_short_stack(cond: AnyCondition) -> bool:
    """Bearish EMA-cross + SMA-below — the ema9_trend_short entry (no RSI)."""
    leaves = _flatten_conditions(cond)
    has_cross = any(
        isinstance(leaf, MaCrossCond) and leaf.ma == "ema" and leaf.direction == "bearish"
        for leaf in leaves
    )
    has_sma = any(
        isinstance(leaf, MaCond) and leaf.ma == "sma" and leaf.compare == "below"
        for leaf in leaves
    )
    return has_cross and has_sma


def entry_sides(config: BotConfig) -> set[str]:
    """Enabled entry action types: ``{'buy'}``, ``{'sell'}``, or both."""
    return {
        rule.action.type
        for rule in config.rules
        if rule.enabled and rule.action.type in {"buy", "sell"}
    }


def rsi_filter_label(config: BotConfig) -> Optional[str]:
    """Short book-label tag such as ``RSI14 < 70`` (pair-cross books only)."""
    for rule in config.rules:
        if not rule.enabled or rule.action.type == "close":
            continue
        if not has_pair_cross(rule.when):
            continue
        rsi_cond = find_rsi_condition(rule.when)
        if rsi_cond is None:
            continue
        parts: list[str] = []
        if rsi_cond.below is not None:
            parts.append(f"< {rsi_cond.below:g}")
        if rsi_cond.above is not None:
            parts.append(f"> {rsi_cond.above:g}")
        if not parts:
            continue
        return f"RSI{rsi_cond.period} {' '.join(parts)}"
    return None


def _lift_nested_rsi(raw: dict[str, Any]) -> dict[str, Any]:
    """Treat ``ema_sma_cross: { ..., rsi: { period, below } }`` as a sibling rsi toggle."""
    out = dict(raw)
    for key in _PAIR_CROSS_KEYS:
        block = out.get(key)
        if not isinstance(block, dict) or "rsi" not in block:
            continue
        if "rsi" not in out:
            out["rsi"] = block["rsi"]
        out[key] = {k: v for k, v in block.items() if k != "rsi"}
        break
    return out


def _pair_cross_timeframe(raw: dict[str, Any]) -> Optional[str]:
    for key in _PAIR_CROSS_KEYS:
        block = raw.get(key)
        if isinstance(block, dict) and block.get("timeframe"):
            return str(block["timeframe"])
    if raw.get("timeframe"):
        return str(raw["timeframe"])
    return None


def _parse_ma_pair_cross(raw: dict[str, Any], default_timeframe: Optional[str] = None) -> MaPairCrossCond:
    block = (
        raw.get("ema_sma_cross")
        or raw.get("ma_pair_cross")
        or raw.get("ema_cross_sma")
        or {}
    )
    if not isinstance(block, dict):
        block = {}
    skip = {*_PAIR_CROSS_KEYS, *_RSI_LEAF_KEYS}
    merged = {**block, **{k: v for k, v in raw.items() if k not in skip}}
    direction = _normalize_cross_direction(merged.get("direction") or merged.get("compare"))
    return MaPairCrossCond(
        ema_period=int(merged.get("ema_period", merged.get("fast_period", 9))),
        sma_period=int(merged.get("sma_period", merged.get("slow_period", 20))),
        timeframe=_condition_timeframe(merged, raw, default=default_timeframe),
        direction=direction,
    )


def _parse_ma_cross(raw: dict[str, Any], default_timeframe: Optional[str] = None) -> MaCrossCond:
    block = (
        raw.get("ema_cross")
        or raw.get("sma_cross")
        or raw.get("ma_cross")
        or raw.get("cross")
        or {}
    )
    if not isinstance(block, dict):
        block = {}
    skip = {"ema_cross", "sma_cross", "ma_cross", "cross"}
    merged = {**block, **{k: v for k, v in raw.items() if k not in skip}}
    if "ema_cross" in raw:
        ma = "ema"
    elif "sma_cross" in raw:
        ma = "sma"
    else:
        ma = merged.get("ma") or merged.get("kind") or "ema"
        if ma not in {"sma", "ema"}:
            ma = "ema"
    direction = merged.get("direction")
    if direction is None:
        compare = merged.get("compare")
        if compare == "below":
            direction = "bearish"
        else:
            direction = "bullish"
    direction = _normalize_cross_direction(direction)
    return MaCrossCond(
        ma=ma,
        period=int(merged["period"]),
        timeframe=_condition_timeframe(merged, raw, default=default_timeframe),
        direction=direction,
    )


def _parse_leaf(raw: dict[str, Any], default_timeframe: Optional[str] = None) -> LeafCondition:
    """Accept several human-friendly YAML shapes for a single condition."""
    if "pattern" in raw:
        name = raw["pattern"]
        if isinstance(name, dict):
            return PatternCond(
                name=name.get("name") or name.get("pattern"),
                timeframe=_condition_timeframe(name, raw, default=default_timeframe),
            )
        return PatternCond(name=name, timeframe=_condition_timeframe(raw, default=default_timeframe))
    if any(key in raw for key in ("ema_sma_cross", "ma_pair_cross", "ema_cross_sma")):
        return _parse_ma_pair_cross(raw, default_timeframe=default_timeframe)
    if any(key in raw for key in ("ema_cross", "sma_cross", "ma_cross", "cross")):
        return _parse_ma_cross(raw, default_timeframe=default_timeframe)
    if "sma" in raw or "ema" in raw or "price_vs_ma" in raw:
        block = raw.get("sma") or raw.get("ema") or raw.get("price_vs_ma") or {}
        if not isinstance(block, dict):
            block = {}
        merged = {**block, **{k: v for k, v in raw.items() if k not in {"sma", "ema", "price_vs_ma"}}}
        ma = "ema" if "ema" in raw else merged.get("ma") or merged.get("kind") or "sma"
        if ma not in {"sma", "ema"}:
            ma = "sma"
        compare = merged.get("compare") or ("below" if merged.get("below") else "above")
        return MaCond(
            ma=ma,
            period=int(merged["period"]),
            timeframe=_condition_timeframe(merged, raw, default=default_timeframe),
            compare=compare,
        )
    if "rsi" in raw or "rsi_below" in raw or "rsi_above" in raw:
        block = raw.get("rsi") if isinstance(raw.get("rsi"), dict) else {}
        merged = {**block, **{k: v for k, v in raw.items() if k != "rsi"}}
        below = merged.get("below", merged.get("rsi_below"))
        above = merged.get("above", merged.get("rsi_above"))
        return RsiCond(
            period=int(merged.get("period", 14)),
            timeframe=_condition_timeframe(merged, raw, default=default_timeframe),
            below=below,
            above=above,
        )
    if _is_volume_prev(raw):
        return _parse_volume_prev(raw, default_timeframe=default_timeframe)
    if "volume" in raw or "volume_above_avg" in raw:
        block = raw.get("volume") if isinstance(raw.get("volume"), dict) else {}
        merged = {**block, **{k: v for k, v in raw.items() if k != "volume"}}
        mult = merged.get("multiplier", merged.get("volume_above_avg", 1.0))
        return VolumeCond(
            period=int(merged.get("period", 20)),
            timeframe=_condition_timeframe(merged, raw, default=default_timeframe),
            multiplier=float(mult),
            compare=merged.get("compare", "above"),
        )
    raise ValueError(f"Unrecognized condition: {raw!r}")


def parse_condition(raw: Any, default_timeframe: Optional[str] = None) -> AnyCondition:
    if not isinstance(raw, dict):
        raise ValueError(f"Condition must be a mapping, got {type(raw).__name__}")
    if "all" in raw and raw["all"] is not None:
        children = raw["all"]
        extra = {k: v for k, v in raw.items() if k != "all"}
        if extra:
            # `{all: [...], pattern: ...}` is invalid; keep strict
            raise ValueError(f"'all' group cannot mix leaf keys: {list(extra)}")
        return GroupCond(
            kind="all",
            conditions=[parse_condition(c, default_timeframe=default_timeframe) for c in children],
        )
    if "any" in raw and raw["any"] is not None:
        extra = {k: v for k, v in raw.items() if k != "any"}
        if extra:
            raise ValueError(f"'any' group cannot mix leaf keys: {list(extra)}")
        return GroupCond(
            kind="any",
            conditions=[parse_condition(c, default_timeframe=default_timeframe) for c in raw["any"]],
        )
    raw = _lift_nested_rsi(raw)
    has_pair_cross = any(key in raw for key in _PAIR_CROSS_KEYS)
    has_rsi = any(key in raw for key in _RSI_LEAF_KEYS)
    if has_pair_cross and has_rsi:
        # Sibling toggle: ema_sma_cross + rsi: { period: 14, below: 70 } → AND.
        cross_raw = {k: v for k, v in raw.items() if k not in _RSI_LEAF_KEYS}
        rsi_raw = {k: v for k, v in raw.items() if k in _RSI_LEAF_KEYS}
        pair_tf = _pair_cross_timeframe(cross_raw)
        if "rsi" in rsi_raw and isinstance(rsi_raw["rsi"], dict):
            rsi_block = dict(rsi_raw["rsi"])
            if not rsi_block.get("timeframe") and pair_tf:
                rsi_block["timeframe"] = pair_tf
            rsi_raw = {**rsi_raw, "rsi": rsi_block}
        return GroupCond(
            kind="all",
            conditions=[
                _parse_ma_pair_cross(cross_raw, default_timeframe=default_timeframe),
                _parse_leaf(rsi_raw, default_timeframe=pair_tf or default_timeframe),
            ],
        )
    return _parse_leaf(raw, default_timeframe=default_timeframe)


def _parse_action(raw: dict[str, Any]) -> ActionSpec:
    size_raw = raw.get("size")
    size = None
    if isinstance(size_raw, dict):
        size = SizeSpec.model_validate(size_raw)
    elif size_raw is not None:
        raise ValueError("action.size must be a mapping (type + value, or risk_pct fields)")
    return ActionSpec(
        type=raw["type"],
        size=size,
        order=raw.get("order", "market"),
        limit_offset_pct=raw.get("limit_offset_pct"),
        stop_loss_pct=raw.get("stop_loss_pct"),
        take_profit_pct=raw.get("take_profit_pct"),
        stop_mode=raw.get("stop_mode", "percent"),
        stop_sma_period=raw.get("stop_sma_period", raw.get("sma_period", raw.get("exit_sma_period", 20))),
        lock_trigger_pct=raw.get("lock_trigger_pct"),
        lock_stop_pct=raw.get("lock_stop_pct"),
        trail_pct=raw.get("trail_pct"),
        pyramid_on_lock=raw.get("pyramid_on_lock", False),
        pyramid_add_pct=raw.get("pyramid_add_pct"),
        partial_take_on_lock=raw.get("partial_take_on_lock", False),
        partial_take_be=raw.get("partial_take_be", False),
        take_anchor=raw.get("take_anchor", "signal"),
        exit=raw.get("exit", "fixed_bracket"),
        exit_ema_period=raw.get("exit_ema_period", raw.get("ema_period", 9)),
        exit_sma_period=raw.get("exit_sma_period", raw.get("sma_period", 20)),
        breakeven_after_bars=raw.get("breakeven_after_bars", 0),
        breakeven_requires_valid=raw.get("breakeven_requires_valid", True),
        breakeven_valid=raw.get("breakeven_valid", "above_ema"),
        breakeven_ema_period=raw.get("breakeven_ema_period", 9),
        time_in_force=raw.get("time_in_force", "day"),
    )


def _parse_rule(raw: dict[str, Any], default_timeframe: Optional[str] = None) -> RuleSpec:
    return RuleSpec(
        id=raw["id"],
        enabled=raw.get("enabled", True),
        symbols=raw.get("symbols"),
        cooldown_minutes=raw.get("cooldown_minutes", 60),
        when=parse_condition(raw["when"], default_timeframe=default_timeframe),
        action=_parse_action(raw["action"]),
        notes=raw.get("notes"),
    )


def load_config(path: str | Path, timeframe: Optional[str] = None) -> BotConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".json"}:
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping")

    settings = Settings.model_validate(data.get("settings") or {})
    universe = data.get("universe") or []
    if isinstance(universe, dict):
        universe = universe.get("symbols") or []
    rules = [_parse_rule(r, default_timeframe=settings.timeframe) for r in (data.get("rules") or [])]
    if not rules:
        raise ValueError("Config must define at least one rule")
    ids = [r.id for r in rules]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate rule ids: {ids}")
    cfg = BotConfig(settings=settings, universe=list(universe), rules=rules)
    override = timeframe or settings.timeframe
    if override:
        cfg = with_timeframe(cfg, override)
    return cfg
