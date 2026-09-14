# ema9_trend AAPL+MSFT: does lock-+1% + EMA9×below SMA20 at close beat plain lock and/or pure MA-cross?

Same entry / gates as the lock-+1% default. **No volume filter. No half-take. No pyramid.** C runs **both** exits: lock-+1% **and** MA-cross at that bar’s close. Whichever hits first wins.

- Tape: Yahoo 15m unadjusted RTH, 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- Entry (all): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70
- A: `stop_mode: lock_plus` only — initial fill × 0.99; first touch of fill × 1.01 locks the stop there. No take.
- B: `action.exit: ma_cross_close` only — EMA vs SMA close-to-close; fill at that bar’s close. No live % stop.
- C: **both** A’s lock-+1% **and** B’s MA-cross at close.
  1. Initial stop fill × 0.99; first touch of fill × 1.01 locks the stop there (live next bar).
  2. EMA(9) crosses below SMA(20) on a completed bar → exit at that close (`ma_cross`).
  3. Session flatten 15:55 ET.
  Same-bar priority: **stop / `lock_stop` is checked first** and beats the pair-cross. Same-bar lock-arm + pair-cross (low above the live stop) exits as `ma_cross` and does not arm. Flatten-bar pair-cross still wins over `session_flatten`.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_macross.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1_macross.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock1_plus_macross.json --report artifacts/ema9_lock1_plus_macross.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_macross.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_macross.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_plus_macross.json --report artifacts/ema9_aug2026_risk_lock1_plus_macross.md`

August 1% risk: A and C size off the live 1.0% fill stop (`stop_pct: 1.0` matches `stop_loss_pct`). B has no live stop and uses `stop_pct: 1.0` as a **reference R only**.

Engine totals below. Not invented; not annualized.

## Verdict

**No vs plain lock-+1%. No vs pure MA-cross on the 10-share tape. Yes vs pure MA-cross on August 1% risk (still behind lock-+1%).**

10-share: A **reproduced 51 / 60.78% / $301.49**. B **reproduced 50 / 56.00% / $427.81**. C is **51 / 54.90% / $296.62**, max DD $106.37. C is **$4.87 behind A** and **$131.19 behind B**. Tightest drawdown of the three.

August 1% risk: A **reproduced 15 / 73.33% / $5,489.78**. B **reproduced 14 / 57.14% / $2,998.96**. C is **15 / 60.00% / $4,586.73**, max DD $1,915.59. C is **$903.05 behind A** and **$1,587.77 ahead of B** (C kept A’s `lock_stop`s, including AAPL 2026-08-04 +$1,007.60 that B cash-skipped).

## 1. 10-share full window

| | A. Lock +1% | B. MA-cross at close | C. Lock + MA-cross |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 35, entry_cutoff 69 | already_in_position 18, entry_cutoff 85 |
| Trades | 51 (AAPL 23, MSFT 28) | 50 (AAPL 22, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 31 / 20 / 0 | 28 / 22 / 0 | 28 / 23 / 0 |
| **Win rate** | **60.78%** | **56.00%** | **54.90%** |
| **Total P&L** | **$301.49 (0.301%)** | **$427.81 (0.428%)** | **$296.62 (0.297%)** |
| Avg win | $27.05 | $30.99 | $27.44 |
| Avg loss | -$26.85 | -$19.99 | -$20.51 |
| **Max drawdown** | **$130.76 (0.13%)** | **$147.68 (0.15%)** | **$106.37 (0.11%)** |
| Ending equity | $100,301.49 | $100,427.81 | $100,296.62 |
| Lock armed | 20 | 0 | 20 |
| Exit mix | lock_stop 20, stop 13, flatten 18 | ma_cross 37, flatten 13 | lock_stop 20, ma_cross 19, stop 7, flatten 5 |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); flatten $76.35 (18) | ma_cross $-123.01 (37); flatten $550.83 (13) | lock_stop $684.73 (20); ma_cross $-202.82 (19); stop $-249.22 (7); flatten $63.92 (5) |

C matches A’s 51 fills and A’s 20 `lock_stop`s **dollar-for-dollar** ($684.73). Adding MA-cross does not change locked trades (lock_stop is checked first; those lots already locked).

A → C reason map on the same 51 fills:

| A exit → C exit | n |
| --- | ---: |
| lock_stop → lock_stop | 20 |
| stop → stop | 7 |
| stop → ma_cross | 6 |
| session_flatten → ma_cross | 13 |
| session_flatten → session_flatten | 5 |

The MA-cross fire is **earlier in the trade**, not a same-bar override of a stop (stop still wins when both print on one bar). Six A `stop`s become earlier `ma_cross` cuts (usually smaller losses). Thirteen A flattens become `ma_cross` (cuts some winners — AAPL 2026-08-05 flatten +$20.70 → `ma_cross` -$5.85). Net **-$4.87 vs A**.

B’s edge vs A/C is the **unprotected flatten runners** ($550.83) plus no hard 1% stop. C keeps the 1% stop / lock and therefore cannot keep those B flatten rides.

### Monthly (10-share)

| Month | A. Lock +1% | B. MA-cross at close | C. Lock + MA-cross |
| --- | ---: | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $68.26 (10t, 40.00%) | $-4.94 (10t, 40.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $235.45 (16t, 62.50%) | $76.02 (17t, 58.82%) |
| 2026-08 | $304.88 (18t, 77.78%) | $192.46 (18t, 66.67%) | $266.43 (18t, 66.67%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-68.35 (6t, 33.33%) | $-40.89 (6t, 33.33%) |

B wins June–July. A wins August. C is between A and B in June and behind both in August.

### By symbol (10-share)

| | A. Lock +1% | B. MA-cross at close | C. Lock + MA-cross |
| --- | ---: | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 | 22t, 50.00%, $129.13 | 23t, 47.83%, $35.19 |
| MSFT | 28t, 67.86%, $295.12 | 28t, 60.71%, $298.68 | 28t, 60.71%, $261.43 |

## 2. August 2026 1% equity risk

| | A. Lock +1% | B. MA-cross at close | C. Lock + MA-cross |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 28, already_in_position 11, insufficient_cash 4 | entry_cutoff 32, already_in_position 7, insufficient_cash 3 |
| Fill-time cash skips | 1 | 1 | 1 |
| Trades | 15 (AAPL 7, MSFT 8) | 14 (AAPL 6, MSFT 8) | 15 (AAPL 7, MSFT 8) |
| Wins / losses / scratch | 11 / 4 / 0 | 8 / 6 / 0 | 9 / 6 / 0 |
| **Win rate** | **73.33%** | **57.14%** | **60.00%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$2,998.96 (2.999%)** | **$4,586.73 (4.587%)** |
| Avg win | $697.61 | $604.79 | $717.43 |
| Avg loss | -$546.00 | -$306.56 | -$311.70 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$2,510.94 (2.44%)** | **$1,915.59 (1.83%)** |
| Ending equity | $105,489.78 | $102,998.96 | $104,586.73 |
| Qty | 203–337 | 200–328 (reference R) | 202–334 |
| Lock armed | 6 | 0 | 6 |
| Exit mix | lock_stop 6, flatten 8, stop 1 | ma_cross 10, flatten 4 | lock_stop 6, ma_cross 7, flatten 2 |
| **Exit P&L** | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | ma_cross $-75.78 (10); flatten $3,074.74 (4) | lock_stop $5,578.22 (6); ma_cross $-1,680.42 (7); flatten $688.93 (2) |

C matches A’s 15 fills (including AAPL 2026-08-04 `lock_stop` +$1,007.60 that B missed). Six A flattens become `ma_cross` (AAPL 2026-08-05 flatten +$683.10 → `ma_cross` -$193.05). One A `stop` -$1,050.69 becomes `ma_cross` -$269.75. Net **-$903.05 vs A**. C still beats B because it keeps the lock_stops.

A → C on the same 15 fills: lock_stop→lock_stop 6; flatten→ma_cross 6; flatten→flatten 2; stop→ma_cross 1.

### By symbol (August 1% risk)

| | A. Lock +1% | B. MA-cross at close | C. Lock + MA-cross |
| --- | ---: | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 | 6t, 50.00%, $1,777.00 | 7t, 57.14%, $2,472.70 |
| MSFT | 8t, 75.00%, $2,824.73 | 8t, 62.50%, $1,221.96 | 8t, 62.50%, $2,114.03 |

## Configs

- A 10-share: `config/ema9_trend_bracket_nobe_lock1.example.yaml`
- B 10-share: `config/ema9_trend_bracket_nobe_macross.example.yaml`
- C 10-share: `config/ema9_trend_bracket_nobe_lock1_macross.example.yaml`
- A 1% risk: `config/ema9_trend_risk_nobe_lock1.example.yaml`
- B 1% risk: `config/ema9_trend_risk_nobe_macross.example.yaml`
- C 1% risk: `config/ema9_trend_risk_nobe_lock1_macross.example.yaml`
