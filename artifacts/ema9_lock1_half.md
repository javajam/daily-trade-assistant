# ema9_trend AAPL+MSFT: does half-take at +1% + lock remainder beat plain lock-+1%?

Same entry / gates as the lock-+1% default. **No adds. No volume filter. No hard 2% take.** B sells half at **original fill × 1.01** and locks the remainder there.

- Tape: Yahoo 15m unadjusted RTH, 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70
- A exit: `stop_mode: lock_plus` — initial fill × 0.99; first touch of fill × 1.01 locks the stop there. No take. No adds.
- B additive:
  1. Initial stop fill × 0.99 (same as A).
  2. First touch of original fill × **1.01** sells `floor(half)` the open shares. Fill: bar **open** if it gaps through that trigger; otherwise the **trigger** (high tagged it). Size ≥ 2 leaves at least 1 share. Size 1 skips the partial and still locks.
  3. Same event locks the stop at original fill × 1.01 on the **remaining** shares. Locked stop is live from the **next** bar.
  4. Remainder rides to `lock_stop` / `session_flatten` / initial stop.
  5. No hard take. No pyramid.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_lock1_half.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock1_half.json --report artifacts/ema9_lock1_half.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lock1_half.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_half.json --report artifacts/ema9_aug2026_risk_lock1_half.md`

Engine totals below. Not invented; not annualized.

## Verdict

**Yes on the 10-share tape that defines the baseline. No on August 2026 1% equity risk.**

10-share full window: A **reproduced 51 / 60.78% / $301.49**. B is the same 51 fills and the same 60.78% win rate, **$39.52 ahead** ($341.01 vs $301.49), max DD $127.57 vs $130.76. **All 20** lock-arm events sold half at the +1% **trigger** (0 gap-through opens on the scale-out; 0 size-1 skips). The entire dollar gap is 8 `lock_stop`s where the remainder gapped through the locked print — A dumped all 10 at that worse open; B had already banked 5 at +1%.

August 1% risk: A **reproduced 15 / 73.33% / $5,489.78**. B is **14 / 71.43% / $4,799.30**, max DD $2,081.26 vs $2,743.31. **Does not beat.** Risk sizing ≈ 100% of equity: B’s earlier half-takes lift equity, so the next lot can size +1 share and then fail the next-open cash check. B has **2** fill-time cash skips vs A’s **1**. The extra miss is AAPL 2026-08-26 (A `lock_stop` **+$871.18**). On the 14 paired trades B is **$180.70 ahead**; the missed fill more than wipes that.

## 1. 10-share full window

A (lock-+1%, no partial) **reproduced**: **51 trades, 60.78%, $301.49**, max DD $130.76.

B (half at +1%, lock remainder): **51 trades, 60.78%, $341.01**, max DD $127.57. **$39.52 ahead of A.**

| | A. Lock +1% | B. Lock +1% half-take |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 28, entry_cutoff 75 |
| Trades | 51 (AAPL 23, MSFT 28) | 51 (AAPL 23, MSFT 28) |
| Wins / losses / scratch | 31 / 20 / 0 | 31 / 20 / 0 |
| **Win rate** | **60.78%** | **60.78%** |
| **Total P&L** | **$301.49 (0.301%)** | **$341.01 (0.341%)** |
| Avg win | $27.05 | $28.32 |
| Avg loss | -$26.85 | -$26.85 |
| **Max drawdown** | **$130.76 (0.13%)** | **$127.57 (0.13%)** |
| Ending equity | $100,301.49 | $100,341.01 |
| Exit mix | stop 13 / lock_stop 20 / flatten 18 | stop 13 / lock_stop 20 / flatten 18 |
| Lock armed | 20 | 20 |
| **Hit +1% and sold half** | 0 | **20** ($381.89 scale-out P&L) |
| Partial skipped (size &lt; 2) | 0 | **0** |
| Scale-out fill | n/a | trigger 20 / gap-open 0 |
| Remainder after take | n/a | lock_stop 20 / flatten 0 / stop 0 |
| Qty mix | 10 shares × 51 | 10 shares × 31 (never locked); 5 remaining × 20 |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); flatten $76.35 (18) | lock_stop $724.25 (20); stop -$459.59 (13); flatten $76.35 (18) |

Same 51 `(symbol, signal_time)` fills. The 31 trades that never locked are dollar-identical ($−383.25). Stop and flatten P&L match. The whole $39.52 gap is the 20 locked trades: A $684.73 vs B $724.25.

On those 20, B scale-out P&L is **$381.89** (5 shares at fill × 1.01) and remainder P&L is **$342.37** (5 shares to `lock_stop`). Combined $724.25.

- **12 / 20** remainder also exits at exactly fill × 1.01 → same dollar P&L as A’s full 10-share `lock_stop`.
- **8 / 20** remainder `lock_stop` fills **below** the lock (gap through the locked print). A exits all 10 at that worse open. B already sold 5 at the trigger.

| Date | Symbol | A lock_stop | B combined | B − A |
| --- | --- | ---: | ---: | ---: |
| 2026-06-26 | MSFT | $29.75 | $32.94 | +$3.19 |
| 2026-06-30 | AAPL | $27.40 | $27.86 | +$0.46 |
| 2026-07-13 | MSFT | $33.10 | $36.02 | +$2.92 |
| 2026-07-15 | MSFT | $21.30 | $30.02 | +$8.72 |
| 2026-07-16 | AAPL | $6.65 | $19.73 | +$13.07 |
| 2026-08-06 | MSFT | $32.40 | $40.86 | +$8.46 |
| 2026-08-26 | AAPL | $25.85 | $28.44 | +$2.59 |
| 2026-09-03 | AAPL | $32.45 | $32.55 | +$0.10 |
| **8 trades** | | | | **+$39.52** |

Largest lift is AAPL 2026-07-16: lock 331.285, remainder / A fill 328.670.

### Monthly (10-share)

| Month | A. Lock +1% | B. Lock +1% half-take |
| --- | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $-15.10 (10t, 40.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $96.28 (17t, 64.71%) |
| 2026-08 | $304.88 (18t, 77.78%) | $315.93 (18t, 77.78%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-56.10 (6t, 33.33%) |

B is ahead or flat every month. July is the bulk of the gap (more gapped `lock_stop`s after the half-take).

### By symbol (10-share)

| | A. Lock +1% | B. Lock +1% half-take |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 (stop 8 / lock_stop 8 / flatten 7) | 23t, 52.17%, $22.59 (stop 8 / lock_stop 8 / flatten 7); half-take 8 ($125.46) |
| MSFT | 28t, 67.86%, $295.12 (lock_stop 12 / flatten 11 / stop 5) | 28t, 67.86%, $318.42 (lock_stop 12 / flatten 11 / stop 5); half-take 12 ($256.43) |

Both names keep the same win rate. AAPL is no longer a scratch.

## 2. August 2026 1% equity risk

Initial lot: `shares = floor((0.01 × equity) / (0.01 × price))` ≈ **100% of equity**. Half-take sells `floor(qty/2)`; odd lots leave the extra share on the remainder.

A (lock-+1%) **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

B (same sizing + half-take): **14 trades, 71.43%, $4,799.30**, max DD $2,081.26. **$690.48 behind A.**

| | A. Lock +1% | B. Lock +1% half-take |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 |
| Fill-time cash skips (accepted signal, no fill) | 1 | **2** |
| Trades | 15 (AAPL 7, MSFT 8) | 14 (AAPL 6, MSFT 8) |
| Win rate | 73.33% | 71.43% |
| **Total P&L** | **$5,489.78 (5.490%)** | **$4,799.30 (4.799%)** |
| Avg win / avg loss | $697.61 / -$546.00 | $698.63 / -$546.76 |
| Max drawdown | $2,743.31 (2.58%) | $2,081.26 (1.97%) |
| Exit mix | stop 1 / lock_stop 6 / flatten 8 | stop 1 / lock_stop 5 / flatten 8 |
| Lock armed | 6 | 5 |
| **Hit +1% and sold half** | 0 | **5** ($2,547.08 scale-out; remainder $2,384.08) |
| Partial skipped (size &lt; 2) | 0 | **0** |
| Scale-out fill | n/a | trigger 5 / gap-open 0 |
| **Exit P&L** | lock_stop $5,623.20 (6); flatten $917.28 (8); stop -$1,050.69 (1) | lock_stop $4,931.16 (5); flatten $918.83 (8); stop -$1,050.69 (1) |

### Missing fill (AAPL 2026-08-26)

B accepted the same AAPL signal at 2026-08-25T20:00:00Z. Next-open fill (2026-08-26T13:30:00Z) was **skipped for cash**. A filled 337 shares and `lock_stop`’d for **+$871.18**. That is the sixth A lock and the whole trade-count gap.

On the **14 paired** trades B is **+$180.70** vs A (largest: MSFT 2026-08-06 `lock_stop` +$176.03 — same gapped-remainder pattern as the 10-share book). Flatten/stop share counts also drift with equity, so never-locked P&L is not dollar-identical.

### By symbol (August 1% risk)

| | A. Lock +1% | B. Lock +1% half-take |
| --- | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 (lock_stop 3 / flatten 3 / stop 1) | 6t, 66.67%, $1,796.98 (lock_stop 2 / flatten 3 / stop 1); half-take 2 ($1,022.79) |
| MSFT | 8t, 75.00%, $2,824.73 (lock_stop 3 / flatten 5) | 8t, 75.00%, $3,002.31 (lock_stop 3 / flatten 5); half-take 3 ($1,524.29) |

MSFT half-take is ahead. AAPL is behind because of the missed Aug 26 lock_stop.

### Odd-lot half-takes (B)

| Date | Symbol | Open qty | Sold | Remainder |
| --- | ---: | ---: | ---: | ---: |
| 2026-08-04 | MSFT | 203 | 101 | 102 |
| 2026-08-04 | AAPL | 329 | 164 | 165 |
| 2026-08-06 | MSFT | 208 | 104 | 104 |
| 2026-08-10 | MSFT | 205 | 102 | 103 |
| 2026-08-19 | AAPL | 334 | 167 | 167 |

## Modeling notes

- One Trade per entry. Combined P&L = scale-out + remainder. `qty` on the closed trade is remaining shares.
- Partial fill convention matches stops/adds: open if the bar opens through fill × 1.01, else the trigger. This tape’s 25 half-takes (20 10-share + 5 August) were all **trigger** fills.
- Locked stop is live next bar. Same-bar pullback after the tag still uses the initial 0.99 stop; the remainder is not `lock_stop`’d on the arm bar.
- If the flatten bar is the first +1% tag, lock manage runs before `session_flatten`: half is sold, remainder flats at that close. No such 10-share case here (all 20 remainders `lock_stop`’d).
- Size 1 skips the partial and still locks (unit-tested; did not occur on these Yahoo books).
- Live runner does not auto scale-out.
- 1% risk ≈ full equity. A half-take changes later cash and share counts. That path — not a worse scale-out rule — is why August B loses.
