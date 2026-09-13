# ema9_trend lock-+1% default: 15m vs 5m (AAPL/MSFT, 10-share)

- Generated (UTC): 2026-09-13T23:04:23.437850Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11 (15m last bar 19:45Z; 5m last bar 19:55Z)
- Bars: AAPL 15m 1560; MSFT 15m 1560; AAPL 5m 4677; MSFT 5m 4676
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry (both): signal-timeframe close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70
- Session gates (both): `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close; 5m flatten = 15:50 ET bar close)
- Stop (both): `stop_mode: lock_plus` — initial fill×0.99; first touch of fill×1.01 moves the stop to fill×1.01 and leaves it (live next bar). No take-profit.
- 15m: `config/ema9_trend.example.yaml` (same rules as prior Book B `config/ema9_trend_bracket_nobe_lock1.example.yaml`)
- 5m: `config/ema9_trend_5m.example.yaml` (identical rules; every indicator on 5m; cooldown still 60 wall-clock minutes)
- Replay: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_5m.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock_5m_vs_15m.json --report artifacts/ema9_lock_5m_vs_15m.md`

**15m reproduced** the prior lock-+1% Book B exactly: **51 trades, 60.78%, $301.49**, max DD $130.76. Same 154 EMA9-cross signals; **75 skipped as `entry_cutoff`**, 28 already-in-position. **20 armed the +1% lock; all 20 then exited as `lock_stop` ($684.73)**. Remaining exits: **stop 13 ($-459.59)**, **session_flatten 18 ($76.35)**.

**5m** (same stack, all indicators on 5m) took more trades: **91 trades, 51.65%, $238.31**, max DD $264.56. 328 signals; **121 skipped as `entry_cutoff`**, 116 already-in-position. **29 armed the +1% lock; 28 exited as `lock_stop` ($982.21)**. Remaining: **stop 20 ($-727.02)**, **session_flatten 43 ($-16.89)**. One armed trade flattened instead of hitting the locked stop.

5m fires more noon crosses (328 vs 154) and holds through the same 12:00 cutoff, so it books more session_flatten scratches. Lock still banks the +1% runners, but 5m also takes more initial 1% stops. Net: **5m is $63.18 behind 15m** and has a larger drawdown ($264.56 vs $130.76).

Yahoo's downloader requests `range=60d` for 5m/15m. This run returned the same calendar start as the prior 15m Book B (**2026-06-17**). Treat the documented ~60-day cap as the reliability limit.

## Side-by-side (10-share, full Yahoo window)

| | 15m lock +1% | 5m lock +1% |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 328 (MSFT 167, AAPL 161) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 116, entry_cutoff 121 |
| Trades | 51 (MSFT 28, AAPL 23) | 91 (MSFT 46, AAPL 45) |
| Wins / losses / scratch | 31 / 20 / 0 | 47 / 44 / 0 |
| **Win rate** | **60.78%** | **51.65%** |
| **Total P&L** | **$301.49 (0.301%)** | **$238.31 (0.238%)** |
| Avg win | $27.05 | $26.72 |
| Avg loss | $-26.85 | $-23.12 |
| **Max drawdown** | **$130.76 (0.13%)** | **$264.56 (0.26%)** |
| Ending equity | $100,301.49 | $100,238.31 |
| Exit mix | stop 13, lock_stop 20, session_flatten 18 | stop 20, lock_stop 28, session_flatten 43 |
| Lock armed | 20 | 29 |
| **Exit P&L** | lock_stop $684.73 (20); session_flatten $76.35 (18); stop $-459.59 (13) | lock_stop $982.21 (28); session_flatten $-16.89 (43); stop $-727.02 (20) |

Figures are engine totals, not annualized. One ~86-day Yahoo window. 10 shares, $0 friction.

