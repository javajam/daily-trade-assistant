from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from dta_bot.backtest import OpenLot, _mark_to_market, run_backtest, summarize
from dta_bot.config import ActionSpec, BotConfig, RuleSpec, Settings, SizeSpec, parse_condition
from dta_bot.models import Bar
from dta_bot.orb import ema_through
from tests.conftest import bar

NY = ZoneInfo("America/New_York")


def _cfg(*rules: RuleSpec, lookback: int = 80, **settings) -> BotConfig:
    return BotConfig(
        settings=Settings(lookback_bars=lookback, max_open_positions=5, **settings),
        universe=["AAPL"],
        rules=list(rules),
    )


def _et_bar(hour: int, minute: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(datetime(2026, 9, 11, hour, minute, tzinfo=NY), o, h, l, c, 1000)


def _buy_rule(**kwargs) -> RuleSpec:
    defaults = dict(
        id="engulf",
        symbols=["AAPL"],
        cooldown_minutes=60,
        when=parse_condition({"pattern": "bullish_engulfing", "timeframe": "15m"}),
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="shares", value=10),
            stop_loss_pct=1.5,
            take_profit_pct=3.0,
        ),
    )
    defaults.update(kwargs)
    return RuleSpec(**defaults)


def _close_rule(**kwargs) -> RuleSpec:
    defaults = dict(
        id="exit",
        symbols=["AAPL"],
        cooldown_minutes=30,
        when=parse_condition(
            {
                "any": [
                    {"pattern": "evening_star", "timeframe": "15m"},
                    {"pattern": "bearish_engulfing", "timeframe": "15m"},
                ]
            }
        ),
        action=ActionSpec(type="close"),
    )
    defaults.update(kwargs)
    return RuleSpec(**defaults)


def test_take_profit_round_trip():
    # bars 0,1 form engulfing; bar 2 is the fill and immediately tags +3% take.
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.4).timestamp, 8.1, 11.0, 8.0, 10.4, 1000),
        Bar(bar(2, 10.4, 10.72, 10.3, 10.5).timestamp, 10.4, 10.72, 10.3, 10.5, 1000),
    ]
    result = run_backtest(_cfg(_buy_rule()), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.signals == 1
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "take"
    assert trade.qty == 10
    assert trade.entry_price == 10.4
    assert trade.exit_price == 10.4 * 1.03  # take is 3% above signal close 10.4
    assert trade.pnl == 10 * (trade.exit_price - trade.entry_price)
    assert result.report.wins == 1
    assert result.report.total_pnl == trade.pnl


def test_stop_loss_round_trip():
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(2, 10.0, 10.1, 9.80, 9.90).timestamp, 10.0, 10.1, 9.80, 9.90, 1000),
    ]
    result = run_backtest(_cfg(_buy_rule()), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "stop"
    assert trade.entry_price == 10.0
    assert trade.exit_price == 10.0 * 0.985
    assert trade.pnl < 0
    assert result.report.losses == 1


def test_gap_through_stop_fills_at_open():
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(2, 9.70, 9.80, 9.60, 9.65).timestamp, 9.70, 9.80, 9.60, 9.65, 1000),
    ]
    result = run_backtest(_cfg(_buy_rule()), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    trade = result.trades[0]
    assert trade.exit_reason == "stop"
    assert trade.entry_price == 9.70
    assert trade.exit_price == 9.70  # gapped through 9.85 stop, both fills at open


def test_close_rule_exits_open_lot():
    # Engulfing entry, then a later bearish engulfing flatten (no stop/take hit).
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(2, 10.0, 10.2, 9.95, 10.1).timestamp, 10.0, 10.2, 9.95, 10.1, 1000),
        Bar(bar(3, 10.1, 10.25, 10.0, 10.2).timestamp, 10.1, 10.25, 10.0, 10.2, 1000),
        Bar(bar(4, 10.25, 10.28, 9.90, 9.95).timestamp, 10.25, 10.28, 9.90, 9.95, 1000),
        Bar(bar(5, 9.95, 10.00, 9.90, 9.92).timestamp, 9.95, 10.00, 9.90, 9.92, 1000),
    ]
    result = run_backtest(
        _cfg(_buy_rule(cooldown_minutes=0), _close_rule()),
        {("AAPL", "15Min"): bars},
        starting_equity=100_000,
    )
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "close_signal"
    assert trade.entry_price == 10.0
    assert trade.exit_price == 9.95


def test_exit_only_counts_signals_without_trades():
    bars = [
        Bar(bar(0, 8.0, 10.2, 7.9, 10.0).timestamp, 8.0, 10.2, 7.9, 10.0, 1000),
        Bar(bar(1, 10.1, 10.3, 7.5, 7.8).timestamp, 10.1, 10.3, 7.5, 7.8, 1000),
        Bar(bar(2, 7.8, 7.9, 7.6, 7.7).timestamp, 7.8, 7.9, 7.6, 7.7, 1000),
    ]
    result = run_backtest(_cfg(_close_rule()), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.signals == 1
    assert result.report.trades == 0
    assert result.signals[0].skip_reason == "no_position"
    assert result.report.total_pnl == 0
    assert result.report.win_rate_pct is None


def test_cooldown_blocks_second_entry():
    # Two engulfing pairs 15 minutes apart; 60m cooldown keeps the second from firing.
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(2, 10.0, 10.1, 9.9, 10.0).timestamp, 10.0, 10.1, 9.9, 10.0, 1000),
        Bar(bar(3, 10.0, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(4, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(5, 10.0, 10.4, 9.9, 10.2).timestamp, 10.0, 10.4, 9.9, 10.2, 1000),
    ]
    blocked = run_backtest(_cfg(_buy_rule(cooldown_minutes=60)), {("AAPL", "15Min"): bars})
    assert blocked.report.signals == 1
    open_cd = run_backtest(_cfg(_buy_rule(cooldown_minutes=0)), {("AAPL", "15Min"): bars}, allow_pyramid=True)
    assert open_cd.report.signals == 2


def test_percent_equity_sizing():
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 50.0).timestamp, 8.1, 11.0, 8.0, 50.0, 1000),
        Bar(bar(2, 50.0, 52.0, 49.6, 51.0).timestamp, 50.0, 52.0, 49.6, 51.0, 1000),
    ]
    rule = _buy_rule(
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="percent_equity", value=2),
            stop_loss_pct=1.0,
            take_profit_pct=2.0,
        )
    )
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    # 2% of 100k = 2000 / 50 = 40 shares; take 2% of signal 50 = 51, fill bar high 52.
    assert result.trades[0].qty == 40
    assert result.trades[0].exit_reason == "take"


def test_same_bar_stop_and_take_uses_stop():
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(2, 10.0, 10.40, 9.80, 10.1).timestamp, 10.0, 10.40, 9.80, 10.1, 1000),
    ]
    result = run_backtest(_cfg(_buy_rule()), {("AAPL", "15Min"): bars})
    assert result.trades[0].exit_reason == "stop"


