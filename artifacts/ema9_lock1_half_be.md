# ema9_trend AAPL+MSFT: does half-take at +1% + BE remainder beat lock-+1% (and half+lock)?

Same entry / gates as the lock-+1% default. **No adds. No volume filter. No hard 2% take.**

- Tape: Yahoo 15m unadjusted RTH, 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Entry (all): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70
- A: `stop_mode: lock_plus` — initial fill × 0.99; first touch of fill × 1.01 locks the stop there. No take. No adds.
- B (prior): sell `floor(half)` at fill × 1.01 and **lock** the remainder there. Writeup: `artifacts/ema9_lock1_half.md`
- C (this variant):
  1. Initial stop fill × 0.99 (same as A).
  2. First touch of original fill × **1.01** sells `floor(half)`. Fill: bar **open** if it gaps through that trigger; otherwise the **trigger**. Size ≥ 2 leaves ≥1 share. Size 1 skips the partial and still arms BE.
  3. Same event rests the remainder stop at **original fill × 1.00** (break-even), **not** lock at +1%. BE stop is live from the **next** bar; same-bar pullback still uses the initial 0.99 stop.
  4. Remainder rides to `breakeven_stop` / `session_flatten` / initial stop.
  5. No hard take. No pyramid.
- Replay 10-share A/B/C: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1_half.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1_half_be.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock1_half_be.json --report artifacts/ema9_lock1_half_be.md`
- Replay August 1% A vs C: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_half_be.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_half_be.json --report artifacts/ema9_aug2026_risk_lock1_half_be.md`

Engine totals below. Not invented; not annualized.

## Verdict

**Yes vs plain lock-+1% on the 10-share tape. No vs prior half+lock. No on August 2026 1% equity risk.**

10-share: A **reproduced 51 / 60.78% / $301.49**. C is the same 51 fills and the same 60.78% win rate, **$39.03 ahead** ($340.52 vs $301.49). Prior B (half+lock) is **$341.01**. C is **$0.49 behind B** and worse on max DD ($147.09 vs B $127.57 / A $130.76).

**All 20** +1% events sold half at the **trigger** (0 gap-open scale-outs; 0 size-1 skips). Scale-out P&L is identical to B (**$381.89**). Of those 20 remainders: **5** `breakeven_stop`, **15** `session_flatten`, **0** initial stop.

August 1% risk: A **reproduced 15 / 73.33% / $5,489.78**. C is **12 / 75.00% / $3,872.16**. **Does not beat.** Risk sizing ≈ 100% of equity plus longer-held BE remainders change later cash/fills (3 fill-time cash skips vs A’s 1). C misses three AAPL trades, including two A `lock_stop`s (+$1,007.60 and +$871.18).

## 1. 10-share full window

A (lock-+1%) **reproduced**: **51 trades, 60.78%, $301.49**, max DD $130.76.

B (half + lock remainder): **51 trades, 60.78%, $341.01**, max DD $127.57.

C (half + BE remainder): **51 trades, 60.78%, $340.52**, max DD $147.09. **$39.03 ahead of A. $0.49 behind B.**

| | A. Lock +1% | B. Half + lock | C. Half + BE |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in 28, cutoff 75 | already_in 28, cutoff 75 | already_in 40, cutoff 63 |
| Trades | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 31 / 20 / 0 | 31 / 20 / 0 | 31 / 20 / 0 |
| **Win rate** | **60.78%** | **60.78%** | **60.78%** |
| **Total P&L** | **$301.49 (0.301%)** | **$341.01 (0.341%)** | **$340.52 (0.341%)** |
| Avg win | $27.05 | $28.32 | $28.31 |
| Avg loss | -$26.85 | -$26.85 | -$26.85 |
| **Max drawdown** | **$130.76 (0.13%)** | **$127.57 (0.13%)** | **$147.09 (0.15%)** |
| Ending equity | $100,301.49 | $100,341.01 | $100,340.52 |
| Exit mix | stop 13 / lock_stop 20 / flatten 18 | stop 13 / lock_stop 20 / flatten 18 | stop 13 / **be_stop 5** / flatten 33 |
| Lock armed | 20 | 20 | 0 |
| BE armed | 0 | 0 | **20** |
| **Hit +1% and sold half** | 0 | **20** ($381.89) | **20** ($381.89) |
| Partial skipped (size &lt; 2) | 0 | 0 | 0 |
| Scale-out fill | n/a | trigger 20 / gap-open 0 | trigger 20 / gap-open 0 |
| Remainder after take | n/a | lock_stop 20 | **be_stop 5 / flatten 15 / stop 0** |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); flatten $76.35 (18) | lock_stop $724.25 (20); stop -$459.59 (13); flatten $76.35 (18) | be_stop $99.96 (5); stop -$459.59 (13); flatten $700.15 (33) |

Same 51 `(symbol, signal_time)` fills. The 31 trades that never tagged +1% are dollar-identical ($−383.25). Stop P&L matches on all three books.

