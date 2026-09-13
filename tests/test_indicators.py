from dta_bot.indicators import ema, last_two_ma, ma_cross, rsi, sma


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


def test_rsi_mixed():
    # Classic saw: up 1, down 0.5 repeating
    closes = [10.0]
    for _ in range(20):
        closes.append(closes[-1] + 1.0)
        closes.append(closes[-1] - 0.5)
    value = rsi(closes, 14)
    assert value is not None
    assert 50 < value < 80
