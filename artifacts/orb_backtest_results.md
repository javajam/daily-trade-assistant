# Rule backtest results

- Generated (UTC): 2026-09-13T13:17:59.262755Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## orb_reversal

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:15Min': 1560, 'AAPL:5Min': 4677, 'MSFT:15Min': 1560, 'MSFT:5Min': 4676, 'SPY:15Min': 1560, 'SPY:5Min': 4680}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 192  (by symbol: {'AAPL': 76, 'MSFT': 60, 'SPY': 56})
- Pattern hits in those signals: {'orb_reversal': 192}
- Trades: 182  (by symbol: {'AAPL': 69, 'MSFT': 59, 'SPY': 54})
- Wins / losses / scratch: 51 / 125 / 6
- Win rate: 28.02%
- Total P&L: $7.04 (0.007% of starting equity)
- Avg win: $12.92
- Avg loss: $-5.21
- Max drawdown: $174.39 (0.17%)
- Ending equity: $100,007.04
- Exit reasons: {'take': 55, 'stop': 126, 'eod': 1}

## Assumptions

- Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).
- After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.
- Probe = signal-bar close inside the 5% (configurable) edge band under the OR high or above the OR low.
- Reversal = the next signal bar, opposite color (top+bearish → short, bottom+bullish → long).
- Entry fills at the open of the bar after the reversal candle.
- Stop is the reversal candle extreme; take-profit is the OR midpoint (v1; A/B tested later).
- Multiple trades are allowed (no daily cap). One open position per symbol; new signals skip while in a position unless on_open_position=replace.
- If stop and take both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Short mark-to-market subtracts qty × mark from cash that already includes short proceeds. The previous 2×entry − mark formula double-counted proceeds and invented a drawdown when shorts flattened; closed-trade P&L was already correct.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
