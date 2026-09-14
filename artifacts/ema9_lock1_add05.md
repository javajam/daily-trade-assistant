# ema9_trend AAPL+MSFT: does add-at-+0.5% + lock-+1% beat plain lock-+1%?

Same entry / gates as the lock-+1% default. B adds one lot at **original fill × 1.005** and still locks at **original fill × 1.01**. **No hard take.**

- Tape: Yahoo 15m unadjusted RTH, 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. **No volume filter.**
- A exit: `stop_mode: lock_plus` — initial fill × 0.99; first touch of fill × 1.01 locks the stop there. No take. No adds.
- B additive:
  1. Initial stop fill × 0.99 (same as A).
  2. First touch of original fill × **1.005** adds the same share count (double total).
  3. Add fill: bar **open** if it gaps through fill × 1.005; otherwise the **trigger** (high tagged it).
  4. First touch of original fill × **1.01** locks the stop there on the **full** position — same lock-+1% as A, after the add. Locked stop is live from the **next** bar.
  5. If a bar gaps through +1% with no earlier +0.5% print: **add first, then lock** on that bar (add at open if open ≥ 1.005, else at 1.005). Same-bar pullback still uses the initial 0.99 stop.
  6. No hard take. Exits = stop / lock_stop / session_flatten.
  7. Cash for the add is **not** reserved at entry. A cash skip is attempted once; the lock can still arm. Live does not auto-add.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1_add05.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock1_add05.json --report artifacts/ema9_lock1_add05.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_add05.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_add05.json --report artifacts/ema9_aug2026_risk_lock1_add05.md`

Engine totals below. Not invented; not annualized.

## Verdict

**No.** Add-at-+0.5% + lock-+1% does **not** beat plain lock-+1% on the 10-share full window. Same 51 fills; B is **$36.17 behind** ($265.32 vs $301.49), win rate 54.90% vs 60.78%, max DD $220.96 vs $130.76.

**35** trades tagged +0.5% and **all 35 added** (0 cash skips). **20** of those then locked at +1%. **15** added and never locked (11 flatten / 4 stop on the doubled lot). **0** locked without an add.

August 2026 1% equity risk is **identical** to A ($5,489.78, 15 trades, 73.33%). **0 of 13** +0.5% tags added (all cash-skipped). The add never ran; the lock book is unchanged.

## 1. 10-share full window

A (lock-+1%, no add) **reproduced**: **51 trades, 60.78%, $301.49**, max DD $130.76.

B (add @ +0.5%, lock @ +1%, no take): **51 trades, 54.90%, $265.32**, max DD $220.96. **$36.17 behind A.**

| | A. Lock +1% | B. Lock +1% add@0.5% |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 28, entry_cutoff 75 |
| Trades | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 31 / 20 / 0 | 28 / 23 / 0 |
| **Win rate** | **60.78%** | **54.90%** |
| **Total P&L** | **$301.49 (0.301%)** | **$265.32 (0.265%)** |
| Avg win | $27.05 | $39.94 |
| Avg loss | -$26.85 | -$37.09 |
| **Max drawdown** | **$130.76 (0.13%)** | **$220.96 (0.22%)** |
| Ending equity | $100,301.49 | $100,265.32 |
| Exit mix | stop 13 / lock_stop 20 / flatten 18 | stop 13 / lock_stop 20 / flatten 18 |
| Lock armed | 20 | 20 |
| **Hit +0.5% and added** | 0 | **35** |
| Added then locked | 0 | **20** |
| Added, never locked | 0 | **15** (flatten 11 / stop 4) |
| Locked without add | 0 | **0** |
| Add skipped (cash) | 0 | **0** |
| Qty mix | 10 shares × 51 | 10 shares × 16 (never tagged +0.5%); 20 shares × 35 |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); flatten $76.35 (18) | lock_stop $987.58 (20); stop -$670.16 (13); flatten -$52.10 (18) |

Same 51 `(symbol, signal_time)` fills. The 16 trades that never tagged +0.5% are dollar-identical ($−339.94). The whole $36.17 gap is the 35 added trades: A $641.43 vs B $605.26.

Lock_stops on the doubled lot pay more ($987.58 vs $684.73) — the add is in at ~+0.5% and out at +1%. That gain is more than given back on the 15 adds that never lock: flatten flips from +$76.35 to −$52.10, and stops from −$459.59 to −$670.16 (the extra 10 shares ride the initial 0.99 stop or the flatten print).

### Monthly (10-share)

| Month | A. Lock +1% | B. Lock +1% add@0.5% |
| --- | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $-40.25 (10t, 40.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $0.25 (17t, 58.82%) |
| 2026-08 | $304.88 (18t, 77.78%) | $359.22 (18t, 72.22%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-53.90 (6t, 16.67%) |

August is the only month B is ahead (more lock_stops on the add). July is nearly scratched vs A +$71.56.

### By symbol (10-share)

| | A. Lock +1% | B. Lock +1% add@0.5% |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 (stop 8 / lock_stop 8 / flatten 7) | 23t, 47.83%, **$-64.51** (stop 8 / lock_stop 8 / flatten 7); lock 8, added 14 |
| MSFT | 28t, 67.86%, $295.12 (lock_stop 12 / flatten 11 / stop 5) | 28t, 60.71%, $329.83 (lock_stop 12 / flatten 11 / stop 5); lock 12, added 21 |

MSFT lock_stops on the add are net better; AAPL’s extra adds that never lock turn a scratch into a loser.

## 2. August 2026 1% equity risk

Initial lot: `shares = floor((0.01 × equity) / (0.01 × price))` ≈ **100% of equity**. The add would double that lot. Cash is **not** reserved for the add at entry.

A (lock-+1%) **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

B (same sizing + add@0.5%): **15 trades, 73.33%, $5,489.78**, max DD $2,743.31. **Identical book.**

| | A. Lock +1% | B. Lock +1% add@0.5% |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 |
| Trades | 15 (AAPL 7, MSFT 8) | 15 (AAPL 7, MSFT 8) |
| Win rate | 73.33% | 73.33% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$5,489.78 (5.490%)** |
| Max drawdown | $2,743.31 (2.58%) | $2,743.31 (2.58%) |
| Exit mix | stop 1 / lock_stop 6 / flatten 8 | stop 1 / lock_stop 6 / flatten 8 |
| Lock armed | 6 | 6 |
| **Hit +0.5%** | n/a | **13** |
| **Actually added** | 0 | **0** |
| Add skipped (cash) | 0 | **13** |
| Locked without add | 0 | **6** |

### Cash / skip behavior (B, 1% risk)

- Initial lot consumes ~all cash.
- **13** trades tagged +0.5% and **all 13** skipped the add (`insufficient_cash` on the add). Qty never doubled.
- **6** of those later locked at +1% on the original lot — same lock_stops as A.
- **2** trades never tagged +0.5% (no add attempt).
- Entry-level `insufficient_cash` (second symbol while the first risk-sized lot is open) is unchanged: **3** on both books.
- No take, so path and sizing do not drift. A and B are the same 15 fills and the same P&L.

## Modeling notes

- Add trigger and lock trigger are separate (`pyramid_add_pct: 0.5`, `lock_trigger_pct: 1.0`).
- Same-bar gap through +1%: initial 0.99 stop check → add at open (or 1.005 if open is still below) → arm lock. Locked stop is **not** live on that bar.
- P&L after an add uses the two-lot cost basis. Un-added lots keep `qty × (exit − fill)` so baseline A stays bit-identical ($301.49 / $5,489.78).
- `allow_pyramid` (second EMA signal) stays off. This add is intra-lot.
- Live runner does not auto-add.
