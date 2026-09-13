from pathlib import Path

import pytest

from dta_bot.config import MaCond, MaCrossCond, load_config, parse_condition
from dta_bot.patterns import PATTERN_NAMES


def test_example_config_loads():
    cfg = load_config("config/rules.example.yaml")
    assert cfg.settings.paper is True
    assert cfg.settings.allow_live is False
    assert cfg.settings.dry_run is True
    assert {r.id for r in cfg.rules} == {
        "engulfing-with-trend",
        "hammer-oversold",
        "evening-star-or-engulfing-exit",
    }
    pairs = cfg.all_symbol_timeframes()
    assert ("AAPL", "15Min") in pairs
    assert ("SPY", "1Hour") in pairs
    assert cfg.symbols_for(cfg.rules[2]) == ["AAPL", "MSFT", "SPY"]


def test_ema9_trend_config_loads():
    cfg = load_config("config/ema9_trend.example.yaml")
    assert cfg.settings.paper is True
    assert cfg.settings.allow_live is False
    assert cfg.settings.dry_run is True
    assert [r.id for r in cfg.rules] == ["ema9_trend", "ema9_cross_raw", "engulfing-with-trend"]
    assert all(r.cooldown_minutes == 60 for r in cfg.rules)
    assert all(r.action.size and r.action.size.value == 10 for r in cfg.rules)
    assert all(r.action.stop_loss_pct == 1.5 and r.action.take_profit_pct == 3.0 for r in cfg.rules)
    pairs = cfg.all_symbol_timeframes()
    assert pairs == {("AAPL", "15Min"), ("MSFT", "15Min")}


def test_ema_cross_yaml_parses_and_does_not_steal_level_ema():
    cross = parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}})
    assert isinstance(cross, MaCrossCond)
    assert cross.ma == "ema"
    assert cross.period == 9
    assert cross.direction == "bullish"
    level = parse_condition({"ema": {"period": 9, "timeframe": "15m", "compare": "below"}})
    assert isinstance(level, MaCond)
    assert level.compare == "below"
    bear = parse_condition({"sma_cross": {"period": 20, "timeframe": "1h", "compare": "below"}})
    assert isinstance(bear, MaCrossCond)
    assert bear.ma == "sma"
    assert bear.direction == "bearish"


def test_unknown_pattern_rejected(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        """
settings: {dry_run: true}
rules:
  - id: x
    when:
      pattern: not_a_real_pattern
      timeframe: 15m
    action:
      type: buy
      size: {type: shares, value: 1}
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        load_config(bad)


def test_duplicate_ids_rejected(tmp_path: Path):
    bad = tmp_path / "dup.yaml"
    bad.write_text(
        """
rules:
  - id: same
    when: {pattern: doji, timeframe: 1d}
    action: {type: close}
  - id: same
    when: {pattern: doji, timeframe: 1d}
    action: {type: close}
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate"):
        load_config(bad)


def test_pattern_names_cover_required_set():
    required = {
        "bullish_engulfing",
        "bearish_engulfing",
        "hammer",
        "inverted_hammer",
        "shooting_star",
        "doji",
        "morning_star",
        "evening_star",
        "three_white_soldiers",
        "three_black_crows",
    }
    assert required <= set(PATTERN_NAMES)
