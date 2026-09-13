# Rule backtest results

BEFORE vs AFTER on this same Yahoo window: `artifacts/orb_probe_touch_and_band_comparison.md`.

- Generated (UTC): 2026-09-13T14:33:59.311231Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## orb_reversal

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:15Min': 1560, 'AAPL:5Min': 4677, 'MSFT:15Min': 1560, 'MSFT:5Min': 4676, 'SPY:15Min': 1560, 'SPY:5Min': 4680}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 153  (by symbol: {'AAPL': 55, 'MSFT': 48, 'SPY': 50})
- Pattern hits in those signals: {'orb_reversal': 153}
- Trades: 31  (by symbol: {'AAPL': 10, 'MSFT': 13, 'SPY': 8})
- Wins / losses / scratch: 12 / 17 / 2
- Win rate: 38.71%
- Total P&L: $27.67 (0.028% of starting equity)
- Avg win: $10.11
- Avg loss: $-5.51
- Max drawdown: $46.45 (0.05%)
- Ending equity: $100,027.67
- Exit reasons: {'take': 14, 'stop': 17}

## Assumptions

- Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).
- After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.
- Probe = signal bar must touch the opening-range extreme (top: high >= OR high; bottom: low <= OR low) AND close inside the 5% (configurable) edge band (top: [or_high - band, or_high]; bottom: [or_low, or_low + band]) (probe_mode: touch_and_band, default).
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
