# EMA9 lock-+1% 15m — SPY+QQQ long-only (Yahoo window) vs AAPL+MSFT

- Generated (UTC): 2026-09-13T23:59:20.130993Z (10-share) / 2026-09-13T23:59:25.835551Z (August 1% risk)
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Window: **2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z** (60 NY session days; ~86 calendar days)
- Bars: SPY 15m 1560; QQQ 15m 1560; AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Universe: **SPY+QQQ** (long-only; shorts parked). AAPL+MSFT is the same long lock-+1% book on the same tape.
- Entry (all books): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close)
- Stop: `stop_mode: lock_plus` — initial fill×0.99; first touch of fill×1.01 moves the stop to fill×1.01 and leaves it (live next bar). No take-profit.
- Configs:
  - SPY+QQQ 10-share: `config/ema9_trend_spy_qqq.example.yaml`
  - SPY+QQQ 1% risk (`stop_pct` 1.0): `config/ema9_trend_risk_spy_qqq.example.yaml`
  - AAPL+MSFT 10-share long-only: `config/ema9_trend_bracket.example.yaml`
  - AAPL+MSFT 1% risk long-only: `config/ema9_trend_risk_nobe_lock1.example.yaml`
- Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_spy_qqq.example.yaml \
  --compare-config config/ema9_trend_bracket.example.yaml \
  --source yahoo --combined-only \
  --output artifacts/ema9_spy_qqq_15m.json \
  --report artifacts/ema9_spy_qqq_15m.md

python -m dta_bot backtest \
  --config config/ema9_trend_risk_spy_qqq.example.yaml \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk_spy_qqq.json \
  --report artifacts/ema9_aug2026_risk_spy_qqq.md
