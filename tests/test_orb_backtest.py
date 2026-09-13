from datetime import date, timedelta

import pytest

from dta_bot.models import Bar
from dta_bot.orb import build_opening_range, find_setups
from dta_bot.orb_backtest import run_orb_backtest
from dta_bot.orb_config import load_orb_config
from dta_bot.orb_demo_bars import SESSION, aapl_top_fade_short, build_fixture, msft_bottom_fade_long
from dta_bot.models import Account, Position
from dta_bot.orb import ema_cross_exit, ema_through
from dta_bot.orb_engine import (
    build_orb_order,
    ema_cross_flatten_bar,
    evaluate_orb,
    first_profit_flatten_bar,
    last_reversal_ts,
)
from dta_bot.state import BotState, fmt_ts


def _cfg(**orb_over):
    cfg = load_orb_config("config/orb_reversal.example.yaml")
    if orb_over:
        cfg = cfg.model_copy(update={"orb": cfg.orb.model_copy(update=orb_over)})
    return cfg


def _b(minutes: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(SESSION + timedelta(minutes=minutes), o, h, l, c, 1000)


def test_fixture_backtest_exits_ema_cross():
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

    # AAPL short: default TP is first post-entry close above EMA9 (10:10 close 103.00).
    short = by_sym["AAPL"]
    assert short.side == "sell"
    assert short.entry_price == 102.55
    assert short.exit_price == 103.00
    assert short.exit_reason == "take"
    assert short.qty == 10
    assert short.pnl == 10 * (102.55 - 103.00)

    # MSFT long: default TP is first post-entry close below EMA9 (10:10 close 201.20).
    long = by_sym["MSFT"]
    assert long.side == "buy"
    assert long.entry_price == 201.50
    assert long.exit_price == 201.20
    assert long.exit_reason == "take"
    assert long.pnl == 10 * (201.20 - 201.50)


def test_first_profitable_close_still_available():
    cfg = _cfg(take_profit_mode="first_profitable_close")
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
    # Entry bar itself is already profitable vs the fill.
    assert by_sym["AAPL"].exit_price == 102.45
    assert by_sym["MSFT"].exit_price == 201.60
    assert by_sym["AAPL"].exit_reason == "take"
    assert by_sym["MSFT"].exit_reason == "take"


def test_or_midpoint_take_still_available():
    cfg = _cfg(take_profit_mode="or_midpoint")
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
    assert by_sym["AAPL"].exit_price == 100.0
    assert by_sym["MSFT"].exit_price == 205.0
    assert by_sym["AAPL"].exit_reason == "take"
    assert by_sym["MSFT"].exit_reason == "take"


def test_entry_is_open_of_bar_after_reversal():
    cfg = _cfg()
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    aapl = aapl_top_fade_short()
    result = run_orb_backtest(
        cfg,
        {("AAPL", "15Min"): aapl["15Min"], ("AAPL", "5Min"): aapl["5Min"]},
    )
    trade = result.trades[0]
    reversal = next(
        b for b in aapl["5Min"] if b.timestamp.hour == 13 and b.timestamp.minute == 55
    )
    entry = next(
        b for b in aapl["5Min"] if b.timestamp.hour == 14 and b.timestamp.minute == 0
    )
    assert reversal.timestamp + timedelta(minutes=5) == entry.timestamp
    assert trade.entry_time == entry.timestamp
    assert trade.entry_price == entry.open


def test_skip_second_entry_while_still_in_position():
    # Isolate the in-position skip from the default one-trade-before-10:30 gate.
    # A second same-session top-touch would print the Friday OR-high stop, so the
    # second fade is the next session on a tighter OR that never trades 104/100.
    # Keep the older midpoint take so a later session's first print cannot
    # flatten Friday and free the symbol before Monday's fill is tested.
    cfg = _cfg(max_trades_before_cutoff=5, take_profit_mode="or_midpoint", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    day2 = 3 * 24 * 60  # Monday 2026-09-14
    orb = [_b(0, 100, 104, 96, 101), _b(day2, 102, 103, 101, 102)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),  # Fri probe
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),  # Fri entry; close not profitable for short
        _b(35, 102.60, 102.70, 102.50, 102.65),
        _b(day2 + 15, 102.2, 102.4, 102.0, 102.3),
        _b(day2 + 20, 102.70, 103.00, 102.60, 102.95),  # Mon touch of 103 + close in 5% band
        _b(day2 + 25, 102.80, 102.90, 102.20, 102.30),
        _b(day2 + 30, 102.25, 102.35, 102.15, 102.20),  # would-be entry
    ]
    rng = build_opening_range(orb, date(2026, 9, 11), orb_timeframe="15m")
    assert len(find_setups("AAPL", signal, rng, ema_filter=False)) == 1
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
    assert "SOXL" in missed
    aapl = next(r for r in results if r.symbol == "AAPL" and r.matched)
    assert aapl.extra["stop"] == 104.0
    assert aapl.extra["take"] is None
    assert aapl.extra["take_profit_mode"] == "ema_cross"
    assert aapl.extra["reversal_in_range"] == "close"
    assert aapl.extra["ema_filter"] is True
    assert aapl.extra["ema"] is not None
    assert aapl.extra["stop_mode"] == "orb_extreme"
    assert aapl.extra["probe_mode"] == "touch_and_band"
    assert aapl.extra["entry_open"] == 102.55
    assert aapl.extra["or_open"] == 100.0
    assert aapl.extra["or_height_pct"] == pytest.approx(0.08)


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
    assert "[NO]   SOXL / orb_reversal" in out
    assert "short" in out
    assert "long" in out


