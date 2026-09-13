"""Side-by-side comparison of ORB and sample-rule backtest books.

Keeps the two engines on separate books: the ORB state machine and the
pattern-rule evaluator do not share positions or a combined equity curve.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from dta_bot.backtest import (
    BacktestResult,
    format_report_md,
    restrict_config,
    run_backtest,
)
from dta_bot.config import (
    BotConfig,
    entry_sides,
    find_rsi_condition,
    has_noon_short_stack,
    has_noon_stack,
    restrict_universe,
    rsi_filter_label,
    timeframe_label,
)
from dta_bot.history import YAHOO_INTERVAL
from dta_bot.orb_backtest import run_orb_backtest
from dta_bot.orb_config import OrbBotConfig
from dta_bot.timeframes import normalize

PATTERN_HIT_NAMES = (
    "bullish_engulfing",
    "bearish_engulfing",
    "evening_star",
    "hammer",
    "ema_sma_cross",
    "ema_cross",
    "sma_cross",
    "ma_pair_cross",
)

EXIT_ONLY_NOTE = (
    "Exit-only rule: isolated book has no entries, so P&L is $0. "
    "Signal count is how often the pattern would have fired; "
    "the combined book uses those fires to flatten longs from the entry rules."
)

ENTRIES_ONLY_NOTE = (
    "Entry rules only (no evening-star/engulfing flatten). "
    "Stops and takes still apply; this is the B+C book without D."
)

COMBINED_NOTE = (
    "All sample rules on one book. Close signals flatten longs from the entry rules. "
    "This is not the sum of the isolated books (shared one-lot-per-symbol constraint)."
)

LONG_SHORT_COMBINED_NOTE = (
    "Long and short on one book. One position per symbol (long or short, not both). "
    "An opposite signal while that symbol is already in a trade is skipped "
    "(opposite_signal_in_trade). Combined P&L is not the sum of the isolated books "
    "when the other side is skipped because a lot is already open. "
    "Session flatten covers longs and shorts. Max DD by side is the isolated-book figure."
)

MULTI_ENGINE_NOTE = (
    "ORB and the sample rules use separate engines and are not merged into one "
    "shared-position book. Ranking is apples-to-apples across isolated (and sample "
    "combined) books, not a single multi-strategy portfolio."
)

SHORT_MTM_NOTE = (
    "Short mark-to-market subtracts qty × mark from cash that already includes "
    "short proceeds. The previous 2×entry − mark formula double-counted proceeds "
    "and invented a drawdown when shorts flattened; closed-trade P&L was already correct."
)

YAHOO_CAP_NOTE = (
    "Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). "
    "Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. "
    "Requesting more than the cap returns HTTP 422. ORB needs 15m to build the "
    "opening range and 5m for probe/reversal, so its longest reliable Yahoo window "
    "is the 5m/15m 60-day cap."
)


def _orb_probe_assumption(config: Optional[OrbBotConfig]) -> str:
    spec = config.orb if config is not None else None
    mode = spec.probe_mode if spec is not None else "touch_and_band"
    pct = spec.edge_pct if spec is not None else 0.05
    if mode == "edge_band":
        return (
            f"Probe = signal-bar close inside the {pct:.0%} (configurable) edge band "
            "under the OR high or above the OR low (probe_mode: edge_band)."
        )
    if mode == "touch":
        return (
            "Probe = signal bar must touch the opening-range extreme "
            "(top: high >= OR high; bottom: low <= OR low). "
            "Close inside the edge band is not required "
            "(probe_mode: touch)."
        )
    return (
        f"Probe = signal bar must touch the opening-range extreme "
        f"(top: high >= OR high; bottom: low <= OR low) AND close inside the "
        f"{pct:.0%} (configurable) edge band "
        f"(top: [or_high - band, or_high]; bottom: [or_low, or_low + band]) "
        f"(probe_mode: touch_and_band, default)."
    )


def _orb_reversal_range_assumption(config: Optional[OrbBotConfig]) -> str:
    mode = config.orb.reversal_in_range if config is not None else "close"
    if mode == "off":
        return (
            "Reversal in-range filter is off (opposite color alone is enough). "
            "Set orb.reversal_in_range: close to require the reversal close inside the OR."
        )
    if mode == "body":
        return (
            "Reversal candle must be fully inside the OR (high and low within "
            "or_low–or_high; reversal_in_range: body). A close-only filter is "
            "orb.reversal_in_range: close."
        )
    return (
        "Reversal close must sit inside the opening range "
        "(or_low <= close <= or_high; reversal_in_range: close, default). "
        "If the reversal closes outside the OR, do not enter. "
        "Set orb.reversal_in_range: body for the stricter fully-inside mode "
        "(high and low within the OR), or off to disable the filter."
    )


def _orb_stop_assumption(config: Optional[OrbBotConfig]) -> str:
    mode = config.orb.stop_mode if config is not None else "orb_extreme"
    take = config.orb.take_profit_mode if config is not None else "ema_cross"
    period = config.orb.ema_period if config is not None else 9
    if take == "one_r":
        take_txt = (
            "take-profit is 1R from entry (R = |entry − stop|; long: entry + R; "
            "short: entry − R; take_profit_mode: one_r)."
        )
    elif take == "first_profitable_close":
        take_txt = (
            "take-profit is the close of the first signal-timeframe bar that is "
            "strictly profitable vs entry (long: close > entry; short: close < entry; "
            "take_profit_mode: first_profitable_close)."
        )
    elif take == "or_midpoint":
        take_txt = "take-profit is the OR midpoint (take_profit_mode: or_midpoint)."
    else:
        take_txt = (
            f"take-profit is the close of the first post-entry signal-timeframe bar "
            f"on the other side of EMA({period}) (long: close < EMA; short: close > EMA; "
            f"take_profit_mode: ema_cross, default)."
        )
    if mode == "reversal_candle":
        return f"Stop is the reversal candle extreme; {take_txt}"
    return (
        "Stop is the opening-range extreme (long → OR low, short → OR high); "
        f"{take_txt} "
        "Set orb.stop_mode: reversal_candle to restore the previous candle-extreme stop. "
        "Set orb.take_profit_mode: or_midpoint for the OR-midpoint target. "
        "Set orb.take_profit_mode: one_r for a 1R target. "
        "Set orb.take_profit_mode: first_profitable_close to restore the first-profit close exit."
    )


def _orb_frequency_assumption(config: Optional[OrbBotConfig]) -> str:
    spec = config.orb if config is not None else None
    cutoff = spec.entry_cutoff if spec is not None else "10:30"
    max_n = spec.max_trades_before_cutoff if spec is not None else 1
    allow_after = spec.allow_entries_after_cutoff if spec is not None else False
    tz = spec.session_timezone if spec is not None else "America/New_York"
    if not cutoff:
        return (
            "Multiple trades are allowed (no clock cutoff). One open position per symbol; "
            "new signals skip while in a position unless on_open_position=replace."
        )
    noun = "entry" if max_n == 1 else "entries"
    if allow_after:
        return (
            f"At most {max_n} {noun} per symbol per session with entry time before "
            f"{cutoff} {tz}; additional entries at/after the cutoff are allowed. "
            "One open position per symbol unless on_open_position=replace."
        )
    return (
        f"At most {max_n} {noun} per symbol per session, and only if that entry is "
        f"before {cutoff} {tz} (no new entries at/after the cutoff). "
        "One open position per symbol unless on_open_position=replace."
    )


def _orb_ema_assumption(config: Optional[OrbBotConfig]) -> str:
    spec = config.orb if config is not None else None
    on = spec.ema_filter if spec is not None else True
    period = spec.ema_period if spec is not None else 9
    require_open = spec.ema_require_open if spec is not None else False
    if not on:
        return (
            "EMA filter is off (ema_filter: false). "
            "Set orb.ema_filter: true to require the reversal close above "
            f"EMA({period}) for longs and below it for shorts."
        )
    open_bit = (
        " Also require the reversal open on the same side of the EMA (ema_require_open)."
        if require_open
        else " Default compare is close vs EMA (ema_require_open: false)."
    )
    return (
        f"EMA filter (ema_filter: true, default): compute EMA({period}) on the "
        "signal timeframe through the reversal bar (inclusive). "
        f"Long: close > EMA{period}; short: close < EMA{period}.{open_bit} "
        "If EMA cannot be computed (not enough closes), skip the entry. "
        "Set ema_filter: false to disable."
    )


def _orb_height_assumption(config: Optional[OrbBotConfig]) -> str:
    spec = config.orb if config is not None else None
    floor = spec.min_or_height_pct if spec is not None else 0.01
    if floor is None or floor <= 0:
        return (
            "High-vol gate is off (min_or_height_pct 0 / null). "
            "Set orb.min_or_height_pct: 0.01 to require OR height of at least 1% of OR open."
        )
    return (
        f"High-vol gate: trade only when (or_high − or_low) / or_open "
        f">= {floor:.2%} (min_or_height_pct, default 1%). "
        "Denominator is the OR candle open; if that print is missing, the OR midpoint "
        "is used. Below the threshold, skip the symbol for that session (no entries). "
        "Set 0 / null to disable."
    )


def assumptions_orb(
    friction: str,
    starting_equity: float,
    config: Optional[OrbBotConfig] = None,
) -> list[str]:
    return [
        "Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).",
        "After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.",
        _orb_probe_assumption(config),
        "Reversal = the next signal bar, opposite color (top+bearish → short, bottom+bullish → long).",
        _orb_reversal_range_assumption(config),
        _orb_ema_assumption(config),
        "Entry fills at the open of the bar after the reversal candle.",
        _orb_stop_assumption(config),
        _orb_height_assumption(config),
        _orb_frequency_assumption(config),
        "If stop and take (EMA-cross, 1R, midpoint, or first-profit close) both trade in the same bar, the stop is assumed to fill first.",
        "A gap through stop/take fills at that bar's open.",
        "Open lots still on the last bar are flattened at the last close (exit reason eod).",
        SHORT_MTM_NOTE,
        "Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.",
        friction,
        f"Starting equity ${starting_equity:,.2f}.",
    ]


def _rules_exit_assumption(config: Optional[BotConfig]) -> str:
    modes = {
        rule.action.exit
        for rule in (config.rules if config is not None else [])
        if rule.action.type != "close"
    }
    periods = {
        rule.action.exit_ema_period
        for rule in (config.rules if config is not None else [])
        if rule.action.exit == "ema_invalid"
    }
    period = next(iter(periods), 9)
    ma_rules = [
        rule
        for rule in (config.rules if config is not None else [])
        if rule.action.type != "close" and rule.action.exit == "ma_cross"
    ]
    if modes == {"ma_cross"} and ma_rules:
        action = ma_rules[0].action
        return (
            f"Exit is MA-cross (action.exit: ma_cross): hold until "
            f"EMA({action.exit_ema_period}) crosses SMA({action.exit_sma_period}) against "
            "the position and flatten at the next bar open — the same fill as entries. "
            "Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). "
            "Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). "
            "Optional stop_loss_pct / lock_plus is the protective stop. Percent "
            "take-profit is ignored. Same-bar stop on the cross bar still wins. If the "
            "cross bar is also the flatten bar, session_flatten at that close wins."
        )
    if "ma_cross" in modes and ma_rules:
        action = ma_rules[0].action
        lock_rules = [
            rule
            for rule in (config.rules if config is not None else [])
            if rule.action.type != "close" and rule.action.stop_mode == "lock_plus"
        ]
        lock_txt = ""
        if lock_rules:
            lock_action = lock_rules[0].action
            trig = lock_action.resolved_lock_trigger_pct()
            lock_txt = (
                f" Lock-plus stop (stop_mode: lock_plus) still applies: initial stop "
                f"is {lock_action.stop_loss_pct:g}% from the fill (long: below; short: above). "
                f"First trade/touch of entry×(1+{(trig or 0):g}/100) for a long "
                f"(bar high ≥ that print) or entry×(1−{(trig or 0):g}/100) for a short "
                f"(bar low ≤ that print) moves the stop to that same print and leaves it."
            )
        return (
            f"Mixed exits: ma_cross flattens at the next bar open after "
            f"EMA({action.exit_ema_period}) crosses SMA({action.exit_sma_period}) against "
            "the position (long: EMA under SMA; short: EMA above SMA — cover). "
            "fixed_bracket uses stop / lock_plus / session_flatten (no MA-cross cover). "
            "ema_invalid holds until a signal-timeframe close < EMA (exit at that close)."
            + lock_txt
        )
    if modes == {"ema_invalid"} or (config is not None and "ema_invalid" in modes and "fixed_bracket" not in modes and "ma_cross" not in modes):
        return (
            f"Exit is EMA-invalidation (action.exit: ema_invalid): hold the long until a "
            f"signal-timeframe bar closes < EMA({period}) and exit at that close. "
            f"Close == EMA({period}) stays valid. Optional stop_loss_pct is a catastrophic "
            "stop only (off when omitted). Percent take-profit is ignored."
        )
    if "ema_invalid" in modes:
        return (
            f"Mixed exits: ema_invalid holds until a signal-timeframe close < EMA({period}) "
            "(exit at that close; equals EMA stays valid). fixed_bracket uses stop_loss_pct / "
            "take_profit_pct from the signal-bar close. Same-bar stop + EMA-invalid → stop."
        )
    sma_rules = [
        rule
        for rule in (config.rules if config is not None else [])
        if rule.action.type != "close" and rule.action.stop_mode == "sma20"
    ]
    if sma_rules:
        action = sma_rules[0].action
        take_txt = (
            f" Optional take_profit_pct {action.take_profit_pct:g}% is still from the signal-bar close."
            if action.take_profit_pct
            else " take_profit_pct is omitted (SMA20 stop + session flatten only; no % take)."
        )
        return (
            f"Stop is the SMA({action.stop_sma_period}) value of the signal bar "
            f"(stop_mode: sma20) — a fixed protective level, not trailed. "
            "Longs skip when that SMA is at/above the signal close (sma20_above_entry) "
            "or when the next-bar fill is at/below it (no percent fallback). "
            f"action.exit: {action.exit}.{take_txt} "
            "Set stop_mode: percent to restore stop_loss_pct from the signal-bar close."
        )
    manage_rules = [
        rule
        for rule in (config.rules if config is not None else [])
        if rule.action.type != "close" and rule.action.stop_mode in {"entry_pct", "lock_plus", "trail"}
    ]
    if manage_rules:
        action = manage_rules[0].action
        stop_pct = action.stop_loss_pct
        stop_txt = f"{stop_pct:g}%" if stop_pct is not None else "n/a"
        take_txt = (
            f" Optional take_profit_pct {action.take_profit_pct:g}% is still from the signal-bar close."
            if action.take_profit_pct
            else " take_profit_pct is omitted (stop variant or session_flatten only; no % take)."
        )
        if action.stop_mode == "entry_pct":
            return (
                f"Stop is a fixed {stop_txt} below the *fill* (next-bar open; "
                f"stop_mode: entry_pct). It never moves.{take_txt} "
                "percent still uses stop_loss_pct from the signal-bar close."
            )
        if action.stop_mode == "lock_plus":
            trig = action.resolved_lock_trigger_pct()
            lock = action.resolved_lock_stop_pct()
            return (
                f"Lock-plus stop (stop_mode: lock_plus): initial stop is {stop_txt} from "
                f"the fill (long: below; short: above). First trade/touch of "
                f"entry×(1+{(trig or 0):g}/100) for a long (bar high ≥ that print) or "
                f"entry×(1−{(trig or 0):g}/100) for a short (bar low ≤ that print) moves "
                f"the stop to that same print and leaves it. The locked stop is live "
                f"from the next bar; same-bar pullback after the tag uses the initial stop. "
                f"A later hit of the locked stop is lock_stop.{take_txt}"
            )
        trail = action.resolved_trail_pct()
        return (
            f"Trailing stop (stop_mode: trail): stop is always "
            f"peak_price_since_entry × (1−{(trail or 0):g}/100), ratcheting up only. "
            f"Initial stop starts at fill×(1−{(trail or 0):g}/100) (peak starts at entry). "
            "Peak updates from each bar's high after the current-stop check, so a new "
            f"trail is live from the next bar. Stop hits are trail_stop.{take_txt}"
        )
    return (
        "Stop/take are computed from the signal-bar close (same as live bracket_prices; "
        "action.exit: fixed_bracket, default; stop_mode: percent). Set action.stop_mode: sma20 "
        "to rest the protective stop at SMA(20) of the signal bar. Set action.stop_mode: entry_pct "
        "for a fixed percent stop from the fill. Set action.stop_mode: lock_plus to lock the stop "
        "to +stop_loss_pct after the first touch of that print. Set action.stop_mode: trail to "
        "ratchet the stop to peak×(1−stop_loss_pct/100). Set action.exit: ma_cross "
        "to flatten at the next bar open after EMA crosses SMA against the position "
        "(long: under; short: over). Set action.exit: ema_invalid "
        "to hold until a signal-timeframe close is on the wrong side of EMA (long: close < EMA; "
        "exit at that close)."
    )


def _breakeven_assumption(config: Optional[BotConfig]) -> Optional[str]:
    if config is None:
        return None
    rules = [
        r
        for r in config.rules
        if r.enabled and r.action.type != "close" and r.action.breakeven_after_bars > 0
    ]
    if not rules:
        return None
    action = rules[0].action
    valid = (
        f"long close > EMA({action.breakeven_ema_period}) on the signal timeframe "
        f"(breakeven_valid: {action.breakeven_valid})"
        if action.breakeven_valid == "above_ema"
        else "always (breakeven_valid: always)"
    )
    need = (
        f"only if the trade is still valid ({valid})"
        if action.breakeven_requires_valid
        else "regardless of EMA validity"
    )
    return (
        f"Break-even stop (breakeven_after_bars: {action.breakeven_after_bars}): after "
        f"that many complete signal-timeframe bars finish after the entry bar "
        f"(1 = the next full candle after fill), at that close, {need}, move the stop "
        "to entry price and leave it there. If not valid, keep the original percent "
        "stop (do not retry). Same-bar stop/take on the evaluation bar still use the "
        "original stop. A later hit of the armed entry stop is exit reason breakeven_stop."
    )


def _rsi_filter_assumption(config: Optional[BotConfig]) -> Optional[str]:
    if config is None:
        return None
    exits = {
        rule.action.exit
        for rule in config.rules
        if rule.enabled and rule.action.type != "close"
    }
    label = rsi_filter_label(config)
    if label:
        rsi_cond = next(
            (
                found
                for rule in config.rules
                if rule.enabled and rule.action.type != "close"
                for found in [find_rsi_condition(rule.when)]
                if found is not None
            ),
            None,
        )
        period = rsi_cond.period if rsi_cond is not None else 14
        below = rsi_cond.below if rsi_cond is not None and rsi_cond.below is not None else 70
        noon = (
            " (same threshold as the default noon price-cross book)"
            if below == 70
            else " (tighter than the default noon book's RSI14 < 70)"
        )
        return (
            f"RSI filter on ({label}): only take the EMA/SMA pair-cross entry when "
            f"RSI({period}) on the signal timeframe is below {below:g}{noon}. "
            "YAML toggle is a sibling of ema_sma_cross: `rsi: { period: 14, below: 70 }`. "
            "Omit the rsi key to disable."
        )
    if exits == {"ma_cross"}:
        return (
            "No RSI entry filter. Add a sibling of ema_sma_cross to require RSI on the "
            "signal bar: `rsi: { period: 14, below: 70 }` (same threshold as the default "
            "noon price-cross book). Nested `ema_sma_cross.rsi` is also accepted."
        )
    return None


def _noon_entry_assumption(config: Optional[BotConfig]) -> Optional[str]:
    if config is None:
        return None
    long_txt = None
    short_txt = None
    for rule in config.rules:
        if not rule.enabled or rule.action.type == "close":
            continue
        rsi_cond = find_rsi_condition(rule.when)
        period = rsi_cond.period if rsi_cond is not None else 14
        if has_noon_stack(rule.when):
            below = rsi_cond.below if rsi_cond is not None and rsi_cond.below is not None else 70
            long_txt = (
                f"Long: close crosses above EMA(9) AND close > SMA(20) AND "
                f"RSI({period}) < {below:g}"
            )
        if has_noon_short_stack(rule.when):
            if rsi_cond is not None and rsi_cond.above is not None:
                short_txt = (
                    f"Short: close crosses below EMA(9) AND close < SMA(20) AND "
                    f"RSI({period}) > {rsi_cond.above:g}"
                )
            else:
                short_txt = (
                    "Short: close crosses below EMA(9) AND close < SMA(20) "
                    "(no RSI filter). Cover when EMA(9) crosses above SMA(20) "
                    "(next bar open) plus stop / lock_stop / session_flatten"
                )
    if not long_txt and not short_txt:
        return None
    parts = [p for p in (long_txt, short_txt) if p]
    return (
        "Entry is the noon day-trade stack on the signal timeframe "
        f"({'; '.join(parts)}). Fill at the next bar open. "
        "One position per symbol (long or short, not both); an opposite signal "
        "while in a trade is skipped (opposite_signal_in_trade)."
    )


def _session_gate_assumption(config: Optional[BotConfig]) -> Optional[str]:
    if config is None:
        return None
    s = config.settings
    if not s.entry_cutoff and not s.flatten_by:
        return None
    tz = s.session_timezone or "America/New_York"
    cutoff = s.entry_cutoff or "off"
    flatten = s.flatten_by or "off"
    return (
        f"Session gates ({tz}): entry_cutoff={cutoff} skips a signal when the next-bar "
        f"fill (bar open) is at/after that clock. flatten_by={flatten} force-flats at "
        "the close of the bar that contains that clock (exit reason session_flatten): "
        "15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when "
        "flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); "
        "5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). "
        "Stop/take/ema_invalid/ma_cross-on-this-bar still win if they hit first "
        "(ma_cross fills at the next open, so a same-bar flatten_by close wins). "
        "Set entry_cutoff / flatten_by to null / off to restore overnight holds."
    )


def _fixed_bracket_tag(config: BotConfig) -> Optional[str]:
    """Stop/take tag so 1.5/3.0, 1.0/2.0, and SMA20 books stay distinct."""
    rules = [
        r
        for r in config.rules
        if r.enabled
        and r.action.type != "close"
        and (
            r.action.exit == "fixed_bracket"
            or r.action.stop_mode in {"entry_pct", "lock_plus", "trail", "sma20"}
        )
    ]
    if not rules:
        return None
    action = rules[0].action
    take = action.take_profit_pct
    if action.stop_mode == "sma20":
        period = action.stop_sma_period
        if take is None:
            return f"SMA{period} stop"
        return f"SMA{period}/{take:.1f}"
    stop = action.stop_loss_pct
    if action.stop_mode == "entry_pct":
        if stop is None:
            return "entry stop"
        return f"entry {stop:.1f}%"
    if action.stop_mode == "lock_plus":
        trig = action.resolved_lock_trigger_pct() or stop
        if trig is None:
            return "lock+"
        return f"lock +{trig:.1f}%"
    if action.stop_mode == "trail":
        trail = action.resolved_trail_pct() or stop
        if trail is None:
            return "trail"
        return f"trail {trail:.1f}%"
    if stop is None:
        return None
    if take is None:
        return f"stop {stop:.1f}%"
    return f"{stop:.1f}/{take:.1f}"


def universe_tag(config: BotConfig) -> str:
    """AAPL+MSFT / TSLA+MU so combined books with the same gates stay distinct."""
    return "+".join(config.universe) if config.universe else ""


def sizing_tag(config: BotConfig) -> str:
    """10-share vs 1% risk so same-universe books do not share a label."""
    for rule in config.rules:
        if not rule.enabled or rule.action.type == "close":
            continue
        size = rule.action.size
        if size is None:
            continue
        if size.type == "risk_pct" and size.equity_risk is not None:
            return f"{size.equity_risk * 100:g}% risk"
        if size.type == "shares" and size.value is not None:
            value = size.value
            return f"{int(value) if float(value).is_integer() else value}-share"
        if size.type == "percent_equity" and size.value is not None:
            return f"{size.value:g}% equity"
    return ""


def side_tag(config: BotConfig) -> str:
    """long / short / long+short so isolated and combined books stay distinct."""
    sides = entry_sides(config)
    if sides == {"buy", "sell"}:
        return "long+short"
    if sides == {"sell"}:
        return "short"
    if sides == {"buy"}:
        return "long"
    return ""


def combined_book_label(config: BotConfig) -> str:
    bits = [bit for bit in (universe_tag(config), sizing_tag(config)) if bit]
    tag = side_tag(config)
    if tag in {"long+short", "short"}:
        bits.append(tag)
    return " ".join(bits) if bits else "combined"


def session_gate_suffix(config: BotConfig) -> str:
    """Book-label tag so gated and overnight books stay distinct."""
    s = config.settings
    rsi_tag = rsi_filter_label(config)
    bracket = _fixed_bracket_tag(config)
    if not s.entry_cutoff and not s.flatten_by:
        extras = [bit for bit in (bracket, rsi_tag) if bit]
        return f" ({', '.join(extras)})" if extras else ""
    bits: list[str] = []
    if s.entry_cutoff:
        bits.append(f"cutoff {s.entry_cutoff}")
    if s.flatten_by:
        bits.append(f"flat {s.flatten_by}")
    be = next(
        (
            r.action.breakeven_after_bars
            for r in config.rules
            if r.enabled and r.action.type != "close" and r.action.breakeven_after_bars > 0
        ),
        None,
    )
    if be:
        bits.append(f"BE {be}")
    exits = {
        r.action.exit
        for r in config.rules
        if r.enabled and r.action.type != "close"
    }
    short_ma = any(
        r.enabled and r.action.type == "sell" and r.action.exit == "ma_cross"
        for r in config.rules
    )
    long_bracket = any(
        r.enabled and r.action.type == "buy" and r.action.exit == "fixed_bracket"
        for r in config.rules
    )
    if short_ma and long_bracket:
        bits.append("short MA-cross")
    elif exits == {"ma_cross"}:
        bits.append("MA-cross")
    if bracket:
        bits.append(bracket)
    if rsi_tag:
        bits.append(rsi_tag)
    return " (" + ", ".join(bits) + ")"


def assumptions_rules(
    friction: str,
    starting_equity: float,
    config: Optional[BotConfig] = None,
) -> list[str]:
    notes = [
        "Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).",
        "A rule is evaluated when any of its referenced timeframes prints a newly closed bar.",
        "Entries and close-signals fill at the next bar open of the finest rule timeframe.",
        _noon_entry_assumption(config),
        _rules_exit_assumption(config),
        _breakeven_assumption(config),
        "If stop and take (or EMA-invalidation) both trade in the fill bar, the stop is assumed to fill first.",
        "A gap through stop/take fills at that bar's open. EMA-invalidation fills at the invalidating close. "
        "MA-cross exits fill at the next bar open after the opposing EMA/SMA pair-cross "
        "(long: EMA under SMA; short: EMA over SMA).",
        "One open lot per symbol (no pyramiding; long or short, not both). "
        "A second signal while that symbol is already open is skipped "
        "(already_in_position, or opposite_signal_in_trade when the new side is the other way).",
        "A second symbol may open at the same time when cash covers its sized notional; otherwise the later signal is skipped (insufficient_cash).",
        "Open lots still on the last bar are flattened at the last close (exit reason eod).",
        "Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.",
        friction,
        f"Starting equity ${starting_equity:,.2f}. Size types: shares, percent_equity, or risk_pct "
        "(percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); "
        "stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).",
    ]
    rsi_note = _rsi_filter_assumption(config)
    if rsi_note:
        notes.insert(-3, rsi_note)
    gate = _session_gate_assumption(config)
    if gate:
        notes.insert(-3, gate)
    return [n for n in notes if n]


def pattern_hits_from_result(result: BacktestResult) -> dict[str, int]:
    hits: dict[str, int] = {}
    if result.label == "orb_reversal" or result.report.rule_id == "orb_reversal":
        if result.report.signals:
            hits["orb_reversal"] = result.report.signals
        return hits
    for sig in result.signals:
        for name in PATTERN_HIT_NAMES:
            if f"{name} matched" in sig.reason:
                hits[name] = hits.get(name, 0) + 1
                break
    return hits


def compact_run(result: BacktestResult, hits: Optional[dict[str, int]] = None) -> dict[str, Any]:
    payload = result.to_dict()
    payload["pattern_hits"] = hits if hits is not None else pattern_hits_from_result(result)
    return {
        "label": payload["label"],
        "report": payload["report"],
        "bars_used": payload["bars_used"],
        "pattern_hits": payload["pattern_hits"],
        "trades": payload["trades"],
        "period_stats": payload.get("period_stats"),
        "signals": [
            {
                k: sig[k]
                for k in (
                    "rule_id",
                    "symbol",
                    "action_type",
                    "signal_time",
                    "accepted",
                    "skip_reason",
                )
            }
            for sig in payload["signals"]
        ],
    }


def entry_rule_ids(config: BotConfig) -> list[str]:
    return [rule.id for rule in config.rules if rule.action.type != "close"]


def rule_book_plan(
    config: BotConfig,
    *,
    combined_only: bool = False,
    include_entries_only: bool = True,
) -> list[tuple[str, Optional[list[str]], Optional[str]]]:
    """Return (label, rule_ids or None for all rules, extra_note)."""
    if combined_only:
        return [(combined_book_label(config), None, COMBINED_NOTE)]
    plans: list[tuple[str, Optional[list[str]], Optional[str]]] = []
    for rule in config.rules:
        note = EXIT_ONLY_NOTE if rule.action.type == "close" else None
        plans.append((rule.id, [rule.id], note))
    entries = entry_rule_ids(config)
    close_rules = [rule for rule in config.rules if rule.action.type == "close"]
    if include_entries_only and len(entries) >= 2 and close_rules:
        plans.append(("sample-entries", entries, ENTRIES_ONLY_NOTE))
    if len(config.rules) > 1:
        long_short = entry_sides(config) == {"buy", "sell"} and not close_rules
        extra = LONG_SHORT_COMBINED_NOTE if long_short else COMBINED_NOTE
        label = combined_book_label(config) if long_short else "combined"
        plans.append((label, None, extra))
    return plans


def run_orb_book(
    config: OrbBotConfig,
    bars: dict,
    *,
    starting_equity: float,
    commission: float,
    slippage_pct: float,
    data_source: str,
    notes: Optional[list[str]] = None,
) -> dict[str, Any]:
    result = run_orb_backtest(
        config,
        bars,
        starting_equity=starting_equity,
        commission=commission,
        slippage_pct=slippage_pct,
        label="orb_reversal",
        data_source=data_source,
        notes=notes,
    )
    return compact_run(result)


def run_rule_books(
    config: BotConfig,
    bars: dict,
    *,
    starting_equity: float,
    commission: float,
    slippage_pct: float,
    data_source: str,
    assumptions: list[str],
    combined_only: bool = False,
    include_entries_only: bool = True,
    label_prefix: str = "",
    breakout_symbols: Optional[list[str]] = None,
    breakout_rule_ids: Optional[list[str]] = None,
    trade_start: Optional[datetime] = None,
    trade_end: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    prefix = f"{label_prefix} " if label_prefix else ""
    suffix = session_gate_suffix(config)

    def _run(label: str, subset: BotConfig, extra: Optional[str] = None) -> None:
        notes = list(assumptions)
        if extra:
            notes.append(extra)
        result = run_backtest(
            subset,
            bars,
            starting_equity=starting_equity,
            commission=commission,
            slippage_pct=slippage_pct,
            label=label,
            data_source=data_source,
            notes=notes,
            trade_start=trade_start,
            trade_end=trade_end,
        )
        runs.append(compact_run(result))

    for label, ids, extra in rule_book_plan(
        config, combined_only=combined_only, include_entries_only=include_entries_only
    ):
        _run(f"{prefix}{label}{suffix}", restrict_config(config, ids), extra)

    wanted_breakouts = [s.strip().upper() for s in (breakout_symbols or []) if s and str(s).strip()]
    if wanted_breakouts and not combined_only:
        entry_ids = breakout_rule_ids or [
            rule.id for rule in config.rules if rule.enabled and rule.action.type != "close" and rule.id == "ema9_trend"
        ]
        if not entry_ids:
            entry_ids = entry_rule_ids(config)[:1]
        for rule_id in entry_ids:
            for symbol in wanted_breakouts:
                try:
                    subset = restrict_universe(restrict_config(config, [rule_id]), [symbol])
                except ValueError:
                    continue
                _run(
                    f"{prefix}{rule_id} {symbol}{suffix}",
                    subset,
                    f"Isolated {symbol} book — its own equity curve, not mixed with the full universe.",
                )
    return runs


def yahoo_cap_for_tf(timeframe: str) -> Optional[str]:
    pair = YAHOO_INTERVAL.get(normalize(timeframe))
    return pair[1] if pair else None


def data_window_notes(spans: list[str], sources: dict[str, str]) -> list[str]:
    notes = [YAHOO_CAP_NOTE]
    yahooish = any(
        str(v).startswith("yahoo") or "Yahoo" in str(v) or str(v).startswith("cache:")
        for v in sources.values()
    )
    if yahooish:
        notes.append(
            "5m and 15m history is the binding limit for ORB and for the 15m sample rules. "
            "The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer "
            "and its P&L% is not time-normalized against the 60-day books."
        )
    if spans:
        notes.append("Actual closed-bar windows downloaded:")
        notes.extend(f"  {span}" for span in spans)
    return notes


def _period_days(report: dict[str, Any]) -> Optional[float]:
    start = report.get("period_start")
    end = report.get("period_end")
    if not start or not end:
        return None
    try:
        a = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
    except ValueError:
        return None
    return max((b - a).total_seconds() / 86400.0, 0.0)


def sample_size_caveat(report: dict[str, Any]) -> str:
    trades = int(report.get("trades") or 0)
    notes: list[str] = []
    extra = " ".join(report.get("notes") or [])
    if "Exit-only" in extra or trades == 0 and "close" in (report.get("rule_id") or ""):
        notes.append("exit-only / no isolated entries")
    if trades == 0:
        notes.append("no closed trades")
    elif trades < 30:
        notes.append(f"small sample ({trades} trades)")
    days = _period_days(report)
    if days is not None and days >= 300:
        notes.append(f"longer window (~{days:.0f}d) vs ~60d 5m/15m books")
    elif days is not None and days > 0:
        notes.append(f"~{days:.0f} calendar days")
    return "; ".join(notes) if notes else "—"


def rank_books(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank compact runs by total P&L % (engine figure, not annualized)."""
    ranked: list[dict[str, Any]] = []
    ordered = sorted(
        runs,
        key=lambda block: float(block["report"].get("total_pnl_pct") or 0.0),
        reverse=True,
    )
    for i, block in enumerate(ordered, start=1):
        report = block["report"]
        ranked.append(
            {
                "rank": i,
                "label": block.get("label") or report.get("rule_id"),
                "trades": report.get("trades"),
                "win_rate_pct": report.get("win_rate_pct"),
                "total_pnl": report.get("total_pnl"),
                "total_pnl_pct": report.get("total_pnl_pct"),
                "max_drawdown": report.get("max_drawdown"),
                "max_drawdown_pct": report.get("max_drawdown_pct"),
                "avg_win": report.get("avg_win"),
                "avg_loss": report.get("avg_loss"),
                "period_start": report.get("period_start"),
                "period_end": report.get("period_end"),
                "data_source": report.get("data_source"),
                "caveat": sample_size_caveat(report),
            }
        )
    return ranked


