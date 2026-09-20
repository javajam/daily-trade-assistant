# ema9_trend AAPL+MSFT: locked MA-cross vs range > last 3 (variant E)

Same entry, gates, and universe as the locked noon day-trade book. **No MA-cross exit. No percent stop. No lock_plus. No half-take. No pyramid. No volume filter.** E replaces `ma_cross_close` with a range-expansion exit.

## Convention (documented; engine had no prior range-exit)

- **Bigger** = bar **range** (high − low), not body.
- Exit when the current completed bar’s range is **strictly greater than** `max(range of the previous 3 bars)` (equivalently larger than each of the last three).
- Fill at that bar’s **close**.
- **Do not arm on the entry/fill bar.** The first eligible bar is the next completed bar after fill. Need 3 prior bars in the series (warmup covers that on this tape).
- Equal range stays valid.
- Optional stop is off on this book. If a stop were set, same-bar stop + range expansion → stop (stop is checked first).
- Session flatten still applies. **Same-bar range expansion + flatten → `range_expansion`** at that close (close-fill wins, same as `ma_cross_close` / `lower_high`). On this tape every E trade exited as `range_expansion` (0 flatten).

- Tape: Yahoo 15m unadjusted RTH, **same cache as the prior PR runs** — 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z (AAPL/MSFT 1560 closed bars each; cache hit)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill at the **next bar open**.
- A exit (locked): EMA(9) crosses below SMA(20) close-to-close; fill at **that bar’s close** (`action.exit: ma_cross_close`).
- E exit: `action.exit: range_expansion`, `exit_range_bars: 3`.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_bracket_nobe_range3.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_range3.json --report artifacts/ema9_range3.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_nobe_range3.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_range3.json --report artifacts/ema9_aug2026_risk_range3.md`

August 1% risk sizes both books with `stop_pct: 1.0` as a **reference R only**. No live percent stop.

Engine totals below. Not invented; not annualized.

## Reproduction

A 10-share **50 / 58.00% / $560.31** matches the prior PR on this cache. August 1% A **14 / 57.14% / $2,998.96** also matches.

## Verdict

**E beats the locked book on both required runs.**

10-share: A **50 / 58.00% / $560.31**. E is **54 / 75.93% / $696.66**, max DD $115.38 vs $147.68. **$136.35 ahead of A.** All 54 E exits are `range_expansion` ($696.66); 0 flatten. Range expansion clips A’s flatten runners (still net ahead) and turns many `ma_cross` losers into small wins.

August 2026 1% risk: A **14 / 57.14% / $2,998.96**. E is **16 / 87.50% / $6,008.19**, max DD $2,028.83 vs $2,510.94. **Beats** ($3,009.23 ahead). AAPL 1% is 6t / 100% / $4,015.35 vs A’s $1,777.00. The cost is clipping MSFT 2026-08-06 A `session_flatten` **+$1,337.77** down to **+$399.84**.

## 1. 10-share full window

A **reproduced**: **50 trades, 58.00%, $560.31**, max DD $147.68. Signals 160. Skips: `entry_cutoff` 69, `already_in_position` 41. Exits: **ma_cross 35 ($-118.06)**, **session_flatten 15 ($678.37)**.

E (range > last 3): **54 trades, 75.93%, $696.66**, max DD $115.38. Signals 160 (AAPL 81, MSFT 79). Skips: `entry_cutoff` 92, `already_in_position` 14. Exits: **range_expansion 54 ($696.66)**. Earlier exits free the one-lot slot, so `already_in_position` drops (41 → 14) and four extra fills appear.

### Side-by-side (10-share)

| | A. Locked MA-cross | E. Range > last 3 |
| --- | ---: | ---: |
| Signals | 160 (AAPL 81, MSFT 79) | 160 (AAPL 81, MSFT 79) |
| Skips | already_in_position 41, entry_cutoff 69 | already_in_position 14, entry_cutoff 92 |
| Trades | 50 (AAPL 23, MSFT 27) | 54 (AAPL 26, MSFT 28) |
| Wins / losses | 29 / 21 | 41 / 13 |
| **Win rate** | **58.00%** | **75.93%** |
| **Total P&L** | **$560.31 (0.560%)** | **$696.66 (0.697%)** |
| Avg win | $33.60 | $25.51 |
| Avg loss | $-19.71 | $-26.86 |
| **Max drawdown** | **$147.68 (0.15%)** | **$115.38 (0.11%)** |
| Ending equity | $100,560.31 | $100,696.66 |
| Exit mix | ma_cross 35, flatten 15 | range_expansion 54 |
| **Exit P&L** | ma_cross $-118.06 (35); flatten $678.37 (15) | range_expansion $696.66 (54) |

Entry fill is next-bar open on both. E never used session flatten on this window.

### Monthly (10-share)

| Month | A. Locked | E. Range > last 3 |
| --- | ---: | ---: |
| 2026-06 | $111.01 (5t, 60.00%) | $128.40 (5t, 60.00%) |
| 2026-07 | $235.45 (16t, 62.50%) | $245.14 (16t, 68.75%) |
| 2026-08 | $192.46 (18t, 66.67%) | $276.41 (19t, 89.47%) |
| 2026-09 | $21.40 (11t, 36.36%) | $46.71 (14t, 71.43%) |

Every month is ahead. August and September are where the win-rate lift shows.

### By symbol (10-share)

| | A. Locked | E. Range > last 3 |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $178.08 | 26t, 76.92%, $223.97 |
| MSFT | 27t, 62.96%, $382.23 | 28t, 75.00%, $472.70 |

### What changed vs A (10-share)

All 50 shared fills change exit. Shared-fill delta **+$168.35**. Four extra E fills net **$-32.00**. Net **+$136.35**.

Notable shared-fill moves (10 shares):

- AAPL 2026-08-19 `ma_cross` **+$35.11** → range **+$61.77**
- MSFT 2026-08-10 **+$4.65** → **+$46.45**
- MSFT 2026-08-21 `ma_cross` **$-6.69** → **+$28.81**
- AAPL 2026-08-07 **$-4.50** → **+$12.20**
- MSFT 2026-08-06 flatten **+$65.90** → **+$19.60** (gave back a runner)
- AAPL 2026-07-31 `ma_cross` **$-0.20** → **$-30.80** (range expansion worse)

Extra E-only fills: AAPL 2026-09-02 **$-11.90**, AAPL 2026-09-14 **+$3.90**, AAPL 2026-09-16 **+$9.90**, MSFT 2026-08-14 **$-33.90**.

## 2. August 2026 1% equity risk

| | A. Locked 1% | E. Range > last 3 1% |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 4 | entry_cutoff 35, already_in_position 3, insufficient_cash 3 |
| Trades | 14 (AAPL 6, MSFT 8) | 16 (AAPL 6, MSFT 10) |
| Wins / losses | 8 / 6 | 14 / 2 |
| **Win rate** | **57.14%** | **87.50%** |
| **Total P&L** | **$2,998.96 (2.999%)** | **$6,008.19 (6.008%)** |
| Avg win | $604.79 | $537.84 |
| Avg loss | $-306.56 | $-760.79 |
| **Max drawdown** | **$2,510.94 (2.44%)** | **$2,028.83 (1.96%)** |
| Ending equity | $102,998.96 | $106,008.19 |
| Exit mix | ma_cross 10, flatten 4 | range_expansion 16 |
| **Exit P&L** | ma_cross $-75.78 (10); flatten $3,074.74 (4) | range_expansion $6,008.19 (16) |
| AAPL | 6t, 50.00%, $1,777.00 | 6t, 100.00%, $4,015.35 |
| MSFT | 8t, 62.50%, $1,221.96 | 10t, 80.00%, $1,992.85 |

Shared-fill delta **+$3,255.63**. Two extra MSFT fills net **$-246.39** (2026-08-14 **$-691.56**, 2026-08-19 **+$445.17**). Net **+$3,009.23**.

Clipped flatten runner: MSFT 2026-08-06 A **+$1,337.77** → E **+$399.84**. Offset by turning AAPL 08-05 / 08-07 / 08-20 and MSFT 08-14 / 08-21 `ma_cross` losers into wins, plus AAPL 08-19 **+$1,130.45** → **+$2,007.50**.

## Fill conventions

| Leg | When | Fill |
| --- | --- | --- |
| Entry | Signal bar closes with a valid long setup before `entry_cutoff` | **Next 15m bar open** |
| `ma_cross_close` (A) | Completed bar after entry: prev EMA ≥ prev SMA and curr EMA < curr SMA | **That bar’s close** |
| `range_expansion` (E) | Completed bar **after the fill bar**: range > max of previous 3 | **That bar’s close** |
| `session_flatten` | Bar containing 15:55 ET if still open and no same-bar close-fill exit | That bar’s close |

Same-bar range expansion + flatten → **range_expansion**. Same-bar stop (if set) + range expansion → **stop**.

Full engine dumps: `artifacts/ema9_range3.json`, `artifacts/ema9_aug2026_risk_range3.json`.
