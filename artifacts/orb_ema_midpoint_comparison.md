# ORB BEFORE vs AFTER: midpoint take-profit + 9 EMA reversal filter

- Generated (UTC): 2026-09-13T15:32:23Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC), fresh download then clipped
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars: AAPL 15m 1560 / 5m 4677; MSFT 15m 1560 / 5m 4676; SPY 15m 1560 / 5m 4680; SOXL 15m 1560 / 5m 4680
- Same closed-bar window as `artifacts/orb_one_r_vol_gate_comparison.md` / PR #9
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares

Replaying **1R + 1% vol** (`take_profit_mode: one_r`, `ema_filter: false`, `min_or_height_pct: 0.01`, `reversal_in_range: close`) on this tape reproduced the PR #9 AFTER book exactly: AAPL/MSFT/SPY 18 trades, 33.33%, $-67.27, max DD $86.63; isolated SOXL 2 trades, 50.00%, $-10.40, max DD $18.70; full example universe 20 trades, 35.00%, $-77.67, max DD $97.03.

Default product on this branch: `take_profit_mode: or_midpoint`, `ema_filter: true`, `ema_period: 9` (reversal close vs EMA on the signal timeframe: long `close > ema9`, short `close < ema9`), `reversal_in_range: close`, `touch_and_band`, OR-extreme stop, `min_or_height_pct: 0.01`, one trade before 10:30 ET. Example universe is AAPL / MSFT / SPY / SOXL.

If stop and midpoint both trade on the same bar, the stop fills first.

## Headline (AAPL / MSFT / SPY only)

