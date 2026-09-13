"""Evaluate rules on an interval or once. Idempotent; kill switch blocks orders."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from dta_bot.broker import Broker
from dta_bot.config import BotConfig, RuleSpec, condition_timeframes
from dta_bot.engine import cooldown_key, evaluate_all, fire_key, ma_pair_cross_flatten_bar
from dta_bot.killswitch import is_active, reason as kill_reason
from dta_bot.market_data import MarketData
from dta_bot.models import EvalResult, Position
from dta_bot.orb_config import OrbBotConfig
from dta_bot.orb_engine import (
    RULE_ID as ORB_RULE_ID,
    build_orb_order,
    ema_cross_flatten_bar,
    evaluate_orb,
    first_profit_flatten_bar,
    last_reversal_ts,
    position_blocks_entry,
    setup_from_eval,
)
from dta_bot.indicators import sma
from dta_bot.session import fill_at_or_after_cutoff, is_flatten_bar, wall_clock_at_or_after
from dta_bot.sizing import build_order, sma_stop_valid
from dta_bot.state import BotState, parse_ts, save_state
from dta_bot.timeframes import duration

log = logging.getLogger("dta_bot.runner")


def fetch_bars(config: BotConfig | OrbBotConfig, data: MarketData) -> dict[tuple[str, str], list]:
    bars: dict[tuple[str, str], list] = {}
    for symbol, tf in sorted(config.all_symbol_timeframes()):
        try:
            series = data.get_bars(symbol, tf, limit=config.settings.lookback_bars)
        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            log.error("Failed to fetch %s %s: %s", symbol, tf, exc)
            series = []
        bars[(symbol, tf)] = series
        if series:
            log.info(
                "bars %s %s: %s closed (last %s)",
                symbol,
                tf,
                len(series),
                series[-1].summary(),
            )
        else:
            log.warning("bars %s %s: none", symbol, tf)
    return bars


def _position_map(positions: list[Position]) -> dict[str, Position]:
    return {p.symbol.upper(): p for p in positions}


def _last_price(symbol: str, bars) -> Optional[float]:
    """Most recent closed print for the symbol across fetched timeframes."""
    latest = None
    price = None
    for (sym, _tf), series in bars.items():
        if sym != symbol or not series:
            continue
        ts = series[-1].timestamp
        if latest is None or ts > latest:
            latest = ts
            price = series[-1].close
    return price


def execute_decision(
    *,
    ev: EvalResult,
    rule: RuleSpec,
    config: BotConfig,
    broker: Broker,
    bars,
    state: BotState,
    dry_run: bool,
) -> None:
    kill_file = config.settings.kill_switch_file
    if is_active(kill_file):
        log.warning(
            "[BLOCKED] %s %s %s — %s — would have acted on: %s",
            ev.symbol,
            ev.action_type,
            ev.rule_id,
            kill_reason(kill_file),
            ev.explain(),
        )
        return

    account = broker.get_account()
    positions = _position_map(broker.get_positions())
    if ev.action_type != "close" and len(positions) >= config.settings.max_open_positions:
        if ev.symbol not in positions:
            log.warning(
                "[BLOCKED] %s / %s — max_open_positions=%s reached",
                ev.symbol,
                ev.rule_id,
                config.settings.max_open_positions,
            )
            return

    last = _last_price(ev.symbol, bars)
    if last is None:
        log.error("No last price for %s — cannot size order", ev.symbol)
        return
    sma_value = _signal_sma(rule, ev.symbol, bars)
    if ev.action_type != "close" and rule.action.stop_mode == "sma20":
        side = "buy" if ev.action_type == "buy" else "sell"
        if sma_value is None:
            log.info(
                "[SKIP] %s / %s — stop_mode sma20 but SMA(%s) unavailable",
                ev.symbol,
                ev.rule_id,
                rule.action.stop_sma_period,
            )
            return
        if not sma_stop_valid(side, last, sma_value):
            log.info(
                "[SKIP] %s / %s — SMA%s %.4f is not beyond last %.4f (stop_mode sma20)",
                ev.symbol,
                ev.rule_id,
                rule.action.stop_sma_period,
                sma_value,
                last,
            )
            return

    if ev.action_type != "close" and _entry_blocked_by_cutoff(rule, ev.symbol, config, bars):
        log.info(
            "[SKIP] %s / %s — entry_cutoff %s %s (fill would be at/after cutoff)",
            ev.symbol,
            ev.rule_id,
            config.settings.entry_cutoff,
            config.settings.session_timezone,
        )
        return

    if ev.action_type == "close":
        if ev.symbol not in positions:
            log.info("[SKIP] close %s / %s — no open position", ev.symbol, ev.rule_id)
            return
        log.info(
            "DECISION close %s | rule=%s | last=%.4f | why: %s",
            ev.symbol,
            ev.rule_id,
            last,
            ev.explain(),
        )
        broker.close_position(ev.symbol)
    else:
        order = build_order(
            symbol=ev.symbol,
            action=rule.action,
            account=account,
            last_price=last,
            position=positions.get(ev.symbol),
            sma_value=sma_value,
        )
        if order is None:
            log.error("Could not build order for %s / %s", ev.symbol, ev.rule_id)
            return
        log.info(
            "DECISION %s %s x%s %s last=%.4f stop=%s take=%s | rule=%s | why: %s",
            order.side.upper(),
            order.symbol,
            order.qty,
            order.order_type,
            last,
            f"{order.stop_loss_price:.4f}" if order.stop_loss_price else "-",
            f"{order.take_profit_price:.4f}" if order.take_profit_price else "-",
            ev.rule_id,
            ev.explain(),
        )
        broker.submit_order(order)

    if ev.signal_bar_ts is not None:
        state.mark_fired(
            fire_key(ev.rule_id, ev.symbol, ev.signal_bar_ts),
            cooldown_key(ev.rule_id, ev.symbol),
            rule.cooldown_minutes,
        )
        save_state(config.settings.state_file, state)
    if dry_run:
        log.info("DRY-RUN: order was not sent to Alpaca")


def last_rule_fire_ts(state: BotState, rule_id: str, symbol: str) -> Optional[datetime]:
    """Latest signal-bar timestamp marked fired for this rule+symbol."""
    prefix = f"{rule_id}:{symbol.upper()}:"
    times: list[datetime] = []
    for key in state.fired_keys:
        if key.startswith(prefix):
            times.append(parse_ts(key[len(prefix) :]))
    return max(times) if times else None


def _flatten_ma_cross(
    config: BotConfig,
    broker: Broker,
    bars,
    state: BotState,
    *,
    dry_run: bool,
) -> None:
    """Close paper/live lots when EMA crosses under SMA (long) after entry.

    Live fill is a market flatten on the next poll after the signal bar closes,
    matching the backtest next-bar-open convention as closely as the loop allows.
    Optional percent stop stays on the broker when stop_loss_pct is set.
    """
    kill_file = config.settings.kill_switch_file
    if is_active(kill_file):
        return
    positions = _position_map(broker.get_positions())
    for rule in config.rules:
        if not rule.enabled or rule.action.exit != "ma_cross":
            continue
        needed = condition_timeframes(rule.when)
        if not needed:
            continue
        fill_tf = min(needed, key=lambda t: duration(t))
        for symbol in config.symbols_for(rule):
            pos = positions.get(symbol.upper())
            if pos is None:
                continue
            series = bars.get((symbol.upper(), fill_tf), []) or []
            after = last_rule_fire_ts(state, rule.id, symbol)
            hit = ma_pair_cross_flatten_bar(
                pos,
                series,
                after=after,
                ema_period=rule.action.exit_ema_period,
                sma_period=rule.action.exit_sma_period,
            )
            if hit is None:
                continue
            log.info(
                "MA-cross flatten %s %s entry=%.4f EMA%s/SMA%s @%s rule=%s",
                pos.side,
                symbol,
                pos.avg_entry_price,
                rule.action.exit_ema_period,
                rule.action.exit_sma_period,
                hit.timestamp.isoformat(),
                rule.id,
            )
            broker.close_position(symbol)
            if dry_run:
                log.info("DRY-RUN: MA-cross flatten was not sent to Alpaca")


def _flatten_ema_invalid(
    config: BotConfig,
    broker: Broker,
    bars,
    state: BotState,
    *,
    dry_run: bool,
) -> None:
    """Close paper/live lots when a signal-timeframe close invalidates EMA.

    Long: close < EMA. If we cannot prove the bar is after entry (no fire key),
    skip flatten so a restart cannot dump a fresh fill. Optional catastrophic
    stop stays on the broker when stop_loss_pct is set.
    """
    kill_file = config.settings.kill_switch_file
    if is_active(kill_file):
        return
    positions = _position_map(broker.get_positions())
    for rule in config.rules:
        if not rule.enabled or rule.action.exit != "ema_invalid":
            continue
        needed = condition_timeframes(rule.when)
        if not needed:
            continue
        fill_tf = min(needed, key=lambda t: duration(t))
        for symbol in config.symbols_for(rule):
            pos = positions.get(symbol.upper())
            if pos is None:
                continue
            series = bars.get((symbol.upper(), fill_tf), []) or []
            after = last_rule_fire_ts(state, rule.id, symbol)
            hit = ema_cross_flatten_bar(
                pos, series, after=after, period=rule.action.exit_ema_period
            )
            if hit is None:
                continue
            log.info(
                "EMA-invalid flatten %s %s entry=%.4f close=%.4f EMA%s @%s rule=%s",
                pos.side,
                symbol,
                pos.avg_entry_price,
                hit.close,
                rule.action.exit_ema_period,
                hit.timestamp.isoformat(),
                rule.id,
            )
            broker.close_position(symbol)
            if dry_run:
                log.info("DRY-RUN: EMA-invalid flatten was not sent to Alpaca")


def _signal_sma(rule: RuleSpec, symbol: str, bars) -> Optional[float]:
    """SMA(stop_sma_period) on the finest rule timeframe through the last closed bar."""
    needed = condition_timeframes(rule.when)
    if not needed:
        return None
    fill_tf = min(needed, key=lambda t: duration(t))
    series = bars.get((symbol.upper(), fill_tf), []) or []
    if not series:
        return None
    return sma([b.close for b in series], rule.action.stop_sma_period)


def _entry_blocked_by_cutoff(
    rule: RuleSpec,
    symbol: str,
    config: BotConfig,
    bars,
    *,
    now: Optional[datetime] = None,
) -> bool:
    """Reject new entries whose fill (next-bar open) is at/after entry_cutoff."""
    cutoff = config.settings.entry_cutoff
    tz_name = config.settings.session_timezone
    if not cutoff:
        return False
    now = now or datetime.now(timezone.utc)
    if wall_clock_at_or_after(now, cutoff, tz_name):
        return True
    needed = condition_timeframes(rule.when)
    if not needed:
        return False
    fill_tf = min(needed, key=lambda t: duration(t))
    series = bars.get((symbol.upper(), fill_tf), []) or []
    if not series:
        return False
    fill_ts = series[-1].timestamp + duration(fill_tf)
    return fill_at_or_after_cutoff(fill_ts, cutoff, tz_name)


def _flatten_session(
    config: BotConfig,
    broker: Broker,
    bars,
    *,
    dry_run: bool,
    now: Optional[datetime] = None,
) -> None:
    """Force-flat open lots at/after flatten_by (wall clock or flatten-bar close).

    Live 15m: wall clock >= 15:55 ET closes the book (no 15:55 print on 15m).
    If the 15:45 bar has already closed, that close is also a flatten trigger.
    """
    flatten_by = config.settings.flatten_by
    tz_name = config.settings.session_timezone
    if not flatten_by:
        return
    kill_file = config.settings.kill_switch_file
    if is_active(kill_file):
        return
    now = now or datetime.now(timezone.utc)
    due_clock = wall_clock_at_or_after(now, flatten_by, tz_name)
    positions = _position_map(broker.get_positions())
    if not positions:
        return
    due_symbols: set[str] = set()
    if due_clock:
        due_symbols.update(positions)
    for (symbol, tf), series in bars.items():
        if not series or symbol not in positions:
            continue
        last = series[-1]
        if is_flatten_bar(last.timestamp, tf, flatten_by, tz_name):
            close_ts = last.timestamp + duration(tf)
            if now >= close_ts or due_clock:
                due_symbols.add(symbol)
    for symbol in sorted(due_symbols):
        pos = positions.get(symbol)
        if pos is None:
            continue
        log.info(
            "Session flatten %s %s entry=%.4f flatten_by=%s %s",
            pos.side,
            symbol,
            pos.avg_entry_price,
            flatten_by,
            tz_name,
        )
        broker.close_position(symbol)
        if dry_run:
            log.info("DRY-RUN: session flatten was not sent to Alpaca")


def run_once(
    config: BotConfig,
    *,
    broker: Broker,
    data: MarketData,
    state: BotState,
    dry_run: bool,
) -> list[EvalResult]:
    log.info(
        "Cycle start paper=%s dry_run=%s broker=%s kill=%s",
        config.settings.paper,
        dry_run,
        getattr(broker, "mode", "?"),
        kill_reason(config.settings.kill_switch_file) or "off",
    )
    bars = fetch_bars(config, data)
    _flatten_session(config, broker, bars, dry_run=dry_run)
    if any(rule.enabled and rule.action.exit == "ema_invalid" for rule in config.rules):
        _flatten_ema_invalid(config, broker, bars, state, dry_run=dry_run)
    if any(rule.enabled and rule.action.exit == "ma_cross" for rule in config.rules):
        _flatten_ma_cross(config, broker, bars, state, dry_run=dry_run)
    results = evaluate_all(config, bars, state)
    rules = {r.id: r for r in config.rules}
    fired = [ev for ev in results if ev.matched]
    log.info(
        "Cycle summary: %s evaluations, %s fires",
        len(results),
        len(fired),
    )
    for ev in fired:
        rule = rules[ev.rule_id]
        execute_decision(
            ev=ev,
            rule=rule,
            config=config,
            broker=broker,
            bars=bars,
            state=state,
            dry_run=dry_run,
        )
    return results


def run_loop(
    config: BotConfig,
    *,
    broker: Broker,
    data: MarketData,
    state: BotState,
    dry_run: bool,
    once: bool = False,
) -> None:
    interval = config.settings.poll_interval_seconds
    while True:
        started = datetime.now(timezone.utc)
        try:
            run_once(config, broker=broker, data=data, state=state, dry_run=dry_run)
        except Exception:
            log.exception("Cycle failed")
        if once:
            return
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        sleep_for = max(1.0, interval - elapsed)
        log.info("Sleeping %.1fs until next cycle", sleep_for)
        time.sleep(sleep_for)


def execute_orb_decision(
    *,
    ev: EvalResult,
    config: OrbBotConfig,
    broker: Broker,
    bars,
    state: BotState,
    dry_run: bool,
) -> None:
    kill_file = config.settings.kill_switch_file
    if is_active(kill_file):
        log.warning(
            "[BLOCKED] %s %s %s — %s — would have acted on: %s",
            ev.symbol,
            ev.action_type,
            ev.rule_id,
            kill_reason(kill_file),
            ev.explain(),
        )
        return

    setup = setup_from_eval(ev, bars, config)
    if setup is None:
        log.error("Could not rebuild ORB setup for %s / %s", ev.symbol, ev.rule_id)
        return

    account = broker.get_account()
    positions = _position_map(broker.get_positions())
    blocked = position_blocks_entry(setup, positions, config)
    if blocked:
        log.info("[SKIP] %s / %s — %s", ev.symbol, ev.rule_id, blocked)
        return
    if ev.action_type != "close" and len(positions) >= config.settings.max_open_positions:
        if ev.symbol not in positions:
            log.warning(
                "[BLOCKED] %s / %s — max_open_positions=%s reached",
                ev.symbol,
                ev.rule_id,
                config.settings.max_open_positions,
            )
            return

    if ev.symbol in positions and config.orb.on_open_position == "replace":
        log.info("ORB replace: closing existing %s before new %s", ev.symbol, setup.side)
        broker.close_position(ev.symbol)

    last = setup.reversal.close
    order = build_orb_order(setup, account=account, config=config, last_price=last)
    if order is None:
        log.error("Could not build ORB order for %s", ev.symbol)
        return
    log.info(
        "DECISION %s %s x%s %s last=%.4f stop=%s take=%s | %s | why: %s",
        order.side.upper(),
        order.symbol,
        order.qty,
        order.order_type,
        last,
        f"{order.stop_loss_price:.4f}" if order.stop_loss_price else "-",
        f"{order.take_profit_price:.4f}" if order.take_profit_price else "-",
        ev.rule_id,
        ev.explain(),
    )
    broker.submit_order(order)

    if ev.signal_bar_ts is not None:
        state.mark_fired(
            fire_key(ORB_RULE_ID, ev.symbol, ev.signal_bar_ts),
            cooldown_key(ORB_RULE_ID, ev.symbol),
            config.orb.cooldown_minutes,
        )
        save_state(config.settings.state_file, state)
    if dry_run:
        log.info("DRY-RUN: order was not sent to Alpaca")


def _flatten_first_profit(
    config: OrbBotConfig,
    broker: Broker,
    bars,
    state: BotState,
    *,
    dry_run: bool,
) -> None:
    """Close paper/live lots on a close-based take (EMA-cross or first-profit).

    Stop stays on the broker. If we cannot prove the bar is after entry
    (no fire key), skip flatten so a restart cannot dump a fresh fill.
    """
    kill_file = config.settings.kill_switch_file
    if is_active(kill_file):
        return
    positions = _position_map(broker.get_positions())
    sig_tf = config.orb.signal_timeframe
    for symbol in config.universe:
        pos = positions.get(symbol.upper())
        if pos is None:
            continue
        series = bars.get((symbol.upper(), sig_tf), []) or []
        after = last_reversal_ts(state, symbol)
        if config.orb.take_profit_mode == "ema_cross":
            hit = ema_cross_flatten_bar(
                pos, series, after=after, period=config.orb.ema_period
            )
            why = "EMA-cross"
        else:
            hit = first_profit_flatten_bar(pos, series, after=after)
            why = "first-profit"
        if hit is None:
            continue
        log.info(
            "ORB %s flatten %s %s entry=%.4f close=%.4f @%s",
            why,
            pos.side,
            symbol,
            pos.avg_entry_price,
            hit.close,
            hit.timestamp.isoformat(),
        )
        broker.close_position(symbol)
        if dry_run:
            log.info("DRY-RUN: %s flatten was not sent to Alpaca", why)


def run_orb_once(
    config: OrbBotConfig,
    *,
    broker: Broker,
    data: MarketData,
    state: BotState,
    dry_run: bool,
    scan_all: bool = False,
) -> list[EvalResult]:
    log.info(
        "ORB cycle start paper=%s dry_run=%s broker=%s kill=%s scan_all=%s",
        config.settings.paper,
        dry_run,
        getattr(broker, "mode", "?"),
        kill_reason(config.settings.kill_switch_file) or "off",
        scan_all,
    )
    bars = fetch_bars(config, data)
    if not scan_all and config.orb.take_profit_mode in {
        "first_profitable_close",
        "ema_cross",
    }:
        _flatten_first_profit(config, broker, bars, state, dry_run=dry_run)
    results = evaluate_orb(config, bars, state, scan_all=scan_all)
    fired = [ev for ev in results if ev.matched]
    for ev in results:
        # Always echo the decision line so `evaluate` is readable without log filters.
        print(ev.explain(), flush=True)
    log.info("ORB cycle summary: %s evaluations, %s fires", len(results), len(fired))
    if scan_all:
        return results
    for ev in fired:
        execute_orb_decision(
            ev=ev,
            config=config,
            broker=broker,
            bars=bars,
            state=state,
            dry_run=dry_run,
        )
    return results


def run_orb_loop(
    config: OrbBotConfig,
    *,
    broker: Broker,
    data: MarketData,
    state: BotState,
    dry_run: bool,
    once: bool = False,
    scan_all: bool = False,
) -> None:
    interval = config.settings.poll_interval_seconds
    while True:
        started = datetime.now(timezone.utc)
        try:
            run_orb_once(
                config,
                broker=broker,
                data=data,
                state=state,
                dry_run=dry_run,
                scan_all=scan_all,
            )
        except Exception:
            log.exception("ORB cycle failed")
        if once:
            return
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        sleep_for = max(1.0, interval - elapsed)
        log.info("Sleeping %.1fs until next cycle", sleep_for)
        time.sleep(sleep_for)
