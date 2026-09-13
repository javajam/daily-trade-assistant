"""Daily / weekly / monthly books from closed trades and the equity curve.

Session dates are America/New_York calendar dates (RTH Yahoo bars are UTC).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def session_date(dt: datetime) -> date:
    return _aware(dt).astimezone(NY).date()


def parse_trade_bound(value: Optional[str], *, end: bool = False) -> Optional[datetime]:
    """Parse a CLI/config timestamp.

    Date-only values are America/New_York midnights. ``end=True`` makes a
    date inclusive (returns the next NY midnight, exclusive bound).
    """
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    if "T" in raw:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=NY)
        return _aware(dt)
    day = date.fromisoformat(raw)
    start = datetime(day.year, day.month, day.day, tzinfo=NY)
    if end:
        start = start + timedelta(days=1)
    return start.astimezone(timezone.utc)


def _iso_date(d: date) -> str:
    return d.isoformat()


def _week_key(d: date) -> tuple[int, int]:
    iso = d.isocalendar()
    return (iso.year, iso.week)


def _week_label(year: int, week: int, days: list[date]) -> str:
    first = min(days)
    last = max(days)
    return f"{year}-W{week:02d} ({first.isoformat()} → {last.isoformat()})"


def _month_key(d: date) -> tuple[int, int]:
    return (d.year, d.month)


def _month_label(year: int, month: int, days: list[date]) -> str:
    first = min(days)
    last = max(days)
    return f"{year:04d}-{month:02d} ({first.isoformat()} → {last.isoformat()})"


def equity_eod_by_date(equity_curve: Iterable[tuple[datetime, float]]) -> dict[date, float]:
    eod: dict[date, float] = {}
    for ts, eq in equity_curve:
        eod[session_date(ts)] = eq
    return eod


def build_period_stats(
    *,
    trades: list[Any],
    equity_curve: list[tuple[datetime, float]],
    starting_equity: float,
    ending_equity: float,
    session_start: Optional[date] = None,
    session_end: Optional[date] = None,
) -> dict[str, Any]:
    """Aggregate realized P&L by NY session day / ISO week / calendar month.

    Daily P&L is the sum of trades whose *exit* falls on that NY date.
    Equity EOD is the last mark on that date. Days with tape but no exits
    still appear (0 trades / $0 realized).
    """
    eod = equity_eod_by_date(equity_curve)
    dates = sorted(eod)
    if session_start is not None:
        dates = [d for d in dates if d >= session_start]
    if session_end is not None:
        dates = [d for d in dates if d <= session_end]
    trades_by_day: dict[date, list[Any]] = defaultdict(list)
    for trade in trades:
        day = session_date(trade.exit_time)
        if session_start is not None and day < session_start:
            continue
        if session_end is not None and day > session_end:
            continue
        trades_by_day[day].append(trade)

    daily: list[dict[str, Any]] = []
    prev_eq = starting_equity
    for day in dates:
        day_trades = trades_by_day.get(day, [])
        wins = [t for t in day_trades if t.pnl > 0]
        losses = [t for t in day_trades if t.pnl < 0]
        pnl = sum(t.pnl for t in day_trades)
        eq = eod[day]
        daily.append(
            {
                "date": _iso_date(day),
                "trades": len(day_trades),
                "wins": len(wins),
                "losses": len(losses),
                "pnl": pnl,
                "pnl_pct": (pnl / starting_equity * 100.0) if starting_equity else 0.0,
                "equity_eod": eq,
                "equity_change": eq - prev_eq,
                "equity_change_pct": (eq - prev_eq) / prev_eq * 100.0 if prev_eq else 0.0,
            }
        )
        prev_eq = eq

    weeks: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in daily:
        d = date.fromisoformat(row["date"])
        weeks[_week_key(d)].append(row)

    weekly: list[dict[str, Any]] = []
    for (year, week), rows in sorted(weeks.items()):
        days = [date.fromisoformat(r["date"]) for r in rows]
        trades_n = sum(r["trades"] for r in rows)
        wins_n = sum(r["wins"] for r in rows)
        losses_n = sum(r["losses"] for r in rows)
        pnl = sum(r["pnl"] for r in rows)
        closed = wins_n + losses_n
        weekly.append(
            {
                "week": _week_label(year, week, days),
                "iso_year": year,
                "iso_week": week,
                "trades": trades_n,
                "wins": wins_n,
                "losses": losses_n,
                "win_rate_pct": (wins_n / closed * 100.0) if closed else None,
                "pnl": pnl,
                "pnl_pct": (pnl / starting_equity * 100.0) if starting_equity else 0.0,
                "equity": rows[-1]["equity_eod"],
            }
        )

    month_groups: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in daily:
        d = date.fromisoformat(row["date"])
        month_groups[_month_key(d)].append(row)

    months: list[dict[str, Any]] = []
    for (year, month), rows in sorted(month_groups.items()):
        days = [date.fromisoformat(r["date"]) for r in rows]
        trades_n = sum(r["trades"] for r in rows)
        wins_n = sum(r["wins"] for r in rows)
        losses_n = sum(r["losses"] for r in rows)
        pnl = sum(r["pnl"] for r in rows)
        closed = wins_n + losses_n
        months.append(
            {
                "month": _month_label(year, month, days),
                "year": year,
                "calendar_month": month,
                "trades": trades_n,
                "wins": wins_n,
                "losses": losses_n,
                "win_rate_pct": (wins_n / closed * 100.0) if closed else None,
                "pnl": pnl,
                "pnl_pct": (pnl / starting_equity * 100.0) if starting_equity else 0.0,
                "equity": rows[-1]["equity_eod"],
                "session_days": len(rows),
            }
        )

    total_pnl = sum(t.pnl for t in trades)
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    closed = len(wins) + len(losses)
    best = max(daily, key=lambda r: r["pnl"]) if daily else None
    worst = min(daily, key=lambda r: r["pnl"]) if daily else None
    month_key = None
    if dates:
        first = dates[0]
        month_key = f"{first.year:04d}-{first.month:02d}"
        if dates[-1].month != first.month or dates[-1].year != first.year:
            month_key = f"{_iso_date(dates[0])} → {_iso_date(dates[-1])}"

    monthly = {
        "month": month_key,
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": (len(wins) / closed * 100.0) if closed else None,
        "total_pnl": total_pnl,
        "return_pct": (total_pnl / starting_equity * 100.0) if starting_equity else 0.0,
        "starting_equity": starting_equity,
        "ending_equity": ending_equity,
        "best_day": (
            {"date": best["date"], "pnl": best["pnl"], "trades": best["trades"]}
            if best
            else None
        ),
        "worst_day": (
            {"date": worst["date"], "pnl": worst["pnl"], "trades": worst["trades"]}
            if worst
            else None
        ),
        "session_days": len(daily),
    }
    return {"daily": daily, "weekly": weekly, "months": months, "monthly": monthly}


def format_period_stats_md(stats: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    monthly = stats.get("monthly") or {}
    if monthly:
        lines.extend(
            [
                "### Monthly",
                "",
                f"- Month: {monthly.get('month')}",
                f"- Session days: {monthly.get('session_days')}",
                f"- Trades: {monthly.get('trades')}  (wins {monthly.get('wins')} / losses {monthly.get('losses')})",
                f"- Win rate: {_fmt_opt_pct(monthly.get('win_rate_pct'))}",
                f"- Total P&L: {_fmt_money(monthly.get('total_pnl'))} ({_fmt_opt_pct(monthly.get('return_pct'))} of starting equity)",
                f"- Ending equity: {_fmt_money(monthly.get('ending_equity'))}",
            ]
        )
        best = monthly.get("best_day")
        worst = monthly.get("worst_day")
        if best:
            lines.append(
                f"- Best day (realized): {best.get('date')} {_fmt_money(best.get('pnl'))} ({best.get('trades')} trades)"
            )
        if worst:
            lines.append(
                f"- Worst day (realized): {worst.get('date')} {_fmt_money(worst.get('pnl'))} ({worst.get('trades')} trades)"
            )
        lines.append("")

    months = stats.get("months") or []
    if months:
        lines.extend(
            [
                "### By calendar month",
                "",
                "| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in months:
            lines.append(
                "| {month} | {days} | {trades} | {win} | {pnl} | {pct} | {eq} |".format(
                    month=row["month"],
                    days=row.get("session_days"),
                    trades=row["trades"],
                    win=_fmt_opt_pct(row.get("win_rate_pct")),
                    pnl=_fmt_money(row.get("pnl")),
                    pct=_fmt_opt_pct(row.get("pnl_pct")),
                    eq=_fmt_money(row.get("equity")),
                )
            )
        lines.append("")

    weekly = stats.get("weekly") or []
    if weekly:
        lines.extend(
            [
                "### Weekly",
                "",
                "| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in weekly:
            lines.append(
                "| {week} | {trades} | {win} | {pnl} | {pct} | {eq} |".format(
                    week=row["week"],
                    trades=row["trades"],
                    win=_fmt_opt_pct(row.get("win_rate_pct")),
                    pnl=_fmt_money(row.get("pnl")),
                    pct=_fmt_opt_pct(row.get("pnl_pct")),
                    eq=_fmt_money(row.get("equity")),
                )
            )
        lines.append("")

    daily = stats.get("daily") or []
    if daily:
        lines.extend(
            [
                "### Daily",
                "",
                "| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in daily:
            lines.append(
                "| {date} | {trades} | {wins} | {losses} | {pnl} | {pct} | {eq} |".format(
                    date=row["date"],
                    trades=row["trades"],
                    wins=row["wins"],
                    losses=row["losses"],
                    pnl=_fmt_money(row.get("pnl")),
                    pct=_fmt_opt_pct(row.get("pnl_pct")),
                    eq=_fmt_money(row.get("equity_eod")),
                )
            )
        lines.append("")
    return lines


def _fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def _fmt_opt_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}%"
