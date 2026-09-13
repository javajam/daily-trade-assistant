from datetime import datetime, timezone

from dta_bot.backtest import Trade
from dta_bot.period_stats import build_period_stats, parse_trade_bound, session_date


def _ts(day: int, hour: int = 20, minute: int = 0) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=timezone.utc)


def _trade(day: int, pnl: float, symbol: str = "AAPL") -> Trade:
    entry = _ts(day, 14, 0)
    exit_ = _ts(day, 18, 0)
    return Trade(
        rule_id="ema9_trend",
        symbol=symbol,
        qty=100,
        side="buy",
        entry_time=entry,
        entry_price=200.0,
        exit_time=exit_,
        exit_price=200.0 + pnl / 100.0,
        pnl=pnl,
        pnl_pct=pnl / 20000.0 * 100.0,
        exit_reason="take" if pnl > 0 else "stop",
    )


def test_parse_trade_bound_ny_inclusive_end():
    start = parse_trade_bound("2026-08-01")
    end = parse_trade_bound("2026-08-31", end=True)
    assert start is not None and end is not None
    assert start.tzinfo is not None
    assert session_date(start).isoformat() == "2026-08-01"
    # Exclusive bound is 2026-09-01 00:00 America/New_York.
    assert end.isoformat().startswith("2026-09-01")


def test_daily_weekly_monthly_from_closed_trades():
    trades = [
        _trade(3, 300.0, "AAPL"),
        _trade(3, -150.0, "MSFT"),
        _trade(4, 90.0, "AAPL"),
        _trade(10, -40.0, "MSFT"),
    ]
    curve = [
        (_ts(3, 20, 0), 100_150.0),
        (_ts(4, 20, 0), 100_240.0),
        (_ts(10, 20, 0), 100_200.0),
    ]
    stats = build_period_stats(
        trades=trades,
        equity_curve=curve,
        starting_equity=100_000.0,
        ending_equity=100_200.0,
        session_start=None,
        session_end=None,
    )
    daily = {row["date"]: row for row in stats["daily"]}
    assert daily["2026-08-03"]["trades"] == 2
    assert daily["2026-08-03"]["wins"] == 1
    assert daily["2026-08-03"]["losses"] == 1
    assert daily["2026-08-03"]["pnl"] == 150.0
    assert daily["2026-08-03"]["equity_eod"] == 100_150.0
    assert daily["2026-08-04"]["trades"] == 1
    assert daily["2026-08-10"]["pnl"] == -40.0

    assert len(stats["weekly"]) >= 2
    monthly = stats["monthly"]
    assert monthly["trades"] == 4
    assert monthly["wins"] == 2
    assert monthly["losses"] == 2
    assert monthly["total_pnl"] == 200.0
    assert monthly["best_day"]["date"] == "2026-08-03"
    assert monthly["worst_day"]["date"] == "2026-08-10"
    assert monthly["win_rate_pct"] == 50.0