### 15m trades (lock +1%, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 10:00 ET @ 379.32 | lock_stop | $37.56 |
| 2 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 15:45 ET @ 297.09 | stop | $-30.01 |
| 3 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 11:45 ET @ 297.47 | stop | $-30.05 |
| 4 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | $-8.40 |
| 5 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 13:30 ET @ 371.05 | stop | $-37.48 |
| 6 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 10:30 ET @ 364.21 | lock_stop | $29.75 |
| 7 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 12:30 ET @ 275.43 | stop | $-27.82 |
| 8 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 16:00 ET @ 281.63 | session_flatten | $-1.90 |
| 9 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 10:45 ET @ 286.01 | lock_stop | $27.40 |
| 10 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 11 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 12 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 13 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 13:30 ET @ 392.78 | lock_stop | $33.10 |
| 14 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 10:15 ET @ 389.60 | lock_stop | $21.30 |
| 15 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 10:30 ET @ 328.67 | lock_stop | $6.65 |
| 16 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 12:15 ET @ 399.98 | lock_stop | $39.60 |
| 17 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 10:15 ET @ 329.21 | stop | $-33.25 |
| 18 | AAPL | 10 | 2026-07-17 10:45 ET @ 333.07 | 2026-07-17 13:15 ET @ 329.74 | stop | $-33.31 |
| 19 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 12:00 ET @ 398.30 | lock_stop | $39.44 |
| 20 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 12:30 ET @ 329.33 | lock_stop | $32.61 |
| 21 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 386.07 | stop | $-39.00 |
| 22 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 09:45 ET @ 382.68 | stop | $-38.65 |
| 23 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 12:00 ET @ 398.44 | lock_stop | $39.45 |
| 24 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 25 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 301.76 | stop | $-30.48 |
| 26 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 455.37 | stop | $-46.00 |
| 27 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 12:15 ET @ 462.40 | lock_stop | $45.78 |
| 28 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 11:00 ET @ 495.99 | lock_stop | $49.11 |
| 29 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 13:30 ET @ 309.32 | lock_stop | $30.63 |
| 30 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $20.70 |
| 31 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 10:45 ET @ 496.51 | lock_stop | $32.40 |
| 32 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $11.60 |
| 33 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 11:00 ET @ 510.25 | lock_stop | $50.52 |
| 34 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-10.75 |
| 35 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 36 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-30.60 |
| 37 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 38 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 12:30 ET @ 487.48 | lock_stop | $48.26 |
| 39 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 13:00 ET @ 314.81 | lock_stop | $31.17 |
| 40 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.26 | stop | $-31.74 |
| 41 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $13.50 |
| 42 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-8.00 |
| 43 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 10:30 ET @ 312.83 | lock_stop | $25.85 |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 11:15 ET @ 320.26 | lock_stop | $31.71 |
| 46 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 12:00 ET @ 495.17 | stop | $-50.02 |
| 47 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | $-4.65 |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 10:45 ET @ 329.71 | lock_stop | $32.45 |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:30 ET @ 314.68 | stop | $-31.79 |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | $-13.10 |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |

