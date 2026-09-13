# Rule backtest results

- Generated (UTC): 2026-09-13T12:18:28.419959Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## engulfing-with-trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 94  (by symbol: {'AAPL': 50, 'MSFT': 44})
- Pattern hits in those signals: {'bullish_engulfing': 94}
- Trades: 39  (by symbol: {'MSFT': 19, 'AAPL': 20})
- Wins / losses / scratch: 17 / 22 / 0
- Win rate: 43.59%
- Total P&L: $697.90 (0.698% of starting equity)
- Avg win: $123.00
- Avg loss: $-63.32
- Max drawdown: $471.57 (0.47%)
- Ending equity: $100,697.90
- Exit reasons: {'stop': 22, 'take': 16, 'eod': 1}

## hammer-oversold

- Period: 2024-09-12T13:30:00Z → 2026-09-11T19:30:00Z
- Bars used: {'SPY:1Hour': 3477}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 34  (by symbol: {'SPY': 34})
- Pattern hits in those signals: {'hammer': 34}
- Trades: 24  (by symbol: {'SPY': 24})
- Wins / losses / scratch: 10 / 14 / 0
- Win rate: 41.67%
- Total P&L: $112.67 (0.113% of starting equity)
- Avg win: $33.08
- Avg loss: $-15.58
- Max drawdown: $142.76 (0.14%)
- Ending equity: $100,112.67
- Exit reasons: {'take': 9, 'stop': 14, 'eod': 1}

## evening-star-or-engulfing-exit

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560, 'SPY:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 560  (by symbol: {'SPY': 188, 'MSFT': 189, 'AAPL': 183})
- Pattern hits in those signals: {'bearish_engulfing': 356, 'evening_star': 280}
- Trades: 0  (by symbol: {})
- Wins / losses / scratch: 0 / 0 / 0
- Win rate: n/a
- Total P&L: $0.00 (0.000% of starting equity)
- Avg win: n/a
- Avg loss: n/a
- Max drawdown: $0.00 (0.00%)
- Ending equity: $100,000.00
- Exit reasons: {}
- Exit-only rule: isolated book has no entries, so P&L is $0. Signal count is how often the pattern would have fired; the combined book uses those fires to flatten longs from the entry rules.

## combined

- Period: 2024-09-12T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560, 'SPY:15Min': 1560, 'SPY:1Hour': 3477}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 688  (by symbol: {'SPY': 222, 'MSFT': 233, 'AAPL': 233})
- Pattern hits in those signals: {'hammer': 34, 'bearish_engulfing': 356, 'evening_star': 280, 'bullish_engulfing': 94}
- Trades: 110  (by symbol: {'SPY': 26, 'AAPL': 44, 'MSFT': 40})
- Wins / losses / scratch: 46 / 63 / 1
- Win rate: 41.82%
- Total P&L: $447.01 (0.447% of starting equity)
- Avg win: $30.87
- Avg loss: $-15.44
- Max drawdown: $273.85 (0.27%)
- Ending equity: $100,447.01
- Exit reasons: {'take': 13, 'stop': 16, 'close_signal': 81}

## Assumptions

- Signals come from the live evaluate_rule path (same pattern/SMA/RSI/volume detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Stop/take are computed from the signal-bar close (same as live bracket_prices).
- If stop and take both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open.
- One open lot per symbol (no pyramiding). A second signal while flat-in-symbol is skipped.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
