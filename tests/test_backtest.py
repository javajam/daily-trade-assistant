from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from dta_bot.backtest import OpenLot, _mark_to_market, run_backtest, summarize
from dta_bot.config import ActionSpec, BotConfig, RuleSpec, Settings, SizeSpec, parse_condition
from dta_bot.models import Bar
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


def _session_cfg(*, gates: bool = True, cutoff: str = "15:15", tf: str = "15m") -> BotConfig:
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


def test_entry_cutoff_skips_fill_at_or_after_1515_et():
    # Engulfing completes on the 15:00 ET bar (closes 15:15); next open is 15:15.
    bars = [
        _et_bar(14, 45, 10.0, 10.2, 8.0, 8.2),
        _et_bar(15, 0, 8.1, 11.0, 8.0, 10.4),
        _et_bar(15, 15, 10.4, 10.5, 10.3, 10.45),
    ]
    result = run_backtest(_session_cfg(), {("AAPL", "15Min"): bars}, starting_equity=100_000)
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
    result = run_backtest(_session_cfg(), {("AAPL", "15Min"): bars}, starting_equity=100_000)
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
