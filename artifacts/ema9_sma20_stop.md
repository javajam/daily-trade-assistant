# ema9_trend 10-share: noon 1.0/2.0 percent vs SMA20 stop (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:33:00Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry (all): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70 — the older noon day-trade entry, **not** the EMA9×SMA20 pair-cross
- Session gates (all): `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York
- No break-even
- A. **stop 1.0% / take 2.0%** (`stop_mode: percent`): `config/ema9_trend_bracket_nobe_12.example.yaml`
- B. **SMA20 stop + 2% take** (`stop_mode: sma20`): `config/ema9_trend_bracket_sma20.example.yaml`
- C. **SMA20 stop, no % take**: `config/ema9_trend_bracket_sma20_notake.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_12.example.yaml --compare-config config/ema9_trend_bracket_sma20.example.yaml --compare-config config/ema9_trend_bracket_sma20_notake.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_sma20_stop.json --report artifacts/ema9_sma20_stop.md`

**Stop (v1).** `stop_mode: sma20` rests a **fixed** protective stop at the SMA(20) of the **signal bar** (not trailed to later SMA prints). Longs skip when that SMA is at/above the signal close (`sma20_above_entry`) or when the next-bar fill is at/below it (no percent fallback). `stop_mode: percent` keeps `stop_loss_pct` from the signal-bar close.

**Fill convention:** entries fill at the next bar open. Percent take (when set) is from the signal-bar close. Same-bar stop still wins over take. `flatten_by` 15:55 force-flats at the 15:45 ET 15m bar close (`session_flatten`) unless stop/take already hit.

**Book A reproduced** the prior noon 1.0/2.0 tape exactly: **51 trades, 56.86%, $462.18**, max DD $149.36. Same 154 EMA9-cross signals; **62 skipped as `entry_cutoff`**, 41 skipped as already-in-position. Exits: **session_flatten 30 ($309.62)**, **stop 13 ($-373.02)**, **take 8 ($525.59)**.

**Book B (SMA20 + 2% take)** on the same tape: **51 trades, 39.22%, $270.16**, max DD $138.22. Same 154 signals; **79 skipped as `entry_cutoff`**, 21 skipped as already-in-position; **0 `sma20_above_entry`** (entry already requires close > SMA20); **3 accepted signals skipped at fill** because the next-bar open was at/below SMA20. Exits: **stop 28 ($-354.61)**, **session_flatten 17 ($239.14)**, **take 6 ($385.63)**.

**Book C (SMA20, no take)** on the same tape: **51 trades, 39.22%, $284.39**, max DD $141.52. Same 154 signals; **76 skipped as `entry_cutoff`**, 24 skipped as already-in-position; same 3 fill skips. Exits: **stop 28 ($-354.61)**, **session_flatten 23 ($638.99)**. The six 2% takes on B become session-flatten (or stay winners) on C; net **+$14.23** vs B because the two extra flatten winners (MSFT 6/26 $101.25 vs $72.25 take; AAPL 8/19 $51.88 vs $62.47 take, plus AAPL 6/30 $58.20 vs $56.65 and the other takes that ride further) more than replace the early 2% exits.

SMA20 is a **tighter** stop than 1%. On the 28 B/C stop-outs, mean adverse distance was **$1.27 / 0.33%** of entry (range 0.03%–1.14%). That cuts average loss vs A ($-13.52 vs $-24.23) but fires **15 extra stops**, many of them scratches that A rode to a noon flatten. Win rate falls from 56.86% to 39.22%. Tighter stops also free the symbol earlier, so leftover signals land in the noon cutoff instead of already-in-position (A 62/41 vs B 79/21). Book A still makes more money (**$192.02** vs B, **$177.79** vs C) because the 1% stop lets more winners reach flatten/take.

## Side-by-side

| | A. 1.0% / 2.0% (percent) | B. SMA20 / 2.0% | C. SMA20 stop only |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 41, entry_cutoff 62 | already_in_position 21, entry_cutoff 79 | already_in_position 24, entry_cutoff 76 |
| Fill skips | — | 3 (SMA20 ≥ next open) | 3 (SMA20 ≥ next open) |
| Trades | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 29 / 21 / 1 | 20 / 31 / 0 | 20 / 31 / 0 |
| **Win rate** | **56.86%** | **39.22%** | **39.22%** |
| **Total P&L** | **$462.18** (0.462%) | **$270.16** (0.270%) | **$284.39** (0.284%) |
| Avg win | $33.48 | $34.46 | $35.17 |
| Avg loss | $-24.23 | $-13.52 | $-13.52 |
| **Max drawdown** | **$149.36** (0.15%) | **$138.22** (0.14%) | **$141.52** (0.14%) |
| Ending equity | $100,462.18 | $100,270.16 | $100,284.39 |
| Exit mix | **session_flatten 30**, stop 13, take 8 | **stop 28**, session_flatten 17, take 6 | **stop 28**, session_flatten 23 |
| **Exit P&L** | session_flatten **$309.62**; stop $-373.02; take **$525.59** | session_flatten $239.14; stop $-354.61; take $385.63 | session_flatten **$638.99**; stop $-354.61 |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window. 10 shares, $0 friction.

### Book A trades (1.0/2.0 percent, 10 shares)

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

### Book B trades (SMA20 + 2% take, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 14:15 ET @ 298.71 | stop | $-13.85 |
| 2 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 10:00 ET @ 299.48 | stop | $-9.89 |
| 3 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | $-8.40 |
| 4 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 10:45 ET @ 373.61 | stop | $-11.92 |
| 5 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 10:30 ET @ 276.96 | stop | $-12.54 |
| 6 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 11:00 ET @ 368.46 | take | $72.25 |
| 7 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 11:15 ET @ 280.75 | stop | $-10.75 |
| 8 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 11:45 ET @ 288.94 | take | $56.65 |
| 9 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 10 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 11 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 12 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 16:00 ET @ 390.98 | session_flatten | $15.10 |
| 13 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 10:30 ET @ 395.27 | take | $77.95 |
| 14 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 09:45 ET @ 327.08 | stop | $-9.27 |
| 15 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 12:30 ET @ 395.71 | stop | $-3.09 |
| 16 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 09:45 ET @ 331.80 | stop | $-7.39 |
| 17 | AAPL | 10 | 2026-07-17 10:45 ET @ 333.07 | 2026-07-17 11:00 ET @ 332.07 | stop | $-10.03 |
| 18 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 12:45 ET @ 402.21 | take | $78.52 |
| 19 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 10:30 ET @ 325.71 | stop | $-3.65 |
| 20 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 09:45 ET @ 388.79 | stop | $-11.76 |
| 21 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 16:00 ET @ 381.74 | session_flatten | $-48.08 |
| 22 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 10:00 ET @ 391.88 | stop | $-26.24 |
| 23 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 24 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 454.71 | stop | $-52.59 |
| 25 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $70.95 |
| 26 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.30 |
| 27 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 |
| 28 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 11:30 ET @ 308.76 | stop | $-0.86 |
| 29 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $65.90 |
| 30 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 12:15 ET @ 311.70 | stop | $-4.45 |
| 31 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $7.75 |
| 32 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 14:30 ET @ 493.32 | stop | $-45.65 |
| 33 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 13:45 ET @ 495.55 | stop | $-29.28 |
| 34 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 35 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 10:45 ET @ 480.72 | stop | $-6.60 |
| 36 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 10:15 ET @ 482.17 | stop | $-4.77 |
| 37 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 11:00 ET @ 317.94 | take | $62.47 |
| 38 | MSFT | 10 | 2026-08-19 11:00 ET @ 484.23 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $2.50 |
| 39 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 14:15 ET @ 315.93 | stop | $-15.03 |
| 40 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 10:00 ET @ 481.65 | stop | $-3.52 |
| 41 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-8.00 |
| 42 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 10:00 ET @ 488.58 | stop | $-2.08 |
| 43 | MSFT | 10 | 2026-08-25 11:00 ET @ 489.27 | 2026-08-25 14:15 ET @ 488.22 | stop | $-10.54 |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 09:45 ET @ 309.46 | stop | $-7.87 |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 11:15 ET @ 320.87 | take | $37.78 |
| 46 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 10:00 ET @ 325.35 | stop | $-1.05 |
| 47 | AAPL | 10 | 2026-09-02 11:30 ET @ 326.53 | 2026-09-02 11:45 ET @ 325.07 | stop | $-14.59 |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 16:00 ET @ 328.21 | session_flatten | $17.40 |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:15 ET @ 316.14 | stop | $-17.17 |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 11:15 ET @ 492.26 | stop | $-8.21 |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |

### Book C trades (SMA20 stop, no take, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 14:15 ET @ 298.71 | stop | $-13.85 |
| 2 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 10:00 ET @ 299.48 | stop | $-9.89 |
| 3 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | $-8.40 |
| 4 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 10:45 ET @ 373.61 | stop | $-11.92 |
| 5 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 10:30 ET @ 276.96 | stop | $-12.54 |
| 6 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 16:00 ET @ 371.36 | session_flatten | $101.25 |
| 7 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 11:15 ET @ 280.75 | stop | $-10.75 |
| 8 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 16:00 ET @ 289.09 | session_flatten | $58.20 |
| 9 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 10 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 11 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 12 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 16:00 ET @ 390.98 | session_flatten | $15.10 |
| 13 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 16:00 ET @ 395.62 | session_flatten | $81.50 |
| 14 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 09:45 ET @ 327.08 | stop | $-9.27 |
| 15 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 12:30 ET @ 395.71 | stop | $-3.09 |
| 16 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 09:45 ET @ 331.80 | stop | $-7.39 |
| 17 | AAPL | 10 | 2026-07-17 10:45 ET @ 333.07 | 2026-07-17 11:00 ET @ 332.07 | stop | $-10.03 |
| 18 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 16:00 ET @ 402.51 | session_flatten | $81.50 |
| 19 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 10:30 ET @ 325.71 | stop | $-3.65 |
| 20 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 09:45 ET @ 388.79 | stop | $-11.76 |
| 21 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 16:00 ET @ 381.74 | session_flatten | $-48.08 |
| 22 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 10:00 ET @ 391.88 | stop | $-26.24 |
| 23 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 24 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 454.71 | stop | $-52.59 |
| 25 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $70.95 |
| 26 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.30 |
| 27 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 |
| 28 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 11:30 ET @ 308.76 | stop | $-0.86 |
| 29 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $65.90 |
| 30 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 12:15 ET @ 311.70 | stop | $-4.45 |
| 31 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $7.75 |
| 32 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 14:30 ET @ 493.32 | stop | $-45.65 |
| 33 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 13:45 ET @ 495.55 | stop | $-29.28 |
| 34 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 35 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 10:45 ET @ 480.72 | stop | $-6.60 |
| 36 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 10:15 ET @ 482.17 | stop | $-4.77 |
| 37 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $51.88 |
| 38 | MSFT | 10 | 2026-08-19 11:00 ET @ 484.23 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $2.50 |
| 39 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 14:15 ET @ 315.93 | stop | $-15.03 |
| 40 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 10:00 ET @ 481.65 | stop | $-3.52 |
| 41 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-8.00 |
| 42 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 10:00 ET @ 488.58 | stop | $-2.08 |
| 43 | MSFT | 10 | 2026-08-25 11:00 ET @ 489.27 | 2026-08-25 14:15 ET @ 488.22 | stop | $-10.54 |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 09:45 ET @ 309.46 | stop | $-7.87 |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 16:00 ET @ 319.64 | session_flatten | $25.52 |
| 46 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 10:00 ET @ 325.35 | stop | $-1.05 |
| 47 | AAPL | 10 | 2026-09-02 11:30 ET @ 326.53 | 2026-09-02 11:45 ET @ 325.07 | stop | $-14.59 |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 16:00 ET @ 328.21 | session_flatten | $17.40 |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:15 ET @ 316.14 | stop | $-17.17 |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 11:15 ET @ 492.26 | stop | $-8.21 |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |
