from datetime import date, timedelta

from dta_bot.models import Bar
from dta_bot.orb import build_opening_range, find_setups
from dta_bot.orb_backtest import run_orb_backtest
from dta_bot.orb_config import load_orb_config
from dta_bot.orb_demo_bars import SESSION, aapl_top_fade_short, build_fixture, msft_bottom_fade_long
from dta_bot.orb_engine import evaluate_orb
from dta_bot.state import BotState


def _cfg(**orb_over):
    cfg = load_orb_config("config/orb_reversal.example.yaml")
    if orb_over:
        cfg = cfg.model_copy(update={"orb": cfg.orb.model_copy(update=orb_over)})
    return cfg


def _b(minutes: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(SESSION + timedelta(minutes=minutes), o, h, l, c, 1000)


def test_fixture_backtest_takes_midpoint_on_both_fades():
    cfg = _cfg()
    aapl = aapl_top_fade_short()
    msft = msft_bottom_fade_long()
    bars = {
        ("AAPL", "15Min"): aapl["15Min"],
        ("AAPL", "5Min"): aapl["5Min"],
        ("MSFT", "15Min"): msft["15Min"],
        ("MSFT", "5Min"): msft["5Min"],
        ("SPY", "15Min"): [],
        ("SPY", "5Min"): [],
    }
    result = run_orb_backtest(cfg, bars, starting_equity=100_000)
    by_sym = {t.symbol: t for t in result.trades}
    assert set(by_sym) == {"AAPL", "MSFT"}

    short = by_sym["AAPL"]
    assert short.side == "sell"
    assert short.entry_price == 102.55
    assert short.exit_price == 100.0
    assert short.exit_reason == "take"
    assert short.qty == 10
    assert short.pnl == 10 * (102.55 - 100.0)

    long = by_sym["MSFT"]
    assert long.side == "buy"
    assert long.entry_price == 201.50
    assert long.exit_price == 205.0
    assert long.exit_reason == "take"
    assert long.pnl == 10 * (205.0 - 201.50)


def test_entry_is_open_of_bar_after_reversal():
    cfg = _cfg()
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    aapl = aapl_top_fade_short()
    result = run_orb_backtest(
        cfg,
        {("AAPL", "15Min"): aapl["15Min"], ("AAPL", "5Min"): aapl["5Min"]},
    )
    trade = result.trades[0]
    reversal = aapl["5Min"][2]
    entry = aapl["5Min"][3]
    assert reversal.timestamp + timedelta(minutes=5) == entry.timestamp
    assert trade.entry_time == entry.timestamp
    assert trade.entry_price == entry.open


def test_skip_second_entry_while_still_in_position():
    cfg = _cfg()
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    # First fade enters at 10:00; price never hits stop/take. Second fade at 10:20.
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 103.85, 103.10, 103.80),  # probe 1
        _b(25, 103.70, 103.90, 102.50, 102.60),  # reversal 1
        _b(30, 102.55, 102.70, 102.40, 102.50),  # entry 1; no stop/take
        _b(35, 102.50, 102.60, 102.30, 102.40),
        _b(40, 103.30, 103.80, 103.20, 103.70),  # probe 2
        _b(45, 103.60, 103.85, 102.80, 102.90),  # reversal 2
        _b(50, 102.85, 102.95, 102.70, 102.80),  # would-be entry 2
    ]
    rng = build_opening_range(orb, date(2026, 9, 11), orb_timeframe="15m")
    assert len(find_setups("AAPL", signal, rng)) == 2
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.signals == 2
    accepted = [s for s in result.signals if s.accepted]
    skipped = [s for s in result.signals if s.skip_reason == "already_in_position"]
    assert len(accepted) == 1
    assert len(skipped) == 1
    assert result.report.trades == 1  # flattened at eod
    assert result.trades[0].exit_reason == "eod"


def test_evaluate_scan_fires_fixture_setups():
    cfg = load_orb_config("config/orb_reversal.example.yaml")
    raw = build_fixture()
    from dta_bot.market_data import bars_from_rows
    from dta_bot.timeframes import normalize

    bars = {}
    for symbol, tfs in raw.items():
        for tf, rows in tfs.items():
            bars[(symbol, normalize(tf))] = bars_from_rows(rows)
    results = evaluate_orb(cfg, bars, BotState(), scan_all=True)
    fired = {(r.symbol, r.action_type) for r in results if r.matched}
    missed = {r.symbol for r in results if not r.matched}
    assert ("AAPL", "sell") in fired
    assert ("MSFT", "buy") in fired
    assert "SPY" in missed
    aapl = next(r for r in results if r.symbol == "AAPL" and r.matched)
    assert aapl.extra["stop"] == 103.9
    assert aapl.extra["take"] == 100.0
    assert aapl.extra["entry_open"] == 102.55


def test_cli_evaluate_fixture_prints_fires(capsys):
    from dta_bot.cli import main

    rc = main(
        [
            "evaluate",
            "--config",
            "config/orb_reversal.example.yaml",
            "--fixture",
            "config/orb_sample_bars.json",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "[FIRE] AAPL / orb_reversal" in out
    assert "[FIRE] MSFT / orb_reversal" in out
    assert "[NO]   SPY / orb_reversal" in out
    assert "short" in out
    assert "long" in out