def test_ema_invalid_exits_at_close_below_ema9():
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(12)]
    bars[-2] = Bar(bars[-2].timestamp, 10.0, 10.1, 9.9, 10.0, 1000)
    bars[-1] = Bar(bars[-1].timestamp, 10.0, 12.5, 9.9, 12.0, 1000)
    fill = Bar(bar(12, 12.0, 12.3, 11.8, 12.1).timestamp, 12.0, 12.3, 11.8, 12.1, 1000)
    drop = Bar(bar(13, 12.1, 12.2, 9.4, 9.5).timestamp, 12.1, 12.2, 9.4, 9.5, 1000)
    rule = _buy_rule(
        id="ema9",
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
        action=ActionSpec(type="buy", size=SizeSpec(type="shares", value=10), exit="ema_invalid"),
    )
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): bars + [fill, drop]}, starting_equity=100_000)
    assert result.report.signals == 1
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "ema_invalid"
    assert trade.entry_price == 12.0
    assert trade.exit_price == 9.5
    assert result.report.exit_reasons == {"ema_invalid": 1}


def test_ema_invalid_does_not_exit_when_close_equals_or_holds_above_ema():
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(12)]
    bars[-2] = Bar(bars[-2].timestamp, 10.0, 10.1, 9.9, 10.0, 1000)
    bars[-1] = Bar(bars[-1].timestamp, 10.0, 12.5, 9.9, 12.0, 1000)
    hold = [
        Bar(bar(12 + i, 12.0, 12.2, 11.9, 12.05).timestamp, 12.0, 12.2, 11.9, 12.05, 1000)
        for i in range(3)
    ]
    rule = _buy_rule(
        id="ema9",
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
        action=ActionSpec(type="buy", size=SizeSpec(type="shares", value=10), exit="ema_invalid"),
    )
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): bars + hold}, starting_equity=100_000)
    assert result.report.trades == 1
    assert result.trades[0].exit_reason == "eod"
    assert result.trades[0].exit_price == 12.05


def test_ema_invalid_optional_stop_still_fires_first():
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(12)]
    bars[-2] = Bar(bars[-2].timestamp, 10.0, 10.1, 9.9, 10.0, 1000)
    bars[-1] = Bar(bars[-1].timestamp, 10.0, 12.5, 9.9, 12.0, 1000)
    fill = Bar(bar(12, 12.0, 12.1, 11.5, 11.6).timestamp, 12.0, 12.1, 11.5, 11.6, 1000)
    rule = _buy_rule(
        id="ema9",
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="shares", value=10),
            exit="ema_invalid",
            stop_loss_pct=2.0,
        ),
    )
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): bars + [fill]}, starting_equity=100_000)
    assert result.trades[0].exit_reason == "stop"
    assert result.trades[0].exit_price == pytest.approx(12.0 * 0.98)


def test_ema_cross_entry_takes_profit():
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(12)]
    bars[-2] = Bar(bars[-2].timestamp, 10.0, 10.1, 9.9, 10.0, 1000)
    bars[-1] = Bar(bars[-1].timestamp, 10.0, 12.5, 9.9, 12.0, 1000)
    fill = Bar(bar(12, 12.0, 12.5, 11.9, 12.2).timestamp, 12.0, 12.5, 11.9, 12.2, 1000)
    rule = _buy_rule(
        id="ema9",
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
    )
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): bars + [fill]}, starting_equity=100_000)
    assert result.report.signals == 1
    assert result.report.trades == 1
    assert result.trades[0].exit_reason == "take"
    assert "ema_cross matched" in result.signals[0].reason


def test_unused_series_do_not_widen_period():
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.4).timestamp, 8.1, 11.0, 8.0, 10.4, 1000),
        Bar(bar(2, 10.4, 10.72, 10.3, 10.5).timestamp, 10.4, 10.72, 10.3, 10.5, 1000),
    ]
    leftover = Bar(datetime(2020, 1, 1, tzinfo=timezone.utc), 1, 1, 1, 1, 1)
    result = run_backtest(
        _cfg(_buy_rule()),
        {("AAPL", "15Min"): bars, ("SPY", "1Hour"): [leftover]},
        starting_equity=100_000,
    )
    assert result.report.period_start.startswith("2026-09-11")
    assert "SPY:1Hour" not in result.bars_used


def test_summarize_handles_empty_book():
    report = summarize(
        label="empty",
        starting_equity=100_000,
        ending_equity=100_000,
        trades=[],
        signals=[],
        equity_curve=[(datetime(2026, 1, 1, tzinfo=timezone.utc), 100_000.0)],
        period_start=None,
        period_end=None,
        data_source="fixture",
    )
    assert report.trades == 0
    assert report.win_rate_pct is None
    assert report.avg_win is None
    assert report.max_drawdown == 0


def _lot(side: str, entry: float, qty: float = 10) -> OpenLot:
    ts = datetime(2026, 9, 11, 14, 0, tzinfo=timezone.utc)
    return OpenLot(
        rule_id="orb_reversal",
        symbol="AAPL",
        qty=qty,
        side=side,
        entry_time=ts,
        entry_price=entry,
        stop=None,
        take=None,
        signal_time=ts,
        tf="5Min",
    )


def test_short_mark_to_market_does_not_double_count_proceeds():
    # Short 10 @ 300: cash already includes +3000 proceeds.
    cash = 100_000.0 + 10 * 300.0
    lot = _lot("sell", 300.0)
    assert _mark_to_market(cash, [lot], {"AAPL": 300.0}) == 100_000.0
    assert _mark_to_market(cash, [lot], {"AAPL": 310.0}) == 99_900.0
    assert _mark_to_market(cash, [lot], {"AAPL": 290.0}) == 100_100.0


def test_long_mark_to_market_still_adds_inventory():
    cash = 100_000.0 - 10 * 300.0
    lot = _lot("buy", 300.0)
    assert _mark_to_market(cash, [lot], {"AAPL": 300.0}) == 100_000.0
    assert _mark_to_market(cash, [lot], {"AAPL": 310.0}) == 100_100.0


def _engulf_at_200() -> list[Bar]:
    # prev bearish 210→200, curr bullish 199→212 (engulfs). Signal close 212.
    return [
        Bar(bar(0, 210, 211.0, 199.0, 200.0).timestamp, 210.0, 211.0, 199.0, 200.0, 1000),
        Bar(bar(1, 199, 220.0, 198.0, 212.0).timestamp, 199.0, 220.0, 198.0, 212.0, 1000),
        Bar(bar(2, 212.0, 220.0, 210.0, 213.0).timestamp, 212.0, 220.0, 210.0, 213.0, 1000),
    ]


def test_risk_pct_sizes_from_equity_each_entry():
    rule = _buy_rule(
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="risk_pct", equity_risk=0.01, stop_pct=1.5),
            stop_loss_pct=1.5,
            take_profit_pct=3.0,
        )
    )
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): _engulf_at_200()}, starting_equity=100_000)
    # floor(100000 / (1.5 * 212)) = 314
    assert result.trades[0].qty == 314
    assert result.trades[0].exit_reason == "take"
    assert result.period_stats is not None
    assert result.period_stats["monthly"]["trades"] == 1


