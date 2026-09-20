from datetime import datetime, timedelta, timezone

from dta_bot.config import ActionSpec, MaCond, PatternCond, RsiCond, RuleSpec, SizeSpec, parse_condition
from dta_bot.engine import (
    evaluate_all,
    evaluate_rule,
    fire_key,
    range_expansion_exit,
    range_expansion_flatten_bar,
)
from dta_bot.models import Bar, Position
from dta_bot.state import BotState
from tests.conftest import bar


def _rule(**kwargs) -> RuleSpec:
    defaults = dict(
        id="r1",
        when=PatternCond(name="bullish_engulfing", timeframe="15m"),
        action=ActionSpec(type="buy", size=SizeSpec(type="shares", value=1)),
        symbols=["AAPL"],
        cooldown_minutes=60,
    )
    defaults.update(kwargs)
    return RuleSpec(**defaults)


def _engulfing_bars() -> list[Bar]:
    return [bar(0, 10.0, 10.2, 8.0, 8.2), bar(1, 8.1, 11.0, 8.0, 10.4)]


def test_pattern_and_ma_all_match():
    # Build 20 rising closes then engulfing so SMA20 < last close
    bars = [bar(i, 10 + i * 0.1, 10.2 + i * 0.1, 9.9 + i * 0.1, 10.1 + i * 0.1) for i in range(20)]
    # overwrite last two with engulfing that still finishes above the SMA
    bars[-2] = Bar(bars[-2].timestamp, 12.0, 12.1, 11.4, 11.5, 1000)
    bars[-1] = Bar(bars[-1].timestamp, 11.45, 13.0, 11.4, 12.8, 2000)
    cond = parse_condition(
        {
            "all": [
                {"pattern": "bullish_engulfing", "timeframe": "15m"},
                {"sma": {"period": 20, "timeframe": "15m", "compare": "above"}},
            ]
        }
    )
    rule = _rule(when=cond)
    ev = evaluate_rule(rule, "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert "bullish_engulfing matched" in ev.reasons[0]
    assert "SMA20" in ev.reasons[0]


def test_or_fires_when_one_side_hits():
    cond = parse_condition(
        {
            "any": [
                {"pattern": "evening_star", "timeframe": "15m"},
                {"pattern": "bearish_engulfing", "timeframe": "15m"},
            ]
        }
    )
    bars = [bar(0, 8.0, 10.2, 7.9, 10.0), bar(1, 10.1, 10.3, 7.5, 7.8)]
    ev = evaluate_rule(_rule(when=cond, action=ActionSpec(type="close")), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert ev.action_type == "close"
    assert "bearish_engulfing matched" in ev.reasons[0]


def test_and_fails_when_rsi_too_high():
    # Strong trend → RSI ~100, so below 30 fails
    bars = [bar(i, 10 + i, 10.5 + i, 9.9 + i, 10.4 + i) for i in range(20)]
    cond = parse_condition(
        {
            "all": [
                {"rsi": {"period": 14, "timeframe": "15m", "below": 30}},
            ]
        }
    )
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert not ev.matched
    assert "RSI14" in ev.reasons[0]


def test_cooldown_skips_even_if_pattern_matches():
    bars = _engulfing_bars()
    state = BotState()
    now = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)
    state.mark_fired("x", "r1:AAPL", 60, when=now - timedelta(minutes=10))
    ev = evaluate_rule(_rule(), "AAPL", {("AAPL", "15Min"): bars}, state, now=now)
    assert ev.skipped == "cooldown"
    assert not ev.matched


def test_idempotent_same_bar_does_not_refire():
    bars = _engulfing_bars()
    state = BotState()
    first = evaluate_rule(_rule(), "AAPL", {("AAPL", "15Min"): bars}, state)
    assert first.matched
    state.mark_fired(fire_key("r1", "AAPL", first.signal_bar_ts), "r1:AAPL", 0)
    second = evaluate_rule(_rule(), "AAPL", {("AAPL", "15Min"): bars}, state)
    assert second.skipped == "already_fired"
    assert not second.matched


def test_volume_filter():
    bars = [bar(i, 10, 10.2, 9.8, 10.1, v=1000) for i in range(20)]
    bars.append(bar(20, 8.2, 11, 8, 10.5, v=5000))  # not used as pattern
    # volume condition vs prior 20-bar avg of 1000
    cond = parse_condition({"volume": {"period": 20, "timeframe": "15m", "multiplier": 2.0}})
    # last bar volume 5000 > 2*1000
    series = bars[:20] + [bar(20, 10, 10.2, 9.8, 10.1, v=5000)]
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): series}, BotState())
    assert ev.matched