def _fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def _fmt_pct(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}%"


def combined_book_effect(runs: list[dict[str, Any]]) -> Optional[str]:
    by_label = {block.get("label"): block for block in runs}
    entries = by_label.get("sample-entries")
    combined = by_label.get("combined")
    exit_only = by_label.get("evening-star-or-engulfing-exit")
    if not entries or not combined:
        return None
    e = entries["report"]
    c = combined["report"]
    fires = (exit_only or {}).get("report", {}).get("signals")
    close_exits = (c.get("exit_reasons") or {}).get("close_signal", 0)
    delta = c["total_pnl"] - e["total_pnl"]
    fire_txt = f"{fires} isolated fires" if fires is not None else "n/a isolated fires"
    return (
        f"sample-entries (B+C) P&L ${e['total_pnl']:,.2f} on {e['trades']} trades vs "
        f"combined (B+C+D) P&L ${c['total_pnl']:,.2f} on {c['trades']} trades "
        f"({delta:+,.2f} from adding D). Exit-only isolated book: {fire_txt}, $0 P&L. "
        f"Combined book flattened {close_exits} lots on close_signal. "
        "More combined trades than the entries book because flattening frees the symbol for a later entry."
    )


def _signal_mix(report: dict[str, Any]) -> str:
    n = int(report.get("signals") or 0)
    by_symbol = report.get("signals_by_symbol") or {}
    if not by_symbol:
        return str(n)
    detail = ", ".join(f"{sym} {count}" for sym, count in sorted(by_symbol.items()))
    return f"{n} ({detail})"


