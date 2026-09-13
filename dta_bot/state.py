"""Persisted runner state: cooldowns and per-bar fire keys (idempotency)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fmt_ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


@dataclass
class BotState:
    fired_keys: dict[str, str] = field(default_factory=dict)
    cooldowns_until: dict[str, str] = field(default_factory=dict)

    def already_fired(self, key: str) -> bool:
        return key in self.fired_keys

    def mark_fired(self, key: str, cooldown_key: str, cooldown_minutes: int, when: Optional[datetime] = None) -> None:
        when = when or _now()
        self.fired_keys[key] = fmt_ts(when)
        if cooldown_minutes > 0:
            until = when.timestamp() + cooldown_minutes * 60
            self.cooldowns_until[cooldown_key] = fmt_ts(
                datetime.fromtimestamp(until, tz=timezone.utc)
            )

    def on_cooldown(self, cooldown_key: str, now: Optional[datetime] = None) -> Optional[datetime]:
        raw = self.cooldowns_until.get(cooldown_key)
        if not raw:
            return None
        until = parse_ts(raw)
        now = now or _now()
        if now < until:
            return until
        return None


def load_state(path: str | Path) -> BotState:
    path = Path(path)
    if not path.exists():
        return BotState()
    data = json.loads(path.read_text(encoding="utf-8"))
    return BotState(
        fired_keys=dict(data.get("fired_keys") or {}),
        cooldowns_until=dict(data.get("cooldowns_until") or {}),
    )


def save_state(path: str | Path, state: BotState) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fired_keys": state.fired_keys,
        "cooldowns_until": state.cooldowns_until,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