def test_volume_gt_prev_filter():
    low = [bar(i, 10, 10.2, 9.8, 10.1, v=1000) for i in range(2)]
    high = [bar(0, 10, 10.2, 9.8, 10.1, v=1000), bar(1, 10, 10.2, 9.8, 10.1, v=1500)]
    cond = parse_condition({"volume_gt_prev": {"timeframe": "15m"}})
    miss = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): low}, BotState())
    hit = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): high}, BotState())
    assert not miss.matched
    assert hit.matched
    vs_prev = parse_condition({"volume": {"vs": "prev", "timeframe": "15m"}})
    again = evaluate_rule(_rule(when=vs_prev), "AAPL", {("AAPL", "15Min"): high}, BotState())
    assert again.matched


def test_evaluate_all_covers_universe_and_disabled():
    from dta_bot.config import BotConfig, Settings

    enabled = _rule(id="on", symbols=["AAPL"])
    disabled = _rule(id="off", enabled=False, symbols=["AAPL"])
    cfg = BotConfig(settings=Settings(), universe=["AAPL"], rules=[enabled, disabled])
    bars = {("AAPL", "15Min"): _engulfing_bars()}
    results = evaluate_all(cfg, bars, BotState())
    assert [r.rule_id for r in results] == ["on", "off"]
    assert results[0].matched
    assert results[1].skipped == "disabled"


def test_rsi_condition_direct():
    # Falling prices → low RSI
    bars = [bar(i, 50 - i * 0.4, 50.1 - i * 0.4, 49.6 - i * 0.4, 49.7 - i * 0.4) for i in range(20)]
    cond = RsiCond(period=14, timeframe="15m", below=40)
    ev = evaluate_rule(_rule(when=cond), "SPY", {("SPY", "15Min"): bars}, BotState())
    assert ev.matched


def test_ma_below():
    bars = [bar(i, 20 - i * 0.2, 20.1 - i * 0.2, 19.8 - i * 0.2, 19.9 - i * 0.2) for i in range(20)]
    cond = MaCond(ma="sma", period=20, timeframe="15m", compare="below")
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched


def _flat_then(last_close: float, n: int = 11) -> list:
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(n - 1)]
    bars.append(bar(n - 1, 10.0, max(10.1, last_close), min(9.9, last_close), last_close))
    return bars


def test_ema_cross_bullish_fires():
    bars = _flat_then(12.0)
    cond = parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}})
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert "ema_cross matched (bullish)" in ev.reasons[0]


def test_ema_cross_rejects_when_already_above():
    # Rising closes stay above the lagging EMA — no fresh cross on the last bar.
    bars = [bar(i, 10 + i * 0.5, 10.2 + i * 0.5, 9.9 + i * 0.5, 10.1 + i * 0.5) for i in range(16)]
    cond = parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}})
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert not ev.matched
    assert "ema_cross not found (bullish)" in ev.reasons[0]


def _flat_pair(n: int = 20, last_close: float = 12.0) -> list:
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(n)]
    bars.append(bar(n, 10.0, max(10.1, last_close), min(9.9, last_close), last_close))
    return bars


