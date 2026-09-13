"""Replay YAML rules over historical bars using the live evaluation engine.

Fills, stops, and take-profits are simulated here; pattern / SMA / RSI / volume
matches always go through ``evaluate_rule`` so detectors stay in one place.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dta_bot.config import AnyCondition, BotConfig, GroupCond, RuleSpec
from dta_bot.engine import BarMap, cooldown_key, evaluate_rule, fire_key
from dta_bot.models import Account, Bar
from dta_bot.sizing import bracket_prices, shares_for
from dta_bot.state import BotState
from dta_bot.timeframes import duration, normalize

log = logging.getLogger("dta_bot.backtest")


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return _aware(dt).isoformat().replace("+00:00", "Z")


def rule_timeframes(rule: RuleSpec) -> set[str]:
    def walk(cond: AnyCondition) -> list[str]:
        if isinstance(cond, GroupCond):
            out: list[str] = []
            for child in cond.conditions:
                out.extend(walk(child))
            return out
        return [cond.timeframe]

    return set(walk(rule.when))


def restrict_config(config: BotConfig, rule_ids: Optional[list[str]]) -> BotConfig:
    if not rule_ids:
        return config
    wanted = set(rule_ids)
    rules = [r for r in config.rules if r.id in wanted]
    if not rules:
        raise ValueError(f"No rules matched {rule_ids}")
    return BotConfig(settings=config.settings, universe=list(config.universe), rules=rules)


@dataclass
class Trade:
    rule_id: str
    symbol: str
    qty: float
    side: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    pnl: float
    pnl_pct: float
    exit_reason: str
    signal_time: Optional[datetime] = None
    entry_rule_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["entry_time"] = _iso(self.entry_time)
        d["exit_time"] = _iso(self.exit_time)
        d["signal_time"] = _iso(self.signal_time)
        return d


@dataclass
class Signal:
    rule_id: str
    symbol: str
    action_type: str
    signal_time: datetime
    bar_ts: Optional[datetime]
    reason: str
    accepted: bool
    skip_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "symbol": self.symbol,
            "action_type": self.action_type,
            "signal_time": _iso(self.signal_time),
            "bar_ts": _iso(self.bar_ts),
            "reason": self.reason,
            "accepted": self.accepted,
            "skip_reason": self.skip_reason,
        }


@dataclass
class OpenLot:
    rule_id: str
    symbol: str
    qty: float
    side: str
    entry_time: datetime
    entry_price: float
    stop: Optional[float]
    take: Optional[float]
    signal_time: datetime
    tf: str


@dataclass
class PendingOrder:
    kind: str  # enter | close
    rule_id: str
    symbol: str
    tf: str
    fill_ts: datetime
    qty: Optional[float]
    side: str
    stop: Optional[float]
    take: Optional[float]
    signal_time: datetime
    signal_price: float
    entry_rule_id: str = ""


@dataclass
class RuleReport:
    rule_id: str
    signals: int
    trades: int
    wins: int
    losses: int
    breakeven: int
    win_rate_pct: Optional[float]
    total_pnl: float
    total_pnl_pct: float
    avg_win: Optional[float]
    avg_loss: Optional[float]
    max_drawdown: Optional[float]
    max_drawdown_pct: Optional[float]
    starting_equity: float
    ending_equity: float
    period_start: Optional[str]
    period_end: Optional[str]
    data_source: str
    notes: list[str] = field(default_factory=list)
    exit_reasons: dict[str, int] = field(default_factory=dict)
    signals_by_symbol: dict[str, int] = field(default_factory=dict)
    trades_by_symbol: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BacktestResult:
    label: str
    report: RuleReport
    trades: list[Trade]
    signals: list[Signal]
    equity_curve: list[tuple[datetime, float]]
    bars_used: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "report": self.report.to_dict(),
            "trades": [t.to_dict() for t in self.trades],
            "signals": [s.to_dict() for s in self.signals],
            "equity_curve": [[_iso(t), eq] for t, eq in self.equity_curve],
            "bars_used": self.bars_used,
        }


def _next_bar(series: list[Bar], after_ts: datetime) -> Optional[Bar]:
    after_ts = _aware(after_ts)
    for bar in series:
        if _aware(bar.timestamp) > after_ts:
            return bar
    return None


def _mark_to_market(cash: float, lots: list[OpenLot], last_price: dict[str, float]) -> float:
    """Cash plus long inventory minus short liabilities.

    Entries already moved cash (longs debit ``qty * entry``, shorts credit it),
    so a short must subtract ``qty * mark`` — not add ``qty * (2*entry - mark)``,
    which double-counts proceeds and fabricates a drawdown when the short closes.
    """
    equity = cash
    for lot in lots:
        px = last_price.get(lot.symbol, lot.entry_price)
        if lot.side == "buy":
            equity += lot.qty * px
        else:
            equity -= lot.qty * px
    return equity


def _apply_slippage(price: float, side: str, slippage_pct: float, *, is_entry: bool) -> float:
    if slippage_pct <= 0:
        return price
    frac = slippage_pct / 100.0
    buying = (side == "buy" and is_entry) or (side == "sell" and not is_entry)
    return price * (1.0 + frac) if buying else price * (1.0 - frac)


def _stop_take_hit(bar: Bar, lot: OpenLot) -> Optional[tuple[str, float]]:
    """Return (reason, fill_price) if stop/take is touched on this bar.

    Conservative same-bar rule: if both levels trade, assume stop fills first.
    Gaps through a level fill at the open.
    """
    if lot.side == "buy":
        if lot.stop is not None and bar.open <= lot.stop:
            return "stop", bar.open
        if lot.take is not None and bar.open >= lot.take:
            return "take", bar.open
        stop_hit = lot.stop is not None and bar.low <= lot.stop
        take_hit = lot.take is not None and bar.high >= lot.take
        if stop_hit and take_hit:
            return "stop", lot.stop
        if stop_hit:
            return "stop", lot.stop
        if take_hit:
            return "take", lot.take
        return None
    if lot.stop is not None and bar.open >= lot.stop:
        return "stop", bar.open
    if lot.take is not None and bar.open <= lot.take:
        return "take", bar.open
    stop_hit = lot.stop is not None and bar.high >= lot.stop
    take_hit = lot.take is not None and bar.low <= lot.take
    if stop_hit and take_hit:
        return "stop", lot.stop
    if stop_hit:
        return "stop", lot.stop
    if take_hit:
        return "take", lot.take
    return None


def _close_lot(
    lot: OpenLot,
    *,
    when: datetime,
    price: float,
    reason: str,
    cash: float,
    commission: float,
    slippage_pct: float,
) -> tuple[Trade, float]:
    fill = _apply_slippage(price, lot.side, slippage_pct, is_entry=False)
    if lot.side == "buy":
        proceeds = lot.qty * fill
        cash += proceeds - commission
        pnl = lot.qty * (fill - lot.entry_price) - commission
    else:
        cost = lot.qty * fill
        cash -= cost + commission
        pnl = lot.qty * (lot.entry_price - fill) - commission
    notional = lot.qty * lot.entry_price
    pnl_pct = (pnl / notional * 100.0) if notional else 0.0
    trade = Trade(
        rule_id=lot.rule_id,
        symbol=lot.symbol,
        qty=lot.qty,
        side=lot.side,
        entry_time=lot.entry_time,
        entry_price=lot.entry_price,
        exit_time=when,
        exit_price=fill,
        pnl=pnl,
        pnl_pct=pnl_pct,
        exit_reason=reason,
        signal_time=lot.signal_time,
        entry_rule_id=lot.rule_id,
    )
    return trade, cash


def _max_drawdown(curve: list[tuple[datetime, float]]) -> tuple[Optional[float], Optional[float]]:
    if not curve:
        return None, None
    peak = curve[0][1]
    max_dd = 0.0
    max_dd_pct = 0.0
    for _ts, eq in curve:
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = (dd / peak * 100.0) if peak else 0.0
    return max_dd, max_dd_pct


def summarize(
    *,
    label: str,
    starting_equity: float,
    ending_equity: float,
    trades: list[Trade],
    signals: list[Signal],
    equity_curve: list[tuple[datetime, float]],
    period_start: Optional[datetime],
    period_end: Optional[datetime],
    data_source: str,
    notes: Optional[list[str]] = None,
) -> RuleReport:
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    flat = [t for t in trades if t.pnl == 0]
    total_pnl = sum(t.pnl for t in trades)
    closed = len(trades)
    win_rate = (len(wins) / closed * 100.0) if closed else None
    dd, dd_pct = _max_drawdown(equity_curve)
    reasons: dict[str, int] = {}
    for t in trades:
        reasons[t.exit_reason] = reasons.get(t.exit_reason, 0) + 1
    by_sig: dict[str, int] = {}
    for s in signals:
        by_sig[s.symbol] = by_sig.get(s.symbol, 0) + 1
    by_tr: dict[str, int] = {}
    for t in trades:
        by_tr[t.symbol] = by_tr.get(t.symbol, 0) + 1
    return RuleReport(
        rule_id=label,
        signals=len(signals),
        trades=closed,
        wins=len(wins),
        losses=len(losses),
        breakeven=len(flat),
        win_rate_pct=win_rate,
        total_pnl=total_pnl,
        total_pnl_pct=(total_pnl / starting_equity * 100.0) if starting_equity else 0.0,
        avg_win=(sum(t.pnl for t in wins) / len(wins)) if wins else None,
        avg_loss=(sum(t.pnl for t in losses) / len(losses)) if losses else None,
        max_drawdown=dd,
        max_drawdown_pct=dd_pct,
        starting_equity=starting_equity,
        ending_equity=ending_equity,
        period_start=_iso(period_start),
        period_end=_iso(period_end),
        data_source=data_source,
        notes=list(notes or []),
        exit_reasons=reasons,
        signals_by_symbol=by_sig,
        trades_by_symbol=by_tr,
    )


def run_backtest(
    config: BotConfig,
    bars_by_key: BarMap,
    *,
    starting_equity: float = 100_000.0,
    commission: float = 0.0,
    slippage_pct: float = 0.0,
    allow_pyramid: bool = False,
    flatten_at_end: bool = True,
    label: Optional[str] = None,
    data_source: str = "",
    notes: Optional[list[str]] = None,
) -> BacktestResult:
    """Walk closed bars in time order and evaluate ``config.rules`` at each close."""
    logging.getLogger("dta_bot.engine").setLevel(logging.WARNING)

    needed = {(s.upper(), normalize(tf)) for s, tf in config.all_symbol_timeframes()}
    series_map: BarMap = {}
    for key, series in bars_by_key.items():
        symbol, tf = key[0].upper(), normalize(key[1])
        if needed and (symbol, tf) not in needed:
            continue
        cleaned = sorted(series, key=lambda b: _aware(b.timestamp))
        series_map[(symbol, tf)] = cleaned

    # Event list: each bar contributes its *close* time.
    events: dict[datetime, list[tuple[str, str, Bar]]] = {}
    for (symbol, tf), series in series_map.items():
        dur = duration(tf)
        for bar in series:
            close_ts = _aware(bar.timestamp) + dur
            events.setdefault(close_ts, []).append((symbol, tf, bar))

    lookback = config.settings.lookback_bars
    state = BotState()
    cash = starting_equity
    lots: list[OpenLot] = []
    pending: list[PendingOrder] = []
    trades: list[Trade] = []
    signals: list[Signal] = []
    equity_curve: list[tuple[datetime, float]] = []
    last_price: dict[str, float] = {}

    def symbols_in_position() -> set[str]:
        return {lot.symbol for lot in lots}

    def equity_now() -> float:
        return _mark_to_market(cash, lots, last_price)

    def account() -> Account:
        eq = equity_now()
        return Account(equity=eq, cash=cash, buying_power=cash, status="ACTIVE")

    def flatten_symbol(symbol: str, when: datetime, price: float, reason: str, rule_id: str) -> None:
        nonlocal cash
        remaining: list[OpenLot] = []
        for lot in lots:
            if lot.symbol != symbol:
                remaining.append(lot)
                continue
            trade, cash = _close_lot(
                lot,
                when=when,
                price=price,
                reason=reason,
                cash=cash,
                commission=commission,
                slippage_pct=slippage_pct,
            )
            trade.rule_id = rule_id
            trades.append(trade)
        lots[:] = remaining

    unique_times = sorted(events)
    cursors: dict[tuple[str, str], int] = {k: 0 for k in series_map}

    for now in unique_times:
        # Advance each series to bars whose close <= now.
        windows: BarMap = {}
        for key, series in series_map.items():
            dur = duration(key[1])
            i = cursors[key]
            while i < len(series) and _aware(series[i].timestamp) + dur <= now:
                last_price[key[0]] = series[i].close
                i += 1
            cursors[key] = i
            windows[key] = series[max(0, i - lookback) : i]

        # Finer timeframes first so 15m stops run before 1h evaluations at the same stamp.
        closing = sorted(events[now], key=lambda row: duration(row[1]))

        # 1) Fills scheduled for the bar that just completed (fill at that bar's open).
        still_pending: list[PendingOrder] = []
        for order in pending:
            fill_bar = None
            for symbol, tf, bar in closing:
                if symbol == order.symbol and tf == order.tf and _aware(bar.timestamp) == _aware(order.fill_ts):
                    fill_bar = bar
                    break
            if fill_bar is None:
                still_pending.append(order)
                continue
            last_price[order.symbol] = fill_bar.open
            if order.kind == "close":
                if order.symbol in symbols_in_position():
                    flatten_symbol(order.symbol, _aware(fill_bar.timestamp), fill_bar.open, "close_signal", order.rule_id)
                continue
            if not allow_pyramid and order.symbol in symbols_in_position():
                continue
            if order.qty is None or order.qty < 1:
                continue
            if order.symbol not in symbols_in_position() and len(symbols_in_position()) >= config.settings.max_open_positions:
                continue
            fill_px = _apply_slippage(fill_bar.open, order.side, slippage_pct, is_entry=True)
            if order.side == "buy":
                cash -= order.qty * fill_px + commission
            else:
                cash += order.qty * fill_px - commission
            lots.append(
                OpenLot(
                    rule_id=order.rule_id,
                    symbol=order.symbol,
                    qty=order.qty,
                    side=order.side,
                    entry_time=_aware(fill_bar.timestamp),
                    entry_price=fill_px,
                    stop=order.stop,
                    take=order.take,
                    signal_time=order.signal_time,
                    tf=order.tf,
                )
            )
        pending = still_pending

        # 2) Stop / take on the bar that just completed (after any fill at its open).
        for symbol, tf, bar in closing:
            last_price[symbol] = bar.close
            survivors: list[OpenLot] = []
            for lot in lots:
                if lot.symbol != symbol or lot.tf != tf:
                    survivors.append(lot)
                    continue
                hit = _stop_take_hit(bar, lot)
                if hit is None:
                    survivors.append(lot)
                    continue
                reason, px = hit
                trade, cash = _close_lot(
                    lot,
                    when=now,
                    price=px,
                    reason=reason,
                    cash=cash,
                    commission=commission,
                    slippage_pct=slippage_pct,
                )
                trades.append(trade)
            lots[:] = survivors

        # 3) Evaluate rules whose timeframes just got a newly closed bar.
        newly_closed_tf: dict[str, set[str]] = {}
        for symbol, tf, _bar in closing:
            newly_closed_tf.setdefault(symbol, set()).add(tf)

        for rule in config.rules:
            if not rule.enabled:
                continue
            needed = rule_timeframes(rule)
            for symbol in config.symbols_for(rule):
                if not (newly_closed_tf.get(symbol, set()) & needed):
                    continue
                ev = evaluate_rule(rule, symbol, windows, state, now=now)
                if not ev.matched:
                    continue
                why = ev.reasons[0] if ev.reasons else ""
                accepted = True
                skip_reason = None
                action = rule.action.type

                fill_tf = min(needed, key=lambda t: duration(t))
                series = series_map.get((symbol, fill_tf), [])
                nxt = _next_bar(series, ev.signal_bar_ts) if ev.signal_bar_ts else None

                if action == "close":
                    if symbol not in symbols_in_position():
                        accepted = False
                        skip_reason = "no_position"
                    elif nxt is None:
                        accepted = False
                        skip_reason = "no_next_bar"
                    else:
                        pending.append(
                            PendingOrder(
                                kind="close",
                                rule_id=rule.id,
                                symbol=symbol,
                                tf=fill_tf,
                                fill_ts=_aware(nxt.timestamp),
                                qty=None,
                                side="sell",
                                stop=None,
                                take=None,
                                signal_time=now,
                                signal_price=last_price.get(symbol, nxt.open),
                            )
                        )
                elif not allow_pyramid and symbol in symbols_in_position():
                    accepted = False
                    skip_reason = "already_in_position"
                elif (
                    symbol not in symbols_in_position()
                    and len(symbols_in_position()) >= config.settings.max_open_positions
                ):
                    accepted = False
                    skip_reason = "max_open_positions"
                else:
                    px = last_price.get(symbol)
                    if px is None or px <= 0:
                        accepted = False
                        skip_reason = "no_price"
                    else:
                        try:
                            qty = shares_for(rule.action, account(), px)
                        except ValueError:
                            accepted = False
                            skip_reason = "size_zero"
                            qty = 0.0
                        if accepted and nxt is None:
                            accepted = False
                            skip_reason = "no_next_bar"
                        elif accepted:
                            side = "buy" if action == "buy" else "sell"
                            stop, take = bracket_prices(rule.action, px, side)
                            pending.append(
                                PendingOrder(
                                    kind="enter",
                                    rule_id=rule.id,
                                    symbol=symbol,
                                    tf=fill_tf,
                                    fill_ts=_aware(nxt.timestamp),
                                    qty=qty,
                                    side=side,
                                    stop=stop,
                                    take=take,
                                    signal_time=now,
                                    signal_price=px,
                                )
                            )

                if ev.signal_bar_ts is not None:
                    state.mark_fired(
                        fire_key(rule.id, symbol, ev.signal_bar_ts),
                        cooldown_key(rule.id, symbol),
                        rule.cooldown_minutes,
                        when=now,
                    )
                signals.append(
                    Signal(
                        rule_id=rule.id,
                        symbol=symbol,
                        action_type=action,
                        signal_time=now,
                        bar_ts=ev.signal_bar_ts,
                        reason=why,
                        accepted=accepted,
                        skip_reason=skip_reason,
                    )
                )

        equity_curve.append((now, equity_now()))

    if flatten_at_end and lots:
        end_ts = unique_times[-1] if unique_times else datetime.now(timezone.utc)
        remaining = list(lots)
        lots.clear()
        for lot in remaining:
            px = last_price.get(lot.symbol, lot.entry_price)
            trade, cash = _close_lot(
                lot,
                when=end_ts,
                price=px,
                reason="eod",
                cash=cash,
                commission=commission,
                slippage_pct=slippage_pct,
            )
            trades.append(trade)
        equity_curve.append((end_ts, cash))

    ending = cash if not lots else equity_now()
    starts = [series[0].timestamp for series in series_map.values() if series]
    ends = [series[-1].timestamp for series in series_map.values() if series]
    period_start = min(starts) if starts else None
    period_end = max(ends) if ends else None
    used = {f"{s}:{tf}": len(series) for (s, tf), series in series_map.items()}
    tag = label or ",".join(r.id for r in config.rules) or "backtest"
    report = summarize(
        label=tag,
        starting_equity=starting_equity,
        ending_equity=ending,
        trades=trades,
        signals=signals,
        equity_curve=equity_curve,
        period_start=period_start,
        period_end=period_end,
        data_source=data_source,
        notes=notes,
    )
    return BacktestResult(
        label=tag,
        report=report,
        trades=trades,
        signals=signals,
        equity_curve=equity_curve,
        bars_used=used,
    )


def write_results_json(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def format_report_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Rule backtest results",
        "",
        f"- Generated (UTC): {payload.get('generated_at')}",
        f"- Starting equity: ${payload.get('starting_equity'):,.2f}" if payload.get("starting_equity") is not None else "",
        f"- Commission / slippage: {payload.get('friction')}",
        f"- Data: {payload.get('data_source')}",
        "",
    ]
    for block in payload.get("runs", []):
        r = block["report"]
        lines.extend(
            [
                f"## {r['rule_id']}",
                "",
                f"- Period: {r.get('period_start')} → {r.get('period_end')}",
                f"- Bars used: {block.get('bars_used')}",
                f"- Data source: {r.get('data_source')}",
                f"- Signals: {r['signals']}  (by symbol: {r.get('signals_by_symbol')})",
                f"- Pattern hits in those signals: {block.get('pattern_hits')}",
                f"- Trades: {r['trades']}  (by symbol: {r.get('trades_by_symbol')})",
                f"- Wins / losses / scratch: {r['wins']} / {r['losses']} / {r['breakeven']}",
                f"- Win rate: {_fmt_opt_pct(r.get('win_rate_pct'))}",
                f"- Total P&L: ${r['total_pnl']:,.2f} ({r['total_pnl_pct']:.3f}% of starting equity)",
                f"- Avg win: {_fmt_opt_money(r.get('avg_win'))}",
                f"- Avg loss: {_fmt_opt_money(r.get('avg_loss'))}",
                f"- Max drawdown: {_fmt_opt_money(r.get('max_drawdown'))} ({_fmt_opt_pct(r.get('max_drawdown_pct'))})",
                f"- Ending equity: ${r['ending_equity']:,.2f}",
                f"- Exit reasons: {r.get('exit_reasons')}",
            ]
        )
        extra_notes = [n for n in (r.get("notes") or []) if n.startswith("Exit-only")]
        for note in extra_notes:
            lines.append(f"- {note}")
        lines.append("")
    extra = payload.get("assumptions") or []
    if extra:
        lines.append("## Assumptions")
        lines.append("")
        for item in extra:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(line for line in lines if line is not None)


def _fmt_opt_money(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def _fmt_opt_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}%"
