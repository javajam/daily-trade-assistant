# ema9_trend — August 2026 1% risk with SOXL (entry_cutoff 12:00, flatten_by 15:55)

- Window: 2026-08-01 → 2026-08-31 America/New_York (inclusive). Same Yahoo 15m tape; bars before August are warmup only.
- Entry / exit / sizing: same locked 15m EMA9 + SMA20 + RSI14 < 70, 1.5/3.0 brackets, `risk_pct` 1% of equity at the 1.5% stop
- Session: `entry_cutoff: "12:00"`, `flatten_by: "15:55"` America/New_York
- Config: `config/ema9_trend_risk_soxl.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_soxl.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --breakout SOXL --output artifacts/ema9_aug2026_risk_soxl.json --report artifacts/ema9_aug2026_risk_soxl.md`

AAPL+MSFT-only August 1% risk (12:00): **15 trades, 73.33%, $3,194.05**, max DD $1,676.30, 14 `session_flatten`, 24 `entry_cutoff` skips.

**AAPL+MSFT+SOXL (shared book):** **24 trades, 45.83%, $-4,120.21**, max DD $5,533.16. Signals 94 (AAPL 26, MSFT 32, SOXL 36). Skips `entry_cutoff` 44, already_in_position 16, insufficient_cash 10. Exits: **14 `session_flatten`**, 9 stop, 1 take. Wins / losses / scratch: 11 / 11 / 2.

**Isolated SOXL (1% risk):** **15 trades, 13.33%, $-6,805.96**, max DD $6,805.96. Signals 36. Skips `entry_cutoff` 18, already_in_position 3. Exits: 12 stop, 2 take, **1 `session_flatten`**. Wins / losses / scratch: 2 / 11 / 2.

SOXL 1% risk on this August tape is a large loser (most names size to hundreds of shares at ~$110–$140). Adding it to the AAPL+MSFT book turns August from **+$3,194.05** to **$-4,120.21**. Isolated SOXL max DD equals its full loss ($6,805.96) — the curve never recovers.

## Side-by-side (August 2026)

| | AAPL+MSFT 1% risk | AAPL+MSFT+SOXL 1% risk | Isolated SOXL 1% risk |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 94 (AAPL 26, MSFT 32, SOXL 36) | 36 (SOXL 36) |
| Skips | already_in_position 15, **entry_cutoff 24**, insufficient_cash 4 | already_in_position 16, **entry_cutoff 44**, insufficient_cash 10 | already_in_position 3, **entry_cutoff 18** |
| Trades | 15 (AAPL 7, MSFT 8) | 24 (AAPL 7, MSFT 8, SOXL 9) | 15 (SOXL 15) |
| Wins / losses / scratch | 11 / 4 / 0 | 11 / 11 / 2 | 2 / 11 / 2 |
| **Win rate** | **73.33%** | **45.83%** | **13.33%** |
| **Total P&L** | **$3,194.05** (3.194%) | **$-4,120.21** (−4.120%) | **$-6,805.96** (−6.806%) |
| Avg win | $450.53 | $432.03 | $1,764.19 |
| Avg loss | $-440.45 | $-806.59 | $-939.49 |
| **Max drawdown** | **$1,676.30** (1.63%) | **$5,533.16** (5.50%) | **$6,805.96** (6.81%) |
| Ending equity | $103,194.05 | $95,879.79 | $93,194.04 |
| Exit mix | **session_flatten 14**, stop 1 | **session_flatten 14**, stop 9, take 1 | stop 12, take 2, **session_flatten 1** |

### Monthly — AAPL+MSFT+SOXL (August 2026)

- Month: 2026-08
- Session days: 21
- Trades: 24  (wins 11 / losses 11)
- Win rate: 50.00%
- Total P&L: $-4,120.21 (−4.12% of starting equity)
- Ending equity: $95,879.79
- Best day (realized): 2026-08-19 $1,063.54 (1 trades)
- Worst day (realized): 2026-08-11 $-1,947.18 (2 trades)

### Monthly — isolated SOXL (August 2026)

- Month: 2026-08
- Session days: 21
- Trades: 15  (wins 2 / losses 11)
- Win rate: 15.38%
- Total P&L: $-6,805.96 (−6.81% of starting equity)
- Ending equity: $93,194.04
- Best day (realized): 2026-08-13 $1,901.27 (1 trades)
- Worst day (realized): 2026-08-10 $-2,419.28 (2 trades)

