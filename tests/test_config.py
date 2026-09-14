from pathlib import Path

import pytest

from dta_bot.cli import main
from dta_bot.config import (
    GroupCond,
    MaCond,
    MaCrossCond,
    MaPairCrossCond,
    RsiCond,
    VolumePrevCond,
    condition_timeframes,
    find_rsi_condition,
    has_noon_short_stack,
    has_noon_stack,
    has_volume_gt_prev,
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
    assert isinstance(rule.when, GroupCond)
    assert has_noon_stack(rule.when)
    assert any(isinstance(c, MaCrossCond) for c in rule.when.conditions)
    rsi = find_rsi_condition(rule.when)
    assert rsi is not None and rsi.below == 70
    assert rule.action.exit == "ma_cross_close"
    assert rule.action.exit_ema_period == 9
    assert rule.action.exit_sma_period == 20
    assert rule.action.stop_loss_pct is None
    assert rule.action.take_profit_pct is None
    assert rule.action.breakeven_after_bars == 0
    assert not has_volume_gt_prev(rule.when)
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
    assert [r.id for r in cfg.rules] == ["ema9_trend"]
    rule = cfg.rules[0]
    assert rule.action.exit == "ma_cross_close"
    assert rule.action.exit_ema_period == 9
    assert rule.action.exit_sma_period == 20
    assert rule.action.stop_loss_pct is None
    assert rule.action.take_profit_pct is None
    assert rule.action.size is not None
    assert rule.action.size.type == "risk_pct"
    assert rule.action.size.equity_risk == 0.01
    assert rule.action.size.stop_pct == 1.0
    assert rule.action.breakeven_after_bars == 0
    assert has_noon_stack(rule.when)
    assert not has_volume_gt_prev(rule.when)
    assert cfg.settings.entry_cutoff == "12:00"
    assert cfg.settings.flatten_by == "15:55"
    assert cfg.all_symbol_timeframes() == {("AAPL", "15Min"), ("MSFT", "15Min")}
    five = load_config("config/ema9_trend_risk_5m.example.yaml")
    assert five.settings.timeframe == "5Min"
    assert [r.id for r in five.rules] == ["ema9_trend"]
    assert five.rules[0].action.exit == "ma_cross_close"
    assert five.rules[0].action.stop_loss_pct is None
    assert five.rules[0].action.size is not None
    assert five.rules[0].action.size.type == "risk_pct"
    assert five.rules[0].action.size.stop_pct == 1.0
    assert has_noon_stack(five.rules[0].when)
    assert five.all_symbol_timeframes() == {("AAPL", "5Min"), ("MSFT", "5Min")}


def test_ema9_trend_bracket_config_keeps_ten_shares():
    cfg = load_config("config/ema9_trend_bracket.example.yaml")
    assert cfg.universe == ["AAPL", "MSFT"]
    assert cfg.rules[0].action.size and cfg.rules[0].action.size.type == "shares"
    assert cfg.rules[0].action.size.value == 10
    assert cfg.rules[0].action.exit == "ma_cross_close"
    assert cfg.rules[0].action.exit_ema_period == 9
    assert cfg.rules[0].action.exit_sma_period == 20
    assert cfg.rules[0].action.stop_loss_pct is None
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


def test_ema9_trend_aapl_msft_meta_configs_load():
    ten = load_config("config/ema9_trend_aapl_msft_meta.example.yaml")
    assert ten.universe == ["AAPL", "MSFT", "META"]
    assert [r.id for r in ten.rules] == ["ema9_trend"]
    rule = ten.rules[0]
    assert rule.symbols == ["AAPL", "MSFT", "META"]
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
    assert ten.all_symbol_timeframes() == {
        ("AAPL", "15Min"),
        ("MSFT", "15Min"),
        ("META", "15Min"),
    }

    risk = load_config("config/ema9_trend_risk_aapl_msft_meta.example.yaml")
    assert risk.universe == ["AAPL", "MSFT", "META"]
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
    assert risk.all_symbol_timeframes() == {
        ("AAPL", "15Min"),
        ("MSFT", "15Min"),
        ("META", "15Min"),
    }


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
    assert cfg.rules[0].action.exit == "ma_cross_close"
    assert cfg.rules[0].action.exit_ema_period == 9
    assert cfg.rules[0].action.exit_sma_period == 20
    assert cfg.rules[0].action.stop_loss_pct is None
    assert cfg.rules[0].action.take_profit_pct is None
    assert has_noon_stack(cfg.rules[0].when)
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
    assert has_noon_stack(five.rules[0].when)
    assert five.rules[0].action.exit == "ma_cross_close"
    assert condition_timeframes(five.rules[0].when) == {"5Min"}
    loaded_5m = load_config("config/ema9_trend.example.yaml", timeframe="5m")
    assert loaded_5m.all_symbol_timeframes() == five.all_symbol_timeframes()
    assert loaded_5m.rules[0].action.exit == "ma_cross_close"
    assert loaded_5m.rules[0].action.stop_loss_pct is None


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


def test_ema9_trend_lock1_add05_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_lock1_add05.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.resolved_lock_stop_pct() == 1.0
    assert rule.action.pyramid_add_pct == 0.5
    assert rule.action.pyramid_on_lock is False
    assert rule.action.take_profit_pct is None
    assert rule.action.has_pyramid_add() is True
    assert rule.action.resolved_pyramid_add_pct() == 0.5
    assert rule.action.size and rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert not has_volume_gt_prev(rule.when)
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    risk = load_config("config/ema9_trend_risk_nobe_lock1_add05.example.yaml")
    assert risk.rules[0].action.pyramid_add_pct == 0.5
    assert risk.rules[0].action.take_profit_pct is None
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01


def test_ema9_trend_lock1_pyramid2_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_lock1_pyramid2.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.resolved_lock_stop_pct() == 1.0
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.pyramid_on_lock is True
    assert rule.action.take_anchor == "entry"
    assert rule.action.take_profit_pct == 2.0
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert not has_volume_gt_prev(rule.when)
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    risk = load_config("config/ema9_trend_risk_nobe_lock1_pyramid2.example.yaml")
    assert risk.rules[0].action.stop_mode == "lock_plus"
    assert risk.rules[0].action.pyramid_on_lock is True
    assert risk.rules[0].action.take_anchor == "entry"
    assert risk.rules[0].action.take_profit_pct == 2.0
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01
    assert risk.rules[0].action.size.stop_pct == 1.0


def test_ema9_trend_lock1_half_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_lock1_half.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.resolved_lock_stop_pct() == 1.0
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.partial_take_on_lock is True
    assert rule.action.pyramid_on_lock is False
    assert rule.action.pyramid_add_pct is None
    assert rule.action.take_profit_pct is None
    assert rule.action.has_pyramid_add() is False
    assert rule.action.size and rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert not has_volume_gt_prev(rule.when)
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    risk = load_config("config/ema9_trend_risk_nobe_lock1_half.example.yaml")
    assert risk.rules[0].action.partial_take_on_lock is True
    assert risk.rules[0].action.pyramid_on_lock is False
    assert risk.rules[0].action.take_profit_pct is None
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01
    assert risk.rules[0].action.size.stop_pct == 1.0


def test_ema9_trend_lock1_half_be_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_lock1_half_be.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.partial_take_be is True
    assert rule.action.partial_take_on_lock is False
    assert rule.action.pyramid_on_lock is False
    assert rule.action.pyramid_add_pct is None
    assert rule.action.take_profit_pct is None
    assert rule.action.size and rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert not has_volume_gt_prev(rule.when)
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    risk = load_config("config/ema9_trend_risk_nobe_lock1_half_be.example.yaml")
    assert risk.rules[0].action.partial_take_be is True
    assert risk.rules[0].action.partial_take_on_lock is False
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01


def test_partial_take_be_requires_lock_plus_and_rejects_combos(tmp_path: Path):
    bad_mode = tmp_path / "bad_be_mode.yaml"
    bad_mode.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 10}
      stop_mode: entry_pct
      stop_loss_pct: 1.0
      partial_take_be: true
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="partial_take_be"):
        load_config(bad_mode)
    bad_lock = tmp_path / "bad_be_lock.yaml"
    bad_lock.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 10}
      stop_mode: lock_plus
      stop_loss_pct: 1.0
      partial_take_be: true
      partial_take_on_lock: true
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="cannot combine"):
        load_config(bad_lock)
    bad_pyr = tmp_path / "bad_be_pyr.yaml"
    bad_pyr.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 10}
      stop_mode: lock_plus
      stop_loss_pct: 1.0
      partial_take_be: true
      pyramid_add_pct: 0.5
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="cannot combine"):
        load_config(bad_pyr)