def test_second_symbol_skips_when_cash_cannot_cover_risk_size():
    rule = _buy_rule(
        symbols=["AAPL", "MSFT"],
        action=ActionSpec(
            type="buy",
            size=SizeSpec(type="risk_pct", equity_risk=0.01, stop_pct=1.5),
            stop_loss_pct=1.5,
            take_profit_pct=3.0,
        ),
    )
    cfg = BotConfig(
        settings=Settings(lookback_bars=80, max_open_positions=5),
        universe=["AAPL", "MSFT"],
        rules=[rule],
    )
    bars = _engulf_at_200()
    result = run_backtest(
        cfg,
        {("AAPL", "15Min"): bars, ("MSFT", "15Min"): list(bars)},
        starting_equity=100_000,
    )
    accepted = [s for s in result.signals if s.accepted]
    skipped = [s for s in result.signals if s.skip_reason == "insufficient_cash"]
    assert len(accepted) == 1
    assert accepted[0].symbol == "AAPL"
    assert len(skipped) == 1
    assert skipped[0].symbol == "MSFT"
    assert [t.symbol for t in result.trades] == ["AAPL"]


def test_trade_window_blocks_entries_before_start():
    start = datetime(2026, 9, 11, 14, 0, 1, tzinfo=timezone.utc)
    result = run_backtest(
        _cfg(_buy_rule()),
        {("AAPL", "15Min"): _engulf_at_200()},
        starting_equity=100_000,
        trade_start=start,
    )
    assert result.report.signals == 0
    assert result.report.trades == 0


def _session_cfg(*, gates: bool = True, cutoff: str = "12:00", tf: str = "15m") -> BotConfig:
    settings = dict(entry_cutoff=cutoff, flatten_by="15:55") if gates else dict(
        entry_cutoff=None, flatten_by=None
    )
    return _cfg(_buy_rule(cooldown_minutes=0), **settings)


