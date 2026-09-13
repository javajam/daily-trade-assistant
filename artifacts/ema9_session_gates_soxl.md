# ema9_trend 12:00 / 15:55 — 10-share AAPL+MSFT+SOXL vs isolated SOXL

- Generated (UTC): 2026-09-13T19:53:54.565817Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560; SOXL 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares; stop 1.5%; take 3.0%; cooldown 60 minutes
- Session: `entry_cutoff: "12:00"`, `flatten_by: "15:55"` America/New_York
- Config: `config/ema9_trend_bracket_soxl.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_bracket_soxl.example.yaml --source yahoo --breakout SOXL --output artifacts/ema9_session_gates_soxl.json --report artifacts/ema9_session_gates_soxl.md`

AAPL+MSFT-only on this cutoff (from `artifacts/ema9_session_gates.md`): **50 trades, 62.00%, $453.00**, max DD $207.70, **55 `entry_cutoff` skips**, **41 `session_flatten`**.

**Full set (AAPL+MSFT+SOXL):** **86 trades, 47.67%, $572.83**, max DD $225.05. Signals 240 (AAPL 77, MSFT 77, SOXL 86). Skips `entry_cutoff` 101, already_in_position 53. Exits: **43 `session_flatten`**, 31 stop, 12 take. Wins / losses / scratch: 41 / 36 / 9.

**Isolated SOXL:** **36 trades, 27.78%, $119.83**, max DD $162.52. Signals 86. Skips `entry_cutoff` 46, already_in_position 4. Exits: 23 stop, 11 take, **2 `session_flatten`**. Wins / losses / scratch: 10 / 18 / 8.

SOXL adds $119.83 on its own 10-share book. Combined with AAPL+MSFT that is **$572.83** versus **$453.00** without SOXL. Win rate falls because SOXL is 10/36 winners (27.78%) with 8 scratches; 23 of 36 SOXL exits are stops.

## Side-by-side

| | AAPL+MSFT (12:00) | AAPL+MSFT+SOXL (12:00) | Isolated SOXL (12:00) |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 240 (AAPL 77, MSFT 77, SOXL 86) | 86 (SOXL 86) |
| Skips | already_in_position 49, **entry_cutoff 55** | already_in_position 53, **entry_cutoff 101** | already_in_position 4, **entry_cutoff 46** |
| Trades | 50 (AAPL 22, MSFT 28) | 86 (AAPL 22, MSFT 28, SOXL 36) | 36 (SOXL 36) |
| Wins / losses / scratch | 31 / 18 / 1 | 41 / 36 / 9 | 10 / 18 / 8 |
| **Win rate** | **62.00%** | **47.67%** | **27.78%** |
| **Total P&L** | **$453.00** (0.453%) | **$572.83** (0.573%) | **$119.83** (0.120%) |
| Avg win | $32.19 | $36.63 | $50.38 |
| Avg loss | $-30.27 | $-25.80 | $-21.33 |
| **Max drawdown** | **$207.70** (0.21%) | **$225.05** (0.22%) | **$162.52** (0.16%) |
| Ending equity | $100,453.00 | $100,572.83 | $100,119.83 |
| Exit mix | **session_flatten 41**, stop 8, take 1 | **session_flatten 43**, stop 31, take 12 | stop 23, take 11, **session_flatten 2** |

