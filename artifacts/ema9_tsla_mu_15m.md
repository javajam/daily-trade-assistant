# EMA9 lock-+1% 15m — TSLA+MU (Yahoo window) vs AAPL+MSFT

- Generated (UTC): 2026-09-13T23:15:13.738140Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Window: **2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z** (60 NY session days; ~86 calendar days)
- Bars: TSLA 15m 1560; MU 15m 1560; AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry (all four books): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close)
- Stop: `stop_mode: lock_plus` — initial fill×0.99; first touch of fill×1.01 moves the stop to fill×1.01 and leaves it (live next bar). No take-profit.
- Configs:
  - TSLA+MU 10-share: `config/ema9_trend_tsla_mu.example.yaml`
  - TSLA+MU 1% risk (`stop_pct` 1.0): `config/ema9_trend_risk_tsla_mu.example.yaml`
  - AAPL+MSFT 10-share: `config/ema9_trend.example.yaml`
  - AAPL+MSFT 1% risk: `config/ema9_trend_risk.example.yaml`
- Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_tsla_mu.example.yaml \
  --compare-config config/ema9_trend_risk_tsla_mu.example.yaml \
  --compare-config config/ema9_trend.example.yaml \
  --compare-config config/ema9_trend_risk.example.yaml \
  --source yahoo --combined-only \
  --output artifacts/ema9_tsla_mu_15m.json \
  --report artifacts/ema9_tsla_mu_15m.md
