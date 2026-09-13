# Rule backtest results

BEFORE vs AFTER on this same Yahoo window: `artifacts/orb_reversal_in_range_first_profit_comparison.md`.

- Generated (UTC): 2026-09-13T14:50:42.026506Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## orb_reversal

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:15Min': 1560, 'AAPL:5Min': 4677, 'MSFT:15Min': 1560, 'MSFT:5Min': 4676, 'SPY:15Min': 1560, 'SPY:5Min': 4680}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 152  (by symbol: {'AAPL': 55, 'MSFT': 48, 'SPY': 49})
- Pattern hits in those signals: {'orb_reversal': 152}
- Trades: 31  (by symbol: {'AAPL': 10, 'MSFT': 13, 'SPY': 8})
- Wins / losses / scratch: 13 / 18 / 0
- Win rate: 41.94%
- Total P&L: $-74.17 (-0.074% of starting equity)
- Avg win: $4.98
- Avg loss: $-7.72
- Max drawdown: $81.00 (0.08%)
- Ending equity: $99,925.83
- Exit reasons: {'take': 13, 'stop': 18}

## Assumptions

- Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).
- After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.
- Probe = signal bar must touch the opening-range extreme (top: high >= OR high; bottom: low <= OR low) AND close inside the 5% (configurable) edge band (top: [or_high - band, or_high]; bottom: [or_low, or_low + band]) (probe_mode: touch_and_band, default).
- Reversal = the next signal bar, opposite color (top+bearish → short, bottom+bullish → long).
- Reversal close must sit inside the opening range (or_low <= close <= or_high; reversal_in_range: close, default). If the reversal closes outside the OR, do not enter. Set orb.reversal_in_range: body for the stricter fully-inside mode (high and low within the OR), or off to disable the filter.
- Entry fills at the open of the bar after the reversal candle.
- Stop is the opening-range extreme (long → OR low, short → OR high); take-profit is the close of the first signal-timeframe bar that is strictly profitable vs entry (long: close > entry; short: close < entry; take_profit_mode: first_profitable_close, default). Set orb.stop_mode: reversal_candle to restore the previous candle-extreme stop. Set orb.take_profit_mode: or_midpoint to restore the previous midpoint target.
- At most 1 entry per symbol per session, and only if that entry is before 10:30 America/New_York (no new entries at/after the cutoff). One open position per symbol unless on_open_position=replace.
- If stop and take (midpoint or first-profit close) both trade in the same bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Short mark-to-market subtracts qty × mark from cash that already includes short proceeds. The previous 2×entry − mark formula double-counted proceeds and invented a drawdown when shorts flattened; closed-trade P&L was already correct.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
