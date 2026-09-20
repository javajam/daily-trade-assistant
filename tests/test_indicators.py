import pytest

from dta_bot.indicators import atr, ema, last_two_ma, last_two_ma_pair, ma_cross, ma_pair_cross, rsi, sma, true_range


def test_sma():
    assert sma([1, 2, 3, 4], 3) == 3.0
    assert sma([1, 2], 3) is None


def test_ema_seeds_from_sma_then_updates():
    values = [1, 2, 3, 4, 5]
    # period 3: seed = 2.0, then 4 → 3.0, then 5 → 4.0
    assert ema(values, 3) == 4.0
    assert ema([1, 2], 3) is None


def test_rsi_all_up_is_100():
    closes = [float(i) for i in range(1, 20)]
    assert rsi(closes, 14) == 100.0


def test_last_two_ma_and_bullish_cross():
    # Flat 10s seed EMA9 at 10; last print 12 crosses above the updating EMA.
    values = [10.0] * 10 + [12.0]
    pair = last_two_ma(values, 9, "ema")
    assert pair is not None
    prev_close, prev_ma, curr_close, curr_ma = pair
    assert prev_close == 10.0
    assert prev_ma == 10.0
    assert curr_close == 12.0
    assert curr_ma == 10.4  # k=0.2 → 12*0.2 + 10*0.8
    assert ma_cross(values, 9, kind="ema", direction="bullish") is True
    assert ma_cross(values, 9, kind="ema", direction="bearish") is False
    assert ma_cross([10.0] * 9, 9, kind="ema") is None


def test_ema9_sma20_pair_cross_up_and_down():
    # 20 flats seed both MAs at 10; 12.0 lifts EMA9 over SMA20.
    up = [10.0] * 20 + [12.0]
    pair = last_two_ma_pair(up, 9, 20)
    assert pair is not None
    prev_ema, prev_sma, curr_ema, curr_sma = pair
    assert prev_ema == 10.0
    assert prev_sma == 10.0
    assert curr_ema == 10.4
    assert curr_sma == 10.1
    assert ma_pair_cross(up, 9, 20, direction="bullish") is True
    assert ma_pair_cross(up, 9, 20, direction="bearish") is False
    # Next print 8.0 drops EMA9 back under SMA20.
    down = up + [8.0]
    assert ma_pair_cross(down, 9, 20, direction="bearish") is True
    assert ma_pair_cross(down, 9, 20, direction="bullish") is False
    assert last_two_ma_pair([10.0] * 20, 9, 20) is None


def test_rsi_mixed():
    # Classic saw: up 1, down 0.5 repeating
    closes = [10.0]
    for _ in range(20):
        closes.append(closes[-1] + 1.0)
        closes.append(closes[-1] - 0.5)
    value = rsi(closes, 14)
    assert value is not None
    assert 50 < value < 80


def test_true_range_uses_gap():
    assert true_range(11.0, 10.0, 10.5) == 1.0
    # Gap up: prev close 10, high 12, low 11 → TR = max(1, 2, 1) = 2
    assert true_range(12.0, 11.0, 10.0) == 2.0


def test_wilder_atr_seeds_from_sma_then_smooths():
    # 15 identical TR=1 bars (16 prints: first close seeds TR). ATR(14) = 1.0
    highs = [11.0] * 16
    lows = [10.0] * 16
    closes = [10.5] * 16
    assert atr(highs, lows, closes, 14) == 1.0
    assert atr(highs[:14], lows[:14], closes[:14], 14) is None
    # Next TR = 2.0 → ATR = (1*13 + 2) / 14
    highs2 = highs + [12.0]
    lows2 = lows + [10.0]
    closes2 = closes + [11.0]
    assert atr(highs2, lows2, closes2, 14) == pytest.approx(15.0 / 14.0)

