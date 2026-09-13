"""Timeframe aliases and helpers for closed-bar filtering."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Human aliases → Alpaca v2 timeframe strings
_TO_ALPACA = {
    "1m": "1Min",
    "1min": "1Min",
    "5m": "5Min",
    "5min": "5Min",
    "15m": "15Min",
    "15min": "15Min",
    "30m": "30Min",
    "30min": "30Min",
    "1h": "1Hour",
    "1hr": "1Hour",
    "1hour": "1Hour",
    "4h": "4Hour",
    "4hour": "4Hour",
    "1d": "1Day",
    "1day": "1Day",
    "d": "1Day",
    "1w": "1Week",
    "1week": "1Week",
}

_DURATION = {
    "1Min": timedelta(minutes=1),
    "5Min": timedelta(minutes=5),
    "15Min": timedelta(minutes=15),
    "30Min": timedelta(minutes=30),
    "1Hour": timedelta(hours=1),
    "4Hour": timedelta(hours=4),
    "1Day": timedelta(days=1),
    "1Week": timedelta(weeks=1),
}


def normalize(tf: str) -> str:
    raw = tf.strip()
    key = raw.lower().replace(" ", "")
    if key in _TO_ALPACA:
        return _TO_ALPACA[key]
    # Already an Alpaca name?
    for official in _DURATION:
        if raw.lower() == official.lower():
            return official
    raise ValueError(
        f"Unsupported timeframe {tf!r}. Use 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w "
        "(or Alpaca names like 15Min)."
    )


def duration(tf: str) -> timedelta:
    return _DURATION[normalize(tf)]


def drop_incomplete(bars, tf: str, now: datetime | None = None):
    """Drop the last bar if it is still forming (timestamp + duration > now)."""
    if not bars:
        return bars
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    last = bars[-1]
    ts = last.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if ts + duration(tf) > now:
        return bars[:-1]
    return bars
