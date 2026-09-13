# EMA9 15m — long vs simplified short vs combined (AAPL+MSFT)

- Generated (UTC): 2026-09-13T23:44:28.994485Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Window: **2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z** (60 NY session days; ~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Universe: **AAPL+MSFT** (not TSLA/MU)
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close)
- Config: `config/ema9_trend.example.yaml` (`ema9_trend` + `ema9_trend_short`)
- Isolated books come from the same YAML (one rule each). Combined is both rules on one book.

**Long (A):** close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Stop: initial fill×0.99; first touch of fill×1.01 locks the stop there (live next bar). No take. **Unchanged.**

**Short (B, new):** close crosses below EMA(9) AND close < SMA(20). **No RSI.** Cover when EMA(9) crosses above SMA(20) — flatten at the next bar open (`action.exit: ma_cross`). Stop: initial fill×1.01; first touch of fill×0.99 (−1%) locks the stop there (live next bar). Session flatten still applies.

**Combined (C):** both sides, one position per symbol (long or short, not both). Opposite signal while in a trade is skipped (`opposite_signal_in_trade`).

Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend.example.yaml \
  --source yahoo \
  --output artifacts/ema9_long_short_15m.json \
  --report artifacts/ema9_long_short_15m.md
```

Engine totals only. Not annualized. June and September are **partial** months (tape starts mid-June and ends 2026-09-11).

## Data window (do not treat this as multi-year)

Yahoo’s downloader requests `range=60d` for 15m. Asking for `3mo`, `6mo`, or a `period1` older than that cap returns **HTTP 422**. This run’s `60d` request returned **2026-06-17 → 2026-09-11** — the same calendar window as the prior AAPL/MSFT lock-+1% 15m books.

No other free source was used. Alpaca keys are unset.

## Side-by-side (10-share, full Yahoo window)

| | A. Long-only | B. New short-only | C. Long+new short |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 126 (AAPL 69, MSFT 57) | 280 (AAPL 146, MSFT 134) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 16, entry_cutoff 64, no_next_bar 1 | already_in_position 34, entry_cutoff 127, **opposite_signal_in_trade 36**, no_next_bar 1 |
| Trades | 51 (MSFT 28, AAPL 23) | 45 (MSFT 22, AAPL 23) | 82 (MSFT 43, AAPL 39) |
| Wins / losses | 31 / 20 | 19 / 26 | 44 / 38 |
| **Win rate** | **60.78%** | **42.22%** | **53.66%** |
| **Total P&L** | **$301.49 (0.301%)** | **$-61.44 (−0.061%)** | **$196.03 (0.196%)** |
| Avg win | $27.05 | $28.24 | $26.62 |
| Avg loss | $-26.85 | $-23.00 | $-25.66 |
| **Max drawdown** | **$130.76 (0.13%)** | **$287.85 (0.29%)** | **$155.03 (0.15%)** |
| Ending equity | $100,301.49 | $99,938.56 | $100,196.03 |
| Exit mix | lock_stop 20, stop 13, session_flatten 18 | ma_cross 19, lock_stop 12, stop 10, session_flatten 4 | lock_stop 30, stop 19, session_flatten 17, ma_cross 16 |
| Lock armed | 20 | 13 | 30 |
| **Exit P&L** | lock_stop $684.73; session_flatten $76.35; stop $-459.59 | lock_stop $421.75; session_flatten $79.75; ma_cross $-159.85; stop $-403.09 | lock_stop $1,036.49; session_flatten $19.52; ma_cross $-138.19; stop $-721.79 |

**A reproduced** the prior AAPL+MSFT lock-+1% 15m long book exactly: **51 trades, 60.78%, $301.49**, max DD $130.76 (20 `lock_stop` / 13 stop / 18 `session_flatten`; 20 armed). Same tape, same long rule.

**B vs prior short-only (RSI>30, no MA-cross cover):** that book was **41 trades, 53.66%, $96.19**, max DD $281.82 (121 signals; lock_stop 13 / stop 12 / session_flatten 16). The new short printed **45 trades, 42.22%, $-61.44**, max DD $287.85 on the same tape. Signals 121 → 126; trades 41 → 45. The new cover fired **19 `ma_cross` exits for $-159.85**; session_flatten fell from 16 to 4.

**C is not A+B.** Isolated books sum to 96 trades / $240.05. Combined printed **82 trades / $196.03** because **36** opposite-side signals were skipped while the other side was already open. Combined max DD ($155.03) sits between the isolated-side drawdowns. Max DD **by side** is the isolated-book figure (A $130.76 long, B $287.85 short) — not a split of the shared equity curve.

Prior combined (RSI>30 shorts, flatten-only) was **79 trades, 56.96%, $301.75**, max DD $170.99 (42 opposite skips).

### Combined book by side (same shared lot constraint)

| Side | Trades | Wins / losses | Win rate | P&L | Lock armed | Exit mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Long | 44 | 27 / 17 | 61.36% | $273.85 | 19 | lock_stop 19, stop 11, session_flatten 14 |
| Short | 38 | 17 / 21 | 44.74% | $-77.82 | 11 | ma_cross 16, lock_stop 11, stop 8, session_flatten 3 |

On the shared book the long side kept most of isolated-A P&L ($273.85 of $301.49). Combined shorts were cut from 45 isolated trades to 38 and from $-61.44 to $-77.82.

## Monthly breakdown (10-share, realized P&L)

P&L is the sum of trades whose **exit** falls in that NY calendar month. June = 2026-06-17→06-30 (9 sessions). September = 2026-09-01→09-11 (8 sessions).

| Month | Sessions | A long t / WR / P&L | B new short t / WR / P&L | C combined t / WR / P&L |
| --- | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 10 / 40.00% / $-18.75 | 5 / 60.00% / $125.79 | 12 / 50.00% / $56.36 |
| 2026-07 (07-01 → 07-31) | 22 | 17 / 64.71% / $71.56 | 14 / 42.86% / $-37.54 | 29 / 55.17% / $28.30 |
| 2026-08 (08-03 → 08-31) | 21 | 18 / 77.78% / $304.88 | 21 / 38.10% / $-172.42 | 33 / 54.55% / $104.15 |
| 2026-09 (09-01 → 09-11) | 8 | 6 / 33.33% / $-56.20 | 5 / 40.00% / $22.73 | 8 / 50.00% / $7.22 |
| **Window** | **60** | **51 / 60.78% / $301.49** | **45 / 42.22% / $-61.44** | **82 / 53.66% / $196.03** |

August 10-share longs still carried A. Isolated new shorts lost $172.42 that month (prior RSI short lost $133.34). Combined August is $104.15 (not 304.88 − 172.42) because opposite-side skips change which trades exist.

## August 2026 — 1% equity risk (B and C)

Same tape, trade window **2026-08-01 → 2026-08-31** (21 NY sessions; 2026-08-03 is the first RTH session). Config: `config/ema9_trend_risk.example.yaml`. Size: `risk_pct` 1% of equity at the 1.0% initial fill stop. Isolated long (A) is included so the long book can be checked against the prior August 1% long.

```
python -m dta_bot backtest \
  --config config/ema9_trend_risk.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 \
  --output artifacts/ema9_aug2026_risk_long_short.json \
  --report artifacts/ema9_aug2026_risk_long_short.md
