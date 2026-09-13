# Rule backtest results

BEFORE vs AFTER on this same Yahoo window: `artifacts/orb_one_r_vol_gate_comparison.md`.

- Generated (UTC): 2026-09-13T15:13:24.838378Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## orb_reversal

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:15Min': 1560, 'AAPL:5Min': 4677, 'MSFT:15Min': 1560, 'MSFT:5Min': 4676, 'SOXL:15Min': 1560, 'SOXL:5Min': 4680, 'SPY:15Min': 1560, 'SPY:5Min': 4680}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 208  (by symbol: {'AAPL': 55, 'MSFT': 48, 'SPY': 49, 'SOXL': 56})
- Pattern hits in those signals: {'orb_reversal': 208}
- Trades: 20  (by symbol: {'MSFT': 11, 'AAPL': 7, 'SOXL': 2})
- Wins / losses / scratch: 7 / 13 / 0
- Win rate: 35.00%
- Total P&L: $-77.67 (-0.078% of starting equity)
- Avg win: $9.00
- Avg loss: $-10.82
- Max drawdown: $97.03 (0.10%)
- Ending equity: $99,922.33
- Exit reasons: {'take': 7, 'stop': 13}

## Assumptions

- Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).
- After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.
- Probe = signal bar must touch the opening-range extreme (top: high >= OR high; bottom: low <= OR low) AND close inside the 5% (configurable) edge band (top: [or_high - band, or_high]; bottom: [or_low, or_low + band]) (probe_mode: touch_and_band, default).
- Reversal = the next signal bar, opposite color (top+bearish → short, bottom+bullish → long).
- Reversal close must sit inside the opening range (or_low <= close <= or_high; reversal_in_range: close, default). If the reversal closes outside the OR, do not enter. Set orb.reversal_in_range: body for the stricter fully-inside mode (high and low within the OR), or off to disable the filter.
- Entry fills at the open of the bar after the reversal candle.
- Stop is the opening-range extreme (long → OR low, short → OR high); take-profit is 1R from entry (R = |entry − stop|; long: entry + R; short: entry − R; take_profit_mode: one_r, default). Set orb.stop_mode: reversal_candle to restore the previous candle-extreme stop. Set orb.take_profit_mode: or_midpoint to restore the previous midpoint target. Set orb.take_profit_mode: first_profitable_close to restore the first-profit close exit.
- High-vol gate: trade only when (or_high − or_low) / or_open >= 1.00% (min_or_height_pct, default 1%). Denominator is the OR candle open; if that print is missing, the OR midpoint is used. Below the threshold, skip the symbol for that session (no entries). Set 0 / null to disable.
- At most 1 entry per symbol per session, and only if that entry is before 10:30 America/New_York (no new entries at/after the cutoff). One open position per symbol unless on_open_position=replace.
- If stop and take (1R, midpoint, or first-profit close) both trade in the same bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Short mark-to-market subtracts qty × mark from cash that already includes short proceeds. The previous 2×entry − mark formula double-counted proceeds and invented a drawdown when shorts flattened; closed-trade P&L was already correct.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
