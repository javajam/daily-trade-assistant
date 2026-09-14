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
    has_noon_short_stack,
    has_noon_stack,
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
    assert [r.id for r in cfg.rules] == ["ema9_trend", "ema9_trend_short"]
    rule = cfg.rules[0]
    assert rule.cooldown_minutes == 60
    assert rule.action.size and rule.action.size.value == 10
    assert isinstance(rule.when, GroupCond)
    assert has_noon_stack(rule.when)
    assert any(isinstance(c, MaCrossCond) for c in rule.when.conditions)
    rsi = find_rsi_condition(rule.when)
    assert rsi is not None and rsi.below == 70
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.resolved_lock_stop_pct() == 1.0
    assert rule.action.take_profit_pct is None
    assert rule.action.breakeven_after_bars == 0
    short = cfg.rules[1]
    assert short.enabled is True
    assert short.action.type == "sell"
    assert has_noon_short_stack(short.when)
    assert find_rsi_condition(short.when) is None
    assert short.action.exit == "ma_cross"
    assert short.action.exit_ema_period == 9
    assert short.action.exit_sma_period == 20
    assert short.action.stop_loss_pct is None
    assert short.action.stop_mode == "percent"
    assert short.action.take_profit_pct is None
    assert has_noon_short_stack(
        parse_condition(
            {
                "all": [
                    {"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bearish"}},
                    {"sma": {"period": 20, "timeframe": "15m", "compare": "below"}},
                ]
            }
        )
    )
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
    assert [r.id for r in cfg.rules] == ["ema9_trend", "ema9_trend_short"]
    rule = cfg.rules[0]
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.take_profit_pct is None
    assert rule.action.size is not None
    assert rule.action.size.type == "risk_pct"
    assert rule.action.size.equity_risk == 0.01
    assert rule.action.size.stop_pct == 1.0
    assert rule.action.breakeven_after_bars == 0
    assert has_noon_stack(rule.when)
    assert cfg.rules[1].action.type == "sell"
    assert has_noon_short_stack(cfg.rules[1].when)
    assert find_rsi_condition(cfg.rules[1].when) is None
    assert cfg.rules[1].action.exit == "ma_cross"
    assert cfg.rules[1].action.stop_loss_pct is None
    assert cfg.rules[1].action.size is not None
    assert cfg.rules[1].action.size.type == "shares"
    assert cfg.rules[1].action.size.value == 10
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"
    assert cfg.all_symbol_timeframes() == {("AAPL", "15Min"), ("MSFT", "15Min")}
    five = load_config("config/ema9_trend_risk_5m.example.yaml")
    assert five.settings.timeframe == "5Min"
    assert five.rules[0].action.stop_mode == "lock_plus"
    assert five.rules[0].action.size is not None
    assert five.rules[0].action.size.type == "risk_pct"
    assert five.rules[0].action.size.stop_pct == 1.0
    assert has_noon_stack(five.rules[0].when)
    assert [r.id for r in five.rules] == ["ema9_trend", "ema9_trend_short"]
    assert five.rules[1].action.type == "sell"
    assert has_noon_short_stack(five.rules[1].when)
    assert find_rsi_condition(five.rules[1].when) is None
    assert five.rules[1].action.exit == "ma_cross"
    assert five.rules[1].action.stop_loss_pct is None
    assert five.rules[1].action.size is not None
    assert five.rules[1].action.size.type == "shares"
    assert five.all_symbol_timeframes() == {("AAPL", "5Min"), ("MSFT", "5Min")}