```

| | A. Long-only 1% | B. New short-only 1% | C. Long+new short 1% |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 47 (AAPL 25, MSFT 22) | 105 (AAPL 51, MSFT 54) |
| Skips | already_in_position 11, entry_cutoff 28, insufficient_cash 3 | already_in_position 8, entry_cutoff 18 | already_in_position 13, entry_cutoff 44, **opposite_signal_in_trade 15**, insufficient_cash 1 |
| Trades | 15 (MSFT 8, AAPL 7) | 21 (AAPL 9, MSFT 12) | 30 (MSFT 18, AAPL 12) |
| Wins / losses | 11 / 4 | 8 / 13 | 15 / 15 |
| **Win rate** | **73.33%** | **38.10%** | **50.00%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$-3,505.00 (−3.505%)** | **$887.15 (0.887%)** |
| Avg win | $697.61 | $553.24 | $660.94 |
| Avg loss | $-546.00 | $-610.07 | $-601.80 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$6,309.57 (6.20%)** | **$4,002.83 (3.85%)** |
| Ending equity | $105,489.78 | $96,495.00 | $100,887.15 |
| Exit mix | lock_stop 6, session_flatten 8, stop 1 | ma_cross 11, stop 5, lock_stop 4, session_flatten 1 | ma_cross 11, lock_stop 9, stop 5, session_flatten 5 |
| Lock armed | 6 | 4 | 9 |
| **Exit P&L** | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 | lock_stop $3,742.47; session_flatten $371.91; ma_cross $-2,667.64; stop $-4,951.74 | lock_stop $8,546.55; session_flatten $198.83; ma_cross $-2,756.37; stop $-5,101.86 |

**A reproduced** the prior August 15m 1% lock-+1% long book exactly: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

**B vs prior August short 1%** (RSI>30, no MA-cross cover): that book was **20 trades, 45.00%, $-2,879.01**, max DD $6,304.92 (46 signals). The new short printed **21 trades, 38.10%, $-3,505.00**, max DD $6,309.57 (47 signals). **11 `ma_cross` covers lost $2,667.64.**

**C** stayed positive (**$887.15**) but below the prior combined 1% (**29 trades, 55.17%, $1,533.99**, max DD $4,117.37). Combined is again not A+B (36 trades / $1,984.78 vs 30 / $887.15) after **15** `opposite_signal_in_trade` skips.

### August 1% combined by side

| Side | Trades | Wins / losses | Win rate | P&L |
| --- | ---: | ---: | ---: | ---: |
| Long | 10 | 7 / 3 | 70.00% | $3,462.55 |
| Short | 20 | 8 / 12 | 40.00% | $-2,575.40 |

Max DD by side on this window is the isolated 1% book: long **$2,743.31**, short **$6,309.57**. Combined max DD is **$4,002.83**.

## Notes

- Shorts are enabled in the default YAML (`ema9_trend_short.enabled: true`). Disable a side with `enabled: false`.
- One lot per symbol. The engine does not reverse an open long into a short (or the other way). That skip is `opposite_signal_in_trade`.
- Short `ma_cross` cover fills at the **next bar open**. Same-bar stop / lock_stop / `session_flatten` still win if they hit first.
- JSON: `artifacts/ema9_long_short_15m.json`, `artifacts/ema9_aug2026_risk_long_short.json`.
