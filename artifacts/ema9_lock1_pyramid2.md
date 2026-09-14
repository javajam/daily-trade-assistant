# ema9_trend AAPL+MSFT: does pyramid-on-lock + 2% take beat lock-+1%?

Same entry / gates as the lock-+1% default. B adds one lot when the +1% lock arms and takes the **entire** (doubled) position at original fill × 1.02.

- Tape: Yahoo 15m unadjusted RTH, 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. **No volume filter.**
- A exit: `stop_mode: lock_plus` — initial fill × 0.99; first touch of fill × 1.01 locks the stop there. No take. No adds.
- B additive:
  1. When the +1% lock arms, **add** the same share count as the open lot (double total shares).
  2. Add fill: bar **open** if it gaps through original fill × 1.01; otherwise the **trigger** (high tagged it). Same gap-through convention as stops.
  3. After lock, stop stays at **original fill × 1.01** on the **full** position. Locked stop is live from the **next** bar; the arm bar checks take only after the add.
  4. Take the entire position at **original fill × 1.02** (`take_anchor: entry`; exit reason `take_2pct`). If stop and take both trade on a later bar, stop wins.
  5. Session flatten if neither stop nor 2% take hits.
  6. Cash for the add is **not** reserved at entry. If cash cannot cover the add, the lock still arms and the add is skipped. Live does not auto-add.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1_pyramid2.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock1_pyramid2.json --report artifacts/ema9_lock1_pyramid2.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_pyramid2.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_pyramid2.json --report artifacts/ema9_aug2026_risk_lock1_pyramid2.md`

Engine totals below. Not invented; not annualized.

## Verdict

**No on the 10-share full window.** Pyramid+2% does **not** beat plain lock-+1%. Same 51 fills; B is **$16.70 behind** ($284.79 vs $301.49), win rate 58.82% vs 60.78%, max DD $137.13 vs $130.76.

All 20 lock-arm events **did add** (0 cash skips). Only **1** of those 20 reached `take_2pct`. The other 19 hit `lock_stop` on the doubled lot. Unarmed trades (stop / flatten) are dollar-identical to A.

August 2026 1% equity risk: B prints **$6,630.33 vs $5,489.78** with a smaller DD, but **0 of 6 lock-arm adds filled** (all skipped for cash). That book is lock-+1% **plus a 2% fill take on the original lot**, not a working pyramid. Do not credit the add.

## 1. 10-share full window

A (lock-+1%, no take, no add) **reproduced**: **51 trades, 60.78%, $301.49**, max DD $130.76.

B (lock-+1% + pyramid + 2% fill take): **51 trades, 58.82%, $284.79**, max DD $137.13. **$16.70 behind A.**

| | A. Lock +1% | B. Lock +1% pyramid/2% |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 28, entry_cutoff 75 |
| Trades | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 31 / 20 / 0 | 30 / 21 / 0 |
| **Win rate** | **60.78%** | **58.82%** |
| **Total P&L** | **$301.49 (0.301%)** | **$284.79 (0.285%)** |
| Avg win | $27.05 | $28.04 |
| Avg loss | -$26.85 | -$26.50 |
| **Max drawdown** | **$130.76 (0.13%)** | **$137.13 (0.14%)** |
| Ending equity | $100,301.49 | $100,284.79 |
| Exit mix | stop 13 / lock_stop 20 / take_2pct 0 / flatten 18 | stop 13 / lock_stop 19 / take_2pct 1 / flatten 18 |
| Lock armed | 20 | 20 |
| **Actually added** | 0 | **20** |
| Add skipped (cash) | 0 | **0** |
| Qty mix | 10 shares × 51 | 10 shares × 31 (never locked); 20 shares × 20 (added) |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); flatten $76.35 (18) | lock_stop $574.52 (19); take_2pct $93.51 (1); stop -$459.59 (13); flatten $76.35 (18) |

Same 51 `(symbol, signal_time)` fills. The 31 trades that never armed the lock are identical ($−383.25). The whole $16.70 gap is the 20 lock-armed trades: A $684.73 vs B $668.03.

What the add + 2% take did on those 20:

- **1 take_2pct** (AAPL, fill 311.69): B doubled, exited at fill × 1.02 for **$93.51**. A’s later `lock_stop` on 10 shares was **$31.17**. B +$62.34 on this name.
- **19 lock_stop on the doubled lot.** Add at ~fill × 1.01, then stop at fill × 1.01, so the add is often scratch or a small gap loss. One AAPL lock_stop that was **+$6.65** on A (10 shares, exit just above fill) becomes **−$19.50** on B (add filled, then lock_stop below the add). That one name more than offsets part of the take.

### Monthly (10-share)

| Month | A. Lock +1% | B. Lock +1% pyramid/2% |
| --- | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $-26.05 (10t, 40.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $22.12 (17t, 58.82%) |
| 2026-08 | $304.88 (18t, 77.78%) | $345.12 (18t, 77.78%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-56.40 (6t, 33.33%) |

August is the only month B is ahead (the one 2% take). July is where the doubled lock_stops hurt ($22.12 vs $71.56).

### By symbol (10-share)

| | A. Lock +1% | B. Lock +1% pyramid/2% |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 (stop 8 / lock_stop 8 / flatten 7) | 23t, 47.83%, $36.26 (stop 8 / lock_stop 7 / take_2pct 1 / flatten 7); lock 8, added 8 |
| MSFT | 28t, 67.86%, $295.12 (lock_stop 12 / flatten 11 / stop 5) | 28t, 67.86%, $248.53 (lock_stop 12 / flatten 11 / stop 5); lock 12, added 12 |

AAPL is the take winner; MSFT lock_stops on the add are net worse ($248.53 vs $295.12).

## 2. August 2026 1% equity risk

Initial lot: `shares = floor((0.01 × equity) / (0.01 × price))` ≈ **100% of equity**. The add would double that lot. Cash is **not** reserved for the add at entry.

A (lock-+1%) **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

B (same sizing + pyramid/2%): **15 trades, 73.33%, $6,630.33**, max DD $1,471.05.

| | A. Lock +1% | B. Lock +1% pyramid/2% |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, **insufficient_cash 3** | entry_cutoff 28, already_in_position 11, **insufficient_cash 2** |
| Trades | 15 (AAPL 7, MSFT 8) | 15 (AAPL 6, MSFT 9) |
| Win rate | 73.33% | 73.33% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$6,630.33 (6.630%)** |
| Avg win / avg loss | $697.61 / -$546.00 | $803.47 / -$551.96 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$1,471.05 (1.40%)** |
| Ending equity | $105,489.78 | $106,630.33 |
| Exit mix | stop 1 / lock_stop 6 / take_2pct 0 / flatten 8 | stop 1 / lock_stop 5 / take_2pct 1 / flatten 8 |
| Lock armed | 6 | 6 |
| **Actually added** | 0 | **0** |
| Add skipped (cash) | 0 | **6** |
| **Exit P&L** | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | lock_stop $4,695.46 (5); take_2pct $2,075.87 (1); flatten $928.74 (8); stop -$1,069.74 (1) |

### Cash / skip behavior (B, 1% risk)

- Initial lot consumes ~all cash (`equity_risk` 1% / `stop_pct` 1% ⇒ notional ≈ equity).
- **No cash is reserved** for the add. After the fill, leftover cash cannot cover another full lot.
- All **6** lock-arm events set `pyramid_add_skipped`. Qty never doubled.
- Entry-level `insufficient_cash` is a **different** skip (second symbol while the first risk-sized lot is open): A 3, B 2. B’s earlier 2% take freed the book, so one later MSFT fill that A missed got cash, and one later AAPL lock_stop that A took never opened on B.

### Path (not the pyramid)

Match on `(symbol, signal_time)`: 14 overlap; 1 only-A; 1 only-B.

- AAPL 2026-08-19: A `lock_stop` $1,037.93 on 333 shares → B `take_2pct` $2,075.87 on the **same 333 shares** (add skipped). That is the 2% take, not an add.
- After that exit, B is in MSFT 2026-08-19 (`lock_stop` $981.38) instead of A’s later AAPL 2026-08-25 (`lock_stop` $871.18). Later lots also size slightly larger because B’s equity is higher.

**B’s August edge is the fill-anchored 2% take plus path/sizing drift. The pyramid add never ran.**

### By symbol (August 1% risk)

| | A. Lock +1% | B. Lock +1% pyramid/2% |
| --- | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 (lock_stop 3 / flatten 3 / stop 1) | 6t, 66.67%, $2,807.95 (lock_stop 1 / take_2pct 1 / flatten 3 / stop 1); lock 2, added 0, skip 2 |
| MSFT | 8t, 75.00%, $2,824.73 (lock_stop 3 / flatten 5) | 9t, 77.78%, $3,822.38 (lock_stop 4 / flatten 5); lock 4, added 0, skip 4 |

## Modeling notes

- Take is **fill-anchored** (`take_anchor: entry`), not signal-close. A 2% take is original fill × 1.02.
- Same-bar sequence on the lock-arm bar: initial 0.99 stop only → arm lock → add → take-only. The locked 1.01 stop is **not** live on the arm bar (same convention as plain lock-+1%).
- P&L after an add uses the two-lot cost basis (original fill + add fill). Un-added lots keep the original `qty × (exit − fill)` formula so baseline A stays bit-identical ($301.49 / $5,489.78).
- `allow_pyramid` (second EMA signal) stays off. This add is intra-lot.
- Live runner does not auto-add on lock.