### Closed trades — AAPL+MSFT+SOXL (August, cutoff 12:00)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | SOXL | 573 | 2026-08-03 11:00 ET @ 116.23 | 2026-08-03 11:15 ET @ 114.54 | stop | $-970.78 |
| 2 | MSFT | 134 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $233.16 |
| 3 | AAPL | 214 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $442.98 |
| 4 | MSFT | 134 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $883.06 |
| 5 | SOXL | 470 | 2026-08-07 09:45 ET @ 142.43 | 2026-08-07 10:00 ET @ 140.34 | stop | $-983.29 |
| 6 | AAPL | 212 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $245.89 |
| 7 | SOXL | 474 | 2026-08-10 09:30 ET @ 141.15 | 2026-08-10 09:45 ET @ 138.16 | stop | $-1,420.29 |
| 8 | MSFT | 129 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $99.97 |
| 9 | SOXL | 485 | 2026-08-11 09:45 ET @ 135.14 | 2026-08-11 10:00 ET @ 133.19 | stop | $-947.32 |
| 10 | SOXL | 483 | 2026-08-11 11:00 ET @ 134.62 | 2026-08-11 12:15 ET @ 132.55 | stop | $-999.87 |
| 11 | MSFT | 129 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-138.68 |
| 12 | MSFT | 128 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-391.68 |
| 13 | MSFT | 133 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $72.82 |
| 14 | AAPL | 205 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $1,063.54 |
| 15 | SOXL | 530 | 2026-08-20 09:45 ET @ 122.04 | 2026-08-20 10:00 ET @ 120.25 | stop | $-949.34 |
| 16 | AAPL | 202 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 16:00 ET @ 312.66 | stop | $-963.80 |
| 17 | MSFT | 131 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $176.85 |
| 18 | SOXL | 527 | 2026-08-24 09:30 ET @ 115.00 | 2026-08-24 09:45 ET @ 115.00 | stop | $0.00 |
| 19 | AAPL | 204 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-163.20 |
| 20 | MSFT | 129 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $350.23 |
| 21 | AAPL | 205 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $663.18 |
| 22 | SOXL | 550 | 2026-08-27 09:30 ET @ 123.40 | 2026-08-27 09:45 ET @ 123.40 | take | $0.00 |
| 23 | AAPL | 204 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 16:00 ET @ 319.64 | session_flatten | $520.61 |
| 24 | SOXL | 573 | 2026-08-31 09:45 ET @ 112.49 | 2026-08-31 12:00 ET @ 110.84 | stop | $-944.27 |

### Closed trades — isolated SOXL (August, cutoff 12:00)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | SOXL | 573 | 2026-08-03 11:00 ET @ 116.23 | 2026-08-03 11:15 ET @ 114.54 | stop | $-970.78 |
| 2 | SOXL | 479 | 2026-08-06 10:15 ET @ 137.70 | 2026-08-06 11:00 ET @ 135.74 | stop | $-937.47 |
| 3 | SOXL | 458 | 2026-08-07 09:45 ET @ 142.43 | 2026-08-07 10:00 ET @ 140.34 | stop | $-958.19 |
| 4 | SOXL | 473 | 2026-08-07 11:15 ET @ 136.82 | 2026-08-07 16:00 ET @ 140.26 | session_flatten | $1,627.11 |
| 5 | SOXL | 469 | 2026-08-10 09:30 ET @ 141.15 | 2026-08-10 09:45 ET @ 138.16 | stop | $-1,405.31 |
| 6 | SOXL | 463 | 2026-08-10 10:15 ET @ 140.09 | 2026-08-10 10:30 ET @ 137.90 | stop | $-1,013.97 |
| 7 | SOXL | 475 | 2026-08-11 09:45 ET @ 135.14 | 2026-08-11 10:00 ET @ 133.19 | stop | $-927.78 |
| 8 | SOXL | 472 | 2026-08-11 11:00 ET @ 134.62 | 2026-08-11 12:15 ET @ 132.55 | stop | $-977.09 |
| 9 | SOXL | 432 | 2026-08-13 09:45 ET @ 145.51 | 2026-08-13 10:15 ET @ 149.91 | take | $1,901.27 |
| 10 | SOXL | 526 | 2026-08-20 09:45 ET @ 122.04 | 2026-08-20 10:00 ET @ 120.25 | stop | $-942.17 |
| 11 | SOXL | 527 | 2026-08-24 09:30 ET @ 115.00 | 2026-08-24 09:45 ET @ 115.00 | stop | $0.00 |
| 12 | SOXL | 541 | 2026-08-25 09:45 ET @ 117.54 | 2026-08-25 10:15 ET @ 115.77 | stop | $-959.17 |
| 13 | SOXL | 543 | 2026-08-26 09:30 ET @ 114.70 | 2026-08-26 10:15 ET @ 114.10 | stop | $-324.50 |
| 14 | SOXL | 537 | 2026-08-27 09:30 ET @ 123.40 | 2026-08-27 09:45 ET @ 123.40 | take | $0.00 |
| 15 | SOXL | 557 | 2026-08-31 09:45 ET @ 112.49 | 2026-08-31 12:00 ET @ 110.84 | stop | $-917.91 |

