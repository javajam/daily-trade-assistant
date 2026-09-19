# ema9_trend AAPL+MSFT: locked MA-cross-at-close book vs pair-cross + SMA20 flat/rising entry

Same exit, gates, and universe as the locked noon day-trade book. **No RSI. No price-cross-above-EMA9. No lock-+1% / percent stop / half-take / pyramid / volume filter.** B enters when **EMA(9) crosses above SMA(20)** close-to-close **and** SMA(20) on the signal bar is flat or rising.

- Tape: Yahoo 15m unadjusted RTH, 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- A entry (locked): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill at the **next bar open**.
- B entry (new):
  1. EMA(9) crosses above SMA(20) close-to-close: prev EMA ≤ prev SMA and curr EMA > curr SMA — the inverse of the `ma_cross_close` exit convention (`ema_sma_cross` bullish).
  2. SMA(20) flat or rising on the signal bar: SMA20[curr] ≥ SMA20[prev] (`sma_slope` `compare: flat_or_rising`).
  3. No RSI. No price×EMA9 filter.
  4. Fill at the **next bar open** (same as A).
- Exit (both): EMA(9) crosses below SMA(20) close-to-close; fill at **that bar’s close** (`action.exit: ma_cross_close`). If the cross bar is also the flatten bar, `ma_cross` at that close wins.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_bracket_nobe_pair_slope.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_pair_slope.json --report artifacts/ema9_pair_slope.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_nobe_pair_slope.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_pair_slope.json --report artifacts/ema9_aug2026_risk_pair_slope.md`

August 1% risk sizes both books with `stop_pct: 1.0` as a **reference R only** (1% of entry): `shares = floor((0.01 × equity) / (0.01 × price))`. No live 1% stop is placed.

Engine totals below. Not invented; not annualized.

## Tape vs the recorded locked-book window

Prior recorded locked 10-share was **50 / 56.00% / $427.81** on Yahoo ~2026-06-17→2026-09-11. This run’s 15m Yahoo window has rolled to **2026-06-25→2026-09-18** (still 1560 closed bars per name). The overlapping months **reproduce** the prior MA-cross-at-close 10-share rows: July **16t / 62.50% / $235.45**, August **18t / 66.67% / $192.46**. June is truncated (5t / $111.01 vs the old 10t / $68.26) and September has extra sessions (11t / $21.40 vs the old 6t / $-68.35). Full-window A on this tape is therefore **50 / 58.00% / $560.31**, not $427.81.

August 2026 1% risk A **reproduced**: **14 / 57.14% / $2,998.96**, max DD $2,510.94.

## Verdict

**The new entry does not beat the locked book on this tape.**

10-share full window: A **50 / 58.00% / $560.31**, max DD $147.68. B is **34 / 58.82% / $381.18**, max DD $124.44. **$179.13 behind A** on P&L. Pair-cross + slope cuts signals 160 → 46. Win rate is a hair higher; drawdown is tighter; trade count and flatten-runner P&L are not.

August 2026 1% risk: A **14 / 57.14% / $2,998.96**. B is **10 / 70.00% / $1,504.39**, max DD $2,879.23 vs $2,510.94. **Does not beat** ($1,494.57 behind). B missed A’s MSFT 2026-08-06 `session_flatten` **+$1,337.77** (no pair-cross that morning) and took a worse AAPL 2026-08-05 `ma_cross` (B 15:00Z fill **$-990.14** vs A’s earlier 14:45Z price-cross **$-189.54**).

## 1. Baseline A (10-share locked book, this tape)

**50 trades, 58.00%, $560.31**, max DD $147.68. Signals 160 (AAPL 81, MSFT 79). Skips: `entry_cutoff` 69, `already_in_position` 41. Exits: **ma_cross 35 ($-118.06)**, **session_flatten 15 ($678.37)**.

## 2. Variant B, same tape (10-share)

**34 trades, 58.82%, $381.18**, max DD $124.44. Signals 46 (AAPL 25, MSFT 21). Skips: `entry_cutoff` 12 (no `already_in_position` — pair-cross is rare enough that the lot is free before the next noon setup). Exits: **ma_cross 26 ($81.83)**, **session_flatten 8 ($299.35)**.

Pair-cross + SMA-flat/rising **does not beat** the locked book on this window: **$179.13 behind**, fewer trades, less flatten P&L ($299.35 vs $678.37).

### Side-by-side (10-share, full Yahoo window)

| | A. Locked MA-cross-at-close | B. Pair-cross + SMA20 flat/rising |
| --- | ---: | ---: |
| Signals | 160 (AAPL 81, MSFT 79) | 46 (AAPL 25, MSFT 21) |
| Skips | already_in_position 41, entry_cutoff 69 | entry_cutoff 12 |
| Trades | 50 (AAPL 23, MSFT 27) | 34 (AAPL 19, MSFT 15) |
| Wins / losses / scratch | 29 / 21 / 0 | 20 / 14 / 0 |
| **Win rate** | **58.00%** | **58.82%** |
| **Total P&L** | **$560.31 (0.560%)** | **$381.18 (0.381%)** |
| Avg win | $33.60 | $30.25 |
| Avg loss | $-19.71 | $-15.99 |
| **Max drawdown** | **$147.68 (0.15%)** | **$124.44 (0.12%)** |
| Ending equity | $100,560.31 | $100,381.18 |
| Exit mix | ma_cross 35, session_flatten 15 | ma_cross 26, session_flatten 8 |
| **Exit P&L** | ma_cross $-118.06 (35); session_flatten $678.37 (15) | ma_cross $81.83 (26); session_flatten $299.35 (8) |

Figures are engine totals, not annualized. One ~85-day Yahoo 15m window. 10 shares, $0 friction. Entry fill is next-bar open on both books; exit fill is the completed cross bar’s close.

### Monthly (10-share)

| Month | A. Locked book | B. Pair-cross + SMA20 flat/rising |
| --- | ---: | ---: |
| 2026-06 | $111.01 (5t, 60.00%) | $-22.75 (1t, 0.00%) |
| 2026-07 | $235.45 (16t, 62.50%) | $395.00 (13t, 76.92%) |
| 2026-08 | $192.46 (18t, 66.67%) | $48.08 (11t, 63.64%) |
| 2026-09 | $21.40 (11t, 36.36%) | $-39.15 (9t, 33.33%) |

July is the only month B is ahead ($395.00 vs $235.45). August is where the locked price-cross book pulls away ($192.46 vs $48.08) — the same month the 1% risk book then fails to beat.

### By symbol (10-share)

| | A. Locked book | B. Pair-cross + SMA20 flat/rising |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $178.08 (ma_cross 17 / flatten 6) | 19t, 47.37%, $160.73 (ma_cross 16 / flatten 3) |
| MSFT | 27t, 62.96%, $382.23 (ma_cross 18 / flatten 9) | 15t, 73.33%, $220.45 (ma_cross 10 / flatten 5) |

MSFT still carries both books. B’s higher MSFT win rate does not offset missing flatten runners (9 → 5).

## 3. August 2026 1% equity risk (both books)

Same tape, `--start 2026-08-01 --end 2026-08-31`. Locked book **reproduced**: **14 trades, 57.14%, $2,998.96**, max DD $2,510.94 (10 `ma_cross` / 4 `session_flatten`). New book: **10 trades, 70.00%, $1,504.39**, max DD $2,879.23 (8 `ma_cross` / 2 flatten).

| | A. Locked 1% risk | B. Pair-cross + SMA20 flat/rising 1% risk |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 16 (AAPL 9, MSFT 7) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 4 | entry_cutoff 5, insufficient_cash 1 |
| Trades | 14 (AAPL 6, MSFT 8) | 10 (AAPL 5, MSFT 5) |
| Wins / losses | 8 / 6 | 7 / 3 |
| **Win rate** | **57.14%** | **70.00%** |
| **Total P&L** | **$2,998.96 (2.999%)** | **$1,504.39 (1.504%)** |
| Avg win | $604.79 | $508.03 |
| Avg loss | $-306.56 | $-683.95 |
| **Max drawdown** | **$2,510.94 (2.44%)** | **$2,879.23 (2.84%)** |
| Ending equity | $102,998.96 | $101,504.39 |
| Exit mix | ma_cross 10, session_flatten 4 | ma_cross 8, session_flatten 2 |
| **Exit P&L** | ma_cross $-75.78 (10); session_flatten $3,074.74 (4) | ma_cross $390.77 (8); session_flatten $1,113.62 (2) |
| AAPL | 6t, 50.00%, $1,777.00 | 5t, 60.00%, $1,177.00 |
| MSFT | 8t, 62.50%, $1,221.96 | 5t, 80.00%, $327.39 |

August 1% risk is a small sample. The locked book is **$1,494.57 ahead**. B’s higher win rate is the wrong kind: it skips A’s MSFT 2026-08-06 flatten **+$1,337.77** (no EMA9×above SMA20 that session) and MSFT 2026-08-25 / AAPL 2026-08-26 flatten runners are smaller (later pair-cross fills, fewer shares). The 2026-08-05 AAPL pair-cross also fills one bar later than A’s price-cross and loses **$800.60 more**. B-only AAPL 2026-08-28 `ma_cross` **+$733.06** does not close the gap.

## Fill conventions (both books)

| Leg | When | Fill |
| --- | --- | --- |
| Entry | Signal bar closes with a valid long setup before `entry_cutoff` | **Next 15m bar open** |
| `ma_cross_close` exit | Completed bar after entry: prev EMA ≥ prev SMA and curr EMA < curr SMA | **That bar’s close** |
| `session_flatten` | Bar containing 15:55 ET (15:45 ET 15m close) if still open and no same-bar pair-cross | That bar’s close |

No live percent stop on either book. Risk YAMLs use `stop_pct: 1.0` only to size shares.

Full engine dumps: `artifacts/ema9_pair_slope.json`, `artifacts/ema9_aug2026_risk_pair_slope.json` (August narrative also in `artifacts/ema9_aug2026_risk_pair_slope.md`).
