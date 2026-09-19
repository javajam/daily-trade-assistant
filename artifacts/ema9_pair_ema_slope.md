# ema9_trend AAPL+MSFT: locked book vs pair-cross + EMA9 flat/rising (variant C)

Same exit, gates, and universe as the locked noon day-trade book. **No RSI. No price-cross-above-EMA9. No SMA20 slope. No lock-+1% / percent stop / half-take / pyramid / volume filter.** C enters when **EMA(9) crosses above SMA(20)** close-to-close **and** EMA(9) on the signal bar is flat or rising.

Prior variant B (SMA20 flat/rising on the same pair-cross) is included for the delta. B lost to A on this tape (`artifacts/ema9_pair_slope.md`).

- Tape: Yahoo 15m unadjusted RTH, **same cache as the B run** — 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z (AAPL/MSFT 1560 closed bars each; cache hit)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- A entry (locked): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill at the **next bar open**.
- B entry (prior): EMA(9)×above SMA(20) close-to-close AND SMA20[curr] ≥ SMA20[prev]. Fill next bar open.
- C entry (this run):
  1. EMA(9) crosses above SMA(20) close-to-close: prev EMA ≤ prev SMA and curr EMA > curr SMA — the inverse of `ma_cross_close`.
  2. EMA(9) flat or rising: EMA9[curr] ≥ EMA9[prev] (`ema_slope` `compare: flat_or_rising`).
  3. SMA20 slope is **not** required. No RSI. No price×EMA9.
  4. Fill at the **next bar open** (same as A and B).
