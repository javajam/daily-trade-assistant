"""Synthetic OHLC fixtures for every built-in candlestick detector."""

from dta_bot.patterns import (
    detect,
    detect_bearish_engulfing,
    detect_bullish_engulfing,
    detect_doji,
    detect_evening_star,
    detect_hammer,
    detect_inverted_hammer,
    detect_morning_star,
    detect_shooting_star,
    detect_three_black_crows,
    detect_three_white_soldiers,
)
from tests.conftest import bar


def test_doji_match_and_miss():
    assert detect_doji([bar(0, 10, 10.5, 9.5, 10.02)]).matched
    assert not detect_doji([bar(0, 10, 11, 9, 10.8)]).matched


def test_doji_zero_range():
    assert not detect_doji([bar(0, 10, 10, 10, 10)]).matched


def test_bullish_engulfing():
    prev = bar(0, 10.0, 10.2, 8.0, 8.2)
    curr = bar(1, 8.1, 11.0, 8.0, 10.4)
    hit = detect_bullish_engulfing([prev, curr])
    assert hit.matched
    assert "bullish_engulfing matched" in hit.reason
    assert "2026-09-11" in hit.reason


def test_bullish_engulfing_rejects_same_color():
    a = bar(0, 8.0, 10.2, 8.0, 10.0)
    b = bar(1, 8.1, 11.0, 8.0, 10.4)
    assert not detect_bullish_engulfing([a, b]).matched


def test_bearish_engulfing():
    prev = bar(0, 8.0, 10.2, 7.9, 10.0)
    curr = bar(1, 10.1, 10.3, 7.5, 7.8)
    assert detect_bearish_engulfing([prev, curr]).matched
    assert not detect_bearish_engulfing([curr, prev]).matched


def test_hammer():
    # Long lower wick, small upper wick, body near the high
    h = bar(0, 10.0, 10.2, 8.0, 10.1)
    assert detect_hammer([h]).matched
    # Long upper wick is not a hammer
    inv = bar(0, 10.0, 12.0, 9.9, 10.1)
    assert not detect_hammer([inv]).matched


def test_inverted_hammer():
    inv = bar(0, 10.0, 12.2, 9.95, 10.15)
    assert detect_inverted_hammer([inv]).matched
    assert not detect_inverted_hammer([bar(0, 10.0, 10.2, 8.0, 10.1)]).matched


def test_shooting_star():
    prior = bar(0, 10.0, 11.0, 9.9, 10.9)
    star = bar(1, 10.95, 13.2, 10.85, 11.05)
    hit = detect_shooting_star([prior, star])
    assert hit.matched
    assert not detect_shooting_star([star]).matched  # needs 2 bars


def test_morning_star():
    a = bar(0, 12.0, 12.1, 10.0, 10.1)  # long bear
    b = bar(1, 9.9, 10.2, 9.6, 10.0)  # small star
    c = bar(2, 10.1, 11.8, 10.0, 11.6)  # bull into first body
    hit = detect_morning_star([a, b, c])
    assert hit.matched
    assert not detect_morning_star([c, b, a]).matched


def test_evening_star():
    a = bar(0, 10.0, 12.0, 9.9, 11.9)
    b = bar(1, 12.1, 12.4, 11.9, 12.2)
    c = bar(2, 12.0, 12.1, 10.2, 10.4)
    assert detect_evening_star([a, b, c]).matched
    assert not detect_evening_star([c, b, a]).matched


def test_three_white_soldiers():
    a = bar(0, 10.0, 11.2, 9.9, 11.1)
    b = bar(1, 11.05, 12.2, 10.95, 12.1)
    c = bar(2, 12.05, 13.2, 11.95, 13.1)
    assert detect_three_white_soldiers([a, b, c]).matched
    # Not rising closes
    assert not detect_three_white_soldiers([c, b, a]).matched


def test_three_black_crows():
    a = bar(0, 13.0, 13.1, 11.8, 11.9)
    b = bar(1, 11.95, 12.05, 10.8, 10.9)
    c = bar(2, 10.95, 11.05, 9.8, 9.9)
    assert detect_three_black_crows([a, b, c]).matched
    assert not detect_three_black_crows([c, b, a]).matched


def test_detect_dispatch_and_unknown():
    assert detect("bullish-engulfing", [bar(0, 10, 10.2, 8, 8.2), bar(1, 8.1, 11, 8, 10.4)]).matched
    miss = detect("head_and_shoulders", [bar(0, 1, 2, 0.5, 1.5)])
    assert not miss.matched
    assert "unknown pattern" in miss.reason


def test_need_enough_bars():
    assert not detect_morning_star([bar(0, 1, 2, 0.5, 0.8)]).matched
    assert "need 3" in detect_morning_star([bar(0, 1, 2, 0.5, 0.8)]).reason
