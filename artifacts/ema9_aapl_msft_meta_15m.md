# EMA9 lock-+1% 15m — AAPL+MSFT+META long-only vs AAPL+MSFT

- Generated (UTC): 2026-09-14T00:50:46.528903Z (10-share) / 2026-09-14T00:50:53.385634Z (August 1% risk)
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Window: **2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z** (60 NY session days; ~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560; META 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Universe: **AAPL+MSFT+META** (long-only; shorts parked). AAPL+MSFT is the same long lock-+1% book on the same tape. Isolated META is `--breakout META`.
- Entry (all books): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York (15m flatten = 15:45 ET bar close)
- Stop: `stop_mode: lock_plus` — initial fill×0.99; first touch of fill×1.01 moves the stop to fill×1.01 and leaves it (live next bar). No take-profit.
- Configs:
  - AAPL+MSFT+META 10-share: `config/ema9_trend_aapl_msft_meta.example.yaml`
  - AAPL+MSFT+META 1% risk (`stop_pct` 1.0): `config/ema9_trend_risk_aapl_msft_meta.example.yaml`
  - AAPL+MSFT 10-share long-only: `config/ema9_trend_bracket.example.yaml`
  - AAPL+MSFT 1% risk long-only: `config/ema9_trend_risk_nobe_lock1.example.yaml`
- Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_aapl_msft_meta.example.yaml \
  --compare-config config/ema9_trend_bracket.example.yaml \
  --source yahoo --combined-only --breakout META \
  --output artifacts/ema9_aapl_msft_meta_15m.json \
  --report artifacts/ema9_aapl_msft_meta_15m.md

python -m dta_bot backtest \
  --config config/ema9_trend_risk_aapl_msft_meta.example.yaml \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --breakout META \
  --output artifacts/ema9_aug2026_risk_aapl_msft_meta.json \
  --report artifacts/ema9_aug2026_risk_aapl_msft_meta.md
```

Engine totals only. Not annualized. June and September are **partial** months (tape starts mid-June and ends 2026-09-11).

## Data window (do not treat this as multi-year)

Yahoo’s downloader requests `range=60d` for 15m. Asking for `3mo`, `6mo`, or a `period1` older than that cap returns **HTTP 422** (`15m data not available … must be within the last 60 days`). This run’s `60d` request still returned **2026-06-17 → 2026-09-11** — the same calendar start as the prior AAPL/MSFT lock-+1% 15m book.

No other free source was used:

- Alpaca keys are unset.
- HF Data Library has longer 15m history but requires a registered API key (unauthenticated request → 401). Post-2022 it is **IEX-only** (~2–3% of volume), so it is not the same tape as Yahoo regular-session bars and was not mixed in.

Per-month stats below are the four calendar months that actually sit on this tape.

## 1. 10-share full Yahoo 15m window

| | AAPL+MSFT+META 10-share | AAPL+MSFT 10-share | Isolated META 10-share |
| --- | ---: | ---: | ---: |
| Signals | 225 (AAPL 77, MSFT 77, META 71) | 154 (AAPL 77, MSFT 77) | 71 (META 71) |
| Skips | entry_cutoff 109, already_in_position 37 | entry_cutoff 75, already_in_position 28 | entry_cutoff 34, already_in_position 9 |
| Trades | 79 (MSFT 28, META 28, AAPL 23) | 51 (MSFT 28, AAPL 23) | 28 (META 28) |
| Wins / losses | 45 / 34 | 31 / 20 | 14 / 14 |
| **Win rate** | **56.96%** | **60.78%** | **50.00%** |
| **Total P&L** | **$179.35 (0.179%)** | **$301.49 (0.301%)** | **$-122.13 (−0.122%)** |
| Avg win | $34.10 | $27.05 | $49.73 |
| Avg loss | $-39.86 | $-26.85 | $-58.45 |
| **Max drawdown** | **$346.37 (0.34%)** | **$130.76 (0.13%)** | **$342.82 (0.34%)** |
| Ending equity | $100,179.35 | $100,301.49 | $99,877.87 |
| Exit mix | lock_stop 33, stop 24, session_flatten 22 | lock_stop 20, session_flatten 18, stop 13 | lock_stop 13, stop 11, session_flatten 4 |
| Lock armed | 34 | 20 | 14 |
| **Exit P&L** | lock_stop $1,240.34; session_flatten $81.52; stop $-1,142.51 | lock_stop $684.73; session_flatten $76.35; stop $-459.59 | lock_stop $555.61; session_flatten $5.18; stop $-682.91 |
| Max concurrent | 3 (22 ticks with 2+ names open) | 2 (6 ticks with both names open) | 1 (0 ticks with 2+ names open) |

AAPL+MSFT 10-share **reproduced** the prior lock-+1% 15m long book exactly: **51 trades, 60.78%, $301.49**, max DD $130.76.

**META is a strictly additive 10-share overlay.** Combined trades are baseline + isolated META (51 + 28 = 79). Combined P&L is **$179.35** versus **$301.49 + $-122.13 = $179.36** ($0.01 rounding). AAPL and MSFT fills in the three-name book match the baseline one-for-one (AAPL 23 / $6.36; MSFT 28 / $295.12). Isolated META matches the META rows inside the combined book (28 trades, 14 / 14, **$-122.13**). Skips also add: cutoff 75 + 34 = 109; already_in_position 28 + 9 = 37. Ten shares on three names never hit `insufficient_cash`.

**Adding META costs $122.14 versus the AAPL+MSFT baseline** and cuts win rate from 60.78% to 56.96%. Drawdown ($346.37) is about **2.6×** the baseline ($130.76) and is essentially the isolated META hole ($342.82). Peak combined equity is **$100,491.32** (W36); W37 gives it back.

### By-symbol breakout (META)

| | META in combined book | Isolated META (`--breakout META`) | AAPL in combined | MSFT in combined |
| --- | ---: | ---: | ---: | ---: |
| Trades | 28 | 28 | 23 | 28 |
| Wins / losses | 14 / 14 | 14 / 14 | 12 / 11 | 19 / 9 |
| **Win rate** | **50.00%** | **50.00%** | **52.17%** | **67.86%** |
| **P&L** | **$-122.13** | **$-122.13** | **$6.36** | **$295.12** |
| Exit mix | lock_stop 13 $555.61; stop 11 $-682.91; session_flatten 4 $5.18 | same | lock_stop 8 $218.46; stop 8 $-248.45; session_flatten 7 $36.35 | lock_stop 12 $466.27; session_flatten 11 $40.00; stop 5 $-211.15 |

META **does** arm the +1% lock (**14 / 28**). Locks were green ($555.61). The name is red because the **initial 1% stop fired 11 times** and cost **$-682.91**. Session flats were a scratch ($5.18). That is the opposite of AAPL+MSFT, where lock-stops ($684.73) and session flats ($76.35) covered the 13 stops ($-459.59).

### Monthly breakdown (realized P&L)

P&L is the sum of trades whose **exit** falls in that NY calendar month. June = 2026-06-17→06-30 (9 sessions). September = 2026-09-01→09-11 (8 sessions).

| Month | Sessions | +META trades | +META win | +META P&L | +META EOM | AAPL+MSFT trades | AAPL+MSFT win | AAPL+MSFT P&L | AAPL+MSFT EOM | META trades | META win | META P&L | META EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (06-17 → 06-30) | 9 | 13 | 38.46% | $-77.90 | $99,922.10 | 10 | 40.00% | $-18.75 | $99,981.25 | 3 | 33.33% | $-59.15 | $99,940.85 |
| 2026-07 (07-01 → 07-31) | 22 | 26 | 61.54% | $66.96 | $99,989.06 | 17 | 64.71% | $71.56 | $100,052.81 | 9 | 55.56% | $-4.60 | $99,936.25 |
| 2026-08 (08-03 → 08-31) | 21 | 27 | 74.07% | $415.30 | $100,404.36 | 18 | 77.78% | $304.88 | $100,357.69 | 9 | 66.67% | $110.42 | $100,046.67 |
| 2026-09 (09-01 → 09-11) | 8 | 13 | 30.77% | $-225.00 | $100,179.35 | 6 | 33.33% | $-56.20 | $100,301.49 | 7 | 28.57% | $-168.80 | $99,877.87 |
| **Window** | **60** | **79** | **56.96%** | **$179.35** | **$100,179.35** | **51** | **60.78%** | **$301.49** | **$100,301.49** | **28** | **50.00%** | **$-122.13** | **$99,877.87** |

AAPL+MSFT+META 10-share best day: 2026-08-10 **$110.17** (2 trades). Worst day: 2026-09-10 **$-115.49** (2 trades). Isolated META best day: 2026-07-07 **$89.40** (1 trade). Worst day: 2026-09-10 **$-115.49** (2 trades).

August is still the AAPL+MSFT month (**$304.88** at 77.78%). META August is also green (**$110.42** at 66.67%), so the three-name book prints **$415.30** at 74.07% — the only month META helps. September is the META hole (7 trades, 28.57%, **$-168.80**); that is **$168.80** of the three-name September loss of **$-225.00**.

### Weekly (isolated META 10-share)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W25 (06-17 → 06-18) | 0 | n/a | $0.00 | $100,000.00 |
| 2026-W26 (06-22 → 06-26) | 3 | 33.33% | $-59.15 | $99,940.85 |
| 2026-W27 (06-29 → 07-02) | 0 | n/a | $0.00 | $99,940.85 |
| 2026-W28 (07-06 → 07-10) | 2 | 100.00% | $147.03 | $100,087.89 |
| 2026-W29 (07-13 → 07-17) | 4 | 50.00% | $-66.86 | $100,021.03 |
| 2026-W30 (07-20 → 07-24) | 1 | 0.00% | $-64.39 | $99,956.64 |
| 2026-W31 (07-27 → 07-31) | 2 | 50.00% | $-20.39 | $99,936.25 |
| 2026-W32 (08-03 → 08-07) | 2 | 50.00% | $-56.71 | $99,879.54 |
| 2026-W33 (08-10 → 08-14) | 3 | 66.67% | $67.83 | $99,947.37 |
| 2026-W34 (08-17 → 08-21) | 0 | n/a | $0.00 | $99,947.37 |
| 2026-W35 (08-24 → 08-28) | 4 | 75.00% | $99.29 | $100,046.67 |
| 2026-W36 (08-31 → 09-04) | 2 | 100.00% | $109.18 | $100,155.85 |
| 2026-W37 (09-08 → 09-11) | 5 | 0.00% | $-277.98 | $99,877.87 |

Peak isolated-META equity is **$100,155.85** (W36). W37 is a 0% week (5 trades, **$-277.98**) and is the whole META hole.

## 2. August 2026 1% equity risk (`stop_pct` 1.0)

Same noon stack and lock-+1% stop. Size: `shares = floor((0.01 * equity) / (0.01 * entry_price))`. Trade window `--start 2026-08-01 --end 2026-08-31` (warmup bars from 2026-06-17). Writeup companion: `artifacts/ema9_aug2026_risk_aapl_msft_meta.md`.

| | AAPL+MSFT+META 1% risk | AAPL+MSFT 1% risk | Isolated META 1% risk |
| --- | ---: | ---: | ---: |
| Signals | 84 (MSFT 32, AAPL 26, META 26) | 58 (MSFT 32, AAPL 26) | 26 (META 26) |
| Skips | entry_cutoff 47, insufficient_cash 10, already_in_position 9 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 14, already_in_position 3 |
| Trades | 16 (MSFT 8, AAPL 5, META 3) | 15 (MSFT 8, AAPL 7) | 9 (META 9) |
| Wins / losses | 10 / 6 | 11 / 4 | 6 / 3 |
| **Win rate** | **62.50%** | **73.33%** | **66.67%** |
| **Total P&L** | **$1,913.28 (1.913%)** | **$5,489.78 (5.490%)** | **$1,961.82 (1.962%)** |
| Avg win | $610.49 | $697.61 | $805.21 |
| Avg loss | $-698.60 | $-546.00 | $-956.47 |
| **Max drawdown** | **$2,774.85 (2.65%)** | **$2,743.31 (2.58%)** | **$1,182.03 (1.16%)** |
| Ending equity | $101,913.28 | $105,489.78 | $101,961.82 |
| Exit mix | session_flatten 7, lock_stop 6, stop 3 | session_flatten 8, lock_stop 6, stop 1 | lock_stop 6, stop 2, session_flatten 1 |
| Lock armed | 6 | 6 | 6 |
| **Exit P&L** | lock_stop $4,758.19; session_flatten $230.58; stop $-3,075.50 | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 | lock_stop $4,831.24; session_flatten $-855.14; stop $-2,014.28 |
| Size | AAPL 325–329; MSFT 202–212; META 171–179 | AAPL 329–337; MSFT 203–215 | META 166–181 |
| Max concurrent | 1 (0 ticks with 2+ names open) | 1 (0 ticks with 2+ names open) | 1 |

AAPL+MSFT August 1% **reproduced** the prior lock-+1% risk book exactly: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

**This is not an additive overlay.** Isolated META is green (**9 trades, 66.67%, $1,961.82**). Putting META on the AAPL+MSFT book does **not** add that $1,961.82. Combined is **16 trades, 62.50%, $1,913.28** — **$3,576.50 worse** than AAPL+MSFT alone.

A 1% stop on these prices sizes ~full equity (AAPL ~$306–317 → 325–337 shares; MSFT ~$481–505 → 202–215 shares; META ~$552–596 → 166–181 shares). Max concurrent is **1**. Combined skipped **10** accepted signals as `insufficient_cash` (baseline had 3). Isolated META had **0** cash skips.

What the three-name book actually took:

- **MSFT** 8 trades, 6 wins, **$2,795.18** (baseline MSFT 8 / $2,824.73 — same fills, slightly smaller size off the weaker equity path)
- **AAPL** 5 trades, 3 wins, **$1,112.06** (baseline AAPL 7 / $2,665.05)
- **META** 3 trades, 1 win, **$-1,993.97** (isolated META 9 / $1,961.82)

Two baseline AAPL winners are missing from the three-name book:

- 2026-08-05 10:45 AAPL session_flatten **$683.10** — skipped `insufficient_cash` because META was already open (09:45 stop **$-1,019.28**)
- 2026-08-26 09:30 AAPL lock_stop **$871.18** — not in the three-name fill list; that morning the book took META’s 10:00 1% stop (**$-1,024.57**) instead

Six of isolated META’s nine fills never opened in the combined book (`insufficient_cash` while AAPL or MSFT was on): 08-10 lock $990.25, 08-13 lock $999.18, 08-14 session flatten $-855.14, 08-24 lock $778.30, 08-25 lock $1,008.46, 08-28 lock $1,006.63. The three META fills that did open are two initial 1% stops and one $49.88 lock.

Combined 1% best day: 2026-08-04 **$2,004.49** (2 trades). Worst day: 2026-08-20 **$-1,031.65** (1 trade). Peak equity **$103,379.05** after the 2026-08-19 AAPL lock, then bleed to $101,913.28. Baseline peaked at the August close (**$105,489.78**).

### August 1% weekly

| Week | +META trades | +META win | +META P&L | +META EOW | AAPL+MSFT trades | AAPL+MSFT win | AAPL+MSFT P&L | AAPL+MSFT EOW | META trades | META win | META P&L | META EOW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (08-03 → 08-07) | 6 | 83.33% | $2,073.03 | $102,073.03 | 5 | 100.00% | $3,745.45 | $103,745.45 | 2 | 50.00% | $-947.01 | $99,052.99 |
| 2026-W33 (08-10 → 08-14) | 3 | 33.33% | $167.61 | $102,240.64 | 3 | 33.33% | $170.36 | $103,915.81 | 3 | 66.67% | $1,134.28 | $100,187.27 |
| 2026-W34 (08-17 → 08-21) | 4 | 75.00% | $392.97 | $102,633.61 | 4 | 75.00% | $395.20 | $104,311.01 | 0 | n/a | $0.00 | $100,187.27 |
| 2026-W35 (08-24 → 08-28) | 3 | 33.33% | $-720.33 | $101,913.28 | 3 | 66.67% | $1,178.77 | $105,489.78 | 4 | 75.00% | $1,774.54 | $101,961.82 |
| 2026-W36 (08-31) | 0 | n/a | $0.00 | $101,913.28 | 0 | n/a | $0.00 | $105,489.78 | 0 | n/a | $0.00 | $101,961.82 |

W32 is where META first crowds AAPL (META 08-05 stop instead of AAPL $683.10). W35 is the other hole: combined takes META’s 08-26 stop ($-1,024.57) and misses isolated META’s 08-24 / 08-25 / 08-28 locks.

### August 1% fills (AAPL+MSFT+META)

| # | Symbol | Qty | Entry (ET) | Exit (ET) | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 203 | 2026-08-04 10:00 @ 491.08 | 2026-08-04 11:00 @ 495.99 | lock_stop | $996.89 |
| 2 | AAPL | 329 | 2026-08-04 11:45 @ 306.26 | 2026-08-04 13:30 @ 309.32 | lock_stop | $1,007.60 |
| 3 | META | 171 | 2026-08-05 09:45 @ 596.07 | 2026-08-05 11:00 @ 590.11 | stop | $-1,019.28 |
| 4 | MSFT | 204 | 2026-08-06 09:45 @ 493.27 | 2026-08-06 10:45 @ 496.51 | lock_stop | $660.98 |
| 5 | META | 172 | 2026-08-07 09:30 @ 589.00 | 2026-08-07 10:00 @ 589.29 | lock_stop | $49.88 |
| 6 | AAPL | 325 | 2026-08-07 10:15 @ 312.14 | 2026-08-07 16:00 @ 313.30 | session_flatten | $376.96 |
| 7 | MSFT | 202 | 2026-08-10 09:45 @ 505.20 | 2026-08-10 11:00 @ 510.25 | lock_stop | $1,020.49 |
| 8 | MSFT | 207 | 2026-08-13 09:45 @ 497.89 | 2026-08-13 16:00 @ 496.81 | session_flatten | $-222.53 |
| 9 | MSFT | 206 | 2026-08-14 10:00 @ 498.48 | 2026-08-14 16:00 @ 495.42 | session_flatten | $-630.36 |
| 10 | MSFT | 212 | 2026-08-18 10:15 @ 481.38 | 2026-08-18 16:00 @ 481.93 | session_flatten | $116.07 |
| 11 | AAPL | 328 | 2026-08-19 09:45 @ 311.69 | 2026-08-19 13:00 @ 314.81 | lock_stop | $1,022.35 |
| 12 | AAPL | 325 | 2026-08-20 11:00 @ 317.43 | 2026-08-20 15:30 @ 314.26 | stop | $-1,031.65 |
| 13 | MSFT | 212 | 2026-08-21 09:45 @ 482.00 | 2026-08-21 16:00 @ 483.35 | session_flatten | $286.20 |
| 14 | AAPL | 329 | 2026-08-24 09:45 @ 311.15 | 2026-08-24 16:00 @ 310.35 | session_flatten | $-263.20 |
| 15 | MSFT | 209 | 2026-08-25 09:45 @ 488.79 | 2026-08-25 16:00 @ 491.50 | session_flatten | $567.43 |
| 16 | META | 179 | 2026-08-26 10:00 @ 572.39 | 2026-08-26 10:30 @ 566.66 | stop | $-1,024.57 |

### August 1% fills (isolated META)

| # | Symbol | Qty | Entry (ET) | Exit (ET) | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | META | 167 | 2026-08-05 09:45 @ 596.07 | 2026-08-05 11:00 @ 590.11 | stop | $-995.44 |
| 2 | META | 167 | 2026-08-07 09:30 @ 589.00 | 2026-08-07 10:00 @ 589.29 | lock_stop | $48.43 |
| 3 | META | 166 | 2026-08-10 09:45 @ 596.53 | 2026-08-10 10:45 @ 602.50 | lock_stop | $990.25 |
| 4 | META | 170 | 2026-08-13 09:45 @ 587.75 | 2026-08-13 15:30 @ 593.63 | lock_stop | $999.18 |
| 5 | META | 169 | 2026-08-14 11:45 @ 594.97 | 2026-08-14 16:00 @ 589.91 | session_flatten | $-855.14 |
| 6 | META | 181 | 2026-08-24 10:00 @ 551.88 | 2026-08-24 12:00 @ 556.18 | lock_stop | $778.30 |
| 7 | META | 179 | 2026-08-25 11:30 @ 563.38 | 2026-08-25 16:00 @ 569.02 | lock_stop | $1,008.46 |
| 8 | META | 178 | 2026-08-26 10:00 @ 572.39 | 2026-08-26 10:30 @ 566.66 | stop | $-1,018.85 |
| 9 | META | 176 | 2026-08-28 09:30 @ 571.95 | 2026-08-28 10:30 @ 577.67 | lock_stop | $1,006.63 |

## What this says about adding META to the refined 15m book

On this Yahoo 15m window the noon lock-+1% stack **does take META trades** (28 ten-share, 9 isolated August risk). Adding META to AAPL+MSFT is **not a free overlay**:

1. **10-share is additive and worse.** META is 28 trades at 50.00% and **$-122.13**. Combined is **$179.35** versus the reproduced AAPL+MSFT **$301.49**. AAPL and MSFT fills do not change. Drawdown rises from $130.76 to $346.37 because META’s own DD is $342.82.
2. **META’s 10-share hole is the initial 1% stop** (11 / 28, $-682.91). Locks were green ($555.61 on 13). September W37 is a 0% week (5 trades, $-277.98). August META is the one green month ($110.42).
3. **August 1% risk is the opposite of additive.** Isolated META is **+$1,961.82**. Combined is **+$1,913.28** versus AAPL+MSFT **+$5,489.78**. META’s ~$560–596 print at a 1% stop sizes ~full equity (166–181 shares). Only one name can be open. Combined cash-skips jump from 3 to **10**.
4. The three META fills that got through in the combined August book are the **bad ones** (two 1% stops and a $49.88 lock, **$-1,993.97**). The isolated META locks that made the solo book green were skipped while AAPL or MSFT was already on.
5. Combined also dropped two baseline AAPL winners ($683.10 on 08-05; $871.18 on 08-26). That is the add-on: META does not stack on AAPL+MSFT at 1% risk; it **replaces** AAPL/MSFT fills.

Trade-level rows are in `artifacts/ema9_aapl_msft_meta_15m.json` (10-share) and `artifacts/ema9_aug2026_risk_aapl_msft_meta.json` (August 1%). Daily books are in each run’s `period_stats.daily`.

## Assumptions (engine)

- Signals come from the live `evaluate_rule` path (same EMA/SMA/RSI detectors).
- Fill at the next 15m bar open. One open lot per symbol; no pyramiding. Shorts are parked (not in these YAMLs).
- Lock-plus: initial stop fill×0.99; first bar high ≥ fill×1.01 locks the stop to fill×1.01 from the **next** bar. Same-bar pullback after the tag still uses the initial stop.
- `flatten_by` 15:55 flats the 15:45 ET bar close (`session_flatten`) if stop/lock has not already filled.
- Open lots on the last bar flatten at the last close (`eod`). None of these books used `eod`.
- Yahoo regular-session bars, unadjusted OHLC. commission=$0.00/fill, slippage=0.0%.
- Starting equity $100,000. Risk size: `shares = floor((0.01 * equity) / (0.01 * entry_price))`.
- `--breakout META` runs an isolated META book even with `--combined-only`.