```

Engine totals only. Not annualized. June and September are **partial** months (tape starts mid-June and ends 2026-09-11).

## Data window (do not treat this as multi-year)

Yahoo’s downloader requests `range=60d` for 15m. Asking for `3mo`, `6mo`, or a `period1` older than that cap returns **HTTP 422** (`15m data not available … must be within the last 60 days`). This run’s `60d` request still returned **2026-06-17 → 2026-09-11** — the same calendar start as the prior AAPL/MSFT lock-+1% 15m book.

No other free source was used:

- Alpaca keys are unset.
- HF Data Library has longer 15m history but requires a registered API key (unauthenticated request → 401). Post-2022 it is **IEX-only** (~2–3% of volume), so it is not the same tape as Yahoo regular-session bars and was not mixed in.

Per-month stats below are the four calendar months that actually sit on this tape.

## 1. 10-share full Yahoo 15m window

| | SPY+QQQ 10-share | AAPL+MSFT 10-share |
| --- | ---: | ---: |
| Signals | 136 (SPY 69, QQQ 67) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 41, entry_cutoff 37 | already_in_position 28, entry_cutoff 75 |
| Trades | 58 (QQQ 31, SPY 27) | 51 (MSFT 28, AAPL 23) |
| Wins / losses | 27 / 31 | 31 / 20 |
| **Win rate** | **46.55%** | **60.78%** |
| **Total P&L** | **$-334.30 (−0.334%)** | **$301.49 (0.301%)** |
| Avg win | $30.26 | $27.05 |
| Avg loss | $-37.14 | $-26.85 |
| **Max drawdown** | **$669.37 (0.67%)** | **$130.76 (0.13%)** |
| Ending equity | $99,665.70 | $100,301.49 |
| Exit mix | session_flatten 43, stop 9, lock_stop 6 | lock_stop 20, session_flatten 18, stop 13 |
| Lock armed | 6 | 20 |
| **Exit P&L** | lock_stop $388.62; session_flatten $-75.05; stop $-647.87 | lock_stop $684.73; session_flatten $76.35; stop $-459.59 |
| Max concurrent | 2 (23 ticks with both names open) | 2 (6 ticks with both names open) |

AAPL+MSFT 10-share **reproduced** the prior lock-+1% 15m long book exactly: **51 trades, 60.78%, $301.49**, max DD $130.76.

**SPY+QQQ is a weaker 15m tape for this book.** Same rules, same window: 10-share loses **$635.79** versus AAPL+MSFT and wins less often (46.55% vs 60.78%). Drawdown is about **5×** deeper ($669.37 vs $130.76).

Both index names lost. QQQ was the smaller hole (**31 trades, 16 wins, $-73.31**). SPY was worse (**27 trades, 11 wins, $-260.99**).

The exit mix is the other difference. SPY+QQQ almost never armed the +1% lock (**6 / 58** vs **20 / 51** on AAPL+MSFT). **43 of 58** flats were `session_flatten` and those were a small net loser ($-75.05). The nine initial 1% stops cost **$-647.87** and account for the red book. Lock-stops were the only profitable exit bucket ($388.62).

### Monthly breakdown (realized P&L)

P&L is the sum of trades whose **exit** falls in that NY calendar month. June = 2026-06-17→06-30 (9 sessions). September = 2026-09-01→09-11 (8 sessions).

| Month | Sessions | SPY+QQQ trades | SPY+QQQ win | SPY+QQQ P&L | SPY+QQQ EOM | AAPL+MSFT trades | AAPL+MSFT win | AAPL+MSFT P&L | AAPL+MSFT EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 8 | 62.50% | $114.23 | $100,114.23 | 10 | 40.00% | $-18.75 | $99,981.25 |
| 2026-07 (07-01 → 07-31) | 22 | 26 | 50.00% | $-292.15 | $99,822.08 | 17 | 64.71% | $71.56 | $100,052.81 |
| 2026-08 (08-03 → 08-31) | 21 | 20 | 35.00% | $-132.28 | $99,689.80 | 18 | 77.78% | $304.88 | $100,357.69 |
| 2026-09 (09-01 → 09-11) | 8 | 4 | 50.00% | $-24.10 | $99,665.70 | 6 | 33.33% | $-56.20 | $100,301.49 |
| **Window** | **60** | **58** | **46.55%** | **$-334.30** | **$99,665.70** | **51** | **60.78%** | **$301.49** | **$100,301.49** |

SPY+QQQ 10-share best day: 2026-07-30 **$121.12** (2 trades). Worst day: 2026-07-20 **$-174.00** (3 trades).

June is the only green SPY+QQQ month. July is the hole (26 trades, $-292.15). August, the AAPL+MSFT month (**$304.88** at 77.78%), is red on the indexes (**$-132.28** at 35.00%).

### Weekly (SPY+QQQ 10-share)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W25 (06-17 → 06-18) | 1 | 100.00% | $73.10 | $100,073.10 |
| 2026-W26 (06-22 → 06-26) | 5 | 60.00% | $96.86 | $100,169.96 |
| 2026-W27 (06-29 → 07-02) | 5 | 20.00% | $-213.15 | $99,956.80 |
| 2026-W28 (07-06 → 07-10) | 3 | 100.00% | $86.50 | $100,043.30 |
| 2026-W29 (07-13 → 07-17) | 5 | 60.00% | $-80.24 | $99,963.07 |
| 2026-W30 (07-20 → 07-24) | 9 | 33.33% | $-208.72 | $99,754.34 |
| 2026-W31 (07-27 → 07-31) | 6 | 66.67% | $67.74 | $99,822.08 |
| 2026-W32 (08-03 → 08-07) | 4 | 75.00% | $61.47 | $99,883.55 |
| 2026-W33 (08-10 → 08-14) | 6 | 0.00% | $-122.05 | $99,761.50 |
| 2026-W34 (08-17 → 08-21) | 4 | 50.00% | $-2.95 | $99,758.55 |
| 2026-W35 (08-24 → 08-28) | 6 | 33.33% | $-68.75 | $99,689.80 |
| 2026-W36 (08-31 → 09-04) | 1 | 100.00% | $7.10 | $99,696.90 |
| 2026-W37 (09-08 → 09-11) | 3 | 33.33% | $-31.20 | $99,665.70 |

Peak equity is **$100,169.96** (W26). W27 and W30 give it back. W33 is a 0% week (6 trades, $-122.05).

## 2. August 2026 1% equity risk (`stop_pct` 1.0)

Same noon stack and lock-+1% stop. Size: `shares = floor((0.01 * equity) / (0.01 * entry_price))`. Trade window `--start 2026-08-01 --end 2026-08-31` (warmup bars from 2026-06-17). Writeup companion: `artifacts/ema9_aug2026_risk_spy_qqq.md`.

| | SPY+QQQ 1% risk | AAPL+MSFT 1% risk |
| --- | ---: | ---: |
| Signals | 45 (SPY 24, QQQ 21) | 58 (MSFT 32, AAPL 26) |
| Skips | entry_cutoff 18, insufficient_cash 8, already_in_position 7 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 |
| Trades | 12 (SPY 10, QQQ 2) | 15 (MSFT 8, AAPL 7) |
| Wins / losses | 4 / 8 | 11 / 4 |
| **Win rate** | **33.33%** | **73.33%** |
| **Total P&L** | **$-515.42 (−0.515%)** | **$5,489.78 (5.490%)** |
| Avg win | $305.66 | $697.61 |
| Avg loss | $-217.26 | $-546.00 |
| **Max drawdown** | **$1,674.93 (1.66%)** | **$2,743.31 (2.58%)** |
| Ending equity | $99,484.58 | $105,489.78 |
| Exit mix | session_flatten 11, lock_stop 1 | session_flatten 8, lock_stop 6, stop 1 |
| Lock armed | 1 | 6 |
| **Exit P&L** | lock_stop $993.83; session_flatten $-1,509.25 | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 |
| Size | 129–144 shares | AAPL 329–337; MSFT 203–215 |
| Max concurrent | 1 (0 ticks with both names open) | 1 (0 ticks with both names open) |

AAPL+MSFT August 1% **reproduced** the prior lock-+1% risk book exactly: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

**SPY+QQQ August 1% is red.** 12 trades, 33.33%, **$-515.42**. The one QQQ lock on 2026-08-03 made **$993.83**; the other eleven exits are session flattens that lost **$1,509.25**. No initial 1% stop fired.

A 1% stop on these prices sizes ~full equity (SPY ~$770 → 129–130 shares; QQQ ~$690–734 → 136–144 shares). Max concurrent is **1**, and **8** accepted signals skipped as `insufficient_cash`. That is why QQQ only printed **2** fills (1 win $611.67 net) while SPY printed **10** (3 wins, **$-1,127.10**).

SPY+QQQ 1% best day: 2026-08-03 **$993.83** (1 trade). Worst day: 2026-08-11 **$-409.50** (1 trade). Equity peaked at **$100,993.83** after the first QQQ lock, then bled to $99,484.58.

### August 1% weekly (SPY+QQQ)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W32 (08-03 → 08-07) | 3 | 66.67% | $750.73 | $100,750.73 |
| 2026-W33 (08-10 → 08-14) | 4 | 0.00% | $-927.86 | $99,822.87 |
| 2026-W34 (08-17 → 08-21) | 2 | 50.00% | $-67.87 | $99,755.00 |
| 2026-W35 (08-24 → 08-28) | 3 | 33.33% | $-270.43 | $99,484.58 |
| 2026-W36 (08-31) | 0 | n/a | $0.00 | $99,484.58 |

W33 is the hole: four session-flatten losers, 0%.

### August 1% fills (SPY+QQQ)

| # | Symbol | Qty | Entry (ET) | Exit (ET) | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | QQQ | 144 | 2026-08-03 09:45 @ 690.16 | 2026-08-03 11:15 @ 697.06 | lock_stop | $993.83 |
| 2 | SPY | 130 | 2026-08-06 10:15 @ 771.53 | 2026-08-06 16:00 @ 768.53 | session_flatten | $-390.00 |
| 3 | SPY | 130 | 2026-08-07 09:45 @ 771.99 | 2026-08-07 16:00 @ 773.12 | session_flatten | $146.90 |
| 4 | SPY | 130 | 2026-08-10 11:15 @ 773.82 | 2026-08-10 16:00 @ 773.07 | session_flatten | $-97.50 |
| 5 | SPY | 130 | 2026-08-11 11:00 @ 773.63 | 2026-08-11 16:00 @ 770.48 | session_flatten | $-409.50 |
| 6 | SPY | 129 | 2026-08-12 09:45 @ 772.82 | 2026-08-12 16:00 @ 772.52 | session_flatten | $-38.70 |
| 7 | QQQ | 136 | 2026-08-14 09:45 @ 733.86 | 2026-08-14 16:00 @ 731.05 | session_flatten | $-382.16 |
| 8 | SPY | 129 | 2026-08-19 09:45 @ 770.11 | 2026-08-19 16:00 @ 769.09 | session_flatten | $-131.57 |
| 9 | SPY | 130 | 2026-08-21 09:45 @ 765.16 | 2026-08-21 16:00 @ 765.65 | session_flatten | $63.71 |
| 10 | SPY | 130 | 2026-08-25 09:45 @ 766.15 | 2026-08-25 16:00 @ 765.84 | session_flatten | $-40.95 |
| 11 | SPY | 130 | 2026-08-26 11:00 @ 765.87 | 2026-08-26 16:00 @ 766.01 | session_flatten | $18.20 |
| 12 | SPY | 129 | 2026-08-28 10:30 @ 771.30 | 2026-08-28 16:00 @ 769.38 | session_flatten | $-247.68 |

## What this says about the refined 15m book on SPY+QQQ

On this Yahoo 15m window the noon lock-+1% stack **does take trades** on SPY+QQQ (58 ten-share, 12 August risk). It does **not** look like the AAPL+MSFT book:

1. Win rate sits in the mid-40s (10-share) / low-30s (August 1%), not ~61% / ~73%.
2. The +1% lock almost never arms (6 / 58 ten-share; 1 / 12 August risk). AAPL+MSFT armed 20 / 51 and 6 / 15.
3. Session flatten dominates (43 / 58 and 11 / 12) and is a net loser on the indexes. AAPL+MSFT session flats were green.
4. July and August are the red months on SPY+QQQ; August is the AAPL+MSFT month.
5. 1% of equity at a 1% stop on ~$700–770 names is a near-full-book lot (129–144 shares). Only one name can be open; 8 August signals skipped for cash.

Trade-level rows are in `artifacts/ema9_spy_qqq_15m.json` (10-share) and `artifacts/ema9_aug2026_risk_spy_qqq.json` (August 1%). Daily books are in each run’s `period_stats.daily`.

## Assumptions (engine)

- Signals come from the live `evaluate_rule` path (same EMA/SMA/RSI detectors).
- Fill at the next 15m bar open. One open lot per symbol; no pyramiding. Shorts are parked (not in these YAMLs).
- Lock-plus: initial stop fill×0.99; first bar high ≥ fill×1.01 locks the stop to fill×1.01 from the **next** bar. Same-bar pullback after the tag still uses the initial stop.
- `flatten_by` 15:55 flats the 15:45 ET bar close (`session_flatten`) if stop/lock has not already filled.
- Open lots on the last bar flatten at the last close (`eod`). None of these books used `eod`.
- Yahoo regular-session bars, unadjusted OHLC. commission=$0.00/fill, slippage=0.0%.
- Starting equity $100,000. Risk size: `shares = floor((0.01 * equity) / (0.01 * entry_price))`.
