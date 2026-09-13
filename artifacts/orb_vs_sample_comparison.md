# ORB vs sample-rule backtest comparison

- Generated (UTC): 2026-09-13T13:17:56.926182Z
- Configs: config/orb_reversal.example.yaml, config/rules.example.yaml
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## Ranking by P&L % of starting equity

Figures are the engine totals for each book. They are **not** annualized and **not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.

| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | sample-entries | 63 | 42.86% | $810.57 | 0.811% | $498.00 | $89.70 | $-44.76 | 2024-09-12T13:30:00Z → 2026-09-11T19:45:00Z | longer window (~729d) vs ~60d 5m/15m books |
| 2 | engulfing-with-trend | 39 | 43.59% | $697.90 | 0.698% | $471.57 | $123.00 | $-63.32 | 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z | ~86 calendar days |
| 3 | combined | 110 | 41.82% | $447.01 | 0.447% | $273.85 | $30.87 | $-15.44 | 2024-09-12T13:30:00Z → 2026-09-11T19:45:00Z | longer window (~729d) vs ~60d 5m/15m books |
| 4 | hammer-oversold | 24 | 41.67% | $112.67 | 0.113% | $142.76 | $33.08 | $-15.58 | 2024-09-12T13:30:00Z → 2026-09-11T19:30:00Z | small sample (24 trades); longer window (~729d) vs ~60d 5m/15m books |
| 5 | orb_reversal | 182 | 28.02% | $7.04 | 0.007% | $174.39 | $12.92 | $-5.21 | 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z | ~86 calendar days |
| 6 | evening-star-or-engulfing-exit | 0 | n/a | $0.00 | 0.000% | $0.00 | n/a | n/a | 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z | exit-only / no isolated entries; no closed trades; ~86 calendar days |

ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.

## Combined-book effect of the exit-only rule

sample-entries (B+C) P&L $810.57 on 63 trades vs combined (B+C+D) P&L $447.01 on 110 trades (-363.56 from adding D). Exit-only isolated book: 560 isolated fires, $0 P&L. Combined book flattened 81 lots on close_signal. More combined trades than the entries book because flattening frees the symbol for a later entry.

## Data windows and Yahoo limits

- Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. Requesting more than the cap returns HTTP 422. ORB needs 15m to build the opening range and 5m for probe/reversal, so its longest reliable Yahoo window is the 5m/15m 60-day cap.
- 5m and 15m history is the binding limit for ORB and for the 15m sample rules. The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer and its P&L% is not time-normalized against the 60-day books.
- Actual closed-bar windows downloaded:
- `AAPL 15Min: 1560 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:45:00+00:00`
- `AAPL 5Min: 4677 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:55:00+00:00`
- `MSFT 15Min: 1560 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:45:00+00:00`
- `MSFT 5Min: 4676 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:55:00+00:00`
- `SPY 15Min: 1560 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:45:00+00:00`
- `SPY 1Hour: 3477 bars 2024-09-12 13:30:00+00:00 → 2026-09-11 19:30:00+00:00`
- `SPY 5Min: 4680 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:55:00+00:00`

# Per-book detail

- Generated (UTC): 2026-09-13T13:17:56.926182Z
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

## sample-entries

- Period: 2024-09-12T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560, 'SPY:1Hour': 3477}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 128  (by symbol: {'SPY': 34, 'AAPL': 50, 'MSFT': 44})
- Pattern hits in those signals: {'hammer': 34, 'bullish_engulfing': 94}
- Trades: 63  (by symbol: {'SPY': 24, 'MSFT': 19, 'AAPL': 20})
- Wins / losses / scratch: 27 / 36 / 0
- Win rate: 42.86%
- Total P&L: $810.57 (0.811% of starting equity)
- Avg win: $89.70
- Avg loss: $-44.76
- Max drawdown: $498.00 (0.49%)
- Ending equity: $100,810.57
- Exit reasons: {'take': 25, 'stop': 36, 'eod': 2}

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
- Signals come from the live evaluate_rule path (same pattern/SMA/RSI/volume detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Stop/take are computed from the signal-bar close (same as live bracket_prices).
- One open lot per symbol (no pyramiding). A second signal while flat-in-symbol is skipped.
- ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.