| | 1R + 1% vol (PR #9 reference) | Midpoint + EMA9 + 1% vol (new default) |
| --- | ---: | ---: |
| Take profit | 1R | OR midpoint |
| EMA filter | off | EMA(9) on 5m through the reversal (`close > ema` long / `close < ema` short) |
| High-vol gate | `(or_high − or_low) / or_open >= 1%` | same |
| Signals detected | 152 | 92 |
| Trades | 18 | 5 |
| Wins / losses / scratch | 6 / 12 / 0 | 1 / 3 / 1 |
| **Win rate** | **33.33%** | **20.00%** |
| **Total P&L** | **$-67.27** (−0.067%) | **$-35.58** (−0.036%) |
| Avg win | $9.12 | $5.72 |
| Avg loss | $-10.16 | $-13.77 |
| **Max drawdown** | **$86.63** (0.09%) | **$41.30** (0.04%) |
| Ending equity | $99,932.73 | $99,964.42 |
| Exit reasons | take 6, stop 12 | take 2, stop 3 |
| Trades by symbol | AAPL 7, MSFT 11, SPY 0 | AAPL 4, MSFT 1, SPY 0 |

Skipped on the new default (still counted as signals, not trades): `min_or_height` 48, `entry_cutoff` 38, `max_trades_before_cutoff` 1.

The EMA filter cut detected setups 152 → 92 and taken fills 18 → 5. SPY still has no fill (vol gate). One of the five fills is a scratch: AAPL short 2026-06-23 13:55Z @ 298.36 exited at the same print on the midpoint take. The remaining loser is the 2026-09-01 MSFT short stop (−$32.80), which is also in the 1R book. Closed-trade P&L is less red (−$67.27 → −$35.58) and max DD tightened ($86.63 → $41.30) because most of the 1R losers never cleared the EMA. Win rate fell (33.33% → 20.00%) on a five-trade sample.

## SOXL (isolated book)

SOXL 5m/15m covered the same window (15m 1560, 5m 4680). Isolated book — its own equity curve, not mixed with AAPL/MSFT/SPY.

| | 1R + 1% vol (PR #9) | Midpoint + EMA9 + 1% vol |
| --- | ---: | ---: |
| Signals detected | 56 | 40 |
| Trades | 2 | 0 |
| Wins / losses / scratch | 1 / 1 / 0 | 0 / 0 / 0 |
| **Win rate** | **50.00%** | **n/a** |
| **Total P&L** | **$-10.40** (−0.010%) | **$0.00** (0.000%) |
| Avg win | $8.30 | n/a |
| Avg loss | $-18.70 | n/a |
| **Max drawdown** | **$18.70** (0.02%) | **$0.00** (0.00%) |
| Ending equity | $99,989.60 | $100,000.00 |
| Exit reasons | take 1, stop 1 | — |
| Skips | `entry_cutoff` 54 | `entry_cutoff` 40 |

The two PR #9 SOXL fills (10 shares, times UTC):

| Side | Entry | Exit | P&L | Reason |
| --- | --- | --- | ---: | --- |
| short | 2026-07-08 14:10 @ 171.17 | 14:15 @ 170.34 | +$8.30 | take (1R) |
| long | 2026-07-28 14:05 @ 107.14 | 14:10 @ 105.27 | −$18.70 | stop (OR extreme) |

Both of those reversals fail the new EMA9 filter, so the isolated SOXL book is empty. The 16 dropped SOXL signals are EMA rejects (56 → 40 detected setups); the remaining 40 are all `entry_cutoff`.

## Full example universe (AAPL / MSFT / SPY / SOXL)

This is the new example-config default book (shared equity curve).

| | 1R + 1% vol (PR #9 default) | Midpoint + EMA9 + 1% vol (new default) |
| --- | ---: | ---: |
| Signals detected | 208 | 132 |
| Trades | 20 | 5 |
| Wins / losses / scratch | 7 / 13 / 0 | 1 / 3 / 1 |
| **Win rate** | **35.00%** | **20.00%** |
| **Total P&L** | **$-77.67** (−0.078%) | **$-35.58** (−0.036%) |
| Avg win | $9.00 | $5.72 |
| Avg loss | $-10.82 | $-13.77 |
| **Max drawdown** | **$97.03** (0.10%) | **$41.30** (0.04%) |
| Ending equity | $99,922.33 | $99,964.42 |
| Exit reasons | take 7, stop 13 | take 2, stop 3 |
| Trades by symbol | AAPL 7, MSFT 11, SPY 0, SOXL 2 | AAPL 4, MSFT 1, SPY 0, SOXL 0 |
| Skips | `min_or_height` 70, `entry_cutoff` 116, `max_trades_before_cutoff` 2 | `min_or_height` 48, `entry_cutoff` 78, `max_trades_before_cutoff` 1 |

Because the EMA-filtered SOXL book has no fills, the four-symbol new-default book equals the three-symbol book (same five trades, same P&L, same max DD).

The five new-default fills (10 shares, times UTC):

| Symbol | Side | Entry | Exit | P&L | Reason |
| --- | --- | --- | --- | ---: | --- |
| AAPL | short | 2026-06-23 13:55 @ 298.36 | 14:00 @ 298.36 | $0.00 | take (OR midpoint, scratch) |
| AAPL | long | 2026-07-01 13:55 @ 291.29 | 14:00 @ 291.86 | +$5.72 | take (OR midpoint) |
| AAPL | long | 2026-07-28 13:55 @ 338.24 | 14:00 @ 337.71 | −$5.30 | stop (OR extreme) |
| AAPL | long | 2026-08-25 14:25 @ 310.57 | 14:30 @ 310.25 | −$3.20 | stop (OR extreme) |
| MSFT | short | 2026-09-01 13:55 @ 501.35 | 14:20 @ 504.63 | −$32.80 | stop (OR extreme) |

## What the tape showed

| Variant | Universe | Trades | Win rate | P&L | Max DD |
| --- | --- | ---: | ---: | ---: | ---: |
| **1R + 1% vol (PR #9)** | AAPL/MSFT/SPY | **18** | **33.33%** | **$-67.27** | **$86.63** |
| **1R + 1% vol (PR #9)** | SOXL only | **2** | **50.00%** | **$-10.40** | **$18.70** |
| **1R + 1% vol (PR #9)** | AAPL/MSFT/SPY/SOXL | **20** | **35.00%** | **$-77.67** | **$97.03** |
| **Midpoint + EMA9 + 1% vol** | AAPL/MSFT/SPY | **5** | **20.00%** | **$-35.58** | **$41.30** |
| **Midpoint + EMA9 + 1% vol** | SOXL only | **0** | **n/a** | **$0.00** | **$0.00** |
| **Midpoint + EMA9 + 1% vol (new default)** | AAPL/MSFT/SPY/SOXL | **5** | **20.00%** | **$-35.58** | **$41.30** |

This is one ~86-day Yahoo window at 10 shares. It is not a claim that midpoint + EMA9 is a better or worse rule outside this sample.
