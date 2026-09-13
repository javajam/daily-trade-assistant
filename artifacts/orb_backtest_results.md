# Rule backtest results

BEFORE vs AFTER on this same Yahoo window: `artifacts/orb_stop_cutoff_comparison.md`.

- Generated (UTC): 2026-09-13T14:11:07.072611Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## orb_reversal

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:15Min': 1560, 'AAPL:5Min': 4677, 'MSFT:15Min': 1560, 'MSFT:5Min': 4676, 'SPY:15Min': 1560, 'SPY:5Min': 4680}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 192  (by symbol: {'AAPL': 76, 'MSFT': 60, 'SPY': 56})
- Pattern hits in those signals: {'orb_reversal': 192}
- Trades: 39  (by symbol: {'AAPL': 14, 'MSFT': 15, 'SPY': 10})
- Wins / losses / scratch: 13 / 23 / 3
- Win rate: 33.33%
- Total P&L: $14.63 (0.015% of starting equity)
- Avg win: $10.22
- Avg loss: $-5.14
- Max drawdown: $49.25 (0.05%)
- Ending equity: $100,014.63
- Exit reasons: {'take': 16, 'stop': 23}

## Assumptions

- Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).
- After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.
- Probe = signal-bar close inside the 5% (configurable) edge band under the OR high or above the OR low.
- Reversal = the next signal bar, opposite color (top+bearish → short, bottom+bullish → long).
- Entry fills at the open of the bar after the reversal candle.
- Stop is the opening-range extreme (long → OR low, short → OR high); take-profit remains the OR midpoint (v1; A/B tested later). Set orb.stop_mode: reversal_candle to restore the previous candle-extreme stop.
- At most 1 entry per symbol per session, and only if that entry is before 10:30 America/New_York (no new entries at/after the cutoff). One open position per symbol unless on_open_position=replace.
- If stop and take both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Short mark-to-market subtracts qty × mark from cash that already includes short proceeds. The previous 2×entry − mark formula double-counted proceeds and invented a drawdown when shorts flattened; closed-trade P&L was already correct.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
