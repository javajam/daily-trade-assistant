from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from dta_bot.session import (
    fill_at_or_after_cutoff,
    is_flatten_bar,
    parse_optional_hhmm,
    parse_timezone,
    wall_clock_at_or_after,
)

NY = ZoneInfo("America/New_York")


def et(hour: int, minute: int) -> datetime:
    return datetime(2026, 9, 11, hour, minute, tzinfo=NY)


def test_parse_optional_hhmm_normalizes_and_disables():
    assert parse_optional_hhmm("13:00") == "13:00"
    assert parse_optional_hhmm("9:5") == "09:05"
    assert parse_optional_hhmm(None) is None
    assert parse_optional_hhmm("off") is None
    assert parse_optional_hhmm("") is None
    with pytest.raises(ValueError):
        parse_optional_hhmm("25:00")


def test_parse_timezone_defaults_and_rejects_unknown():
    assert parse_timezone(None) == "America/New_York"
    assert parse_timezone("UTC") == "UTC"
    with pytest.raises(Exception):
        parse_timezone("Not/AZone")


def test_fill_at_or_after_cutoff_is_inclusive():
    tz = "America/New_York"
    assert fill_at_or_after_cutoff(et(12, 45), "13:00", tz) is False
    assert fill_at_or_after_cutoff(et(13, 0), "13:00", tz) is True
    assert fill_at_or_after_cutoff(et(13, 15), "13:00", tz) is True
    assert fill_at_or_after_cutoff(et(13, 0), None, tz) is False
    assert fill_at_or_after_cutoff(et(11, 45), "12:00", tz) is False
    assert fill_at_or_after_cutoff(et(12, 0), "12:00", tz) is True
    assert fill_at_or_after_cutoff(et(12, 15), "12:00", tz) is True
    assert fill_at_or_after_cutoff(et(15, 0), "15:15", tz) is False
    assert fill_at_or_after_cutoff(et(15, 15), "15:15", tz) is True
    assert fill_at_or_after_cutoff(et(15, 30), "15:15", tz) is True


def test_is_flatten_bar_15m_uses_1545_close():
    tz = "America/New_York"
    assert is_flatten_bar(et(15, 30), "15m", "15:55", tz) is False
    assert is_flatten_bar(et(15, 45), "15m", "15:55", tz) is True
    assert is_flatten_bar(et(15, 15), "15m", "15:55", tz) is False
    assert is_flatten_bar(et(15, 45), "15Min", None, tz) is False


def test_is_flatten_bar_5m_uses_1550_close():
    tz = "America/New_York"
    assert is_flatten_bar(et(15, 45), "5m", "15:55", tz) is False
    assert is_flatten_bar(et(15, 50), "5m", "15:55", tz) is True
    assert is_flatten_bar(et(15, 55), "5m", "15:55", tz) is False


def test_wall_clock_at_or_after_flatten():
    tz = "America/New_York"
    assert wall_clock_at_or_after(et(15, 54), "15:55", tz) is False
    assert wall_clock_at_or_after(et(15, 55), "15:55", tz) is True
    assert wall_clock_at_or_after(et(16, 0), "15:55", tz) is True
