import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from dta_bot.broker import DryRunBroker
from dta_bot.config import ActionSpec, BotConfig, RuleSpec, Settings, SizeSpec, load_config, parse_condition
from dta_bot.demo_bars import write_fixture
from dta_bot.engine import fire_key
from dta_bot.history import save_fixture
from dta_bot.killswitch import pause
from dta_bot.market_data import FixtureMarketData
from dta_bot.models import Account, Bar, Position
from dta_bot.runner import _entry_blocked_by_cutoff, _flatten_session, last_rule_fire_ts, run_once
from dta_bot.state import BotState
from tests.conftest import bar

NY = ZoneInfo("America/New_York")


def test_fixture_dry_run_fires_example_rules(tmp_path, caplog):
    fixture = write_fixture(tmp_path / "bars.json")
    cfg = load_config("config/rules.example.yaml")
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
    by_id = {(r.rule_id, r.symbol): r for r in results}
    assert by_id[("engulfing-with-trend", "AAPL")].matched
    assert not by_id[("engulfing-with-trend", "MSFT")].matched
    assert by_id[("hammer-oversold", "SPY")].matched
    assert by_id[("evening-star-or-engulfing-exit", "SPY")].matched
    # Dry-run recorded intended buys but did not mark submitted
    symbols = {o.symbol for o in broker.submitted}
    assert "AAPL" in symbols
    assert all(o.side == "buy" for o in broker.submitted)


def test_kill_switch_blocks_submit(tmp_path):
    fixture = write_fixture(tmp_path / "bars.json")
    cfg = load_config("config/rules.example.yaml")
    cfg.settings.state_file = str(tmp_path / "state.json")
    kill = tmp_path / "KILL"
    cfg.settings.kill_switch_file = str(kill)
    pause(str(kill))
    broker = DryRunBroker(equity=100_000)
    run_once(
        cfg,
        broker=broker,
        data=FixtureMarketData(fixture),
        state=BotState(),
        dry_run=False,
    )
    assert broker.submitted == []


def test_second_cycle_is_idempotent(tmp_path):
    fixture = write_fixture(tmp_path / "bars.json")
    cfg = load_config("config/rules.example.yaml")
    cfg.settings.state_file = str(tmp_path / "state.json")
    cfg.settings.kill_switch_file = str(tmp_path / "KILL")
    broker = DryRunBroker(equity=100_000)
    data = FixtureMarketData(fixture)
    state = BotState()
    run_once(cfg, broker=broker, data=data, state=state, dry_run=True)
    first_n = len(broker.submitted)
    run_once(cfg, broker=broker, data=data, state=state, dry_run=True)
    assert len(broker.submitted) == first_n


class _PosBroker:
    mode = "dry-run/offline"

    def __init__(self, positions: list[Position]) -> None:
        self._positions = {p.symbol.upper(): p for p in positions}
        self.closed: list[str] = []

    def get_account(self) -> Account:
        return Account(equity=100_000, cash=100_000, buying_power=100_000, status="ACTIVE")

    def get_positions(self) -> list[Position]:
        return list(self._positions.values())

    def submit_order(self, order):
        raise AssertionError("should not submit")

    def close_position(self, symbol: str) -> dict:
        self.closed.append(symbol)
        self._positions.pop(symbol.upper(), None)
        return {"symbol": symbol}


def test_ema_invalid_live_flatten_closes_when_close_below_ema(tmp_path):
    closes = [10.0] * 12 + [12.0, 9.0]
    bars = [
        bar(i, c, c + 0.1, c - 0.1, c)
        for i, c in enumerate(closes)
    ]
    fixture = tmp_path / "bars.json"
    save_fixture(fixture, {"AAPL": {"15Min": bars}})
    rule = RuleSpec(
        id="ema9_trend",
        symbols=["AAPL"],
        cooldown_minutes=0,
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
        action=ActionSpec(type="buy", size=SizeSpec(type="shares", value=10), exit="ema_invalid"),
    )
    cfg = BotConfig(
        settings=Settings(
            lookback_bars=80,
            max_open_positions=5,
            state_file=str(tmp_path / "state.json"),
            kill_switch_file=str(tmp_path / "KILL"),
        ),
        universe=["AAPL"],
        rules=[rule],
    )
    state = BotState()
    state.mark_fired(fire_key("ema9_trend", "AAPL", bars[-2].timestamp), "ema9_trend:AAPL", 0)
    assert last_rule_fire_ts(state, "ema9_trend", "AAPL") == bars[-2].timestamp
    broker = _PosBroker(
        [Position(symbol="AAPL", qty=10, side="long", avg_entry_price=12.0, market_value=90.0)]
    )
    run_once(cfg, broker=broker, data=FixtureMarketData(fixture), state=state, dry_run=True)
    assert broker.closed == ["AAPL"]


