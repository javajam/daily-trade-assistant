from datetime import datetime, timedelta, timezone

from dta_bot.models import Bar


def ts(i: int, minutes: int = 15) -> datetime:
    return datetime(2026, 9, 11, 13, 30, tzinfo=timezone.utc) + timedelta(minutes=minutes * i)


def bar(
    i: int,
    o: float,
    h: float,
    l: float,
    c: float,
    v: float = 1000,
    minutes: int = 15,
) -> Bar:
    return Bar(timestamp=ts(i, minutes), open=o, high=h, low=l, close=c, volume=v)
