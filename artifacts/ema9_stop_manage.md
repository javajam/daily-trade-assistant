# ema9_trend 10-share: fixed 1% vs lock-+1% vs trail-1% (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:52:26.615664Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry (all): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70 — the older noon day-trade entry, **not** the EMA9×SMA20 pair-cross
- Session gates (all): `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York
- No break-even. **No percent take-profit** on any book (exits = stop variant or `session_flatten`)
- A. **Fixed 1%** (`stop_mode: entry_pct`): `config/ema9_trend_bracket_nobe_fixed1.example.yaml`
- B. **Lock to +1%** (`stop_mode: lock_plus`): `config/ema9_trend_bracket_nobe_lock1.example.yaml`
- C. **Trail 1%** (`stop_mode: trail`): `config/ema9_trend_bracket_nobe_trail1.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_fixed1.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_trail1.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_stop_manage.json --report artifacts/ema9_stop_manage.md`

**Stops are from the fill** (next-bar open), not the signal-bar close. `percent` still uses the signal close; these three modes do not.

| Mode | Initial stop | After |
| --- | --- | --- |
| A `entry_pct` | fill × 0.99 | never moves |
| B `lock_plus` | fill × 0.99 | first **trade/touch** of fill × 1.01 (long: bar high ≥ trigger) moves the stop to fill × 1.01 and leaves it. Locked stop is live from the **next** bar; same-bar pullback after the tag still uses the initial 1% stop. Later hit → `lock_stop` |
| C `trail` | fill × 0.99 (peak starts at fill) | stop = `peak_price_since_entry × 0.99`, ratchets up only. Peak updates from each bar high **after** the current-stop check, so a new trail is live from the next bar. Any stop hit → `trail_stop` |

**Book A (fixed 1%)**: **51 trades, 56.86%, $364.05**, max DD $186.89. Same 154 EMA9-cross signals; **61 skipped as `entry_cutoff`**, 42 already-in-position. Exits: **session_flatten 37 ($861.20)**, **stop 14 ($-497.15)**.

**Book B (lock +1%)**: **51 trades, 60.78%, $301.49**, max DD $130.76. Same 154 signals; **75 skipped as `entry_cutoff`**, 28 already-in-position. **20 armed the +1% lock; all 20 then exited as `lock_stop` ($684.73)**. Remaining exits: **stop 13 ($-459.59)**, **session_flatten 18 ($76.35)**. Locking cuts the runners that A rode to flatten (e.g. MSFT 6/26 A +$101.25 flatten vs B +$29.75 lock; MSFT 7/15 A +$81.50 vs B +$21.30). That raises win rate (more +1% scratches count as wins) but **loses $62.56 vs A**.

**Book C (trail 1%)**: **51 trades, 54.90%, $253.40**, max DD $117.41. Same 154 signals; **75 skipped as `entry_cutoff`**, 28 already-in-position. **49 of 51 ratcheted** the trail above the fill stop. Exits: **trail_stop 37 ($2.85)**, **session_flatten 14 ($250.55)**. The trail is almost a scratch on stop hits; flatten still pays. Tightest drawdown of the three, **$110.65 behind A**.

Same 51-trade count on all three: lock/trail free the symbol earlier, so leftover signals land in the noon cutoff instead of already-in-position (A 61/42 vs B/C 75/28).

## Side-by-side (10-share, full Yahoo window)

| | A. Fixed 1% | B. Lock +1% | C. Trail 1% |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 42, entry_cutoff 61 | already_in_position 28, entry_cutoff 75 | already_in_position 28, entry_cutoff 75 |
| Trades | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 29 / 22 / 0 | 31 / 20 / 0 | 28 / 23 / 0 |
| **Win rate** | **56.86%** | **60.78%** | **54.90%** |
| **Total P&L** | **$364.05 (0.364%)** | **$301.49 (0.301%)** | **$253.40 (0.253%)** |
| Avg win | $32.72 | $27.05 | $24.32 |
| Avg loss | -$26.58 | -$26.85 | -$18.59 |
| **Max drawdown** | **$186.89 (0.19%)** | **$130.76 (0.13%)** | **$117.41 (0.12%)** |
| Ending equity | $100,364.05 | $100,301.49 | $100,253.40 |
| Exit mix | stop 14, session_flatten 37 | stop 13, lock_stop 20, session_flatten 18 | trail_stop 37, session_flatten 14 |
| Lock armed / trail ratcheted | 0 / 0 | 20 / 0 | 0 / 49 |
| **Exit P&L** | session_flatten $861.20 (37); stop -$497.15 (14) | session_flatten $76.35 (18); stop -$459.59 (13); lock_stop $684.73 (20) | session_flatten $250.55 (14); trail_stop $2.85 (37) |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window. 10 shares, $0 friction.

### Book A trades (fixed 1%, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 11:00 ET @ 371.80 | stop | -$37.56 |
| 2 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 15:45 ET @ 297.09 | stop | -$30.01 |
| 3 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 11:45 ET @ 297.47 | stop | -$30.05 |
| 4 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | -$8.40 |
| 5 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 13:30 ET @ 371.05 | stop | -$37.48 |
| 6 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 12:30 ET @ 275.43 | stop | -$27.82 |
| 7 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 16:00 ET @ 371.36 | session_flatten | $101.25 |
| 8 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 16:00 ET @ 281.63 | session_flatten | -$1.90 |
| 9 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 16:00 ET @ 289.09 | session_flatten | $58.20 |
| 10 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 11 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 12 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 13 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 16:00 ET @ 390.98 | session_flatten | $15.10 |
| 14 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 16:00 ET @ 395.62 | session_flatten | $81.50 |
| 15 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 16:00 ET @ 333.27 | session_flatten | $52.65 |
| 16 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 16:00 ET @ 401.12 | session_flatten | $51.00 |
| 17 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 10:15 ET @ 329.21 | stop | -$33.25 |
| 18 | AAPL | 10 | 2026-07-17 10:45 ET @ 333.07 | 2026-07-17 13:15 ET @ 329.74 | stop | -$33.31 |
| 19 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 16:00 ET @ 402.51 | session_flatten | $81.50 |
| 20 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 16:00 ET @ 327.59 | session_flatten | $15.20 |
| 21 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 386.07 | stop | -$39.00 |
| 22 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 09:45 ET @ 382.68 | stop | -$38.65 |
| 23 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 24 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 16:00 ET @ 393.47 | session_flatten | -$10.30 |
| 25 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 301.76 | stop | -$30.48 |
| 26 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 455.37 | stop | -$46.00 |
| 27 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $70.95 |
| 28 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.30 |
| 29 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 |
| 30 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $20.70 |
| 31 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $65.90 |
| 32 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $11.60 |
| 33 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $7.75 |
| 34 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | -$10.75 |
| 35 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 36 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | -$30.60 |
| 37 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 38 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $51.88 |
| 39 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $18.30 |
| 40 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.26 | stop | -$31.74 |
| 41 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $13.50 |
| 42 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | -$8.00 |
| 43 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $32.35 |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 16:00 ET @ 319.64 | session_flatten | $25.52 |
| 46 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 12:00 ET @ 495.17 | stop | -$50.02 |
| 47 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | -$4.65 |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 16:00 ET @ 328.21 | session_flatten | $17.40 |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:30 ET @ 314.68 | stop | -$31.79 |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | -$13.10 |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |

### Book B trades (lock +1%, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 10:00 ET @ 379.32 | lock_stop | $37.56 |
| 2 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 15:45 ET @ 297.09 | stop | -$30.01 |
| 3 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 11:45 ET @ 297.47 | stop | -$30.05 |
| 4 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | -$8.40 |
| 5 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 13:30 ET @ 371.05 | stop | -$37.48 |
| 6 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 10:30 ET @ 364.21 | lock_stop | $29.75 |
| 7 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 12:30 ET @ 275.43 | stop | -$27.82 |
| 8 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 16:00 ET @ 281.63 | session_flatten | -$1.90 |
| 9 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 10:45 ET @ 286.01 | lock_stop | $27.40 |
| 10 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 11 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 12 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 13 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 13:30 ET @ 392.78 | lock_stop | $33.10 |
| 14 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 10:15 ET @ 389.60 | lock_stop | $21.30 |
| 15 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 10:30 ET @ 328.67 | lock_stop | $6.65 |
| 16 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 12:15 ET @ 399.98 | lock_stop | $39.60 |
| 17 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 10:15 ET @ 329.21 | stop | -$33.25 |
| 18 | AAPL | 10 | 2026-07-17 10:45 ET @ 333.07 | 2026-07-17 13:15 ET @ 329.74 | stop | -$33.31 |
| 19 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 12:00 ET @ 398.30 | lock_stop | $39.44 |
| 20 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 12:30 ET @ 329.33 | lock_stop | $32.61 |
| 21 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 386.07 | stop | -$39.00 |
| 22 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 09:45 ET @ 382.68 | stop | -$38.65 |
| 23 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 12:00 ET @ 398.44 | lock_stop | $39.45 |
| 24 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 25 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 301.76 | stop | -$30.48 |
| 26 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 455.37 | stop | -$46.00 |
| 27 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 12:15 ET @ 462.40 | lock_stop | $45.78 |
| 28 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 11:00 ET @ 495.99 | lock_stop | $49.11 |
| 29 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 13:30 ET @ 309.32 | lock_stop | $30.63 |
| 30 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $20.70 |
| 31 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 10:45 ET @ 496.51 | lock_stop | $32.40 |
| 32 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $11.60 |
| 33 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 11:00 ET @ 510.25 | lock_stop | $50.52 |
| 34 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | -$10.75 |
| 35 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 36 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | -$30.60 |
| 37 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 38 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 12:30 ET @ 487.48 | lock_stop | $48.26 |
| 39 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 13:00 ET @ 314.81 | lock_stop | $31.17 |
| 40 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.26 | stop | -$31.74 |
| 41 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $13.50 |
| 42 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | -$8.00 |
| 43 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 10:30 ET @ 312.83 | lock_stop | $25.85 |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 11:15 ET @ 320.26 | lock_stop | $31.71 |
| 46 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 12:00 ET @ 495.17 | stop | -$50.02 |
| 47 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | -$4.65 |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 10:45 ET @ 329.71 | lock_stop | $32.45 |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:30 ET @ 314.68 | stop | -$31.79 |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | -$13.10 |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |

### Book C trades (trail 1%, 10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 10:15 ET @ 377.81 | trail_stop | $22.54 |
| 2 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 15:45 ET @ 298.42 | trail_stop | -$16.79 |
| 3 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 11:15 ET @ 373.45 | trail_stop | -$12.97 |
| 4 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 11:30 ET @ 298.62 | trail_stop | -$18.46 |
| 5 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 13:30 ET @ 371.84 | trail_stop | -$29.58 |
| 6 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 11:45 ET @ 277.67 | trail_stop | -$5.45 |
| 7 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 12:15 ET @ 367.80 | trail_stop | $65.70 |
| 8 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 12:45 ET @ 280.20 | trail_stop | -$16.16 |
| 9 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 15:00 ET @ 286.76 | trail_stop | $34.93 |
| 10 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 11 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 12 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 13 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 15:45 ET @ 389.70 | trail_stop | $2.34 |
| 14 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 11:00 ET @ 393.81 | trail_stop | $63.42 |
| 15 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 12:30 ET @ 328.96 | trail_stop | $9.52 |
| 16 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 12:30 ET @ 396.60 | trail_stop | $5.84 |
| 17 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 10:00 ET @ 331.63 | trail_stop | -$9.10 |
| 18 | AAPL | 10 | 2026-07-17 10:45 ET @ 333.07 | 2026-07-17 12:15 ET @ 331.52 | trail_stop | -$15.49 |
| 19 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 16:00 ET @ 402.51 | session_flatten | $81.50 |
| 20 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 16:00 ET @ 327.59 | session_flatten | $15.20 |
| 21 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 387.86 | trail_stop | -$21.03 |
| 22 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 09:45 ET @ 382.68 | trail_stop | -$38.65 |
| 23 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 12:15 ET @ 396.32 | trail_stop | $18.17 |
| 24 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 25 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 301.76 | trail_stop | -$30.48 |
| 26 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:15 ET @ 458.23 | trail_stop | -$17.39 |
| 27 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 14:00 ET @ 460.15 | trail_stop | $23.27 |
| 28 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 13:00 ET @ 494.45 | trail_stop | $33.66 |
| 29 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.30 |
| 30 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 11:30 ET @ 308.59 | trail_stop | -$2.59 |
| 31 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 12:45 ET @ 493.98 | trail_stop | $7.10 |
| 32 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 12:15 ET @ 311.66 | trail_stop | -$4.78 |
| 33 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 11:00 ET @ 508.59 | trail_stop | $33.94 |
| 34 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 11:15 ET @ 496.33 | trail_stop | -$15.58 |
| 35 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 15:15 ET @ 495.01 | trail_stop | -$34.70 |
| 36 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 37 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 38 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 12:00 ET @ 316.09 | trail_stop | $43.95 |
| 39 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 13:00 ET @ 484.40 | trail_stop | $17.47 |
| 40 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:15 ET @ 314.60 | trail_stop | -$28.28 |
| 41 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 14:00 ET @ 481.50 | trail_stop | -$5.04 |
| 42 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.23 | trail_stop | -$9.24 |
| 43 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |
| 44 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $32.35 |
| 45 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 15:00 ET @ 319.15 | trail_stop | $20.58 |
| 46 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 12:00 ET @ 495.27 | trail_stop | -$49.03 |
| 47 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | -$4.65 |
| 48 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 13:30 ET @ 327.50 | trail_stop | $10.32 |
| 49 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:30 ET @ 314.95 | trail_stop | -$29.11 |
| 50 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | -$13.10 |
| 51 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |

## Pick (10-share)

On this tape **A makes the most money**. B wins more often and cuts DD by locking +1% runners that would have gone further (or given it back). C has the smallest DD and the weakest P&L because the 1% trail stops out most of the day's extension. If the goal is dollars on 10 shares, take **fixed 1%**. If the goal is a higher win rate / tighter DD and you will accept giving back the flatten runners, take **lock +1%**. Trail-1% is the defensive book.