def test_lower_high_live_flatten_closes_when_high_drops(tmp_path):
    bars = [
        bar(0, 10.0, 10.5, 9.9, 10.2),
        bar(1, 10.2, 11.0, 10.1, 10.8),
        bar(2, 10.8, 10.9, 10.6, 10.7),
    ]
    fixture = tmp_path / "bars.json"
    save_fixture(fixture, {"AAPL": {"15Min": bars}})
    rule = RuleSpec(
        id="ema9_trend",
        symbols=["AAPL"],
        cooldown_minutes=0,
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
        action=ActionSpec(type="buy", size=SizeSpec(type="shares", value=10), exit="lower_high"),
    )
    cfg = BotConfig(
        settings=Settings(
            lookback_bars=80,
            max_open_positions=5,
            state_file=str(tmp_path / "state.json"),
            kill_switch_file=str(tmp_path / "KILL"),
        ),
        universe=["AAPL"],
        rules=[rule],
    )
    state = BotState()
    state.mark_fired(fire_key("ema9_trend", "AAPL", bars[0].timestamp), "ema9_trend:AAPL", 0)
    broker = _PosBroker(
        [Position(symbol="AAPL", qty=10, side="long", avg_entry_price=10.8, market_value=107.0)]
    )
    run_once(cfg, broker=broker, data=FixtureMarketData(fixture), state=state, dry_run=True)
    assert broker.closed == ["AAPL"]


def test_range_expansion_live_flatten_closes_when_range_expands(tmp_path):
    bars = [
        bar(0, 10.0, 10.2, 9.8, 10.0),
        bar(1, 10.0, 10.2, 9.8, 10.1),
        bar(2, 10.1, 10.3, 10.0, 10.2),
        bar(3, 10.2, 12.0, 9.5, 11.0),
    ]
    fixture = tmp_path / "bars.json"
    save_fixture(fixture, {"AAPL": {"15Min": bars}})
    rule = RuleSpec(
        id="ema9_trend",
        symbols=["AAPL"],
        cooldown_minutes=0,
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="shares", value=10),
            exit="range_expansion",
            exit_range_bars=3,
        ),
    )
    cfg = BotConfig(
        settings=Settings(
            lookback_bars=80,
            max_open_positions=5,
            state_file=str(tmp_path / "state.json"),
            kill_switch_file=str(tmp_path / "KILL"),
        ),
        universe=["AAPL"],
        rules=[rule],
    )
    state = BotState()
    state.mark_fired(fire_key("ema9_trend", "AAPL", bars[1].timestamp), "ema9_trend:AAPL", 0)
    broker = _PosBroker(
        [Position(symbol="AAPL", qty=10, side="long", avg_entry_price=10.2, market_value=110.0)]
    )
    run_once(cfg, broker=broker, data=FixtureMarketData(fixture), state=state, dry_run=True)
    assert broker.closed == ["AAPL"]


def test_ma_cross_live_flatten_closes_when_ema_crosses_under_sma(tmp_path):
    closes = [10.0] * 20 + [12.0, 8.0]
    bars = [bar(i, c, c + 0.1, c - 0.1, c) for i, c in enumerate(closes)]
    fixture = tmp_path / "bars.json"
    save_fixture(fixture, {"AAPL": {"15Min": bars}})
    rule = RuleSpec(
        id="ema9_trend",
        symbols=["AAPL"],
        cooldown_minutes=0,
        when=parse_condition(
            {"ema_sma_cross": {"ema_period": 9, "sma_period": 20, "timeframe": "15m", "direction": "bullish"}}
        ),
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="shares", value=10),
            exit="ma_cross",
            exit_ema_period=9,
            exit_sma_period=20,
            stop_loss_pct=1.5,
        ),
    )
    cfg = BotConfig(
        settings=Settings(
            lookback_bars=80,
            max_open_positions=5,
            state_file=str(tmp_path / "state.json"),
            kill_switch_file=str(tmp_path / "KILL"),
        ),
        universe=["AAPL"],
        rules=[rule],
    )
    state = BotState()
    state.mark_fired(fire_key("ema9_trend", "AAPL", bars[-2].timestamp), "ema9_trend:AAPL", 0)
    broker = _PosBroker(
        [Position(symbol="AAPL", qty=10, side="long", avg_entry_price=12.0, market_value=80.0)]
    )
    run_once(cfg, broker=broker, data=FixtureMarketData(fixture), state=state, dry_run=True)
    assert broker.closed == ["AAPL"]


