# Rule backtest results

- Generated (UTC): 2026-09-13T16:47:15.091947Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m ema9_trend

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 58  (by symbol: {'AAPL': 26, 'MSFT': 32})
- Pattern hits in those signals: {'ema_cross': 58}
- Trades: 11  (by symbol: {'AAPL': 5, 'MSFT': 6})
- Wins / losses / scratch: 6 / 5 / 0
- Win rate: 54.55%
- Total P&L: $430.47 (0.430% of starting equity)
- Avg win: $119.52
- Avg loss: $-57.34
- Max drawdown: $251.10 (0.25%)
- Ending equity: $100,430.47
- Exit reasons: {'take': 6, 'stop': 4, 'eod': 1}

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 11  (wins 6 / losses 5)
- Win rate: 54.55%
- Total P&L: $430.47 (0.43% of starting equity)
- Ending equity: $100,430.47
- Best day (realized): 2026-08-28 $242.40 (2 trades)
- Worst day (realized): 2026-08-17 $-76.68 (1 trades)

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 2 | 100.00% | $238.97 | 0.24% | $100,260.37 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 2 | 0.00% | $-121.65 | -0.12% | $100,100.58 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 3 | 33.33% | $-32.84 | -0.03% | $100,088.46 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 3 | 100.00% | $386.63 | 0.39% | $100,471.12 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 1 | 0.00% | $-40.65 | -0.04% | $100,430.47 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $99,944.70 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,058.10 |
| 2026-08-05 | 0 | 0 | 0 | $0.00 | 0.00% | $100,019.80 |
| 2026-08-06 | 1 | 1 | 0 | $92.01 | 0.09% | $100,203.01 |
| 2026-08-07 | 1 | 1 | 0 | $146.96 | 0.15% | $100,260.37 |
| 2026-08-10 | 1 | 0 | 1 | $-46.70 | -0.05% | $100,200.02 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $100,178.42 |
| 2026-08-12 | 1 | 0 | 1 | $-74.94 | -0.07% | $100,117.33 |
| 2026-08-13 | 0 | 0 | 0 | $0.00 | 0.00% | $100,106.58 |
| 2026-08-14 | 0 | 0 | 0 | $0.00 | 0.00% | $100,100.58 |
| 2026-08-17 | 1 | 0 | 1 | $-76.68 | -0.08% | $100,045.95 |
| 2026-08-18 | 0 | 0 | 0 | $0.00 | 0.00% | $100,096.53 |
| 2026-08-19 | 1 | 1 | 0 | $91.55 | 0.09% | $100,163.17 |
| 2026-08-20 | 1 | 0 | 1 | $-47.71 | -0.05% | $100,084.45 |
| 2026-08-21 | 0 | 0 | 0 | $0.00 | 0.00% | $100,088.46 |
| 2026-08-24 | 0 | 0 | 0 | $0.00 | 0.00% | $100,137.66 |
| 2026-08-25 | 0 | 0 | 0 | $0.00 | 0.00% | $100,174.76 |
| 2026-08-26 | 1 | 1 | 0 | $144.23 | 0.14% | $100,271.12 |
| 2026-08-27 | 0 | 0 | 0 | $0.00 | 0.00% | $100,369.17 |
| 2026-08-28 | 2 | 2 | 0 | $242.40 | 0.24% | $100,471.12 |
| 2026-08-31 | 1 | 0 | 1 | $-40.65 | -0.04% | $100,430.47 |


## Assumptions

- CLI trade window 2026-08-01T04:00:00+00:00 → 2026-09-01T04:00:00+00:00 (America/New_York date bounds; prior bars used only for warmup).
- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Stop/take are computed from the signal-bar close (same as live bracket_prices; action.exit: fixed_bracket, default). Set action.exit: ema_invalid to hold until a signal-timeframe close is on the wrong side of EMA (long: close < EMA; exit at that close).
- If stop and take (or EMA-invalidation) both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open. EMA-invalidation fills at the invalidating close.
- One open lot per symbol (no pyramiding). A second signal while that symbol is already open is skipped.
- A second symbol may open at the same time when cash covers its sized notional; otherwise the later signal is skipped (insufficient_cash).
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (shares = floor((equity_risk * equity) / ((stop_pct/100) * price))).
