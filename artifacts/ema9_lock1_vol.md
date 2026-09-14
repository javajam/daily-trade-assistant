# ema9_trend AAPL+MSFT: does volume>prev improve lock-+1%?

Isolate the **volume filter only**. Both books use the same lock-+1% exit. The only difference is whether the signal candle’s volume must exceed the previous candle.

- Tape: Yahoo 15m unadjusted RTH, 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70
- Exit (both): `stop_mode: lock_plus` — initial fill × 0.99; first touch of fill × 1.01 locks the stop there
- B only: **signal-bar volume > previous-bar volume** (`volume_gt_prev`)
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1_vol.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock1_vol.json --report artifacts/ema9_lock1_vol.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_vol.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_vol.json --report artifacts/ema9_aug2026_risk_lock1_vol.md`

## Verdict

**No.** Volume alone does **not** improve the lock-+1% book on this tape. Win rate is flat; P&L and drawdown get worse. The 21 baseline fills that fail `volume>prev` were **net winners** ($152.04, 13/8, 61.90%). The filter is not cutting losers.

## 1. 10-share full window

A (lock-+1%, no volume) **reproduced**: **51 trades, 60.78%, $301.49**, max DD $130.76.

B (lock-+1% + vol>prev): **33 trades, 60.61%, $182.91**, max DD $183.54. **$118.58 behind A.**

| | A. Lock +1% | B. Lock +1% + vol>prev |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 101 (AAPL 49, MSFT 52) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 14, entry_cutoff 54 |
| Trades | 51 (AAPL 23, MSFT 28) | 33 (AAPL 14, MSFT 19) |
| Wins / losses / scratch | 31 / 20 / 0 | 20 / 13 / 0 |
| **Win rate** | **60.78%** | **60.61%** |
| **Total P&L** | **$301.49 (0.301%)** | **$182.91 (0.183%)** |
| Avg win | $27.05 | $27.90 |
| Avg loss | -$26.85 | -$28.85 |
| **Max drawdown** | **$130.76 (0.13%)** | **$183.54 (0.18%)** |
| Ending equity | $100,301.49 | $100,182.91 |
| Exit mix | lock_stop 20, stop 13, session_flatten 18 | lock_stop 14, stop 9, session_flatten 10 |
| Lock armed | 20 | 14 |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); session_flatten $76.35 (18) | lock_stop $470.93 (14); stop -$332.50 (9); session_flatten $44.47 (10) |

Engine totals, not annualized. Same ~86-day Yahoo 15m window. 10 shares, $0 friction.

### Monthly (10-share)

| Month | A. Lock +1% | B. Lock +1% + vol>prev |
| --- | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $28.86 (4t, 50.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $-13.18 (14t, 57.14%) |
| 2026-08 | $304.88 (18t, 77.78%) | $200.20 (12t, 75.00%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-32.97 (3t, 33.33%) |

June is the only month B is ahead. July flips from A +$71.56 to B -$13.18. August still pays on both, but A keeps more of it.

### By symbol (10-share)

| | A. Lock +1% | B. Lock +1% + vol>prev |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 (stop 8 / lock_stop 8 / flatten 7) | 14t, 50.00%, **$-50.12** (stop 5 / lock_stop 4 / flatten 5) |
| MSFT | 28t, 67.86%, $295.12 (lock_stop 12 / flatten 11 / stop 5) | 19t, 68.42%, $233.03 (lock_stop 10 / flatten 5 / stop 4) |

Volume turns AAPL from a scratch ($6.36) into a loser. MSFT win rate is unchanged; P&L drops because some lock-stop winners fail the volume gate.

## Did volume filter out losers?

Match trades by `(symbol, signal_time)`.

| Bucket | Trades | W/L | WR | P&L | Exit mix |
| --- | ---: | ---: | ---: | ---: | --- |
| Overlap (same fill in A and B) | 30 | 18/12 | 60.00% | $149.45 | lock_stop 13 $426.12; flatten 8 $55.82; stop 9 $-332.50 |
| **Only A** (baseline fills whose signal fails vol>prev) | **21** | **13/8** | **61.90%** | **$152.04** | lock_stop 7 $258.61; flatten 10 $20.52; stop 4 $-127.10 |
| Only B (path-dependent; A was on cooldown / in the prior lot) | 3 | 2/1 | 66.67% | $33.46 | lock_stop 1 $44.81; flatten 2 $-11.35 |

A = overlap $149.45 + only-A $152.04 = $301.49. B = overlap $149.45 + only-B $33.46 = $182.91.

Of A’s 154 signals, 59 are absent from B’s matched set (AAPL 33, MSFT 26). Those 59: 21 accepted fills (the only-A bucket), 28 `entry_cutoff`, 10 `already_in_position`. B also records 6 signals A never logged — A had already fired on an earlier volume-failing bar and was in the 60-minute cooldown, so the later volume-passing setup was not evaluated on A. Three of those became the only-B fills.

**The 21 A fills volume would have blocked are net +$152.04 (WR 61.90%), slightly better than the 30 overlapping fills.** Seven of them armed the +1% lock ($258.61). Volume is dropping winners, not losers.

No overlapping A fill that passed volume was skipped by B for path reasons. The 3 only-B trades are later same-session setups that A never reached because A was still in (or cooling down from) a volume-failing lot.

## 2. August 2026 1% equity risk

Same lock-+1% stop. Size: `risk_pct` 1% of equity at a matching 1.0% fill stop (`stop_pct: 1.0`). A **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

B: **11 trades, 72.73%, $3,613.53**, max DD $1,436.03. **$1,876.25 behind A.** Win rate again flat; smaller DD because B misses three large lock-stop winners.

| | A. Lock +1% 1% risk | B. Lock +1% + vol>prev 1% risk |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 43 (AAPL 19, MSFT 24) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 21, already_in_position 10 |
| Trades | 15 (AAPL 7, MSFT 8) | 11 (AAPL 5, MSFT 6) |
| Wins / losses | 11 / 4 | 8 / 3 |
| **Win rate** | **73.33%** | **72.73%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$3,613.53 (3.614%)** |
| Avg win | $697.61 | $641.09 |
| Avg loss | -$546.00 | -$505.07 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$1,436.03 (1.40%)** |
| Ending equity | $105,489.78 | $103,613.53 |
| Exit mix | lock_stop 6, session_flatten 8, stop 1 | lock_stop 4, session_flatten 6, stop 1 |
| **Exit P&L** | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | lock_stop $3,472.58 (4); flatten $1,172.59 (6); stop -$1,031.65 (1) |
| AAPL | 7t, 71.43%, $2,665.05 | 5t, 60.00%, $364.71 |
| MSFT | 8t, 75.00%, $2,824.73 | 6t, 83.33%, $3,248.81 |

### August filled-set buckets

| Bucket | Trades | W/L | WR | P&L (A sizing) |
| --- | ---: | ---: | ---: | ---: |
| Overlap | 9 | 6/3 | 66.67% | A $2,585.27 / B $2,532.72 (qty differs slightly as equity paths diverge) |
| **Only A** (vol-rejected fills) | **6** | **5/1** | **83.33%** | **$2,904.51** |
| Only B | 2 | 2/0 | 100.00% | $1,080.80 (B sizing) |

The 6 August A fills that fail volume: MSFT 8/04 lock_stop $996.89; AAPL 8/04 lock_stop $1,007.60; AAPL 8/07 flatten $383.92; MSFT 8/14 flatten -$639.54; MSFT 8/18 flatten $117.71; AAPL 8/19 lock_stop $1,037.93. Five winners. Volume’s tighter DD is the cost of skipping those lock-stop runners.

16 A signals are absent from B (AAPL 8, MSFT 8): 6 accepted fills, 6 `entry_cutoff`, 2 `already_in_position`, 2 `insufficient_cash`.

## Configs

- A 10-share: `config/ema9_trend_bracket_nobe_lock1.example.yaml`
- B 10-share: `config/ema9_trend_bracket_nobe_lock1_vol.example.yaml`
- A 1% risk: `config/ema9_trend_risk_nobe_lock1.example.yaml`
- B 1% risk: `config/ema9_trend_risk_nobe_lock1_vol.example.yaml`

Engine dumps: `artifacts/ema9_lock1_vol.json`, `artifacts/ema9_aug2026_risk_lock1_vol.json` (August narrative also in `artifacts/ema9_aug2026_risk_lock1_vol.md`).
