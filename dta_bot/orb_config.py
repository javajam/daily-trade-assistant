"""Human-editable YAML/JSON config for the ORB edge-fade strategy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from dta_bot.config import Settings, SizeSpec
from dta_bot.orb import parse_hhmm
from dta_bot.timeframes import normalize


class OrbSpec(BaseModel):
    session_open: str = "09:30"
    session_close: str = "16:00"
    session_timezone: str = "America/New_York"
    orb_timeframe: str = "15m"
    signal_timeframe: str = "5m"
    edge_pct: float = Field(default=0.05, gt=0)
    # One open position per symbol (no blind pyramiding).
    # skip = ignore new entries until flat (default).
    # replace = close the open lot and take the new signal.
    on_open_position: Literal["skip", "replace"] = "skip"
    # v1 take-profit is the OR midpoint. Exit strategy will be A/B tested later.
    take_profit: Literal["midpoint"] = "midpoint"
    cooldown_minutes: int = Field(default=0, ge=0)

    @field_validator("orb_timeframe", "signal_timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        return normalize(v)

    @field_validator("session_open", "session_close")
    @classmethod
    def _hhmm(cls, v: str) -> str:
        parsed = parse_hhmm(v)
        return f"{parsed.hour:02d}:{parsed.minute:02d}"

    @field_validator("session_timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        name = (v or "").strip() or "America/New_York"
        from zoneinfo import ZoneInfo

        ZoneInfo(name)  # raises if unknown
        return name

    @field_validator("edge_pct")
    @classmethod
    def _edge(cls, v: float) -> float:
        if v > 1:
            raise ValueError(
                f"edge_pct should be a fraction of OR height (0.05 = 5%), not {v}. "
                "Use 0.05 for a 5% band."
            )
        return v

    @field_validator("on_open_position", mode="before")
    @classmethod
    def _pos(cls, v: Any) -> str:
        key = str(v or "skip").strip().lower()
        aliases = {"skip": "skip", "flat": "skip", "flat_only": "skip", "replace": "replace", "flip": "replace"}
        if key not in aliases:
            raise ValueError("on_open_position must be 'skip' or 'replace'")
        return aliases[key]


class OrderSpec(BaseModel):
    type: Literal["market", "limit"] = "market"
    time_in_force: str = "day"
    limit_offset_pct: Optional[float] = None


class OrbBotConfig(BaseModel):
    strategy: Literal["orb_reversal"] = "orb_reversal"
    settings: Settings = Field(default_factory=Settings)
    universe: list[str] = Field(default_factory=list)
    orb: OrbSpec = Field(default_factory=OrbSpec)
    sizing: SizeSpec = Field(default_factory=lambda: SizeSpec(type="shares", value=10))
    order: OrderSpec = Field(default_factory=OrderSpec)

    @field_validator("universe")
    @classmethod
    def _uni(cls, v: list[str]) -> list[str]:
        return [s.strip().upper() for s in v if str(s).strip()]

    @model_validator(mode="after")
    def _paper_defaults(self) -> "OrbBotConfig":
        # Never flip paper/live gates just because this is the ORB config.
        return self

    def all_symbol_timeframes(self) -> set[tuple[str, str]]:
        pairs: set[tuple[str, str]] = set()
        tfs = {self.orb.orb_timeframe, self.orb.signal_timeframe}
        for symbol in self.universe:
            for tf in tfs:
                pairs.add((symbol, tf))
        return pairs


def peek_config_kind(path: str | Path) -> str:
    """Return 'orb' or 'rules' based on the file contents."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return "rules"
    strategy = str(data.get("strategy") or "").strip().lower()
    if strategy == "orb_reversal" or ("orb" in data and not data.get("rules")):
        return "orb"
    return "rules"


def load_orb_config(path: str | Path) -> OrbBotConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping")
    settings = Settings.model_validate(data.get("settings") or {})
    universe = data.get("universe") or []
    if isinstance(universe, dict):
        universe = universe.get("symbols") or []
    orb_raw = data.get("orb") or {}
    sizing_raw = data.get("sizing") or {"type": "shares", "value": 10}
    order_raw = data.get("order") or {}
    return OrbBotConfig(
        strategy="orb_reversal",
        settings=settings,
        universe=list(universe),
        orb=OrbSpec.model_validate(orb_raw),
        sizing=SizeSpec.model_validate(sizing_raw),
        order=OrderSpec.model_validate(order_raw),
    )