def test_partial_take_on_lock_requires_lock_plus_and_rejects_pyramid(tmp_path: Path):
    bad_mode = tmp_path / "bad_half_mode.yaml"
    bad_mode.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 10}
      stop_mode: entry_pct
      stop_loss_pct: 1.0
      partial_take_on_lock: true
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="partial_take_on_lock"):
        load_config(bad_mode)
    bad_pyr = tmp_path / "bad_half_pyr.yaml"
    bad_pyr.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 10}
      stop_mode: lock_plus
      stop_loss_pct: 1.0
      partial_take_on_lock: true
      pyramid_on_lock: true
      take_profit_pct: 2.0
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="cannot combine"):
        load_config(bad_pyr)
    bad_add = tmp_path / "bad_half_add.yaml"
    bad_add.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 10}
      stop_mode: lock_plus
      stop_loss_pct: 1.0
      partial_take_on_lock: true
      pyramid_add_pct: 0.5
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="cannot combine"):
        load_config(bad_add)


def test_pyramid_on_lock_requires_lock_plus_and_take(tmp_path: Path):
    bad_mode = tmp_path / "bad_pyr_mode.yaml"
    bad_mode.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 1}
      stop_mode: entry_pct
      stop_loss_pct: 1.0
      pyramid_on_lock: true
      take_profit_pct: 2.0
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="pyramid_on_lock"):
        load_config(bad_mode)
    bad_take = tmp_path / "bad_pyr_take.yaml"
    bad_take.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action:
      type: buy
      size: {type: shares, value: 1}
      stop_mode: lock_plus
      stop_loss_pct: 1.0
      pyramid_on_lock: true
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="take_profit_pct"):
        load_config(bad_take)