def _skip_mix(report: dict[str, Any]) -> str:
    reasons = report.get("skip_reasons") or {}
    parts = [f"{key} {count}" for key, count in sorted(reasons.items()) if count]
    return ", ".join(parts) if parts else "—"


def _side_mix(report: dict[str, Any]) -> str:
    sides = report.get("sides") or {}
    if not sides:
        return "—"
    labels = {"buy": "long", "sell": "short"}
    parts = []
    for key in ("buy", "sell"):
        block = sides.get(key)
        if not block:
            continue
        wr = _fmt_pct(block.get("win_rate_pct"), 2)
        parts.append(
            f"{labels.get(key, key)} {int(block.get('trades') or 0)}t {wr} "
            f"{_fmt_money(block.get('total_pnl'))}"
        )
    return "; ".join(parts) if parts else "—"


def exit_mix(report: dict[str, Any]) -> str:
    reasons = report.get("exit_reasons") or {}
    take = int(reasons.get("take") or 0)
    stop = int(reasons.get("stop") or 0)
    eod = int(reasons.get("eod") or 0)
    ema_inv = int(reasons.get("ema_invalid") or 0)
    ma_x = int(reasons.get("ma_cross") or 0)
    sess = int(reasons.get("session_flatten") or 0)
    be_stop = int(reasons.get("breakeven_stop") or 0)
    lock_stop = int(reasons.get("lock_stop") or 0)
    trail_stop = int(reasons.get("trail_stop") or 0)
    parts: list[str] = []
    if ema_inv:
        parts.append(f"ema_invalid {ema_inv}")
    if ma_x:
        parts.append(f"ma_cross {ma_x}")
    parts.extend([f"take {take}", f"stop {stop}"])
    if be_stop:
        parts.append(f"breakeven_stop {be_stop}")
    if lock_stop:
        parts.append(f"lock_stop {lock_stop}")
    if trail_stop:
        parts.append(f"trail_stop {trail_stop}")
    if sess:
        parts.append(f"session_flatten {sess}")
    if eod:
        parts.append(f"eod {eod}")
    extra = [
        f"{key} {count}"
        for key, count in reasons.items()
        if key
        not in {
            "take",
            "stop",
            "eod",
            "ema_invalid",
            "ma_cross",
            "session_flatten",
            "breakeven_stop",
            "lock_stop",
            "trail_stop",
        }
        and count
    ]
    parts.extend(extra)
    return ", ".join(parts)