def test_ema9_trend_bracket_config_keeps_ten_shares():
    cfg = load_config("config/ema9_trend_bracket.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.type == "shares"
    assert cfg.rules[0].action.size.value == 10
    assert cfg.rules[0].action.exit == "fixed_bracket"
    assert cfg.rules[0].action.stop_mode == "lock_plus"
    assert cfg.rules[0].action.stop_loss_pct == 1.0
    assert cfg.rules[0].action.take_profit_pct is None
    assert cfg.rules[0].action.breakeven_after_bars == 0
    assert has_noon_stack(cfg.rules[0].when)
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"


def test_ema9_trend_pair_configs_preserve_ma_cross():
    cfg = load_config("config/ema9_trend_pair.example.yaml")
    rule = cfg.rules[0]
    assert isinstance(rule.when, MaPairCrossCond)
    assert rule.when.ema_period == 9
    assert rule.when.sma_period == 20
    assert rule.action.exit == "ma_cross"
    assert rule.action.stop_loss_pct == 1.5
    assert rule.action.take_profit_pct is None
    risk = load_config("config/ema9_trend_risk_pair.example.yaml")
    assert isinstance(risk.rules[0].when, MaPairCrossCond)
    assert risk.rules[0].action.exit == "ma_cross"
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.stop_pct == 1.5
    five = load_config("config/ema9_trend_5m_pair.example.yaml")
    assert five.settings.timeframe == "5Min"
    assert isinstance(five.rules[0].when, MaPairCrossCond)
    assert five.rules[0].action.exit == "ma_cross"


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


def test_ema9_trend_tsla_mu_configs_load():
    ten = load_config("config/ema9_trend_tsla_mu.example.yaml")
    assert ten.universe == ["TSLA", "MU"]
    assert [r.id for r in ten.rules] == ["ema9_trend"]
    rule = ten.rules[0]
    assert rule.symbols == ["TSLA", "MU"]
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.take_profit_pct is None
    assert has_noon_stack(rule.when)
    rsi = find_rsi_condition(rule.when)
    assert rsi is not None and rsi.below == 70
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    assert ten.settings.timeframe == "15Min"
    assert ten.all_symbol_timeframes() == {("TSLA", "15Min"), ("MU", "15Min")}

    risk = load_config("config/ema9_trend_risk_tsla_mu.example.yaml")
    assert risk.universe == ["TSLA", "MU"]
    rrule = risk.rules[0]
    assert rrule.action.size is not None
    assert rrule.action.size.type == "risk_pct"
    assert rrule.action.size.equity_risk == 0.01
    assert rrule.action.size.stop_pct == 1.0
    assert rrule.action.stop_mode == "lock_plus"
    assert rrule.action.take_profit_pct is None
    assert has_noon_stack(rrule.when)
    assert risk.settings.entry_cutoff == "12:00"
    assert risk.settings.flatten_by == "15:55"
    assert risk.all_symbol_timeframes() == {("TSLA", "15Min"), ("MU", "15Min")}


def test_ema9_trend_spy_qqq_configs_load():
    ten = load_config("config/ema9_trend_spy_qqq.example.yaml")
    assert ten.universe == ["SPY", "QQQ"]
    assert [r.id for r in ten.rules] == ["ema9_trend"]
    rule = ten.rules[0]
    assert rule.symbols == ["SPY", "QQQ"]
    assert rule.enabled is True
    assert rule.action.type == "buy"
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.resolved_lock_stop_pct() == 1.0
    assert rule.action.take_profit_pct is None
    assert has_noon_stack(rule.when)
    rsi = find_rsi_condition(rule.when)
    assert rsi is not None and rsi.below == 70
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    assert ten.settings.timeframe == "15Min"
    assert ten.all_symbol_timeframes() == {("SPY", "15Min"), ("QQQ", "15Min")}

    risk = load_config("config/ema9_trend_risk_spy_qqq.example.yaml")
    assert risk.universe == ["SPY", "QQQ"]
    assert [r.id for r in risk.rules] == ["ema9_trend"]
    rrule = risk.rules[0]
    assert rrule.action.type == "buy"
    assert rrule.action.size is not None
    assert rrule.action.size.type == "risk_pct"
    assert rrule.action.size.equity_risk == 0.01
    assert rrule.action.size.stop_pct == 1.0
    assert rrule.action.stop_mode == "lock_plus"
    assert rrule.action.take_profit_pct is None
    assert has_noon_stack(rrule.when)
    assert risk.settings.entry_cutoff == "12:00"
    assert risk.settings.flatten_by == "15:55"
    assert risk.all_symbol_timeframes() == {("SPY", "15Min"), ("QQQ", "15Min")}


def test_ema9_trend_nvda_amd_configs_load():
    ten = load_config("config/ema9_trend_nvda_amd.example.yaml")
    assert ten.universe == ["NVDA", "AMD"]
    assert [r.id for r in ten.rules] == ["ema9_trend"]
    rule = ten.rules[0]
    assert rule.symbols == ["NVDA", "AMD"]
    assert rule.enabled is True
    assert rule.action.type == "buy"
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.resolved_lock_stop_pct() == 1.0
    assert rule.action.take_profit_pct is None
    assert has_noon_stack(rule.when)
    rsi = find_rsi_condition(rule.when)
    assert rsi is not None and rsi.below == 70
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    assert ten.settings.timeframe == "15Min"
    assert ten.all_symbol_timeframes() == {("NVDA", "15Min"), ("AMD", "15Min")}

    risk = load_config("config/ema9_trend_risk_nvda_amd.example.yaml")
    assert risk.universe == ["NVDA", "AMD"]
    assert [r.id for r in risk.rules] == ["ema9_trend"]
    rrule = risk.rules[0]
    assert rrule.action.type == "buy"
    assert rrule.action.size is not None
    assert rrule.action.size.type == "risk_pct"
    assert rrule.action.size.equity_risk == 0.01
    assert rrule.action.size.stop_pct == 1.0
    assert rrule.action.stop_mode == "lock_plus"
    assert rrule.action.take_profit_pct is None
    assert has_noon_stack(rrule.when)
    assert risk.settings.entry_cutoff == "12:00"
    assert risk.settings.flatten_by == "15:55"
    assert risk.all_symbol_timeframes() == {("NVDA", "15Min"), ("AMD", "15Min")}


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
    assert [r.id for r in cfg.rules] == ["ema9_trend", "ema9_trend_short"]
    assert cfg.rules[0].cooldown_minutes == 60
    assert cfg.rules[0].action.exit == "fixed_bracket"
    assert cfg.rules[0].action.stop_mode == "lock_plus"
    assert cfg.rules[0].action.stop_loss_pct == 1.0
    assert cfg.rules[0].action.take_profit_pct is None
    assert has_noon_stack(cfg.rules[0].when)
    assert cfg.rules[1].action.type == "sell"
    assert has_noon_short_stack(cfg.rules[1].when)
    assert find_rsi_condition(cfg.rules[1].when) is None
    assert cfg.rules[1].action.exit == "ma_cross"
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
    assert [r.cooldown_minutes for r in five.rules] == [60, 60]
    assert [r.id for r in five.rules] == [r.id for r in cfg.rules]
    assert has_noon_stack(five.rules[0].when)
    assert has_noon_short_stack(five.rules[1].when)
    assert find_rsi_condition(five.rules[1].when) is None
    assert five.rules[1].action.exit == "ma_cross"
    assert condition_timeframes(five.rules[0].when) == {"5Min"}
    assert condition_timeframes(five.rules[1].when) == {"5Min"}
    loaded_5m = load_config("config/ema9_trend.example.yaml", timeframe="5m")
    assert loaded_5m.all_symbol_timeframes() == five.all_symbol_timeframes()
    assert loaded_5m.rules[0].action.stop_mode == "lock_plus"


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
    assert cfg.rules[0].action.exit == "fixed_bracket"
    assert cfg.rules[0].action.stop_loss_pct == 1.5
    assert cfg.rules[0].action.take_profit_pct == 3.0
    assert isinstance(cfg.rules[0].when, GroupCond)
    assert any(isinstance(c, MaCrossCond) for c in cfg.rules[0].when.conditions)
    rsi = find_rsi_condition(cfg.rules[0].when)
    assert rsi is not None and rsi.below == 70


def test_ema9_trend_bracket_nobe_12_uses_tighter_brackets():
    cfg = load_config("config/ema9_trend_bracket_nobe_12.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"
    rule = cfg.rules[0]
    assert rule.action.breakeven_after_bars == 0
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "percent"
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.take_profit_pct == 2.0
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert isinstance(rule.when, GroupCond)
    assert any(isinstance(c, MaCrossCond) for c in rule.when.conditions)
    rsi = find_rsi_condition(rule.when)
    assert rsi is not None and rsi.below == 70


def test_ema9_trend_risk_nobe_matches_stop_pct_to_bracket():
    wide = load_config("config/ema9_trend_risk_nobe.example.yaml")
    tight = load_config("config/ema9_trend_risk_nobe_12.example.yaml")
    assert wide.rules[0].action.size is not None
    assert wide.rules[0].action.size.type == "risk_pct"
    assert wide.rules[0].action.size.equity_risk == 0.01
    assert wide.rules[0].action.size.stop_pct == 1.5
    assert wide.rules[0].action.stop_loss_pct == 1.5
    assert wide.rules[0].action.take_profit_pct == 3.0
    assert wide.rules[0].action.exit == "fixed_bracket"
    assert wide.rules[0].action.breakeven_after_bars == 0
    assert tight.rules[0].action.size is not None
    assert tight.rules[0].action.size.type == "risk_pct"
    assert tight.rules[0].action.size.equity_risk == 0.01
    assert tight.rules[0].action.size.stop_pct == 1.0
    assert tight.rules[0].action.stop_loss_pct == 1.0
    assert tight.rules[0].action.take_profit_pct == 2.0
    assert tight.rules[0].action.stop_mode == "percent"
    assert tight.rules[0].action.exit == "fixed_bracket"
    assert tight.rules[0].action.breakeven_after_bars == 0
    for cfg in (wide, tight):
        assert cfg.settings.entry_cutoff == "12:00"
        assert cfg.settings.flatten_by == "15:55"
        assert isinstance(cfg.rules[0].when, GroupCond)
        assert any(isinstance(c, MaCrossCond) for c in cfg.rules[0].when.conditions)
        rsi = find_rsi_condition(cfg.rules[0].when)
        assert rsi is not None and rsi.below == 70


def test_ema9_trend_sma20_stop_configs_load():
    ten = load_config("config/ema9_trend_bracket_sma20.example.yaml")
    rule = ten.rules[0]
    assert rule.action.stop_mode == "sma20"
    assert rule.action.stop_sma_period == 20
    assert rule.action.take_profit_pct == 2.0
    assert rule.action.stop_loss_pct is None
    assert rule.action.breakeven_after_bars == 0
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    notake = load_config("config/ema9_trend_bracket_sma20_notake.example.yaml")
    assert notake.rules[0].action.stop_mode == "sma20"
    assert notake.rules[0].action.take_profit_pct is None
    risk = load_config("config/ema9_trend_risk_sma20.example.yaml")
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01
    assert risk.rules[0].action.size.stop_pct is None
    assert risk.rules[0].action.stop_mode == "sma20"
    assert risk.rules[0].action.take_profit_pct == 2.0
    risk_notake = load_config("config/ema9_trend_risk_sma20_notake.example.yaml")
    assert risk_notake.rules[0].action.stop_mode == "sma20"
    assert risk_notake.rules[0].action.take_profit_pct is None


def test_ema9_trend_stop_manage_configs_load():
    fixed = load_config("config/ema9_trend_bracket_nobe_fixed1.example.yaml")
    lock = load_config("config/ema9_trend_bracket_nobe_lock1.example.yaml")
    trail = load_config("config/ema9_trend_bracket_nobe_trail1.example.yaml")
    assert fixed.rules[0].action.stop_mode == "entry_pct"
    assert fixed.rules[0].action.stop_loss_pct == 1.0
    assert fixed.rules[0].action.take_profit_pct is None
    assert lock.rules[0].action.stop_mode == "lock_plus"
    assert lock.rules[0].action.resolved_lock_trigger_pct() == 1.0
    assert lock.rules[0].action.resolved_lock_stop_pct() == 1.0
    assert lock.rules[0].action.take_profit_pct is None
    assert trail.rules[0].action.stop_mode == "trail"
    assert trail.rules[0].action.resolved_trail_pct() == 1.0
    assert trail.rules[0].action.take_profit_pct is None
    for cfg in (fixed, lock, trail):
        assert cfg.settings.entry_cutoff == "12:00"
        assert cfg.settings.flatten_by == "15:55"
        assert cfg.rules[0].action.exit == "fixed_bracket"
        assert cfg.rules[0].action.size and cfg.rules[0].action.size.type == "shares"
        assert cfg.rules[0].action.size.value == 10
        rsi = find_rsi_condition(cfg.rules[0].when)
        assert rsi is not None and rsi.below == 70
    risk_fixed = load_config("config/ema9_trend_risk_nobe_fixed1.example.yaml")
    risk_lock = load_config("config/ema9_trend_risk_nobe_lock1.example.yaml")
    risk_trail = load_config("config/ema9_trend_risk_nobe_trail1.example.yaml")
    for cfg, mode in (
        (risk_fixed, "entry_pct"),
        (risk_lock, "lock_plus"),
        (risk_trail, "trail"),
    ):
        assert cfg.rules[0].action.stop_mode == mode
        assert cfg.rules[0].action.size is not None
        assert cfg.rules[0].action.size.type == "risk_pct"
        assert cfg.rules[0].action.size.equity_risk == 0.01
        assert cfg.rules[0].action.size.stop_pct == 1.0
        assert cfg.rules[0].action.stop_loss_pct == 1.0
        assert cfg.rules[0].action.take_profit_pct is None


def test_stop_mode_aliases_and_defaults():
    lock = load_config("config/ema9_trend_bracket_nobe_lock1.example.yaml")
    # Explicit lock fields resolve to 1.0; omitting them falls back to stop_loss_pct.
    assert lock.rules[0].action.lock_trigger_pct == 1.0
    bare = lock.rules[0].action.model_copy(update={"lock_trigger_pct": None, "lock_stop_pct": None})
    assert bare.resolved_lock_trigger_pct() == 1.0
    assert bare.resolved_lock_stop_pct() == 1.0


def test_stop_mode_unknown_rejected(tmp_path: Path):
    path = tmp_path / "bad_stop.yaml"
    path.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action: {type: buy, size: {type: shares, value: 1}, stop_mode: foobar}
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="stop_mode"):
        load_config(path)


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
    assert "exit=fixed_bracket" in out
    assert "exit=ma_cross" in out
    assert "ema_period=9" in out
    assert "sma_period=20" in out
    assert "stop_mode=lock_plus" in out
    assert "stop=off" in out
    assert "lock_trigger_pct=1" in out
    assert "rsi=RSI14 < 70" in out
    assert "rsi=RSI14 > 30" not in out
    assert "action=sell" in out
    assert "entry_cutoff=12:00" in out
    assert "flatten_by=15:55" in out
    pair_rc = main(["validate", "--config", "config/ema9_trend_pair.example.yaml"])
    assert pair_rc == 0
    pair_out = capsys.readouterr().out
    assert "exit=ma_cross" in pair_out
    assert "ema_period=9" in pair_out
    assert "sma_period=20" in pair_out
    rsi_rc = main(["validate", "--config", "config/ema9_trend_bracket_rsi.example.yaml"])
    assert rsi_rc == 0
    rsi_out = capsys.readouterr().out
    assert "rsi=RSI14 < 70" in rsi_out
    sma_rc = main(["validate", "--config", "config/ema9_trend_bracket_sma20.example.yaml"])
    assert sma_rc == 0
    sma_out = capsys.readouterr().out
    assert "stop_mode=sma20" in sma_out
    assert "stop_sma_period=20" in sma_out
    lock_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_lock1.example.yaml"])
    assert lock_rc == 0
    lock_out = capsys.readouterr().out
    assert "stop_mode=lock_plus" in lock_out
    assert "lock_trigger_pct=1" in lock_out


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