def test_ema9_trend_lock1_vol_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_lock1_vol.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.resolved_lock_trigger_pct() == 1.0
    assert rule.action.resolved_lock_stop_pct() == 1.0
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.take_profit_pct is None
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert has_volume_gt_prev(rule.when)
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    risk = load_config("config/ema9_trend_risk_nobe_lock1_vol.example.yaml")
    assert risk.rules[0].action.stop_mode == "lock_plus"
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01
    assert risk.rules[0].action.size.stop_pct == 1.0
    assert risk.rules[0].action.stop_loss_pct == 1.0
    assert has_volume_gt_prev(risk.rules[0].when)


def test_ema9_trend_lock1_macross_combo_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_lock1_macross.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "ma_cross_close"
    assert rule.action.stop_mode == "lock_plus"
    assert rule.action.stop_loss_pct == 1.0
    assert rule.action.lock_trigger_pct == 1.0
    assert rule.action.lock_stop_pct == 1.0
    assert rule.action.partial_take_on_lock is False
    assert rule.action.pyramid_on_lock is False
    assert rule.action.size and rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert not has_volume_gt_prev(rule.when)
    risk = load_config("config/ema9_trend_risk_nobe_lock1_macross.example.yaml")
    assert risk.rules[0].action.exit == "ma_cross_close"
    assert risk.rules[0].action.stop_mode == "lock_plus"
    assert risk.rules[0].action.stop_loss_pct == 1.0
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01
    assert risk.rules[0].action.size.stop_pct == 1.0


def test_ema9_trend_macross_close_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_macross.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "ma_cross_close"
    assert rule.action.exit_ema_period == 9
    assert rule.action.exit_sma_period == 20
    assert rule.action.stop_loss_pct is None
    assert rule.action.take_profit_pct is None
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert not has_volume_gt_prev(rule.when)
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    risk = load_config("config/ema9_trend_risk_nobe_macross.example.yaml")
    assert risk.rules[0].action.exit == "ma_cross_close"
    assert risk.rules[0].action.stop_loss_pct is None
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01
    assert risk.rules[0].action.size.stop_pct == 1.0
    assert not has_volume_gt_prev(risk.rules[0].when)


def test_ema9_trend_lower_high_vol_configs_load():
    ten = load_config("config/ema9_trend_bracket_nobe_lh_vol.example.yaml")
    rule = ten.rules[0]
    assert rule.action.exit == "lower_high"
    assert rule.action.stop_loss_pct is None
    assert rule.action.take_profit_pct is None
    assert rule.action.size and rule.action.size.type == "shares"
    assert rule.action.size.value == 10
    assert has_noon_stack(rule.when)
    assert has_volume_gt_prev(rule.when)
    leaves = rule.when.conditions
    assert any(isinstance(c, VolumePrevCond) and c.compare == "above" for c in leaves)
    assert ten.settings.entry_cutoff == "12:00"
    assert ten.settings.flatten_by == "15:55"
    risk = load_config("config/ema9_trend_risk_nobe_lh_vol.example.yaml")
    assert risk.rules[0].action.exit == "lower_high"
    assert risk.rules[0].action.stop_loss_pct is None
    assert risk.rules[0].action.size is not None
    assert risk.rules[0].action.size.type == "risk_pct"
    assert risk.rules[0].action.size.equity_risk == 0.01
    assert risk.rules[0].action.size.stop_pct == 1.0
    assert has_volume_gt_prev(risk.rules[0].when)


