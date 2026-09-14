# EMA9 lock-+1% 15m — NVDA+AMD long-only vs AAPL+MSFT and SPY+QQQ

- Generated (UTC): 2026-09-14T00:42:17.778538Z (10-share) / 2026-09-14T00:42:22.160560Z (August 1% risk)
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Window: **2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z** (60 NY session days; ~86 calendar days)
- Bars: NVDA 15m 1560; AMD 15m 1560; AAPL 15m 1560; MSFT 15m 1560; SPY 15m 1560; QQQ 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Universe: **NVDA+AMD** (long-only; shorts parked). AAPL+MSFT and SPY+QQQ are the same long lock-+1% book on the same tape.
- Entry (all books): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close)
- Stop: `stop_mode: lock_plus` — initial fill×0.99; first touch of fill×1.01 moves the stop to fill×1.01 and leaves it (live next bar). No take-profit.
- Configs:
  - NVDA+AMD 10-share: `config/ema9_trend_nvda_amd.example.yaml`
  - NVDA+AMD 1% risk (`stop_pct` 1.0): `config/ema9_trend_risk_nvda_amd.example.yaml`
  - AAPL+MSFT 10-share long-only: `config/ema9_trend_bracket.example.yaml`
  - AAPL+MSFT 1% risk long-only: `config/ema9_trend_risk_nobe_lock1.example.yaml`
  - SPY+QQQ 10-share long-only: `config/ema9_trend_spy_qqq.example.yaml`
  - SPY+QQQ 1% risk long-only: `config/ema9_trend_risk_spy_qqq.example.yaml`
- Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_nvda_amd.example.yaml \
  --compare-config config/ema9_trend_bracket.example.yaml \
  --compare-config config/ema9_trend_spy_qqq.example.yaml \
  --source yahoo --combined-only \
  --output artifacts/ema9_nvda_amd_15m.json \
  --report artifacts/ema9_nvda_amd_15m.md

python -m dta_bot backtest \
  --config config/ema9_trend_risk_nvda_amd.example.yaml \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --compare-config config/ema9_trend_risk_spy_qqq.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk_nvda_amd.json \
  --report artifacts/ema9_aug2026_risk_nvda_amd.md
