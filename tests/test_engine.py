from datetime import datetime, timedelta, timezone

from dta_bot.config import ActionSpec, MaCond, PatternCond, RsiCond, RuleSpec, SizeSpec, parse_condition
from dta_bot.engine import evaluate_all, evaluate_rule, fire_key
from dta_bot.models import Bar
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
