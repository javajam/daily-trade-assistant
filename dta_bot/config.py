"""Load and validate human-editable YAML/JSON rule files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from dta_bot.patterns import PATTERN_NAMES
from dta_bot.timeframes import normalize


class SizeSpec(BaseModel):
    type: Literal["shares", "percent_equity"] = "shares"
    value: float = Field(..., gt=0)

    @field_validator("type")
    @classmethod
    def _type(cls, v: str) -> str:
        return v.lower()


EXIT_MODES = ("fixed_bracket", "ema_invalid")
EXIT_ALIASES = {
    "ema_invalid": "ema_invalid",
    "ema_invalidation": "ema_invalid",
    "ema9_invalid": "ema_invalid",
    "hold_ema": "ema_invalid",
    "invalid": "ema_invalid",
    "fixed_bracket": "fixed_bracket",
    "bracket": "fixed_bracket",
    "fixed": "fixed_bracket",
}


class ActionSpec(BaseModel):
    type: Literal["buy", "sell", "close"]
    size: Optional[SizeSpec] = None
    order: Literal["market", "limit"] = "market"
    limit_offset_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = Field(default=None, gt=0)
    take_profit_pct: Optional[float] = Field(default=None, gt=0)
    # fixed_bracket = optional % stop/take. ema_invalid = hold until a
    # signal-timeframe close is on the wrong side of EMA (long: close < EMA).
    # Optional stop_loss_pct is then a catastrophic stop only; take is ignored.
    exit: Literal["fixed_bracket", "ema_invalid"] = "fixed_bracket"
    exit_ema_period: int = Field(default=9, ge=2)
    time_in_force: str = "day"

    @field_validator("exit", mode="before")
    @classmethod
    def _exit(cls, v: Any) -> str:
        if v is None or str(v).strip() == "":
            return "fixed_bracket"
        key = str(v).strip().lower().replace("-", "_").replace(" ", "_")
        if key not in EXIT_ALIASES:
            raise ValueError("exit must be 'ema_invalid' or 'fixed_bracket'")
        return EXIT_ALIASES[key]

    @model_validator(mode="after")
    def _size_required(self) -> "ActionSpec":
        if self.type in {"buy", "sell"} and self.size is None:
            raise ValueError("buy/sell actions require size (shares or percent_equity)")
        return self


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


LeafCondition = Union[PatternCond, MaCond, RsiCond, VolumeCond, MaCrossCond]


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

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return None
        return normalize(v)


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
    direction = str(direction).strip().lower()
    if direction in {"above", "up", "long"}:
        direction = "bullish"
    elif direction in {"below", "down", "short"}:
        direction = "bearish"
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
    return _parse_leaf(raw, default_timeframe=default_timeframe)


def _parse_action(raw: dict[str, Any]) -> ActionSpec:
    size_raw = raw.get("size")
    size = None
    if isinstance(size_raw, dict):
        size = SizeSpec.model_validate(size_raw)
    elif size_raw is not None:
        raise ValueError("action.size must be {type, value}")
    return ActionSpec(
        type=raw["type"],
        size=size,
        order=raw.get("order", "market"),
        limit_offset_pct=raw.get("limit_offset_pct"),
        stop_loss_pct=raw.get("stop_loss_pct"),
        take_profit_pct=raw.get("take_profit_pct"),
        exit=raw.get("exit", "fixed_bracket"),
        exit_ema_period=raw.get("exit_ema_period", 9),
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
