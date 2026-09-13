from pathlib import Path

import pytest

from dta_bot.cli import main
from dta_bot.config import (
    GroupCond,
    MaCond,
    MaCrossCond,
    MaPairCrossCond,
    RsiCond,
    condition_timeframes,
    find_rsi_condition,
    load_config,
    parse_condition,
    restrict_universe,
    rsi_filter_label,
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
    assert [r.id for r in cfg.rules] == ["ema9_trend"]
    rule = cfg.rules[0]
    assert rule.cooldown_minutes == 60
    assert rule.action.size and rule.action.size.value == 10
    assert isinstance(rule.when, MaPairCrossCond)
    assert rule.when.ema_period == 9
    assert rule.when.sma_period == 20
    assert rule.when.direction == "bullish"
    assert rule.action.exit == "ma_cross"
    assert rule.action.exit_ema_period == 9
    assert rule.action.exit_sma_period == 20
    assert rule.action.stop_loss_pct == 1.5
    assert rule.action.take_profit_pct is None
    assert rule.action.breakeven_after_bars == 0
    pairs = cfg.all_symbol_timeframes()
    assert pairs == {("AAPL", "15Min"), ("MSFT", "15Min")}
    assert cfg.settings.timeframe == "15Min"
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.settings.session_timezone == "America/New_York"
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"


def test_ema9_trend_risk_config_loads():
    cfg = load_config("config/ema9_trend_risk.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert [r.id for r in cfg.rules] == ["ema9_trend"]
    rule = cfg.rules[0]
    assert rule.action.exit == "ma_cross"
    assert rule.action.stop_loss_pct == 1.5
    assert rule.action.take_profit_pct is None
    assert rule.action.size is not None
    assert rule.action.size.type == "risk_pct"
    assert rule.action.size.equity_risk == 0.01
    assert rule.action.size.stop_pct == 1.5
    assert rule.action.breakeven_after_bars == 0
    assert isinstance(rule.when, MaPairCrossCond)
    assert rule.when.ema_period == 9
    assert rule.when.sma_period == 20
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"
    assert cfg.all_symbol_timeframes() == {("AAPL", "15Min"), ("MSFT", "15Min")}


def test_ema9_trend_bracket_config_keeps_ten_shares():
    cfg = load_config("config/ema9_trend_bracket.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.type == "shares"
    assert cfg.rules[0].action.size.value == 10
    assert cfg.rules[0].action.exit == "ma_cross"
    assert cfg.rules[0].action.stop_loss_pct == 1.5
    assert cfg.rules[0].action.take_profit_pct is None
    assert cfg.rules[0].action.breakeven_after_bars == 0
    assert cfg.rules[0].action.exit_ema_period == 9
    assert cfg.rules[0].action.exit_sma_period == 20
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"


def test_ema9_trend_bracket_1300_keeps_prior_cutoff():
    cfg = load_config("config/ema9_trend_bracket_1300.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.value == 10
    assert cfg.rules[0].action.exit == "ma_cross"
    assert cfg.settings.entry_cutoff == "13:00"
    assert cfg.settings.flatten_by == "15:55"


def test_ema9_trend_bracket_1515_keeps_prior_cutoff():
    cfg = load_config("config/ema9_trend_bracket_1515.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.value == 10
    assert cfg.rules[0].action.exit == "ma_cross"
    assert cfg.settings.entry_cutoff == "15:15"
    assert cfg.settings.flatten_by == "15:55"


def test_ema9_trend_bracket_soxl_includes_soxl():
    cfg = load_config("config/ema9_trend_bracket_soxl.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT", "SOXL"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.value == 10
    assert cfg.rules[0].action.exit == "ma_cross"
    assert cfg.rules[0].action.breakeven_after_bars == 0
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"
    assert cfg.all_symbol_timeframes() == {("AAPL", "15Min"), ("MSFT", "15Min"), ("SOXL", "15Min")}


def test_ema9_trend_risk_soxl_includes_soxl():
    cfg = load_config("config/ema9_trend_risk_soxl.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT", "SOXL"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.type == "risk_pct"
    assert cfg.rules[0].action.size.equity_risk == 0.01
    assert cfg.rules[0].action.exit == "ma_cross"
    assert cfg.rules[0].action.breakeven_after_bars == 0
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"


def test_ema9_trend_overnight_config_disables_session_gates():
    cfg = load_config("config/ema9_trend_bracket_overnight.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.value == 10
    assert cfg.settings.entry_cutoff is None
    assert cfg.settings.flatten_by is None
    assert cfg.settings.session_timezone == "America/New_York"


def test_ema9_trend_5m_config_loads():
    cfg = load_config("config/ema9_trend_5m.example.yaml")
    assert [r.id for r in cfg.rules] == ["ema9_trend"]
    assert cfg.rules[0].cooldown_minutes == 60
    assert cfg.rules[0].action.exit == "ma_cross"
    assert cfg.rules[0].action.stop_loss_pct == 1.5
    assert cfg.rules[0].action.take_profit_pct is None
    assert cfg.settings.timeframe == "5Min"
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"
    assert cfg.all_symbol_timeframes() == {("AAPL", "5Min"), ("MSFT", "5Min")}
    for rule in cfg.rules:
        assert condition_timeframes(rule.when) == {"5Min"}


def test_with_timeframe_rewrites_ema9_conditions_and_keeps_cooldown():
    cfg = load_config("config/ema9_trend.example.yaml")
    five = with_timeframe(cfg, "5m")
    assert five.settings.timeframe == "5Min"
    assert five.settings.entry_cutoff == cfg.settings.entry_cutoff
    assert five.settings.flatten_by == cfg.settings.flatten_by
    assert five.all_symbol_timeframes() == {("AAPL", "5Min"), ("MSFT", "5Min")}
    assert [r.cooldown_minutes for r in five.rules] == [60]
    assert [r.id for r in five.rules] == [r.id for r in cfg.rules]
    assert isinstance(five.rules[0].when, MaPairCrossCond)
    loaded_5m = load_config("config/ema9_trend.example.yaml", timeframe="5m")
    assert loaded_5m.all_symbol_timeframes() == five.all_symbol_timeframes()


def test_restrict_universe_keeps_soxl_only():
    cfg = load_config("config/ema9_trend_bracket_soxl.example.yaml")
    soxl = restrict_universe(cfg, ["SOXL"])
    assert soxl.universe == ["SOXL"]
    assert soxl.all_symbol_timeframes() == {("SOXL", "15Min")}
    assert all(r.symbols == ["SOXL"] for r in soxl.rules)


def test_ema9_trend_bracket_nobe_disables_breakeven():
    cfg = load_config("config/ema9_trend_bracket_nobe.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"
    assert cfg.rules[0].action.breakeven_after_bars == 0
    assert cfg.rules[0].action.stop_loss_pct == 1.5
    assert cfg.rules[0].action.take_profit_pct == 3.0


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
    assert "exit=ma_cross" in out
    assert "ema_period=9" in out
    assert "sma_period=20" in out
    assert "entry_cutoff=12:00" in out
    assert "flatten_by=15:55" in out
    rsi_rc = main(["validate", "--config", "config/ema9_trend_bracket_rsi.example.yaml"])
    assert rsi_rc == 0
    rsi_out = capsys.readouterr().out
    assert "rsi=RSI14 < 70" in rsi_out


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


def test_ema9_trend_bracket_rsi_config_loads():
    cfg = load_config("config/ema9_trend_bracket_rsi.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    rule = cfg.rules[0]
    assert rule.action.size and rule.action.size.value == 10
    assert rule.action.exit == "ma_cross"
    assert rule.action.stop_loss_pct == 1.5
    assert rule.action.take_profit_pct is None
    assert rule.action.breakeven_after_bars == 0
    assert isinstance(rule.when, GroupCond)
    assert rule.when.kind == "all"
    assert isinstance(rule.when.conditions[0], MaPairCrossCond)
    rsi = find_rsi_condition(rule.when)
    assert isinstance(rsi, RsiCond)
    assert rsi.period == 14
    assert rsi.below == 70
    assert rsi.timeframe == "15Min"
    assert rsi_filter_label(cfg) == "RSI14 < 70"
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"


def test_ema9_trend_bracket_rsi60_and_risk_rsi_load():
    sixty = load_config("config/ema9_trend_bracket_rsi60.example.yaml")
    sixty_rsi = find_rsi_condition(sixty.rules[0].when)
    assert sixty_rsi is not None and sixty_rsi.below == 60
    assert rsi_filter_label(sixty) == "RSI14 < 60"
    risk = load_config("config/ema9_trend_risk_rsi.example.yaml")
    assert risk.rules[0].action.size and risk.rules[0].action.size.type == "risk_pct"
    risk_rsi = find_rsi_condition(risk.rules[0].when)
    assert risk_rsi is not None and risk_rsi.below == 70
    assert rsi_filter_label(risk) == "RSI14 < 70"


def test_ema_sma_cross_rsi_sibling_toggle():
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
    assert isinstance(cond, GroupCond)
    assert cond.kind == "all"
    assert isinstance(cond.conditions[0], MaPairCrossCond)
    rsi = find_rsi_condition(cond)
    assert isinstance(rsi, RsiCond)
    assert rsi.period == 14
    assert rsi.below == 70
    assert rsi.timeframe == "15Min"


def test_ema_sma_cross_nested_rsi_toggle():
    cond = parse_condition(
        {
            "ema_sma_cross": {
                "ema_period": 9,
                "sma_period": 20,
                "timeframe": "15m",
                "direction": "over",
                "rsi": {"period": 14, "below": 70},
            }
        },
        default_timeframe="15m",
    )
    assert isinstance(cond, GroupCond)
    rsi = find_rsi_condition(cond)
    assert rsi is not None
    assert rsi.below == 70
    assert rsi.timeframe == "15Min"
    assert isinstance(cond.conditions[0], MaPairCrossCond)
    assert cond.conditions[0].direction == "bullish"


def test_ema_sma_cross_yaml_parses():
    cross = parse_condition(
        {"ema_sma_cross": {"ema_period": 9, "sma_period": 20, "timeframe": "15m", "direction": "over"}}
    )
    assert isinstance(cross, MaPairCrossCond)
    assert cross.ema_period == 9
    assert cross.sma_period == 20
    assert cross.direction == "bullish"
    under = parse_condition(
        {"ema_sma_cross": {"ema_period": 9, "sma_period": 20, "timeframe": "15m", "direction": "under"}}
    )
    assert under.direction == "bearish"
    pair = parse_condition(
        {"ma_pair_cross": {"ema_period": 9, "sma_period": 20, "direction": "bullish"}},
        default_timeframe="5m",
    )
    assert pair.timeframe == "5Min"


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
