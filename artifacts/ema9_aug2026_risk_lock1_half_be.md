# August 2026 1% equity risk: lock-+1% vs half-take + BE remainder

Companion to `artifacts/ema9_lock1_half_be.md`. Same Yahoo 15m AAPL+MSFT tape, `--start 2026-08-01 --end 2026-08-31`, 1% equity risk at a 1.0% fill stop.

Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_half_be.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_half_be.json --report artifacts/ema9_aug2026_risk_lock1_half_be.md`

Engine totals. Not invented.

## Verdict

**No.** Half-take at +1% + BE remainder does **not** beat plain lock-+1% on this August 1% risk book.

A **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

C: **12 trades, 75.00%, $3,872.16**, max DD $1,721.08. **$1,617.62 behind.**

C has **3** fill-time cash skips vs A’s **1**, and **4** size-time cash skips vs **3**. Missing AAPL fills: 2026-08-04 `lock_stop` +$1,007.60, 2026-08-24 flatten -$268.00, 2026-08-26 `lock_stop` +$871.18. **4** half-takes ($2,020.55 scale-out); 1 remainder `breakeven_stop`, 3 flatten.

## Side-by-side

| | A. Lock +1% | C. Half + BE |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | cutoff 28, already_in 11, insufficient_cash 3 | cutoff 27, already_in 12, insufficient_cash 4 |
| Fill-time cash skips | 1 | 3 |
| Trades | 15 (AAPL 7, MSFT 8) | 12 (AAPL 4, MSFT 8) |
| Win rate | 73.33% | 75.00% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$3,872.16 (3.872%)** |
| Max drawdown | $2,743.31 (2.58%) | $1,721.08 (1.65%) |
| Exit mix | stop 1 / lock_stop 6 / flatten 8 | stop 1 / be_stop 1 / flatten 10 |
| Half-take | 0 | **4** ($2,020.55) |

JSON: `artifacts/ema9_aug2026_risk_lock1_half_be.json`.
