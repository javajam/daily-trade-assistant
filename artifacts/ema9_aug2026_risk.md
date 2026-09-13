# ema9_trend — August 2026 1% risk book (entry_cutoff 15:15, flatten_by 15:55)

- Window: 2026-08-01 → 2026-08-31 America/New_York (inclusive). Tape is the same Yahoo 15m AAPL/MSFT series as the full-window book (2026-06-17 → 2026-09-11); bars before August are warmup only.
- Entry: 15m bullish EMA(9) cross + close > SMA20 + RSI14 < 70
- Exit: fixed 1.5% stop / 3.0% take, plus session gates
- Session: `entry_cutoff: "15:15"`, `flatten_by: "15:55"` America/New_York. 15m force-flat at the **15:45 ET bar close** (prints 16:00 ET).
- Sizing: `size: { type: risk_pct, equity_risk: 0.01, stop_pct: 1.5 }` on $100,000 start
- Universe: AAPL + MSFT
- Config: `config/ema9_trend_risk.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --output artifacts/ema9_aug2026_risk.json --report artifacts/ema9_aug2026_risk.md`

**WITH 15:15 / 15:55 session gates:** **19 trades, 68.42%, $2,595.50**, max DD $1,668.34. Exits: **18 `session_flatten` time-exits**, 1 stop, 0 take. Signals 58; skips `entry_cutoff` 4, already_in_position 19, insufficient_cash 16.

Prior 13:00 / 15:55 August book on the same window/sizing (recorded in the previous session-gates writeup): **17 trades, 70.59%, $3,022.49**, max DD $1,663.57, 16 `session_flatten`, 17 `entry_cutoff` skips.

Prior overnight August book (gates off): **7 trades, 57.14%, $5,502.59**, max DD $3,282.83.

### Monthly (August 2026)

- Month: 2026-08
- Session days: 21
- Trades: 19  (wins 13 / losses 6)
- Win rate: 68.42%
- Total P&L: $2,595.50 (2.60% of starting equity)
- Ending equity: $102,595.50
- Best day (realized): 2026-08-19 $1,115.42 (1 trade)
- Worst day (realized): 2026-08-20 $-1,021.05 (1 trade)

## Closed trades (August, cutoff 15:15)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | AAPL | 217 | 2026-08-03 12:30 ET @ 306.35 | 2026-08-03 16:00 ET @ 303.27 | session_flatten | $-668.36 |
| 2 | MSFT | 134 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $233.16 |
| 3 | AAPL | 214 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $442.98 |
| 4 | MSFT | 135 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $889.65 |
| 5 | AAPL | 215 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $249.37 |
| 6 | MSFT | 133 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $103.07 |
| 7 | MSFT | 134 | 2026-08-11 14:45 ET @ 502.92 | 2026-08-11 16:00 ET @ 503.81 | session_flatten | $119.26 |
| 8 | MSFT | 135 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-145.13 |
| 9 | MSFT | 135 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-413.10 |
| 10 | MSFT | 139 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $76.10 |
| 11 | AAPL | 215 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $1,115.42 |
| 12 | AAPL | 214 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 16:00 ET @ 312.66 | stop | $-1,021.05 |
| 13 | MSFT | 139 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $187.65 |
| 14 | AAPL | 216 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-172.80 |
| 15 | MSFT | 137 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $371.95 |
| 16 | AAPL | 218 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $705.23 |
| 17 | MSFT | 135 | 2026-08-27 12:15 ET @ 501.08 | 2026-08-27 16:00 ET @ 504.88 | session_flatten | $513.00 |
| 18 | AAPL | 217 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 16:00 ET @ 319.64 | session_flatten | $553.78 |
| 19 | MSFT | 134 | 2026-08-31 13:00 ET @ 511.39 | 2026-08-31 16:00 ET @ 507.32 | session_flatten | $-544.71 |

# Per-book detail

