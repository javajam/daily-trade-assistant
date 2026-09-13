from pathlib import Path

import pytest

from dta_bot.cli import main
from dta_bot.config import (
    MaCond,
    MaCrossCond,
    condition_timeframes,
    load_config,
    parse_condition,
    restrict_universe,
    with_timeframe,
)
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
    by_id = {r.id: r for r in cfg.rules}
    assert by_id["ema9_trend"].action.exit == "ema_invalid"
    assert by_id["ema9_cross_raw"].action.exit == "ema_invalid"
    assert by_id["ema9_trend"].action.stop_loss_pct is None
    assert by_id["ema9_trend"].action.take_profit_pct is None
    assert by_id["engulfing-with-trend"].action.exit == "fixed_bracket"
    assert by_id["engulfing-with-trend"].action.stop_loss_pct == 1.5
    assert by_id["engulfing-with-trend"].action.take_profit_pct == 3.0
    pairs = cfg.all_symbol_timeframes()
    assert pairs == {("AAPL", "15Min"), ("MSFT", "15Min"), ("SOXL", "15Min")}
    assert cfg.settings.timeframe == "15Min"
    assert cfg.universe == ["AAPL", "MSFT", "SOXL"]


def test_ema9_trend_5m_config_loads():
    cfg = load_config("config/ema9_trend_5m.example.yaml")
    assert [r.id for r in cfg.rules] == ["ema9_trend", "ema9_cross_raw", "engulfing-with-trend"]
    assert all(r.cooldown_minutes == 60 for r in cfg.rules)
    assert cfg.rules[0].action.exit == "ema_invalid"
    assert cfg.rules[2].action.exit == "fixed_bracket"
    assert cfg.settings.timeframe == "5Min"
    assert cfg.all_symbol_timeframes() == {("AAPL", "5Min"), ("MSFT", "5Min"), ("SOXL", "5Min")}
    for rule in cfg.rules:
        assert condition_timeframes(rule.when) == {"5Min"}


def test_with_timeframe_rewrites_ema9_conditions_and_keeps_cooldown():
    cfg = load_config("config/ema9_trend.example.yaml")
    five = with_timeframe(cfg, "5m")
    assert five.settings.timeframe == "5Min"
    assert five.all_symbol_timeframes() == {("AAPL", "5Min"), ("MSFT", "5Min"), ("SOXL", "5Min")}
    assert [r.cooldown_minutes for r in five.rules] == [60, 60, 60]
    assert [r.id for r in five.rules] == [r.id for r in cfg.rules]
    loaded_5m = load_config("config/ema9_trend.example.yaml", timeframe="5m")
    assert loaded_5m.all_symbol_timeframes() == five.all_symbol_timeframes()


def test_restrict_universe_keeps_soxl_only():
    cfg = load_config("config/ema9_trend.example.yaml")
    soxl = restrict_universe(cfg, ["SOXL"])
    assert soxl.universe == ["SOXL"]
    assert soxl.all_symbol_timeframes() == {("SOXL", "15Min")}
    assert all(r.symbols == ["SOXL"] for r in soxl.rules)


def test_exit_alias_and_unknown_rejected(tmp_path: Path):
    path = tmp_path / "exit.yaml"
    path.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action: {type: buy, size: {type: shares, value: 1}, exit: hold_ema}
""",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.rules[0].action.exit == "ema_invalid"
    bad = tmp_path / "bad_exit.yaml"
    bad.write_text(
        """
rules:
  - id: x
    when: {pattern: doji, timeframe: 1d}
    action: {type: close, exit: trail}
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        load_config(bad)


def test_parse_condition_inherits_default_timeframe():
    cond = parse_condition({"ema_cross": {"period": 9, "direction": "bullish"}}, default_timeframe="5m")
    assert isinstance(cond, MaCrossCond)
    assert cond.timeframe == "5Min"


def test_cli_validate_timeframe_override(capsys):
    rc = main(["validate", "--config", "config/ema9_trend.example.yaml", "--timeframe", "5m"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "tf=5Min" in out
    assert "cooldown=60m" in out
    assert "exit=ema_invalid" in out


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
