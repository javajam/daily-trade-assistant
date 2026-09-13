# ORB BEFORE vs AFTER: 1R take-profit + 1% high-vol gate

- Generated (UTC): 2026-09-13T15:13:24Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC), cache replay for AAPL/MSFT/SPY plus a fresh SOXL download, then clipped
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars: AAPL 15m 1560 / 5m 4677; MSFT 15m 1560 / 5m 4676; SPY 15m 1560 / 5m 4680; SOXL 15m 1560 / 5m 4680
- Same closed-bar window as `artifacts/orb_one_r_comparison.md` / the last first-profit AFTER book
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares

Replaying **hybrid midpoint** (`reversal_in_range: off`, `or_midpoint`, vol gate off) on this tape reproduced the last hybrid book exactly (31 trades, 38.71%, $27.67, max DD $46.45). Replaying **1R with the vol gate off** on AAPL/MSFT/SPY reproduced the last 1R AFTER book exactly (31 trades, 35.48%, $-61.87, max DD $88.33).

Default product on this branch: `take_profit_mode: one_r`, `min_or_height_pct: 0.01` (OR height / **OR open** ≥ 1%; midpoint only if open is missing), `reversal_in_range: close`, `touch_and_band`, OR-extreme stop, one trade before 10:30 ET. Example universe is now AAPL / MSFT / SPY / SOXL.

If stop and 1R both trade on the same bar, the stop fills first.

## Headline (AAPL / MSFT / SPY only)

| | Hybrid midpoint (reference) | 1R, no vol gate | 1R + 1% vol gate |
| --- | ---: | ---: | ---: |
| Take profit | OR midpoint | 1R | 1R |
| High-vol gate | off | off | `(or_high − or_low) / or_open >= 1%` |
| Signals detected | 153 | 152 | 152 |
| Trades | 31 | 31 | 18 |
| Wins / losses / scratch | 12 / 17 / 2 | 11 / 20 / 0 | 6 / 12 / 0 |
| **Win rate** | **38.71%** | **35.48%** | **33.33%** |
| **Total P&L** | **$27.67** (0.028%) | **$-61.87** (−0.062%) | **$-67.27** (−0.067%) |
| Avg win | $10.11 | $7.93 | $9.12 |
| Avg loss | $-5.51 | $-7.46 | $-10.16 |
| **Max drawdown** | **$46.45** (0.05%) | **$88.33** (0.09%) | **$86.63** (0.09%) |
| Ending equity | $100,027.67 | $99,938.13 | $99,932.73 |
| Exit reasons | take 14, stop 17 | take 11, stop 20 | take 6, stop 12 |
| Trades by symbol | AAPL 10, MSFT 13, SPY 8 | AAPL 10, MSFT 13, SPY 8 | AAPL 7, MSFT 11, SPY 0 |

Skipped on 1R + vol (still counted as signals, not trades): `min_or_height` 70, `entry_cutoff` 62, `max_trades_before_cutoff` 2.

The 1% floor dropped 13 of the 31 one-R fills (31 → 18). Every SPY fill from the ungated 1R book failed the height test (SPY 8 → 0). AAPL 10 → 7, MSFT 13 → 11. Avg win rose a bit ($7.93 → $9.12) because quieter days were removed, but avg loss widened ($-7.46 → $-10.16) and the 3-symbol book finished slightly redder ($-61.87 → $-67.27). Max DD tightened a little ($88.33 → $86.63). Midpoint remains the only green 3-symbol book on this tape.

## SOXL (1R + 1% vol, isolated book)

SOXL 5m/15m covered the same window (15m 1560, 5m 4680). Isolated book — its own equity curve, not mixed with AAPL/MSFT/SPY.

| | SOXL alone |
| --- | ---: |
| Signals detected | 56 |
| Trades | 2 |
| Wins / losses / scratch | 1 / 1 / 0 |
| **Win rate** | **50.00%** |
| **Total P&L** | **$-10.40** (−0.010%) |
| Avg win | $8.30 |
| Avg loss | $-18.70 |
| **Max drawdown** | **$18.70** (0.02%) |
| Ending equity | $99,989.60 |
| Exit reasons | take 1, stop 1 |
| Skips | `entry_cutoff` 54 (no `min_or_height` skips) |

SOXL's opening ranges all cleared 1% of OR open (3x semiconductor ETF), so the vol gate did not drop any SOXL session. The 10:30 / one-trade morning rule did almost all the work: 56 setups → 2 fills. One take and one stop; the loser ($18.70) is larger than the winner ($8.30) at 10 shares, so the isolated book finished red. Two trades is a very small sample.

The two isolated fills (10 shares, times UTC):

| Side | Entry | Exit | P&L | Reason |
| --- | --- | --- | ---: | --- |
| short | 2026-07-08 14:10 @ 171.17 | 14:15 @ 170.34 | +$8.30 | take (1R) |
| long | 2026-07-28 14:05 @ 107.14 | 14:10 @ 105.27 | −$18.70 | stop (OR extreme) |

## Full example universe (AAPL / MSFT / SPY / SOXL, 1R + 1% vol)

This is the new example-config default book (shared equity curve).

| | Full set (new default) |
| --- | ---: |
| Signals detected | 208 |
| Trades | 20 |
| Wins / losses / scratch | 7 / 13 / 0 |
| **Win rate** | **35.00%** |
| **Total P&L** | **$-77.67** (−0.078%) |
| Avg win | $9.00 |
| Avg loss | $-10.82 |
| **Max drawdown** | **$97.03** (0.10%) |
| Ending equity | $99,922.33 |
| Exit reasons | take 7, stop 13 |
| Trades by symbol | AAPL 7, MSFT 11, SPY 0, SOXL 2 |
| Skips | `min_or_height` 70, `entry_cutoff` 116, `max_trades_before_cutoff` 2 |

Closed-trade P&L is the sum of the isolated 3-symbol vol book and the isolated SOXL book ($-67.27 + $-10.40 = $-77.67). Combined max DD ($97.03) is not the sum of the isolated DDs because the lots share one equity curve.

## What the tape showed

| Variant | Universe | Trades | Win rate | P&L | Max DD |
| --- | --- | ---: | ---: | ---: | ---: |
| Last hybrid midpoint | AAPL/MSFT/SPY | 31 | 38.71% | $27.67 | $46.45 |
| 1R, no vol gate | AAPL/MSFT/SPY | 31 | 35.48% | $-61.87 | $88.33 |
| **1R + 1% vol** | AAPL/MSFT/SPY | **18** | **33.33%** | **$-67.27** | **$86.63** |
| **1R + 1% vol** | SOXL only | **2** | **50.00%** | **$-10.40** | **$18.70** |
| **1R + 1% vol (new default)** | AAPL/MSFT/SPY/SOXL | **20** | **35.00%** | **$-77.67** | **$97.03** |

This is one ~86-day Yahoo window at 10 shares. It is not a claim that 1R or the 1% height floor is a better or worse rule outside this sample.
