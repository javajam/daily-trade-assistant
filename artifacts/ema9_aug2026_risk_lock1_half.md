# August 2026 1% equity risk: lock-+1% vs half-take at +1%

Companion to `artifacts/ema9_lock1_half.md`. Same Yahoo 15m AAPL+MSFT tape, `--start 2026-08-01 --end 2026-08-31`, 1% equity risk at a 1.0% fill stop.

Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_half.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_half.json --report artifacts/ema9_aug2026_risk_lock1_half.md`

Engine totals. Not invented.

## Verdict

**No.** Half-take at +1% does **not** beat plain lock-+1% on this August 1% risk book.

A **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

B: **14 trades, 71.43%, $4,799.30**, max DD $2,081.26. **$690.48 behind.**

Risk sizing ≈ 100% of equity. B’s earlier half-takes lift equity; the next lot can size +1 share and fail the next-open cash check. B has **2** fill-time cash skips vs A’s **1**. The extra miss is AAPL 2026-08-26 (A `lock_stop` **+$871.18**). On the 14 paired trades B is **+$180.70**.

## Side-by-side

| | A. Lock +1% | B. Lock +1% half-take |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 |
| Fill-time cash skips | 1 | 2 |
| Trades | 15 (AAPL 7, MSFT 8) | 14 (AAPL 6, MSFT 8) |
| Win rate | 73.33% | 71.43% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$4,799.30 (4.799%)** |
| Avg win / avg loss | $697.61 / -$546.00 | $698.63 / -$546.76 |
| Max drawdown | $2,743.31 (2.58%) | $2,081.26 (1.97%) |
| Exit mix | stop 1 / lock_stop 6 / flatten 8 | stop 1 / lock_stop 5 / flatten 8 |
| Lock armed | 6 | 5 |
| Half-take | 0 | **5** ($2,547.08 scale-out; remainder $2,384.08) |
| Scale-out fill | n/a | trigger 5 / gap-open 0 |
| Exit P&L | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | lock_stop $4,931.16 (5); flatten $918.83 (8); stop -$1,050.69 (1) |

### By symbol

| | A. Lock +1% | B. Lock +1% half-take |
| --- | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 | 6t, 66.67%, $1,796.98 |
| MSFT | 8t, 75.00%, $2,824.73 | 8t, 75.00%, $3,002.31 |

JSON: `artifacts/ema9_aug2026_risk_lock1_half.json`.
