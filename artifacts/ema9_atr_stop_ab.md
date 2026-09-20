# Protective stop A/B/C: 1% vs Wilder ATR on the no-noon range book

Stop-only comparison on Eric’s locked EMA9 day-trade book with **noon cutoff off**. Entry, size, range exit, flatten, and universe stay fixed. Only the protective stop changes.

Engine totals. Not invented. Not annualized. One Yahoo 15m window.

## Verdict — stick with 1% for Monday paper

**Tape winner on AAPL+MSFT is C (1.5×ATR):** 143 / 62.94% / **$776.45**, max DD **$105.57**. That is **+$14.20** vs A and **+$45.27** vs B, with the tightest combined drawdown.

**Monday paper: keep `stop_mode: entry_pct`, `stop_loss_pct: 1.0`.** Do not switch the locked stop.

Why not promote C:

1. **$14 on ~85 days / 140 trades is noise** at 10 shares. Avg win/loss on A is already ~$17.
2. **AAPL prefers A** ($295.20 vs C $230.56). C’s lead is **MSFT-only** ($545.89 vs A $467.05).
3. **B (1.0×ATR) loses** on A+M. On mega-caps 1.0×ATR is a **0.40%** stop (vs 1.00%) and fires 37 times vs A’s 10. Too tight.
4. **SOXL peek prefers A** (least-bad: −$65.58). ATR is *wider* than 1% on the 3× ETF (1.89% / 2.84%) and gives back more.
5. The adopted noon YAML (`config/ema9_trend.example.yaml`) is unchanged. ATR is available if you want a paper trial of **C only** (`config/ema9_trend_bracket_nobe_range3_atr15.example.yaml`).

## ATR definition (Wilder)

Same smoothing as RSI in `dta_bot/indicators.py`. Computed through the **closed signal/entry bar** (the 15m bar that printed the EMA9 cross). Dollar distance is applied to the **fill** (next-bar open). **Not trailing.**

```
TR     = max(high − low, |high − prev_close|, |low − prev_close|)
seed   = SMA of the first 14 true ranges   # needs 15 bars
ATR_t  = (ATR_{t−1} × 13 + TR_t) / 14
stop   = fill − k × ATR_signal             # long
```

No min/max stop-distance floor. Trades skip only when ATR is unavailable (`atr_unavailable`) or the stop is not beyond the fill. That did not fire on this tape.

Live paper still sizes the stop from signal-bar last (same fill-vs-last gap as `entry_pct`).

## Locked book (this A/B)

- Universe: AAPL+MSFT combined; SOXL isolated peek
- 15m Yahoo, 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z (1560 closed bars each; ~60-trading-day / ~85-calendar-day cap)
- Entry: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill at next-bar open
- `entry_cutoff`: **null** (no noon cutoff)
- `flatten_by`: 15:55 ET (15m flatten = 15:45 ET bar close)
- Exit (whichever first): range (high−low) strictly > max of prior 3 **and** expansion bar is non-doji (body/range ≤ 0.10), **or** protective stop. Same-bar stop + range → stop. Range + flatten (no stop) → `range_expansion`
- Size: 10 shares. Long only. $100k start, $0 friction
- `exit_range_skip_doji: true` is on for all three (default locked YAML still does **not** skip dojis; noon cutoff is still 12:00 there)

| | Config | Stop |
| --- | --- | --- |
| A | `config/ema9_trend_bracket_nobe_range3_fixed1_nocutoff.example.yaml` | `stop_mode: entry_pct`, fill × 0.99 |
| B | `config/ema9_trend_bracket_nobe_range3_atr1.example.yaml` | fill − 1.0 × ATR(14) |
| C | `config/ema9_trend_bracket_nobe_range3_atr15.example.yaml` | fill − 1.5 × ATR(14) |

Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_bracket_nobe_range3_fixed1_nocutoff.example.yaml \
  --compare-config config/ema9_trend_bracket_nobe_range3_atr1.example.yaml \
  --compare-config config/ema9_trend_bracket_nobe_range3_atr15.example.yaml \
  --source yahoo --combined-only --symbols AAPL,MSFT \
  --output artifacts/ema9_atr_stop_ab.json \
  --report artifacts/ema9_atr_stop_ab.md

python -m dta_bot backtest \
  --config config/ema9_trend_bracket_nobe_range3_fixed1_nocutoff.example.yaml \
  --compare-config config/ema9_trend_bracket_nobe_range3_atr1.example.yaml \
  --compare-config config/ema9_trend_bracket_nobe_range3_atr15.example.yaml \
  --source yahoo --combined-only --symbols SOXL \
  --output artifacts/ema9_atr_stop_ab_soxl.json \
  --report artifacts/ema9_atr_stop_ab_soxl.md