def test_ema_sma_cross_bullish_fires():
    bars = _flat_pair()
    cond = parse_condition(
        {"ema_sma_cross": {"ema_period": 9, "sma_period": 20, "timeframe": "15m", "direction": "bullish"}}
    )
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert "ema_sma_cross matched (bullish)" in ev.reasons[0]


def test_ema_sma_cross_rejects_when_already_above():
    # Rising closes keep EMA9 above SMA20 — no fresh cross on the last bar.
    bars = [bar(i, 10 + i * 0.5, 10.2 + i * 0.5, 9.9 + i * 0.5, 10.1 + i * 0.5) for i in range(25)]
    cond = parse_condition(
        {"ema_sma_cross": {"ema_period": 9, "sma_period": 20, "timeframe": "15m", "direction": "bullish"}}
    )
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert not ev.matched
    assert "ema_sma_cross not found (bullish)" in ev.reasons[0]


def test_ema_sma_cross_bearish_fires():
    bars = _flat_pair()
    bars.append(bar(21, 12.0, 12.1, 7.9, 8.0))
    cond = parse_condition(
        {"ema_sma_cross": {"ema_period": 9, "sma_period": 20, "timeframe": "15m", "direction": "under"}}
    )
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert "ema_sma_cross matched (bearish)" in ev.reasons[0]


def test_ema_sma_cross_rsi_sibling_rejects_when_rsi_is_100():
    # Flat-then-up pair-cross has no down closes → Wilder RSI is 100.
    bars = _flat_pair()
    cond = parse_condition(
        {
            "ema_sma_cross": {
                "ema_period": 9,
                "sma_period": 20,
                "timeframe": "15m",
                "direction": "bullish",
            },
            "rsi": {"period": 14, "below": 70},
        }
    )
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert not ev.matched
    assert "ema_sma_cross matched (bullish)" in ev.reasons[0]
    assert "RSI14" in ev.reasons[0]
    assert "< 70" in ev.reasons[0]


def test_ema_sma_cross_rsi_sibling_allows_when_below_70():
    # Decline, flatten, then bounce: RSI stays mid/low while EMA9 crosses SMA20.
    closes: list[float] = [20.0 - i * 0.3 for i in range(14)]
    closes += [closes[-1]] * 10
    closes.append(closes[-1] + 3.0)
    bars = [
        bar(i, c - 0.05, max(c - 0.05, c) + 0.05, min(c - 0.05, c) - 0.05, c)
        for i, c in enumerate(closes)
    ]
    cond = parse_condition(
        {
            "ema_sma_cross": {
                "ema_period": 9,
                "sma_period": 20,
                "timeframe": "15m",
                "direction": "bullish",
            },
            "rsi": {"period": 14, "below": 70},
        }
    )
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert "ema_sma_cross matched (bullish)" in ev.reasons[0]
    assert "RSI14" in ev.reasons[0]
    assert "< 70.0 → True" in ev.reasons[0]


