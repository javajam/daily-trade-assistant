# EMA9 15m — long vs cover-only short vs combined (AAPL+MSFT)

- Generated (UTC): 2026-09-13T23:48:36.908580Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Window: **2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z** (60 NY session days; ~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560 (cache: `data/ohlcv/AAPL_15Min.json`, `data/ohlcv/MSFT_15Min.json`)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Universe: **AAPL+MSFT**
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close)
- Config: `config/ema9_trend.example.yaml`

**Long (A):** close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Stop: initial fill×0.99; first touch of fill×1.01 locks the stop there (live next bar). No take. **Unchanged.**

**Short (B, cover-only):** close crosses below EMA(9) AND close < SMA(20). **No RSI. No lock_plus. No percent stop.** Cover when EMA(9) crosses above SMA(20) — flatten at the next bar open (`action.exit: ma_cross`). Session flatten still applies. Optional `stop_loss_pct` is off.

**Combined (C):** both sides, one position per symbol. Opposite signal while in a trade is skipped (`opposite_signal_in_trade`).

Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend.example.yaml \
  --source yahoo \
  --output artifacts/ema9_long_short_15m.json \
  --report artifacts/ema9_long_short_15m.md
```

Engine totals only. Not annualized. June and September are **partial** months.

## Data window

Yahoo `range=60d` for 15m returned **2026-06-17 → 2026-09-11** — the same calendar window as the prior AAPL/MSFT lock-+1% books. No other source. Alpaca keys unset.

## Side-by-side (10-share, full Yahoo window)

| | A. Long-only | B. Cover-only short | C. Long + cover-only short |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 126 (AAPL 69, MSFT 57) | 280 (AAPL 146, MSFT 134) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 25, entry_cutoff 56, no_next_bar 1 | already_in_position 36, entry_cutoff 127, **opposite_signal_in_trade 42**, no_next_bar 1 |
| Trades | 51 (MSFT 28, AAPL 23) | 44 (MSFT 21, AAPL 23) | 74 (AAPL 38, MSFT 36) |
| Wins / losses | 31 / 20 | 19 / 25 | 40 / 34 |
| **Win rate** | **60.78%** | **43.18%** | **54.05%** |
| **Total P&L** | **$301.49 (0.301%)** | **$-66.41 (−0.066%)** | **$37.26 (0.037%)** |
| Avg win | $27.05 | $31.42 | $25.86 |
| Avg loss | $-26.85 | $-26.54 | $-29.32 |
| **Max drawdown** | **$130.76 (0.13%)** | **$348.72 (0.35%)** | **$296.58 (0.30%)** |
| Ending equity | $100,301.49 | $99,933.59 | $100,037.26 |
| Exit mix | lock_stop 20, stop 13, session_flatten 18 | ma_cross 35, session_flatten 9 | ma_cross 30, session_flatten 19, lock_stop 15, stop 10 |
| Lock armed | 20 | 0 | 15 |
| **Exit P&L** | lock_stop $684.73; session_flatten $76.35; stop $-459.59 | ma_cross $-164.86; session_flatten $98.45 | lock_stop $485.43; session_flatten $90.52; ma_cross $-184.70; stop $-353.99 |

**A reproduced** the prior long book exactly: **51 trades, 60.78%, $301.49**, max DD $130.76.

**B vs earlier short books on this same tape** (do not mix these with A):

| Short book | Trades | WR | P&L | Max DD | Short exits |
| --- | ---: | ---: | ---: | ---: | --- |
| **This run (no RSI, cover-only, no stop)** | **44** | **43.18%** | **$-66.41** | **$348.72** | ma_cross 35 / session_flatten 9 |
| Prior revision (no RSI, MA-cross cover + lock_plus) | 45 | 42.22% | $-61.44 | $287.85 | ma_cross 19 / lock_stop 12 / stop 10 / session_flatten 4 |
| Original mirrored short (RSI>30, flatten + lock_plus, no MA-cross cover) | 41 | 53.66% | $96.19 | $281.82 | lock_stop 13 / stop 12 / session_flatten 16 |

Cover-only B has **no** `stop` / `lock_stop` (lock armed 0). Removing the +1% stop let more shorts run into the MA-cross: **35 `ma_cross` exits lost $164.86**. Session flatten is 9 ($98.45). Versus the lock_plus short on this PR, trade count is 45 → 44 (shorts held longer; `already_in_position` 16 → 25) and max DD deepened ($287.85 → $348.72). Versus the original 41t / $96.19 RSI short, this book is a loser with a lower win rate.

**C is not A+B.** Isolated books sum to 95 trades / $235.08. Combined printed **74 trades / $37.26** after **42** `opposite_signal_in_trade` skips (shorts hold to the MA-cross, so they block more opposite longs). Combined max DD ($296.58) is close to isolated-B. Max DD **by side** is the isolated-book figure (A $130.76, B $348.72).

Prior combined (RSI>30 shorts + lock): 79t / 56.96% / $301.75 / DD $170.99. Prior combined on this PR (no RSI + lock_plus): 82t / 53.66% / $196.03 / DD $155.03.

### Combined book by side

| Side | Trades | Wins / losses | Win rate | P&L | Lock armed | Exit mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Long | 37 | 23 / 14 | 62.16% | $177.86 | 15 | lock_stop 15, session_flatten 12, stop 10 |
| Short | 37 | 17 / 20 | 45.95% | $-140.60 | 0 | ma_cross 30, session_flatten 7 |

Shared-book longs kept $177.86 of isolated-A $301.49 (37 of 51 trades). Shared-book shorts: 37 trades, $-140.60 (isolated B was 44 / $-66.41).

## Monthly breakdown (10-share, realized P&L)

P&L is the sum of trades whose **exit** falls in that NY calendar month. June = 2026-06-17→06-30 (9 sessions). September = 2026-09-01→09-11 (8 sessions).

| Month | Sessions | A long t / WR / P&L | B cover-only short t / WR / P&L | C combined t / WR / P&L |
| --- | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 10 / 40.00% / $-18.75 | 5 / 60.00% / $192.02 | 12 / 50.00% / $122.59 |
| 2026-07 (07-01 → 07-31) | 22 | 17 / 64.71% / $71.56 | 14 / 42.86% / $-103.43 | 26 / 53.85% / $-112.59 |
| 2026-08 (08-03 → 08-31) | 21 | 18 / 77.78% / $304.88 | 20 / 40.00% / $-159.74 | 29 / 55.17% / $22.62 |
| 2026-09 (09-01 → 09-11) | 8 | 6 / 33.33% / $-56.20 | 5 / 40.00% / $4.74 | 7 / 57.14% / $4.63 |
| **Window** | **60** | **51 / 60.78% / $301.49** | **44 / 43.18% / $-66.41** | **74 / 54.05% / $37.26** |

## August 1% equity risk — not re-run

`risk_pct` sizing needs a stop distance R. Cover-only shorts have **no stop**, so 1% equity-risk share count is not defined. The risk YAML keeps shorts at 10 shares. August 1% isolated-short and combined books were **not** replayed for this cover-only exit. Isolated August 10-share shorts are the August row above (20t / 40.00% / $-159.74). Prior August 1% figures (with a 1% short stop) do not apply to this rule.

## Notes

- Shorts: `ema9_trend_short.enabled: true`. Disable a side with `enabled: false`.
- One lot per symbol. No reverse. Skip: `opposite_signal_in_trade`.
- Short `ma_cross` fills at the **next bar open**. Same-bar `session_flatten` still wins if that bar is the flatten bar.
- JSON: `artifacts/ema9_long_short_15m.json`.
