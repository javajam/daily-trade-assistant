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
    # touch_and_band (default) = wick must reach the OR extreme AND close in the
    # edge_pct band. touch = wick only. edge_band = close-in-band only.
    probe_mode: Literal["touch_and_band", "touch", "edge_band"] = "touch_and_band"
    edge_pct: float = Field(default=0.05, gt=0)
    # One open position per symbol (no blind pyramiding).
    # skip = ignore new entries until flat (default).
    # replace = close the open lot and take the new signal.
    on_open_position: Literal["skip", "replace"] = "skip"
    # close (default) = reversal close must sit inside the OR.
    # body = high and low both inside the OR (stricter fully-inside mode).
    # off = no in-range filter on the reversal candle.
    reversal_in_range: Literal["close", "body", "off"] = "close"
    # one_r (default) = 1R from entry (R = |entry − stop|; long entry+R, short entry−R).
    # or_midpoint = previous OR-midpoint take-profit.
    # first_profitable_close = exit at the close of the first signal-timeframe
    # bar that is strictly profitable vs entry.
    take_profit_mode: Literal["one_r", "or_midpoint", "first_profitable_close"] = "one_r"
    # orb_extreme = long stop at OR low, short stop at OR high (default).
    # reversal_candle = previous stop at the reversal candle extreme.
    stop_mode: Literal["orb_extreme", "reversal_candle"] = "orb_extreme"
    # High-vol gate: skip the symbol/session when OR height / OR open is below
    # this fraction (0.01 = 1%). Denominator is the OR candle open; if that
    # print is missing, the OR midpoint is used. 0 / null disables the gate.
    min_or_height_pct: Optional[float] = 0.01
    # Strict morning window: at most max_trades_before_cutoff entries per symbol
    # whose fill time is strictly before entry_cutoff (session timezone).
    # allow_entries_after_cutoff=false means the session stops taking new entries
    # at/after that clock time. Empty/null disables the clock gate.
    entry_cutoff: Optional[str] = "10:30"
    max_trades_before_cutoff: int = Field(default=1, ge=0)
    allow_entries_after_cutoff: bool = False
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

    @field_validator("min_or_height_pct", mode="before")
    @classmethod
    def _min_or_height(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, str):
            raw = v.strip().lower()
            if raw in {"", "none", "off", "disabled"}:
                return None
            v = float(raw)
        value = float(v)
        if value < 0:
            raise ValueError("min_or_height_pct cannot be negative")
        if value > 1:
            raise ValueError(
                f"min_or_height_pct should be a fraction of OR open (0.01 = 1%), not {value}. "
                "Use 0.01 for a 1% gate, or 0 / null to disable."
            )
        return None if value == 0 else value

    @field_validator("entry_cutoff")
    @classmethod
    def _cutoff(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        raw = str(v).strip()
        if raw == "" or raw.lower() in {"none", "off", "disabled"}:
            return None
        parsed = parse_hhmm(raw)
        return f"{parsed.hour:02d}:{parsed.minute:02d}"

    @field_validator("session_timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        name = (v or "").strip() or "America/New_York"
        from zoneinfo import ZoneInfo

        ZoneInfo(name)  # raises if unknown
        return name

    @field_validator("probe_mode", mode="before")
    @classmethod
    def _probe_mode(cls, v: Any) -> str:
        key = str(v or "touch_and_band").strip().lower().replace("-", "_")
        aliases = {
            "touch_and_band": "touch_and_band",
            "hybrid": "touch_and_band",
            "touch_band": "touch_and_band",
            "both": "touch_and_band",
            "wick_and_band": "touch_and_band",
            "touch": "touch",
            "wick": "touch",
            "extreme": "touch",
            "or_touch": "touch",
            "edge_band": "edge_band",
            "band": "edge_band",
            "close": "edge_band",
            "close_in_band": "edge_band",
        }
        if key not in aliases:
            raise ValueError("probe_mode must be 'touch_and_band', 'touch', or 'edge_band'")
        return aliases[key]

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

    @field_validator("reversal_in_range", mode="before")
    @classmethod
    def _reversal_in_range(cls, v: Any) -> str:
        key = str(v or "close").strip().lower().replace("-", "_")
        aliases = {
            "close": "close",
            "close_inside": "close",
            "in_range": "close",
            "inside": "close",
            "body": "body",
            "full": "body",
            "fully_inside": "body",
            "reversal_fully_inside": "body",
            "range": "body",
            "off": "off",
            "none": "off",
            "disabled": "off",
        }
        if key not in aliases:
            raise ValueError("reversal_in_range must be 'close', 'body', or 'off'")
        return aliases[key]

    @field_validator("take_profit_mode", mode="before")
    @classmethod
    def _take_profit_mode(cls, v: Any) -> str:
        key = str(v or "one_r").strip().lower().replace("-", "_")
        aliases = {
            "one_r": "one_r",
            "1r": "one_r",
            "1_r": "one_r",
            "oner": "one_r",
            "r": "one_r",
            "risk": "one_r",
            "one_r_target": "one_r",
            "first_profitable_close": "first_profitable_close",
            "first_profit": "first_profitable_close",
            "first_close": "first_profitable_close",
            "profitable_close": "first_profitable_close",
            "or_midpoint": "or_midpoint",
            "midpoint": "or_midpoint",
            "mid": "or_midpoint",
            "or_mid": "or_midpoint",
        }
        if key not in aliases:
            raise ValueError(
                "take_profit_mode must be 'one_r', 'or_midpoint', or 'first_profitable_close'"
            )
        return aliases[key]

    @model_validator(mode="before")
    @classmethod
    def _take_profit_alias(cls, data: Any) -> Any:
        # Older YAML used take_profit: midpoint. Honor it only when the new
        # field is omitted so an explicit take_profit_mode always wins.
        if not isinstance(data, dict):
            return data
        if data.get("take_profit_mode") not in (None, ""):
            return data
        raw = data.get("take_profit")
        if raw in (None, ""):
            return data
        key = str(raw).strip().lower().replace("-", "_")
        aliases = {
            "midpoint": "or_midpoint",
            "or_midpoint": "or_midpoint",
            "mid": "or_midpoint",
            "one_r": "one_r",
            "1r": "one_r",
            "1_r": "one_r",
            "first_profitable_close": "first_profitable_close",
            "first_profit": "first_profitable_close",
        }
        mapped = aliases.get(key)
        if mapped:
            data = dict(data)
            data["take_profit_mode"] = mapped
        return data

    @field_validator("stop_mode", mode="before")
    @classmethod
    def _stop_mode(cls, v: Any) -> str:
        key = str(v or "orb_extreme").strip().lower().replace("-", "_")
        aliases = {
            "orb_extreme": "orb_extreme",
            "orb": "orb_extreme",
            "or": "orb_extreme",
            "range": "orb_extreme",
            "opening_range": "orb_extreme",
            "reversal_candle": "reversal_candle",
            "reversal": "reversal_candle",
            "candle": "reversal_candle",
        }
        if key not in aliases:
            raise ValueError("stop_mode must be 'orb_extreme' or 'reversal_candle'")
        return aliases[key]

    def gate_kwargs(self) -> dict[str, Any]:
        return {
            "entry_cutoff": self.entry_cutoff,
            "max_trades_before_cutoff": self.max_trades_before_cutoff,
            "allow_entries_after_cutoff": self.allow_entries_after_cutoff,
            "session_timezone": self.session_timezone,
            "signal_timeframe": self.signal_timeframe,
            "min_or_height_pct": self.min_or_height_pct,
        }

    def detector_kwargs(self) -> dict[str, Any]:
        return {
            "edge_pct": self.edge_pct,
            "probe_mode": self.probe_mode,
            "stop_mode": self.stop_mode,
            "reversal_in_range": self.reversal_in_range,
            "take_profit_mode": self.take_profit_mode,
        }


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