# Per-book detail

- Generated (UTC): 2026-09-13T19:53:58.986754Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m ema9_trend (cutoff 12:00, flat 15:55)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560, 'SOXL:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 94  (by symbol: {'SOXL': 36, 'AAPL': 26, 'MSFT': 32})
- Pattern hits in those signals: {'ema_cross': 94}
- Trades: 24  (by symbol: {'SOXL': 9, 'MSFT': 8, 'AAPL': 7})
- Wins / losses / scratch: 11 / 11 / 2
- Win rate: 45.83%
- Total P&L: $-4,120.21 (-4.120% of starting equity)
- Avg win: $432.03
- Avg loss: $-806.59
- Max drawdown: $5,533.16 (5.50%)
- Ending equity: $95,879.79
- Exit reasons: {'stop': 9, 'session_flatten': 14, 'take': 1}
- Skip reasons: {'entry_cutoff': 44, 'insufficient_cash': 10, 'already_in_position': 16}
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid on that bar still win if they hit first. Set entry_cutoff / flatten_by to null to restore overnight holds.
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 44 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 14 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 24  (wins 11 / losses 11)
- Win rate: 50.00%
- Total P&L: $-4,120.21 (-4.12% of starting equity)
- Ending equity: $95,879.79
- Best day (realized): 2026-08-19 $1,063.54 (1 trades)
- Worst day (realized): 2026-08-11 $-1,947.18 (2 trades)

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 6 | 66.67% | $-148.97 | -0.15% | $99,851.03 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 6 | 16.67% | $-3,797.86 | -3.80% | $96,053.17 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 5 | 60.00% | $-599.92 | -0.60% | $95,453.25 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 6 | 75.00% | $1,370.82 | 1.37% | $96,824.07 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 1 | 0.00% | $-944.27 | -0.94% | $95,879.79 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 1 | 0 | 1 | $-970.78 | -0.97% | $99,029.22 |
| 2026-08-04 | 1 | 1 | 0 | $233.16 | 0.23% | $99,262.38 |
| 2026-08-05 | 1 | 1 | 0 | $442.98 | 0.44% | $99,705.37 |
| 2026-08-06 | 1 | 1 | 0 | $883.06 | 0.88% | $100,588.42 |
| 2026-08-07 | 2 | 1 | 1 | $-737.40 | -0.74% | $99,851.03 |
| 2026-08-10 | 2 | 1 | 1 | $-1,320.32 | -1.32% | $98,530.71 |
| 2026-08-11 | 2 | 0 | 2 | $-1,947.18 | -1.95% | $96,583.53 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $96,583.53 |
| 2026-08-13 | 1 | 0 | 1 | $-138.68 | -0.14% | $96,444.85 |
| 2026-08-14 | 1 | 0 | 1 | $-391.68 | -0.39% | $96,053.17 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $96,053.17 |
| 2026-08-18 | 1 | 1 | 0 | $72.82 | 0.07% | $96,125.98 |
| 2026-08-19 | 1 | 1 | 0 | $1,063.54 | 1.06% | $97,189.53 |
| 2026-08-20 | 2 | 0 | 2 | $-1,913.13 | -1.91% | $95,276.39 |
| 2026-08-21 | 1 | 1 | 0 | $176.85 | 0.18% | $95,453.25 |
| 2026-08-24 | 2 | 0 | 1 | $-163.20 | -0.16% | $95,290.05 |
| 2026-08-25 | 1 | 1 | 0 | $350.23 | 0.35% | $95,640.28 |
| 2026-08-26 | 1 | 1 | 0 | $663.18 | 0.66% | $96,303.46 |
| 2026-08-27 | 1 | 0 | 0 | $0.00 | 0.00% | $96,303.46 |
| 2026-08-28 | 1 | 1 | 0 | $520.61 | 0.52% | $96,824.07 |
| 2026-08-31 | 1 | 0 | 1 | $-944.27 | -0.94% | $95,879.79 |