- Exit (all): EMA(9) crosses below SMA(20) close-to-close; fill at **that bar’s close** (`action.exit: ma_cross_close`).
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_bracket_nobe_pair_slope.example.yaml --compare-config config/ema9_trend_bracket_nobe_pair_ema_slope.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_pair_ema_slope.json --report artifacts/ema9_pair_ema_slope.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_nobe_pair_slope.example.yaml --compare-config config/ema9_trend_risk_nobe_pair_ema_slope.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_pair_ema_slope.json --report artifacts/ema9_aug2026_risk_pair_ema_slope.md`

August 1% risk sizes all books with `stop_pct: 1.0` as a **reference R only**. No live 1% stop.

Engine totals below. Not invented; not annualized.

## Reproduction

A 10-share **50 / 58.00% / $560.31** and B **34 / 58.82% / $381.18** match the prior PR on this cache. August 1% A **14 / 57.14% / $2,998.96** and B **10 / 70.00% / $1,504.39** also match.

## Verdict

**C does not beat the locked book.**

10-share: A **50 / 58.00% / $560.31**. C is **42 / 59.52% / $445.10**, max DD $126.75 vs $147.68. **$115.21 behind A.** C does beat prior B ($381.18) on this window ($63.92 ahead) by taking more pair-crosses (signals 46 → 91). That is not enough to catch A’s flatten runners.

August 2026 1% risk: A **14 / 57.14% / $2,998.96**. C is **12 / 66.67% / $1,026.54**, max DD $2,879.23 vs $2,510.94. **Does not beat** ($1,972.42 behind A; also **behind B**). C still missed MSFT 2026-08-06 `session_flatten` **+$1,337.77**. Extra pair-crosses vs B include AAPL 2026-08-20 `ma_cross` **$-588.44** and AAPL 2026-08-27 **$-346.11**.

## 1. 10-share full window

A **reproduced**: **50 trades, 58.00%, $560.31**, max DD $147.68. Signals 160. Skips: `entry_cutoff` 69, `already_in_position` 41. Exits: **ma_cross 35 ($-118.06)**, **session_flatten 15 ($678.37)**.

B **reproduced**: **34 trades, 58.82%, $381.18**, max DD $124.44. Signals 46. Skips: `entry_cutoff` 12. Exits: **ma_cross 26 ($81.83)**, **session_flatten 8 ($299.35)**.

C (EMA9 flat/rising): **42 trades, 59.52%, $445.10**, max DD $126.75. Signals 91 (AAPL 49, MSFT 42). Skips: `entry_cutoff` 49. Exits: **ma_cross 30 ($55.28)**, **session_flatten 12 ($389.83)**.

### Side-by-side (10-share)

| | A. Locked | B. Pair-cross + SMA20 slope | C. Pair-cross + EMA9 slope |
| --- | ---: | ---: | ---: |
| Signals | 160 (AAPL 81, MSFT 79) | 46 (AAPL 25, MSFT 21) | 91 (AAPL 49, MSFT 42) |
| Skips | already_in_position 41, entry_cutoff 69 | entry_cutoff 12 | entry_cutoff 49 |
| Trades | 50 (AAPL 23, MSFT 27) | 34 (AAPL 19, MSFT 15) | 42 (AAPL 24, MSFT 18) |
| Wins / losses | 29 / 21 | 20 / 14 | 25 / 17 |
| **Win rate** | **58.00%** | **58.82%** | **59.52%** |
| **Total P&L** | **$560.31 (0.560%)** | **$381.18 (0.381%)** | **$445.10 (0.445%)** |
| Avg win | $33.60 | $30.25 | $28.28 |
| Avg loss | $-19.71 | $-15.99 | $-15.41 |
| **Max drawdown** | **$147.68 (0.15%)** | **$124.44 (0.12%)** | **$126.75 (0.13%)** |
| Ending equity | $100,560.31 | $100,381.18 | $100,445.10 |
| Exit mix | ma_cross 35, flatten 15 | ma_cross 26, flatten 8 | ma_cross 30, flatten 12 |
| **Exit P&L** | ma_cross $-118.06 (35); flatten $678.37 (15) | ma_cross $81.83 (26); flatten $299.35 (8) | ma_cross $55.28 (30); flatten $389.83 (12) |

Entry fill is next-bar open on all three; exit fill is the completed cross bar’s close. 10 shares, $0 friction.

### Monthly (10-share)

| Month | A. Locked | B. SMA slope | C. EMA slope |
| --- | ---: | ---: | ---: |
| 2026-06 | $111.01 (5t, 60.00%) | $-22.75 (1t, 0.00%) | $-30.42 (2t, 0.00%) |
| 2026-07 | $235.45 (16t, 62.50%) | $395.00 (13t, 76.92%) | $460.40 (16t, 81.25%) |
| 2026-08 | $192.46 (18t, 66.67%) | $48.08 (11t, 63.64%) | $54.28 (15t, 60.00%) |
| 2026-09 | $21.40 (11t, 36.36%) | $-39.15 (9t, 33.33%) | $-39.15 (9t, 33.33%) |

July is where C (and B) beat A. August and June still favor the locked price-cross book. September C matches B exactly (9t / $-39.15).

### By symbol (10-share)

| | A. Locked | B. SMA slope | C. EMA slope |
| --- | ---: | ---: | ---: |
| AAPL | 23t, 52.17%, $178.08 | 19t, 47.37%, $160.73 | 24t, 50.00%, $189.05 |
| MSFT | 27t, 62.96%, $382.23 | 15t, 73.33%, $220.45 | 18t, 72.22%, $256.05 |

C’s AAPL 10-share P&L is slightly ahead of A ($189.05 vs $178.08). MSFT is still the gap ($256.05 vs $382.23) — fewer flatten lots (7 vs A’s 9).

## 2. August 2026 1% equity risk

| | A. Locked 1% | B. SMA slope 1% | C. EMA slope 1% |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 16 (AAPL 9, MSFT 7) | 31 (AAPL 19, MSFT 12) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 4 | entry_cutoff 5, insufficient_cash 1 | entry_cutoff 16, insufficient_cash 2 |
| Trades | 14 (AAPL 6, MSFT 8) | 10 (AAPL 5, MSFT 5) | 12 (AAPL 6, MSFT 6) |
| Wins / losses | 8 / 6 | 7 / 3 | 8 / 4 |
| **Win rate** | **57.14%** | **70.00%** | **66.67%** |
| **Total P&L** | **$2,998.96 (2.999%)** | **$1,504.39 (1.504%)** | **$1,026.54 (1.027%)** |
| Avg win | $604.79 | $508.03 | $458.08 |
| Avg loss | $-306.56 | $-683.95 | $-659.53 |
| **Max drawdown** | **$2,510.94 (2.44%)** | **$2,879.23 (2.84%)** | **$2,879.23 (2.84%)** |
| Ending equity | $102,998.96 | $101,504.39 | $101,026.54 |
| Exit mix | ma_cross 10, flatten 4 | ma_cross 8, flatten 2 | ma_cross 9, flatten 3 |
| **Exit P&L** | ma_cross $-75.78 (10); flatten $3,074.74 (4) | ma_cross $390.77 (8); flatten $1,113.62 (2) | ma_cross $-195.07 (9); flatten $1,221.60 (3) |
| AAPL | 6t, 50.00%, $1,777.00 | 5t, 60.00%, $1,177.00 | 6t, 50.00%, $589.84 |
| MSFT | 8t, 62.50%, $1,221.96 | 5t, 80.00%, $327.39 | 6t, 83.33%, $436.70 |

C still misses A’s MSFT 2026-08-06 flatten **+$1,337.77**. Versus B, C adds MSFT 2026-08-18 flatten **+$112.23** (A had **+$113.88**) but also AAPL 2026-08-20 `ma_cross` **$-588.44** (A’s later price-cross that day was **$-265.60**) and AAPL 2026-08-27 **$-346.11**. The extra pair-crosses vs B are net negative in August.

## Fill conventions (all three books)

| Leg | When | Fill |
| --- | --- | --- |
| Entry | Signal bar closes with a valid long setup before `entry_cutoff` | **Next 15m bar open** |
| `ma_cross_close` exit | Completed bar after entry: prev EMA ≥ prev SMA and curr EMA < curr SMA | **That bar’s close** |
| `session_flatten` | Bar containing 15:55 ET if still open and no same-bar pair-cross | That bar’s close |

Full engine dumps: `artifacts/ema9_pair_ema_slope.json`, `artifacts/ema9_aug2026_risk_pair_ema_slope.json`. Prior B-only writeup: `artifacts/ema9_pair_slope.md`.