```

Engine totals only. Not annualized. June and September are **partial** months (tape starts mid-June and ends 2026-09-11).

## Data window (do not treat this as multi-year)

Yahoo’s downloader requests `range=60d` for 15m. Asking for `3mo`, `6mo`, or a `period1` older than that cap returns **HTTP 422** (`15m data not available … must be within the last 60 days`). This run’s `60d` request still returned **2026-06-17 → 2026-09-11** — the same calendar start as the prior AAPL/MSFT lock-+1% 15m book.

No other free source was used:

- Alpaca keys are unset.
- HF Data Library has longer 15m history but requires a registered API key (unauthenticated request → 401). Post-2022 it is **IEX-only** (~2–3% of volume), so it is not the same tape as Yahoo regular-session bars and was not mixed in.

Per-month stats below are the four calendar months that actually sit on this tape.

## Side-by-side (overall)

| | TSLA+MU 10-share | TSLA+MU 1% risk | AAPL+MSFT 10-share | AAPL+MSFT 1% risk |
| --- | ---: | ---: | ---: | ---: |
| Signals | 136 (MU 79, TSLA 57) | 136 (MU 79, TSLA 57) | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 14, entry_cutoff 70 | already_in_position 13, entry_cutoff 71, insufficient_cash 3 | already_in_position 28, entry_cutoff 75 | already_in_position 17, entry_cutoff 84, insufficient_cash 8 |
| Trades | 52 (MU 29, TSLA 23) | 43 (MU 24, TSLA 19) | 51 (MSFT 28, AAPL 23) | 42 (MSFT 25, AAPL 17) |
| Wins / losses | 23 / 29 | 20 / 23 | 31 / 20 | 26 / 16 |
| **Win rate** | **44.23%** | **46.51%** | **60.78%** | **61.90%** |
| **Total P&L** | **$131.12 (0.131%)** | **$18.45 (0.018%)** | **$301.49 (0.301%)** | **$6,833.28 (6.833%)** |
| Avg win | $79.49 | $1,048.72 | $27.05 | $754.24 |
| Avg loss | $-58.52 | $-911.13 | $-26.85 | $-798.56 |
| **Max drawdown** | **$456.89 (0.45%)** | **$5,903.01 (5.59%)** | **$130.76 (0.13%)** | **$3,316.23 (3.27%)** |
| Ending equity | $100,131.12 | $100,018.45 | $100,301.49 | $106,833.28 |
| Exit mix | lock_stop 23, stop 24, session_flatten 5 | lock_stop 20, stop 19, session_flatten 4 | lock_stop 20, stop 13, session_flatten 18 | lock_stop 17, stop 11, session_flatten 14 |
| Lock armed | 24 | 21 | 20 | 17 |
| **Exit P&L** | lock_stop $1,347.11; session_flatten $379.63; stop $-1,595.63 | lock_stop $15,689.87; session_flatten $3,720.03; stop $-19,391.45 | lock_stop $684.73; session_flatten $76.35; stop $-459.59 | lock_stop $16,068.71; session_flatten $2,031.65; stop $-11,267.08 |

AAPL+MSFT 10-share **reproduced** the prior lock-+1% 15m book exactly: **51 trades, 60.78%, $301.49**, max DD $130.76.

**TSLA+MU is a weaker 15m tape for this book.** Same rules, same window: 10-share makes **$170.37 less** than AAPL+MSFT and loses more often (44% vs 61%). 1% equity risk on TSLA+MU is almost flat (**$18.45**) with a **5.59%** drawdown; the same sizing on AAPL+MSFT made **$6,833.28**.

MU carried the TSLA+MU 10-share book (**29 trades, 16 wins, $437.15**). TSLA was a net loser (**23 trades, 7 wins, $-306.03**). On 1% risk that split is larger: MU **$7,116.80** (24 trades, 15 wins) vs TSLA **$-7,098.34** (19 trades, 5 wins). Risk sizing used 86–338 shares (MU ~90 at ~$1,100; TSLA ~250–280 at ~$370). Three accepted TSLA/MU risk signals skipped for `insufficient_cash`.

## Monthly breakdown (realized P&L)

P&L is the sum of trades whose **exit** falls in that NY calendar month. June = 2026-06-17→06-30 (9 sessions). September = 2026-09-01→09-11 (8 sessions).

### TSLA+MU

| Month | Sessions | 10-share trades | 10-share win | 10-share P&L | 10-share EOM | 1% risk trades | 1% risk win | 1% risk P&L | 1% risk EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 7 | 57.14% | $128.57 | $100,128.57 | 7 | 57.14% | $235.11 | $100,235.11 |
| 2026-07 (07-01 → 07-31) | 22 | 19 | 42.11% | $138.98 | $100,267.54 | 12 | 50.00% | $3,240.35 | $103,475.46 |
| 2026-08 (08-03 → 08-31) | 21 | 14 | 50.00% | $46.98 | $100,314.53 | 14 | 50.00% | $-362.99 | $103,112.47 |
| 2026-09 (09-01 → 09-11) | 8 | 12 | 33.33% | $-183.41 | $100,131.12 | 10 | 30.00% | $-3,094.01 | $100,018.45 |
| **Window** | **60** | **52** | **44.23%** | **$131.12** | **$100,131.12** | **43** | **46.51%** | **$18.45** | **$100,018.45** |

10-share best day: 2026-07-08 **$469.70** (1 trade). Worst day: 2026-09-11 **$-182.42** (4 trades).

1% risk best day: 2026-07-08 **$4,931.85** (1 trade). Worst day: 2026-09-11 **$-2,091.73** (3 trades).

July’s one large MU lock is most of the 1% risk profit; the first 11 sessions of September give it back.

### AAPL+MSFT (same window, context)

| Month | Sessions | 10-share trades | 10-share win | 10-share P&L | 10-share EOM | 1% risk trades | 1% risk win | 1% risk P&L | 1% risk EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 10 | 40.00% | $-18.75 | $99,981.25 | 8 | 50.00% | $280.58 | $100,280.58 |
| 2026-07 (07-01 → 07-31) | 22 | 17 | 64.71% | $71.56 | $100,052.81 | 14 | 64.29% | $2,068.75 | $102,349.33 |
| 2026-08 (08-03 → 08-31) | 21 | 18 | 77.78% | $304.88 | $100,357.69 | 15 | 73.33% | $5,624.36 | $107,973.69 |
| 2026-09 (09-01 → 09-11) | 8 | 6 | 33.33% | $-56.20 | $100,301.49 | 5 | 40.00% | $-1,140.41 | $106,833.28 |
| **Window** | **60** | **51** | **60.78%** | **$301.49** | **$100,301.49** | **42** | **61.90%** | **$6,833.28** | **$106,833.28** |

August is the AAPL+MSFT month. September is red on both universes.

## Weekly (TSLA+MU)

| Week | 10-share trades | 10-share win | 10-share P&L | 10-share EOW | 1% risk trades | 1% risk win | 1% risk P&L | 1% risk EOW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-W25 (06-17 → 06-18) | 1 | 100.00% | $70.60 | $100,070.60 | 1 | 100.00% | $635.41 | $100,635.41 |
| 2026-W26 (06-22 → 06-26) | 5 | 40.00% | $-56.66 | $100,013.94 | 5 | 40.00% | $-1,386.12 | $99,249.29 |
| 2026-W27 (06-29 → 07-02) | 3 | 66.67% | $42.63 | $100,056.57 | 2 | 50.00% | $-8.69 | $99,240.59 |
| 2026-W28 (07-06 → 07-10) | 4 | 25.00% | $309.10 | $100,365.67 | 2 | 50.00% | $4,453.05 | $103,693.65 |
| 2026-W29 (07-13 → 07-17) | 5 | 20.00% | $-168.93 | $100,196.73 | 3 | 33.33% | $-1,662.38 | $102,031.27 |
| 2026-W30 (07-20 → 07-24) | 5 | 60.00% | $-10.89 | $100,185.85 | 4 | 75.00% | $1,453.30 | $103,484.57 |
| 2026-W31 (07-27 → 07-31) | 3 | 66.67% | $81.70 | $100,267.54 | 2 | 50.00% | $-9.11 | $103,475.46 |
| 2026-W32 (08-03 → 08-07) | 3 | 66.67% | $29.48 | $100,297.02 | 3 | 66.67% | $319.15 | $103,794.61 |
| 2026-W33 (08-10 → 08-14) | 4 | 75.00% | $161.92 | $100,458.94 | 4 | 75.00% | $1,743.27 | $105,537.88 |
| 2026-W34 (08-17 → 08-21) | 2 | 0.00% | $-108.51 | $100,350.43 | 2 | 0.00% | $-1,400.91 | $104,136.96 |
| 2026-W35 (08-24 → 08-28) | 5 | 40.00% | $-35.91 | $100,314.53 | 5 | 40.00% | $-1,024.49 | $103,112.47 |
| 2026-W36 (08-31 → 09-04) | 4 | 75.00% | $158.88 | $100,473.40 | 4 | 75.00% | $1,733.90 | $104,846.36 |
| 2026-W37 (09-08 → 09-11) | 8 | 12.50% | $-342.28 | $100,131.12 | 6 | 0.00% | $-4,827.91 | $100,018.45 |

W37 (four sessions) is the hole: 8 ten-share trades at 12.5% / $-342.28, and 6 risk trades at 0% / $-4,827.91.

## What this says about the refined 15m book on TSLA+MU

On this Yahoo 15m window the noon lock-+1% stack **does take trades** on TSLA+MU (52 ten-share, 43 risk). It does **not** look like the AAPL+MSFT book:

1. Win rate sits in the mid-40s, not ~60%.
2. Stops outnumber lock_stops (24 vs 23 on 10-share). AAPL+MSFT was the opposite (13 stops vs 20 lock_stops).
3. Session flattens are rare (5 / 4) versus 18 / 14 on AAPL+MSFT — more names hit the 1% stop or the +1% lock before 15:55.
4. **September 1–11 erased the summer.** 10-share peaked around $100,473 (W36) and finished $100,131. 1% risk peaked around $105,538 (W33) and finished $100,018.
5. 1% of equity at a 1% stop on high-priced names is a large lot (86–338 shares). The path is the same signals as 10-share, scaled; three fills were skipped for cash.

Trade-level rows are in `artifacts/ema9_tsla_mu_15m.json`. Daily books are in each run’s `period_stats.daily`.

## Assumptions (engine)

- Signals come from the live `evaluate_rule` path (same EMA/SMA/RSI detectors).
- Fill at the next 15m bar open. One open lot per symbol; no pyramiding.
- Lock-plus: initial stop fill×0.99; first bar high ≥ fill×1.01 locks the stop to fill×1.01 from the **next** bar. Same-bar pullback after the tag still uses the initial stop.
- `flatten_by` 15:55 flats the 15:45 ET bar close (`session_flatten`) if stop/lock has not already filled.
- Open lots on the last bar flatten at the last close (`eod`). None of these four books used `eod`.
- Yahoo regular-session bars, unadjusted OHLC. commission=$0.00/fill, slippage=0.0%.
- Starting equity $100,000. Risk size: `shares = floor((0.01 * equity) / (0.01 * entry_price))`.