## 15m ema9_trend SOXL (cutoff 12:00, flat 15:55)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'SOXL:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 36  (by symbol: {'SOXL': 36})
- Pattern hits in those signals: {'ema_cross': 36}
- Trades: 15  (by symbol: {'SOXL': 15})
- Wins / losses / scratch: 2 / 11 / 2
- Win rate: 13.33%
- Total P&L: $-6,805.96 (-6.806% of starting equity)
- Avg win: $1,764.19
- Avg loss: $-939.49
- Max drawdown: $6,805.96 (6.81%)
- Ending equity: $93,194.04
- Exit reasons: {'stop': 12, 'session_flatten': 1, 'take': 2}
- Skip reasons: {'entry_cutoff': 18, 'already_in_position': 3}
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid on that bar still win if they hit first. Set entry_cutoff / flatten_by to null to restore overnight holds.
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 18 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 1 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 15  (wins 2 / losses 11)
- Win rate: 15.38%
- Total P&L: $-6,805.96 (-6.81% of starting equity)
- Ending equity: $93,194.04
- Best day (realized): 2026-08-13 $1,901.27 (1 trades)
- Worst day (realized): 2026-08-10 $-2,419.28 (2 trades)

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 4 | 25.00% | $-1,239.33 | -1.24% | $98,760.67 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 5 | 20.00% | $-2,422.89 | -2.42% | $96,337.79 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 1 | 0.00% | $-942.17 | -0.94% | $95,395.62 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 4 | 0.00% | $-1,283.66 | -1.28% | $94,111.95 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 1 | 0.00% | $-917.91 | -0.92% | $93,194.04 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 1 | 0 | 1 | $-970.78 | -0.97% | $99,029.22 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $99,029.22 |
| 2026-08-05 | 0 | 0 | 0 | $0.00 | 0.00% | $99,029.22 |
| 2026-08-06 | 1 | 0 | 1 | $-937.47 | -0.94% | $98,091.75 |
| 2026-08-07 | 2 | 1 | 1 | $668.93 | 0.67% | $98,760.67 |
| 2026-08-10 | 2 | 0 | 2 | $-2,419.28 | -2.42% | $96,341.39 |
| 2026-08-11 | 2 | 0 | 2 | $-1,904.88 | -1.90% | $94,436.51 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $94,436.51 |
| 2026-08-13 | 1 | 1 | 0 | $1,901.27 | 1.90% | $96,337.79 |
| 2026-08-14 | 0 | 0 | 0 | $0.00 | 0.00% | $96,337.79 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $96,337.79 |
| 2026-08-18 | 0 | 0 | 0 | $0.00 | 0.00% | $96,337.79 |
| 2026-08-19 | 0 | 0 | 0 | $0.00 | 0.00% | $96,337.79 |
| 2026-08-20 | 1 | 0 | 1 | $-942.17 | -0.94% | $95,395.62 |
| 2026-08-21 | 0 | 0 | 0 | $0.00 | 0.00% | $95,395.62 |
| 2026-08-24 | 1 | 0 | 0 | $0.00 | 0.00% | $95,395.62 |
| 2026-08-25 | 1 | 0 | 1 | $-959.17 | -0.96% | $94,436.45 |
| 2026-08-26 | 1 | 0 | 1 | $-324.50 | -0.32% | $94,111.95 |
| 2026-08-27 | 1 | 0 | 0 | $0.00 | 0.00% | $94,111.95 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $94,111.95 |
| 2026-08-31 | 1 | 0 | 1 | $-917.91 | -0.92% | $93,194.04 |


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
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid on that bar still win if they hit first. Set entry_cutoff / flatten_by to null to restore overnight holds.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (shares = floor((equity_risk * equity) / ((stop_pct/100) * price))).