```

Engine totals only. Not annualized. June and September are **partial** months (tape starts mid-June and ends 2026-09-11).

## Data window (do not treat this as multi-year)

Yahoo’s downloader requests `range=60d` for 15m. Asking for `3mo`, `6mo`, or a `period1` older than that cap returns **HTTP 422** (`15m data not available … must be within the last 60 days`). This run’s `60d` request still returned **2026-06-17 → 2026-09-11** — the same calendar start as the prior AAPL/MSFT and SPY/QQQ lock-+1% 15m books.

No other free source was used:

- Alpaca keys are unset.
- HF Data Library has longer 15m history but requires a registered API key (unauthenticated request → 401). Post-2022 it is **IEX-only** (~2–3% of volume), so it is not the same tape as Yahoo regular-session bars and was not mixed in.

Per-month stats below are the four calendar months that actually sit on this tape.

## 1. 10-share full Yahoo 15m window

| | NVDA+AMD 10-share | AAPL+MSFT 10-share | SPY+QQQ 10-share |
| --- | ---: | ---: | ---: |
| Signals | 140 (NVDA 70, AMD 70) | 154 (AAPL 77, MSFT 77) | 136 (SPY 69, QQQ 67) |
| Skips | entry_cutoff 63, already_in_position 11, no_next_bar 1 | entry_cutoff 75, already_in_position 28 | already_in_position 41, entry_cutoff 37 |
| Trades | 65 (NVDA 33, AMD 32) | 51 (MSFT 28, AAPL 23) | 58 (QQQ 31, SPY 27) |
| Wins / losses | 26 / 39 | 31 / 20 | 27 / 31 |
| **Win rate** | **40.00%** | **60.78%** | **46.55%** |
| **Total P&L** | **$-526.40 (−0.526%)** | **$301.49 (0.301%)** | **$-334.30 (−0.334%)** |
| Avg win | $31.96 | $27.05 | $30.26 |
| Avg loss | $-34.81 | $-26.85 | $-37.14 |
| **Max drawdown** | **$600.73 (0.60%)** | **$130.76 (0.13%)** | **$669.37 (0.67%)** |
| Ending equity | $99,473.60 | $100,301.49 | $99,665.70 |
| Exit mix | stop 35, lock_stop 23, session_flatten 7 | lock_stop 20, session_flatten 18, stop 13 | session_flatten 43, stop 9, lock_stop 6 |
| Lock armed | 25 | 20 | 6 |
| **Exit P&L** | lock_stop $609.35; session_flatten $159.10; stop $-1,294.85 | lock_stop $684.73; session_flatten $76.35; stop $-459.59 | lock_stop $388.62; session_flatten $-75.05; stop $-647.87 |
| Max concurrent | 2 (13 ticks with both names open) | 2 (6 ticks with both names open) | 2 (23 ticks with both names open) |

AAPL+MSFT 10-share **reproduced** the prior lock-+1% 15m long book exactly: **51 trades, 60.78%, $301.49**, max DD $130.76.

SPY+QQQ 10-share **reproduced** the prior index book exactly: **58 trades, 46.55%, $-334.30**, max DD $669.37.

**NVDA+AMD is the weakest 15m tape of the three.** Same rules, same window: 10-share loses **$827.89** versus AAPL+MSFT and **$192.10** versus SPY+QQQ. Win rate is 40.00% vs 60.78% / 46.55%. Drawdown ($600.73) is about **4.6×** AAPL+MSFT ($130.76) and a bit shallower than SPY+QQQ ($669.37).

Both chip names lost. NVDA was the smaller hole (**33 trades, 15 wins, $-67.97**). AMD was worse (**32 trades, 11 wins, $-458.44**).

The exit mix is the other difference. These names **do** arm the +1% lock (**25 / 65**, vs 20 / 51 AAPL+MSFT and 6 / 58 SPY+QQQ). Lock-stops were profitable ($609.35) and the seven session flats were also green ($159.10). The book is red because the **initial 1% stop fired 35 times** and cost **$-1,294.85**. SPY+QQQ almost never locked and bled on session flatten; NVDA+AMD gets stopped out instead of held to 15:55.

### Monthly breakdown (realized P&L)

P&L is the sum of trades whose **exit** falls in that NY calendar month. June = 2026-06-17→06-30 (9 sessions). September = 2026-09-01→09-11 (8 sessions).

| Month | Sessions | NVDA+AMD trades | NVDA+AMD win | NVDA+AMD P&L | NVDA+AMD EOM | AAPL+MSFT trades | AAPL+MSFT win | AAPL+MSFT P&L | AAPL+MSFT EOM | SPY+QQQ trades | SPY+QQQ win | SPY+QQQ P&L | SPY+QQQ EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 12 | 50.00% | $-103.96 | $99,896.04 | 10 | 40.00% | $-18.75 | $99,981.25 | 8 | 62.50% | $114.23 | $100,114.23 |
| 2026-07 (07-01 → 07-31) | 22 | 25 | 40.00% | $-99.95 | $99,796.09 | 17 | 64.71% | $71.56 | $100,052.81 | 26 | 50.00% | $-292.15 | $99,822.08 |
| 2026-08 (08-03 → 08-31) | 21 | 20 | 35.00% | $-305.01 | $99,491.08 | 18 | 77.78% | $304.88 | $100,357.69 | 20 | 35.00% | $-132.28 | $99,689.80 |
| 2026-09 (09-01 → 09-11) | 8 | 8 | 37.50% | $-17.49 | $99,473.60 | 6 | 33.33% | $-56.20 | $100,301.49 | 4 | 50.00% | $-24.10 | $99,665.70 |
| **Window** | **60** | **65** | **40.00%** | **$-526.40** | **$99,473.60** | **51** | **60.78%** | **$301.49** | **$100,301.49** | **58** | **46.55%** | **$-334.30** | **$99,665.70** |

NVDA+AMD 10-share best day: 2026-07-30 **$137.40** (2 trades). Worst day: 2026-06-24 **$-104.16** (2 trades).

Every NVDA+AMD month is red. August is the hole (20 trades, 35.00%, **$-305.01**) — the same month AAPL+MSFT printed **$304.88** at 77.78%. SPY+QQQ August is also red ($-132.28 at 35.00%), but smaller than the chip book.

### Weekly (NVDA+AMD 10-share)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W25 (06-17 → 06-18) | 2 | 100.00% | $23.96 | $100,023.96 |
| 2026-W26 (06-22 → 06-26) | 8 | 37.50% | $-112.95 | $99,911.01 |
| 2026-W27 (06-29 → 07-02) | 3 | 33.33% | $-34.87 | $99,876.15 |
| 2026-W28 (07-06 → 07-10) | 6 | 83.33% | $74.82 | $99,950.97 |
| 2026-W29 (07-13 → 07-17) | 5 | 20.00% | $-101.42 | $99,849.55 |
| 2026-W30 (07-20 → 07-24) | 10 | 30.00% | $-140.91 | $99,708.65 |
| 2026-W31 (07-27 → 07-31) | 3 | 33.33% | $87.44 | $99,796.09 |
| 2026-W32 (08-03 → 08-07) | 4 | 75.00% | $65.70 | $99,861.79 |
| 2026-W33 (08-10 → 08-14) | 7 | 42.86% | $-85.06 | $99,776.73 |
| 2026-W34 (08-17 → 08-21) | 3 | 33.33% | $-53.43 | $99,723.30 |
| 2026-W35 (08-24 → 08-28) | 5 | 0.00% | $-185.11 | $99,538.19 |
| 2026-W36 (08-31 → 09-04) | 7 | 28.57% | $-95.91 | $99,442.28 |
| 2026-W37 (09-08 → 09-11) | 2 | 50.00% | $31.32 | $99,473.60 |

Peak equity is **$100,023.96** (W25). W26 gives it back. W30 and W35 are the other holes. W35 is a 0% week (5 trades, $-185.11).

## 2. August 2026 1% equity risk (`stop_pct` 1.0)

Same noon stack and lock-+1% stop. Size: `shares = floor((0.01 * equity) / (0.01 * entry_price))`. Trade window `--start 2026-08-01 --end 2026-08-31` (warmup bars from 2026-06-17). Writeup companion: `artifacts/ema9_aug2026_risk_nvda_amd.md`.

| | NVDA+AMD 1% risk | AAPL+MSFT 1% risk | SPY+QQQ 1% risk |
| --- | ---: | ---: | ---: |
| Signals | 48 (AMD 25, NVDA 23) | 58 (MSFT 32, AAPL 26) | 45 (SPY 24, QQQ 21) |
| Skips | entry_cutoff 24, already_in_position 4, insufficient_cash 2 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 18, insufficient_cash 8, already_in_position 7 |
| Trades | 16 (NVDA 8, AMD 8) | 15 (MSFT 8, AAPL 7) | 12 (SPY 10, QQQ 2) |
| Wins / losses | 4 / 12 | 11 / 4 | 4 / 8 |
| **Win rate** | **25.00%** | **73.33%** | **33.33%** |
| **Total P&L** | **$-7,292.55 (−7.293%)** | **$5,489.78 (5.490%)** | **$-515.42 (−0.515%)** |
| Avg win | $919.21 | $697.61 | $305.66 |
| Avg loss | $-914.12 | $-546.00 | $-217.26 |
| **Max drawdown** | **$8,311.13 (8.23%)** | **$2,743.31 (2.58%)** | **$1,674.93 (1.66%)** |
| Ending equity | $92,707.45 | $105,489.78 | $99,484.58 |
| Exit mix | stop 11, lock_stop 4, session_flatten 1 | session_flatten 8, lock_stop 6, stop 1 | session_flatten 11, lock_stop 1 |
| Lock armed | 4 | 6 | 1 |
| **Exit P&L** | lock_stop $3,676.85; session_flatten $-240.35; stop $-10,729.05 | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 | lock_stop $993.83; session_flatten $-1,509.25 |
| Size | NVDA 437–494; AMD 197–209 | AAPL 329–337; MSFT 203–215 | 129–144 shares |
| Max concurrent | 1 (0 ticks with both names open) | 1 (0 ticks with both names open) | 1 (0 ticks with both names open) |

AAPL+MSFT August 1% **reproduced** the prior lock-+1% risk book exactly: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

SPY+QQQ August 1% **reproduced** the prior index risk book exactly: **12 trades, 33.33%, $-515.42**, max DD $1,674.93.

**NVDA+AMD August 1% is the red book.** 16 trades, 25.00%, **$-7,292.55**. The four locks made **$3,676.85**. Eleven initial 1% stops cost **$-10,729.05**. The one session flatten lost **$-240.35**.

A 1% stop on these prices sizes ~full equity (NVDA ~$202–226 → 437–494 shares; AMD ~$468–493 → 197–209 shares). Max concurrent is **1**, and **2** accepted signals skipped as `insufficient_cash`. NVDA: 8 trades, 3 wins, **$-1,351.07**. AMD: 8 trades, 1 win, **$-5,941.48**.

NVDA+AMD 1% best day: 2026-08-12 **$987.09** (1 trade). Worst day: 2026-08-25 **$-1,936.96** (2 trades). Equity peaked at **$100,973.18** after the first NVDA lock on 2026-08-03, then bled to $92,707.45.

### August 1% weekly (NVDA+AMD)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W32 (08-03 → 08-07) | 3 | 66.67% | $836.09 | $100,836.09 |
| 2026-W33 (08-10 → 08-14) | 5 | 20.00% | $-2,251.01 | $98,585.08 |
| 2026-W34 (08-17 → 08-21) | 2 | 50.00% | $-135.24 | $98,449.84 |
| 2026-W35 (08-24 → 08-28) | 5 | 0.00% | $-4,809.69 | $93,640.15 |
| 2026-W36 (08-31) | 1 | 0.00% | $-932.70 | $92,707.45 |

W35 is the hole: five 1% stops, 0%.

### August 1% fills (NVDA+AMD)

| # | Symbol | Qty | Entry (ET) | Exit (ET) | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | NVDA | 494 | 2026-08-03 10:00 @ 202.23 | 2026-08-03 10:30 @ 204.20 | lock_stop | $973.18 |
| 2 | NVDA | 454 | 2026-08-06 09:45 @ 222.06 | 2026-08-06 10:30 @ 219.84 | stop | $-1,008.15 |
| 3 | NVDA | 449 | 2026-08-07 09:45 @ 222.27 | 2026-08-07 11:45 @ 224.21 | lock_stop | $871.06 |
| 4 | AMD | 209 | 2026-08-10 10:15 @ 480.43 | 2026-08-10 10:30 @ 475.63 | stop | $-1,004.10 |
| 5 | NVDA | 452 | 2026-08-11 09:45 @ 220.56 | 2026-08-11 12:15 @ 218.35 | stop | $-996.93 |
| 6 | NVDA | 446 | 2026-08-12 09:45 @ 221.32 | 2026-08-12 10:15 @ 223.53 | lock_stop | $987.09 |
| 7 | AMD | 202 | 2026-08-13 09:45 @ 493.42 | 2026-08-13 15:15 @ 488.49 | stop | $-996.71 |
| 8 | NVDA | 437 | 2026-08-14 09:45 @ 225.71 | 2026-08-14 16:00 @ 225.16 | session_flatten | $-240.35 |
| 9 | AMD | 208 | 2026-08-20 09:45 @ 471.52 | 2026-08-20 10:00 @ 466.80 | stop | $-980.76 |
| 10 | AMD | 208 | 2026-08-21 11:15 @ 468.21 | 2026-08-21 15:30 @ 472.28 | lock_stop | $845.52 |
| 11 | AMD | 208 | 2026-08-24 09:30 @ 467.98 | 2026-08-24 09:45 @ 463.30 | stop | $-973.39 |
| 12 | NVDA | 458 | 2026-08-25 09:45 @ 212.64 | 2026-08-25 11:15 @ 210.51 | stop | $-973.89 |
| 13 | NVDA | 456 | 2026-08-25 11:30 @ 211.20 | 2026-08-25 14:15 @ 209.09 | stop | $-963.07 |
| 14 | AMD | 197 | 2026-08-26 11:30 @ 484.29 | 2026-08-26 16:00 @ 479.45 | stop | $-954.05 |
| 15 | AMD | 199 | 2026-08-28 10:00 @ 475.02 | 2026-08-28 12:00 @ 470.27 | stop | $-945.29 |
| 16 | AMD | 198 | 2026-08-31 10:00 @ 471.06 | 2026-08-31 11:15 @ 466.35 | stop | $-932.70 |

## What this says about the refined 15m book on NVDA+AMD

On this Yahoo 15m window the noon lock-+1% stack **does take trades** on NVDA+AMD (65 ten-share, 16 August risk). It does **not** look like the AAPL+MSFT book, and it is **worse than SPY+QQQ**:

1. Win rate sits at 40% (10-share) / 25% (August 1%), not ~61% / ~73% (AAPL+MSFT) or even the mid-40s / low-30s (SPY+QQQ).
2. The +1% lock **does** arm (25 / 65 ten-share; 4 / 16 August risk). That is closer to AAPL+MSFT (20 / 51; 6 / 15) than to SPY+QQQ (6 / 58; 1 / 12). The locks themselves are green. The hole is the **initial 1% stop** (35 / 65 and 11 / 16).
3. Session flatten is rare (7 / 65 and 1 / 16). These names move enough to hit stop or lock before 15:55. SPY+QQQ is the opposite (43 / 58 and 11 / 12 session flats).
4. Every 10-share month is red. August is the chip hole ($-305.01 ten-share; **$-7,292.55** at 1% risk) and the AAPL+MSFT month ($304.88 / $5,489.78).
5. 1% of equity at a 1% stop on ~$210 NVDA / ~$480 AMD is a near-full-book lot (437–494 / 197–209 shares). Only one name can be open; 2 August signals skipped for cash. AMD’s eight August fills are almost all 1% stops (1 lock, 0 session flatten).

Trade-level rows are in `artifacts/ema9_nvda_amd_15m.json` (10-share) and `artifacts/ema9_aug2026_risk_nvda_amd.json` (August 1%). Daily books are in each run’s `period_stats.daily`.

## Assumptions (engine)

- Signals come from the live `evaluate_rule` path (same EMA/SMA/RSI detectors).
- Fill at the next 15m bar open. One open lot per symbol; no pyramiding. Shorts are parked (not in these YAMLs).
- Lock-plus: initial stop fill×0.99; first bar high ≥ fill×1.01 locks the stop to fill×1.01 from the **next** bar. Same-bar pullback after the tag still uses the initial stop.
- `flatten_by` 15:55 flats the 15:45 ET bar close (`session_flatten`) if stop/lock has not already filled.
- Open lots on the last bar flatten at the last close (`eod`). None of these books used `eod`.
- Yahoo regular-session bars, unadjusted OHLC. commission=$0.00/fill, slippage=0.0%.
- Starting equity $100,000. Risk size: `shares = floor((0.01 * equity) / (0.01 * entry_price))`.