def test_backtest_skips_session_when_or_height_below_floor():
    cfg = _cfg(probe_mode="touch", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    # 0.40% OR — probe/reversal still print, but the vol gate blocks the entry.
    orb = [_b(0, 100, 100.40, 100.00, 100.20)]
    signal = [
        _b(15, 100.20, 100.25, 100.15, 100.22),
        _b(20, 100.30, 100.40, 100.28, 100.38),
        _b(25, 100.36, 100.38, 100.10, 100.12),
        _b(30, 100.12, 100.16, 100.08, 100.10),
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.signals == 1
    assert result.signals[0].skip_reason == "min_or_height"
    assert result.report.trades == 0
    off = _cfg(probe_mode="touch", min_or_height_pct=0, ema_filter=False)
    off = off.model_copy(update={"universe": ["AAPL"]})
    taken = run_orb_backtest(off, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert taken.report.trades == 1


def test_backtest_takes_only_first_pre_1030_entry():
    cfg = _cfg(ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.50),  # 10:00 — kept
        _b(35, 102.50, 102.60, 102.30, 102.40),
        _b(40, 103.30, 104.00, 103.20, 103.70),
        _b(45, 103.60, 103.85, 102.80, 102.90),
        _b(50, 102.85, 102.95, 102.70, 102.80),  # 10:20 — gated
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.signals == 2
    assert [s.skip_reason for s in result.signals] == [None, "max_trades_before_cutoff"]
    assert result.report.trades == 1
    assert result.trades[0].entry_time == signal[3].timestamp


def test_backtest_rejects_entry_at_cutoff():
    cfg = _cfg(ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(50, 103.20, 104.00, 103.10, 103.80),
        _b(55, 103.70, 103.90, 102.50, 102.60),
        _b(60, 102.55, 102.70, 102.40, 102.50),  # 10:30
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.trades == 0
    assert result.signals[0].skip_reason == "entry_cutoff"


def test_reversal_candle_mode_keeps_old_stop_in_backtest():
    cfg = _cfg(stop_mode="reversal_candle", take_profit_mode="or_midpoint")
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    aapl = aapl_top_fade_short()
    result = run_orb_backtest(
        cfg,
        {("AAPL", "15Min"): aapl["15Min"], ("AAPL", "5Min"): aapl["5Min"]},
    )
    assert result.trades[0].exit_reason == "take"
    # Fixture never trades the reversal high; the lot still uses that stop.
    assert "reversal candle extreme" in result.signals[0].reason


def test_first_profitable_close_waits_for_later_bar():
    cfg = _cfg(take_profit_mode="first_profitable_close", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),  # entry; close 102.60 not < 102.55
        _b(35, 102.60, 102.70, 102.50, 102.58),  # still not profitable
        _b(40, 102.58, 102.62, 102.20, 102.30),  # first close < entry
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 102.55
    assert trade.exit_price == 102.30
    assert trade.exit_reason == "take"
    assert trade.exit_time == signal[5].timestamp + timedelta(minutes=5)


def test_stop_still_works_before_first_profit():
    cfg = _cfg(take_profit_mode="first_profitable_close", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),  # entry
        _b(35, 102.60, 104.20, 102.50, 103.80),  # trades OR high stop; close not profitable
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "stop"
    assert trade.exit_price == 104.0


def test_stop_wins_same_bar_as_first_profit():
    cfg = _cfg(take_profit_mode="first_profitable_close", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),
        # Wicks the OR-high stop AND closes profitable for the short.
        _b(35, 102.60, 104.10, 102.00, 102.20),
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.trades[0].exit_reason == "stop"
    assert result.trades[0].exit_price == 104.0


def test_stop_wins_same_bar_as_one_r():
    cfg = _cfg(take_profit_mode="one_r", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),
        # Wicks OR-high stop 104 and 1R take 101.10.
        _b(35, 102.60, 104.10, 100.90, 101.00),
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.trades[0].exit_reason == "stop"
    assert result.trades[0].exit_price == 104.0


def test_one_r_take_fills_when_price_reaches_target():
    cfg = _cfg(take_profit_mode="one_r", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),
        # Hits 1R 101.10 without trading the OR-high stop.
        _b(35, 102.40, 102.50, 100.90, 101.20),
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.trades[0].exit_reason == "take"
    assert result.trades[0].exit_price == 101.10
    assert result.trades[0].pnl == 10 * (102.55 - 101.10)


def test_backtest_rejects_reversal_that_closes_outside_or():
    cfg = _cfg(ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 95.20, 95.50),  # bearish but close below OR low
        _b(30, 95.40, 95.60, 95.20, 95.30),
    ]
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.trades == 0
    assert result.report.signals == 0


def test_live_order_omits_resting_take_for_ema_cross():
    cfg = _cfg()
    aapl = aapl_top_fade_short()
    rng = build_opening_range(aapl["15Min"], date(2026, 9, 11), orb_timeframe="15m")
    setup = find_setups("AAPL", aapl["5Min"], rng)[0]
    account = Account(equity=100_000, cash=100_000, buying_power=100_000, status="ACTIVE")
    order = build_orb_order(setup, account=account, config=cfg)
    assert order is not None
    assert order.stop_loss_price == 104.0
    assert order.take_profit_price is None
    mid_cfg = _cfg(take_profit_mode="or_midpoint")
    mid_setup = find_setups("AAPL", aapl["5Min"], rng, take_profit_mode="or_midpoint")[0]
    mid_order = build_orb_order(mid_setup, account=account, config=mid_cfg)
    assert mid_order is not None
    assert mid_order.take_profit_price == 100.0
    one_cfg = _cfg(take_profit_mode="one_r")
    one_setup = find_setups("AAPL", aapl["5Min"], rng, take_profit_mode="one_r")[0]
    one_order = build_orb_order(one_setup, account=account, config=one_cfg)
    assert one_order is not None
    assert one_order.take_profit_price == 101.10
    first_cfg = _cfg(take_profit_mode="first_profitable_close")
    first_setup = find_setups("AAPL", aapl["5Min"], rng, take_profit_mode="first_profitable_close")[0]
    first_order = build_orb_order(first_setup, account=account, config=first_cfg)
    assert first_order is not None
    assert first_order.take_profit_price is None


def test_live_order_estimates_one_r_when_entry_unknown():
    cfg = _cfg(take_profit_mode="one_r")
    aapl = aapl_top_fade_short()
    rng = build_opening_range(aapl["15Min"], date(2026, 9, 11), orb_timeframe="15m")
    # Tape ends on the reversal so the next-open fill is not known yet.
    # Keep the EMA warmup bars (prefix) plus mid/probe/reversal.
    series = aapl["5Min"][:12]
    setup = find_setups("AAPL", series, rng, take_profit_mode="one_r")[0]
    assert setup.entry_bar is None
    assert setup.take is None
    account = Account(equity=100_000, cash=100_000, buying_power=100_000, status="ACTIVE")
    order = build_orb_order(setup, account=account, config=cfg, last_price=102.55)
    assert order is not None
    assert order.take_profit_price == 101.10


def test_first_profit_flatten_requires_bar_after_reversal():
    reversal = _b(25, 103.70, 103.90, 102.50, 102.60)
    entry = _b(30, 102.55, 102.70, 102.40, 102.45)
    pos = Position(
        symbol="AAPL",
        qty=10,
        side="sell",
        avg_entry_price=102.55,
        market_value=-1024.5,
    )
    assert first_profit_flatten_bar(pos, [reversal], after=reversal.timestamp) is None
    hit = first_profit_flatten_bar(pos, [reversal, entry], after=reversal.timestamp)
    assert hit is entry
    assert last_reversal_ts(BotState(), "AAPL") is None
    state = BotState(fired_keys={"orb_reversal:AAPL:" + fmt_ts(reversal.timestamp): fmt_ts(reversal.timestamp)})
    assert last_reversal_ts(state, "AAPL") == reversal.timestamp


def _warmup(price: float, n: int = 9, start_minutes: int = -45) -> list:
    return [
        _b(start_minutes + 5 * i, price, price + 0.10, price - 0.10, price)
        for i in range(n)
    ]


def test_ema_cross_short_exits_first_close_above_ema():
    cfg = _cfg(take_profit_mode="ema_cross", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        *_warmup(103.80),
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),  # entry; close still below EMA9
        _b(35, 102.60, 102.70, 102.50, 102.58),  # still below EMA9
        _b(40, 102.58, 103.50, 102.50, 103.20),  # first close > EMA9
    ]
    assert not ema_cross_exit(
        side="sell", close=signal[-3].close, ema_value=ema_through(signal, signal[-3], 9)
    )
    assert not ema_cross_exit(
        side="sell", close=signal[-2].close, ema_value=ema_through(signal, signal[-2], 9)
    )
    assert ema_cross_exit(
        side="sell", close=signal[-1].close, ema_value=ema_through(signal, signal[-1], 9)
    )
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 102.55
    assert trade.exit_price == 103.20
    assert trade.exit_reason == "take"
    assert trade.exit_time == signal[-1].timestamp + timedelta(minutes=5)


def test_ema_cross_long_exits_first_close_below_ema():
    cfg = _cfg(take_profit_mode="ema_cross", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["MSFT"]})
    orb = [_b(0, 204, 210, 200, 205)]
    signal = [
        *_warmup(200.20),
        _b(15, 205.0, 205.4, 204.6, 205.1),
        _b(20, 200.80, 200.90, 200.00, 200.30),
        _b(25, 200.40, 201.50, 200.20, 201.40),
        _b(30, 201.50, 201.80, 201.30, 201.60),  # entry; close still above EMA9
        _b(35, 201.60, 202.40, 201.50, 202.20),  # still above EMA9
        _b(40, 202.10, 202.20, 200.40, 200.50),  # first close < EMA9
    ]
    assert not ema_cross_exit(
        side="buy", close=signal[-3].close, ema_value=ema_through(signal, signal[-3], 9)
    )
    assert not ema_cross_exit(
        side="buy", close=signal[-2].close, ema_value=ema_through(signal, signal[-2], 9)
    )
    assert ema_cross_exit(
        side="buy", close=signal[-1].close, ema_value=ema_through(signal, signal[-1], 9)
    )
    result = run_orb_backtest(cfg, {("MSFT", "15Min"): orb, ("MSFT", "5Min"): signal})
    trade = result.trades[0]
    assert trade.side == "buy"
    assert trade.entry_price == 201.50
    assert trade.exit_price == 200.50
    assert trade.exit_reason == "take"


def test_stop_wins_same_bar_as_ema_cross():
    cfg = _cfg(take_profit_mode="ema_cross", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        *_warmup(103.80),
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.60),
        # Wicks the OR-high stop AND closes above EMA9 for the short.
        _b(35, 102.60, 104.10, 102.00, 103.20),
    ]
    assert ema_cross_exit(
        side="sell", close=signal[-1].close, ema_value=ema_through(signal, signal[-1], 9)
    )
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.trades[0].exit_reason == "stop"
    assert result.trades[0].exit_price == 104.0