### 5m trades (lock +1%, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 10 | 2026-06-18 10:35 ET @ 377.73 | 2026-06-18 15:55 ET @ 379.14 | session_flatten | $14.10 |
| 2 | MSFT | 10 | 2026-06-22 09:45 ET @ 379.51 | 2026-06-22 10:25 ET @ 375.72 | stop | $-37.95 |
| 3 | AAPL | 10 | 2026-06-22 11:55 ET @ 300.60 | 2026-06-22 15:35 ET @ 297.59 | stop | $-30.06 |
| 4 | MSFT | 10 | 2026-06-23 09:35 ET @ 371.42 | 2026-06-23 09:45 ET @ 375.13 | lock_stop | $37.14 |
| 5 | AAPL | 10 | 2026-06-23 09:40 ET @ 298.93 | 2026-06-23 15:20 ET @ 295.94 | stop | $-29.89 |
| 6 | MSFT | 10 | 2026-06-24 09:35 ET @ 375.75 | 2026-06-24 13:15 ET @ 371.99 | stop | $-37.57 |
| 7 | MSFT | 10 | 2026-06-26 09:35 ET @ 357.53 | 2026-06-26 09:45 ET @ 361.11 | lock_stop | $35.75 |
| 8 | AAPL | 10 | 2026-06-26 10:05 ET @ 277.11 | 2026-06-26 10:40 ET @ 279.69 | lock_stop | $25.80 |
| 9 | MSFT | 10 | 2026-06-26 11:25 ET @ 369.14 | 2026-06-26 15:50 ET @ 372.72 | lock_stop | $35.80 |
| 10 | AAPL | 10 | 2026-06-29 09:35 ET @ 286.26 | 2026-06-29 10:10 ET @ 283.40 | stop | $-28.63 |
| 11 | MSFT | 10 | 2026-06-29 09:35 ET @ 378.27 | 2026-06-29 10:35 ET @ 374.49 | stop | $-37.83 |
| 12 | MSFT | 10 | 2026-06-29 10:45 ET @ 376.47 | 2026-06-29 11:00 ET @ 372.71 | stop | $-37.65 |
| 13 | AAPL | 10 | 2026-06-29 11:30 ET @ 282.34 | 2026-06-29 15:55 ET @ 282.10 | session_flatten | $-2.42 |
| 14 | AAPL | 10 | 2026-06-30 09:35 ET @ 283.23 | 2026-06-30 10:25 ET @ 285.98 | lock_stop | $27.50 |
| 15 | AAPL | 10 | 2026-06-30 10:55 ET @ 286.58 | 2026-06-30 13:10 ET @ 289.45 | lock_stop | $28.66 |
| 16 | AAPL | 10 | 2026-07-01 11:50 ET @ 295.22 | 2026-07-01 15:55 ET @ 294.67 | session_flatten | $-5.50 |
| 17 | AAPL | 10 | 2026-07-02 11:40 ET @ 306.55 | 2026-07-02 15:55 ET @ 308.04 | session_flatten | $14.90 |
| 18 | MSFT | 10 | 2026-07-02 11:15 ET @ 389.19 | 2026-07-02 15:55 ET @ 390.62 | session_flatten | $14.30 |
| 19 | MSFT | 10 | 2026-07-07 10:45 ET @ 393.95 | 2026-07-07 15:15 ET @ 390.01 | stop | $-39.39 |
| 20 | AAPL | 10 | 2026-07-07 10:35 ET @ 312.33 | 2026-07-07 15:55 ET @ 311.51 | session_flatten | $-8.20 |
| 21 | AAPL | 10 | 2026-07-08 10:40 ET @ 310.26 | 2026-07-08 13:20 ET @ 313.36 | lock_stop | $31.03 |
| 22 | MSFT | 10 | 2026-07-10 10:20 ET @ 385.37 | 2026-07-10 11:10 ET @ 381.52 | stop | $-38.54 |
| 23 | MSFT | 10 | 2026-07-13 10:50 ET @ 388.41 | 2026-07-13 12:35 ET @ 392.29 | lock_stop | $38.84 |
| 24 | AAPL | 10 | 2026-07-14 11:00 ET @ 315.00 | 2026-07-14 15:55 ET @ 314.68 | session_flatten | $-3.20 |
| 25 | AAPL | 10 | 2026-07-15 11:10 ET @ 324.07 | 2026-07-15 12:20 ET @ 327.17 | lock_stop | $31.05 |
| 26 | MSFT | 10 | 2026-07-15 11:10 ET @ 395.22 | 2026-07-15 15:55 ET @ 394.77 | session_flatten | $-4.55 |
| 27 | AAPL | 10 | 2026-07-16 10:20 ET @ 329.17 | 2026-07-16 13:30 ET @ 332.43 | lock_stop | $32.60 |
| 28 | AAPL | 10 | 2026-07-20 11:55 ET @ 326.29 | 2026-07-20 15:40 ET @ 329.29 | lock_stop | $30.01 |
| 29 | AAPL | 10 | 2026-07-21 11:15 ET @ 327.55 | 2026-07-21 15:55 ET @ 327.82 | session_flatten | $2.71 |
| 30 | MSFT | 10 | 2026-07-21 10:30 ET @ 401.03 | 2026-07-21 15:55 ET @ 397.54 | session_flatten | $-34.90 |
| 31 | AAPL | 10 | 2026-07-23 11:15 ET @ 321.82 | 2026-07-23 15:55 ET @ 320.96 | session_flatten | $-8.60 |
| 32 | MSFT | 10 | 2026-07-24 09:55 ET @ 382.11 | 2026-07-24 11:35 ET @ 385.23 | lock_stop | $31.16 |
| 33 | AAPL | 10 | 2026-07-27 10:50 ET @ 337.39 | 2026-07-27 15:55 ET @ 337.12 | session_flatten | $-2.70 |
| 34 | MSFT | 10 | 2026-07-27 10:40 ET @ 390.66 | 2026-07-27 15:55 ET @ 389.39 | session_flatten | $-12.70 |
| 35 | MSFT | 10 | 2026-07-28 09:35 ET @ 396.16 | 2026-07-28 09:45 ET @ 398.47 | lock_stop | $23.10 |
| 36 | AAPL | 10 | 2026-07-28 10:20 ET @ 337.44 | 2026-07-28 15:55 ET @ 339.85 | session_flatten | $24.10 |
| 37 | MSFT | 10 | 2026-07-29 11:50 ET @ 394.97 | 2026-07-29 14:20 ET @ 397.60 | lock_stop | $26.30 |
| 38 | AAPL | 10 | 2026-07-29 10:35 ET @ 341.70 | 2026-07-29 15:55 ET @ 339.33 | session_flatten | $-23.70 |
| 39 | AAPL | 10 | 2026-07-30 11:10 ET @ 332.80 | 2026-07-30 15:55 ET @ 332.86 | session_flatten | $0.65 |
| 40 | MSFT | 10 | 2026-07-31 09:35 ET @ 458.46 | 2026-07-31 10:25 ET @ 453.88 | stop | $-45.85 |
| 41 | AAPL | 10 | 2026-07-31 11:20 ET @ 303.89 | 2026-07-31 11:50 ET @ 300.85 | stop | $-30.39 |
| 42 | AAPL | 10 | 2026-08-03 09:55 ET @ 308.27 | 2026-08-03 10:05 ET @ 305.19 | stop | $-30.83 |
| 43 | MSFT | 10 | 2026-08-03 10:40 ET @ 486.08 | 2026-08-03 14:40 ET @ 490.20 | lock_stop | $41.20 |
| 44 | AAPL | 10 | 2026-08-04 09:50 ET @ 304.72 | 2026-08-04 12:50 ET @ 307.74 | lock_stop | $30.20 |
| 45 | MSFT | 10 | 2026-08-04 11:50 ET @ 497.40 | 2026-08-04 15:55 ET @ 494.49 | session_flatten | $-29.10 |
| 46 | MSFT | 10 | 2026-08-05 11:15 ET @ 490.73 | 2026-08-05 14:10 ET @ 485.82 | stop | $-49.07 |
| 47 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 15:55 ET @ 310.93 | session_flatten | $20.80 |
| 48 | MSFT | 10 | 2026-08-06 09:40 ET @ 492.98 | 2026-08-06 10:30 ET @ 496.61 | lock_stop | $36.30 |
| 49 | AAPL | 10 | 2026-08-06 10:55 ET @ 313.33 | 2026-08-06 11:25 ET @ 310.19 | stop | $-31.33 |
| 50 | MSFT | 10 | 2026-08-06 11:30 ET @ 496.47 | 2026-08-06 15:55 ET @ 499.83 | session_flatten | $33.60 |
| 51 | AAPL | 10 | 2026-08-07 09:35 ET @ 313.23 | 2026-08-07 15:55 ET @ 313.23 | session_flatten | $0.05 |
| 52 | MSFT | 10 | 2026-08-07 10:20 ET @ 502.92 | 2026-08-07 15:55 ET @ 500.87 | session_flatten | $-20.50 |
| 53 | MSFT | 10 | 2026-08-10 09:35 ET @ 503.75 | 2026-08-10 10:15 ET @ 508.51 | lock_stop | $47.60 |
| 54 | AAPL | 10 | 2026-08-11 11:25 ET @ 306.59 | 2026-08-11 14:30 ET @ 303.52 | stop | $-30.66 |
| 55 | MSFT | 10 | 2026-08-11 11:10 ET @ 503.14 | 2026-08-11 15:55 ET @ 503.83 | session_flatten | $6.90 |
| 56 | AAPL | 10 | 2026-08-13 09:30 ET @ 304.26 | 2026-08-13 15:55 ET @ 305.21 | session_flatten | $9.52 |
| 57 | MSFT | 10 | 2026-08-13 09:35 ET @ 497.07 | 2026-08-13 15:55 ET @ 496.47 | session_flatten | $-5.95 |
| 58 | MSFT | 10 | 2026-08-14 09:40 ET @ 497.33 | 2026-08-14 15:55 ET @ 495.12 | session_flatten | $-22.18 |
| 59 | MSFT | 10 | 2026-08-17 09:30 ET @ 490.22 | 2026-08-17 09:55 ET @ 485.32 | stop | $-49.02 |
| 60 | AAPL | 10 | 2026-08-17 09:50 ET @ 306.03 | 2026-08-17 13:00 ET @ 302.97 | stop | $-30.60 |
| 61 | MSFT | 10 | 2026-08-17 11:15 ET @ 484.42 | 2026-08-17 13:00 ET @ 479.58 | stop | $-48.44 |
| 62 | AAPL | 10 | 2026-08-18 09:35 ET @ 306.21 | 2026-08-18 10:15 ET @ 309.27 | lock_stop | $30.62 |
| 63 | AAPL | 10 | 2026-08-18 11:30 ET @ 310.43 | 2026-08-18 15:55 ET @ 310.49 | session_flatten | $0.60 |
| 64 | MSFT | 10 | 2026-08-18 09:40 ET @ 482.78 | 2026-08-18 15:55 ET @ 481.85 | session_flatten | $-9.26 |
| 65 | MSFT | 10 | 2026-08-19 09:40 ET @ 483.39 | 2026-08-19 12:05 ET @ 488.22 | lock_stop | $48.34 |
| 66 | AAPL | 10 | 2026-08-19 09:35 ET @ 310.73 | 2026-08-19 15:55 ET @ 316.42 | session_flatten | $56.95 |
| 67 | AAPL | 10 | 2026-08-20 10:55 ET @ 317.05 | 2026-08-20 15:25 ET @ 313.88 | stop | $-31.70 |
| 68 | MSFT | 10 | 2026-08-21 09:35 ET @ 483.50 | 2026-08-21 15:55 ET @ 483.26 | session_flatten | $-2.40 |
| 69 | MSFT | 10 | 2026-08-24 09:35 ET @ 483.65 | 2026-08-24 11:05 ET @ 488.31 | lock_stop | $46.55 |
| 70 | AAPL | 10 | 2026-08-24 09:35 ET @ 310.49 | 2026-08-24 15:55 ET @ 310.83 | session_flatten | $3.40 |
| 71 | MSFT | 10 | 2026-08-24 11:10 ET @ 489.40 | 2026-08-24 15:55 ET @ 488.60 | session_flatten | $-7.99 |
| 72 | AAPL | 10 | 2026-08-25 09:35 ET @ 311.30 | 2026-08-25 15:55 ET @ 309.89 | session_flatten | $-14.10 |
| 73 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 15:55 ET @ 491.77 | session_flatten | $29.85 |
| 74 | AAPL | 10 | 2026-08-26 10:40 ET @ 312.11 | 2026-08-26 15:15 ET @ 315.12 | lock_stop | $30.05 |
| 75 | MSFT | 10 | 2026-08-26 10:45 ET @ 494.32 | 2026-08-26 15:55 ET @ 496.99 | session_flatten | $26.70 |
| 76 | MSFT | 10 | 2026-08-27 09:45 ET @ 495.60 | 2026-08-27 10:10 ET @ 500.30 | lock_stop | $47.00 |
| 77 | MSFT | 10 | 2026-08-28 10:20 ET @ 510.37 | 2026-08-28 11:10 ET @ 515.47 | lock_stop | $51.04 |
| 78 | MSFT | 10 | 2026-08-28 11:50 ET @ 514.88 | 2026-08-28 15:55 ET @ 513.44 | session_flatten | $-14.40 |
| 79 | MSFT | 10 | 2026-08-31 11:45 ET @ 511.10 | 2026-08-31 15:55 ET @ 508.46 | session_flatten | $-26.35 |
| 80 | AAPL | 10 | 2026-09-01 09:40 ET @ 318.17 | 2026-09-01 10:00 ET @ 321.35 | lock_stop | $31.82 |
| 81 | AAPL | 10 | 2026-09-01 11:20 ET @ 325.04 | 2026-09-01 15:55 ET @ 324.93 | session_flatten | $-1.10 |
| 82 | AAPL | 10 | 2026-09-02 09:35 ET @ 325.67 | 2026-09-02 15:55 ET @ 325.27 | session_flatten | $-3.96 |
| 83 | AAPL | 10 | 2026-09-03 09:35 ET @ 325.54 | 2026-09-03 10:40 ET @ 328.80 | lock_stop | $32.55 |
| 84 | MSFT | 10 | 2026-09-03 10:35 ET @ 510.51 | 2026-09-03 14:35 ET @ 514.74 | lock_stop | $42.30 |
| 85 | AAPL | 10 | 2026-09-03 11:05 ET @ 329.26 | 2026-09-03 15:55 ET @ 328.62 | session_flatten | $-6.40 |
| 86 | AAPL | 10 | 2026-09-08 11:25 ET @ 316.36 | 2026-09-08 15:55 ET @ 316.43 | session_flatten | $0.65 |
| 87 | MSFT | 10 | 2026-09-08 11:05 ET @ 492.75 | 2026-09-08 15:55 ET @ 493.63 | session_flatten | $8.80 |
| 88 | AAPL | 10 | 2026-09-09 09:50 ET @ 316.08 | 2026-09-09 11:05 ET @ 312.92 | stop | $-31.61 |
| 89 | MSFT | 10 | 2026-09-09 09:40 ET @ 493.71 | 2026-09-09 15:55 ET @ 491.69 | session_flatten | $-20.22 |
| 90 | AAPL | 10 | 2026-09-10 10:35 ET @ 319.08 | 2026-09-10 11:05 ET @ 322.27 | lock_stop | $31.91 |
| 91 | MSFT | 10 | 2026-09-10 11:20 ET @ 491.91 | 2026-09-10 15:55 ET @ 492.40 | session_flatten | $4.92 |

## Pick (10-share)

On this tape **15m makes more money with a tighter drawdown**. 5m finds more noon crosses and more lock tags, but the extra 1% stops and a slightly negative flatten mix leave it behind. If the goal is dollars on 10 shares with the default lock-+1% book, keep **15m**.
