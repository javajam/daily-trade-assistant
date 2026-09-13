"""Evaluate ORB probe/reversal setups and turn them into explained decisions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from dta_bot.config import ActionSpec
from dta_bot.engine import BarMap, cooldown_key, fire_key
from dta_bot.models import Account, Bar, EvalResult, OrderRequest, Position
from dta_bot.orb import (
    OpeningRange,
    OrbSetup,
    bar_session_date,
    find_all_setups,
    find_session_setups,
    live_setup,
    no_setup_reason,
    session_dt,
)
from dta_bot.orb_config import OrbBotConfig
from dta_bot.sizing import shares_for
from dta_bot.state import BotState, fmt_ts

log = logging.getLogger("dta_bot.orb")

RULE_ID = "orb_reversal"


def _bars(bars_by_key: BarMap, symbol: str, timeframe: str) -> list[Bar]:
    return list(bars_by_key.get((symbol.upper(), timeframe), []) or [])


def _session_date_for(config: OrbBotConfig, now: Optional[datetime], bars: list[Bar]):
    tz = config.orb.session_timezone
    if now is not None:
        return now.astimezone(ZoneInfo(tz)).date()
    if bars:
        return bar_session_date(bars[-1], tz)
    return datetime.now(timezone.utc).astimezone(ZoneInfo(tz)).date()


def _eval_from_setup(
    setup: OrbSetup,
    *,
    skipped: Optional[str] = None,
    edge_pct: float = 0.05,
) -> EvalResult:
    return EvalResult(
        rule_id=RULE_ID,
        symbol=setup.symbol,
        matched=skipped is None,
        reasons=[setup.explain()],
        action_type="buy" if setup.side == "buy" else "sell",
        signal_bar_ts=setup.reversal.timestamp,
        skipped=skipped,
        extra={
            "strategy": RULE_ID,
            "zone": setup.zone,
            "side": setup.side,
            "or_high": setup.opening_range.high,
            "or_low": setup.opening_range.low,
            "or_mid": setup.opening_range.midpoint,
            "band": setup.opening_range.band(edge_pct),
            "stop": setup.stop,
            "take": setup.take,
            "probe": setup.probe.summary(),
            "reversal": setup.reversal.summary(),
            "entry_open": setup.entry_bar.open if setup.entry_bar is not None else None,
        },
    )


def _eval_miss(
    symbol: str,
    opening_range: Optional[OpeningRange],
    signal_bars: list[Bar],
    config: OrbBotConfig,
    *,
    skipped: Optional[str] = None,
) -> EvalResult:
    why = no_setup_reason(
        opening_range=opening_range,
        signal_bars=signal_bars,
        edge_pct=config.orb.edge_pct,
        session_timezone=config.orb.session_timezone,
        session_close=config.orb.session_close,
    )
    extra: dict = {"strategy": RULE_ID}
    if opening_range is not None:
        extra.update(
            {
                "or_high": opening_range.high,
                "or_low": opening_range.low,
                "or_mid": opening_range.midpoint,
            }
        )
    return EvalResult(
        RULE_ID,
        symbol,
        False,
        [why],
        skipped=skipped,
        extra=extra,
    )


def setups_for_symbol(config: OrbBotConfig, symbol: str, bars_by_key: BarMap) -> list[OrbSetup]:
    return find_all_setups(
        symbol,
        orb_bars=_bars(bars_by_key, symbol, config.orb.orb_timeframe),
        signal_bars=_bars(bars_by_key, symbol, config.orb.signal_timeframe),
        session_open=config.orb.session_open,
        session_timezone=config.orb.session_timezone,
        session_close=config.orb.session_close,
        orb_timeframe=config.orb.orb_timeframe,
        signal_timeframe=config.orb.signal_timeframe,
        edge_pct=config.orb.edge_pct,
    )


def evaluate_orb_symbol(
    config: OrbBotConfig,
    symbol: str,
    bars_by_key: BarMap,
    state: BotState,
    *,
    now: Optional[datetime] = None,
    scan_all: bool = False,
) -> list[EvalResult]:
    """Return one result per detected setup (scan_all) or the live reversal bar."""
    symbol = symbol.upper()
    orb_tf = config.orb.orb_timeframe
    sig_tf = config.orb.signal_timeframe
    orb_bars = _bars(bars_by_key, symbol, orb_tf)
    signal_bars = _bars(bars_by_key, symbol, sig_tf)

    if scan_all:
        setups = setups_for_symbol(config, symbol, bars_by_key)
        if not setups:
            rng, _ = find_session_setups(
                symbol,
                orb_bars=orb_bars,
                signal_bars=signal_bars,
                session_date=_session_date_for(config, now, orb_bars or signal_bars),
                session_open=config.orb.session_open,
                session_timezone=config.orb.session_timezone,
                session_close=config.orb.session_close,
                orb_timeframe=orb_tf,
                signal_timeframe=sig_tf,
                edge_pct=config.orb.edge_pct,
            )
            return [_eval_miss(symbol, rng, signal_bars, config)]
        results: list[EvalResult] = []
        for setup in setups:
            cd_until = state.on_cooldown(cooldown_key(RULE_ID, symbol), now=now)
            if cd_until:
                results.append(
                    _eval_from_setup(setup, skipped="cooldown", edge_pct=config.orb.edge_pct)
                )
                results[-1].reasons.append(f"cooldown until {fmt_ts(cd_until)}")
                results[-1].matched = False
                continue
            if setup.reversal.timestamp and state.already_fired(
                fire_key(RULE_ID, symbol, setup.reversal.timestamp)
            ):
                results.append(
                    _eval_from_setup(setup, skipped="already_fired", edge_pct=config.orb.edge_pct)
                )
                continue
            results.append(_eval_from_setup(setup, edge_pct=config.orb.edge_pct))
        return results

    session_date = _session_date_for(config, now, orb_bars or signal_bars)
    if now is not None:
        open_dt = session_dt(session_date, config.orb.session_open, config.orb.session_timezone)
        if now < open_dt:
            return [
                EvalResult(
                    RULE_ID,
                    symbol,
                    False,
                    [f"session open {config.orb.session_open} {config.orb.session_timezone} not reached"],
                    skipped="pre_open",
                    extra={"strategy": RULE_ID},
                )
            ]

    rng, setups = find_session_setups(
        symbol,
        orb_bars=orb_bars,
        signal_bars=signal_bars,
        session_date=session_date,
        session_open=config.orb.session_open,
        session_timezone=config.orb.session_timezone,
        session_close=config.orb.session_close,
        orb_timeframe=orb_tf,
        signal_timeframe=sig_tf,
        edge_pct=config.orb.edge_pct,
    )
    hit = live_setup(setups, signal_bars)
    if hit is None:
        return [_eval_miss(symbol, rng, signal_bars, config)]

    cd_until = state.on_cooldown(cooldown_key(RULE_ID, symbol), now=now)
    if cd_until:
        ev = _eval_from_setup(hit, skipped="cooldown", edge_pct=config.orb.edge_pct)
        ev.reasons.append(f"cooldown until {fmt_ts(cd_until)}")
        ev.matched = False
        return [ev]
    if state.already_fired(fire_key(RULE_ID, symbol, hit.reversal.timestamp)):
        return [_eval_from_setup(hit, skipped="already_fired", edge_pct=config.orb.edge_pct)]
    return [_eval_from_setup(hit, edge_pct=config.orb.edge_pct)]


def evaluate_orb(
    config: OrbBotConfig,
    bars_by_key: BarMap,
    state: BotState,
    *,
    now: Optional[datetime] = None,
    scan_all: bool = False,
) -> list[EvalResult]:
    results: list[EvalResult] = []
    for symbol in config.universe:
        for ev in evaluate_orb_symbol(
            config, symbol, bars_by_key, state, now=now, scan_all=scan_all
        ):
            log.info("%s", ev.explain())
            results.append(ev)
    if not config.universe:
        log.warning("ORB universe is empty — add symbols in YAML (a morning screener will populate this later)")
    return results


def build_orb_order(
    setup: OrbSetup,
    *,
    account: Account,
    config: OrbBotConfig,
    last_price: Optional[float] = None,
) -> Optional[OrderRequest]:
    px = last_price if last_price is not None else setup.reversal.close
    action = ActionSpec(
        type="buy" if setup.side == "buy" else "sell",
        size=config.sizing,
        order=config.order.type,
        limit_offset_pct=config.order.limit_offset_pct,
        time_in_force=config.order.time_in_force,
    )
    try:
        qty = shares_for(action, account, px)
    except ValueError:
        return None
    limit = None
    if config.order.type == "limit":
        offset = (config.order.limit_offset_pct or 0.0) / 100.0
        limit = px * (1.0 + offset) if setup.side == "buy" else px * (1.0 - offset)
    return OrderRequest(
        symbol=setup.symbol,
        side=setup.side,
        qty=qty,
        order_type=config.order.type,
        time_in_force=config.order.time_in_force,
        limit_price=limit,
        stop_loss_price=setup.stop,
        take_profit_price=setup.take,
    )


def setup_from_eval(ev: EvalResult, bars_by_key: BarMap, config: OrbBotConfig) -> Optional[OrbSetup]:
    if ev.signal_bar_ts is None:
        return None
    for setup in setups_for_symbol(config, ev.symbol, bars_by_key):
        if setup.reversal.timestamp == ev.signal_bar_ts:
            return setup
    return None


def position_blocks_entry(
    setup: OrbSetup,
    positions: dict[str, Position],
    config: OrbBotConfig,
) -> Optional[str]:
    pos = positions.get(setup.symbol.upper())
    if pos is None:
        return None
    if config.orb.on_open_position == "replace":
        return None
    return "already_in_position"
