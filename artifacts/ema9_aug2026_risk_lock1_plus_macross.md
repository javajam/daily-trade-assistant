# August 2026 1% equity risk: lock-+1% vs MA-cross at close vs lock + MA-cross

Companion to `artifacts/ema9_lock1_plus_macross.md`. Same Yahoo 15m AAPL+MSFT tape, `--start 2026-08-01 --end 2026-08-31`. A and C size 1% of equity at the live 1.0% fill stop. B has no live stop; `stop_pct: 1.0` is a reference R only.

Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_macross.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_macross.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_plus_macross.json --report artifacts/ema9_aug2026_risk_lock1_plus_macross.md`

Engine totals. Not invented.

## Verdict

**C does not beat plain lock-+1%. C does beat pure MA-cross on this August 1% window.**

A **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

B **reproduced**: **14 trades, 57.14%, $2,998.96**, max DD $2,510.94.

C: **15 trades, 60.00%, $4,586.73**, max DD $1,915.59. **$903.05 behind A**, **$1,587.77 ahead of B**.

C keeps A’s 15 fills and 6 `lock_stop`s (including AAPL 2026-08-04 +$1,007.60 that B cash-skipped). Six A flattens become earlier `ma_cross` cuts. Same-bar priority: stop / `lock_stop` beats the pair-cross.

## Side-by-side

| | A. Lock +1% | B. MA-cross at close | C. Lock + MA-cross |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Trades | 15 (AAPL 7, MSFT 8) | 14 (AAPL 6, MSFT 8) | 15 (AAPL 7, MSFT 8) |
| Win rate | 73.33% | 57.14% | 60.00% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$2,998.96 (2.999%)** | **$4,586.73 (4.587%)** |
| Max drawdown | $2,743.31 (2.58%) | $2,510.94 (2.44%) | $1,915.59 (1.83%) |
| Exit mix | lock_stop 6, flatten 8, stop 1 | ma_cross 10, flatten 4 | lock_stop 6, ma_cross 7, flatten 2 |
| Exit P&L | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | ma_cross $-75.78 (10); flatten $3,074.74 (4) | lock_stop $5,578.22 (6); ma_cross $-1,680.42 (7); flatten $688.93 (2) |

### By symbol

| | A. Lock +1% | B. MA-cross at close | C. Lock + MA-cross |
| --- | ---: | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 | 6t, 50.00%, $1,777.00 | 7t, 57.14%, $2,472.70 |
| MSFT | 8t, 75.00%, $2,824.73 | 8t, 62.50%, $1,221.96 | 8t, 62.50%, $2,114.03 |