### Full-set trades (AAPL+MSFT+SOXL, 12:00 / 15:55)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | SOXL | 10 | 2026-06-18 09:45 ET @ 266.35 | 2026-06-18 10:30 ET @ 274.35 | take | $80.01 |
| 2 | SOXL | 10 | 2026-06-22 09:45 ET @ 291.06 | 2026-06-22 10:15 ET @ 299.77 | take | $87.11 |
| 3 | MSFT | 10 | 2026-06-22 09:30 ET @ 375.56 | 2026-06-22 10:45 ET @ 373.36 | stop | $-21.96 |
| 4 | AAPL | 10 | 2026-06-22 11:15 ET @ 300.10 | 2026-06-22 16:00 ET @ 296.79 | session_flatten | $-33.05 |
| 5 | AAPL | 10 | 2026-06-23 09:45 ET @ 300.47 | 2026-06-23 15:30 ET @ 296.00 | stop | $-44.68 |
| 6 | MSFT | 10 | 2026-06-23 09:45 ET @ 374.74 | 2026-06-23 16:00 ET @ 373.90 | session_flatten | $-8.40 |
| 7 | SOXL | 10 | 2026-06-24 10:45 ET @ 231.68 | 2026-06-24 11:30 ET @ 228.27 | stop | $-34.06 |
| 8 | MSFT | 10 | 2026-06-24 10:30 ET @ 374.80 | 2026-06-24 14:45 ET @ 369.18 | stop | $-56.22 |
| 9 | SOXL | 10 | 2026-06-25 10:15 ET @ 237.24 | 2026-06-25 10:45 ET @ 244.18 | take | $69.42 |
| 10 | SOXL | 10 | 2026-06-26 09:30 ET @ 226.24 | 2026-06-26 09:45 ET @ 226.24 | stop | $0.00 |
| 11 | MSFT | 10 | 2026-06-26 09:45 ET @ 361.23 | 2026-06-26 15:45 ET @ 372.07 | take | $108.37 |
| 12 | AAPL | 10 | 2026-06-26 10:15 ET @ 278.21 | 2026-06-26 16:00 ET @ 281.20 | session_flatten | $29.90 |
| 13 | SOXL | 10 | 2026-06-29 11:00 ET @ 217.85 | 2026-06-29 11:45 ET @ 224.30 | take | $64.53 |
| 14 | AAPL | 10 | 2026-06-29 11:00 ET @ 281.82 | 2026-06-29 16:00 ET @ 281.63 | session_flatten | $-1.90 |
| 15 | AAPL | 10 | 2026-06-30 09:45 ET @ 283.27 | 2026-06-30 16:00 ET @ 289.09 | session_flatten | $58.20 |
| 16 | MSFT | 10 | 2026-06-30 11:30 ET @ 370.62 | 2026-06-30 16:00 ET @ 372.84 | session_flatten | $22.20 |
| 17 | SOXL | 10 | 2026-07-02 10:00 ET @ 223.50 | 2026-07-02 10:15 ET @ 219.80 | stop | $-37.02 |
| 18 | MSFT | 10 | 2026-07-02 11:45 ET @ 388.35 | 2026-07-02 16:00 ET @ 389.62 | session_flatten | $12.70 |
| 19 | SOXL | 10 | 2026-07-06 09:30 ET @ 197.21 | 2026-07-06 09:45 ET @ 197.21 | take | $0.00 |
| 20 | SOXL | 10 | 2026-07-08 09:30 ET @ 159.21 | 2026-07-08 09:45 ET @ 159.21 | stop | $0.00 |
| 21 | SOXL | 10 | 2026-07-09 09:30 ET @ 199.81 | 2026-07-09 09:45 ET @ 199.81 | take | $0.00 |
| 22 | MSFT | 10 | 2026-07-10 11:45 ET @ 383.99 | 2026-07-10 16:00 ET @ 385.08 | session_flatten | $10.92 |
| 23 | MSFT | 10 | 2026-07-13 11:00 ET @ 389.47 | 2026-07-13 16:00 ET @ 390.98 | session_flatten | $15.10 |
| 24 | MSFT | 10 | 2026-07-15 09:45 ET @ 387.47 | 2026-07-15 16:00 ET @ 395.62 | session_flatten | $81.50 |
| 25 | AAPL | 10 | 2026-07-16 09:30 ET @ 328.01 | 2026-07-16 16:00 ET @ 333.27 | session_flatten | $52.65 |
| 26 | MSFT | 10 | 2026-07-16 10:30 ET @ 396.02 | 2026-07-16 16:00 ET @ 401.12 | session_flatten | $51.00 |
| 27 | SOXL | 10 | 2026-07-17 09:30 ET @ 124.73 | 2026-07-17 09:45 ET @ 124.73 | stop | $0.00 |
| 28 | AAPL | 10 | 2026-07-17 09:30 ET @ 332.54 | 2026-07-17 16:00 ET @ 333.74 | session_flatten | $12.00 |
| 29 | SOXL | 10 | 2026-07-20 09:45 ET @ 147.88 | 2026-07-20 10:00 ET @ 145.62 | stop | $-22.57 |
| 30 | SOXL | 10 | 2026-07-20 11:15 ET @ 141.57 | 2026-07-20 12:15 ET @ 145.68 | take | $41.13 |
| 31 | MSFT | 10 | 2026-07-20 10:30 ET @ 394.36 | 2026-07-20 16:00 ET @ 402.51 | session_flatten | $81.50 |
| 32 | SOXL | 10 | 2026-07-21 09:45 ET @ 153.02 | 2026-07-21 10:15 ET @ 150.74 | stop | $-22.76 |
| 33 | AAPL | 10 | 2026-07-21 10:15 ET @ 326.07 | 2026-07-21 16:00 ET @ 327.59 | session_flatten | $15.20 |
| 34 | SOXL | 10 | 2026-07-22 10:00 ET @ 160.22 | 2026-07-22 10:15 ET @ 157.82 | stop | $-24.03 |
| 35 | SOXL | 10 | 2026-07-22 11:00 ET @ 160.05 | 2026-07-22 11:30 ET @ 164.80 | take | $47.50 |
| 36 | MSFT | 10 | 2026-07-23 09:30 ET @ 389.96 | 2026-07-23 10:15 ET @ 384.43 | stop | $-55.39 |
| 37 | MSFT | 10 | 2026-07-24 09:30 ET @ 386.55 | 2026-07-24 16:00 ET @ 381.74 | session_flatten | $-48.08 |
| 38 | AAPL | 10 | 2026-07-28 11:15 ET @ 339.09 | 2026-07-28 16:00 ET @ 340.16 | session_flatten | $10.70 |
| 39 | MSFT | 10 | 2026-07-28 09:45 ET @ 394.50 | 2026-07-28 16:00 ET @ 393.47 | session_flatten | $-10.30 |
| 40 | SOXL | 10 | 2026-07-30 09:45 ET @ 108.89 | 2026-07-30 10:00 ET @ 112.20 | take | $33.08 |
| 41 | AAPL | 10 | 2026-07-31 09:30 ET @ 304.81 | 2026-07-31 09:45 ET @ 304.81 | stop | $0.00 |
| 42 | MSFT | 10 | 2026-07-31 09:45 ET @ 459.97 | 2026-07-31 10:30 ET @ 453.07 | stop | $-69.00 |
| 43 | SOXL | 10 | 2026-07-31 10:30 ET @ 119.62 | 2026-07-31 11:00 ET @ 117.89 | stop | $-17.25 |
| 44 | MSFT | 10 | 2026-07-31 11:30 ET @ 457.83 | 2026-07-31 16:00 ET @ 464.92 | session_flatten | $70.95 |
| 45 | SOXL | 10 | 2026-08-03 11:00 ET @ 116.23 | 2026-08-03 11:15 ET @ 114.54 | stop | $-16.94 |
| 46 | AAPL | 10 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 16:00 ET @ 309.39 | session_flatten | $31.30 |
| 47 | MSFT | 10 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $17.40 |
| 48 | AAPL | 10 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $20.70 |
| 49 | SOXL | 10 | 2026-08-06 10:15 ET @ 137.70 | 2026-08-06 11:00 ET @ 135.74 | stop | $-19.57 |
| 50 | MSFT | 10 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $65.90 |
| 51 | SOXL | 10 | 2026-08-07 09:45 ET @ 142.43 | 2026-08-07 10:00 ET @ 140.34 | stop | $-20.92 |
| 52 | AAPL | 10 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $11.60 |
| 53 | SOXL | 10 | 2026-08-07 11:15 ET @ 136.82 | 2026-08-07 16:00 ET @ 140.26 | session_flatten | $34.40 |
| 54 | SOXL | 10 | 2026-08-10 09:30 ET @ 141.15 | 2026-08-10 09:45 ET @ 138.16 | stop | $-29.96 |
| 55 | SOXL | 10 | 2026-08-10 10:15 ET @ 140.09 | 2026-08-10 10:30 ET @ 137.90 | stop | $-21.90 |
| 56 | MSFT | 10 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $7.75 |
| 57 | SOXL | 10 | 2026-08-11 09:45 ET @ 135.14 | 2026-08-11 10:00 ET @ 133.19 | stop | $-19.53 |
| 58 | SOXL | 10 | 2026-08-11 11:00 ET @ 134.62 | 2026-08-11 12:15 ET @ 132.55 | stop | $-20.70 |
| 59 | SOXL | 10 | 2026-08-13 09:45 ET @ 145.51 | 2026-08-13 10:15 ET @ 149.91 | take | $44.01 |
| 60 | MSFT | 10 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-10.75 |
| 61 | AAPL | 10 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 16:00 ET @ 305.95 | session_flatten | $7.90 |
| 62 | MSFT | 10 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-30.60 |
| 63 | MSFT | 10 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $5.47 |
| 64 | AAPL | 10 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $51.88 |
| 65 | MSFT | 10 | 2026-08-19 10:00 ET @ 482.65 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $18.30 |
| 66 | SOXL | 10 | 2026-08-20 09:45 ET @ 122.04 | 2026-08-20 10:00 ET @ 120.25 | stop | $-17.91 |
| 67 | AAPL | 10 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 16:00 ET @ 312.66 | stop | $-47.71 |
| 68 | MSFT | 10 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $13.50 |
| 69 | SOXL | 10 | 2026-08-24 09:30 ET @ 115.00 | 2026-08-24 09:45 ET @ 115.00 | stop | $0.00 |
| 70 | AAPL | 10 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-8.00 |
| 71 | SOXL | 10 | 2026-08-25 09:45 ET @ 117.54 | 2026-08-25 10:15 ET @ 115.77 | stop | $-17.73 |
| 72 | MSFT | 10 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $27.15 |
| 73 | SOXL | 10 | 2026-08-26 09:30 ET @ 114.70 | 2026-08-26 10:15 ET @ 114.10 | stop | $-5.98 |
| 74 | AAPL | 10 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $32.35 |
| 75 | SOXL | 10 | 2026-08-27 09:30 ET @ 123.40 | 2026-08-27 09:45 ET @ 123.40 | take | $0.00 |
| 76 | AAPL | 10 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 16:00 ET @ 319.64 | session_flatten | $25.52 |
| 77 | SOXL | 10 | 2026-08-31 09:45 ET @ 112.49 | 2026-08-31 12:00 ET @ 110.84 | stop | $-16.48 |
| 78 | AAPL | 10 | 2026-09-02 09:45 ET @ 325.45 | 2026-09-02 16:00 ET @ 324.99 | session_flatten | $-4.65 |
| 79 | MSFT | 10 | 2026-09-02 09:30 ET @ 500.17 | 2026-09-02 16:00 ET @ 496.81 | session_flatten | $-33.60 |
| 80 | SOXL | 10 | 2026-09-02 11:15 ET @ 106.10 | 2026-09-02 16:00 ET @ 106.36 | session_flatten | $2.60 |
| 81 | AAPL | 10 | 2026-09-03 09:45 ET @ 326.47 | 2026-09-03 16:00 ET @ 328.21 | session_flatten | $17.40 |
| 82 | AAPL | 10 | 2026-09-09 10:00 ET @ 317.86 | 2026-09-09 10:45 ET @ 313.11 | stop | $-47.53 |
| 83 | MSFT | 10 | 2026-09-09 10:45 ET @ 493.08 | 2026-09-09 16:00 ET @ 491.77 | session_flatten | $-13.10 |
| 84 | SOXL | 10 | 2026-09-10 09:30 ET @ 116.35 | 2026-09-10 09:45 ET @ 116.35 | stop | $0.00 |
| 85 | SOXL | 10 | 2026-09-11 09:45 ET @ 122.00 | 2026-09-11 10:15 ET @ 120.14 | stop | $-18.64 |
| 86 | MSFT | 10 | 2026-09-11 11:15 ET @ 494.49 | 2026-09-11 16:00 ET @ 495.58 | session_flatten | $10.90 |

### Isolated SOXL trades (12:00 / 15:55)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | SOXL | 10 | 2026-06-18 09:45 ET @ 266.35 | 2026-06-18 10:30 ET @ 274.35 | take | $80.01 |
| 2 | SOXL | 10 | 2026-06-22 09:45 ET @ 291.06 | 2026-06-22 10:15 ET @ 299.77 | take | $87.11 |
| 3 | SOXL | 10 | 2026-06-24 10:45 ET @ 231.68 | 2026-06-24 11:30 ET @ 228.27 | stop | $-34.06 |
| 4 | SOXL | 10 | 2026-06-25 10:15 ET @ 237.24 | 2026-06-25 10:45 ET @ 244.18 | take | $69.42 |
| 5 | SOXL | 10 | 2026-06-26 09:30 ET @ 226.24 | 2026-06-26 09:45 ET @ 226.24 | stop | $0.00 |
| 6 | SOXL | 10 | 2026-06-29 11:00 ET @ 217.85 | 2026-06-29 11:45 ET @ 224.30 | take | $64.53 |
| 7 | SOXL | 10 | 2026-07-02 10:00 ET @ 223.50 | 2026-07-02 10:15 ET @ 219.80 | stop | $-37.02 |
| 8 | SOXL | 10 | 2026-07-06 09:30 ET @ 197.21 | 2026-07-06 09:45 ET @ 197.21 | take | $0.00 |
| 9 | SOXL | 10 | 2026-07-08 09:30 ET @ 159.21 | 2026-07-08 09:45 ET @ 159.21 | stop | $0.00 |
| 10 | SOXL | 10 | 2026-07-09 09:30 ET @ 199.81 | 2026-07-09 09:45 ET @ 199.81 | take | $0.00 |
| 11 | SOXL | 10 | 2026-07-17 09:30 ET @ 124.73 | 2026-07-17 09:45 ET @ 124.73 | stop | $0.00 |
| 12 | SOXL | 10 | 2026-07-20 09:45 ET @ 147.88 | 2026-07-20 10:00 ET @ 145.62 | stop | $-22.57 |
| 13 | SOXL | 10 | 2026-07-20 11:15 ET @ 141.57 | 2026-07-20 12:15 ET @ 145.68 | take | $41.13 |
| 14 | SOXL | 10 | 2026-07-21 09:45 ET @ 153.02 | 2026-07-21 10:15 ET @ 150.74 | stop | $-22.76 |
| 15 | SOXL | 10 | 2026-07-22 10:00 ET @ 160.22 | 2026-07-22 10:15 ET @ 157.82 | stop | $-24.03 |
| 16 | SOXL | 10 | 2026-07-22 11:00 ET @ 160.05 | 2026-07-22 11:30 ET @ 164.80 | take | $47.50 |
| 17 | SOXL | 10 | 2026-07-30 09:45 ET @ 108.89 | 2026-07-30 10:00 ET @ 112.20 | take | $33.08 |
| 18 | SOXL | 10 | 2026-07-31 10:30 ET @ 119.62 | 2026-07-31 11:00 ET @ 117.89 | stop | $-17.25 |
| 19 | SOXL | 10 | 2026-08-03 11:00 ET @ 116.23 | 2026-08-03 11:15 ET @ 114.54 | stop | $-16.94 |
| 20 | SOXL | 10 | 2026-08-06 10:15 ET @ 137.70 | 2026-08-06 11:00 ET @ 135.74 | stop | $-19.57 |
| 21 | SOXL | 10 | 2026-08-07 09:45 ET @ 142.43 | 2026-08-07 10:00 ET @ 140.34 | stop | $-20.92 |
| 22 | SOXL | 10 | 2026-08-07 11:15 ET @ 136.82 | 2026-08-07 16:00 ET @ 140.26 | session_flatten | $34.40 |
| 23 | SOXL | 10 | 2026-08-10 09:30 ET @ 141.15 | 2026-08-10 09:45 ET @ 138.16 | stop | $-29.96 |
| 24 | SOXL | 10 | 2026-08-10 10:15 ET @ 140.09 | 2026-08-10 10:30 ET @ 137.90 | stop | $-21.90 |
| 25 | SOXL | 10 | 2026-08-11 09:45 ET @ 135.14 | 2026-08-11 10:00 ET @ 133.19 | stop | $-19.53 |
| 26 | SOXL | 10 | 2026-08-11 11:00 ET @ 134.62 | 2026-08-11 12:15 ET @ 132.55 | stop | $-20.70 |
| 27 | SOXL | 10 | 2026-08-13 09:45 ET @ 145.51 | 2026-08-13 10:15 ET @ 149.91 | take | $44.01 |
| 28 | SOXL | 10 | 2026-08-20 09:45 ET @ 122.04 | 2026-08-20 10:00 ET @ 120.25 | stop | $-17.91 |
| 29 | SOXL | 10 | 2026-08-24 09:30 ET @ 115.00 | 2026-08-24 09:45 ET @ 115.00 | stop | $0.00 |
| 30 | SOXL | 10 | 2026-08-25 09:45 ET @ 117.54 | 2026-08-25 10:15 ET @ 115.77 | stop | $-17.73 |
| 31 | SOXL | 10 | 2026-08-26 09:30 ET @ 114.70 | 2026-08-26 10:15 ET @ 114.10 | stop | $-5.98 |
| 32 | SOXL | 10 | 2026-08-27 09:30 ET @ 123.40 | 2026-08-27 09:45 ET @ 123.40 | take | $0.00 |
| 33 | SOXL | 10 | 2026-08-31 09:45 ET @ 112.49 | 2026-08-31 12:00 ET @ 110.84 | stop | $-16.48 |
| 34 | SOXL | 10 | 2026-09-02 11:15 ET @ 106.10 | 2026-09-02 16:00 ET @ 106.36 | session_flatten | $2.60 |
| 35 | SOXL | 10 | 2026-09-10 09:30 ET @ 116.35 | 2026-09-10 09:45 ET @ 116.35 | stop | $0.00 |
| 36 | SOXL | 10 | 2026-09-11 09:45 ET @ 122.00 | 2026-09-11 10:15 ET @ 120.14 | stop | $-18.64 |

# Per-book detail

- Generated (UTC): 2026-09-13T19:53:54.565817Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m ema9_trend (cutoff 12:00, flat 15:55)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560, 'SOXL:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 240  (by symbol: {'SOXL': 86, 'AAPL': 77, 'MSFT': 77})
- Pattern hits in those signals: {'ema_cross': 240}
- Trades: 86  (by symbol: {'SOXL': 36, 'MSFT': 28, 'AAPL': 22})
- Wins / losses / scratch: 41 / 36 / 9
- Win rate: 47.67%
- Total P&L: $572.83 (0.573% of starting equity)
- Avg win: $36.63
- Avg loss: $-25.80
- Max drawdown: $225.05 (0.22%)
- Ending equity: $100,572.83
- Exit reasons: {'take': 12, 'stop': 31, 'session_flatten': 43}
- Skip reasons: {'entry_cutoff': 101, 'already_in_position': 53}
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid on that bar still win if they hit first. Set entry_cutoff / flatten_by to null to restore overnight holds.
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 101 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 43 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).

### Monthly

- Month: 2026-06-17 → 2026-09-11
- Session days: 60
- Trades: 86  (wins 41 / losses 36)
- Win rate: 53.25%
- Total P&L: $572.83 (0.57% of starting equity)
- Ending equity: $100,572.83
- Best day (realized): 2026-06-26 $138.27 (3 trades)
- Worst day (realized): 2026-06-24 $-90.28 (2 trades)

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W25 (2026-06-17 → 2026-06-18) | 1 | 100.00% | $80.01 | 0.08% | $100,080.01 |
| 2026-W26 (2026-06-22 → 2026-06-26) | 11 | 40.00% | $96.44 | 0.10% | $100,176.45 |
| 2026-W27 (2026-06-29 → 2026-07-02) | 6 | 66.67% | $118.71 | 0.12% | $100,295.16 |
| 2026-W28 (2026-07-06 → 2026-07-10) | 4 | 100.00% | $10.92 | 0.01% | $100,306.08 |
| 2026-W29 (2026-07-13 → 2026-07-17) | 6 | 100.00% | $212.25 | 0.21% | $100,518.33 |
| 2026-W30 (2026-07-20 → 2026-07-24) | 9 | 44.44% | $12.50 | 0.01% | $100,530.83 |
| 2026-W31 (2026-07-27 → 2026-07-31) | 7 | 50.00% | $18.18 | 0.02% | $100,549.01 |
| 2026-W32 (2026-08-03 → 2026-08-07) | 9 | 66.67% | $123.86 | 0.12% | $100,672.88 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 9 | 33.33% | $-73.79 | -0.07% | $100,599.09 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 6 | 66.67% | $23.53 | 0.02% | $100,622.62 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 8 | 50.00% | $53.31 | 0.05% | $100,675.94 |
| 2026-W36 (2026-08-31 → 2026-09-04) | 5 | 40.00% | $-34.73 | -0.03% | $100,641.21 |
| 2026-W37 (2026-09-08 → 2026-09-11) | 5 | 25.00% | $-68.38 | -0.07% | $100,572.83 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06-17 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-06-18 | 1 | 1 | 0 | $80.01 | 0.08% | $100,080.01 |
| 2026-06-22 | 3 | 1 | 2 | $32.10 | 0.03% | $100,112.11 |
| 2026-06-23 | 2 | 0 | 2 | $-53.08 | -0.05% | $100,059.04 |
| 2026-06-24 | 2 | 0 | 2 | $-90.28 | -0.09% | $99,968.75 |
| 2026-06-25 | 1 | 1 | 0 | $69.42 | 0.07% | $100,038.18 |
| 2026-06-26 | 3 | 2 | 0 | $138.27 | 0.14% | $100,176.45 |
| 2026-06-29 | 2 | 1 | 1 | $62.63 | 0.06% | $100,239.08 |
| 2026-06-30 | 2 | 2 | 0 | $80.40 | 0.08% | $100,319.48 |
| 2026-07-01 | 0 | 0 | 0 | $0.00 | 0.00% | $100,319.48 |
| 2026-07-02 | 2 | 1 | 1 | $-24.32 | -0.02% | $100,295.16 |
| 2026-07-06 | 1 | 0 | 0 | $0.00 | 0.00% | $100,295.16 |
| 2026-07-07 | 0 | 0 | 0 | $0.00 | 0.00% | $100,295.16 |
| 2026-07-08 | 1 | 0 | 0 | $0.00 | 0.00% | $100,295.16 |
| 2026-07-09 | 1 | 0 | 0 | $0.00 | 0.00% | $100,295.16 |
| 2026-07-10 | 1 | 1 | 0 | $10.92 | 0.01% | $100,306.08 |
| 2026-07-13 | 1 | 1 | 0 | $15.10 | 0.02% | $100,321.18 |
| 2026-07-14 | 0 | 0 | 0 | $0.00 | 0.00% | $100,321.18 |
| 2026-07-15 | 1 | 1 | 0 | $81.50 | 0.08% | $100,402.68 |
| 2026-07-16 | 2 | 2 | 0 | $103.65 | 0.10% | $100,506.33 |
| 2026-07-17 | 2 | 1 | 0 | $12.00 | 0.01% | $100,518.33 |
| 2026-07-20 | 3 | 2 | 1 | $100.07 | 0.10% | $100,618.40 |
| 2026-07-21 | 2 | 1 | 1 | $-7.56 | -0.01% | $100,610.84 |
| 2026-07-22 | 2 | 1 | 1 | $23.47 | 0.02% | $100,634.31 |
| 2026-07-23 | 1 | 0 | 1 | $-55.39 | -0.06% | $100,578.91 |
| 2026-07-24 | 1 | 0 | 1 | $-48.08 | -0.05% | $100,530.83 |
| 2026-07-27 | 0 | 0 | 0 | $0.00 | 0.00% | $100,530.83 |
| 2026-07-28 | 2 | 1 | 1 | $0.40 | 0.00% | $100,531.23 |
| 2026-07-29 | 0 | 0 | 0 | $0.00 | 0.00% | $100,531.23 |
| 2026-07-30 | 1 | 1 | 0 | $33.08 | 0.03% | $100,564.31 |
| 2026-07-31 | 4 | 1 | 2 | $-15.30 | -0.02% | $100,549.01 |
| 2026-08-03 | 1 | 0 | 1 | $-16.94 | -0.02% | $100,532.07 |
| 2026-08-04 | 2 | 2 | 0 | $48.70 | 0.05% | $100,580.77 |
| 2026-08-05 | 1 | 1 | 0 | $20.70 | 0.02% | $100,601.47 |
| 2026-08-06 | 2 | 1 | 1 | $46.33 | 0.05% | $100,647.80 |
| 2026-08-07 | 3 | 2 | 1 | $25.08 | 0.03% | $100,672.88 |
| 2026-08-10 | 3 | 1 | 2 | $-44.11 | -0.04% | $100,628.76 |
| 2026-08-11 | 2 | 0 | 2 | $-40.23 | -0.04% | $100,588.53 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $100,588.53 |
| 2026-08-13 | 2 | 1 | 1 | $33.26 | 0.03% | $100,621.79 |
| 2026-08-14 | 2 | 1 | 1 | $-22.70 | -0.02% | $100,599.09 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $100,599.09 |
| 2026-08-18 | 1 | 1 | 0 | $5.47 | 0.01% | $100,604.57 |
| 2026-08-19 | 2 | 2 | 0 | $70.18 | 0.07% | $100,674.75 |
| 2026-08-20 | 2 | 0 | 2 | $-65.62 | -0.07% | $100,609.12 |
| 2026-08-21 | 1 | 1 | 0 | $13.50 | 0.01% | $100,622.62 |
| 2026-08-24 | 2 | 0 | 1 | $-8.00 | -0.01% | $100,614.62 |
| 2026-08-25 | 2 | 1 | 1 | $9.42 | 0.01% | $100,624.04 |
| 2026-08-26 | 2 | 1 | 1 | $26.37 | 0.03% | $100,650.42 |
| 2026-08-27 | 1 | 0 | 0 | $0.00 | 0.00% | $100,650.42 |
| 2026-08-28 | 1 | 1 | 0 | $25.52 | 0.03% | $100,675.94 |
| 2026-08-31 | 1 | 0 | 1 | $-16.48 | -0.02% | $100,659.46 |
| 2026-09-01 | 0 | 0 | 0 | $0.00 | 0.00% | $100,659.46 |
| 2026-09-02 | 3 | 1 | 2 | $-35.65 | -0.04% | $100,623.81 |
| 2026-09-03 | 1 | 1 | 0 | $17.40 | 0.02% | $100,641.21 |
| 2026-09-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,641.21 |
| 2026-09-08 | 0 | 0 | 0 | $0.00 | 0.00% | $100,641.21 |
| 2026-09-09 | 2 | 0 | 2 | $-60.63 | -0.06% | $100,580.58 |
| 2026-09-10 | 1 | 0 | 0 | $0.00 | 0.00% | $100,580.58 |
| 2026-09-11 | 2 | 1 | 1 | $-7.74 | -0.01% | $100,572.83 |


## 15m ema9_trend SOXL (cutoff 12:00, flat 15:55)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'SOXL:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 86  (by symbol: {'SOXL': 86})
- Pattern hits in those signals: {'ema_cross': 86}
- Trades: 36  (by symbol: {'SOXL': 36})
- Wins / losses / scratch: 10 / 18 / 8
- Win rate: 27.78%
- Total P&L: $119.83 (0.120% of starting equity)
- Avg win: $50.38
- Avg loss: $-21.33
- Max drawdown: $162.52 (0.16%)
- Ending equity: $100,119.83
- Exit reasons: {'take': 11, 'stop': 23, 'session_flatten': 2}
- Skip reasons: {'entry_cutoff': 46, 'already_in_position': 4}
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid on that bar still win if they hit first. Set entry_cutoff / flatten_by to null to restore overnight holds.
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 46 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 2 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).

### Monthly

- Month: 2026-06-17 → 2026-09-11
- Session days: 60
- Trades: 36  (wins 10 / losses 18)
- Win rate: 35.71%
- Total P&L: $119.83 (0.12% of starting equity)
- Ending equity: $100,119.83
- Best day (realized): 2026-06-22 $87.11 (1 trades)
- Worst day (realized): 2026-08-10 $-51.86 (2 trades)

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W25 (2026-06-17 → 2026-06-18) | 1 | 100.00% | $80.01 | 0.08% | $100,080.01 |
| 2026-W26 (2026-06-22 → 2026-06-26) | 4 | 66.67% | $122.47 | 0.12% | $100,202.48 |
| 2026-W27 (2026-06-29 → 2026-07-02) | 2 | 50.00% | $27.51 | 0.03% | $100,229.99 |
| 2026-W28 (2026-07-06 → 2026-07-10) | 3 | n/a | $0.00 | 0.00% | $100,229.99 |
| 2026-W29 (2026-07-13 → 2026-07-17) | 1 | n/a | $0.00 | 0.00% | $100,229.99 |
| 2026-W30 (2026-07-20 → 2026-07-24) | 5 | 40.00% | $19.28 | 0.02% | $100,249.27 |
| 2026-W31 (2026-07-27 → 2026-07-31) | 2 | 50.00% | $15.83 | 0.02% | $100,265.09 |
| 2026-W32 (2026-08-03 → 2026-08-07) | 4 | 25.00% | $-23.03 | -0.02% | $100,242.06 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 5 | 20.00% | $-48.09 | -0.05% | $100,193.97 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 1 | 0.00% | $-17.91 | -0.02% | $100,176.06 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 4 | 0.00% | $-23.71 | -0.02% | $100,152.35 |
| 2026-W36 (2026-08-31 → 2026-09-04) | 2 | 50.00% | $-13.88 | -0.01% | $100,138.47 |
| 2026-W37 (2026-09-08 → 2026-09-11) | 2 | 0.00% | $-18.64 | -0.02% | $100,119.83 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06-17 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-06-18 | 1 | 1 | 0 | $80.01 | 0.08% | $100,080.01 |
| 2026-06-22 | 1 | 1 | 0 | $87.11 | 0.09% | $100,167.12 |
| 2026-06-23 | 0 | 0 | 0 | $0.00 | 0.00% | $100,167.12 |
| 2026-06-24 | 1 | 0 | 1 | $-34.06 | -0.03% | $100,133.06 |
| 2026-06-25 | 1 | 1 | 0 | $69.42 | 0.07% | $100,202.48 |
| 2026-06-26 | 1 | 0 | 0 | $0.00 | 0.00% | $100,202.48 |
| 2026-06-29 | 1 | 1 | 0 | $64.53 | 0.06% | $100,267.01 |
| 2026-06-30 | 0 | 0 | 0 | $0.00 | 0.00% | $100,267.01 |
| 2026-07-01 | 0 | 0 | 0 | $0.00 | 0.00% | $100,267.01 |
| 2026-07-02 | 1 | 0 | 1 | $-37.02 | -0.04% | $100,229.99 |
| 2026-07-06 | 1 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-07 | 0 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-08 | 1 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-09 | 1 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-10 | 0 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-13 | 0 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-14 | 0 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-15 | 0 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-16 | 0 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-17 | 1 | 0 | 0 | $0.00 | 0.00% | $100,229.99 |
| 2026-07-20 | 2 | 1 | 1 | $18.57 | 0.02% | $100,248.55 |
| 2026-07-21 | 1 | 0 | 1 | $-22.76 | -0.02% | $100,225.80 |
| 2026-07-22 | 2 | 1 | 1 | $23.47 | 0.02% | $100,249.27 |
| 2026-07-23 | 0 | 0 | 0 | $0.00 | 0.00% | $100,249.27 |
| 2026-07-24 | 0 | 0 | 0 | $0.00 | 0.00% | $100,249.27 |
| 2026-07-27 | 0 | 0 | 0 | $0.00 | 0.00% | $100,249.27 |
| 2026-07-28 | 0 | 0 | 0 | $0.00 | 0.00% | $100,249.27 |
| 2026-07-29 | 0 | 0 | 0 | $0.00 | 0.00% | $100,249.27 |
| 2026-07-30 | 1 | 1 | 0 | $33.08 | 0.03% | $100,282.34 |
| 2026-07-31 | 1 | 0 | 1 | $-17.25 | -0.02% | $100,265.09 |
| 2026-08-03 | 1 | 0 | 1 | $-16.94 | -0.02% | $100,248.15 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,248.15 |
| 2026-08-05 | 0 | 0 | 0 | $0.00 | 0.00% | $100,248.15 |
| 2026-08-06 | 1 | 0 | 1 | $-19.57 | -0.02% | $100,228.58 |
| 2026-08-07 | 2 | 1 | 1 | $13.48 | 0.01% | $100,242.06 |
| 2026-08-10 | 2 | 0 | 2 | $-51.86 | -0.05% | $100,190.19 |
| 2026-08-11 | 2 | 0 | 2 | $-40.23 | -0.04% | $100,149.96 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $100,149.96 |
| 2026-08-13 | 1 | 1 | 0 | $44.01 | 0.04% | $100,193.97 |
| 2026-08-14 | 0 | 0 | 0 | $0.00 | 0.00% | $100,193.97 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $100,193.97 |
| 2026-08-18 | 0 | 0 | 0 | $0.00 | 0.00% | $100,193.97 |
| 2026-08-19 | 0 | 0 | 0 | $0.00 | 0.00% | $100,193.97 |
| 2026-08-20 | 1 | 0 | 1 | $-17.91 | -0.02% | $100,176.06 |
| 2026-08-21 | 0 | 0 | 0 | $0.00 | 0.00% | $100,176.06 |
| 2026-08-24 | 1 | 0 | 0 | $0.00 | 0.00% | $100,176.06 |
| 2026-08-25 | 1 | 0 | 1 | $-17.73 | -0.02% | $100,158.33 |
| 2026-08-26 | 1 | 0 | 1 | $-5.98 | -0.01% | $100,152.35 |
| 2026-08-27 | 1 | 0 | 0 | $0.00 | 0.00% | $100,152.35 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $100,152.35 |
| 2026-08-31 | 1 | 0 | 1 | $-16.48 | -0.02% | $100,135.87 |
| 2026-09-01 | 0 | 0 | 0 | $0.00 | 0.00% | $100,135.87 |
| 2026-09-02 | 1 | 1 | 0 | $2.60 | 0.00% | $100,138.47 |
| 2026-09-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,138.47 |
| 2026-09-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,138.47 |
| 2026-09-08 | 0 | 0 | 0 | $0.00 | 0.00% | $100,138.47 |
| 2026-09-09 | 0 | 0 | 0 | $0.00 | 0.00% | $100,138.47 |
| 2026-09-10 | 1 | 0 | 0 | $0.00 | 0.00% | $100,138.47 |
| 2026-09-11 | 1 | 0 | 1 | $-18.64 | -0.02% | $100,119.83 |


## Assumptions

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
