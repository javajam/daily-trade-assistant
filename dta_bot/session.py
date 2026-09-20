"""Intraday session-clock helpers (America/New_York by default).

Bar timestamps are the **open**. Close = open + timeframe duration.

``flatten_by`` 15:55 on aligned RTH bars:
  - 15m opens :00,:15,:30,:45 → flatten at the **15:45 ET bar close**
    (bar covers 15:45–16:00; last regular 15m bar, labeled as the
    end-of-day flatten aligned with “by 15:55”).
  - 5m opens every 5 minutes → flatten at the **15:50 ET bar close**
    (bar covers 15:50–15:55, the last 5m bar that completes at/before 15:55).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from dta_bot.orb import parse_hhmm, session_dt
from dta_bot.timeframes import duration, normalize


def parse_optional_hhmm(value: Optional[str]) -> Optional[str]:
    """Normalize HH:MM; empty / off / none → disabled."""
    if value is None:
        return None
    raw = str(value).strip()
    if raw == "" or raw.lower() in {"none", "off", "disabled"}:
        return None
    parsed = parse_hhmm(raw)
    return f"{parsed.hour:02d}:{parsed.minute:02d}"


def parse_timezone(value: Optional[str]) -> str:
    name = (value or "").strip() or "America/New_York"
    ZoneInfo(name)  # raises if unknown
    return name


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def session_clock(dt: datetime, hhmm: str, tz_name: str) -> datetime:
    """``hhmm`` on the session calendar date of ``dt`` in ``tz_name``."""
    zone = ZoneInfo(tz_name)
    day = _aware(dt).astimezone(zone).date()
    return session_dt(day, hhmm, tz_name)


def fill_at_or_after_cutoff(
    fill_ts: datetime,
    cutoff: Optional[str],
    tz_name: str,
) -> bool:
    """True when a fill at ``fill_ts`` must be rejected (at/after cutoff)."""
    if not cutoff:
        return False
    return _aware(fill_ts) >= session_clock(fill_ts, cutoff, tz_name)


def is_flatten_bar(
    bar_open: datetime,
    timeframe: str,
    flatten_by: Optional[str],
    tz_name: str,
) -> bool:
    """True when ``flatten_by`` falls in ``(bar_open, bar_close]``.

    That is the last regular bar whose close is at or after the flatten
    clock, which for 15m/15:55 is the 15:45 open and for 5m/15:55 is the
    15:50 open.
    """
    if not flatten_by:
        return False
    open_ts = _aware(bar_open)
    close_ts = open_ts + duration(normalize(timeframe))
    clock = session_clock(open_ts, flatten_by, tz_name)
    return open_ts < clock <= close_ts


def wall_clock_at_or_after(
    now: datetime,
    hhmm: Optional[str],
    tz_name: str,
) -> bool:
    if not hhmm:
        return False
    return _aware(now) >= session_clock(now, hhmm, tz_name)


def bar_opens_at(
    bar_open: datetime,
    hhmm: Optional[str],
    tz_name: str,
) -> bool:
    """True when ``bar_open``'s local clock equals ``hhmm`` in ``tz_name``.

    Bar timestamps may be stored in UTC (Yahoo) or already in the session
    zone; both are converted before the hour:minute compare.
    """
    if not hhmm:
        return False
    local = _aware(bar_open).astimezone(ZoneInfo(tz_name))
    clock = parse_hhmm(hhmm)
    return local.hour == clock.hour and local.minute == clock.minute