def test_volume_gt_prev_yaml_shapes():
    named = parse_condition({"volume_gt_prev": {"timeframe": "15m"}})
    assert isinstance(named, VolumePrevCond)
    assert named.compare == "above"
    vs = parse_condition({"volume": {"vs": "prev", "timeframe": "5m"}})
    assert isinstance(vs, VolumePrevCond)
    assert vs.timeframe == "5Min"


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
    lh_path = tmp_path / "lh.yaml"
    lh_path.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action: {type: buy, size: {type: shares, value: 1}, exit: lowerhigh}
""",
        encoding="utf-8",
    )
    lh = load_config(lh_path)
    assert lh.rules[0].action.exit == "lower_high"
    close_path = tmp_path / "maclose.yaml"
    close_path.write_text(
        """
settings: {timeframe: 15m}
universe: [AAPL]
rules:
  - id: x
    when: {ema_cross: {period: 9, direction: bullish}}
    action: {type: buy, size: {type: shares, value: 1}, exit: ma_cross_at_close}
""",
        encoding="utf-8",
    )
    close_cfg = load_config(close_path)
    assert close_cfg.rules[0].action.exit == "ma_cross_close"
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
    assert "exit=ma_cross_close" in out
    assert "ema_period=9" in out
    assert "sma_period=20" in out
    assert "stop=off" in out
    assert "stop_mode=lock_plus" not in out
    assert "rsi=RSI14 < 70" in out
    assert "rsi=RSI14 > 30" not in out
    assert "action=sell" not in out
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
    add05_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_lock1_add05.example.yaml"])
    assert add05_rc == 0
    add05_out = capsys.readouterr().out
    assert "stop_mode=lock_plus" in add05_out
    assert "pyramid_add_pct=0.5" in add05_out
    half_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_lock1_half.example.yaml"])
    assert half_rc == 0
    half_out = capsys.readouterr().out
    assert "stop_mode=lock_plus" in half_out
    assert "partial_take_on_lock" in half_out
    assert "pyramid_on_lock" not in half_out
    half_be_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_lock1_half_be.example.yaml"])
    assert half_be_rc == 0
    half_be_out = capsys.readouterr().out
    assert "stop_mode=lock_plus" in half_be_out
    assert "partial_take_be" in half_be_out
    assert "partial_take_on_lock" not in half_be_out
    pyr_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_lock1_pyramid2.example.yaml"])
    assert pyr_rc == 0
    pyr_out = capsys.readouterr().out
    assert "stop_mode=lock_plus" in pyr_out
    assert "pyramid_on_lock" in pyr_out
    assert "take_profit_pct=2" in pyr_out
    assert "take_anchor=entry" in pyr_out
    lock_vol_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_lock1_vol.example.yaml"])
    assert lock_vol_rc == 0
    lock_vol_out = capsys.readouterr().out
    assert "stop_mode=lock_plus" in lock_vol_out
    assert "volume_gt_prev" in lock_vol_out
    lh_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_lh_vol.example.yaml"])
    assert lh_rc == 0
    lh_out = capsys.readouterr().out
    assert "exit=lower_high" in lh_out
    assert "volume_gt_prev" in lh_out
    assert "stop=off" in lh_out
    macross_rc = main(["validate", "--config", "config/ema9_trend_bracket_nobe_macross.example.yaml"])
    assert macross_rc == 0
    macross_out = capsys.readouterr().out
    assert "exit=ma_cross_close" in macross_out
    assert "ema_period=9" in macross_out
    assert "sma_period=20" in macross_out
    assert "stop=off" in macross_out
    assert "volume_gt_prev" not in macross_out
    combo_rc = main(
        ["validate", "--config", "config/ema9_trend_bracket_nobe_lock1_macross.example.yaml"]
    )
    assert combo_rc == 0
    combo_out = capsys.readouterr().out
    assert "exit=ma_cross_close" in combo_out
    assert "stop_mode=lock_plus" in combo_out
    assert "lock_trigger_pct=1" in combo_out
    assert "ema_period=9" in combo_out
    assert "partial_take_on_lock" not in combo_out
    assert "volume_gt_prev" not in combo_out


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
