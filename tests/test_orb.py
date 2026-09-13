from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from dta_bot.models import Bar
from dta_bot.orb import (
    aggregate_opening_range,
    build_opening_range,
    find_setups,
    gate_setups,
    live_setup,
    next_signal_bar,
)
from dta_bot.orb_config import load_orb_config
from dta_bot.orb_demo_bars import SESSION, aapl_top_fade_short, msft_bottom_fade_long, spy_no_trade
from tests.conftest import bar


ET = ZoneInfo("America/New_York")


def _b(minutes: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(SESSION + timedelta(minutes=minutes), o, h, l, c, 1000)


def test_example_orb_config_is_paper_only():
    cfg = load_orb_config("config/orb_reversal.example.yaml")
    assert cfg.strategy == "orb_reversal"
    assert cfg.settings.paper is True
    assert cfg.settings.allow_live is False
    assert cfg.settings.dry_run is True
    assert cfg.universe == ["AAPL", "MSFT", "SPY"]
    assert cfg.orb.orb_timeframe == "15Min"
    assert cfg.orb.signal_timeframe == "5Min"
    assert cfg.orb.edge_pct == 0.05
    assert cfg.orb.probe_mode == "touch"
    assert cfg.orb.session_open == "09:30"
    assert cfg.orb.session_timezone == "America/New_York"
    assert cfg.orb.on_open_position == "skip"
    assert cfg.orb.take_profit == "midpoint"
    assert cfg.orb.stop_mode == "orb_extreme"
    assert cfg.orb.entry_cutoff == "10:30"
    assert cfg.orb.max_trades_before_cutoff == 1
    assert cfg.orb.allow_entries_after_cutoff is False
    pairs = cfg.all_symbol_timeframes()
    assert ("AAPL", "15Min") in pairs
    assert ("AAPL", "5Min") in pairs


def test_edge_pct_must_be_a_fraction(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
strategy: orb_reversal
universe: [AAPL]
orb: {edge_pct: 5}
sizing: {type: shares, value: 1}
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="0.05"):
        load_orb_config(path)


def test_probe_mode_must_be_known(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
strategy: orb_reversal
universe: [AAPL]
orb: {probe_mode: wick_only}
sizing: {type: shares, value: 1}
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="touch"):
        load_orb_config(path)


def test_stop_mode_must_be_known(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
strategy: orb_reversal
universe: [AAPL]
orb: {stop_mode: wick}
sizing: {type: shares, value: 1}
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="orb_extreme"):
        load_orb_config(path)


def test_opening_range_is_first_bar_at_or_after_rth_open():
    premkt = _b(-15, 99, 105, 90, 100)  # wider range — must not become the OR
    orb = _b(0, 100, 104, 96, 101)
    later = _b(15, 101, 102, 100, 101)
    rng = build_opening_range(
        [premkt, orb, later],
        date(2026, 9, 11),
        session_open="09:30",
        session_timezone="America/New_York",
        orb_timeframe="15m",
    )
    assert rng is not None
    assert rng.high == 104
    assert rng.low == 96
    assert rng.midpoint == 100
    assert rng.band(0.05) == pytest.approx(0.4)
    assert rng.top_zone(0.05) == (103.6, 104.0)
    assert rng.bottom_zone(0.05) == (96.0, 96.4)
    assert rng.start.astimezone(ET).hour == 9
    assert rng.start.astimezone(ET).minute == 30
    assert (rng.end - rng.start) == timedelta(minutes=15)


def test_classify_close_inclusive_edges_not_breakouts():
    rng = build_opening_range(
        [_b(0, 100, 104, 96, 101)],
        date(2026, 9, 11),
        orb_timeframe="15m",
    )
    assert rng is not None
    assert rng.classify_close(104.0, 0.05) == "top"  # touch of high
    assert rng.classify_close(103.6, 0.05) == "top"
    assert rng.classify_close(104.01, 0.05) is None  # broke the high
    assert rng.classify_close(96.0, 0.05) == "bottom"
    assert rng.classify_close(96.4, 0.05) == "bottom"
    assert rng.classify_close(100.0, 0.05) is None
    assert rng.classify_close(103.59, 0.05) is None


def test_classify_touch_requires_wick_of_or_extreme():
    rng = build_opening_range(
        [_b(0, 100, 104, 96, 101)],
        date(2026, 9, 11),
        orb_timeframe="15m",
    )
    assert rng is not None
    assert rng.classify_touch(_b(20, 103.20, 104.00, 103.10, 103.80)) == "top"
    assert rng.classify_touch(_b(20, 103.20, 104.15, 103.10, 102.50)) == "top"  # wick through
    assert rng.classify_touch(_b(20, 103.20, 103.85, 103.10, 103.80)) is None  # close in band, no touch
    assert rng.classify_touch(_b(20, 96.40, 96.80, 96.00, 96.20)) == "bottom"
    assert rng.classify_touch(_b(20, 96.40, 96.80, 95.90, 96.20)) == "bottom"
    assert rng.classify_touch(_b(20, 96.40, 96.80, 96.10, 96.20)) is None
    assert rng.classify_touch(_b(20, 96.00, 104.00, 96.00, 100.00)) is None  # both edges
    assert rng.classify_probe(_b(20, 103.20, 103.85, 103.10, 103.80), probe_mode="touch") is None
    assert rng.classify_probe(
        _b(20, 103.20, 103.85, 103.10, 103.80), probe_mode="edge_band", edge_pct=0.05
    ) == "top"


def test_close_in_band_without_touch_does_not_fire():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    # Close 103.80 is inside the 5% top band [103.60, 104.00]; high 103.85 never reaches 104.
    probe = _b(20, 103.20, 103.85, 103.10, 103.80)
    reversal = _b(25, 103.70, 103.90, 102.50, 102.60)
    entry = _b(30, 102.55, 102.70, 102.40, 102.45)
    mid = _b(15, 101.0, 101.4, 100.6, 100.8)
    assert rng.classify_close(probe.close, 0.05) == "top"
    assert probe.high < rng.high
    assert find_setups("AAPL", [mid, probe, reversal, entry], rng) == []
    assert find_setups("AAPL", [mid, probe, reversal, entry], rng, probe_mode="touch") == []
    # Old behavior still available.
    band = find_setups(
        "AAPL", [mid, probe, reversal, entry], rng, probe_mode="edge_band", edge_pct=0.05
    )
    assert len(band) == 1
    assert band[0].side == "sell"
    assert band[0].probe_mode == "edge_band"


def test_bottom_close_in_band_without_touch_does_not_fire():
    rng = build_opening_range([_b(0, 204, 210, 200, 205)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    # Close 200.30 is inside the 5% bottom band [200.00, 200.50]; low 200.10 never reaches 200.
    probe = _b(20, 200.80, 200.90, 200.10, 200.30)
    reversal = _b(25, 200.40, 201.50, 200.20, 201.40)
    entry = _b(30, 201.50, 201.80, 201.30, 201.60)
    series = [_b(15, 205, 205.4, 204.6, 205.1), probe, reversal, entry]
    assert rng.classify_close(probe.close, 0.05) == "bottom"
    assert probe.low > rng.low
    assert find_setups("MSFT", series, rng) == []
    band = find_setups("MSFT", series, rng, probe_mode="edge_band")
    assert len(band) == 1
    assert band[0].side == "buy"


def test_touch_plus_opposite_color_still_fires():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    probe = _b(20, 103.20, 104.00, 103.10, 103.80)
    reversal = _b(25, 103.70, 103.90, 102.50, 102.60)
    entry = _b(30, 102.55, 102.70, 102.40, 102.45)
    mid = _b(15, 101.0, 101.4, 100.6, 100.8)
    setups = find_setups("AAPL", [mid, probe, reversal, entry], rng, probe_mode="touch")
    assert len(setups) == 1
    assert setups[0].zone == "top"
    assert setups[0].side == "sell"
    assert setups[0].probe_mode == "touch"
    assert setups[0].probe.high >= rng.high
    assert setups[0].stop == 104.0
    assert setups[0].take == 100.0


def test_touch_wick_through_or_extreme_still_fires():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    # High prints through the OR high; close is mid-range (would miss the old 5% band).
    probe = _b(20, 103.20, 104.25, 102.80, 102.90)
    reversal = _b(25, 102.80, 103.00, 101.50, 101.60)
    entry = _b(30, 101.55, 101.70, 101.40, 101.45)
    setups = find_setups("AAPL", [_b(15, 101.0, 101.4, 100.6, 100.8), probe, reversal, entry], rng)
    assert len(setups) == 1
    assert setups[0].side == "sell"
    assert find_setups(
        "AAPL",
        [_b(15, 101.0, 101.4, 100.6, 100.8), probe, reversal, entry],
        rng,
        probe_mode="edge_band",
    ) == []


def test_aggregate_or_from_signal_bars():
    # Three 5m slices covering 9:30–9:45: highs 102/104/101, lows 99/97/96.
    slices = [
        _b(0, 100, 102, 99, 101),
        _b(5, 101, 104, 97, 100),
        _b(10, 100, 101, 96, 100.5),
    ]
    rng = aggregate_opening_range(
        slices,
        date(2026, 9, 11),
        orb_timeframe="15m",
        signal_timeframe="5m",
    )
    assert rng is not None
    assert rng.high == 104
    assert rng.low == 96
    assert rng.source == "aggregated"


def test_top_fade_short_probe_reversal_entry_stop_target():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    probe = _b(20, 103.20, 104.00, 103.10, 103.80)
    reversal = _b(25, 103.70, 103.90, 102.50, 102.60)
    entry = _b(30, 102.55, 102.70, 102.40, 102.45)
    mid = _b(15, 101.0, 101.4, 100.6, 100.8)
    setups = find_setups("AAPL", [mid, probe, reversal, entry], rng, edge_pct=0.05)
    assert len(setups) == 1
    setup = setups[0]
    assert setup.zone == "top"
    assert setup.side == "sell"
    assert setup.probe.close == 103.80
    assert setup.reversal.is_bearish()
    assert setup.entry_bar is not None
    assert setup.entry_bar.timestamp == entry.timestamp
    assert setup.entry_bar.open == 102.55
    assert setup.stop == 104.0  # opening-range high (orb_extreme)
    assert setup.take == 100.0  # OR midpoint
    assert next_signal_bar([mid, probe, reversal, entry], reversal.timestamp) == entry


def test_bottom_fade_long_probe_reversal_entry_stop_target():
    rng = build_opening_range([_b(0, 204, 210, 200, 205)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    probe = _b(20, 200.80, 200.90, 200.00, 200.30)
    reversal = _b(25, 200.40, 201.50, 200.20, 201.40)
    entry = _b(30, 201.50, 201.80, 201.30, 201.60)
    setups = find_setups("MSFT", [_b(15, 205, 205.4, 204.6, 205.1), probe, reversal, entry], rng)
    assert len(setups) == 1
    setup = setups[0]
    assert setup.zone == "bottom"
    assert setup.side == "buy"
    assert setup.stop == 200.0  # opening-range low (orb_extreme)
    assert setup.take == 205.0
    assert setup.entry_bar.open == 201.50


def test_no_trade_when_close_outside_band():
    rng = build_opening_range([_b(0, 494, 500, 490, 496)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    outside = _b(20, 496.2, 498.4, 496.0, 498.0)
    nxt = _b(25, 498.0, 498.6, 497.2, 497.4)
    assert find_setups("SPY", [_b(15, 496, 496.8, 495.5, 496.2), outside, nxt], rng) == []


def test_no_trade_when_same_color_reversal():
    rng = build_opening_range([_b(0, 494, 500, 490, 496)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    probe = _b(30, 499.60, 500.00, 499.40, 499.80)
    same = _b(35, 499.70, 500.10, 499.50, 499.95)  # bullish after top probe
    assert probe.close >= 499.5
    assert same.is_bullish()
    assert find_setups("SPY", [probe, same], rng) == []


def test_doji_reversal_is_not_opposite_color():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    probe = _b(20, 103.2, 104.0, 103.1, 103.8)
    doji = _b(25, 103.5, 103.6, 103.4, 103.5)
    assert find_setups("AAPL", [probe, doji], rng) == []


def test_live_setup_only_when_last_closed_bar_is_the_reversal():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    probe = _b(20, 103.2, 104.0, 103.1, 103.8)
    reversal = _b(25, 103.7, 103.9, 102.5, 102.6)
    entry = _b(30, 102.55, 102.7, 102.4, 102.45)
    series = [_b(15, 101, 101.4, 100.6, 100.8), probe, reversal, entry]
    setups = find_setups("AAPL", series, rng)
    assert live_setup(setups, series[:-1]) is setups[0]
    assert live_setup(setups, series) is None  # last bar is the entry, too late to fire live


def test_demo_fixture_helpers_match_locked_math():
    aapl = aapl_top_fade_short()
    rng = build_opening_range(aapl["15Min"], date(2026, 9, 11), orb_timeframe="15m")
    setups = find_setups("AAPL", aapl["5Min"], rng)
    assert setups[0].side == "sell"
    assert setups[0].stop == 104.0
    assert setups[0].take == 100.0
    assert setups[0].entry_bar.open == 102.55
    assert setups[0].stop_mode == "orb_extreme"

    msft = msft_bottom_fade_long()
    rng = build_opening_range(msft["15Min"], date(2026, 9, 11), orb_timeframe="15m")
    setups = find_setups("MSFT", msft["5Min"], rng)
    assert setups[0].side == "buy"
    assert setups[0].stop == 200.0
    assert setups[0].take == 205.0

    spy = spy_no_trade()
    rng = build_opening_range(spy["15Min"], date(2026, 9, 11), orb_timeframe="15m")
    assert find_setups("SPY", spy["5Min"], rng) == []


def test_reversal_candle_stop_uses_candle_extreme():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    probe = _b(20, 103.20, 104.00, 103.10, 103.80)
    reversal = _b(25, 103.70, 103.90, 102.50, 102.60)
    entry = _b(30, 102.55, 102.70, 102.40, 102.45)
    setups = find_setups(
        "AAPL",
        [_b(15, 101.0, 101.4, 100.6, 100.8), probe, reversal, entry],
        rng,
        stop_mode="reversal_candle",
    )
    assert setups[0].stop == 103.90
    assert setups[0].stop_mode == "reversal_candle"


def test_gate_keeps_first_pre_cutoff_entry_only():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    # First fade enters 10:00; second would enter 10:20 — both before 10:30.
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(20, 103.20, 104.00, 103.10, 103.80),
        _b(25, 103.70, 103.90, 102.50, 102.60),
        _b(30, 102.55, 102.70, 102.40, 102.50),  # 10:00 entry
        _b(35, 102.50, 102.60, 102.30, 102.40),
        _b(40, 103.30, 104.00, 103.20, 103.70),
        _b(45, 103.60, 103.85, 102.80, 102.90),
        _b(50, 102.85, 102.95, 102.70, 102.80),  # 10:20 would-be entry
    ]
    setups = find_setups("AAPL", signal, rng)
    assert len(setups) == 2
    gated = gate_setups(setups)
    assert gated[0][1] is None
    assert gated[1][1] == "max_trades_before_cutoff"


def test_gate_rejects_entry_at_or_after_1030():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    # Reversal 10:25 → entry bar 10:30 ET (exactly the cutoff).
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(50, 103.20, 104.00, 103.10, 103.80),  # 10:20 probe
        _b(55, 103.70, 103.90, 102.50, 102.60),  # 10:25 reversal
        _b(60, 102.55, 102.70, 102.40, 102.50),  # 10:30 entry
    ]
    setups = find_setups("AAPL", signal, rng)
    assert len(setups) == 1
    assert setups[0].entry_bar is not None
    assert setups[0].entry_bar.timestamp.astimezone(ET).hour == 10
    assert setups[0].entry_bar.timestamp.astimezone(ET).minute == 30
    gated = gate_setups(setups)
    assert gated[0][1] == "entry_cutoff"


def test_gate_allows_post_cutoff_when_configured():
    rng = build_opening_range([_b(0, 100, 104, 96, 101)], date(2026, 9, 11), orb_timeframe="15m")
    assert rng is not None
    signal = [
        _b(15, 101, 101.4, 100.6, 100.8),
        _b(50, 103.20, 104.00, 103.10, 103.80),
        _b(55, 103.70, 103.90, 102.50, 102.60),
        _b(60, 102.55, 102.70, 102.40, 102.50),
    ]
    setups = find_setups("AAPL", signal, rng)
    gated = gate_setups(setups, allow_entries_after_cutoff=True)
    assert gated[0][1] is None


def test_conftest_bar_helper_still_aligned_to_rth():
    # Guard: synthetic 15m index 0 is 9:30 ET on the shared fixture date.
    first = bar(0, 1, 1, 1, 1)
    assert first.timestamp == datetime(2026, 9, 11, 13, 30, tzinfo=timezone.utc)
