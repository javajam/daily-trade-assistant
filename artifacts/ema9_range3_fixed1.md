# ema9_trend AAPL+MSFT: locked range>last-3 vs hard 1% fill stop + range>last-3 (variant F)

Same entry, gates, and universe as the locked noon day-trade book. **Same range-expansion exit.** F adds an initial hard 1% stop at fill × 0.99 (`stop_mode: entry_pct`). The stop does **not** trail or lock-at-+1%. No MA-cross. No half-take. No pyramid. No volume filter.

## Convention

- **A (locked):** `action.exit: range_expansion`, `exit_range_bars: 3`. No live percent stop.
- **F:** same range exit **plus** `stop_mode: entry_pct`, `stop_loss_pct: 1.0`. Initial stop = fill × 0.99. It never moves.
- Exit on **stop OR `range_expansion` OR flatten**, whichever first.
- **Same-bar priority:** stop is checked first. Stop + range → **stop**. Range + flatten (no stop) → **`range_expansion`** at that close.
- Range still uses high − low, strict `>`, fill at that close, not armed on the entry/fill bar.
- August 1% risk: A uses `stop_pct: 1.0` as a **reference R only**. F’s `stop_pct: 1.0` matches a **live** 1% fill stop.

- Tape: Yahoo 15m unadjusted RTH, **same cache as the locked range3 writeup** — 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z (AAPL/MSFT 1560 closed bars each; cache hit)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill at the **next bar open**.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_bracket_nobe_range3_fixed1.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_range3_fixed1.json --report artifacts/ema9_range3_fixed1.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_nobe_range3_fixed1.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_range3_fixed1.json --report artifacts/ema9_aug2026_risk_range3_fixed1.md`

Engine totals below. Not invented; not annualized.

## Reproduction

A 10-share **54 / 75.93% / $696.66** matches the locked range3 writeup on this cache. August 1% A **16 / 87.50% / $6,008.19** also matches.

## Verdict

**F does not beat A on P&L. It only slightly costs pure range3.** Protection is cheap on this tape (user priority).

10-share: A **54 / 75.93% / $696.66**, max DD $115.38. F is **55 / 74.55% / $682.32**, max DD $99.05. **$14.34 behind A.** Six `stop`s ($-219.17) replace six of A’s `range_expansion` losers; 49 remaining F exits stay `range_expansion` ($901.49). One extra AAPL fill after an early stop is **$-7.20**. Shared-fill delta **$-7.14**. No flatten on either book. No `lock_armed` / `lock_stop` on F (stop never moved).

August 2026 1% risk: **identical** — both **16 / 87.50% / $6,008.19**, max DD $2,028.83. The live 1% stop never fired. All 16 exits are `range_expansion`. Sizing matches because both books use a 1.0% R.

Locked default stays **pure range3** (no percent stop). F is the protective sibling.

## 1. 10-share full window

A **reproduced**: **54 trades, 75.93%, $696.66**, max DD $115.38. Signals 160 (AAPL 81, MSFT 79). Skips: `entry_cutoff` 92, `already_in_position` 14. Exits: **range_expansion 54 ($696.66)**.

F (range>last-3 + entry 1.0%): **55 trades, 74.55%, $682.32**, max DD $99.05. Signals 160 (AAPL 81, MSFT 79). Skips: `entry_cutoff` 93, `already_in_position` 12. Exits: **range_expansion 49 ($901.49)**; **stop 6 ($-219.17)**. Earlier stops free the one-lot slot, so `already_in_position` drops (14 → 12) and one extra AAPL fill appears.

### Side-by-side (10-share)

| | A. Locked range>last-3 | F. Range>last-3 + hard 1% |
| --- | ---: | ---: |
| Signals | 160 (AAPL 81, MSFT 79) | 160 (AAPL 81, MSFT 79) |
| Skips | already_in_position 14, entry_cutoff 92 | already_in_position 12, entry_cutoff 93 |
| Trades | 54 (AAPL 26, MSFT 28) | 55 (AAPL 27, MSFT 28) |
| Wins / losses | 41 / 13 | 41 / 14 |
| **Win rate** | **75.93%** | **74.55%** |
| **Total P&L** | **$696.66 (0.697%)** | **$682.32 (0.682%)** |
| Avg win | $25.51 | $25.51 |
| Avg loss | $-26.86 | $-25.97 |
| **Max drawdown** | **$115.38 (0.11%)** | **$99.05 (0.10%)** |
| Ending equity | $100,696.66 | $100,682.32 |
| Exit mix | range_expansion 54 | range_expansion 49, stop 6 |
| **Exit P&L** | range_expansion $696.66 (54) | range_expansion $901.49 (49); stop $-219.17 (6) |

Entry fill is next-bar open on both. Neither book used session flatten. F never armed `lock_plus` (0 `lock_armed`).

### Monthly (10-share)

| Month | A. Locked | F. Range + 1% stop |
| --- | ---: | ---: |
| 2026-06 | $128.40 (5t, 60.00%) | $128.40 (5t, 60.00%) |
| 2026-07 | $245.14 (16t, 68.75%) | $216.89 (17t, 64.71%) |
| 2026-08 | $276.41 (19t, 89.47%) | $276.41 (19t, 89.47%) |
| 2026-09 | $46.71 (14t, 71.43%) | $60.63 (14t, 71.43%) |

June and August are identical. July is where the six stops (five of them) cost P&L. September is ahead because the 09-09 AAPL stop cut a worse range loser.

### By symbol (10-share)

| | A. Locked | F. Range + 1% stop |
| --- | ---: | ---: |
| AAPL | 26t, 76.92%, $223.97 | 27t, 74.07%, $199.65 |
| MSFT | 28t, 75.00%, $472.70 | 28t, 75.00%, $482.68 |

MSFT is **+$9.98** with the stop. AAPL is **$-24.32** (the 07-17 full-1% stop plus the extra $-7.20 fill).

### What changed vs A (10-share)

All 54 A fills also fill on F. Shared-fill delta **$-7.14**. One extra F fill **$-7.20**. Net **$-14.34**.

Six shared fills exit as `stop` at fill × 0.99 (verified on each ticket). Four of those six **cut a worse range loser**. Two **cut a milder range loss into a full 1%**:

| Fill | A range | F stop | Δ |
| --- | ---: | ---: | ---: |
| MSFT 2026-07-23 13:30Z | $-57.50 at 14:15Z close | $-39.00 at 14:15Z fill×0.99 | **+$18.50** (same bar; stop beats range) |
| AAPL 2026-09-09 14:00Z | $-45.70 | $-31.79 | **+$13.91** |
| MSFT 2026-07-31 13:45Z | $-51.65 | $-46.00 | **+$5.65** |
| AAPL 2026-07-31 13:30Z | $-30.80 | $-30.48 | **+$0.32** |
| MSFT 2026-07-24 13:30Z | $-24.48 | $-38.65 | **$-14.17** |
| AAPL 2026-07-17 13:30Z | $-1.90 | $-33.25 | **$-31.35** |

Same-bar priority on this tape: **MSFT 2026-07-23** — A’s range exit and F’s stop share the 14:15Z bar. A fills the close ($384.21, $-57.50). F fills fill × 0.99 ($386.07, $-39.00). Stop wins, as documented.

Extra F-only fill: AAPL 2026-07-17 14:45Z `range_expansion` **$-7.20** (slot freed by the 13:30Z stop).

## 2. August 2026 1% equity risk

| | A. Locked 1% | F. Range + live 1% stop |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 35, already_in_position 3, insufficient_cash 3 | entry_cutoff 35, already_in_position 3, insufficient_cash 3 |
| Trades | 16 (AAPL 6, MSFT 10) | 16 (AAPL 6, MSFT 10) |
| Wins / losses | 14 / 2 | 14 / 2 |
| **Win rate** | **87.50%** | **87.50%** |
| **Total P&L** | **$6,008.19 (6.008%)** | **$6,008.19 (6.008%)** |
| Avg win | $537.84 | $537.84 |
| Avg loss | $-760.79 | $-760.79 |
| **Max drawdown** | **$2,028.83 (1.96%)** | **$2,028.83 (1.96%)** |
| Ending equity | $106,008.19 | $106,008.19 |
| Exit mix | range_expansion 16 | range_expansion 16 |
| **Exit P&L** | range_expansion $6,008.19 (16) | range_expansion $6,008.19 (16) |
| AAPL | 6t, 100.00%, $4,015.35 | 6t, 100.00%, $4,015.35 |
| MSFT | 10t, 80.00%, $1,992.85 | 10t, 80.00%, $1,992.85 |

Shared-fill delta **$0.00**. No extra fills. **0 stops.** August’s two range losers never printed a low at/below fill × 0.99, so the live stop did not change size or exit.

## Fill conventions

| Leg | When | Fill |
| --- | --- | --- |
| Entry | Signal bar closes with a valid long setup before `entry_cutoff` | **Next 15m bar open** |
| `stop` (F) | Bar low ≤ fill × 0.99 (gap-through: that bar’s open) | **Stop price** (fill × 0.99) |
| `range_expansion` | Completed bar **after the fill bar**: range > max of previous 3 | **That bar’s close** |
| `session_flatten` | Bar containing 15:55 ET if still open and no same-bar stop / close-fill exit | That bar’s close |

Same-bar stop + range expansion → **stop**. Same-bar range expansion + flatten (no stop) → **range_expansion**. F’s stop does not trail and does not lock at +1%.

Full engine dumps: `artifacts/ema9_range3_fixed1.json`, `artifacts/ema9_aug2026_risk_range3_fixed1.json`.
