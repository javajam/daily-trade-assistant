# Rule backtest results

BEFORE vs AFTER on this same Yahoo window: `artifacts/orb_ema_cross_comparison.md`.

- Generated (UTC): 2026-09-13T15:41:18.781362Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## orb_reversal

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:15Min': 1560, 'AAPL:5Min': 4677, 'MSFT:15Min': 1560, 'MSFT:5Min': 4676, 'SOXL:15Min': 1560, 'SOXL:5Min': 4680, 'SPY:15Min': 1560, 'SPY:5Min': 4680}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 132  (by symbol: {'AAPL': 34, 'MSFT': 23, 'SPY': 35, 'SOXL': 40})
- Pattern hits in those signals: {'orb_reversal': 132}
- Trades: 5  (by symbol: {'AAPL': 4, 'MSFT': 1})
- Wins / losses / scratch: 1 / 4 / 0
- Win rate: 20.00%
- Total P&L: $-11.80 (-0.012% of starting equity)
- Avg win: $37.00
- Avg loss: $-12.20
- Max drawdown: $55.00 (0.05%)
- Ending equity: $99,988.20
- Exit reasons: {'take': 2, 'stop': 3}

## Assumptions

- Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).
- After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.
- Probe = signal bar must touch the opening-range extreme (top: high >= OR high; bottom: low <= OR low) AND close inside the 5% (configurable) edge band (top: [or_high - band, or_high]; bottom: [or_low, or_low + band]) (probe_mode: touch_and_band, default).
- Reversal = the next signal bar, opposite color (top+bearish → short, bottom+bullish → long).
- Reversal close must sit inside the opening range (or_low <= close <= or_high; reversal_in_range: close, default). If the reversal closes outside the OR, do not enter. Set orb.reversal_in_range: body for the stricter fully-inside mode (high and low within the OR), or off to disable the filter.
- EMA filter (ema_filter: true, default): compute EMA(9) on the signal timeframe through the reversal bar (inclusive). Long: close > EMA9; short: close < EMA9. Default compare is close vs EMA (ema_require_open: false). If EMA cannot be computed (not enough closes), skip the entry. Set ema_filter: false to disable.
- Entry fills at the open of the bar after the reversal candle.
- Stop is the opening-range extreme (long → OR low, short → OR high); take-profit is the close of the first post-entry signal-timeframe bar on the other side of EMA(9) (long: close < EMA; short: close > EMA; take_profit_mode: ema_cross, default). Set orb.stop_mode: reversal_candle to restore the previous candle-extreme stop. Set orb.take_profit_mode: or_midpoint for the OR-midpoint target. Set orb.take_profit_mode: one_r for a 1R target. Set orb.take_profit_mode: first_profitable_close to restore the first-profit close exit.
- High-vol gate: trade only when (or_high − or_low) / or_open >= 1.00% (min_or_height_pct, default 1%). Denominator is the OR candle open; if that print is missing, the OR midpoint is used. Below the threshold, skip the symbol for that session (no entries). Set 0 / null to disable.
- At most 1 entry per symbol per session, and only if that entry is before 10:30 America/New_York (no new entries at/after the cutoff). One open position per symbol unless on_open_position=replace.
- If stop and take (EMA-cross, 1R, midpoint, or first-profit close) both trade in the same bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Short mark-to-market subtracts qty × mark from cash that already includes short proceeds. The previous 2×entry − mark formula double-counted proceeds and invented a drawdown when shorts flattened; closed-trade P&L was already correct.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