```

Same 160 AAPL+MSFT signals on all three (AAPL 81, MSFT 79). Same 84 SOXL signals. Extra trades when an earlier stop frees the one-lot slot.

## 1. AAPL+MSFT combined (required)

| | A. 1% fill | B. 1.0×ATR | C. 1.5×ATR |
| --- | ---: | ---: | ---: |
| N trades | 140 | 146 | 143 |
| WR | **65.71%** | 58.90% | 62.94% |
| P&L $ | $762.25 | $731.18 | **$776.45** |
| Max DD | $135.65 | $130.63 | **$105.57** |
| Stop hit | 10 ($-373.63) | 37 ($-559.80) | 23 ($-518.45) |
| Range exit | 118 ($1,100.32) | 97 ($1,255.43) | 108 ($1,259.34) |
| Flatten | 12 ($35.56) | 12 ($35.56) | 12 ($35.56) |
| Avg stop $ | $3.84 | $1.52 | $2.29 |
| Avg stop % | **1.00%** | 0.40% | 0.60% |
| Skips | already_in_position 20 | already_in_position 14 | already_in_position 17 |

## 2. AAPL (from the combined book)

Per-name Max DD is peak-to-trough of that symbol’s closed-trade P&L, not a separate isolated equity curve.

| | A. 1% fill | B. 1.0×ATR | C. 1.5×ATR |
| --- | ---: | ---: | ---: |
| N trades | 70 | 74 | 72 |
| WR | **64.29%** | 56.76% | 59.72% |
| P&L $ | **$295.20** | $219.90 | $230.56 |
| Max DD (trade) | $67.88 | **$53.00** | $59.11 |
| Stop / range / flatten | 4 / 57 / 9 | 18 / 47 / 9 | 10 / 53 / 9 |
| Avg stop $ / % | $3.16 / 1.00% | $1.26 / 0.40% | $1.89 / 0.60% |

## 3. MSFT (from the combined book)

| | A. 1% fill | B. 1.0×ATR | C. 1.5×ATR |
| --- | ---: | ---: | ---: |
| N trades | 70 | 72 | 71 |
| WR | **67.14%** | 61.11% | 66.20% |
| P&L $ | $467.05 | $511.29 | **$545.89** |
| Max DD (trade) | $105.85 | $110.95 | **$68.95** |
| Stop / range / flatten | 6 / 61 / 3 | 19 / 50 / 3 | 13 / 55 / 3 |
| Avg stop $ / % | $4.51 / 1.00% | $1.80 / 0.40% | $2.71 / 0.61% |

## 4. SOXL peek (isolated book)

Not part of the locked universe. All three lose. ATR is **wider** than 1% here, so the stop protects less, not more.

| | A. 1% fill | B. 1.0×ATR | C. 1.5×ATR |
| --- | ---: | ---: | ---: |
| N trades | 82 | 81 | 78 |
| WR | 31.71% | 39.51% | **41.03%** |
| P&L $ | **−$65.58** | −$178.84 | −$322.94 |
| Max DD | **$259.15** | $396.83 | $449.85 |
| Stop / range / flatten | 47 / 29 / 6 | 31 / 41 / 9 | 21 / 48 / 9 |
| Avg stop $ / % | $1.37 / **1.00%** | $2.68 / 1.89% | $4.03 / 2.84% |

## Monthly (AAPL+MSFT 10-share)

| Month | A. 1% | B. 1.0×ATR | C. 1.5×ATR |
| --- | ---: | ---: | ---: |
| 2026-06 | $131.18 (12t, 58.33%) | $145.08 (12t, 58.33%) | $134.14 (12t, 58.33%) |
| 2026-07 | $239.77 (48t, 58.33%) | $234.89 (49t, 53.06%) | **$275.38** (49t, 57.14%) |
| 2026-08 | **$299.01** (49t, 71.43%) | $252.07 (53t, 64.15%) | $232.47 (50t, 66.00%) |
| 2026-09 | $92.29 (31t, 70.97%) | $99.15 (32t, 59.38%) | **$134.46** (32t, 68.75%) |

C wins July and September. A wins August. June is a wash.

## What this is not

- Not the adopted **noon** book (that YAML still has `entry_cutoff: "12:00"` and does not skip dojis). Turning cutoff off roughly **triples** trade count vs the noon range+1% writeup (140 vs 55).
- Not a 1% risk / share-size A/B. Size stayed 10 shares.
- Not a trailing ATR. Distance is frozen at the signal-bar ATR.

## Paper

Leave `config/ema9_trend.example.yaml` and `config/ema9_trend_tradier_sandbox.example.yaml` on **1% `entry_pct`**. To trial C in paper, point the runner at `config/ema9_trend_bracket_nobe_range3_atr15.example.yaml` (and decide noon cutoff separately — this comparison used cutoff off).