def test_entry_cutoff_skips_fill_at_or_after_1300_et():
    # Engulfing completes on the 12:45 ET bar (closes 13:00); next open is 13:00.
    bars = [
        _et_bar(12, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(12, 45, 8.1, 11.0, 8.0, 10.4),
        _et_bar(13, 0, 10.4, 10.5, 10.3, 10.45),
    ]
    result = run_backtest(
        _session_cfg(cutoff="13:00"), {("AAPL", "15Min"): bars}, starting_equity=100_000
    )
    assert result.report.signals == 1
    assert result.signals[0].accepted is False
    assert result.signals[0].skip_reason == "entry_cutoff"
    assert result.report.trades == 0
    assert result.report.skip_reasons == {"entry_cutoff": 1}


def test_entry_cutoff_allows_fill_before_1300_et():
    # Engulfing completes on the 12:30 ET bar (closes 12:45); fill at 12:45 open.
    bars = [
        _et_bar(12, 15, 10.0, 10.2, 8.0, 8.2),
        _et_bar(12, 30, 8.1, 11.0, 8.0, 10.4),
        _et_bar(12, 45, 10.4, 10.72, 10.3, 10.5),
        _et_bar(13, 0, 10.5, 10.6, 10.4, 10.55),
    ]
    result = run_backtest(
        _session_cfg(cutoff="13:00"), {("AAPL", "15Min"): bars}, starting_equity=100_000
    )
    assert result.report.signals == 1
    assert result.signals[0].accepted is True
    assert result.report.trades == 1
    assert result.trades[0].entry_time == datetime(2026, 9, 11, 12, 45, tzinfo=NY)


def test_entry_cutoff_skips_fill_at_or_after_1200_et():
    # Engulfing completes on the 11:45 ET bar (closes 12:00); next open is 12:00.
    bars = [
        _et_bar(11, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(11, 45, 8.1, 11.0, 8.0, 10.4),
        _et_bar(12, 0, 10.4, 10.5, 10.3, 10.45),
    ]
    result = run_backtest(_session_cfg(), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.signals == 1
    assert result.signals[0].accepted is False
    assert result.signals[0].skip_reason == "entry_cutoff"
    assert result.report.trades == 0
    assert result.report.skip_reasons == {"entry_cutoff": 1}


def test_entry_cutoff_allows_fill_before_1200_et():
    # Engulfing completes on the 11:30 ET bar (closes 11:45); fill at 11:45 open.
    bars = [
        _et_bar(11, 15, 10.0, 10.2, 8.0, 8.2),
        _et_bar(11, 30, 8.1, 11.0, 8.0, 10.4),
        _et_bar(11, 45, 10.4, 10.72, 10.3, 10.5),
        _et_bar(12, 0, 10.5, 10.6, 10.4, 10.55),
    ]
    result = run_backtest(_session_cfg(), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.signals == 1
    assert result.signals[0].accepted is True
    assert result.report.trades == 1
    assert result.trades[0].entry_time == datetime(2026, 9, 11, 11, 45, tzinfo=NY)


def test_entry_cutoff_skips_fill_at_or_after_1515_et():
    # Engulfing completes on the 15:00 ET bar (closes 15:15); next open is 15:15.
    bars = [
        _et_bar(14, 45, 10.0, 10.2, 8.0, 8.2),
        _et_bar(15, 0, 8.1, 11.0, 8.0, 10.4),
        _et_bar(15, 15, 10.4, 10.5, 10.3, 10.45),
    ]
    result = run_backtest(
        _session_cfg(cutoff="15:15"), {("AAPL", "15Min"): bars}, starting_equity=100_000
    )
    assert result.report.signals == 1
    assert result.signals[0].accepted is False
    assert result.signals[0].skip_reason == "entry_cutoff"
    assert result.report.trades == 0
    assert result.report.skip_reasons == {"entry_cutoff": 1}


def test_entry_cutoff_allows_fill_before_1515_et():
    # Engulfing completes on the 14:45 ET bar (closes 15:00); fill at 15:00 open.
    bars = [
        _et_bar(14, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(14, 45, 8.1, 11.0, 8.0, 10.4),
        _et_bar(15, 0, 10.4, 10.72, 10.3, 10.5),
        _et_bar(15, 15, 10.5, 10.6, 10.4, 10.55),
    ]
    result = run_backtest(
        _session_cfg(cutoff="15:15"), {("AAPL", "15Min"): bars}, starting_equity=100_000
    )
    assert result.report.signals == 1
    assert result.signals[0].accepted is True
    assert result.report.trades == 1
    assert result.trades[0].entry_time == datetime(2026, 9, 11, 15, 0, tzinfo=NY)


def test_flatten_by_closes_15m_at_1545_bar_close():
    # Enter 10:00, no stop/take, hold into the 15:45 bar → session_flatten at that close.
    bars = [
        _et_bar(9, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(9, 45, 8.1, 11.0, 8.0, 10.0),
        _et_bar(10, 0, 10.0, 10.1, 9.95, 10.05),
    ]
    t = datetime(2026, 9, 11, 10, 15, tzinfo=NY)
    while t <= datetime(2026, 9, 11, 15, 45, tzinfo=NY):
        bars.append(_et_bar(t.hour, t.minute, 10.05, 10.10, 10.00, 10.06))
        t = t.replace(hour=t.hour + (t.minute + 15) // 60, minute=(t.minute + 15) % 60)
    result = run_backtest(_session_cfg(), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "session_flatten"
    assert trade.exit_price == 10.06
    assert trade.exit_time == datetime(2026, 9, 11, 16, 0, tzinfo=NY)
    assert result.report.exit_reasons == {"session_flatten": 1}


def test_flatten_by_closes_5m_at_1550_bar_close():
    bars = [
        _et_bar(9, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(9, 35, 8.1, 11.0, 8.0, 10.0),
        _et_bar(9, 40, 10.0, 10.1, 9.95, 10.05),
    ]
    t = datetime(2026, 9, 11, 9, 45, tzinfo=NY)
    end = datetime(2026, 9, 11, 15, 55, tzinfo=NY)
    while t <= end:
        bars.append(_et_bar(t.hour, t.minute, 10.05, 10.10, 10.00, 10.06))
        nxt_min = t.minute + 5
        t = t.replace(hour=t.hour + nxt_min // 60, minute=nxt_min % 60)
    rule = _buy_rule(
        cooldown_minutes=0,
        when=parse_condition({"pattern": "bullish_engulfing", "timeframe": "5m"}),
    )
    cfg = _cfg(rule, entry_cutoff="13:00", flatten_by="15:55")
    result = run_backtest(cfg, {("AAPL", "5Min"): bars}, starting_equity=100_000)
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "session_flatten"
    assert trade.exit_time == datetime(2026, 9, 11, 15, 55, tzinfo=NY)
    assert trade.exit_price == 10.06


def test_overnight_book_holds_past_flatten_bar():
    bars = [
        _et_bar(9, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(9, 45, 8.1, 11.0, 8.0, 10.0),
        _et_bar(10, 0, 10.0, 10.1, 9.95, 10.05),
        _et_bar(15, 45, 10.05, 10.10, 10.00, 10.20),
    ]
    result = run_backtest(_session_cfg(gates=False), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.trades == 1
    assert result.trades[0].exit_reason == "eod"
    assert result.trades[0].exit_price == 10.20


def _ema_cross_warmup() -> list[Bar]:
    bars = [bar(i, 10.0, 10.1, 9.9, 10.0) for i in range(12)]
    bars[-2] = Bar(bars[-2].timestamp, 10.0, 10.1, 9.9, 10.0, 1000)
    bars[-1] = Bar(bars[-1].timestamp, 10.0, 12.5, 9.9, 12.0, 1000)
    return bars


def _be_rule(**action_kw) -> RuleSpec:
    defaults = dict(
        type="buy",
        size=SizeSpec(type="shares", value=10),
        stop_loss_pct=1.5,
        take_profit_pct=3.0,
        breakeven_after_bars=1,
        breakeven_requires_valid=True,
        breakeven_valid="above_ema",
    )
    defaults.update(action_kw)
    return _buy_rule(
        id="ema9",
        when=parse_condition({"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bullish"}}),
        action=ActionSpec(**defaults),
    )


def test_breakeven_moves_stop_to_entry_after_one_complete_bar():
    # Fill at bar 12 open 12.0. Confirm bar 13 closes above EMA9 → arm BE.
    # Bar 14 tags the entry stop. Same-bar low at entry on the confirm bar
    # must not fire because BE is armed only at that close.
    warmup = _ema_cross_warmup()
    fill = Bar(bar(12, 12.0, 12.2, 11.95, 12.1).timestamp, 12.0, 12.2, 11.95, 12.1, 1000)
    confirm = Bar(bar(13, 12.1, 12.25, 12.0, 12.15).timestamp, 12.1, 12.25, 12.0, 12.15, 1000)
    hit = Bar(bar(14, 12.15, 12.2, 11.90, 12.00).timestamp, 12.15, 12.2, 11.90, 12.00, 1000)
    result = run_backtest(_cfg(_be_rule()), {("AAPL", "15Min"): warmup + [fill, confirm, hit]})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 12.0
    assert trade.exit_reason == "breakeven_stop"
    assert trade.exit_price == 12.0
    assert trade.pnl == 0.0
    assert trade.breakeven_armed is True
    assert result.report.breakeven_armed == 1
    assert result.report.exit_reasons == {"breakeven_stop": 1}
    assert ema_through(warmup + [fill, confirm], confirm, 9) < confirm.close


def test_breakeven_does_not_arm_on_the_entry_bar():
    warmup = _ema_cross_warmup()
    fill = Bar(bar(12, 12.0, 12.2, 11.95, 12.1).timestamp, 12.0, 12.2, 11.95, 12.1, 1000)
    # If BE armed at fill close, this confirm low at 12.0 would stop out.
    confirm = Bar(bar(13, 12.1, 12.2, 12.0, 12.15).timestamp, 12.1, 12.2, 12.0, 12.15, 1000)
    result = run_backtest(_cfg(_be_rule()), {("AAPL", "15Min"): warmup + [fill, confirm]})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "eod"
    assert trade.breakeven_armed is True
    assert trade.exit_price == 12.15


def test_breakeven_leaves_original_stop_when_confirm_close_not_above_ema():
    warmup = [bar(i, 100.0, 100.2, 99.8, 100.0) for i in range(20)]
    warmup[-2] = Bar(warmup[-2].timestamp, 100.0, 100.2, 99.4, 99.5, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 99.5, 102.0, 99.4, 101.0, 1000)
    fill = Bar(bar(20, 101.0, 101.5, 100.8, 101.2).timestamp, 101.0, 101.5, 100.8, 101.2, 1000)
    ema_at_fill = ema_through(warmup + [fill], fill, 9)
    assert ema_at_fill is not None
    stop = 101.0 * 0.985
    confirm_close = min(ema_at_fill - 0.05, (stop + ema_at_fill) / 2)
    assert stop < confirm_close < ema_at_fill
    confirm = Bar(
        bar(21, 101.2, 101.3, confirm_close - 0.02, confirm_close).timestamp,
        101.2,
        101.3,
        confirm_close - 0.02,
        confirm_close,
        1000,
    )
    hit = Bar(bar(22, confirm_close, 101.0, 99.40, 99.50).timestamp, confirm_close, 101.0, 99.40, 99.50, 1000)
    result = run_backtest(
        _cfg(_be_rule()),
        {("AAPL", "15Min"): warmup + [fill, confirm, hit]},
    )
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.breakeven_armed is False
    assert trade.exit_reason == "stop"
    assert trade.exit_price == pytest.approx(stop)
    assert result.report.breakeven_armed == 0


def test_breakeven_always_arms_when_requires_valid_is_false():
    warmup = [bar(i, 100.0, 100.2, 99.8, 100.0) for i in range(20)]
    warmup[-2] = Bar(warmup[-2].timestamp, 100.0, 100.2, 99.4, 99.5, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 99.5, 102.0, 99.4, 101.0, 1000)
    fill = Bar(bar(20, 101.0, 101.5, 100.8, 101.2).timestamp, 101.0, 101.5, 100.8, 101.2, 1000)
    ema_at_fill = ema_through(warmup + [fill], fill, 9)
    assert ema_at_fill is not None
    confirm_close = ema_at_fill - 0.10
    confirm = Bar(
        bar(21, 101.2, 101.3, confirm_close, confirm_close).timestamp,
        101.2,
        101.3,
        confirm_close,
        confirm_close,
        1000,
    )
    hit = Bar(bar(22, 101.1, 101.2, 100.90, 101.0).timestamp, 101.1, 101.2, 100.90, 101.0, 1000)
    result = run_backtest(
        _cfg(_be_rule(breakeven_requires_valid=False)),
        {("AAPL", "15Min"): warmup + [fill, confirm, hit]},
    )
    trade = result.trades[0]
    assert trade.breakeven_armed is True
    assert trade.exit_reason == "breakeven_stop"
    assert trade.exit_price == 101.0


def test_breakeven_off_keeps_original_percent_stop():
    warmup = _ema_cross_warmup()
    fill = Bar(bar(12, 12.0, 12.2, 11.95, 12.1).timestamp, 12.0, 12.2, 11.95, 12.1, 1000)
    confirm = Bar(bar(13, 12.1, 12.25, 12.0, 12.15).timestamp, 12.1, 12.25, 12.0, 12.15, 1000)
    hit = Bar(bar(14, 12.15, 12.2, 11.80, 11.85).timestamp, 12.15, 12.2, 11.80, 11.85, 1000)
    result = run_backtest(
        _cfg(_be_rule(breakeven_after_bars=0)),
        {("AAPL", "15Min"): warmup + [fill, confirm, hit]},
    )
    trade = result.trades[0]
    assert trade.breakeven_armed is False
    assert trade.exit_reason == "stop"
    assert trade.exit_price == pytest.approx(12.0 * 0.985)


def test_stop_on_flatten_bar_beats_session_flatten():
    bars = [
        _et_bar(9, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(9, 45, 8.1, 11.0, 8.0, 10.0),
        _et_bar(10, 0, 10.0, 10.1, 9.95, 10.05),
        _et_bar(15, 45, 10.05, 10.10, 9.70, 9.80),
    ]
    result = run_backtest(_session_cfg(), {("AAPL", "15Min"): bars}, starting_equity=100_000)
    assert result.report.trades == 1
    assert result.trades[0].exit_reason == "stop"


def _pair_cross_warmup() -> list[Bar]:
    bars = [bar(i, 100.0, 100.1, 99.9, 100.0) for i in range(20)]
    bars.append(bar(20, 100.0, 100.6, 99.9, 100.5))
    return bars


def _ma_cross_rule(**action_kw) -> RuleSpec:
    defaults = dict(
        type="buy",
        size=SizeSpec(type="shares", value=10),
        exit="ma_cross",
        exit_ema_period=9,
        exit_sma_period=20,
        stop_loss_pct=1.5,
    )
    defaults.update(action_kw)
    return _buy_rule(
        id="ema9",
        when=parse_condition(
            {"ema_sma_cross": {"ema_period": 9, "sma_period": 20, "timeframe": "15m", "direction": "bullish"}}
        ),
        action=ActionSpec(**defaults),
    )


def test_ema_sma_cross_up_enters_at_next_open():
    warmup = _pair_cross_warmup()
    fill = Bar(bar(21, 100.5, 100.8, 100.4, 100.5).timestamp, 100.5, 100.8, 100.4, 100.5, 1000)
    result = run_backtest(_cfg(_ma_cross_rule()), {("AAPL", "15Min"): warmup + [fill]})
    assert result.report.signals == 1
    assert "ema_sma_cross matched (bullish)" in result.signals[0].reason
    assert result.report.trades == 1
    assert result.trades[0].entry_price == 100.5
    assert result.trades[0].exit_reason == "eod"


def test_ema_sma_cross_down_exits_at_next_open():
    # Cross-up on bar 20 (close 100.5) → fill bar 21 open 100.5.
    # Bar 22 close 99.2 crosses EMA9 under SMA20; low stays above the 1.5% stop.
    # Flatten at bar 23 open 99.15.
    warmup = _pair_cross_warmup()
    fill = Bar(bar(21, 100.5, 100.7, 100.4, 100.5).timestamp, 100.5, 100.7, 100.4, 100.5, 1000)
    cross_under = Bar(bar(22, 100.5, 100.6, 99.2, 99.2).timestamp, 100.5, 100.6, 99.2, 99.2, 1000)
    exit_bar = Bar(bar(23, 99.15, 99.3, 99.1, 99.2).timestamp, 99.15, 99.3, 99.1, 99.2, 1000)
    result = run_backtest(
        _cfg(_ma_cross_rule()),
        {("AAPL", "15Min"): warmup + [fill, cross_under, exit_bar]},
    )
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 100.5
    assert trade.exit_reason == "ma_cross"
    assert trade.exit_price == 99.15
    assert result.report.exit_reasons == {"ma_cross": 1}
    assert any("Exit P&L" in n and "ma_cross" in n for n in result.report.notes)


def test_ema_sma_cross_rsi_filter_blocks_high_rsi_entry():
    warmup = _pair_cross_warmup()
    fill = Bar(bar(21, 100.5, 100.8, 100.4, 100.5).timestamp, 100.5, 100.8, 100.4, 100.5, 1000)
    rule = _buy_rule(
        id="ema9",
        when=parse_condition(
            {
                "ema_sma_cross": {
                    "ema_period": 9,
                    "sma_period": 20,
                    "timeframe": "15m",
                    "direction": "bullish",
                },
                "rsi": {"period": 14, "below": 70},
            }
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
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): warmup + [fill]})
    assert result.report.signals == 0
    assert result.report.trades == 0


def _short_price_cross_rule(**action_kw) -> RuleSpec:
    defaults = dict(
        type="sell",
        size=SizeSpec(type="shares", value=10),
        exit="ma_cross",
        exit_ema_period=9,
        exit_sma_period=20,
        stop_loss_pct=50.0,
    )
    defaults.update(action_kw)
    return _buy_rule(
        id="ema9_trend_short",
        when=parse_condition(
            {
                "all": [
                    {"ema_cross": {"period": 9, "timeframe": "15m", "direction": "bearish"}},
                    {"sma": {"period": 20, "timeframe": "15m", "compare": "below"}},
                ]
            }
        ),
        action=ActionSpec(**defaults),
    )


def test_short_ma_cross_cover_exits_at_next_open():
    # 20 flats at 100 seed both MAs. Bar 20 close 99 is a bearish price-cross
    # below SMA20 (no RSI). Fill short at bar 21 open 99. Bar 21 stays soft
    # (close 98.5 — EMA still under SMA). Bar 22 close 102 lifts EMA over SMA;
    # wide stop so the cover, not the 1% lock, is what fires. Flatten at bar 23 open.
    warmup = [bar(i, 100.0, 100.1, 99.9, 100.0) for i in range(20)]
    signal = Bar(bar(20, 100.0, 100.1, 98.8, 99.0).timestamp, 100.0, 100.1, 98.8, 99.0, 1000)
    fill = Bar(bar(21, 99.0, 99.2, 98.4, 98.5).timestamp, 99.0, 99.2, 98.4, 98.5, 1000)
    cross_over = Bar(bar(22, 98.5, 102.2, 98.4, 102.0).timestamp, 98.5, 102.2, 98.4, 102.0, 1000)
    cover = Bar(bar(23, 101.80, 102.0, 101.6, 101.9).timestamp, 101.80, 102.0, 101.6, 101.9, 1000)
    result = run_backtest(
        _cfg(_short_price_cross_rule()),
        {("AAPL", "15Min"): warmup + [signal, fill, cross_over, cover]},
    )
    assert result.report.signals == 1
    assert "ema_cross matched (bearish)" in result.signals[0].reason
    assert "RSI14" not in result.signals[0].reason
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.side == "sell"
    assert trade.entry_price == 99.0
    assert trade.exit_reason == "ma_cross"
    assert trade.exit_price == 101.80
    assert result.report.exit_reasons == {"ma_cross": 1}
    assert any("cross-over / cover" in n for n in result.report.notes)


def test_short_stop_beats_ma_cross_cover_on_same_bar():
    warmup = [bar(i, 100.0, 100.1, 99.9, 100.0) for i in range(20)]
    signal = Bar(bar(20, 100.0, 100.1, 98.8, 99.0).timestamp, 100.0, 100.1, 98.8, 99.0, 1000)
    fill = Bar(bar(21, 99.0, 99.2, 98.4, 98.5).timestamp, 99.0, 99.2, 98.4, 98.5, 1000)
    # High tags fill×1.01 (99.99) and close 102 would also be a bullish pair-cross.
    squeeze = Bar(bar(22, 98.5, 102.2, 98.4, 102.0).timestamp, 98.5, 102.2, 98.4, 102.0, 1000)
    after = Bar(bar(23, 101.80, 102.0, 101.6, 101.9).timestamp, 101.80, 102.0, 101.6, 101.9, 1000)
    result = run_backtest(
        _cfg(_short_price_cross_rule(stop_loss_pct=1.0, stop_mode="lock_plus")),
        {("AAPL", "15Min"): warmup + [signal, fill, squeeze, after]},
    )
    assert result.trades[0].side == "sell"
    assert result.trades[0].exit_reason == "stop"
    assert result.trades[0].exit_price == pytest.approx(99.0 * 1.01)


def test_ema_sma_cross_stop_beats_cross_under_on_same_bar():
    warmup = _pair_cross_warmup()
    fill = Bar(bar(21, 100.5, 100.7, 100.4, 100.5).timestamp, 100.5, 100.7, 100.4, 100.5, 1000)
    # Low tags the 1.5% stop (98.9925) and close 99.2 would also be a pair-cross.
    drop = Bar(bar(22, 100.5, 100.6, 98.5, 99.2).timestamp, 100.5, 100.6, 98.5, 99.2, 1000)
    after = Bar(bar(23, 99.2, 99.3, 99.1, 99.2).timestamp, 99.2, 99.3, 99.1, 99.2, 1000)
    result = run_backtest(
        _cfg(_ma_cross_rule()),
        {("AAPL", "15Min"): warmup + [fill, drop, after]},
    )
    assert result.trades[0].exit_reason == "stop"
    assert result.trades[0].exit_price == pytest.approx(100.5 * 0.985)


def _sma20_warmup(close: float = 100.0) -> list[Bar]:
    return [bar(i, close, close + 0.1, close - 0.1, close) for i in range(20)]


def _sma20_rule(**action_kw) -> RuleSpec:
    defaults = dict(
        type="buy",
        size=SizeSpec(type="shares", value=10),
        exit="fixed_bracket",
        stop_mode="sma20",
        stop_sma_period=20,
        take_profit_pct=2.0,
    )
    defaults.update(action_kw)
    return _buy_rule(action=ActionSpec(**defaults))


def test_sma20_stop_fills_at_signal_bar_sma():
    # 20 bars @ 100, then engulfing close 101 → SMA20 = (19*100 + 101) / 20 = 100.05
    warmup = _sma20_warmup()
    warmup[-2] = Bar(warmup[-2].timestamp, 100.0, 100.2, 8.0, 8.2, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 8.1, 102.0, 8.0, 101.0, 1000)
    from dta_bot.indicators import sma as _sma

    signal_sma = _sma([b.close for b in warmup], 20)
    assert signal_sma is not None
    assert signal_sma < 101.0
    fill = Bar(bar(20, 101.0, 101.2, 100.8, 101.1).timestamp, 101.0, 101.2, 100.8, 101.1, 1000)
    hit = Bar(bar(21, 101.1, 101.2, signal_sma - 0.20, 100.5).timestamp, 101.1, 101.2, signal_sma - 0.20, 100.5, 1000)
    result = run_backtest(_cfg(_sma20_rule()), {("AAPL", "15Min"): warmup + [fill, hit]})
    assert result.report.signals == 1
    assert result.signals[0].accepted is True
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "stop"
    assert trade.exit_price == pytest.approx(signal_sma)
    assert trade.entry_price == 101.0
    assert any("stop_mode: sma20" in n for n in result.report.notes)


def test_sma20_stop_skips_when_sma_above_signal_close():
    # Flat 110s, then a lower engulfing (close 102.5) — SMA20 stays ~109, above the close.
    warmup = _sma20_warmup(110.0)
    warmup[-2] = Bar(warmup[-2].timestamp, 102.0, 102.2, 99.0, 99.2, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 99.1, 103.0, 98.0, 102.5, 1000)
    from dta_bot.indicators import sma as _sma

    signal_sma = _sma([b.close for b in warmup], 20)
    assert signal_sma is not None and signal_sma > 102.5
    fill = Bar(bar(20, 102.5, 103.0, 102.0, 102.6).timestamp, 102.5, 103.0, 102.0, 102.6, 1000)
    result = run_backtest(_cfg(_sma20_rule()), {("AAPL", "15Min"): warmup + [fill]})
    assert result.report.signals == 1
    assert result.signals[0].accepted is False
    assert result.signals[0].skip_reason == "sma20_above_entry"
    assert result.report.trades == 0


def test_sma20_stop_skips_fill_when_open_at_or_below_sma():
    warmup = _sma20_warmup()
    warmup[-2] = Bar(warmup[-2].timestamp, 100.0, 100.2, 8.0, 8.2, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 8.1, 102.0, 8.0, 101.0, 1000)
    from dta_bot.indicators import sma as _sma

    signal_sma = _sma([b.close for b in warmup], 20)
    assert signal_sma is not None
    # Next open gaps through the SMA20 stop — skip rather than enter already stopped.
    fill = Bar(
        bar(20, signal_sma - 0.10, signal_sma + 0.20, signal_sma - 0.20, signal_sma).timestamp,
        signal_sma - 0.10,
        signal_sma + 0.20,
        signal_sma - 0.20,
        signal_sma,
        1000,
    )
    result = run_backtest(_cfg(_sma20_rule()), {("AAPL", "15Min"): warmup + [fill]})
    assert result.report.signals == 1
    assert result.signals[0].accepted is True
    assert result.report.trades == 0
    assert any("skipped at fill because SMA20" in n for n in result.report.notes)


def test_sma20_stop_keeps_percent_take():
    warmup = _sma20_warmup()
    warmup[-2] = Bar(warmup[-2].timestamp, 100.0, 100.2, 8.0, 8.2, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 8.1, 102.0, 8.0, 101.0, 1000)
    fill = Bar(bar(20, 101.0, 103.10, 100.9, 102.5).timestamp, 101.0, 103.10, 100.9, 102.5, 1000)
    result = run_backtest(_cfg(_sma20_rule()), {("AAPL", "15Min"): warmup + [fill]})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "take"
    assert trade.exit_price == pytest.approx(101.0 * 1.02)


def test_sma20_stop_without_take_holds_to_eod():
    warmup = _sma20_warmup()
    warmup[-2] = Bar(warmup[-2].timestamp, 100.0, 100.2, 8.0, 8.2, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 8.1, 102.0, 8.0, 101.0, 1000)
    from dta_bot.indicators import sma as _sma

    signal_sma = _sma([b.close for b in warmup], 20)
    fill = Bar(bar(20, 101.0, 101.5, signal_sma + 0.10, 101.2).timestamp, 101.0, 101.5, signal_sma + 0.10, 101.2, 1000)
    result = run_backtest(
        _cfg(_sma20_rule(take_profit_pct=None)),
        {("AAPL", "15Min"): warmup + [fill]},
    )
    assert result.report.trades == 1
    assert result.trades[0].exit_reason == "eod"
    assert result.trades[0].exit_price == 101.2


def test_sma20_risk_pct_sizes_from_entry_to_sma():
    warmup = _sma20_warmup()
    warmup[-2] = Bar(warmup[-2].timestamp, 100.0, 100.2, 8.0, 8.2, 1000)
    warmup[-1] = Bar(warmup[-1].timestamp, 8.1, 102.0, 8.0, 101.0, 1000)
    from dta_bot.indicators import sma as _sma

    signal_sma = _sma([b.close for b in warmup], 20)
    assert signal_sma is not None
    r = 101.0 - signal_sma
    expected = int(1000.0 // r)
    fill = Bar(bar(20, 101.0, 101.2, signal_sma + 0.10, 101.1).timestamp, 101.0, 101.2, signal_sma + 0.10, 101.1, 1000)
    rule = _sma20_rule(
        size=SizeSpec(type="risk_pct", equity_risk=0.01),
        take_profit_pct=None,
    )
    result = run_backtest(_cfg(rule), {("AAPL", "15Min"): warmup + [fill]}, starting_equity=100_000)
    assert result.report.trades == 1
    assert result.trades[0].qty == expected


def _manage_rule(**action_kw) -> RuleSpec:
    defaults = dict(
        type="buy",
        size=SizeSpec(type="shares", value=10),
        exit="fixed_bracket",
        stop_mode="entry_pct",
        stop_loss_pct=1.0,
    )
    defaults.update(action_kw)
    return _buy_rule(action=ActionSpec(**defaults))


def test_entry_pct_stop_uses_fill_not_signal_close():
    # Signal close 10.0; next open gaps to 10.20. Entry stop = 10.20*0.99 = 10.098.
    # A 10.09 low hits the fill stop but would miss a signal-close 9.90 stop.
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(2, 10.20, 10.25, 10.15, 10.22).timestamp, 10.20, 10.25, 10.15, 10.22, 1000),
        Bar(bar(3, 10.22, 10.24, 10.09, 10.10).timestamp, 10.22, 10.24, 10.09, 10.10, 1000),
    ]
    result = run_backtest(_cfg(_manage_rule()), {("AAPL", "15Min"): bars})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 10.20
    assert trade.exit_reason == "stop"
    assert trade.exit_price == pytest.approx(10.20 * 0.99)
    assert any("stop_mode: entry_pct" in n for n in result.report.notes)


def test_lock_plus_arms_on_first_touch_and_fills_next_bar():
    bars = [
        Bar(bar(0, 100, 100.2, 80.0, 82.0).timestamp, 100.0, 100.2, 80.0, 82.0, 1000),
        Bar(bar(1, 81.0, 110.0, 80.0, 100.0).timestamp, 81.0, 110.0, 80.0, 100.0, 1000),
        # Fill at 100. High 100.5 — no +1% touch yet.
        Bar(bar(2, 100.0, 100.5, 99.8, 100.4).timestamp, 100.0, 100.5, 99.8, 100.4, 1000),
        # First touch of 101. Same-bar low 100.2 must NOT fill the locked stop.
        Bar(bar(3, 100.4, 101.05, 100.2, 100.8).timestamp, 100.4, 101.05, 100.2, 100.8, 1000),
        # Next bar opens above the lock, then tags 101.
        Bar(bar(4, 101.05, 101.20, 100.85, 100.90).timestamp, 101.05, 101.20, 100.85, 100.90, 1000),
    ]
    result = run_backtest(
        _cfg(_manage_rule(stop_mode="lock_plus", lock_trigger_pct=1.0, lock_stop_pct=1.0)),
        {("AAPL", "15Min"): bars},
    )
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 100.0
    assert trade.lock_armed is True
    assert trade.exit_reason == "lock_stop"
    assert trade.exit_price == pytest.approx(101.0)
    assert result.report.lock_armed == 1
    assert any("lock_plus" in n for n in result.report.notes)


def test_lock_plus_same_bar_touch_does_not_fill_lock():
    bars = [
        Bar(bar(0, 100, 100.2, 80.0, 82.0).timestamp, 100.0, 100.2, 80.0, 82.0, 1000),
        Bar(bar(1, 81.0, 110.0, 80.0, 100.0).timestamp, 81.0, 110.0, 80.0, 100.0, 1000),
        Bar(bar(2, 100.0, 101.20, 100.10, 100.80).timestamp, 100.0, 101.20, 100.10, 100.80, 1000),
    ]
    result = run_backtest(
        _cfg(_manage_rule(stop_mode="lock_plus")),
        {("AAPL", "15Min"): bars},
    )
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.lock_armed is True
    assert trade.exit_reason == "eod"
    assert trade.exit_price == 100.80


def test_lock_plus_initial_stop_before_touch():
    bars = [
        Bar(bar(0, 100, 100.2, 80.0, 82.0).timestamp, 100.0, 100.2, 80.0, 82.0, 1000),
        Bar(bar(1, 81.0, 110.0, 80.0, 100.0).timestamp, 81.0, 110.0, 80.0, 100.0, 1000),
        Bar(bar(2, 100.0, 100.4, 98.90, 99.20).timestamp, 100.0, 100.4, 98.90, 99.20, 1000),
    ]
    result = run_backtest(
        _cfg(_manage_rule(stop_mode="lock_plus")),
        {("AAPL", "15Min"): bars},
    )
    trade = result.trades[0]
    assert trade.lock_armed is False
    assert trade.exit_reason == "stop"
    assert trade.exit_price == pytest.approx(99.0)


def test_trail_ratchets_from_high_and_fills_next_bar():
    bars = [
        Bar(bar(0, 100, 100.2, 80.0, 82.0).timestamp, 100.0, 100.2, 80.0, 82.0, 1000),
        Bar(bar(1, 81.0, 110.0, 80.0, 100.0).timestamp, 81.0, 110.0, 80.0, 100.0, 1000),
        # Fill. High 102 would make trail 100.98, but same-bar low 100.5 uses initial 99.
        Bar(bar(2, 100.0, 102.0, 100.5, 101.5).timestamp, 100.0, 102.0, 100.5, 101.5, 1000),
        # Next bar hits 102*0.99 = 100.98.
        Bar(bar(3, 101.4, 101.6, 100.90, 101.0).timestamp, 101.4, 101.6, 100.90, 101.0, 1000),
    ]
    result = run_backtest(
        _cfg(_manage_rule(stop_mode="trail", trail_pct=1.0)),
        {("AAPL", "15Min"): bars},
    )
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.entry_price == 100.0
    assert trade.trail_ratcheted is True
    assert trade.exit_reason == "trail_stop"
    assert trade.exit_price == pytest.approx(102.0 * 0.99)
    assert result.report.trail_ratcheted == 1
    assert any("stop_mode: trail" in n for n in result.report.notes)


def test_trail_never_ratchets_down():
    bars = [
        Bar(bar(0, 100, 100.2, 80.0, 82.0).timestamp, 100.0, 100.2, 80.0, 82.0, 1000),
        Bar(bar(1, 81.0, 110.0, 80.0, 100.0).timestamp, 81.0, 110.0, 80.0, 100.0, 1000),
        Bar(bar(2, 100.0, 103.0, 100.5, 102.0).timestamp, 100.0, 103.0, 100.5, 102.0, 1000),
        # Lower high; trail must stay at 103*0.99 = 101.97 (this low is 102.0).
        Bar(bar(3, 102.0, 102.4, 102.0, 102.1).timestamp, 102.0, 102.4, 102.0, 102.1, 1000),
    ]
    result = run_backtest(
        _cfg(_manage_rule(stop_mode="trail")),
        {("AAPL", "15Min"): bars},
    )
    trade = result.trades[0]
    assert trade.exit_reason == "eod"
    assert trade.trail_ratcheted is True
    assert trade.exit_price == 102.1


def _manage_sell_rule(**action_kw) -> RuleSpec:
    defaults = dict(
        type="sell",
        size=SizeSpec(type="shares", value=10),
        exit="fixed_bracket",
        stop_mode="lock_plus",
        stop_loss_pct=1.0,
        lock_trigger_pct=1.0,
        lock_stop_pct=1.0,
    )
    defaults.update(action_kw)
    return _buy_rule(id="ema9_trend_short", action=ActionSpec(**defaults))


def test_lock_plus_short_arms_on_minus_one_and_fills_next_bar():
    bars = [
        Bar(bar(0, 100, 100.2, 80.0, 82.0).timestamp, 100.0, 100.2, 80.0, 82.0, 1000),
        Bar(bar(1, 81.0, 110.0, 80.0, 100.0).timestamp, 81.0, 110.0, 80.0, 100.0, 1000),
        # Fill short at 100. Low 99.8 — no −1% touch yet. High 100.4 stays under 101 stop.
        Bar(bar(2, 100.0, 100.4, 99.8, 100.2).timestamp, 100.0, 100.4, 99.8, 100.2, 1000),
        # First touch of 99. Same-bar high 100.3 must NOT fill the locked stop.
        Bar(bar(3, 100.2, 100.3, 98.90, 99.80).timestamp, 100.2, 100.3, 98.90, 99.80, 1000),
        # Next bar opens below the initial 101 stop, then tags 99 from below.
        Bar(bar(4, 98.80, 99.05, 98.70, 98.90).timestamp, 98.80, 99.05, 98.70, 98.90, 1000),
    ]
    result = run_backtest(_cfg(_manage_sell_rule()), {("AAPL", "15Min"): bars})
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.side == "sell"
    assert trade.entry_price == 100.0
    assert trade.lock_armed is True
    assert trade.exit_reason == "lock_stop"
    assert trade.exit_price == pytest.approx(99.0)
    assert result.report.sides["sell"]["trades"] == 1
    assert any("Short:" not in n or "lock" in n for n in result.report.notes)
    assert any("bar low" in n and "lock_plus" in n for n in result.report.notes)


def test_lock_plus_short_initial_stop_before_touch():
    bars = [
        Bar(bar(0, 100, 100.2, 80.0, 82.0).timestamp, 100.0, 100.2, 80.0, 82.0, 1000),
        Bar(bar(1, 81.0, 110.0, 80.0, 100.0).timestamp, 81.0, 110.0, 80.0, 100.0, 1000),
        Bar(bar(2, 100.0, 101.20, 99.80, 100.50).timestamp, 100.0, 101.20, 99.80, 100.50, 1000),
    ]
    result = run_backtest(_cfg(_manage_sell_rule()), {("AAPL", "15Min"): bars})
    trade = result.trades[0]
    assert trade.side == "sell"
    assert trade.lock_armed is False
    assert trade.exit_reason == "stop"
    assert trade.exit_price == pytest.approx(101.0)


def test_opposite_signal_skipped_while_in_trade():
    bars = [
        Bar(bar(0, 10, 10.2, 8.0, 8.2).timestamp, 10.0, 10.2, 8.0, 8.2, 1000),
        Bar(bar(1, 8.1, 11.0, 8.0, 10.0).timestamp, 8.1, 11.0, 8.0, 10.0, 1000),
        Bar(bar(2, 10.0, 10.15, 9.95, 10.10).timestamp, 10.0, 10.15, 9.95, 10.10, 1000),
        Bar(bar(3, 10.10, 10.20, 10.00, 10.18).timestamp, 10.10, 10.20, 10.00, 10.18, 1000),
        Bar(bar(4, 10.25, 10.30, 9.90, 9.95).timestamp, 10.25, 10.30, 9.90, 9.95, 1000),
        Bar(bar(5, 9.95, 10.00, 9.90, 9.92).timestamp, 9.95, 10.00, 9.90, 9.92, 1000),
    ]
    long_rule = _buy_rule(
        cooldown_minutes=0,
        action=ActionSpec(type="buy", size=SizeSpec(type="shares", value=10), stop_loss_pct=5.0),
    )
    short_rule = _close_rule(
        id="ema9_trend_short",
        cooldown_minutes=0,
        when=parse_condition({"pattern": "bearish_engulfing", "timeframe": "15m"}),
        action=ActionSpec(
            type="sell",
            size=SizeSpec(type="shares", value=10),
            stop_mode="lock_plus",
            stop_loss_pct=1.0,
        ),
    )
    result = run_backtest(
        _cfg(long_rule, short_rule),
        {("AAPL", "15Min"): bars},
        starting_equity=100_000,
    )
    skipped = [s for s in result.signals if s.skip_reason == "opposite_signal_in_trade"]
    assert skipped
    assert all(s.action_type == "sell" for s in skipped)
    assert result.report.trades == 1
    assert result.trades[0].side == "buy"
    assert "sell" not in result.report.sides


def test_flatten_by_closes_short_at_1545_bar_close():
    bars = [
        _et_bar(9, 30, 10.0, 10.2, 8.0, 8.2),
        _et_bar(9, 45, 8.1, 11.0, 8.0, 10.0),
        _et_bar(10, 0, 10.0, 10.1, 9.95, 10.05),
    ]
    t = datetime(2026, 9, 11, 10, 15, tzinfo=NY)
    while t <= datetime(2026, 9, 11, 15, 45, tzinfo=NY):
        bars.append(_et_bar(t.hour, t.minute, 10.05, 10.10, 10.00, 10.06))
        t = t.replace(hour=t.hour + (t.minute + 15) // 60, minute=(t.minute + 15) % 60)
    result = run_backtest(
        _cfg(_manage_sell_rule(stop_loss_pct=50.0), entry_cutoff="12:00", flatten_by="15:55"),
        {("AAPL", "15Min"): bars},
        starting_equity=100_000,
    )
    assert result.report.trades == 1
    trade = result.trades[0]
    assert trade.side == "sell"
    assert trade.exit_reason == "session_flatten"
    assert trade.exit_price == 10.06