- Generated (UTC): 2026-09-13T17:26:23.354493Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m combined (cutoff 15:15, flat 15:55)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 58  (by symbol: {'AAPL': 26, 'MSFT': 32})
- Pattern hits in those signals: {'ema_cross': 58}
- Trades: 19  (by symbol: {'AAPL': 8, 'MSFT': 11})
- Wins / losses / scratch: 13 / 6 / 0
- Win rate: 68.42%
- Total P&L: $2,595.50 (2.595% of starting equity)
- Avg win: $427.74
- Avg loss: $-494.19
- Max drawdown: $1,668.34 (1.63%)
- Ending equity: $102,595.50
- Exit reasons: {'session_flatten': 18, 'stop': 1}
- Skip reasons: {'already_in_position': 19, 'entry_cutoff': 4, 'insufficient_cash': 16}
- Session gates (America/New_York): entry_cutoff=15:15 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid on that bar still win if they hit first. Set entry_cutoff / flatten_by to null to restore overnight holds.
- Session gates (America/New_York): entry_cutoff=15:15 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 4 signal(s) skipped as entry_cutoff (15:15 America/New_York; fill would be at/after the cutoff).
- 18 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 19  (wins 13 / losses 6)
- Win rate: 68.42%
- Total P&L: $2,595.50 (2.60% of starting equity)
- Ending equity: $102,595.50
- Best day (realized): 2026-08-19 $1,115.42 (1 trades)
- Worst day (realized): 2026-08-20 $-1,021.05 (1 trades)

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 5 | 80.00% | $1,146.80 | 1.15% | $101,146.80 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 4 | 50.00% | $-335.89 | -0.34% | $100,810.91 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 4 | 75.00% | $358.12 | 0.36% | $101,169.03 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 5 | 80.00% | $1,971.18 | 1.97% | $103,140.21 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 1 | 0.00% | $-544.71 | -0.54% | $102,595.50 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 1 | 0 | 1 | $-668.36 | -0.67% | $99,331.64 |
| 2026-08-04 | 1 | 1 | 0 | $233.16 | 0.23% | $99,564.80 |
| 2026-08-05 | 1 | 1 | 0 | $442.98 | 0.44% | $100,007.78 |
| 2026-08-06 | 1 | 1 | 0 | $889.65 | 0.89% | $100,897.43 |
| 2026-08-07 | 1 | 1 | 0 | $249.37 | 0.25% | $101,146.80 |
| 2026-08-10 | 1 | 1 | 0 | $103.07 | 0.10% | $101,249.88 |
| 2026-08-11 | 1 | 1 | 0 | $119.26 | 0.12% | $101,369.14 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $101,369.14 |
| 2026-08-13 | 1 | 0 | 1 | $-145.13 | -0.15% | $101,224.01 |
| 2026-08-14 | 1 | 0 | 1 | $-413.10 | -0.41% | $100,810.91 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $100,810.91 |
| 2026-08-18 | 1 | 1 | 0 | $76.10 | 0.08% | $100,887.01 |
| 2026-08-19 | 1 | 1 | 0 | $1,115.42 | 1.12% | $102,002.43 |
| 2026-08-20 | 1 | 0 | 1 | $-1,021.05 | -1.02% | $100,981.38 |
| 2026-08-21 | 1 | 1 | 0 | $187.65 | 0.19% | $101,169.03 |
| 2026-08-24 | 1 | 0 | 1 | $-172.80 | -0.17% | $100,996.23 |
| 2026-08-25 | 1 | 1 | 0 | $371.95 | 0.37% | $101,368.19 |
| 2026-08-26 | 1 | 1 | 0 | $705.23 | 0.71% | $102,073.42 |
| 2026-08-27 | 1 | 1 | 0 | $513.00 | 0.51% | $102,586.43 |
| 2026-08-28 | 1 | 1 | 0 | $553.78 | 0.55% | $103,140.21 |
| 2026-08-31 | 1 | 0 | 1 | $-544.71 | -0.54% | $102,595.50 |


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
- Session gates (America/New_York): entry_cutoff=15:15 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid on that bar still win if they hit first. Set entry_cutoff / flatten_by to null to restore overnight holds.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (shares = floor((equity_risk * equity) / ((stop_pct/100) * price))).