C’s skip mix moves (40 `already_in_position` vs 28) because the BE remainder is **not** `lock_stop`’d at +1%, so lots stay open longer. The 51 fills still match.

On the 20 half-takes, C scale-out P&L is **$381.89** (same as B) and remainder P&L is **$341.88** (B remainder $342.37). Combined C $723.76 vs B $724.25 vs A lock_stop $684.73.

C vs B on those 20: the 5 `breakeven_stop`s give back the locked +1% on the leftover 5 shares; the 15 flattens sometimes run past +1% and sometimes give it back. Net **−$0.49**.

### Monthly (10-share)

| Month | A. Lock +1% | B. Half + lock | C. Half + BE |
| --- | ---: | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $-15.10 (10t, 40.00%) | **$17.27** (10t, 40.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $96.28 (17t, 64.71%) | $99.44 (17t, 64.71%) |
| 2026-08 | $304.88 (18t, 77.78%) | $315.93 (18t, 77.78%) | $287.43 (18t, 77.78%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-56.10 (6t, 33.33%) | $-63.63 (6t, 33.33%) |

C wins June (a flatten after half-take ran) and is behind in August/September vs both A and B.

### By symbol (10-share)

| | A. Lock +1% | B. Half + lock | C. Half + BE |
| --- | ---: | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 (stop 8 / lock_stop 8 / flatten 7) | 23t, 52.17%, $22.59; half-take 8 ($125.46) | 23t, 52.17%, **$29.28** (stop 8 / be_stop 1 / flatten 14); half-take 8 ($125.46) |
| MSFT | 28t, 67.86%, $295.12 (lock_stop 12 / flatten 11 / stop 5) | 28t, 67.86%, $318.42; half-take 12 ($256.43) | 28t, 67.86%, $311.24 (be_stop 4 / flatten 19 / stop 5); half-take 12 ($256.43) |

C is the best AAPL of the three and trails B on MSFT.

## 2. August 2026 1% equity risk (A vs C)

Initial lot: `shares = floor((0.01 × equity) / (0.01 × price))` ≈ **100% of equity**. Half-take sells `floor(qty/2)`.

A (lock-+1%) **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

C (half + BE): **12 trades, 75.00%, $3,872.16**, max DD $1,721.08. **$1,617.62 behind A.**

| | A. Lock +1% | C. Half + BE |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | cutoff 28, already_in 11, insufficient_cash 3 | cutoff 27, already_in 12, insufficient_cash 4 |
| Fill-time cash skips | 1 | **3** |
| Trades | 15 (AAPL 7, MSFT 8) | 12 (AAPL 4, MSFT 8) |
| Win rate | 73.33% | 75.00% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$3,872.16 (3.872%)** |
| Avg win / avg loss | $697.61 / -$546.00 | $640.34 / -$630.29 |
| Max drawdown | $2,743.31 (2.58%) | $1,721.08 (1.65%) |
| Exit mix | stop 1 / lock_stop 6 / flatten 8 | stop 1 / **be_stop 1** / flatten 10 |
| BE armed / half-take | 0 / 0 | **4 / 4** ($2,020.55 scale-out; remainder $1,712.27) |
| Scale-out fill | n/a | trigger 4 / gap-open 0 |
| **Exit P&L** | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | be_stop $510.25 (1); flatten $4,399.91 (10); stop -$1,038.00 (1) |

C misses three AAPL fills that A took:

| A only | Exit | A P&L |
| --- | --- | ---: |
| AAPL 2026-08-04T15:45Z | lock_stop | +$1,007.60 |
| AAPL 2026-08-24T13:45Z | session_flatten | -$268.00 |
| AAPL 2026-08-26T13:30Z | lock_stop | +$871.18 |

On the 12 paired trades C is **-$6.83** vs A. The missed +$1,007.60 / +$871.18 lock_stops dominate.

### By symbol (August 1% risk)

| | A. Lock +1% | C. Half + BE |
| --- | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 | 4t, 75.00%, $1,382.40 |
| MSFT | 8t, 75.00%, $2,824.73 | 8t, 75.00%, $2,489.77 |

## Modeling notes

- Half-take fill convention matches B / stops: open if the bar opens through fill × 1.01, else the trigger. All 24 C half-takes on these tapes (20 10-share + 4 August) were **trigger** fills.
- BE stop is live **next bar**. Same-bar pullback after the +1% tag still uses the initial 0.99 stop (unit-tested).
- `lock_armed` is cleared when C converts to BE so a later hit is `breakeven_stop`, not `lock_stop`. The +1% event still happens once (`breakeven_armed`).
- Size 1 skips the partial and still arms BE (unit-tested; did not occur on these Yahoo books).
- Live runner does not auto scale-out.
- 1% risk ≈ full equity. Half-take + a longer-held BE remainder changes later cash and share counts. That path is why August C loses more trades than A (and than prior B’s 14).
