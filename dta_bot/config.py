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


class ActionSpec(BaseModel):
    type: Literal["buy", "sell", "close"]
    size: Optional[SizeSpec] = None
    order: Literal["market", "limit"] = "market"
    limit_offset_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = Field(default=None, gt=0)
    take_profit_pct: Optional[float] = Field(default=None, gt=0)
    time_in_force: str = "day"

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


LeafCondition = Union[PatternCond, MaCond, RsiCond, VolumeCond]


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


def _parse_leaf(raw: dict[str, Any]) -> LeafCondition:
    """Accept several human-friendly YAML shapes for a single condition."""
    if "pattern" in raw:
        name = raw["pattern"]
        if isinstance(name, dict):
            return PatternCond(name=name.get("name") or name.get("pattern"), timeframe=name["timeframe"])
        return PatternCond(name=name, timeframe=raw["timeframe"])
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
            timeframe=merged.get("timeframe") or raw["timeframe"],
            compare=compare,
        )
    if "rsi" in raw or "rsi_below" in raw or "rsi_above" in raw:
        block = raw.get("rsi") if isinstance(raw.get("rsi"), dict) else {}
        merged = {**block, **{k: v for k, v in raw.items() if k != "rsi"}}
        below = merged.get("below", merged.get("rsi_below"))
        above = merged.get("above", merged.get("rsi_above"))
        return RsiCond(
            period=int(merged.get("period", 14)),
            timeframe=merged.get("timeframe") or raw["timeframe"],
            below=below,
            above=above,
        )
    if "volume" in raw or "volume_above_avg" in raw:
        block = raw.get("volume") if isinstance(raw.get("volume"), dict) else {}
        merged = {**block, **{k: v for k, v in raw.items() if k != "volume"}}
        mult = merged.get("multiplier", merged.get("volume_above_avg", 1.0))
        return VolumeCond(
            period=int(merged.get("period", 20)),
            timeframe=merged.get("timeframe") or raw["timeframe"],
            multiplier=float(mult),
            compare=merged.get("compare", "above"),
        )
    raise ValueError(f"Unrecognized condition: {raw!r}")


def parse_condition(raw: Any) -> AnyCondition:
    if not isinstance(raw, dict):
        raise ValueError(f"Condition must be a mapping, got {type(raw).__name__}")
    if "all" in raw and raw["all"] is not None:
        children = raw["all"]
        extra = {k: v for k, v in raw.items() if k != "all"}
        if extra:
            # `{all: [...], pattern: ...}` is invalid; keep strict
            raise ValueError(f"'all' group cannot mix leaf keys: {list(extra)}")
        return GroupCond(kind="all", conditions=[parse_condition(c) for c in children])
    if "any" in raw and raw["any"] is not None:
        extra = {k: v for k, v in raw.items() if k != "any"}
        if extra:
            raise ValueError(f"'any' group cannot mix leaf keys: {list(extra)}")
        return GroupCond(kind="any", conditions=[parse_condition(c) for c in raw["any"]])
    return _parse_leaf(raw)


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
        time_in_force=raw.get("time_in_force", "day"),
    )


def _parse_rule(raw: dict[str, Any]) -> RuleSpec:
    return RuleSpec(
        id=raw["id"],
        enabled=raw.get("enabled", True),
        symbols=raw.get("symbols"),
        cooldown_minutes=raw.get("cooldown_minutes", 60),
        when=parse_condition(raw["when"]),
        action=_parse_action(raw["action"]),
        notes=raw.get("notes"),
    )


def load_config(path: str | Path) -> BotConfig:
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
    rules = [_parse_rule(r) for r in (data.get("rules") or [])]
    if not rules:
        raise ValueError("Config must define at least one rule")
    ids = [r.id for r in rules]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate rule ids: {ids}")
    return BotConfig(settings=settings, universe=list(universe), rules=rules)