def format_monthly_side_by_side(runs: list[dict[str, Any]]) -> list[str]:
    """One row per calendar month across compared books (realized P&L)."""
    columns: list[tuple[str, list[dict[str, Any]]]] = []
    keys: list[str] = []
    seen: set[str] = set()
    for block in runs:
        months = (block.get("period_stats") or {}).get("months") or []
        if not months:
            continue
        label = str(block.get("label") or (block.get("report") or {}).get("rule_id") or "book")
        columns.append((label, months))
        for row in months:
            key = f"{row.get('year')}-{int(row.get('calendar_month') or 0):02d}"
            if key not in seen:
                seen.add(key)
                keys.append(key)
    if not columns or not keys:
        return []
    lines = [
        "| Month | " + " | ".join(name for name, _ in columns) + " |",
        "| --- | " + " | ".join(["---:" for _ in columns]) + " |",
    ]
    by_col = []
    for _name, months in columns:
        by_col.append(
            {
                f"{row.get('year')}-{int(row.get('calendar_month') or 0):02d}": row
                for row in months
            }
        )
    for key in keys:
        cells = []
        for lookup in by_col:
            row = lookup.get(key)
            if row is None:
                cells.append("—")
                continue
            cells.append(
                "{pnl} ({trades}t, {win})".format(
                    pnl=_fmt_money(row.get("pnl")),
                    trades=row.get("trades") or 0,
                    win=_fmt_pct(row.get("win_rate_pct"), 2),
                )
            )
        lines.append(f"| {key} | " + " | ".join(cells) + " |")
    return lines


