# August 2026 1% equity risk: lock-+1% vs EMA9×below SMA20 at close

Companion to `artifacts/ema9_lock1_macross.md`. Same Yahoo 15m AAPL+MSFT tape, `--start 2026-08-01 --end 2026-08-31`. A sizes 1% of equity at the live 1.0% fill stop. B has **no live percent stop**; share count uses `stop_pct: 1.0` as a **reference R only** (1% of entry): `shares = floor((0.01 × equity) / (0.01 × price))`.

Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_macross.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_macross.json --report artifacts/ema9_aug2026_risk_lock1_macross.md`

Engine totals. Not invented.

## Verdict

**No.** EMA9×below SMA20 at close does **not** beat plain lock-+1% on this August 1% risk book.

A **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

B: **14 trades, 57.14%, $2,998.96**, max DD $2,510.94. **$2,490.82 behind.**

B missed AAPL 2026-08-04 15:45Z (A `lock_stop` **+$1,007.60**) — still in MSFT until the flatten-bar pair-cross, so AAPL failed the cash check. On the 14 paired fills B is still **$1,483.22 behind**.

Cross is EMA vs SMA close-to-close. Fill at that bar’s close. If EMA-cross and flatten fall on the same bar, `ma_cross` at that close wins (here: MSFT 2026-08-04 15:45 ET, +$353.22).

## Side-by-side

| | A. Lock +1% | B. MA-cross at close |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 28, already_in_position 11, insufficient_cash 4 |
| Fill-time cash skips | 1 | 1 |
| Trades | 15 (AAPL 7, MSFT 8) | 14 (AAPL 6, MSFT 8) |
| Wins / losses / scratch | 11 / 4 / 0 | 8 / 6 / 0 |
| Win rate | 73.33% | 57.14% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$2,998.96 (2.999%)** |
| Avg win / avg loss | $697.61 / -$546.00 | $604.79 / -$306.56 |
| Max drawdown | $2,743.31 (2.58%) | $2,510.94 (2.44%) |
| Qty | 203–337 | 200–328 (reference R = 1% of entry; no live stop) |
| Exit mix | lock_stop 6, session_flatten 8, stop 1 | ma_cross 10, session_flatten 4 |
| Exit P&L | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | ma_cross $-75.78 (10); flatten $3,074.74 (4) |

### By symbol

| | A. Lock +1% | B. MA-cross at close |
| --- | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 | 6t, 50.00%, $1,777.00 |
| MSFT | 8t, 75.00%, $2,824.73 | 8t, 62.50%, $1,221.96 |
