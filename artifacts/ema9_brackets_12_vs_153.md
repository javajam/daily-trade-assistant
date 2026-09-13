# ema9_trend 10-share: noon price×EMA9 1.5/3.0 vs 1.0/2.0 (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:19:01.430360Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry (both): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70 — the older noon day-trade entry, **not** the EMA9×SMA20 pair-cross
- Session gates (both): `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York
- No break-even
- A. **stop 1.5% / take 3.0%** (control): `config/ema9_trend_bracket_nobe.example.yaml`
- B. **stop 1.0% / take 2.0%**: `config/ema9_trend_bracket_nobe_12.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe.example.yaml --compare-config config/ema9_trend_bracket_nobe_12.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_brackets_12_vs_153.json --report artifacts/ema9_brackets_12_vs_153.md`

**Fill convention:** entries fill at the next bar open. Stop/take are computed from the signal-bar close (`action.exit: fixed_bracket`). Same-bar stop still wins over take. `flatten_by` 15:55 force-flats at the 15:45 ET 15m bar close (`session_flatten`) unless stop/take already hit.

**Book A reproduced** the prior noon day-trade tape exactly: **50 trades, 62.00%, $453.00**, max DD $207.70. Same 154 EMA9-cross signals; **55 skipped as `entry_cutoff`**, 49 skipped as already-in-position. **41 of 50 closed trades were `session_flatten`** (8 stop, 1 take). Exit P&L: session_flatten $687.12, stop $-342.49, take $108.37.

**Book B (1.0/2.0)** on the same tape: **51 trades, 56.86%, $462.18**, max DD $149.36. Same 154 signals; **62 skipped as `entry_cutoff`**, 41 skipped as already-in-position. Tighter stops free the symbol earlier, so more leftover signals land in the noon cutoff instead of already-in-position, and one extra fill appears (AAPL 2026-07-17 10:45, after the 09:30 long stopped at 10:15). Exits: **session_flatten 30 ($309.62)**, **stop 13 ($-373.02)**, **take 8 ($525.59)**.

Tighter brackets beat the control by **$9.18** and cut max DD by **$58.35**. Win rate falls because eight 2% takes replace noon-flatten winners and five extra 1% stops replace wider 1.5% stops / flatten losers. The single 3% take on A (MSFT 2026-06-26, $108.37) becomes a 2% take on B ($72.25).

## Side-by-side

| | A. 1.5% / 3.0% (control) | B. 1.0% / 2.0% |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 49, entry_cutoff 55 | already_in_position 41, entry_cutoff 62 |
| Trades | 50 (AAPL 22, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 31 / 18 / 1 | 29 / 21 / 1 |
| **Win rate** | **62.00%** | **56.86%** |
| **Total P&L** | **$453.00** (0.453%) | **$462.18** (0.462%) |
| Avg win | $32.19 | $33.48 |
| Avg loss | $-30.27 | $-24.23 |
| **Max drawdown** | **$207.70** (0.21%) | **$149.36** (0.15%) |
| Ending equity | $100,453.00 | $100,462.18 |
| Exit mix | **session_flatten 41**, stop 8, take 1 | **session_flatten 30**, stop 13, take 8 |
| **Exit P&L** | session_flatten **$687.12**; stop $-342.49; take $108.37 | session_flatten **$309.62**; stop $-373.02; take **$525.59** |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window. 10 shares, $0 friction.

### Book A trades (1.5/3.0, 10 shares)

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

### Book B trades (1.0/2.0, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 09:45 ET @ 375.26 | stop | $-3.01 |
| 2 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 15:45 ET @ 297.11 | stop | $-29.86 |
| 3 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 11:45 ET @ 297.50 | stop | $-29.65 |
| 4 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | $-8.40 |
| 5 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 13:30 ET @ 371.05 | stop | $-37.48 |
| 6 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 11:00 ET @ 368.46 | take | $72.25 |
| 7 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 12:30 ET @ 275.41 | stop | $-28.02 |
| 8 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 16:00 ET @ 281.63 | session_flatten | $-1.90 |
| 9 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 11:45 ET @ 288.94 | take | $56.65 |
| 10 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 11 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 12 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 13 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 16:00 ET @ 390.98 | session_flatten | $15.10 |
| 14 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 10:30 ET @ 395.27 | take | $77.95 |
| 15 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 13:00 ET @ 403.90 | take | $78.80 |
| 16 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 15:15 ET @ 334.12 | take | $61.16 |
| 17 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 10:15 ET @ 329.94 | stop | $-26.03 |
| 18 | AAPL | 10 | 2026-07-17 10:45 ET @ 333.07 | 2026-07-17 13:15 ET @ 329.74 | stop | $-33.31 |
| 19 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 12:45 ET @ 402.21 | take | $78.52 |
| 20 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 16:00 ET @ 327.59 | session_flatten | $15.20 |
| 21 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 386.38 | stop | $-35.88 |
| 22 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 16:00 ET @ 381.74 | session_flatten | $-48.08 |
| 23 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 24 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 16:00 ET @ 393.47 | session_flatten | $-10.30 |
| 25 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 304.81 | stop | $0.00 |
| 26 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 455.37 | stop | $-46.00 |
| 27 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $70.95 |
| 28 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.30 |
| 29 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 |
| 30 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $20.70 |
| 31 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $65.90 |
| 32 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $11.60 |
| 33 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $7.75 |
| 34 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-10.75 |
| 35 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 36 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-30.60 |
| 37 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 38 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 11:00 ET @ 317.94 | take | $62.47 |
| 39 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $18.30 |
| 40 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.25 | stop | $-31.84 |
| 41 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $13.50 |
| 42 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-8.00 |
| 43 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $32.35 |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 11:15 ET @ 320.87 | take | $37.78 |
| 46 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 09:45 ET @ 496.14 | stop | $-40.32 |
| 47 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | $-4.65 |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 16:00 ET @ 328.21 | session_flatten | $17.40 |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:30 ET @ 314.70 | stop | $-31.64 |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | $-13.10 |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |
