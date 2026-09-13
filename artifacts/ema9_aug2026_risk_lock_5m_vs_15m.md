# ema9_trend lock-+1% August 2026 1% risk: 15m vs 5m (AAPL/MSFT)

- Generated (UTC): 2026-09-13T23:04:27.974786Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC) — same download as the 10-share lock 5m vs 15m book
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (prior bars kept for SMA/EMA/RSI warmup)
- Bars: AAPL 15m 1560; MSFT 15m 1560; AAPL 5m 4677; MSFT 5m 4676 (tape 2026-06-17T13:30:00Z → 2026-09-11)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing (both): `risk_pct` equity_risk 0.01, `stop_pct` 1.0 — shares = floor((0.01 × equity) / (0.01 × price)). Stop distance matches the 1% fill stop.
- Entry / session / lock-+1% / no-take: same as the default 10-share book
- 15m: `config/ema9_trend_risk.example.yaml` (same rules as prior Book B `config/ema9_trend_risk_nobe_lock1.example.yaml`)
- 5m: `config/ema9_trend_risk_5m.example.yaml` (identical rules; every indicator on 5m; flatten_by 15:55 → 15:50 ET bar close)
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_5m.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock_5m_vs_15m.json --report artifacts/ema9_aug2026_risk_lock_5m_vs_15m.md`

**15m reproduced** the prior August lock-+1% Book B exactly: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31. 58 signals; 28 `entry_cutoff`, 11 already-in-position, 3 `insufficient_cash` at size time (+ 1 fill skip). **6 armed the +1% lock; all 6 exited as `lock_stop` ($5,623.20)**. Remaining: **session_flatten 8 ($917.28)**, **stop 1 ($-1,050.69)**. Sizing 203–337 shares.

**5m** on the same August window is feasible: **26 trades, 57.69%, $4,061.83**, max DD $3,441.69. 125 signals; 49 `entry_cutoff`, 33 already-in-position, 16 `insufficient_cash` at size time (+ 1 fill skip). **9 armed the +1% lock; 8 exited as `lock_stop` ($7,519.45)** (AAPL 8/19 armed then flattened +$1,856.57). Remaining: **session_flatten 13 ($1,615.31)**, **stop 5 ($-5,072.94)**. Max concurrent symbols this run: 1 (cash rarely covers a second 1% risk lot on 5m).

5m locks more dollars on the +1% tags than 15m, but five full 1R stops (vs one on 15m) and extra flatten losers leave it **$1,427.95 behind 15m** with a larger drawdown.

## Side-by-side (August 1% risk)

| | 15m lock +1% | 5m lock +1% |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 125 (AAPL 53, MSFT 72) |
| Skips | already_in_position 11, entry_cutoff 28, insufficient_cash 3 | already_in_position 33, entry_cutoff 49, insufficient_cash 16 |
| Trades | 15 (MSFT 8, AAPL 7) | 26 (AAPL 11, MSFT 15) |
| Wins / losses / scratch | 11 / 4 / 0 | 15 / 11 / 0 |
| **Win rate** | **73.33%** | **57.69%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$4,061.83 (4.062%)** |
| Avg win | $697.61 | $737.18 |
| Avg loss | $-546.00 | $-635.99 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$3,441.69 (3.31%)** |
| Ending equity | $105,489.78 | $104,061.83 |
| Exit mix | stop 1, lock_stop 6, session_flatten 8 | stop 5, lock_stop 8, session_flatten 13 |
| Lock armed | 6 | 9 |
| **Exit P&L** | lock_stop $5,623.20 (6); session_flatten $917.28 (8); stop $-1,050.69 (1) | lock_stop $7,519.45 (8); session_flatten $1,615.31 (13); stop $-5,072.94 (5) |

Figures are engine totals, not annualized. Small sample (15 / 26 trades). $0 friction. 1% equity risk at a matching 1.0% stop.

### 15m trades (lock +1%, 1% risk)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 203 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 11:00 ET @ 495.99 | lock_stop | $996.89 |
| 2 | AAPL | 329 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 13:30 ET @ 309.32 | lock_stop | $1,007.60 |
| 3 | AAPL | 330 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $683.10 |
| 4 | MSFT | 208 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 10:45 ET @ 496.51 | lock_stop | $673.94 |
| 5 | AAPL | 331 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $383.92 |
| 6 | MSFT | 205 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 11:00 ET @ 510.25 | lock_stop | $1,035.65 |
| 7 | MSFT | 210 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-225.75 |
| 8 | MSFT | 209 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-639.54 |
| 9 | MSFT | 215 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $117.71 |
| 10 | AAPL | 333 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 13:00 ET @ 314.81 | lock_stop | $1,037.93 |
| 11 | AAPL | 331 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.26 | stop | $-1,050.69 |
| 12 | MSFT | 215 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $290.25 |
| 13 | AAPL | 335 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-268.00 |
| 14 | MSFT | 212 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $575.58 |
| 15 | AAPL | 337 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 10:30 ET @ 312.83 | lock_stop | $871.18 |

### 5m trades (lock +1%, 1% risk)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | AAPL | 324 | 2026-08-03 09:55 ET @ 308.27 | 2026-08-03 10:05 ET @ 305.19 | stop | $-998.79 |
| 2 | MSFT | 203 | 2026-08-03 10:40 ET @ 486.08 | 2026-08-03 14:40 ET @ 490.20 | lock_stop | $836.37 |
| 3 | AAPL | 327 | 2026-08-04 09:50 ET @ 304.72 | 2026-08-04 12:50 ET @ 307.74 | lock_stop | $987.54 |
| 4 | AAPL | 326 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 15:55 ET @ 310.93 | session_flatten | $678.08 |
| 5 | MSFT | 205 | 2026-08-06 09:40 ET @ 492.98 | 2026-08-06 10:30 ET @ 496.61 | lock_stop | $744.14 |
| 6 | AAPL | 326 | 2026-08-06 10:55 ET @ 313.33 | 2026-08-06 11:25 ET @ 310.19 | stop | $-1,021.44 |
| 7 | MSFT | 203 | 2026-08-06 11:30 ET @ 496.47 | 2026-08-06 15:55 ET @ 499.83 | session_flatten | $682.08 |
| 8 | AAPL | 325 | 2026-08-07 09:35 ET @ 313.23 | 2026-08-07 15:55 ET @ 313.23 | session_flatten | $1.63 |
| 9 | MSFT | 202 | 2026-08-10 09:35 ET @ 503.75 | 2026-08-10 10:15 ET @ 508.51 | lock_stop | $961.52 |
| 10 | MSFT | 204 | 2026-08-11 11:10 ET @ 503.14 | 2026-08-11 15:55 ET @ 503.83 | session_flatten | $140.75 |
| 11 | MSFT | 207 | 2026-08-13 09:35 ET @ 497.07 | 2026-08-13 15:55 ET @ 496.47 | session_flatten | $-123.17 |
| 12 | MSFT | 206 | 2026-08-14 09:40 ET @ 497.33 | 2026-08-14 15:55 ET @ 495.12 | session_flatten | $-456.85 |
| 13 | MSFT | 206 | 2026-08-17 09:30 ET @ 490.22 | 2026-08-17 09:55 ET @ 485.32 | stop | $-1,009.85 |
| 14 | MSFT | 209 | 2026-08-17 11:15 ET @ 484.42 | 2026-08-17 13:00 ET @ 479.58 | stop | $-1,012.44 |
| 15 | AAPL | 327 | 2026-08-18 09:35 ET @ 306.21 | 2026-08-18 10:15 ET @ 309.27 | lock_stop | $1,001.31 |
| 16 | MSFT | 210 | 2026-08-18 10:40 ET @ 481.53 | 2026-08-18 15:55 ET @ 481.85 | session_flatten | $67.33 |
| 17 | AAPL | 326 | 2026-08-19 09:35 ET @ 310.73 | 2026-08-19 15:55 ET @ 316.42 | session_flatten | $1,856.57 |
| 18 | AAPL | 325 | 2026-08-20 10:55 ET @ 317.05 | 2026-08-20 15:25 ET @ 313.88 | stop | $-1,030.41 |
| 19 | MSFT | 211 | 2026-08-21 09:35 ET @ 483.50 | 2026-08-21 15:55 ET @ 483.26 | session_flatten | $-50.64 |
| 20 | AAPL | 329 | 2026-08-24 09:35 ET @ 310.49 | 2026-08-24 15:55 ET @ 310.83 | session_flatten | $111.86 |
| 21 | AAPL | 328 | 2026-08-25 09:35 ET @ 311.30 | 2026-08-25 15:55 ET @ 309.89 | session_flatten | $-462.47 |
| 22 | AAPL | 326 | 2026-08-26 10:40 ET @ 312.11 | 2026-08-26 15:15 ET @ 315.12 | lock_stop | $979.63 |
| 23 | MSFT | 207 | 2026-08-27 09:45 ET @ 495.60 | 2026-08-27 10:10 ET @ 500.30 | lock_stop | $972.90 |
| 24 | MSFT | 203 | 2026-08-28 10:20 ET @ 510.37 | 2026-08-28 11:10 ET @ 515.47 | lock_stop | $1,036.05 |
| 25 | MSFT | 203 | 2026-08-28 11:50 ET @ 514.88 | 2026-08-28 15:55 ET @ 513.44 | session_flatten | $-292.32 |
| 26 | MSFT | 204 | 2026-08-31 11:45 ET @ 511.10 | 2026-08-31 15:55 ET @ 508.46 | session_flatten | $-537.54 |

## Pick (August 1% risk)

On this August tape **15m lock-+1% makes more money with a smaller drawdown**. 5m is runnable (26 trades, cash-constrained to one name) but pays five full 1R stops. If the goal is August 1% risk with the default lock book, keep **15m**.