def test_ema_cross_and_trend_filter():
    # Gentle saw keeps RSI mid-range; last two bars dip under EMA9 then cross back.
    closes: list[float] = []
    price = 10.0
    for i in range(30):
        price = price + (0.08 if i % 2 == 0 else -0.06)
        closes.append(round(price, 4))
    closes[-2] = round(closes[-3] - 0.15, 4)
    closes[-1] = round(closes[-2] + 0.25, 4)
    bars = [
        bar(i, c - 0.02, max(c - 0.02, c) + 0.02, min(c - 0.02, c) - 0.02, c)
        for i, c in enumerate(closes)
    ]
    cond = parse_condition(
        {
            "all": [
                {"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}},
                {"sma": {"period": 20, "timeframe": "15m", "compare": "above"}},
                {"rsi": {"period": 14, "timeframe": "15m", "below": 70}},
            ]
        }
    )
    ev = evaluate_rule(_rule(when=cond), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert "ema_cross matched" in ev.reasons[0]
    assert "SMA20" in ev.reasons[0]
    assert "RSI14" in ev.reasons[0]


def test_noon_short_stack_fires_without_rsi_even_when_oversold():
    # Flats seed EMA/SMA at 10; last print 8 is a bearish price-cross below SMA20.
    # One drop after flats drives Wilder RSI near 0, so RSI > 30 would block.
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(20)]
    bars.append(bar(20, 10.0, 10.1, 7.9, 8.0))
    cond = parse_condition(
        {
            "all": [
                {"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bearish"}},
                {"sma": {"period": 20, "timeframe": "15m", "compare": "below"}},
            ]
        }
    )
    ev = evaluate_rule(
        _rule(when=cond, action=ActionSpec(type="sell", size=SizeSpec(type="shares", value=10))),
        "AAPL",
        {("AAPL", "15Min"): bars},
        BotState(),
    )
    assert ev.matched
    assert "ema_cross matched (bearish)" in ev.reasons[0]
    assert "SMA20" in ev.reasons[0]
    assert "RSI14" not in ev.reasons[0]

    blocked = parse_condition(
        {
            "all": [
                {"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bearish"}},
                {"sma": {"period": 20, "timeframe": "15m", "compare": "below"}},
                {"rsi": {"period": 14, "timeframe": "15m", "above": 30}},
            ]
        }
    )
    blocked_ev = evaluate_rule(
        _rule(when=blocked, action=ActionSpec(type="sell", size=SizeSpec(type="shares", value=10))),
        "AAPL",
        {("AAPL", "15Min"): bars},
        BotState(),
    )
    assert not blocked_ev.matched
    assert "RSI14" in blocked_ev.reasons[0]


def test_range_expansion_exit_strict_gt():
    prior = [
        bar(0, 10.0, 10.2, 9.8, 10.0),
        bar(1, 10.0, 10.3, 9.9, 10.1),
        bar(2, 10.1, 10.4, 10.0, 10.2),
    ]
    # max prior range = 0.4
    wide = bar(3, 10.2, 10.9, 10.0, 10.5)
    equal = bar(3, 10.2, 10.6, 10.2, 10.4)
    assert range_expansion_exit(wide, prior) is True
    assert range_expansion_exit(equal, prior) is False
    assert range_expansion_exit(wide, []) is False


def test_range_expansion_skip_doji():
    prior = [
        bar(0, 10.0, 10.2, 9.8, 10.0),
        bar(1, 10.0, 10.3, 9.9, 10.1),
        bar(2, 10.1, 10.4, 10.0, 10.2),
    ]
    # Range 3.0 > 0.4, but body/range = 0.1/3.0 < 0.10
    doji = bar(3, 12.1, 14.0, 11.0, 12.2)
    body = bar(3, 12.1, 14.0, 11.0, 13.5)
    assert range_expansion_exit(doji, prior) is True
    assert range_expansion_exit(doji, prior, skip_doji=True) is False
    assert range_expansion_exit(body, prior, skip_doji=True) is True


def test_range_expansion_flatten_skips_entry_bar():
    bars = [
        bar(0, 10.0, 10.2, 9.8, 10.0),
        bar(1, 10.0, 10.2, 9.8, 10.1),
        bar(2, 10.1, 12.0, 9.0, 11.0),  # entry: huge range
    ]
    pos = Position(symbol="AAPL", qty=10, side="long", avg_entry_price=10.1, market_value=110.0)
    assert range_expansion_flatten_bar(pos, bars, after=bars[0].timestamp, lookback=3) is None
    after_entry = bars + [bar(3, 11.0, 11.2, 10.9, 11.1)]
    assert range_expansion_flatten_bar(pos, after_entry, after=bars[0].timestamp, lookback=3) is None
    wide = bars + [
        bar(3, 11.0, 11.1, 10.95, 11.0),
        bar(4, 11.0, 14.0, 10.0, 12.0),
    ]
    hit = range_expansion_flatten_bar(pos, wide, after=bars[0].timestamp, lookback=3)
    assert hit is not None
    assert hit.timestamp == wide[-1].timestamp
