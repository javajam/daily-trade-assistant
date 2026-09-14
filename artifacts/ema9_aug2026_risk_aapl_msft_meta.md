# ema9_trend August 2026 1% risk — AAPL+MSFT+META vs AAPL+MSFT

- Generated (UTC): 2026-09-14T00:50:53.385634Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: AAPL 15m 1560; MSFT 15m 1560; META 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry: 15m close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill next open.
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 (15m flatten = 15:45 ET bar close)
- Stop: `stop_mode: lock_plus` — initial fill×0.99; lock at fill×1.01 (live next bar). No take-profit.
- Size: 1% equity risk at `stop_pct` 1.0 — `shares = floor((0.01 * equity) / (0.01 * entry_price))`
- Shorts parked. Configs: `config/ema9_trend_risk_aapl_msft_meta.example.yaml`, `config/ema9_trend_risk_nobe_lock1.example.yaml`
- Isolated META: `--breakout META`
- Full-window 10-share writeup: `artifacts/ema9_aapl_msft_meta_15m.md`
- Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_risk_aapl_msft_meta.example.yaml \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --breakout META \
  --output artifacts/ema9_aug2026_risk_aapl_msft_meta.json \
  --report artifacts/ema9_aug2026_risk_aapl_msft_meta.md
```

Engine totals only. Not annualized. One August window on the Yahoo 15m tape.

## Totals

| | AAPL+MSFT+META 1% risk | AAPL+MSFT 1% risk | Isolated META 1% risk |
| --- | ---: | ---: | ---: |
| Signals | 84 (MSFT 32, AAPL 26, META 26) | 58 (MSFT 32, AAPL 26) | 26 (META 26) |
| Skips | entry_cutoff 47, insufficient_cash 10, already_in_position 9 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 14, already_in_position 3 |
| Trades | 16 (MSFT 8, AAPL 5, META 3) | 15 (MSFT 8, AAPL 7) | 9 (META 9) |
| Wins / losses | 10 / 6 | 11 / 4 | 6 / 3 |
| **Win rate** | **62.50%** | **73.33%** | **66.67%** |
| **Total P&L** | **$1,913.28 (1.913%)** | **$5,489.78 (5.490%)** | **$1,961.82 (1.962%)** |
| Avg win | $610.49 | $697.61 | $805.21 |
| Avg loss | $-698.60 | $-546.00 | $-956.47 |
| **Max drawdown** | **$2,774.85 (2.65%)** | **$2,743.31 (2.58%)** | **$1,182.03 (1.16%)** |
| Ending equity | $101,913.28 | $105,489.78 | $101,961.82 |
| Exit mix | session_flatten 7, lock_stop 6, stop 3 | session_flatten 8, lock_stop 6, stop 1 | lock_stop 6, stop 2, session_flatten 1 |
| Lock armed | 6 | 6 | 6 |
| **Exit P&L** | lock_stop $4,758.19; session_flatten $230.58; stop $-3,075.50 | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 | lock_stop $4,831.24; session_flatten $-855.14; stop $-2,014.28 |
| Size | AAPL 325–329; MSFT 202–212; META 171–179 | AAPL 329–337; MSFT 203–215 | META 166–181 |
| Max concurrent | 1 | 1 | 1 |

AAPL+MSFT **reproduced** the prior August lock-+1% 1% risk book: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

Isolated META is green: 9 trades, 6 wins, **$1,961.82**. Combined is **not** baseline + META. Combined **$1,913.28** is **$3,576.50** behind AAPL+MSFT. META at ~$560–596 with a 1% stop sizes near full equity, so only one name can be open (**10** `insufficient_cash` skips vs 3 on the baseline). Combined META: 3 trades, 1 win, **$-1,993.97**. Combined AAPL: 5 trades, 3 wins, **$1,112.06** (baseline AAPL 7 / $2,665.05). Combined MSFT: 8 trades, 6 wins, **$2,795.18** (baseline MSFT 8 / $2,824.73).

Best day: 2026-08-04 **$2,004.49**. Worst day: 2026-08-20 **$-1,031.65**. Peak equity **$103,379.05** after the 2026-08-19 AAPL lock, then $101,913.28.

### Weekly (AAPL+MSFT+META)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W32 (08-03 → 08-07) | 6 | 83.33% | $2,073.03 | $102,073.03 |
| 2026-W33 (08-10 → 08-14) | 3 | 33.33% | $167.61 | $102,240.64 |
| 2026-W34 (08-17 → 08-21) | 4 | 75.00% | $392.97 | $102,633.61 |
| 2026-W35 (08-24 → 08-28) | 3 | 33.33% | $-720.33 | $101,913.28 |
| 2026-W36 (08-31) | 0 | n/a | $0.00 | $101,913.28 |

### Trades (AAPL+MSFT+META)

| # | Symbol | Qty | Entry (ET) | Exit (ET) | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 203 | 2026-08-04 10:00 @ 491.08 | 2026-08-04 11:00 @ 495.99 | lock_stop | $996.89 |
| 2 | AAPL | 329 | 2026-08-04 11:45 @ 306.26 | 2026-08-04 13:30 @ 309.32 | lock_stop | $1,007.60 |
| 3 | META | 171 | 2026-08-05 09:45 @ 596.07 | 2026-08-05 11:00 @ 590.11 | stop | $-1,019.28 |
| 4 | MSFT | 204 | 2026-08-06 09:45 @ 493.27 | 2026-08-06 10:45 @ 496.51 | lock_stop | $660.98 |
| 5 | META | 172 | 2026-08-07 09:30 @ 589.00 | 2026-08-07 10:00 @ 589.29 | lock_stop | $49.88 |
| 6 | AAPL | 325 | 2026-08-07 10:15 @ 312.14 | 2026-08-07 16:00 @ 313.30 | session_flatten | $376.96 |
| 7 | MSFT | 202 | 2026-08-10 09:45 @ 505.20 | 2026-08-10 11:00 @ 510.25 | lock_stop | $1,020.49 |
| 8 | MSFT | 207 | 2026-08-13 09:45 @ 497.89 | 2026-08-13 16:00 @ 496.81 | session_flatten | $-222.53 |
| 9 | MSFT | 206 | 2026-08-14 10:00 @ 498.48 | 2026-08-14 16:00 @ 495.42 | session_flatten | $-630.36 |
| 10 | MSFT | 212 | 2026-08-18 10:15 @ 481.38 | 2026-08-18 16:00 @ 481.93 | session_flatten | $116.07 |
| 11 | AAPL | 328 | 2026-08-19 09:45 @ 311.69 | 2026-08-19 13:00 @ 314.81 | lock_stop | $1,022.35 |
| 12 | AAPL | 325 | 2026-08-20 11:00 @ 317.43 | 2026-08-20 15:30 @ 314.26 | stop | $-1,031.65 |
| 13 | MSFT | 212 | 2026-08-21 09:45 @ 482.00 | 2026-08-21 16:00 @ 483.35 | session_flatten | $286.20 |
| 14 | AAPL | 329 | 2026-08-24 09:45 @ 311.15 | 2026-08-24 16:00 @ 310.35 | session_flatten | $-263.20 |
| 15 | MSFT | 209 | 2026-08-25 09:45 @ 488.79 | 2026-08-25 16:00 @ 491.50 | session_flatten | $567.43 |
| 16 | META | 179 | 2026-08-26 10:00 @ 572.39 | 2026-08-26 10:30 @ 566.66 | stop | $-1,024.57 |

Full-window 10-share comparison and isolated-META August fills: `artifacts/ema9_aapl_msft_meta_15m.md`.
