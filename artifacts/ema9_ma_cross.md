# ema9_trend 10-share: EMA9/SMA20 pair-cross vs prior noon price-cross (AAPL/MSFT)

- Generated (UTC): 2026-09-13T21:52:01.812090Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- New book: `config/ema9_trend_bracket.example.yaml` — EMA(9) cross **over** SMA(20) entry; flatten at **next bar open** when EMA(9) crosses **under** SMA(20); 1.5% stop; no take-profit; no break-even
- Prior noon book (old entry): `config/ema9_trend_bracket_nobe.example.yaml` — price crosses EMA(9) while close > SMA20 and RSI14 < 70; 1.5/3.0 brackets; no BE
- Session gates (both): `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York
- Replay: `python -m dta_bot backtest --config config/ema9_trend_bracket.example.yaml --compare-config config/ema9_trend_bracket_nobe.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_ma_cross.json --report artifacts/ema9_ma_cross.md`

**Fill convention:** entries and MA-cross exits fill at the next bar open. Same-bar 1.5% stop still wins. If the EMA/SMA cross-under print is also the flatten bar, `session_flatten` at that close wins.

The prior noon price-cross book **reproduced** the earlier 12:00 / 15:55 tape exactly: **50 trades, 62.00%, $453.00**, max DD $207.70. Same 154 EMA9-cross signals; **55 skipped as `entry_cutoff`**, 49 skipped as already-in-position. **41 of 50 closed trades were `session_flatten`** (8 stop, 1 take). Exit P&L: session_flatten $687.12, stop $-342.49, take $108.37.

The new EMA(9)/SMA(20) pair-cross book on the same tape: **44 trades, 54.55%, $349.33**, max DD $131.87. 98 pair-cross signals (AAPL 52, MSFT 46); **54 skipped as `entry_cutoff`**. Exits: **ma_cross 28 ($-84.50)**, **session_flatten 14 ($451.13)**, stop 2 ($-17.29). Almost all of the book’s P&L is the noon flatten, not the MA cross-under.

## Side-by-side

| | EMA9/SMA20 pair-cross (new) | Prior noon price-cross (old entry) |
| --- | ---: | ---: |
| Signals | 98 (AAPL 52, MSFT 46) | 154 (AAPL 77, MSFT 77) |
| Skips | **entry_cutoff 54** | already_in_position 49, **entry_cutoff 55** |
| Trades | 44 (AAPL 26, MSFT 18) | 50 (AAPL 22, MSFT 28) |
| Wins / losses / scratch | 24 / 20 / 0 | 31 / 18 / 1 |
| **Win rate** | **54.55%** | **62.00%** |
| **Total P&L** | **$349.33** (0.349%) | **$453.00** (0.453%) |
| Avg win | $28.27 | $32.19 |
| Avg loss | $-16.46 | $-30.27 |
| **Max drawdown** | **$131.87** (0.13%) | **$207.70** (0.21%) |
| Ending equity | $100,349.33 | $100,453.00 |
| Exit mix | **ma_cross 28**, session_flatten 14, stop 2 | **session_flatten 41**, stop 8, take 1 |
| **Exit P&L** | ma_cross **$-84.50**; session_flatten **$451.13**; stop $-17.29 | session_flatten **$687.12**; stop $-342.49; take $108.37 |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window.

### New pair-cross trades (10 shares)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | AAPL | 10 | 2026-06-18 10:15 ET @ 298.96 | 2026-06-18 14:00 ET @ 297.58 | ma_cross | $-13.90 |
| 2 | AAPL | 10 | 2026-06-22 09:30 ET @ 297.50 | 2026-06-22 13:45 ET @ 299.33 | ma_cross | $18.30 |
| 3 | AAPL | 10 | 2026-06-23 10:45 ET @ 300.37 | 2026-06-23 11:45 ET @ 297.77 | ma_cross | $-26.00 |
| 4 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 14:00 ET @ 373.56 | ma_cross | $-11.85 |
| 5 | AAPL | 10 | 2026-06-24 11:45 ET @ 298.23 | 2026-06-24 14:15 ET @ 295.57 | ma_cross | $-26.60 |
| 6 | AAPL | 10 | 2026-06-26 10:30 ET @ 278.28 | 2026-06-26 12:15 ET @ 276.01 | ma_cross | $-22.75 |
| 7 | MSFT | 10 | 2026-06-30 10:00 ET @ 371.55 | 2026-06-30 14:30 ET @ 370.77 | ma_cross | $-7.77 |
| 8 | AAPL | 10 | 2026-07-01 09:45 ET @ 291.00 | 2026-07-01 15:15 ET @ 294.57 | ma_cross | $35.70 |
| 9 | AAPL | 10 | 2026-07-02 09:45 ET @ 300.38 | 2026-07-02 16:00 ET @ 308.22 | session_flatten | $78.40 |
| 10 | MSFT | 10 | 2026-07-02 10:30 ET @ 388.65 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $9.65 |
| 11 | AAPL | 10 | 2026-07-07 11:30 ET @ 314.10 | 2026-07-07 14:00 ET @ 311.86 | ma_cross | $-22.43 |
| 12 | AAPL | 10 | 2026-07-14 09:30 ET @ 313.64 | 2026-07-14 09:45 ET @ 312.66 | stop | $-9.81 |
| 13 | MSFT | 10 | 2026-07-15 10:00 ET @ 389.60 | 2026-07-15 15:00 ET @ 395.65 | ma_cross | $60.50 |
| 14 | MSFT | 10 | 2026-07-16 11:00 ET @ 397.34 | 2026-07-16 16:00 ET @ 401.12 | session_flatten | $37.80 |
| 15 | MSFT | 10 | 2026-07-20 11:15 ET @ 396.64 | 2026-07-20 16:00 ET @ 402.51 | session_flatten | $58.75 |
| 16 | AAPL | 10 | 2026-07-23 09:30 ET @ 321.73 | 2026-07-23 09:45 ET @ 320.98 | stop | $-7.48 |
| 17 | AAPL | 10 | 2026-07-24 09:30 ET @ 324.38 | 2026-07-24 16:00 ET @ 333.07 | session_flatten | $86.95 |
| 18 | AAPL | 10 | 2026-07-27 09:45 ET @ 335.02 | 2026-07-27 14:00 ET @ 335.54 | ma_cross | $5.20 |
| 19 | MSFT | 10 | 2026-07-27 09:45 ET @ 389.86 | 2026-07-27 16:00 ET @ 389.13 | session_flatten | $-7.30 |
| 20 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 15:00 ET @ 396.96 | ma_cross | $24.60 |
| 21 | AAPL | 10 | 2026-07-28 09:45 ET @ 338.56 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $16.00 |
| 22 | MSFT | 10 | 2026-07-30 09:45 ET @ 449.17 | 2026-07-30 16:00 ET @ 451.48 | session_flatten | $23.10 |
| 23 | MSFT | 10 | 2026-07-31 11:45 ET @ 459.80 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $51.20 |
| 24 | AAPL | 10 | 2026-08-04 11:15 ET @ 306.27 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.20 |
| 25 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 |
| 26 | AAPL | 10 | 2026-08-05 11:00 ET @ 311.34 | 2026-08-05 11:45 ET @ 308.27 | ma_cross | $-30.75 |
| 27 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 14:00 ET @ 505.62 | ma_cross | $4.30 |
| 28 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 12:45 ET @ 494.30 | ma_cross | $-35.85 |
| 29 | AAPL | 10 | 2026-08-13 09:30 ET @ 304.26 | 2026-08-13 13:15 ET @ 303.08 | ma_cross | $-11.78 |
| 30 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 31 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 14:00 ET @ 315.19 | ma_cross | $35.00 |
| 32 | AAPL | 10 | 2026-08-20 09:45 ET @ 318.48 | 2026-08-20 13:45 ET @ 316.60 | ma_cross | $-18.80 |
| 33 | AAPL | 10 | 2026-08-24 10:15 ET @ 312.21 | 2026-08-24 14:15 ET @ 311.71 | ma_cross | $-5.00 |
| 34 | MSFT | 10 | 2026-08-24 10:00 ET @ 486.91 | 2026-08-24 14:45 ET @ 487.71 | ma_cross | $8.00 |
| 35 | MSFT | 10 | 2026-08-25 11:15 ET @ 489.34 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $21.60 |
| 36 | AAPL | 10 | 2026-08-26 09:45 ET @ 311.39 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $20.90 |
| 37 | AAPL | 10 | 2026-08-27 11:30 ET @ 314.65 | 2026-08-27 15:30 ET @ 313.58 | ma_cross | $-10.75 |
| 38 | AAPL | 10 | 2026-08-28 09:45 ET @ 317.28 | 2026-08-28 14:45 ET @ 319.59 | ma_cross | $23.07 |
| 39 | AAPL | 10 | 2026-09-02 11:30 ET @ 326.53 | 2026-09-02 12:30 ET @ 324.66 | ma_cross | $-18.70 |
| 40 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 14:00 ET @ 326.90 | ma_cross | $4.30 |
| 41 | AAPL | 10 | 2026-09-09 09:30 ET @ 315.93 | 2026-09-09 09:45 ET @ 315.85 | ma_cross | $-0.80 |
| 42 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:30 ET @ 314.71 | ma_cross | $-31.50 |
| 43 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 11:30 ET @ 492.14 | ma_cross | $-9.40 |
| 44 | MSFT | 10 | 2026-09-11 09:45 ET @ 495.61 | 2026-09-11 14:15 ET @ 495.73 | ma_cross | $1.15 |
