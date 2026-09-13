# ema9_trend 10-share: 12:00 book vs one-bar break-even (AAPL/MSFT)

- Generated (UTC): 2026-09-13T20:20:05.118265Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares; initial stop 1.5%; take 3.0%; cooldown 60 minutes
- Without BE (prior 12:00 book): `config/ema9_trend_bracket_nobe.example.yaml`
- With BE: `config/ema9_trend_bracket.example.yaml` (`breakeven_after_bars: 1`, `breakeven_requires_valid: true`, `breakeven_valid: above_ema`)
- Replay: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe.example.yaml --compare-config config/ema9_trend_bracket.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_breakeven.json --report artifacts/ema9_breakeven.md`

**Break-even rule:** after the fill, wait for **one complete 15m bar after the entry bar**. At that close, if the long is still valid (`close > EMA(9)`), move the stop to **entry** and leave it there. If not valid, keep the 1.5% stop (do not retry). Same-bar stop/take on the evaluation bar still use the original stop. A later hit of the armed entry stop is `breakeven_stop`.

The no-BE book reproduced the prior 12:00 / 15:55 tape exactly: **50 trades, 62.00%, $453.00**, max DD $207.70. Same 154 EMA9-cross signals; **55 skipped as `entry_cutoff`**, 49 skipped as already-in-position. **41 of 50 closed trades were `session_flatten`** (8 stop, 1 take). BE armed 0 / BE stop hit 0.

Adding the one-bar BE rule on the same tape: **51 trades, 31.37%, $349.70**, max DD $199.67. Same 154 signals; **83 skipped as `entry_cutoff`**, 20 skipped as already-in-position (BE exits free the symbol earlier, so more of the remaining signals land in the noon cutoff instead of already-in-position). **40 of 51 trades armed break-even; 27 exited as `breakeven_stop`**. Remaining exits: session_flatten 19, stop 4, take 1. Win rate falls because 20 scratches are not wins; P&L is $103.31 below the prior 12:00 book and max DD is $8.04 tighter.

## Side-by-side

| | 12:00 / 15:55 (no BE) | 12:00 / 15:55 + BE after 1 bar |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 49, **entry_cutoff 55** | already_in_position 20, **entry_cutoff 83** |
| Trades | 50 (AAPL 22, MSFT 28) | 51 (AAPL 22, MSFT 29) |
| Wins / losses / scratch | 31 / 18 / 1 | 16 / 15 / 20 |
| **Win rate** | **62.00%** | **31.37%** |
| **Total P&L** | **$453.00** (0.453%) | **$349.70** (0.350%) |
| Avg win | $32.19 | $42.87 |
| Avg loss | $-30.27 | $-22.41 |
| **Max drawdown** | **$207.70** (0.21%) | **$199.67** (0.20%) |
| Ending equity | $100,453.00 | $100,349.70 |
| Exit mix | **session_flatten 41**, stop 8, take 1 | **breakeven_stop 27**, session_flatten 19, stop 4, take 1 |
| **BE armed** | **0** | **40** |
| **BE stop hit** | **0** | **27** |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window.

### Without BE (prior 12:00 book)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 10:45 ET @ 373.36 | stop | $-21.96 |
| 2 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 16:00 ET @ 296.79 | session_flatten | $-33.05 |
| 3 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 15:30 ET @ 296.00 | stop | $-44.68 |
| 4 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | $-8.40 |
| 5 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 14:45 ET @ 369.18 | stop | $-56.22 |
| 6 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 15:45 ET @ 372.07 | take | $108.37 |
| 7 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 16:00 ET @ 281.20 | session_flatten | $29.90 |
| 8 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 16:00 ET @ 281.63 | session_flatten | $-1.90 |
| 9 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 16:00 ET @ 289.09 | session_flatten | $58.20 |
| 10 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 11 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 12 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 13 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 16:00 ET @ 390.98 | session_flatten | $15.10 |
| 14 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 16:00 ET @ 395.62 | session_flatten | $81.50 |
| 15 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 16:00 ET @ 333.27 | session_flatten | $52.65 |
| 16 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 16:00 ET @ 401.12 | session_flatten | $51.00 |
| 17 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 16:00 ET @ 333.74 | session_flatten | $12.00 |
| 18 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 16:00 ET @ 402.51 | session_flatten | $81.50 |
| 19 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 16:00 ET @ 327.59 | session_flatten | $15.20 |
| 20 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 384.43 | stop | $-55.39 |
| 21 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 16:00 ET @ 381.74 | session_flatten | $-48.08 |
| 22 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 23 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 16:00 ET @ 393.47 | session_flatten | $-10.30 |
| 24 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 304.81 | stop | $0.00 |
| 25 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 453.07 | stop | $-69.00 |
| 26 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $70.95 |
| 27 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.30 |
| 28 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 |
| 29 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $20.70 |
| 30 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $65.90 |
| 31 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $11.60 |
| 32 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $7.75 |
| 33 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-10.75 |
| 34 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 35 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-30.60 |
| 36 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 37 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $51.88 |
| 38 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $18.30 |
| 39 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 16:00 ET @ 312.66 | stop | $-47.71 |
| 40 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $13.50 |
| 41 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-8.00 |
| 42 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |
| 43 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $32.35 |
| 44 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 16:00 ET @ 319.64 | session_flatten | $25.52 |
| 45 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | $-4.65 |
| 46 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 16:00 ET @ 496.81 | session_flatten | $-33.60 |
| 47 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 16:00 ET @ 328.21 | session_flatten | $17.40 |
| 48 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:45 ET @ 313.11 | stop | $-47.53 |
| 49 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | $-13.10 |
| 50 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |

### With BE (default 12:00 book)

| # | Symbol | Qty | Entry | Exit | Reason | P&L | BE armed |
| ---: | --- | ---: | --- | --- | --- | ---: | --- |
| 1 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 10:30 ET @ 375.56 | breakeven_stop | $0.00 | Y |
| 2 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 12:45 ET @ 300.10 | breakeven_stop | $0.00 | Y |
| 3 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 10:30 ET @ 299.43 | breakeven_stop | $-10.40 | Y |
| 4 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 10:30 ET @ 374.27 | breakeven_stop | $-4.75 | Y |
| 5 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 11:15 ET @ 374.80 | breakeven_stop | $0.00 | Y |
| 6 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 11:45 ET @ 278.21 | breakeven_stop | $0.00 | Y |
| 7 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 15:45 ET @ 372.07 | take | $108.37 | Y |
| 8 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 12:00 ET @ 281.82 | breakeven_stop | $0.00 | Y |
| 9 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 12:15 ET @ 370.55 | breakeven_stop | $-0.70 | Y |
| 10 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 16:00 ET @ 289.09 | session_flatten | $58.20 | Y |
| 11 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 | Y |
| 12 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 13:45 ET @ 383.99 | breakeven_stop | $0.00 | Y |
| 13 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 16:00 ET @ 390.98 | session_flatten | $15.10 | Y |
| 14 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 16:00 ET @ 395.62 | session_flatten | $81.50 | Y |
| 15 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 10:15 ET @ 328.01 | breakeven_stop | $0.00 | Y |
| 16 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 12:30 ET @ 396.02 | breakeven_stop | $0.00 | Y |
| 17 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 16:00 ET @ 333.74 | session_flatten | $12.00 |  |
| 18 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 16:00 ET @ 402.51 | session_flatten | $81.50 | Y |
| 19 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 16:00 ET @ 327.59 | session_flatten | $15.20 | Y |
| 20 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 384.43 | stop | $-55.39 |  |
| 21 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 10:15 ET @ 381.23 | breakeven_stop | $-53.18 | Y |
| 22 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 10:30 ET @ 394.27 | breakeven_stop | $-2.30 | Y |
| 23 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 12:00 ET @ 339.09 | breakeven_stop | $0.00 | Y |
| 24 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 304.81 | stop | $0.00 |  |
| 25 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 453.07 | stop | $-69.00 |  |
| 26 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $70.95 | Y |
| 27 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 12:30 ET @ 306.26 | breakeven_stop | $0.00 | Y |
| 28 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 | Y |
| 29 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 11:30 ET @ 308.85 | breakeven_stop | $0.00 | Y |
| 30 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $65.90 | Y |
| 31 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 12:00 ET @ 312.14 | breakeven_stop | $0.00 | Y |
| 32 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 14:15 ET @ 505.20 | breakeven_stop | $0.00 | Y |
| 33 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 10:45 ET @ 497.89 | breakeven_stop | $0.00 | Y |
| 34 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 11:00 ET @ 498.48 | breakeven_stop | $0.00 | Y |
| 35 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 12:30 ET @ 305.16 | breakeven_stop | $0.00 | Y |
| 36 | MSFT | 10 | 2026-08-14 11:45 ET @ 498.82 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-34.00 |  |
| 37 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 11:00 ET @ 481.14 | breakeven_stop | $-2.42 | Y |
| 38 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $51.88 | Y |
| 39 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $18.30 |  |
| 40 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 11:45 ET @ 317.23 | breakeven_stop | $-2.00 | Y |
| 41 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 10:45 ET @ 482.00 | breakeven_stop | $0.00 | Y |
| 42 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 14:45 ET @ 311.15 | breakeven_stop | $0.00 | Y |
| 43 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |  |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $32.35 | Y |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 10:15 ET @ 316.77 | breakeven_stop | $-3.18 | Y |
| 46 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | $-4.65 |  |
| 47 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 16:00 ET @ 496.81 | session_flatten | $-33.60 |  |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 16:00 ET @ 328.21 | session_flatten | $17.40 | Y |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:45 ET @ 313.11 | stop | $-47.53 |  |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | $-13.10 |  |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 12:00 ET @ 494.49 | breakeven_stop | $0.00 | Y |
