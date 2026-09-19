"""SMA, EMA, RSI, and volume helpers on oldest-first close/volume series."""

from __future__ import annotations

from typing import Optional, Sequence


def sma(values: Sequence[float], period: int) -> Optional[float]:
    if period <= 0 or len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / period


def sma_through(closes: Sequence[float], period: int) -> Optional[float]:
    """SMA of the last ``period`` closes (oldest-first series through the signal bar)."""
    return sma(closes, period)


def ema(values: Sequence[float], period: int) -> Optional[float]:
    if period <= 0 or len(values) < period:
        return None
    k = 2.0 / (period + 1)
    seed = sum(values[:period]) / period
    val = seed
    for price in values[period:]:
        val = price * k + val * (1.0 - k)
    return val


def rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    """Wilder RSI. Needs period+1 closes."""
    if period <= 0 or len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def average_volume(volumes: Sequence[float], period: int) -> Optional[float]:
    return sma(volumes, period)


def last_two_ma(
    values: Sequence[float],
    period: int,
    kind: str = "ema",
) -> Optional[tuple[float, float, float, float]]:
    """Return (prev_close, prev_ma, curr_close, curr_ma) or None if too short.

    Previous MA is computed on ``values[:-1]`` so a cross compares each close
    to the MA as of that bar, not to a single current-bar MA.
    Needs ``period + 1`` values.
    """
    if period <= 0 or len(values) < period + 1:
        return None
    fn = sma if kind == "sma" else ema
    prev_ma = fn(values[:-1], period)
    curr_ma = fn(values, period)
    if prev_ma is None or curr_ma is None:
        return None
    return values[-2], prev_ma, values[-1], curr_ma


def ma_cross(
    values: Sequence[float],
    period: int,
    *,
    kind: str = "ema",
    direction: str = "bullish",
) -> Optional[bool]:
    """Bullish: prev close <= prev MA and curr close > curr MA. Bearish is the inverse."""
    pair = last_two_ma(values, period, kind)
    if pair is None:
        return None
    prev_close, prev_ma, curr_close, curr_ma = pair
    if direction == "bearish":
        return prev_close >= prev_ma and curr_close < curr_ma
    return prev_close <= prev_ma and curr_close > curr_ma


def last_two_ma_pair(
    values: Sequence[float],
    ema_period: int,
    sma_period: int,
) -> Optional[tuple[float, float, float, float]]:
    """Return (prev_ema, prev_sma, curr_ema, curr_sma) or None if too short.

    Previous values use ``values[:-1]`` so a cross compares each MA pair as of
    that bar. Needs ``max(ema_period, sma_period) + 1`` values.
    """
    need = max(ema_period, sma_period) + 1
    if ema_period <= 0 or sma_period <= 0 or len(values) < need:
        return None
    prev_ema = ema(values[:-1], ema_period)
    prev_sma = sma(values[:-1], sma_period)
    curr_ema = ema(values, ema_period)
    curr_sma = sma(values, sma_period)
    if prev_ema is None or prev_sma is None or curr_ema is None or curr_sma is None:
        return None
    return prev_ema, prev_sma, curr_ema, curr_sma


def ma_pair_cross(
    values: Sequence[float],
    ema_period: int = 9,
    sma_period: int = 20,
    *,
    direction: str = "bullish",
) -> Optional[bool]:
    """Bullish: prev EMA <= prev SMA and curr EMA > curr SMA. Bearish is the inverse."""
    pair = last_two_ma_pair(values, ema_period, sma_period)
    if pair is None:
        return None
    prev_ema, prev_sma, curr_ema, curr_sma = pair
    if direction == "bearish":
        return prev_ema >= prev_sma and curr_ema < curr_sma
    return prev_ema <= prev_sma and curr_ema > curr_sma


def ma_slope(
    values: Sequence[float],
    period: int,
    *,
    kind: str = "sma",
    compare: str = "flat_or_rising",
) -> Optional[bool]:
    """Signal-bar MA vs previous-bar MA. Needs ``period + 1`` values.

    ``flat_or_rising`` is curr MA >= prev MA (the noon pair-cross slope gate).
    """
    pair = last_two_ma(values, period, kind)
    if pair is None:
        return None
    _, prev_ma, _, curr_ma = pair
    if compare in {"rising", "gt", "up"}:
        return curr_ma > prev_ma
    if compare in {"falling", "lt", "down"}:
        return curr_ma < prev_ma
    if compare in {"flat_or_falling", "falling_or_flat", "le", "not_rising"}:
        return curr_ma <= prev_ma
    if compare in {"flat", "eq"}:
        return curr_ma == prev_ma
    return curr_ma >= prev_ma