def format_side_by_side_table(columns: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Side-by-side trades, win rate, P&L, max DD, avg win/loss, takes vs stops."""
    reports = [(name, (block.get("report") or block)) for name, block in columns]
    names = [name for name, _ in reports]
    lines = [
        "| | " + " | ".join(names) + " |",
        "| --- | " + " | ".join(["---:" for _ in names]) + " |",
    ]

    def cells(fmt) -> str:
        return " | ".join(fmt(report) for _name, report in reports)

    rows = [
        ("Signals", lambda r: _signal_mix(r)),
        ("Skips", lambda r: _skip_mix(r)),
        ("Trades", lambda r: str(int(r.get("trades") or 0))),
        ("Win rate", lambda r: _fmt_pct(r.get("win_rate_pct"), 2)),
        ("P&L", lambda r: _fmt_money(r.get("total_pnl"))),
        ("Max DD", lambda r: _fmt_money(r.get("max_drawdown"))),
        ("Avg win", lambda r: _fmt_money(r.get("avg_win"))),
        ("Avg loss", lambda r: _fmt_money(r.get("avg_loss"))),
        ("Takes vs stops", lambda r: exit_mix(r)),
        ("BE armed", lambda r: str(int(r.get("breakeven_armed") or 0))),
        ("Lock armed", lambda r: str(int(r.get("lock_armed") or 0))),
        ("Trail ratcheted", lambda r: str(int(r.get("trail_ratcheted") or 0))),
        ("By side", lambda r: _side_mix(r)),
    ]
    for label, fmt in rows:
        lines.append(f"| {label} | {cells(fmt)} |")
    return lines


def format_comparison_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        period = "n/a"
        if row.get("period_start") and row.get("period_end"):
            period = f"{row['period_start']} → {row['period_end']}"
        lines.append(
            "| {rank} | {label} | {trades} | {win} | {pnl} | {pnl_pct} | {dd} | {avg_w} | {avg_l} | {period} | {caveat} |".format(
                rank=row["rank"],
                label=row["label"],
                trades=row.get("trades") if row.get("trades") is not None else 0,
                win=_fmt_pct(row.get("win_rate_pct"), 2),
                pnl=_fmt_money(row.get("total_pnl")),
                pnl_pct=_fmt_pct(row.get("total_pnl_pct"), 3),
                dd=_fmt_money(row.get("max_drawdown")),
                avg_w=_fmt_money(row.get("avg_win")),
                avg_l=_fmt_money(row.get("avg_loss")),
                period=period,
                caveat=row.get("caveat") or "—",
            )
        )
    return lines


def format_comparison_md(payload: dict[str, Any]) -> str:
    lines = [
        "# ORB vs sample-rule backtest comparison",
        "",
        f"- Generated (UTC): {payload.get('generated_at')}",
        f"- Configs: {', '.join(payload.get('configs') or [payload.get('config') or ''])}",
        f"- Starting equity: ${payload.get('starting_equity'):,.2f}"
        if payload.get("starting_equity") is not None
        else "",
        f"- Commission / slippage: {payload.get('friction')}",
        f"- Data: {payload.get('data_source')}",
        "",
        "## Ranking by P&L % of starting equity",
        "",
        "Figures are the engine totals for each book. They are **not** annualized and "
        "**not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). "
        "Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.",
        "",
    ]
    rows = payload.get("comparison") or rank_books(payload.get("runs") or [])
    lines.extend(format_comparison_table(rows))
    lines.extend(["", MULTI_ENGINE_NOTE, ""])
    effect = combined_book_effect(payload.get("runs") or [])
    if effect:
        lines.extend(["## Combined-book effect of the exit-only rule", "", effect, ""])

    window_notes = payload.get("window_notes") or []
    if window_notes:
        lines.extend(["## Data windows and Yahoo limits", ""])
        for note in window_notes:
            lines.append(f"- {note}" if not note.startswith("  ") else f"- `{note.strip()}`")
        lines.append("")

    month_table = format_monthly_side_by_side(payload.get("runs") or [])
    if month_table:
        lines.extend(["## Monthly breakdown (realized P&L)", ""])
        lines.extend(month_table)
        lines.append("")

    per_book = format_report_md(
        {
            "generated_at": payload.get("generated_at"),
            "starting_equity": payload.get("starting_equity"),
            "friction": payload.get("friction"),
            "data_source": payload.get("data_source"),
            "runs": payload.get("runs") or [],
            "assumptions": payload.get("assumptions") or [],
        }
    )
    # Drop the duplicate title block; keep per-book sections + assumptions.
    body = per_book.split("\n", 1)[1] if per_book.startswith("# ") else per_book
    lines.append("# Per-book detail")
    lines.append(body)
    return "\n".join(line for line in lines if line is not None)
