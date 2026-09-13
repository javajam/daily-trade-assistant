from dta_bot.indicators import ema, rsi, sma


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


def test_rsi_mixed():
    # Classic saw: up 1, down 0.5 repeating
    closes = [10.0]
    for _ in range(20):
        closes.append(closes[-1] + 1.0)
        closes.append(closes[-1] - 0.5)
    value = rsi(closes, 14)
    assert value is not None
    assert 50 < value < 80
