# ema9_trend August 2026 1% risk: fixed 1% vs lock-+1% vs trail-1% (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:52:31.638090Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC) — same 15m download as the 10-share book
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (prior bars kept for SMA/EMA/RSI warmup)
- Bars: AAPL 15m 1560; MSFT 15m 1560 (tape 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing (all): `risk_pct` equity_risk 0.01, `stop_pct` 1.0 — shares = floor((0.01 × equity) / (0.01 × price)). Stop distance matches the 1% fill stop.
- Entry / session / no-take: same as the 10-share A/B/C books
- A. **Fixed 1%** (`stop_mode: entry_pct`): `config/ema9_trend_risk_nobe_fixed1.example.yaml`
- B. **Lock to +1%** (`stop_mode: lock_plus`): `config/ema9_trend_risk_nobe_lock1.example.yaml`
- C. **Trail 1%** (`stop_mode: trail`): `config/ema9_trend_risk_nobe_trail1.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_fixed1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_trail1.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_stop_manage.json --report artifacts/ema9_aug2026_risk_stop_manage.md`

**Book A (fixed 1%)**: **14 trades, 71.43%, $4,500.84**, max DD $2,289.59. 58 signals; 24 `entry_cutoff`, 15 already-in-position, 4 `insufficient_cash` (+ 1 fill skip). Exits: **session_flatten 13 ($5,538.83)**, **stop 1 ($-1,038.00)** (AAPL 8/20, 327 shares). Sizing 203–333 shares.

**Book B (lock +1%)**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31. Same 58 signals; 28 `entry_cutoff`, 11 already-in-position, 3 `insufficient_cash` (+ 1 fill skip). **6 armed the +1% lock; all 6 exited as `lock_stop` ($5,623.20)**. Remaining: **session_flatten 8 ($917.28)**, **stop 1 ($-1,050.69)**. Extra trade vs A is AAPL 8/4: MSFT locked out at 11:00, which freed cash/slot for the 11:45 AAPL signal (A held MSFT to flatten). Locking the +1% runners (MSFT 8/4, 8/6, 8/10; AAPL 8/4, 8/19, 8/26) banks ~1R each instead of hoping the flatten is larger — on this August tape that **beats A by $988.94**.

**Book C (trail 1%)**: **14 trades, 50.00%, $2,071.50**, max DD $2,552.41. Same 58 signals; 30 `entry_cutoff`, 9 already-in-position, 4 `insufficient_cash` (+ 1 fill skip). **All 14 ratcheted**. Exits: **trail_stop 11 ($349.67)**, **session_flatten 3 ($1,721.83)**. Trail stops the same days B locked, but after a smaller extension (or a give-back), and it also stops several A-flatten winners (AAPL 8/5, 8/7, 8/24). **$2,429.34 behind A**.

## Side-by-side (August 1% risk)

| | A. Fixed 1% | B. Lock +1% | C. Trail 1% |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | already_in_position 15, entry_cutoff 24, insufficient_cash 4 | already_in_position 11, entry_cutoff 28, insufficient_cash 3 | already_in_position 9, entry_cutoff 30, insufficient_cash 4 |
| Trades | 14 (AAPL 6, MSFT 8) | 15 (AAPL 7, MSFT 8) | 14 (AAPL 6, MSFT 8) |
| Wins / losses / scratch | 10 / 4 / 0 | 11 / 4 / 0 | 7 / 7 / 0 |
| **Win rate** | **71.43%** | **73.33%** | **50.00%** |
| **Total P&L** | **$4,500.84 (4.501%)** | **$5,489.78 (5.490%)** | **$2,071.50 (2.071%)** |
| Avg win | $665.24 | $697.61 | $662.20 |
| Avg loss | -$537.89 | -$546.00 | -$366.27 |
| **Max drawdown** | **$2,289.59 (2.20%)** | **$2,743.31 (2.58%)** | **$2,552.41 (2.49%)** |
| Ending equity | $104,500.84 | $105,489.78 | $102,071.50 |
| Exit mix | stop 1, session_flatten 13 | stop 1, lock_stop 6, session_flatten 8 | trail_stop 11, session_flatten 3 |
| Lock armed / trail ratcheted | 0 / 0 | 6 / 0 | 0 / 14 |
| **Exit P&L** | session_flatten $5,538.83 (13); stop -$1,038.00 (1) | session_flatten $917.28 (8); stop -$1,050.69 (1); lock_stop $5,623.20 (6) | session_flatten $1,721.83 (3); trail_stop $349.67 (11) |

Figures are engine totals, not annualized. Small sample (14–15 trades). $0 friction. 1% equity risk at a matching 1.0% stop.

### Book A trades (fixed 1%, 1% risk)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 203 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $353.22 |
| 2 | AAPL | 324 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $670.68 |
| 3 | MSFT | 204 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $1,344.36 |
| 4 | AAPL | 327 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $379.28 |
| 5 | MSFT | 203 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $157.32 |
| 6 | MSFT | 206 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | -$221.45 |
| 7 | MSFT | 205 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | -$627.30 |
| 8 | MSFT | 212 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $116.07 |
| 9 | AAPL | 327 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $1,696.48 |
| 10 | AAPL | 327 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.26 | stop | -$1,038.00 |
| 11 | MSFT | 213 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $287.55 |
| 12 | AAPL | 331 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | -$264.80 |
| 13 | MSFT | 210 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $570.15 |
| 14 | AAPL | 333 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $1,077.26 |

### Book B trades (lock +1%, 1% risk)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 203 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 11:00 ET @ 495.99 | lock_stop | $996.89 |
| 2 | AAPL | 329 | 2026-08-04 11:45 ET @ 306.26 | 2026-08-04 13:30 ET @ 309.32 | lock_stop | $1,007.60 |
| 3 | AAPL | 330 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $683.10 |
| 4 | MSFT | 208 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 10:45 ET @ 496.51 | lock_stop | $673.94 |
| 5 | AAPL | 331 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $383.92 |
| 6 | MSFT | 205 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 11:00 ET @ 510.25 | lock_stop | $1,035.65 |
| 7 | MSFT | 210 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | -$225.75 |
| 8 | MSFT | 209 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | -$639.54 |
| 9 | MSFT | 215 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $117.71 |
| 10 | AAPL | 333 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 13:00 ET @ 314.81 | lock_stop | $1,037.93 |
| 11 | AAPL | 331 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.26 | stop | -$1,050.69 |
| 12 | MSFT | 215 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $290.25 |
| 13 | AAPL | 335 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | -$268.00 |
| 14 | MSFT | 212 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $575.58 |
| 15 | AAPL | 337 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 10:30 ET @ 312.83 | lock_stop | $871.18 |

### Book C trades (trail 1%, 1% risk)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 203 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 13:00 ET @ 494.45 | trail_stop | $683.20 |
| 2 | AAPL | 325 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 11:30 ET @ 308.59 | trail_stop | -$84.14 |
| 3 | MSFT | 203 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 12:45 ET @ 493.98 | trail_stop | $144.19 |
| 4 | AAPL | 322 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 12:15 ET @ 311.66 | trail_stop | -$153.98 |
| 5 | MSFT | 199 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 11:00 ET @ 508.59 | trail_stop | $675.36 |
| 6 | MSFT | 203 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 11:15 ET @ 496.33 | trail_stop | -$316.36 |
| 7 | MSFT | 202 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 15:15 ET @ 495.01 | trail_stop | -$700.96 |
| 8 | MSFT | 208 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $113.88 |
| 9 | AAPL | 321 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 12:00 ET @ 316.09 | trail_stop | $1,410.83 |
| 10 | AAPL | 320 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:15 ET @ 314.60 | trail_stop | -$904.89 |
| 11 | MSFT | 209 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 14:00 ET @ 481.50 | trail_stop | -$105.26 |
| 12 | AAPL | 323 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.23 | trail_stop | -$298.33 |
| 13 | MSFT | 205 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $556.57 |
| 14 | AAPL | 325 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $1,051.38 |

## Pick (August 1% risk)

On this August window **B (lock +1%) makes the most money** and has the highest win rate. A still wins on flatten-heavy days (MSFT 8/6 +$1,344 flatten vs B's +$674 lock) but gives back more when the name never tags +1% and then stops (only one stop on both A and B: AAPL 8/20). C trails because the 1% ratchet exits most names before the flatten. Small sample — do not treat August as a general ranking over the 10-share full window, where **A won**.
