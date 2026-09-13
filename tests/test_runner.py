from dta_bot.broker import DryRunBroker
from dta_bot.config import ActionSpec, BotConfig, RuleSpec, Settings, SizeSpec, load_config, parse_condition
from dta_bot.demo_bars import write_fixture
from dta_bot.engine import fire_key
from dta_bot.history import save_fixture
from dta_bot.killswitch import pause
from dta_bot.market_data import FixtureMarketData
from dta_bot.models import Account, Position
from dta_bot.runner import last_rule_fire_ts, run_once
from dta_bot.state import BotState
from tests.conftest import bar


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