def _gated_rule() -> RuleSpec:
    return RuleSpec(
        id="ema9_trend",
        symbols=["AAPL"],
        cooldown_minutes=0,
        when=parse_condition({"pattern": "bullish_engulfing", "timeframe": "15m"}),
        action=ActionSpec(type="buy", size=SizeSpec(type="shares", value=10)),
    )


def test_entry_cutoff_blocks_fill_at_1300(tmp_path):
    last = Bar(datetime(2026, 9, 11, 12, 45, tzinfo=NY), 10.0, 10.2, 9.9, 10.1, 1000)
    rule = _gated_rule()
    cfg = BotConfig(
        settings=Settings(entry_cutoff="13:00", flatten_by="15:55"),
        universe=["AAPL"],
        rules=[rule],
    )
    bars = {("AAPL", "15Min"): [last]}
    before = datetime(2026, 9, 11, 12, 50, tzinfo=NY)
    after = datetime(2026, 9, 11, 13, 0, tzinfo=NY)
    assert _entry_blocked_by_cutoff(rule, "AAPL", cfg, bars, now=before) is True
    assert _entry_blocked_by_cutoff(rule, "AAPL", cfg, bars, now=after) is True
    early_bar = Bar(datetime(2026, 9, 11, 12, 30, tzinfo=NY), 10.0, 10.2, 9.9, 10.1, 1000)
    assert (
        _entry_blocked_by_cutoff(
            rule, "AAPL", cfg, {("AAPL", "15Min"): [early_bar]}, now=before
        )
        is False
    )


def test_session_flatten_closes_at_wall_clock(tmp_path):
    cfg = BotConfig(
        settings=Settings(
            entry_cutoff="13:00",
            flatten_by="15:55",
            kill_switch_file=str(tmp_path / "KILL"),
        ),
        universe=["AAPL"],
        rules=[_gated_rule()],
    )
    broker = _PosBroker(
        [Position(symbol="AAPL", qty=10, side="long", avg_entry_price=10.0, market_value=100.0)]
    )
    last = Bar(datetime(2026, 9, 11, 15, 45, tzinfo=NY), 10.0, 10.2, 9.9, 10.1, 1000)
    _flatten_session(
        cfg,
        broker,
        {("AAPL", "15Min"): [last]},
        dry_run=True,
        now=datetime(2026, 9, 11, 15, 55, tzinfo=NY),
    )
    assert broker.closed == ["AAPL"]


def test_session_flatten_waits_until_due(tmp_path):
    cfg = BotConfig(
        settings=Settings(
            entry_cutoff="13:00",
            flatten_by="15:55",
            kill_switch_file=str(tmp_path / "KILL"),
        ),
        universe=["AAPL"],
        rules=[_gated_rule()],
    )
    broker = _PosBroker(
        [Position(symbol="AAPL", qty=10, side="long", avg_entry_price=10.0, market_value=100.0)]
    )
    last = Bar(datetime(2026, 9, 11, 15, 30, tzinfo=NY), 10.0, 10.2, 9.9, 10.1, 1000)
    _flatten_session(
        cfg,
        broker,
        {("AAPL", "15Min"): [last]},
        dry_run=True,
        now=datetime(2026, 9, 11, 15, 40, tzinfo=NY),
    )
    assert broker.closed == []


def test_runner_skips_opposite_signal_while_in_trade(tmp_path, caplog):
    bars = [
        bar(0, 10.10, 10.20, 10.00, 10.18),
        bar(1, 10.25, 10.30, 9.90, 9.95),
    ]
    fixture = tmp_path / "bars.json"
    save_fixture(fixture, {"AAPL": {"15Min": bars}})
    rule = RuleSpec(
        id="ema9_trend_short",
        symbols=["AAPL"],
        cooldown_minutes=0,
        when=parse_condition({"pattern": "bearish_engulfing", "timeframe": "15m"}),
        action=ActionSpec(
            type="sell",
            size=SizeSpec(type="shares", value=10),
            stop_mode="lock_plus",
            stop_loss_pct=1.0,
        ),
    )
    cfg = BotConfig(
        settings=Settings(
            lookback_bars=80,
            max_open_positions=5,
            state_file=str(tmp_path / "state.json"),
            kill_switch_file=str(tmp_path / "KILL"),
        ),
        universe=["AAPL"],
        rules=[rule],
    )
    broker = _PosBroker(
        [Position(symbol="AAPL", qty=10, side="long", avg_entry_price=10.0, market_value=100.0)]
    )
    with caplog.at_level(logging.INFO):
        results = run_once(
            cfg,
            broker=broker,
            data=FixtureMarketData(fixture),
            state=BotState(),
            dry_run=True,
        )
    assert any(r.matched and r.action_type == "sell" for r in results)
    assert broker.closed == []
    assert "opposite_signal_in_trade" in caplog.text
