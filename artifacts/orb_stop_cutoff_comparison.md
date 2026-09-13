# ORB BEFORE vs AFTER: OR-extreme stop + 10:30 one-trade gate

- Generated (UTC): 2026-09-13T14:11:07Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC), cache replay
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars: AAPL 15m 1560 / 5m 4677; MSFT 15m 1560 / 5m 4676; SPY 15m 1560 / 5m 4680
- Same closed-bar window as the previous published ORB book (`artifacts/orb_backtest_results.md` from 2026-09-13T13:17:59Z)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares

Replaying the **old** settings on this download reproduced the published book exactly (182 trades, 28.02%, $7.04, max DD $174.39). The AFTER column is the new example-config defaults on that same tape.

## Headline

| | BEFORE (published / reproduced) | AFTER (new defaults) |
| --- | ---: | ---: |
| Stop | reversal candle extreme | opening-range extreme (long → OR low, short → OR high) |
| Frequency | no clock cutoff; multiple trades/day | 1 entry/symbol, only if fill is before 10:30 ET |
| Signals detected | 192 | 192 |
| Trades | 182 | 39 |
| Wins / losses / scratch | 51 / 125 / 6 | 13 / 23 / 3 |
| **Win rate** | **28.02%** | **33.33%** |
| **Total P&L** | **$7.04** (0.007%) | **$14.63** (0.015%) |
| Avg win | $12.92 | $10.22 |
| Avg loss | $-5.21 | $-5.14 |
| **Max drawdown** | **$174.39** (0.17%) | **$49.25** (0.05%) |
| Ending equity | $100,007.04 | $100,014.63 |
| Exit reasons | take 55, stop 126, eod 1 | take 16, stop 23 |
| Trades by symbol | AAPL 69, MSFT 59, SPY 54 | AAPL 14, MSFT 15, SPY 10 |

Skipped on AFTER (still counted as signals, not trades): `entry_cutoff` 151, `max_trades_before_cutoff` 2. BEFORE skipped 10 as `already_in_position`.

## What moved the numbers

Both changes together, measured on this tape (not a forecast):

| Variant | Trades | Win rate | P&L | Max DD |
| --- | ---: | ---: | ---: | ---: |
| Old (reversal-candle stop, no cutoff) | 182 | 28.02% | $7.04 | $174.39 |
| Stop only (`orb_extreme`, no cutoff) | 184 | 24.46% | $15.43 | $176.28 |
| Gate only (reversal-candle stop + 10:30 / max 1) | 39 | 35.90% | $-36.77 | $83.55 |
| **Both (new defaults)** | **39** | **33.33%** | **$14.63** | **$49.25** |

The morning gate is what cut the book from 182 trades to 39 and lifted win rate. The OR-extreme stop is what kept the gated book profitable on this window (gate-only was −$36.77). Win rate is still well below the sample-rule books.

## vs sample strategies (same prior Yahoo run)

Sample books below are from `artifacts/orb_vs_sample_comparison.md` (generated 2026-09-13T13:17:56Z). The 15m engulfing book shares this ~86-day 5m/15m window. Hammer / sample-entries / combined include the longer 1h SPY tape (~729d) and are **not** time-normalized. ORB and sample engines stay on separate books. Sizing is **not** equal: ORB and engulfing use 10 shares; hammer uses 2% of equity.

| Book | Trades | Win rate | P&L | Max DD | Window |
| --- | ---: | ---: | ---: | ---: | --- |
| sample-entries | 63 | 42.86% | $810.57 | $498.00 | longer (~729d) |
| engulfing-with-trend | 39 | 43.59% | $697.90 | $471.57 | ~86d (same 15m cap) |
| combined | 110 | 41.82% | $447.01 | $273.85 | longer (~729d) |
| hammer-oversold | 24 | 41.67% | $112.67 | $142.76 | longer (~729d) |
| **ORB AFTER** | **39** | **33.33%** | **$14.63** | **$49.25** | ~86d |
| ORB BEFORE | 182 | 28.02% | $7.04 | $174.39 | ~86d |
| evening-star-or-engulfing-exit | 0 | n/a | $0.00 | $0.00 | ~86d (exit-only) |

On this evidence the new ORB defaults improved win rate, P&L, and drawdown versus the previous ORB book, and now have the smallest max DD in that table. They still trail the sample entry rules on win rate and especially on P&L (engulfing made $697.90 on the same 39-trade / 10-share / ~86-day footing).
