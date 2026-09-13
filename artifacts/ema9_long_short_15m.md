# EMA9 lock-+1% 15m — long vs short vs combined (AAPL+MSFT)

- Generated (UTC): 2026-09-13T23:32:43.273251Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Window: **2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z** (60 NY session days; ~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Universe: **AAPL+MSFT** (not TSLA/MU)
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close)
- Config: `config/ema9_trend.example.yaml` (shorts enabled; `ema9_trend` + `ema9_trend_short`)
- Isolated books come from the same YAML (one rule each). Combined is both rules on one book.

**Long (A):** close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Stop: initial fill×0.99; first touch of fill×1.01 locks the stop there (live next bar). No take.

**Short (B):** close crosses below EMA(9) AND close < SMA(20) AND RSI(14) > 30. Stop: initial fill×1.01; first touch of fill×0.99 (−1%) locks the stop there (live next bar). No take.

**Combined (C):** both sides, one position per symbol (long or short, not both). Opposite signal while in a trade is skipped (`opposite_signal_in_trade`). Session flatten covers both sides.

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

Yahoo’s downloader requests `range=60d` for 15m. Asking for `3mo`, `6mo`, or a `period1` older than that cap returns **HTTP 422**. This run’s `60d` request returned **2026-06-17 → 2026-09-11** — the same calendar window as the prior AAPL/MSFT lock-+1% 15m long book.

No other free source was used. Alpaca keys are unset.

## Side-by-side (10-share, full Yahoo window)

| | A. Long-only | B. Short-only | C. Long+short combined |
| --- | ---: | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 121 (AAPL 65, MSFT 56) | 275 (AAPL 142, MSFT 133) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 19, entry_cutoff 60, no_next_bar 1 | already_in_position 37, entry_cutoff 116, **opposite_signal_in_trade 42**, no_next_bar 1 |
| Trades | 51 (MSFT 28, AAPL 23) | 41 (MSFT 21, AAPL 20) | 79 (MSFT 43, AAPL 36) |
| Wins / losses | 31 / 20 | 22 / 19 | 45 / 34 |
| **Win rate** | **60.78%** | **53.66%** | **56.96%** |
| **Total P&L** | **$301.49 (0.301%)** | **$96.19 (0.096%)** | **$301.75 (0.302%)** |
| Avg win | $27.05 | $30.12 | $28.15 |
| Avg loss | $-26.85 | $-29.81 | $-28.39 |
| **Max drawdown** | **$130.76 (0.13%)** | **$281.82 (0.28%)** | **$170.99 (0.17%)** |
| Ending equity | $100,301.49 | $100,096.19 | $100,301.75 |
| Exit mix | lock_stop 20, stop 13, session_flatten 18 | lock_stop 13, stop 12, session_flatten 16 | lock_stop 30, stop 21, session_flatten 28 |
| Lock armed | 20 | 14 | 30 |
| **Exit P&L** | lock_stop $684.73; session_flatten $76.35; stop $-459.59 | lock_stop $456.89; session_flatten $121.95; stop $-482.65 | lock_stop $1,041.73; session_flatten $61.38; stop $-801.36 |

**A reproduced** the prior AAPL+MSFT lock-+1% 15m long book exactly: **51 trades, 60.78%, $301.49**, max DD $130.76 (20 `lock_stop` / 13 stop / 18 `session_flatten`; 20 armed).

**B** is a weaker isolated book on this tape: **41 trades, 53.66%, $96.19**, and a **deeper** max DD ($281.82 vs $130.76). Shorts still made money; lock_stop P&L ($456.89) paid for the 12 initial stops ($-482.65).

**C is not A+B.** Isolated books sum to 92 trades / $397.68. Combined printed **79 trades / $301.75** because **42** opposite-side signals were skipped while the other side was already open. Combined max DD ($170.99) sits between the isolated-side drawdowns. Max DD **by side** is the isolated-book figure (A $130.76 long, B $281.82 short) — not a split of the shared equity curve.

### Combined book by side (same shared lot constraint)

| Side | Trades | Wins / losses | Win rate | P&L | Lock armed | Exit mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Long | 44 | 27 / 17 | 61.36% | $273.85 | 19 | lock_stop 19, stop 11, session_flatten 14 |
| Short | 35 | 18 / 17 | 51.43% | $27.90 | 11 | lock_stop 11, stop 10, session_flatten 14 |

On the shared book the long side kept most of isolated-A P&L ($273.85 of $301.49). Combined shorts were cut from 41 isolated trades to 35 and from $96.19 to $27.90.

## Monthly breakdown (10-share, realized P&L)

