# 9 EMA trend on 5-minute bars

Isolated Yahoo 5m books from `config/ema9_trend_5m.example.yaml`. Headline comparison vs 15m is `artifacts/ema9_5m_vs_15m.md`.

# Rule backtest results

- Generated (UTC): 2026-09-13T16:07:55.806271Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## ema9_trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 328  (by symbol: {'MSFT': 167, 'AAPL': 161})
- Pattern hits in those signals: {'ema_cross': 328}
- Trades: 56  (by symbol: {'MSFT': 25, 'AAPL': 31})
- Wins / losses / scratch: 27 / 29 / 0
- Win rate: 48.21%
- Total P&L: $1,305.23 (1.305% of starting equity)
- Avg win: $121.25
- Avg loss: $-67.88
- Max drawdown: $422.43 (0.42%)
- Ending equity: $101,305.23
- Exit reasons: {'stop': 28, 'take': 26, 'eod': 2}

## ema9_cross_raw

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 485  (by symbol: {'AAPL': 242, 'MSFT': 243})
- Pattern hits in those signals: {'ema_cross': 485}
- Trades: 63  (by symbol: {'AAPL': 32, 'MSFT': 31})
- Wins / losses / scratch: 29 / 34 / 0
- Win rate: 46.03%
- Total P&L: $996.80 (0.997% of starting equity)
- Avg win: $110.52
- Avg loss: $-64.95
- Max drawdown: $447.46 (0.45%)
- Ending equity: $100,996.80
- Exit reasons: {'stop': 33, 'take': 28, 'eod': 2}

## engulfing-with-trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 233  (by symbol: {'MSFT': 117, 'AAPL': 116})
- Pattern hits in those signals: {'bullish_engulfing': 233}
- Trades: 49  (by symbol: {'MSFT': 22, 'AAPL': 27})
- Wins / losses / scratch: 26 / 23 / 0
- Win rate: 53.06%
- Total P&L: $1,520.70 (1.521% of starting equity)
- Avg win: $122.82
- Avg loss: $-72.73
- Max drawdown: $434.06 (0.43%)
- Ending equity: $101,520.70
- Exit reasons: {'stop': 23, 'take': 25, 'eod': 1}

## sample-entries

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 1046  (by symbol: {'AAPL': 519, 'MSFT': 527})
- Pattern hits in those signals: {'ema_cross': 813, 'bullish_engulfing': 233}
- Trades: 57  (by symbol: {'AAPL': 26, 'MSFT': 31})
- Wins / losses / scratch: 27 / 30 / 0
- Win rate: 47.37%
- Total P&L: $928.25 (0.928% of starting equity)
- Avg win: $111.61
- Avg loss: $-69.50
- Max drawdown: $447.46 (0.45%)
- Ending equity: $100,928.25
- Exit reasons: {'stop': 29, 'take': 26, 'eod': 2}

## combined

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 1046  (by symbol: {'AAPL': 519, 'MSFT': 527})
- Pattern hits in those signals: {'ema_cross': 813, 'bullish_engulfing': 233}
- Trades: 57  (by symbol: {'AAPL': 26, 'MSFT': 31})
- Wins / losses / scratch: 27 / 30 / 0
- Win rate: 47.37%
- Total P&L: $928.25 (0.928% of starting equity)
- Avg win: $111.61
- Avg loss: $-69.50
- Max drawdown: $447.46 (0.45%)
- Ending equity: $100,928.25
- Exit reasons: {'stop': 29, 'take': 26, 'eod': 2}

## Assumptions

- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
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
