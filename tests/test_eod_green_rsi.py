"""EOD add-on: 15:30 ET green + RSI(14)<70, enter 15:45 open, −0.5% or flatten."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from dta_bot.backtest import run_backtest
from dta_bot.broker import DryRunBroker
from dta_bot.cli import main
from dta_bot.config import (
    ActionSpec,
    BarCond,
    BotConfig,
    RuleSpec,
    Settings,
    SizeSpec,
    has_eod_green_rsi,
    has_noon_stack,
    load_config,
    parse_condition,
)
from dta_bot.engine import evaluate_rule
from dta_bot.history import save_fixture
from dta_bot.indicators import rsi
from dta_bot.market_data import FixtureMarketData
from dta_bot.models import Bar
from dta_bot.runner import run_once
from dta_bot.state import BotState

NY = ZoneInfo("America/New_York")


def _et_bar(hour: int, minute: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(datetime(2026, 9, 11, hour, minute, tzinfo=NY), o, h, l, c, 1000)


def _walk_session(end_hour: int, end_minute: int, *, trend: str) -> list[Bar]:
    """15m RTH bars from 9:30 ET up to (not including) the end clock."""
    bars: list[Bar] = []
    t = datetime(2026, 9, 11, 9, 30, tzinfo=NY)
    end = datetime(2026, 9, 11, end_hour, end_minute, tzinfo=NY)
    i = 0
    while t < end:
        if trend == "down":
            close = 20.0 - i * 0.12
            bars.append(_et_bar(t.hour, t.minute, close + 0.04, close + 0.06, close - 0.05, close))
        else:
            close = 10.0 + i * 0.35
            bars.append(_et_bar(t.hour, t.minute, close - 0.04, close + 0.06, close - 0.06, close))
        nxt = t.minute + 15
        t = t.replace(hour=t.hour + nxt // 60, minute=nxt % 60)
        i += 1
    return bars


def _eod_when():
    return parse_condition(
        {
            "all": [
                {"bar": {"open_at": "15:30", "color": "green", "timeframe": "15m"}},
                {"rsi": {"period": 14, "timeframe": "15m", "below": 70}},
            ]
        }
    )


def _eod_rule(**kwargs) -> RuleSpec:
    defaults = dict(
        id="eod_green_rsi",
        symbols=["AAPL"],
        cooldown_minutes=60,
        when=_eod_when(),
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="shares", value=10),
            exit="fixed_bracket",
            stop_mode="entry_pct",
            stop_loss_pct=0.5,
        ),
    )
    defaults.update(kwargs)
    return RuleSpec(**defaults)


def _cfg(rule: RuleSpec) -> BotConfig:
    return BotConfig(
        settings=Settings(
            lookback_bars=80,
            timeframe="15m",
            session_timezone="America/New_York",
            entry_cutoff=None,
            flatten_by="15:55",
        ),
        universe=["AAPL"],
        rules=[rule],
    )


def test_parse_bar_open_at_and_color_shapes():
    combined = parse_condition({"bar": {"open_at": "15:30", "color": "bullish", "timeframe": "15m"}})
    assert isinstance(combined, BarCond)
    assert combined.open_at == "15:30"
    assert combined.color == "green"
    assert combined.timezone == "America/New_York"

    timed = parse_condition({"bar_open_at": "15:30", "timeframe": "15m"})
    assert isinstance(timed, BarCond)
    assert timed.open_at == "15:30"
    assert timed.color is None

    colored = parse_condition({"bar_color": "red", "timeframe": "15m"})
    assert isinstance(colored, BarCond)
    assert colored.color == "red"
    assert has_eod_green_rsi(_eod_when())
    assert not has_noon_stack(_eod_when())


def test_eod_green_rsi_fires_on_1530_green_with_rsi_below_70():
    bars = _walk_session(15, 30, trend="down")
    bars.append(_et_bar(15, 30, 16.00, 16.20, 15.90, 16.15))
    assert rsi([b.close for b in bars], 14) < 70
    ev = evaluate_rule(_eod_rule(), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert ev.matched
    assert "open_at 15:30" in ev.reasons[0]
    assert "green" in ev.reasons[0]
    assert "RSI14" in ev.reasons[0]


def test_eod_rejects_red_1530_even_when_rsi_is_low():
    bars = _walk_session(15, 30, trend="down")
    bars.append(_et_bar(15, 30, 16.20, 16.25, 15.80, 15.90))
    ev = evaluate_rule(_eod_rule(), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert not ev.matched
    assert "green" in ev.reasons[0]
    assert "→ False" in ev.reasons[0]


def test_eod_rejects_green_bar_that_is_not_1530():
    bars = _walk_session(15, 15, trend="down")
    bars.append(_et_bar(15, 15, 16.00, 16.20, 15.90, 16.15))
    ev = evaluate_rule(_eod_rule(), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert not ev.matched
    assert "open_at 15:30" in ev.reasons[0]


def test_eod_rejects_green_1530_when_rsi_at_or_above_70():
    bars = _walk_session(15, 30, trend="up")
    bars.append(_et_bar(15, 30, 18.00, 18.40, 17.90, 18.30))
    assert rsi([b.close for b in bars], 14) >= 70
    ev = evaluate_rule(_eod_rule(), "AAPL", {("AAPL", "15Min"): bars}, BotState())
    assert not ev.matched
    assert "RSI14" in ev.reasons[0]
    assert "< 70" in ev.reasons[0]


def test_eod_backtest_enters_1545_open_and_flattens_at_close():
    bars = _walk_session(15, 30, trend="down")
    bars.append(_et_bar(15, 30, 16.00, 16.20, 15.90, 16.15))
    # Fill 16.20 → stop 16.119. Keep the 15:45 low above that so flatten wins.
    bars.append(_et_bar(15, 45, 16.20, 16.30, 16.15, 16.28))
    result = run_backtest(_cfg(_eod_rule()), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 16.20
    assert trade.entry_time == datetime(2026, 9, 11, 15, 45, tzinfo=NY)
    assert trade.exit_reason == "session_flatten"
    assert trade.exit_price == 16.28
    assert trade.exit_time == datetime(2026, 9, 11, 16, 0, tzinfo=NY)
    assert trade.qty == 10


def test_eod_backtest_half_pct_fill_stop_beats_flatten():
    bars = _walk_session(15, 30, trend="down")
    bars.append(_et_bar(15, 30, 16.00, 16.20, 15.90, 16.15))
    # Fill 16.20 → stop 16.20 * 0.995 = 16.119. Low 16.05 tags it.
    bars.append(_et_bar(15, 45, 16.20, 16.30, 16.05, 16.10))
    result = run_backtest(_cfg(_eod_rule()), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 16.20
    assert trade.exit_reason == "stop"
    assert trade.exit_price == pytest.approx(16.20 * 0.995)


def test_eod_tradier_sandbox_config_loads_and_validates(capsys):
    cfg = load_config("config/eod_green_rsi_tradier_sandbox.example.yaml")
    assert cfg.settings.broker == "tradier"
    assert cfg.settings.tradier_endpoint == "sandbox"
    assert cfg.settings.tradier_preview is True
    assert cfg.settings.data_source == "yahoo"
    assert cfg.settings.dry_run is True
    assert cfg.settings.paper is True
    assert cfg.settings.allow_live is False
    assert cfg.settings.entry_cutoff is None
    assert cfg.settings.flatten_by == "15:55"
    assert cfg.settings.state_file == "data/state_eod_green_rsi.json"
    assert cfg.universe == ["AAPL"]
    rule = cfg.rules[0]
    assert rule.id == "eod_green_rsi"
    assert has_eod_green_rsi(rule.when)
    assert not has_noon_stack(rule.when)
    assert rule.action.stop_mode == "entry_pct"
    assert rule.action.stop_loss_pct == 0.5
    assert rule.action.exit == "fixed_bracket"
    assert rule.action.size and rule.action.size.value == 10
    assert cfg.all_symbol_timeframes() == {("AAPL", "15Min")}

    rc = main(["validate", "--config", "config/eod_green_rsi_tradier_sandbox.example.yaml"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "broker=tradier" in out
    assert "data_source=yahoo" in out
    assert "tradier_endpoint=sandbox" in out
    assert "stop_mode=entry_pct" in out
    assert "stop_loss_pct=0.5" in out
    assert "flatten_by=15:55" in out
    assert "entry_cutoff=None" in out


def test_eod_dry_run_fires_without_sending_orders(tmp_path):
    bars = _walk_session(15, 30, trend="down")
    bars.append(_et_bar(15, 30, 16.00, 16.20, 15.90, 16.15))
    fixture = tmp_path / "bars.json"
    save_fixture(fixture, {"AAPL": {"15Min": bars}})
    cfg = load_config("config/eod_green_rsi_tradier_sandbox.example.yaml")
    cfg.settings.state_file = str(tmp_path / "state.json")
    cfg.settings.kill_switch_file = str(tmp_path / "KILL")
    broker = DryRunBroker(equity=100_000)
    results = run_once(
        cfg,
        broker=broker,
        data=FixtureMarketData(fixture),
        state=BotState(),
        dry_run=True,
    )
    ev = next(r for r in results if r.rule_id == "eod_green_rsi" and r.symbol == "AAPL")
    assert ev.matched
    assert len(broker.submitted) == 1
    order = broker.submitted[0]
    assert order.symbol == "AAPL"
    assert order.side == "buy"
    assert order.qty == 10
    assert order.stop_loss_price == pytest.approx(16.15 * 0.995)
    assert broker.mode.startswith("dry-run/")
