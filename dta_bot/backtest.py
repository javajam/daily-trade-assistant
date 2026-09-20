"""Replay YAML rules over historical bars using the live evaluation engine.

Fills, stops, and take-profits are simulated here; pattern / SMA / RSI / volume
matches always go through ``evaluate_rule`` so detectors stay in one place.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from dta_bot.config import (
    ENTRY_STOP_MODES,
    ActionSpec,
    AnyCondition,
    BotConfig,
    GroupCond,
    RuleSpec,
)
from dta_bot.engine import (
    BarMap,
    cooldown_key,
    evaluate_rule,
    fire_key,
    lower_high_exit,
    range_expansion_exit,
)
from dta_bot.models import Account, Bar
from dta_bot.indicators import atr, ma_pair_cross, sma
from dta_bot.orb import ema_cross_exit, ema_through
from dta_bot.period_stats import build_period_stats, format_period_stats_md, session_date
from dta_bot.session import fill_at_or_after_cutoff, is_flatten_bar
from dta_bot.sizing import atr_stop_price, bracket_prices, buy_notional, shares_for, sma_stop_valid
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
    breakeven_armed: bool = False
    lock_armed: bool = False
    trail_ratcheted: bool = False
    pyramid_added: bool = False
    pyramid_add_skipped: bool = False
    partial_take: bool = False
    partial_take_qty: float = 0.0
    partial_take_price: Optional[float] = None
    partial_take_pnl: float = 0.0
    partial_take_skipped_size: bool = False
    stop: Optional[float] = None

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
    exit_mode: str = "fixed_bracket"
    exit_ema_period: int = 9
    exit_sma_period: int = 20
    exit_range_bars: int = 3
    exit_range_skip_doji: bool = False
    exit_range_doji_frac: float = 0.10
    completed_bars: int = 0
    breakeven_after_bars: int = 0
    breakeven_requires_valid: bool = True
    breakeven_valid: str = "above_ema"
    breakeven_ema_period: int = 9
    breakeven_armed: bool = False
    breakeven_checked: bool = False
    stop_mode: str = "percent"
    stop_loss_pct: Optional[float] = None
    lock_trigger_pct: Optional[float] = None
    lock_stop_pct: Optional[float] = None
    trail_pct: Optional[float] = None
    stop_atr_mult: float = 1.0
    stop_atr_period: int = 14
    atr_value: Optional[float] = None
    peak_price: Optional[float] = None
    lock_armed: bool = False
    trail_ratcheted: bool = False
    pyramid_on_lock: bool = False
    pyramid_add_pct: Optional[float] = None
    pyramid_added: bool = False
    pyramid_add_skipped: bool = False
    base_qty: float = 0.0
    cost_basis: float = 0.0
    take_anchor: str = "signal"
    take_profit_pct: Optional[float] = None
    partial_take_on_lock: bool = False
    partial_take_be: bool = False
    partial_take: bool = False
    partial_take_skipped_size: bool = False
    partial_take_qty: float = 0.0
    partial_take_price: Optional[float] = None
    partial_take_pnl: float = 0.0


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
    exit_mode: str = "fixed_bracket"
    exit_ema_period: int = 9
    exit_sma_period: int = 20
    exit_range_bars: int = 3
    exit_range_skip_doji: bool = False
    exit_range_doji_frac: float = 0.10
    close_reason: str = "close_signal"
    stop_mode: str = "percent"
    stop_loss_pct: Optional[float] = None
    lock_trigger_pct: Optional[float] = None
    lock_stop_pct: Optional[float] = None
    trail_pct: Optional[float] = None
    stop_atr_mult: float = 1.0
    stop_atr_period: int = 14
    atr_value: Optional[float] = None
    breakeven_after_bars: int = 0
    breakeven_requires_valid: bool = True
    breakeven_valid: str = "above_ema"
    breakeven_ema_period: int = 9
    pyramid_on_lock: bool = False
    pyramid_add_pct: Optional[float] = None
    take_anchor: str = "signal"
    take_profit_pct: Optional[float] = None
    partial_take_on_lock: bool = False
    partial_take_be: bool = False


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
    skip_reasons: dict[str, int] = field(default_factory=dict)
    signals_by_symbol: dict[str, int] = field(default_factory=dict)
    trades_by_symbol: dict[str, int] = field(default_factory=dict)
    sides: dict[str, dict[str, Any]] = field(default_factory=dict)
    breakeven_armed: int = 0
    lock_armed: int = 0
    trail_ratcheted: int = 0
    pyramid_added: int = 0
    pyramid_add_skipped: int = 0
    partial_take: int = 0
    partial_take_pnl: float = 0.0
    partial_take_skipped_size: int = 0

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
    period_stats: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "report": self.report.to_dict(),
            "trades": [t.to_dict() for t in self.trades],
            "signals": [s.to_dict() for s in self.signals],
            "equity_curve": [[_iso(t), eq] for t, eq in self.equity_curve],
            "bars_used": self.bars_used,
            "period_stats": self.period_stats,
        }


def _next_bar(series: list[Bar], after_ts: datetime) -> Optional[Bar]:
    after_ts = _aware(after_ts)
    for bar in series:
        if _aware(bar.timestamp) > after_ts:
            return bar
    return None


def _prev_n_bars(series: list[Bar], ts: datetime, n: int) -> Optional[list[Bar]]:
    """The ``n`` bars immediately before ``ts``, or None if fewer than ``n`` exist."""
    if n < 1:
        return None
    ts = _aware(ts)
    prior: list[Bar] = []
    for bar in series:
        if _aware(bar.timestamp) >= ts:
            break
        prior.append(bar)
    if len(prior) < n:
        return None
    return prior[-n:]


def _prev_bar(series: list[Bar], ts: datetime) -> Optional[Bar]:
    ts = _aware(ts)
    prev: Optional[Bar] = None
    for bar in series:
        if _aware(bar.timestamp) >= ts:
            return prev
        prev = bar
    return prev


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


def _effective_take(lot: OpenLot) -> Optional[float]:
    """Take is live only after lock when pyramid_on_lock is on.

    Before the lock arms, a bar that tags fill×1.02 must add first, then
    take the full (doubled) position — not flatten the original lot at 1.02.
    """
    if lot.pyramid_on_lock and not lot.lock_armed:
        return None
    return lot.take


def _stop_take_hit(bar: Bar, lot: OpenLot) -> Optional[tuple[str, float]]:
    """Return (reason, fill_price) if stop/take is touched on this bar.

    Conservative same-bar rule: if both levels trade, assume stop fills first.
    Gaps through a level fill at the open.
    """
    take = _effective_take(lot)
    if lot.side == "buy":
        if lot.stop is not None and bar.open <= lot.stop:
            return "stop", bar.open
        if take is not None and bar.open >= take:
            return "take", bar.open
        stop_hit = lot.stop is not None and bar.low <= lot.stop
        take_hit = take is not None and bar.high >= take
        if stop_hit and take_hit:
            return "stop", lot.stop
        if stop_hit:
            return "stop", lot.stop
        if take_hit:
            return "take", take
        return None
    if lot.stop is not None and bar.open >= lot.stop:
        return "stop", bar.open
    if take is not None and bar.open <= take:
        return "take", bar.open
    stop_hit = lot.stop is not None and bar.high >= lot.stop
    take_hit = take is not None and bar.low <= take
    if stop_hit and take_hit:
        return "stop", lot.stop
    if stop_hit:
        return "stop", lot.stop
    if take_hit:
        return "take", take
    return None


def _take_only_hit(bar: Bar, lot: OpenLot) -> Optional[tuple[str, float]]:
    """Take check used on the lock-arm bar after the add (do not re-check stop).

    The locked stop is live from the *next* bar. Re-running the full stop/take
    check after arming would lock_stop the doubled lot on the same bar's low.
    """
    if lot.take is None:
        return None
    if lot.side == "buy":
        if bar.open >= lot.take:
            return "take", bar.open
        if bar.high >= lot.take:
            return "take", lot.take
        return None
    if bar.open <= lot.take:
        return "take", bar.open
    if bar.low <= lot.take:
        return "take", lot.take
    return None


def _take_exit_reason(lot: OpenLot) -> str:
    if lot.take_anchor == "entry" and lot.take_profit_pct is not None:
        if abs(lot.take_profit_pct - 2.0) < 1e-9:
            return "take_2pct"
    return "take"


def _breakeven_fields(action: ActionSpec) -> dict[str, Any]:
    return {
        "breakeven_after_bars": action.breakeven_after_bars,
        "breakeven_requires_valid": action.breakeven_requires_valid,
        "breakeven_valid": action.breakeven_valid,
        "breakeven_ema_period": action.breakeven_ema_period,
    }


def _exit_range_fields(action: ActionSpec) -> dict[str, Any]:
    return {
        "exit_range_bars": action.exit_range_bars,
        "exit_range_skip_doji": action.exit_range_skip_doji,
        "exit_range_doji_frac": action.exit_range_doji_frac,
    }


def _stop_manage_fields(action: ActionSpec) -> dict[str, Any]:
    return {
        "stop_mode": action.stop_mode,
        "stop_loss_pct": action.stop_loss_pct,
        "lock_trigger_pct": action.resolved_lock_trigger_pct(),
        "lock_stop_pct": action.resolved_lock_stop_pct(),
        "trail_pct": action.resolved_trail_pct(),
        "stop_atr_mult": action.stop_atr_mult,
        "stop_atr_period": action.stop_atr_period,
        "pyramid_on_lock": action.pyramid_on_lock,
        "pyramid_add_pct": action.pyramid_add_pct,
        "take_anchor": action.take_anchor,
        "take_profit_pct": action.take_profit_pct,
        "partial_take_on_lock": action.partial_take_on_lock,
        "partial_take_be": action.partial_take_be,
    }


def _entry_anchored_take(side: str, entry_price: float, pct: Optional[float]) -> Optional[float]:
    if pct is None or entry_price <= 0:
        return None
    if side == "buy":
        return _pct_level(entry_price, pct, above=True)
    return _pct_level(entry_price, pct, above=False)


def _pct_level(price: float, pct: float, *, above: bool) -> float:
    return price * (1.0 + pct / 100.0) if above else price * (1.0 - pct / 100.0)


def _entry_anchored_stop(side: str, entry_price: float, pct: Optional[float]) -> Optional[float]:
    if pct is None or entry_price <= 0:
        return None
    if side == "buy":
        return _pct_level(entry_price, pct, above=False)
    return _pct_level(entry_price, pct, above=True)


def _maybe_arm_lock(lot: OpenLot, bar: Bar) -> bool:
    """Arm lock_plus on first trade/touch of entry × (1 + lock_trigger_pct/100).

    The locked stop is live from the *next* bar. Same-bar pullback after the
    tag still uses the initial entry×(1 − stop_loss_pct/100) stop.
    Returns True when the lock newly armed on this bar.
    """
    if lot.lock_armed or lot.stop_mode != "lock_plus":
        return False
    # Variant C already converted the +1% event to a BE remainder stop.
    if lot.partial_take_be and lot.breakeven_armed:
        return False
    trigger_pct = lot.lock_trigger_pct
    lock_pct = lot.lock_stop_pct
    if trigger_pct is None or lock_pct is None:
        return False
    if lot.side == "buy":
        trigger = _pct_level(lot.entry_price, trigger_pct, above=True)
        touched = bar.high >= trigger
        new_stop = _pct_level(lot.entry_price, lock_pct, above=True)
    else:
        trigger = _pct_level(lot.entry_price, trigger_pct, above=False)
        touched = bar.low <= trigger
        new_stop = _pct_level(lot.entry_price, lock_pct, above=False)
    if not touched:
        return False
    lot.stop = new_stop
    lot.lock_armed = True
    return True


def _pyramid_add_trigger_pct(lot: OpenLot) -> Optional[float]:
    """Percent from original fill that arms the intra-lot add.

    Explicit ``pyramid_add_pct`` (e.g. 0.5) wins. ``pyramid_on_lock`` falls
    back to the lock trigger so the add and lock share a print.
    """
    if lot.pyramid_add_pct is not None:
        return lot.pyramid_add_pct
    if lot.pyramid_on_lock:
        return lot.lock_trigger_pct
    return None


def _pyramid_add_touched(lot: OpenLot, bar: Bar) -> bool:
    pct = _pyramid_add_trigger_pct(lot)
    if pct is None or lot.entry_price <= 0:
        return False
    if lot.side == "buy":
        return bar.high >= _pct_level(lot.entry_price, pct, above=True)
    return bar.low <= _pct_level(lot.entry_price, pct, above=False)


def _pyramid_add_price(lot: OpenLot, bar: Bar) -> Optional[float]:
    """Fill the add at the same gap-through convention as stops.

    Trigger = original fill × (1 ± add_pct/100). If the bar opens through
    the trigger, the add fills at the open; otherwise at the trigger
    (the high/low tagged it).
    """
    trigger_pct = _pyramid_add_trigger_pct(lot)
    if trigger_pct is None or lot.entry_price <= 0:
        return None
    if lot.side == "buy":
        trigger = _pct_level(lot.entry_price, trigger_pct, above=True)
        return bar.open if bar.open >= trigger else trigger
    trigger = _pct_level(lot.entry_price, trigger_pct, above=False)
    return bar.open if bar.open <= trigger else trigger


def _try_pyramid_add(
    lot: OpenLot,
    bar: Bar,
    cash: float,
    commission: float,
    slippage_pct: float,
) -> tuple[float, bool]:
    """Add ``base_qty`` at the add-trigger print. Returns (cash, skipped_for_cash).

    Does not pre-reserve cash at entry. A cash skip is attempted once; lock
    can still arm later. Not a second EMA signal.
    """
    if lot.pyramid_added or lot.pyramid_add_skipped:
        return cash, False
    if _pyramid_add_trigger_pct(lot) is None:
        return cash, False
    if not _pyramid_add_touched(lot, bar):
        return cash, False
    add_qty = lot.base_qty if lot.base_qty >= 1 else lot.qty
    if add_qty < 1:
        return cash, False
    raw_px = _pyramid_add_price(lot, bar)
    if raw_px is None:
        return cash, False
    add_px = _apply_slippage(raw_px, lot.side, slippage_pct, is_entry=True)
    if lot.side == "buy":
        cost = buy_notional(add_qty, add_px, commission)
        if cost > cash + 1e-9:
            lot.pyramid_add_skipped = True
            return cash, True
        cash -= cost
        lot.cost_basis += add_qty * add_px
    else:
        cash += add_qty * add_px - commission
        lot.cost_basis += add_qty * add_px
    lot.qty += add_qty
    lot.pyramid_added = True
    return cash, False


def _maybe_ratchet_trail(lot: OpenLot, bar: Bar) -> None:
    """Ratchet trail stop to peak_price_since_entry × (1 − trail_pct/100).

    Peak updates from this bar's extreme *after* the current-stop check, so
    the new trail is live from the next bar. Ratchets favorable only.
    """
    if lot.stop_mode != "trail":
        return
    pct = lot.trail_pct
    if pct is None:
        return
    peak = lot.peak_price if lot.peak_price is not None else lot.entry_price
    if lot.side == "buy":
        peak = max(peak, bar.high)
        new_stop = _pct_level(peak, pct, above=False)
        if lot.stop is None or new_stop > lot.stop:
            lot.stop = new_stop
            if peak > lot.entry_price + 1e-12:
                lot.trail_ratcheted = True
    else:
        peak = min(peak, bar.low)
        new_stop = _pct_level(peak, pct, above=True)
        if lot.stop is None or new_stop < lot.stop:
            lot.stop = new_stop
            if peak < lot.entry_price - 1e-12:
                lot.trail_ratcheted = True
    lot.peak_price = peak


def _maybe_manage_stop(lot: OpenLot, bar: Bar) -> bool:
    just_armed = _maybe_arm_lock(lot, bar)
    _maybe_ratchet_trail(lot, bar)
    return just_armed


def _partial_take_qty(qty: float) -> float:
    """Shares to scale out: floor(half), leaving ≥1 when size ≥ 2. Size 1 → 0."""
    if qty < 2:
        return 0.0
    return float(math.floor(qty / 2.0))


def _lock_trigger_fill_price(lot: OpenLot, bar: Bar) -> Optional[float]:
    """Gap-through fill at the lock trigger (same convention as stops/adds)."""
    trigger_pct = lot.lock_trigger_pct
    if trigger_pct is None or lot.entry_price <= 0:
        return None
    if lot.side == "buy":
        trigger = _pct_level(lot.entry_price, trigger_pct, above=True)
        return bar.open if bar.open >= trigger else trigger
    trigger = _pct_level(lot.entry_price, trigger_pct, above=False)
    return bar.open if bar.open <= trigger else trigger


def _try_partial_take_on_lock(
    lot: OpenLot,
    bar: Bar,
    cash: float,
    commission: float,
    slippage_pct: float,
) -> float:
    """Sell half at the lock-arm print; lock already rests on the remainder.

    Size 1 skips the scale-out and keeps the single share (still locked).
    Locked stop is live next bar — do not re-check stop after this.
    """
    if not (lot.partial_take_on_lock or lot.partial_take_be) or lot.partial_take or not lot.lock_armed:
        return cash
    take_qty = _partial_take_qty(lot.qty)
    if take_qty < 1:
        lot.partial_take_skipped_size = True
        return cash
    raw_px = _lock_trigger_fill_price(lot, bar)
    if raw_px is None:
        return cash
    take_px = _apply_slippage(raw_px, lot.side, slippage_pct, is_entry=False)
    if lot.side == "buy":
        cash += take_qty * take_px - commission
        pnl = take_qty * (take_px - lot.entry_price) - commission
    else:
        cash -= take_qty * take_px + commission
        pnl = take_qty * (lot.entry_price - take_px) - commission
    if lot.cost_basis:
        frac = take_qty / lot.qty if lot.qty else 0.0
        lot.cost_basis -= lot.cost_basis * frac
    lot.qty -= take_qty
    lot.partial_take = True
    lot.partial_take_qty = take_qty
    lot.partial_take_price = take_px
    lot.partial_take_pnl = pnl
    return cash


def _lock_arm_pyramid_then_take(
    lot: OpenLot,
    bar: Bar,
    cash: float,
    commission: float,
    slippage_pct: float,
) -> tuple[float, bool, Optional[tuple[str, float]]]:
    """After stop/take miss: add if the add print tagged, then lock, then take.

    Add-before-lock so a bar that gaps through +0.5% and +1% (no earlier
    +0.5% bar) still doubles first, then arms the lock on the full lot.
    Locked stop is live next bar; take is checked only on the arm bar.
    partial_take_on_lock scales out half at the lock print after the lock arms.
    partial_take_be then rests the remainder stop at original fill (BE),
    live next bar — not lock at +1%.
    """
    cash, skipped = _try_pyramid_add(lot, bar, cash, commission, slippage_pct)
    just_armed = _maybe_manage_stop(lot, bar)
    if just_armed:
        cash = _try_partial_take_on_lock(lot, bar, cash, commission, slippage_pct)
        if lot.partial_take_be:
            lot.stop = lot.entry_price
            lot.breakeven_armed = True
            lot.lock_armed = False
    take_hit = _take_only_hit(bar, lot) if just_armed else None
    return cash, skipped, take_hit


def _stop_exit_reason(lot: OpenLot) -> str:
    if lot.lock_armed:
        return "lock_stop"
    if lot.stop_mode == "trail":
        return "trail_stop"
    if lot.breakeven_armed:
        return "breakeven_stop"
    return "stop"


def _breakeven_trade_valid(lot: OpenLot, bar: Bar, series: list[Bar]) -> bool:
    """True when the evaluation-bar close still qualifies for a BE move.

    Long valid (``above_ema``): close > EMA(period) on this timeframe.
    Short valid: close < EMA(period). A missing EMA is not valid.
    ``always`` (or ``breakeven_requires_valid`` off) always qualifies.
    """
    if not lot.breakeven_requires_valid or lot.breakeven_valid == "always":
        return True
    ema_val = ema_through(series, bar, lot.breakeven_ema_period)
    if ema_val is None:
        return False
    if lot.side == "buy":
        return bar.close > ema_val
    return bar.close < ema_val


def _closes_through(series: list[Bar], bar: Bar) -> Optional[list[float]]:
    closes: list[float] = []
    target = _aware(bar.timestamp)
    for item in series:
        closes.append(item.close)
        if _aware(item.timestamp) == target:
            return closes
    return None


def _ma_pair_cross_exit(lot: OpenLot, bar: Bar, series: list[Bar]) -> bool:
    """True when EMA crossed SMA against the lot on this closed bar.

    Long: previous EMA >= previous SMA and current EMA < current SMA.
    Short: previous EMA <= previous SMA and current EMA > current SMA.
    """
    closes = _closes_through(series, bar)
    if not closes:
        return False
    direction = "bearish" if lot.side == "buy" else "bullish"
    hit = ma_pair_cross(
        closes,
        lot.exit_ema_period,
        lot.exit_sma_period,
        direction=direction,
    )
    return bool(hit)


def _sma_through(series: list[Bar], bar: Bar, period: int) -> Optional[float]:
    """SMA(period) of closes through ``bar`` (inclusive)."""
    closes = _closes_through(series, bar)
    if not closes:
        return None
    return sma(closes, period)


def _signal_sma_stop(
    action: ActionSpec,
    series: list[Bar],
    signal_bar_ts: Optional[datetime],
) -> Optional[float]:
    if action.stop_mode != "sma20" or signal_bar_ts is None:
        return None
    target = _aware(signal_bar_ts)
    signal_bar = next((item for item in series if _aware(item.timestamp) == target), None)
    if signal_bar is None:
        return None
    return _sma_through(series, signal_bar, action.stop_sma_period)


def _bars_through(series: list[Bar], bar: Bar) -> Optional[list[Bar]]:
    out: list[Bar] = []
    target = _aware(bar.timestamp)
    for item in series:
        out.append(item)
        if _aware(item.timestamp) == target:
            return out
    return None


def _signal_atr(
    action: ActionSpec,
    series: list[Bar],
    signal_bar_ts: Optional[datetime],
) -> Optional[float]:
    """Wilder ATR(stop_atr_period) through the closed signal/entry bar."""
    if action.stop_mode != "atr" or signal_bar_ts is None:
        return None
    target = _aware(signal_bar_ts)
    signal_bar = next((item for item in series if _aware(item.timestamp) == target), None)
    if signal_bar is None:
        return None
    window = _bars_through(series, signal_bar)
    if not window:
        return None
    return atr(
        [b.high for b in window],
        [b.low for b in window],
        [b.close for b in window],
        action.stop_atr_period,
    )


def _open_side(lots: list[OpenLot], symbol: str) -> Optional[str]:
    for lot in lots:
        if lot.symbol == symbol:
            return lot.side
    return None


def _action_side(action: str) -> str:
    return "buy" if action == "buy" else "sell"


def _side_stats(trades: list[Trade], starting_equity: float) -> dict[str, dict[str, Any]]:
    """Trades / win rate / P&L by lot side. Max DD stays on the isolated book."""
    out: dict[str, dict[str, Any]] = {}
    for side in ("buy", "sell"):
        group = [t for t in trades if t.side == side]
        if not group:
            continue
        wins = [t for t in group if t.pnl > 0]
        losses = [t for t in group if t.pnl < 0]
        pnl = sum(t.pnl for t in group)
        closed = len(group)
        reasons: dict[str, int] = {}
        for t in group:
            reasons[t.exit_reason] = reasons.get(t.exit_reason, 0) + 1
        out[side] = {
            "trades": closed,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": (len(wins) / closed * 100.0) if closed else None,
            "total_pnl": pnl,
            "total_pnl_pct": (pnl / starting_equity * 100.0) if starting_equity else 0.0,
            "avg_win": (sum(t.pnl for t in wins) / len(wins)) if wins else None,
            "avg_loss": (sum(t.pnl for t in losses) / len(losses)) if losses else None,
            "exit_reasons": reasons,
            "lock_armed": sum(1 for t in group if t.lock_armed),
        }
    return out


def _exit_pnl_note(trades: list[Trade]) -> Optional[str]:
    if not trades:
        return None
    grouped: dict[str, list[Trade]] = {}
    for trade in trades:
        grouped.setdefault(trade.exit_reason, []).append(trade)
    parts = [
        f"{reason} ${sum(t.pnl for t in group):,.2f} ({len(group)} trade(s))"
        for reason, group in sorted(grouped.items())
    ]
    return "Exit P&L: " + "; ".join(parts) + "."


def _maybe_arm_breakeven(lot: OpenLot, bar: Bar, series: list[Bar]) -> None:
    """After one (or N) complete bars *after* the entry bar, move stop to entry.

    Evaluated at that bar's close, only if the lot is still open. Same-bar
    stop/take already ran; a BE move applies to later bars only. If the
    trade is not valid, leave the original stop (do not retry later).
    """
    if lot.breakeven_armed or lot.breakeven_checked:
        return
    if lot.breakeven_after_bars <= 0:
        return
    if _aware(bar.timestamp) == _aware(lot.entry_time):
        return
    lot.completed_bars += 1
    if lot.completed_bars < lot.breakeven_after_bars:
        return
    lot.breakeven_checked = True
    if not _breakeven_trade_valid(lot, bar, series):
        return
    lot.stop = lot.entry_price
    lot.breakeven_armed = True


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
        if lot.pyramid_added:
            basis = lot.cost_basis if lot.cost_basis else lot.qty * lot.entry_price
            remainder_pnl = proceeds - basis - commission
        else:
            remainder_pnl = lot.qty * (fill - lot.entry_price) - commission
    else:
        cost = lot.qty * fill
        cash -= cost + commission
        if lot.pyramid_added:
            basis = lot.cost_basis if lot.cost_basis else lot.qty * lot.entry_price
            remainder_pnl = basis - cost - commission
        else:
            remainder_pnl = lot.qty * (lot.entry_price - fill) - commission
    pnl = remainder_pnl + lot.partial_take_pnl
    orig_qty = (lot.qty + lot.partial_take_qty) if lot.partial_take else lot.qty
    notional = orig_qty * lot.entry_price
    if lot.pyramid_added and lot.cost_basis:
        notional = lot.cost_basis + (
            lot.partial_take_qty * lot.entry_price if lot.partial_take else 0.0
        )
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
        breakeven_armed=lot.breakeven_armed,
        lock_armed=lot.lock_armed,
        trail_ratcheted=lot.trail_ratcheted,
        pyramid_added=lot.pyramid_added,
        pyramid_add_skipped=lot.pyramid_add_skipped,
        partial_take=lot.partial_take,
        partial_take_qty=lot.partial_take_qty,
        partial_take_price=lot.partial_take_price,
        partial_take_pnl=lot.partial_take_pnl,
        partial_take_skipped_size=lot.partial_take_skipped_size,
        stop=lot.stop,
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
    skips: dict[str, int] = {}
    for s in signals:
        if s.skip_reason:
            skips[s.skip_reason] = skips.get(s.skip_reason, 0) + 1
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
        skip_reasons=skips,
        signals_by_symbol=by_sig,
        trades_by_symbol=by_tr,
        sides=_side_stats(trades, starting_equity),
        breakeven_armed=sum(1 for t in trades if t.breakeven_armed),
        lock_armed=sum(1 for t in trades if t.lock_armed),
        pyramid_added=sum(1 for t in trades if t.pyramid_added),
        pyramid_add_skipped=sum(1 for t in trades if t.pyramid_add_skipped),
        partial_take=sum(1 for t in trades if t.partial_take),
        partial_take_pnl=sum(t.partial_take_pnl for t in trades if t.partial_take),
        partial_take_skipped_size=sum(1 for t in trades if t.partial_take_skipped_size),
        trail_ratcheted=sum(1 for t in trades if t.trail_ratcheted),
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
    trade_start: Optional[datetime] = None,
    trade_end: Optional[datetime] = None,
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
    entry_cutoff = config.settings.entry_cutoff
    flatten_by = config.settings.flatten_by
    session_tz = config.settings.session_timezone
    state = BotState()
    cash = starting_equity
    lots: list[OpenLot] = []
    pending: list[PendingOrder] = []
    trades: list[Trade] = []
    signals: list[Signal] = []
    equity_curve: list[tuple[datetime, float]] = []
    last_price: dict[str, float] = {}
    cash_skips = 0
    pyramid_add_skips = 0
    sma20_fill_skips = 0
    atr_fill_skips = 0
    max_concurrent = 0
    both_open_ticks = 0
    window_start = _aware(trade_start) if trade_start is not None else None
    window_end = _aware(trade_end) if trade_end is not None else None

    def symbols_in_position() -> set[str]:
        return {lot.symbol for lot in lots}

    def equity_now() -> float:
        return _mark_to_market(cash, lots, last_price)

    def account() -> Account:
        eq = equity_now()
        return Account(equity=eq, cash=cash, buying_power=cash, status="ACTIVE")

    def reserved_buy_cash() -> float:
        return sum(
            (order.qty or 0.0) * order.signal_price
            for order in pending
            if order.kind == "enter" and order.side == "buy" and order.qty
        )

    def note_open_book() -> None:
        nonlocal max_concurrent, both_open_ticks
        n = len(symbols_in_position())
        if n > max_concurrent:
            max_concurrent = n
        if n >= 2:
            both_open_ticks += 1

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
        if window_end is not None and now >= window_end:
            break
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
                    flatten_symbol(
                        order.symbol,
                        _aware(fill_bar.timestamp),
                        fill_bar.open,
                        order.close_reason,
                        order.rule_id,
                    )
                continue
            if fill_at_or_after_cutoff(_aware(fill_bar.timestamp), entry_cutoff, session_tz):
                continue
            if not allow_pyramid and order.symbol in symbols_in_position():
                continue
            if order.qty is None or order.qty < 1:
                continue
            if order.symbol not in symbols_in_position() and len(symbols_in_position()) >= config.settings.max_open_positions:
                continue
            fill_px = _apply_slippage(fill_bar.open, order.side, slippage_pct, is_entry=True)
            if order.stop_mode == "sma20" and not sma_stop_valid(order.side, fill_px, order.stop):
                sma20_fill_skips += 1
                continue
            fill_stop = order.stop
            if order.stop_mode in ENTRY_STOP_MODES:
                fill_stop = _entry_anchored_stop(order.side, fill_px, order.stop_loss_pct)
            if order.stop_mode == "atr":
                fill_stop = atr_stop_price(
                    order.side, fill_px, order.atr_value, order.stop_atr_mult
                )
                if fill_stop is None:
                    atr_fill_skips += 1
                    continue
            fill_take = order.take
            if order.take_anchor == "entry":
                fill_take = _entry_anchored_take(order.side, fill_px, order.take_profit_pct)
            if order.side == "buy":
                cost = buy_notional(order.qty, fill_px, commission)
                if cost > cash + 1e-9:
                    cash_skips += 1
                    continue
                cash -= cost
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
                    stop=fill_stop,
                    take=fill_take,
                    signal_time=order.signal_time,
                    tf=order.tf,
                    exit_mode=order.exit_mode,
                    exit_ema_period=order.exit_ema_period,
                    exit_sma_period=order.exit_sma_period,
                    exit_range_bars=order.exit_range_bars,
                    exit_range_skip_doji=order.exit_range_skip_doji,
                    exit_range_doji_frac=order.exit_range_doji_frac,
                    breakeven_after_bars=order.breakeven_after_bars,
                    breakeven_requires_valid=order.breakeven_requires_valid,
                    breakeven_valid=order.breakeven_valid,
                    breakeven_ema_period=order.breakeven_ema_period,
                    stop_mode=order.stop_mode,
                    stop_loss_pct=order.stop_loss_pct,
                    lock_trigger_pct=order.lock_trigger_pct,
                    lock_stop_pct=order.lock_stop_pct,
                    trail_pct=order.trail_pct,
                    stop_atr_mult=order.stop_atr_mult,
                    stop_atr_period=order.stop_atr_period,
                    atr_value=order.atr_value,
                    peak_price=fill_px,
                    pyramid_on_lock=order.pyramid_on_lock,
                    pyramid_add_pct=order.pyramid_add_pct,
                    partial_take_on_lock=order.partial_take_on_lock,
                    partial_take_be=order.partial_take_be,
                    base_qty=order.qty,
                    cost_basis=order.qty * fill_px,
                    take_anchor=order.take_anchor,
                    take_profit_pct=order.take_profit_pct,
                )
            )
            note_open_book()
        pending = still_pending

        # 2) Stop / take on the bar that just completed (after any fill at its open).
        #    ema_invalid then exits at this bar's close when the close is on the
        #    wrong side of EMA (long: close < EMA). Same-bar stop + invalid → stop.
        #    lower_high exits at this bar's close when the completed bar's high is
        #    strictly below the previous bar's high (long). Same fill as ema_invalid.
        #    range_expansion exits at this bar's close when range (high − low) is
        #    strictly greater than max(range of the previous N bars). Not armed on
        #    the entry/fill bar. Same-bar stop + range → stop.
        #    ma_cross_close uses the same EMA-vs-SMA close-to-close pair-cross as
        #    ma_cross (long: prev EMA >= prev SMA and curr EMA < curr SMA) but
        #    fills at this bar's close. Same-bar stop + cross → stop.
        #    ma_cross schedules flatten at the *next* bar open (same fill as entries).
        for symbol, tf, bar in closing:
            last_price[symbol] = bar.close
            survivors: list[OpenLot] = []
            for lot in lots:
                if lot.symbol != symbol or lot.tf != tf:
                    survivors.append(lot)
                    continue
                hit = _stop_take_hit(bar, lot)
                series = series_map.get((symbol, tf), [])
                if hit is None and lot.exit_mode == "ema_invalid":
                    ema_val = ema_through(series, bar, lot.exit_ema_period)
                    if ema_cross_exit(side=lot.side, close=bar.close, ema_value=ema_val):
                        hit = ("ema_invalid", bar.close)
                if hit is None and lot.exit_mode == "lower_high":
                    prev = _prev_bar(series, bar.timestamp)
                    if prev is not None and lower_high_exit(lot.side, bar, prev):
                        hit = ("lower_high", bar.close)
                if (
                    hit is None
                    and lot.exit_mode == "range_expansion"
                    and _aware(bar.timestamp) != _aware(lot.entry_time)
                ):
                    prior = _prev_n_bars(series, bar.timestamp, lot.exit_range_bars)
                    if prior is not None and range_expansion_exit(
                        bar,
                        prior,
                        skip_doji=lot.exit_range_skip_doji,
                        doji_frac=lot.exit_range_doji_frac,
                    ):
                        hit = ("range_expansion", bar.close)
                if hit is None and lot.exit_mode == "ma_cross_close" and _ma_pair_cross_exit(
                    lot, bar, series
                ):
                    hit = ("ma_cross", bar.close)
                if hit is None and lot.exit_mode == "ma_cross" and _ma_pair_cross_exit(lot, bar, series):
                    nxt = _next_bar(series, bar.timestamp)
                    already = any(
                        order.kind == "close"
                        and order.symbol == lot.symbol
                        and order.tf == lot.tf
                        for order in pending
                    )
                    _maybe_arm_breakeven(lot, bar, series)
                    cash, skipped, take_hit = _lock_arm_pyramid_then_take(
                        lot, bar, cash, commission, slippage_pct
                    )
                    if skipped:
                        pyramid_add_skips += 1
                    if take_hit is not None:
                        _reason, px = take_hit
                        trade, cash = _close_lot(
                            lot,
                            when=now,
                            price=px,
                            reason=_take_exit_reason(lot),
                            cash=cash,
                            commission=commission,
                            slippage_pct=slippage_pct,
                        )
                        trades.append(trade)
                        continue
                    if nxt is not None and not already:
                        pending.append(
                            PendingOrder(
                                kind="close",
                                rule_id=lot.rule_id,
                                symbol=lot.symbol,
                                tf=lot.tf,
                                fill_ts=_aware(nxt.timestamp),
                                qty=None,
                                side="sell" if lot.side == "buy" else "buy",
                                stop=None,
                                take=None,
                                signal_time=now,
                                signal_price=bar.close,
                                exit_mode=lot.exit_mode,
                                exit_ema_period=lot.exit_ema_period,
                                exit_sma_period=lot.exit_sma_period,
                                close_reason="ma_cross",
                            )
                        )
                    survivors.append(lot)
                    continue
                if hit is None:
                    _maybe_arm_breakeven(lot, bar, series)
                    cash, skipped, take_hit = _lock_arm_pyramid_then_take(
                        lot, bar, cash, commission, slippage_pct
                    )
                    if skipped:
                        pyramid_add_skips += 1
                    if take_hit is not None:
                        _reason, px = take_hit
                        trade, cash = _close_lot(
                            lot,
                            when=now,
                            price=px,
                            reason=_take_exit_reason(lot),
                            cash=cash,
                            commission=commission,
                            slippage_pct=slippage_pct,
                        )
                        trades.append(trade)
                        continue
                    survivors.append(lot)
                    continue
                reason, px = hit
                if reason == "stop":
                    reason = _stop_exit_reason(lot)
                elif reason == "take":
                    reason = _take_exit_reason(lot)
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

        # 2b) Session flatten at the close of the bar that contains flatten_by.
        #     15m + 15:55 → 15:45 ET bar close. 5m + 15:55 → 15:50 ET bar close.
        #     Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close on this bar already
        #     ran; they win if they hit. Next-open ma_cross is still pending, so
        #     flatten at this close wins over that scheduled next-open fill.
        if flatten_by:
            for symbol, tf, bar in closing:
                if not is_flatten_bar(bar.timestamp, tf, flatten_by, session_tz):
                    continue
                last_price[symbol] = bar.close
                survivors: list[OpenLot] = []
                for lot in lots:
                    if lot.symbol != symbol or lot.tf != tf:
                        survivors.append(lot)
                        continue
                    trade, cash = _close_lot(
                        lot,
                        when=now,
                        price=bar.close,
                        reason="session_flatten",
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

        allow_entries = window_start is None or now >= window_start
        if not allow_entries:
            equity_curve.append((now, equity_now()))
            continue

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
                                exit_mode=rule.action.exit,
                                exit_ema_period=rule.action.exit_ema_period,
                                exit_sma_period=rule.action.exit_sma_period,
                                exit_range_bars=rule.action.exit_range_bars,
                                **_breakeven_fields(rule.action),
                            )
                        )
                elif not allow_pyramid and symbol in symbols_in_position():
                    accepted = False
                    open_side = _open_side(lots, symbol)
                    incoming = _action_side(action)
                    if open_side is not None and open_side != incoming:
                        skip_reason = "opposite_signal_in_trade"
                    else:
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
                        sma_stop = _signal_sma_stop(rule.action, series, ev.signal_bar_ts)
                        atr_val = _signal_atr(rule.action, series, ev.signal_bar_ts)
                        if accepted and rule.action.stop_mode == "sma20":
                            side_probe = "buy" if action == "buy" else "sell"
                            if sma_stop is None:
                                accepted = False
                                skip_reason = "sma20_unavailable"
                            elif not sma_stop_valid(side_probe, px, sma_stop):
                                accepted = False
                                skip_reason = "sma20_above_entry"
                        if accepted and rule.action.stop_mode == "atr":
                            if atr_val is None or atr_val <= 0:
                                accepted = False
                                skip_reason = "atr_unavailable"
                        try:
                            qty = (
                                shares_for(
                                    rule.action,
                                    account(),
                                    px,
                                    stop_price=sma_stop
                                    if rule.action.stop_mode == "sma20"
                                    else atr_stop_price(
                                        "buy" if action == "buy" else "sell",
                                        px,
                                        atr_val,
                                        rule.action.stop_atr_mult,
                                    )
                                    if rule.action.stop_mode == "atr"
                                    else None,
                                )
                                if accepted
                                else 0.0
                            )
                        except ValueError:
                            accepted = False
                            skip_reason = "size_zero"
                            qty = 0.0
                        if accepted and nxt is None:
                            accepted = False
                            skip_reason = "no_next_bar"
                        elif (
                            accepted
                            and nxt is not None
                            and window_end is not None
                            and _aware(nxt.timestamp) >= window_end
                        ):
                            accepted = False
                            skip_reason = "outside_window"
                        elif accepted and nxt is not None and fill_at_or_after_cutoff(
                            _aware(nxt.timestamp), entry_cutoff, session_tz
                        ):
                            accepted = False
                            skip_reason = "entry_cutoff"
                        elif accepted and action == "buy":
                            available = cash - reserved_buy_cash()
                            if buy_notional(qty, px, commission) > available + 1e-9:
                                accepted = False
                                skip_reason = "insufficient_cash"
                        if accepted and nxt is not None:
                            side = "buy" if action == "buy" else "sell"
                            stop, take = bracket_prices(
                                rule.action, px, side, sma_value=sma_stop, atr_value=atr_val
                            )
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
                                    exit_mode=rule.action.exit,
                                    exit_ema_period=rule.action.exit_ema_period,
                                    exit_sma_period=rule.action.exit_sma_period,
                                    atr_value=atr_val,
                                    **_exit_range_fields(rule.action),
                                    **_stop_manage_fields(rule.action),
                                    **_breakeven_fields(rule.action),
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
        end_ts = (
            equity_curve[-1][0]
            if equity_curve
            else (unique_times[-1] if unique_times else datetime.now(timezone.utc))
        )
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
    tape_start = min(starts) if starts else None
    tape_end = max(ends) if ends else None
    period_start = window_start or tape_start
    if window_end is not None:
        period_end = window_end - timedelta(microseconds=1)
    else:
        period_end = tape_end
    used = {f"{s}:{tf}": len(series) for (s, tf), series in series_map.items()}
    tag = label or ",".join(r.id for r in config.rules) or "backtest"
    extra_notes = list(notes or [])
    if entry_cutoff or flatten_by:
        extra_notes.append(
            f"Session gates ({session_tz}): entry_cutoff={entry_cutoff or 'off'} "
            "(skip signals whose next-bar fill is at/after that clock); "
            f"flatten_by={flatten_by or 'off'} "
            "(force flat at the close of the bar containing that clock: "
            "15m RTH → 15:45 ET bar close when flatten_by is 15:55; "
            "5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55)."
        )
    cutoff_skips = sum(1 for s in signals if s.skip_reason == "entry_cutoff")
    if cutoff_skips:
        extra_notes.append(
            f"{cutoff_skips} signal(s) skipped as entry_cutoff "
            f"({entry_cutoff} {session_tz}; fill would be at/after the cutoff)."
        )
    session_flats = sum(1 for t in trades if t.exit_reason == "session_flatten")
    if session_flats:
        extra_notes.append(
            f"{session_flats} trade(s) exited as session_flatten "
            f"(time-exit at the flatten bar close; flatten_by {flatten_by} {session_tz})."
        )
    be_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.breakeven_after_bars > 0
    ]
    if be_rules:
        sample = be_rules[0].action
        valid_txt = (
            f"close > EMA({sample.breakeven_ema_period}) on that timeframe"
            if sample.breakeven_valid == "above_ema"
            else "always"
        )
        extra_notes.append(
            f"Break-even: after {sample.breakeven_after_bars} complete signal-timeframe "
            f"bar(s) after the entry bar, at that close, if the lot is still open"
            + (
                f" and still valid ({valid_txt})"
                if sample.breakeven_requires_valid
                else ""
            )
            + ", move the stop to entry and leave it there. "
            "If not valid, keep the original percent stop (do not retry). "
            "Same-bar stop/take on the evaluation bar still use the original stop."
        )
        armed = sum(1 for t in trades if t.breakeven_armed)
        be_hits = sum(1 for t in trades if t.exit_reason == "breakeven_stop")
        extra_notes.append(
            f"{armed} trade(s) armed break-even; {be_hits} exited as breakeven_stop."
        )
    if window_start is not None or window_end is not None:
        extra_notes.append(
            "Trade window "
            f"{_iso(window_start) or 'tape start'} → {_iso(window_end) or 'tape end'} "
            "(prior bars kept for indicator warmup; no new entries outside the window)."
        )
        extra_notes.append(
            f"Downloaded tape span {_iso(tape_start)} → {_iso(tape_end)}."
        )
    ma_close_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.exit == "ma_cross_close"
    ]
    if ma_close_rules:
        sample = ma_close_rules[0].action
        extra_notes.append(
            f"MA-cross-at-close exit (action.exit: ma_cross_close): after entry, on each "
            f"completed signal-timeframe bar, leave when EMA({sample.exit_ema_period}) "
            f"crosses SMA({sample.exit_sma_period}) against the position and fill at "
            "that bar's close (same convention as ema_invalid / lower_high). "
            "Cross is EMA vs SMA close-to-close, not price vs MA. "
            "Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). "
            "Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). "
            "Same-bar stop / lock_stop + cross → stop (stop is checked first). "
            "A same-bar lock-arm touch + pair-cross (low stays above the live stop) "
            "exits as ma_cross at that close and does not arm the lock. "
            "If the cross bar is also the flatten bar, ma_cross at that close wins "
            "over session_flatten."
        )
        ma_close_exits = sum(1 for t in trades if t.exit_reason == "ma_cross")
        extra_notes.append(
            f"{ma_close_exits} trade(s) exited as ma_cross "
            "(EMA/SMA pair-cross against the position, fill at that bar's close)."
        )
    ma_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.exit == "ma_cross"
    ]
    if ma_rules:
        sample = ma_rules[0].action
        extra_notes.append(
            f"MA-cross exit (action.exit: ma_cross): flatten at the next bar open after "
            f"EMA({sample.exit_ema_period}) crosses SMA({sample.exit_sma_period}) against "
            "the position. Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). "
            "Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). "
            "Same fill convention as entries. Same-bar stop on the signal bar still wins. "
            "If that signal is also the flatten bar, session_flatten at that close wins."
        )
        ma_exits = sum(1 for t in trades if t.exit_reason == "ma_cross")
        extra_notes.append(
            f"{ma_exits} trade(s) exited as ma_cross "
            "(EMA/SMA pair-cross against the position)."
        )
    lh_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.exit == "lower_high"
    ]
    if lh_rules:
        extra_notes.append(
            "Lower-high exit (action.exit: lower_high): after entry, on each completed "
            "signal-timeframe bar, leave the long when that bar's high is strictly below "
            "the previous bar's high and exit at that bar's close (same fill convention "
            "as ema_invalid). Equal highs stay valid. Shorts use the symmetric higher low "
            "(current low > previous low). Same-bar stop + lower-high → stop. "
            "If the lower-high bar is also the flatten bar, lower_high at that close wins."
        )
        lh_exits = sum(1 for t in trades if t.exit_reason == "lower_high")
        extra_notes.append(
            f"{lh_exits} trade(s) exited as lower_high "
            "(completed bar high < previous bar high)."
        )
    range_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.exit == "range_expansion"
    ]
    if range_rules:
        sample = range_rules[0].action
        n = sample.exit_range_bars
        doji_txt = ""
        if sample.exit_range_skip_doji:
            doji_txt = (
                f" Expansion bars with body/range <= {sample.exit_range_doji_frac:g} "
                "(doji) do not fire the range exit; wait for a later non-doji expansion, "
                "the protective stop, or flatten."
            )
        extra_notes.append(
            f"Range-expansion exit (action.exit: range_expansion): after entry, on each "
            f"completed signal-timeframe bar *after the entry/fill bar*, leave when that "
            f"bar's range (high − low) is strictly greater than the max range of the "
            f"previous {n} bars and exit at that bar's close (same fill convention as "
            "ema_invalid / lower_high). Equal range stays valid. Need those prior bars "
            "in the series. Same-bar stop + range expansion → stop. If the expansion bar "
            "is also the flatten bar, range_expansion at that close wins over session_flatten."
            + doji_txt
        )
        range_exits = sum(1 for t in trades if t.exit_reason == "range_expansion")
        extra_notes.append(
            f"{range_exits} trade(s) exited as range_expansion "
            f"(bar range > max of previous {n} bars, fill at that close)."
        )
    pnl_note = _exit_pnl_note(trades)
    if pnl_note:
        extra_notes.append(pnl_note)
    extra_notes.append(
        f"One lot per symbol (long or short, not both); both names may be open at once "
        f"if cash covers the second risk-sized entry, otherwise the later signal is skipped. "
        f"An opposite-side signal while that symbol is already in a trade is skipped "
        f"(opposite_signal_in_trade). Max concurrent symbols this run: {max_concurrent}. "
        f"Ticks with 2+ names open: {both_open_ticks}."
    )
    opp_skips = sum(1 for s in signals if s.skip_reason == "opposite_signal_in_trade")
    if opp_skips:
        extra_notes.append(
            f"{opp_skips} signal(s) skipped as opposite_signal_in_trade "
            "(one position per symbol; the other side does not reverse an open lot)."
        )
    sma_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.stop_mode == "sma20"
    ]
    if sma_rules:
        sample = sma_rules[0].action
        take_txt = (
            f" Optional take_profit_pct {sample.take_profit_pct:g}% is still from the signal-bar close."
            if sample.take_profit_pct
            else " No percent take-profit (SMA20 stop + session flatten / EMA exit only)."
        )
        extra_notes.append(
            f"SMA20 stop (stop_mode: sma20): protective stop is the SMA({sample.stop_sma_period}) "
            "value of the signal bar — a fixed level, not trailed to later SMA prints. "
            "Longs require that SMA below the signal close; if SMA20 is at/above the signal "
            "close the signal is skipped (sma20_above_entry). If the next-bar fill is at/below "
            "that SMA20, the fill is skipped rather than falling back to a percent stop. "
            "v1 does not trail the stop to the latest SMA20 each bar."
            + take_txt
        )
        extra_notes.append(
            f"{sum(1 for s in signals if s.skip_reason == 'sma20_above_entry')} signal(s) "
            "skipped as sma20_above_entry; "
            f"{sum(1 for s in signals if s.skip_reason == 'sma20_unavailable')} as sma20_unavailable."
        )
    if sma20_fill_skips:
        extra_notes.append(
            f"{sma20_fill_skips} accepted signal(s) skipped at fill because SMA20 was at/above "
            "the next-bar open (long stop not below entry)."
        )
    atr_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.stop_mode == "atr"
    ]
    if atr_rules:
        sample = atr_rules[0].action
        extra_notes.append(
            f"ATR stop (stop_mode: atr): Wilder ATR({sample.stop_atr_period}) is computed "
            "through the closed signal/entry bar (true range = max(H−L, |H−prev close|, "
            f"|L−prev close|); seed = SMA of the first {sample.stop_atr_period} TRs, then "
            f"ATR = (prev_ATR×({sample.stop_atr_period}−1) + TR) / {sample.stop_atr_period}). "
            f"Protective stop is fill − {sample.stop_atr_mult:g}×ATR (long) or fill + "
            f"{sample.stop_atr_mult:g}×ATR (short). The dollar distance is taken from the "
            "signal-bar ATR and applied to the next-bar fill; it never trails. Signals skip "
            "when ATR is unavailable (atr_unavailable). Fills skip when that stop is not "
            "beyond the fill. No min/max stop-distance floor."
        )
        extra_notes.append(
            f"{sum(1 for s in signals if s.skip_reason == 'atr_unavailable')} signal(s) "
            "skipped as atr_unavailable."
        )
    if atr_fill_skips:
        extra_notes.append(
            f"{atr_fill_skips} accepted signal(s) skipped at fill because the ATR stop "
            "was not beyond the next-bar open."
        )
    entry_stop_rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.stop_mode in ENTRY_STOP_MODES
    ]
    if entry_stop_rules:
        sample = entry_stop_rules[0].action
        stop_pct = sample.stop_loss_pct
        stop_txt = f"{stop_pct:g}%" if stop_pct is not None else "n/a"
        extra_notes.append(
            f"Entry-anchored stop (stop_mode: {sample.stop_mode}): initial protective stop is "
            f"{stop_txt} from the *fill* (next-bar open), not the signal-bar close. "
            "percent still uses the signal close. No percent take when take_profit_pct is omitted."
        )
        if sample.stop_mode == "entry_pct":
            if sample.exit == "range_expansion":
                extra_notes.append(
                    "Fixed entry stop (stop_mode: entry_pct): the initial fill stop never "
                    "moves (not lock_plus). Exits are that stop, range_expansion, or "
                    "session_flatten (or eod). Same-bar stop + range expansion → stop "
                    "(stop is checked first)."
                )
            else:
                extra_notes.append(
                    "Fixed entry stop (stop_mode: entry_pct): the initial fill stop never moves. "
                    "Exits are that stop or session_flatten (or eod)."
                )
        if sample.stop_mode == "lock_plus":
            trig = sample.resolved_lock_trigger_pct()
            lock = sample.resolved_lock_stop_pct()
            lock_sides = {r.action.type for r in entry_stop_rules}
            if lock_sides == {"buy"}:
                extra_notes.append(
                    f"Lock-plus (stop_mode: lock_plus) on longs only: first trade/touch of "
                    f"entry×(1+{(trig or 0):g}/100) (bar high ≥ that print) moves the stop "
                    "there and leaves it. Shorts have no percent / lock_plus stop. "
                    "The locked stop is live from the next bar; same-bar pullback after the "
                    "tag still uses the initial 1% protective stop. Later hit of the locked "
                    "stop is exit reason lock_stop. Session flatten covers longs and shorts."
                )
            else:
                extra_notes.append(
                    f"Lock-plus (stop_mode: lock_plus): first trade/touch of the lock trigger "
                    f"moves the stop to the lock level and leaves it. Long: trigger/lock at "
                    f"entry×(1+{(trig or 0):g}/100) (bar high ≥ that print). Short: trigger/lock "
                    f"at entry×(1−{(lock or 0):g}/100) (bar low ≤ that print). "
                    "The locked stop is live from the next bar; same-bar pullback after the "
                    "tag still uses the initial 1% protective stop. Later hit of the locked "
                    "stop is exit reason lock_stop. Session flatten covers longs and shorts."
                )
            extra_notes.append(
                f"{sum(1 for t in trades if t.lock_armed)} trade(s) armed the +lock; "
                f"{sum(1 for t in trades if t.exit_reason == 'lock_stop')} exited as lock_stop."
            )
            if sample.pyramid_add_pct is not None:
                add_pct = sample.pyramid_add_pct
                extra_notes.append(
                    f"Pyramid add (pyramid_add_pct: {add_pct:g}): when price first reaches "
                    f"original fill × (1+{add_pct:g}/100) (long: bar high ≥ that print), "
                    "add the same share count as the open lot (double total shares). "
                    "Add fill: if the bar opens through that trigger the add fills at the "
                    "open (gapped buy-stop); otherwise at the trigger (high tagged it). "
                    f"The +{(trig or 0):g}% lock still arms separately on first touch of "
                    f"original fill × (1+{(trig or 0):g}/100) and rests the stop there on "
                    "the full position. If a bar gaps through both prints with no earlier "
                    "+add bar, the engine adds first, then locks; the locked stop is live "
                    "from the next bar. No hard take-profit when take_profit_pct is omitted. "
                    "Cash for the add is not reserved at entry; a cash skip is attempted "
                    "once and the lock can still arm. Session flatten still applies. "
                    "This add is intra-lot, not a second EMA signal. Live does not auto-add."
                )
                extra_notes.append(
                    f"{sum(1 for t in trades if t.pyramid_added)} trade(s) added at "
                    f"+{add_pct:g}%; "
                    f"{sum(1 for t in trades if t.pyramid_add_skipped)} skipped the add "
                    f"(insufficient cash); "
                    f"{sum(1 for t in trades if t.pyramid_added and t.lock_armed)} "
                    f"added then armed the +lock; "
                    f"{sum(1 for t in trades if t.lock_armed and not t.pyramid_added)} "
                    f"locked without an add."
                )
            elif sample.pyramid_on_lock:
                take_pct = sample.take_profit_pct
                extra_notes.append(
                    f"Pyramid-on-lock (pyramid_on_lock): when the +{(trig or 0):g}% lock arms, "
                    "add the same share count as the open lot (double total shares). "
                    "Add fill: if the bar opens through original fill × "
                    f"(1+{(trig or 0):g}/100) the add fills at that open (gapped buy-stop); "
                    "otherwise at the trigger (high tagged it). After the add, the stop stays "
                    f"at original fill × (1+{(sample.resolved_lock_stop_pct() or 0):g}/100) on "
                    "the full position. Take is fill-anchored "
                    f"(take_anchor: entry, {take_pct:g}% → original fill × "
                    f"(1+{(take_pct or 0):g}/100)); a hit is take_2pct when that percent is 2. "
                    "The locked stop is still live from the next bar — the arm bar checks "
                    "take only after the add (same-bar pullback does not lock_stop the add). "
                    "If stop and take both trade on a later bar, stop wins. "
                    "Cash for the add is not reserved at entry; if cash cannot cover the add, "
                    "the lock still arms and the add is skipped. Session flatten still applies. "
                    "This add is intra-lot, not a second EMA signal (allow_pyramid stays off). "
                    "Live runner does not auto-add on lock."
                )
                extra_notes.append(
                    f"{sum(1 for t in trades if t.pyramid_added)} trade(s) added at the lock; "
                    f"{sum(1 for t in trades if t.pyramid_add_skipped)} armed the lock but "
                    f"skipped the add (insufficient cash). "
                    f"{sum(1 for t in trades if t.exit_reason == 'take_2pct')} exited as take_2pct; "
                    f"{sum(1 for t in trades if t.exit_reason == 'take')} exited as take."
                )
            elif sample.take_anchor == "entry" and sample.take_profit_pct:
                extra_notes.append(
                    f"Take is fill-anchored (take_anchor: entry): "
                    f"take_profit_pct {sample.take_profit_pct:g}% from the fill, not the "
                    "signal-bar close."
                )
            if sample.partial_take_be:
                extra_notes.append(
                    f"Partial take then BE (partial_take_be): when price first reaches "
                    f"original fill × (1+{(trig or 0):g}/100), sell floor(half) of the "
                    "open shares at the lock-trigger print (gap-through: fill at open "
                    "if the bar opens through that trigger, else at the trigger) and "
                    "rest the remainder stop at original fill × 1.00 (break-even), "
                    "not at fill × "
                    f"(1+{(sample.resolved_lock_stop_pct() or 0):g}/100). Odd lots "
                    "round the take down so at least 1 share remains when size ≥ 2. "
                    "Size 1 skips the partial and still arms BE. The BE stop is live "
                    "from the next bar; same-bar pullback after the tag still uses "
                    "the initial 1% stop. Remainder exits as breakeven_stop / "
                    "session_flatten / stop (if never +1%). No hard full take. No "
                    "pyramid. Live does not auto scale-out."
                )
                extra_notes.append(
                    f"{sum(1 for t in trades if t.partial_take)} trade(s) scaled out half "
                    f"at +{(trig or 0):g}% "
                    f"(${sum(t.partial_take_pnl for t in trades if t.partial_take):,.2f}); "
                    f"{sum(1 for t in trades if t.partial_take_skipped_size)} skipped "
                    "the partial (size < 2); "
                    f"{sum(1 for t in trades if t.breakeven_armed)} armed BE on the "
                    f"remainder; "
                    f"{sum(1 for t in trades if t.exit_reason == 'breakeven_stop')} "
                    "exited as breakeven_stop."
                )
            elif sample.partial_take_on_lock:
                extra_notes.append(
                    f"Partial take on lock (partial_take_on_lock): when the "
                    f"+{(trig or 0):g}% lock arms, sell floor(half) of the open shares "
                    "at the lock-trigger print (gap-through: fill at open if the bar "
                    "opens through original fill × "
                    f"(1+{(trig or 0):g}/100), else at the trigger) and lock the "
                    "remainder at that same print. Odd lots round the take down so at "
                    "least 1 share remains when size ≥ 2. Size 1 skips the partial and "
                    "still locks. No hard full take. No pyramid add. The locked stop is "
                    "live from the next bar. Remainder exits as lock_stop / "
                    "session_flatten / stop. Live does not auto scale-out."
                )
                extra_notes.append(
                    f"{sum(1 for t in trades if t.partial_take)} trade(s) scaled out half "
                    f"at +{(trig or 0):g}% "
                    f"(${sum(t.partial_take_pnl for t in trades if t.partial_take):,.2f}); "
                    f"{sum(1 for t in trades if t.partial_take_skipped_size)} skipped "
                    "the partial (size < 2)."
                )
        if sample.stop_mode == "trail":
            trail = sample.resolved_trail_pct()
            extra_notes.append(
                f"Trailing stop (stop_mode: trail): stop is always "
                f"peak_price_since_entry × (1−{(trail or 0):g}/100), ratcheting up only. "
                "Peak starts at the fill and updates from each bar's high after the "
                "current-stop check, so a new trail is live from the next bar. "
                "Initial stop is entry×0.99 when trail_pct/stop_loss_pct is 1. "
                "A stop hit is exit reason trail_stop."
            )
            extra_notes.append(
                f"{sum(1 for t in trades if t.trail_ratcheted)} trade(s) ratcheted the trail "
                f"above the initial fill stop; "
                f"{sum(1 for t in trades if t.exit_reason == 'trail_stop')} exited as trail_stop."
            )
    if cash_skips:
        extra_notes.append(
            f"{cash_skips} accepted signal(s) skipped at fill for insufficient cash."
        )
    if pyramid_add_skips:
        extra_notes.append(
            f"{pyramid_add_skips} pyramid add(s) skipped for insufficient cash "
            "(lock can still arm; cash is not reserved for the add at entry)."
        )
    cash_signal_skips = sum(1 for s in signals if s.skip_reason == "insufficient_cash")
    if cash_signal_skips:
        extra_notes.append(
            f"{cash_signal_skips} signal(s) skipped at size time for insufficient cash."
        )
    session_start = session_date(window_start) if window_start is not None else None
    session_end = session_date(window_end - timedelta(seconds=1)) if window_end is not None else None
    stats = build_period_stats(
        trades=trades,
        equity_curve=equity_curve,
        starting_equity=starting_equity,
        ending_equity=ending,
        session_start=session_start,
        session_end=session_end,
    )
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
        notes=extra_notes,
    )
    return BacktestResult(
        label=tag,
        report=report,
        trades=trades,
        signals=signals,
        equity_curve=equity_curve,
        bars_used=used,
        period_stats=stats,
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
                f"- Break-even armed: {r.get('breakeven_armed', 0)}"
                if r.get("breakeven_armed") or (r.get("exit_reasons") or {}).get("breakeven_stop")
                else "",
                f"- Lock armed: {r.get('lock_armed', 0)}"
                if r.get("lock_armed") or (r.get("exit_reasons") or {}).get("lock_stop")
                else "",
                f"- Pyramid added: {r.get('pyramid_added', 0)}"
                if r.get("pyramid_added") or r.get("pyramid_add_skipped")
                else "",
                f"- Pyramid add skipped (cash): {r.get('pyramid_add_skipped', 0)}"
                if r.get("pyramid_add_skipped")
                else "",
                f"- Partial take (half at +lock): {r.get('partial_take', 0)} "
                f"(${float(r.get('partial_take_pnl') or 0):,.2f})"
                if r.get("partial_take") or r.get("partial_take_pnl")
                else "",
                f"- Trail ratcheted: {r.get('trail_ratcheted', 0)}"
                if r.get("trail_ratcheted") or (r.get("exit_reasons") or {}).get("trail_stop")
                else "",
                f"- Skip reasons: {r.get('skip_reasons')}" if r.get("skip_reasons") else "",
                *(_format_side_lines(r.get("sides") or {})),
            ]
        )
        extra_notes = [
            n
            for n in (r.get("notes") or [])
            if n.startswith("Exit-only")
            or n.startswith("Session gates")
            or n.startswith("Break-even")
            or n.startswith("MA-cross exit")
            or n.startswith("Lower-high exit")
            or n.startswith("SMA20 stop")
            or n.startswith("ATR stop")
            or n.startswith("Entry-anchored stop")
            or n.startswith("Fixed entry stop")
            or n.startswith("Lock-plus")
            or n.startswith("Pyramid-on-lock")
            or n.startswith("Pyramid add")
            or n.startswith("Partial take")
            or n.startswith("Take is fill-anchored")
            or n.startswith("Trailing stop")
            or n.startswith("Exit P&L")
            or n.startswith("RSI filter")
            or n.startswith("No RSI")
            or "entry_cutoff" in n
            or "sma20" in n
            or "SMA20" in n
            or "ATR stop" in n
            or "atr_unavailable" in n
            or "session_flatten" in n
            or "armed break-even" in n
            or "armed BE" in n
            or "breakeven_stop" in n
            or "exited as ma_cross" in n
            or "exited as lower_high" in n
            or "exited as range_expansion" in n
            or "lock_stop" in n
            or "trail_stop" in n
            or "armed the +lock" in n
            or "added at the lock" in n
            or "scaled out half" in n
            or "lock-arm add" in n
            or "ratcheted the trail" in n
            or "opposite_signal_in_trade" in n
            or n.startswith("One lot per symbol")
        ]
        for note in extra_notes:
            lines.append(f"- {note}")
        stats = block.get("period_stats")
        if stats:
            lines.append("")
            lines.extend(format_period_stats_md(stats))
        lines.append("")
    extra = payload.get("assumptions") or []
    if extra:
        lines.append("## Assumptions")
        lines.append("")
        for item in extra:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(line for line in lines if line is not None)


def _format_side_lines(sides: dict[str, Any]) -> list[str]:
    if not sides:
        return []
    labels = {"buy": "Long", "sell": "Short"}
    lines = ["- By side:"]
    for key in ("buy", "sell"):
        block = sides.get(key)
        if not block:
            continue
        wr = _fmt_opt_pct(block.get("win_rate_pct"))
        lines.append(
            f"  - {labels.get(key, key)}: {block.get('trades', 0)} trades, "
            f"{block.get('wins', 0)} / {block.get('losses', 0)} wins/losses, "
            f"WR {wr}, P&L ${_fmt_side_pnl(block.get('total_pnl'))}"
        )
    return lines


def _fmt_side_pnl(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):,.2f}"


def _fmt_opt_money(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def _fmt_opt_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}%"
