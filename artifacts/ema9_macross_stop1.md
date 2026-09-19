# ema9_trend AAPL+MSFT: locked MA-cross vs hard 1% fill stop + MA-cross (variant D)

Same entry, gates, and universe as the locked noon day-trade book. **No lock_plus. No lock-at-+1%. No half-take. No pyramid. No volume filter.** D adds a **hard 1% stop at fill × 0.99** (`stop_mode: entry_pct`; never moves) on top of `ma_cross_close`.

- Tape: Yahoo 15m unadjusted RTH, **same cache as the prior pair-cross PR run** — 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z (AAPL/MSFT 1560 closed bars each; cache hit)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill at the **next bar open**.
- A exit (locked): EMA(9) crosses below SMA(20) close-to-close; fill at **that bar’s close** (`action.exit: ma_cross_close`). No live percent stop.
- D exit (this run):
  1. Hard stop: bar low ≤ fill × 0.99 (`stop_mode: entry_pct`). Gap-through fills at that bar’s open. Stop never moves (not `lock_plus`).
  2. `ma_cross_close`: prev EMA ≥ prev SMA and curr EMA < curr SMA; fill at that completed bar’s close.
  3. `session_flatten` at 15:55.
  4. **Same-bar priority:** stop is checked first, so stop + pair-cross on the same bar → `stop`. If the cross bar is also the flatten bar and the stop did not hit, `ma_cross` at that close wins over `session_flatten`.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_bracket_nobe_macross_stop1.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_macross_stop1.json --report artifacts/ema9_macross_stop1.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_nobe_macross_stop1.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_macross_stop1.json --report artifacts/ema9_aug2026_risk_macross_stop1.md`

August 1% risk: A sizes off `stop_pct: 1.0` as a **reference R only** (no live stop). D uses the same 1.0% R **and** a live `entry_pct` 1% stop, so share count matches A while the stop is real.

Engine totals below. Not invented; not annualized.

## Reproduction

A 10-share **50 / 58.00% / $560.31** matches the prior PR on this cache. August 1% A **14 / 57.14% / $2,998.96** also matches.

## Verdict

**D does not beat the locked book.**

10-share: A **50 / 58.00% / $560.31**. D is **51 / 56.86% / $531.27**, max DD $137.48 vs $147.68. **$29.04 behind A.** Flatten P&L is identical ($678.37 on 15 trades). Six `ma_cross` losers become `stop` (net **$-219.17** on those six vs A’s corresponding `ma_cross` P&L); one extra AAPL 2026-07-17 re-entry after the stop (`ma_cross` **$-13.25**) is the extra trade.

August 2026 1% risk: A **14 / 57.14% / $2,998.96**. D is **identical** (same 14 fills, same exits, **0 stop hits**). **Does not beat** (tie). No August loser tagged fill × 0.99 before `ma_cross` / flatten.

## 1. 10-share full window

A **reproduced**: **50 trades, 58.00%, $560.31**, max DD $147.68. Signals 160. Skips: `entry_cutoff` 69, `already_in_position` 41. Exits: **ma_cross 35 ($-118.06)**, **session_flatten 15 ($678.37)**.

D (hard 1% fill stop): **51 trades, 56.86%, $531.27**, max DD $137.48. Signals 160 (AAPL 81, MSFT 79). Skips: `entry_cutoff` 71, `already_in_position` 38. Exits: **ma_cross 30 ($72.06)**, **session_flatten 15 ($678.37)**, **stop 6 ($-219.17)**. All six stops have `lock_armed` false.

### Side-by-side (10-share)

| | A. Locked (no % stop) | D. Hard 1% fill stop + MA-cross |
| --- | ---: | ---: |
| Signals | 160 (AAPL 81, MSFT 79) | 160 (AAPL 81, MSFT 79) |
| Skips | already_in_position 41, entry_cutoff 69 | already_in_position 38, entry_cutoff 71 |
| Trades | 50 (AAPL 23, MSFT 27) | 51 (AAPL 24, MSFT 27) |
| Wins / losses | 29 / 21 | 29 / 22 |
| **Win rate** | **58.00%** | **56.86%** |
| **Total P&L** | **$560.31 (0.560%)** | **$531.27 (0.531%)** |
| Avg win | $33.60 | $33.60 |
| Avg loss | $-19.71 | $-20.14 |
| **Max drawdown** | **$147.68 (0.15%)** | **$137.48 (0.14%)** |
| Ending equity | $100,560.31 | $100,531.27 |
| Exit mix | ma_cross 35, flatten 15 | ma_cross 30, flatten 15, stop 6 |
| **Exit P&L** | ma_cross $-118.06 (35); flatten $678.37 (15) | ma_cross $72.06 (30); flatten $678.37 (15); stop $-219.17 (6) |

Entry fill is next-bar open on both; `ma_cross_close` fill is the completed cross bar’s close; stop fill is the 1% level (or bar open on a gap-through). 10 shares, $0 friction.

### Monthly (10-share)

| Month | A. Locked | D. Hard 1% stop |
| --- | ---: | ---: |
| 2026-06 | $111.01 (5t, 60.00%) | $111.01 (5t, 60.00%) |
| 2026-07 | $235.45 (16t, 62.50%) | $207.09 (17t, 58.82%) |
| 2026-08 | $192.46 (18t, 66.67%) | $192.46 (18t, 66.67%) |
| 2026-09 | $21.40 (11t, 36.36%) | $20.71 (11t, 36.36%) |

June and August 10-share match A exactly (0 stop hits). July is the gap. September is one same-bar stop vs `ma_cross` (AAPL 2026-09-09).

### By symbol (10-share)

| | A. Locked | D. Hard 1% stop |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $178.08 | 24t, 50.00%, $108.56 |
| MSFT | 27t, 62.96%, $382.23 | 27t, 62.96%, $422.71 |

MSFT 10-share is ahead of A (stops cut two larger `ma_cross` losers). AAPL is behind (same-bar stop turned a scratch `ma_cross` into −1%, plus the 2026-07-17 stop + re-entry).

### Stop vs A’s `ma_cross` (10-share)

Same-bar stop + pair-cross → stop. AAPL 2026-07-31 and AAPL 2026-09-09 exit on the same bar in both books.

| Trade | A (`ma_cross`) | D (`stop`) | Δ |
| --- | ---: | ---: | ---: |
| AAPL 2026-07-17 13:30 | $-7.95 | $-33.25 | $-25.30 |
| AAPL 2026-07-17 14:45 (D only) | — | $-13.25 (`ma_cross`) | $-13.25 |
| MSFT 2026-07-23 13:30 | $-57.50 | $-39.00 | $+18.50 |
| MSFT 2026-07-24 13:30 | $-31.48 | $-38.65 | $-7.18 |
| AAPL 2026-07-31 13:30 (same bar) | $-0.20 | $-30.48 | $-30.28 |
| MSFT 2026-07-31 13:45 | $-75.15 | $-46.00 | $+29.15 |
| AAPL 2026-09-09 14:00 (same bar) | $-31.10 | $-31.79 | $-0.69 |
| **Net** | | | **$-29.04** |

## 2. August 2026 1% equity risk

| | A. Locked 1% (reference R) | D. Hard 1% fill stop (live) |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 4 | entry_cutoff 28, already_in_position 11, insufficient_cash 4 |
| Trades | 14 (AAPL 6, MSFT 8) | 14 (AAPL 6, MSFT 8) |
| Wins / losses | 8 / 6 | 8 / 6 |
| **Win rate** | **57.14%** | **57.14%** |
| **Total P&L** | **$2,998.96 (2.999%)** | **$2,998.96 (2.999%)** |
| Avg win | $604.79 | $604.79 |
| Avg loss | $-306.56 | $-306.56 |
| **Max drawdown** | **$2,510.94 (2.44%)** | **$2,510.94 (2.44%)** |
| Ending equity | $102,998.96 | $102,998.96 |
| Exit mix | ma_cross 10, flatten 4 | ma_cross 10, flatten 4 |
| **Exit P&L** | ma_cross $-75.78 (10); flatten $3,074.74 (4) | ma_cross $-75.78 (10); flatten $3,074.74 (4) |
| AAPL | 6t, 50.00%, $1,777.00 | 6t, 50.00%, $1,777.00 |
| MSFT | 8t, 62.50%, $1,221.96 | 8t, 62.50%, $1,221.96 |

D’s live 1% stop **never hit** in August. Every August 1% fill matches A (same entry time, exit reason, P&L). Sizing matches because D’s live 1% R is the same formula A uses as a reference R.

## Fill conventions (both books)

| Leg | When | Fill |
| --- | --- | --- |
| Entry | Signal bar closes with a valid long setup before `entry_cutoff` | **Next 15m bar open** |
| Hard 1% stop (D only) | Completed bar after entry: long low ≤ fill × 0.99 | **Stop level**, or that bar’s open on a gap-through |
| `ma_cross_close` exit | Completed bar after entry: prev EMA ≥ prev SMA and curr EMA < curr SMA | **That bar’s close** |
| `session_flatten` | Bar containing 15:55 ET if still open and no same-bar pair-cross / stop | That bar’s close |

Same-bar stop + pair-cross → **stop**. Same-bar pair-cross + flatten (no stop) → **ma_cross**. Stop never moves; a +1% rally does not lock.

Full engine dumps: `artifacts/ema9_macross_stop1.json`, `artifacts/ema9_aug2026_risk_macross_stop1.json`.