def test_ema_cross_does_not_exit_when_ema_missing():
    cfg = _cfg(take_profit_mode="ema_cross", ema_filter=False)
    cfg = cfg.model_copy(update={"universe": ["AAPL"]})
    orb = [_b(0, 100, 104, 96, 101)]
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 103.20),  # would cross if EMA existed
    ]
    assert ema_through(signal, signal[-1], 9) is None
    result = run_orb_backtest(cfg, {("AAPL", "15Min"): orb, ("AAPL", "5Min"): signal})
    assert result.trades[0].exit_reason == "eod"
    assert result.trades[0].exit_price == 103.20


def test_ema_cross_flatten_requires_bar_after_reversal():
    warmup = _warmup(103.80)
    reversal = _b(25, 103.70, 103.90, 102.50, 102.60)
    entry = _b(30, 102.55, 102.70, 102.40, 102.45)
    mid_hold = _b(35, 102.40, 102.50, 99.80, 100.10)
    cross = _b(40, 100.20, 103.20, 100.10, 103.00)
    series = [
        *warmup,
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        reversal,
        entry,
        mid_hold,
        cross,
    ]
    pos = Position(
        symbol="AAPL",
        qty=10,
        side="sell",
        avg_entry_price=102.55,
        market_value=-1024.5,
    )
    assert ema_cross_flatten_bar(pos, series[: series.index(entry) + 1], after=reversal.timestamp) is None
    hit = ema_cross_flatten_bar(pos, series, after=reversal.timestamp)
    assert hit is cross
    assert ema_cross_flatten_bar(pos, series, after=None) is None
