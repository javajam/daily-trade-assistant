"""Replay the ORB edge-fade strategy on historical bars.

Fills reuse the shared stop/take simulator from ``dta_bot.backtest``.
Setups always come from ``find_all_setups`` so the state machine stays in one place.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from dta_bot.backtest import (
    BacktestResult,
    OpenLot,
    PendingOrder,
    Signal,
    Trade,
    _apply_slippage,
    _aware,
    _close_lot,
    _mark_to_market,
    _stop_take_hit,
    summarize,
)
from dta_bot.config import ActionSpec
from dta_bot.engine import BarMap
from dta_bot.models import Account
from dta_bot.orb import (
    OrbSetup,
    find_all_setups,
    first_profitable_close,
    gate_setups,
    next_signal_bar,
)
from dta_bot.orb_config import OrbBotConfig
from dta_bot.orb_engine import RULE_ID
from dta_bot.sizing import shares_for
from dta_bot.timeframes import duration, normalize


def run_orb_backtest(
    config: OrbBotConfig,
    bars_by_key: BarMap,
    *,
    starting_equity: float = 100_000.0,
    commission: float = 0.0,
    slippage_pct: float = 0.0,
    flatten_at_end: bool = True,
    label: Optional[str] = None,
    data_source: str = "",
    notes: Optional[list[str]] = None,
) -> BacktestResult:
    """Walk signal-timeframe bars and take every eligible ORB fade."""
    orb_tf = normalize(config.orb.orb_timeframe)
    sig_tf = normalize(config.orb.signal_timeframe)
    needed = {(s.upper(), tf) for s in config.universe for tf in {orb_tf, sig_tf}}
    series_map: BarMap = {}
    for key, series in bars_by_key.items():
        symbol, tf = key[0].upper(), normalize(key[1])
        if needed and (symbol, tf) not in needed:
            continue
        series_map[(symbol, tf)] = sorted(series, key=lambda b: _aware(b.timestamp))

    # reversal close time → (setup, entry bar)
    activate: dict[datetime, list[tuple[OrbSetup, object]]] = {}
    signals: list[Signal] = []
    for symbol in config.universe:
        series = series_map.get((symbol, sig_tf), [])
        setups = find_all_setups(
            symbol,
            orb_bars=series_map.get((symbol, orb_tf), []),
            signal_bars=series,
            session_open=config.orb.session_open,
            session_timezone=config.orb.session_timezone,
            session_close=config.orb.session_close,
            orb_timeframe=orb_tf,
            signal_timeframe=sig_tf,
            **config.orb.detector_kwargs(),
        )
        for setup, gate_skip in gate_setups(setups, **config.orb.gate_kwargs()):
            nxt = next_signal_bar(series, setup.reversal.timestamp)
            close_ts = _aware(setup.reversal.timestamp) + duration(sig_tf)
            if gate_skip:
                signals.append(
                    Signal(
                        rule_id=RULE_ID,
                        symbol=symbol,
                        action_type="buy" if setup.side == "buy" else "sell",
                        signal_time=close_ts,
                        bar_ts=setup.reversal.timestamp,
                        reason=setup.explain(),
                        accepted=False,
                        skip_reason=gate_skip,
                    )
                )
                continue
            accepted = nxt is not None
            signals.append(
                Signal(
                    rule_id=RULE_ID,
                    symbol=symbol,
                    action_type="buy" if setup.side == "buy" else "sell",
                    signal_time=close_ts,
                    bar_ts=setup.reversal.timestamp,
                    reason=setup.explain(),
                    accepted=accepted,
                    skip_reason=None if accepted else "no_next_bar",
                )
            )
            if nxt is not None:
                activate.setdefault(close_ts, []).append((setup, nxt))

    events: dict[datetime, list[tuple[str, str]]] = {}
    for symbol in config.universe:
        for bar in series_map.get((symbol, sig_tf), []):
            close_ts = _aware(bar.timestamp) + duration(sig_tf)
            events.setdefault(close_ts, []).append((symbol, sig_tf))

    cash = starting_equity
    lots: list[OpenLot] = []
    pending: list[PendingOrder] = []
    trades: list[Trade] = []
    equity_curve: list[tuple[datetime, float]] = []
    last_price: dict[str, float] = {}

    def symbols_in_position() -> set[str]:
        return {lot.symbol for lot in lots}

    def equity_now() -> float:
        return _mark_to_market(cash, lots, last_price)

    def account() -> Account:
        eq = equity_now()
        return Account(equity=eq, cash=cash, buying_power=cash, status="ACTIVE")

    def mark_skip(symbol: str, signal_time: datetime, reason: str) -> None:
        for sig in signals:
            if sig.symbol == symbol and sig.bar_ts is not None and _aware(sig.bar_ts) == _aware(signal_time):
                sig.accepted = False
                sig.skip_reason = reason

    def flatten_symbol(symbol: str, when: datetime, price: float, reason: str) -> None:
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
            trades.append(trade)
        lots[:] = remaining

    unique_times = sorted(events)
    cursors: dict[tuple[str, str], int] = {k: 0 for k in series_map}

    for now in unique_times:
        closing: list[tuple[str, str, object]] = []
        for key, series in series_map.items():
            dur = duration(key[1])
            i = cursors[key]
            while i < len(series) and _aware(series[i].timestamp) + dur <= now:
                last_price[key[0]] = series[i].close
                if key[1] == sig_tf and _aware(series[i].timestamp) + dur == now:
                    closing.append((key[0], key[1], series[i]))
                i += 1
            cursors[key] = i

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
            in_pos = order.symbol in symbols_in_position()
            if in_pos and config.orb.on_open_position == "skip":
                mark_skip(order.symbol, order.signal_time, "already_in_position")
                continue
            if in_pos and config.orb.on_open_position == "replace":
                flatten_symbol(order.symbol, _aware(fill_bar.timestamp), fill_bar.open, "replaced")
            if (
                order.symbol not in symbols_in_position()
                and len(symbols_in_position()) >= config.settings.max_open_positions
            ):
                mark_skip(order.symbol, order.signal_time, "max_open_positions")
                continue
            try:
                qty = shares_for(
                    ActionSpec(
                        type="buy" if order.side == "buy" else "sell",
                        size=config.sizing,
                    ),
                    account(),
                    fill_bar.open,
                )
            except ValueError:
                mark_skip(order.symbol, order.signal_time, "size_zero")
                continue
            fill_px = _apply_slippage(fill_bar.open, order.side, slippage_pct, is_entry=True)
            if order.side == "buy":
                cash -= qty * fill_px + commission
            else:
                cash += qty * fill_px - commission
            lots.append(
                OpenLot(
                    rule_id=order.rule_id,
                    symbol=order.symbol,
                    qty=qty,
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
        #    Stop is always checked first. first_profitable_close then exits at
        #    this bar's close if it is strictly profitable vs entry. Same-bar
        #    stop + first-profit (or midpoint) → stop wins.
        for symbol, tf, bar in closing:
            last_price[symbol] = bar.close
            survivors: list[OpenLot] = []
            for lot in lots:
                if lot.symbol != symbol or lot.tf != tf:
                    survivors.append(lot)
                    continue
                hit = _stop_take_hit(bar, lot)
                if hit is None and config.orb.take_profit_mode == "first_profitable_close":
                    if first_profitable_close(
                        side=lot.side, entry_price=lot.entry_price, close=bar.close
                    ):
                        hit = ("take", bar.close)
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

        # 3) A reversal that just closed schedules a fill at the next signal bar open.
        for setup, nxt in activate.get(now, []):
            pending.append(
                PendingOrder(
                    kind="enter",
                    rule_id=RULE_ID,
                    symbol=setup.symbol,
                    tf=sig_tf,
                    fill_ts=_aware(nxt.timestamp),
                    qty=None,
                    side=setup.side,
                    stop=setup.stop,
                    take=setup.take,
                    signal_time=_aware(setup.reversal.timestamp),
                    signal_price=setup.reversal.close,
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
    tag = label or RULE_ID
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