P&L is the sum of trades whose **exit** falls in that NY calendar month. June = 2026-06-17→06-30 (9 sessions). September = 2026-09-01→09-11 (8 sessions).

| Month | Sessions | A long t / WR / P&L | B short t / WR / P&L | C combined t / WR / P&L |
| --- | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 10 / 40.00% / $-18.75 | 5 / 80.00% / $157.70 | 12 / 50.00% / $56.36 |
| 2026-07 (07-01 → 07-31) | 22 | 17 / 64.71% / $71.56 | 12 / 41.67% / $-22.58 | 27 / 55.56% / $43.25 |
| 2026-08 (08-03 → 08-31) | 21 | 18 / 77.78% / $304.88 | 20 / 45.00% / $-133.34 | 32 / 59.38% / $143.23 |
| 2026-09 (09-01 → 09-11) | 8 | 6 / 33.33% / $-56.20 | 4 / 100.00% / $94.41 | 8 / 62.50% / $58.91 |
| **Window** | **60** | **51 / 60.78% / $301.49** | **41 / 53.66% / $96.19** | **79 / 56.96% / $301.75** |

August 10-share longs carried A. Isolated shorts lost $133.34 that month; combined August is $143.23 (not 304.88 − 133.34) because opposite-side skips change which trades exist.

## August 2026 — 1% equity risk (A and C)

Same tape, trade window **2026-08-01 → 2026-08-31** (21 NY sessions; 2026-08-03 is the first RTH session). Config: `config/ema9_trend_risk.example.yaml`. Size: `risk_pct` 1% of equity at the 1.0% initial fill stop. Isolated short (B) is included so the combined-side split has an isolated max DD.

```
python -m dta_bot backtest \
  --config config/ema9_trend_risk.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 \
  --output artifacts/ema9_aug2026_risk_long_short.json \
  --report artifacts/ema9_aug2026_risk_long_short.md
```

| | A. Long-only 1% | B. Short-only 1% | C. Long+short 1% |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 46 (AAPL 24, MSFT 22) | 104 (AAPL 50, MSFT 54) |
| Skips | already_in_position 11, entry_cutoff 28, insufficient_cash 3 | already_in_position 11, entry_cutoff 15 | already_in_position 16, entry_cutoff 33, **opposite_signal_in_trade 23**, insufficient_cash 1 |
| Trades | 15 (MSFT 8, AAPL 7) | 20 (MSFT 12, AAPL 8) | 29 (MSFT 18, AAPL 11) |
| Wins / losses | 11 / 4 | 9 / 11 | 16 / 13 |
| **Win rate** | **73.33%** | **45.00%** | **55.17%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$-2,879.01 (−2.879%)** | **$1,533.99 (1.534%)** |
| Avg win | $697.61 | $643.80 | $708.74 |
| Avg loss | $-546.00 | $-788.48 | $-754.30 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$6,304.92 (6.19%)** | **$4,117.37 (3.96%)** |
| Ending equity | $105,489.78 | $97,120.99 | $101,533.99 |
| Exit mix | lock_stop 6, session_flatten 8, stop 1 | lock_stop 4, stop 7, session_flatten 9 | lock_stop 9, stop 7, session_flatten 13 |
| Lock armed | 6 | 4 | 9 |
| **Exit P&L** | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 | lock_stop $3,752.95; session_flatten $258.38; stop $-6,890.35 | lock_stop $8,557.26; session_flatten $103.31; stop $-7,126.58 |

**A reproduced** the prior August 15m 1% lock-+1% long book exactly: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

**C** kept a profit (**$1,533.99**) but the isolated short book lost **$2,879.01** with a **6.19%** drawdown. Combined is again not A+B (35 trades / $2,610.77 vs 29 / $1,533.99) after **23** `opposite_signal_in_trade` skips.

### August 1% combined by side

| Side | Trades | Wins / losses | Win rate | P&L |
| --- | ---: | ---: | ---: | ---: |
| Long | 10 | 7 / 3 | 70.00% | $3,464.69 |
| Short | 19 | 9 / 10 | 47.37% | $-1,930.70 |

Max DD by side on this window is the isolated 1% book: long **$2,743.31**, short **$6,304.92**. Combined max DD is **$4,117.37**.

## Notes

- Shorts are enabled in the default YAML (`ema9_trend_short.enabled: true`). Disable a side with `enabled: false`.
- One lot per symbol. The engine does not reverse an open long into a short (or the other way). That skip is `opposite_signal_in_trade`.
- `session_flatten` closed shorts as well as longs (B 16 of 41; C 14 of 35 shorts on the 10-share window).
- JSON: `artifacts/ema9_long_short_15m.json`, `artifacts/ema9_aug2026_risk_long_short.json`.
