from dta_bot.broker import DryRunBroker
from dta_bot.config import load_config
from dta_bot.demo_bars import write_fixture
from dta_bot.killswitch import pause
from dta_bot.market_data import FixtureMarketData
from dta_bot.runner import run_once
from dta_bot.state import BotState


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
