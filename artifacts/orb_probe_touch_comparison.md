# ORB BEFORE vs AFTER: probe must touch the OR extreme

- Generated (UTC): 2026-09-13T14:22:25Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC), cache replay
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars: AAPL 15m 1560 / 5m 4677; MSFT 15m 1560 / 5m 4676; SPY 15m 1560 / 5m 4680
- Same closed-bar window as the previous AFTER book (`artifacts/orb_stop_cutoff_comparison.md` / `artifacts/orb_backtest_results.md` from 2026-09-13T14:11:07Z)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares

Replaying **`probe_mode: edge_band`** on this download reproduced that previous AFTER book exactly (39 trades, 33.33%, $14.63, max DD $49.25). The AFTER column is the new example-config default (`probe_mode: touch`) on that same tape. Locked rules are unchanged: opposite-color next bar, entry at the following open, stop at the OR extreme, TP at the OR midpoint, one trade per symbol, entry strictly before 10:30 ET.

## Headline

| | BEFORE (last AFTER / `edge_band`) | AFTER (`touch`, new default) |
| --- | ---: | ---: |
| Probe | close inside 5% edge band | wick must touch OR extreme (top: high ≥ OR high; bottom: low ≤ OR low) |
| Signals detected | 192 | 3062 |
| Trades | 39 | 145 |
| Wins / losses / scratch | 13 / 23 / 3 | 34 / 37 / 74 |
| **Win rate** | **33.33%** | **23.45%** |
| **Total P&L** | **$14.63** (0.015%) | **$92.80** (0.093%) |
| Avg win | $10.22 | $10.49 |
| Avg loss | $-5.14 | $-7.13 |
| **Max drawdown** | **$49.25** (0.05%) | **$59.05** (0.06%) |
| Ending equity | $100,014.63 | $100,092.80 |
| Exit reasons | take 16, stop 23 | take 55, stop 90 |
| Trades by symbol | AAPL 14, MSFT 15, SPY 10 | AAPL 43, MSFT 48, SPY 54 |

Skipped on BEFORE (still counted as signals, not trades): `entry_cutoff` 151, `max_trades_before_cutoff` 2.

Skipped on AFTER: `entry_cutoff` 2812, `max_trades_before_cutoff` 105.

## What moved the numbers

Touch is a looser probe than “close in the outer 5% of the range”: any 5m wick that prints the OR high or low qualifies, including bars that close mid-range. On this tape that exploded detected setups (192 → 3062). The 10:30 / one-trade gate still holds the book to at most one fill per symbol per morning, but more mornings now *have* a qualifying pre-10:30 setup, so taken trades rose 39 → 145.

Measured on this tape (not a forecast):

| Variant | Trades | Win rate | P&L | Max DD |
| --- | ---: | ---: | ---: | ---: |
| Last AFTER (`edge_band`, OR-extreme stop, 10:30 / max 1) | 39 | 33.33% | $14.63 | $49.25 |
| **New default (`touch`, same stop + gate)** | **145** | **23.45%** | **$92.80** | **$59.05** |

P&L is higher ($14.63 → $92.80) because there are more completed trades and more takes (16 → 55). Win rate fell (33.33% → 23.45%), scratches jumped (3 → 74), and max DD widened slightly ($49.25 → $59.05). Average loss also worsened ($-5.14 → $-7.13). This is one ~86-day Yahoo window on three symbols at 10 shares; it is not a claim that touch is a better rule.

## vs sample strategies (same prior Yahoo run)

Sample books below are from `artifacts/orb_vs_sample_comparison.md` (generated 2026-09-13T13:17:56Z). The 15m engulfing book shares this ~86-day 5m/15m window. Hammer / sample-entries / combined include the longer 1h SPY tape (~729d) and are **not** time-normalized. ORB and sample engines stay on separate books. Sizing is **not** equal: ORB and engulfing use 10 shares; hammer uses 2% of equity.

| Book | Trades | Win rate | P&L | Max DD | Window |
| --- | ---: | ---: | ---: | ---: | --- |
| sample-entries | 63 | 42.86% | $810.57 | $498.00 | longer (~729d) |
| engulfing-with-trend | 39 | 43.59% | $697.90 | $471.57 | ~86d (same 15m cap) |
| combined | 110 | 41.82% | $447.01 | $273.85 | longer (~729d) |
| hammer-oversold | 24 | 41.67% | $112.67 | $142.76 | longer (~729d) |
| **ORB AFTER (touch)** | **145** | **23.45%** | **$92.80** | **$59.05** | ~86d |
| ORB BEFORE (`edge_band`) | 39 | 33.33% | $14.63 | $49.25 | ~86d |
| evening-star-or-engulfing-exit | 0 | n/a | $0.00 | $0.00 | ~86d (exit-only) |

Touch-required ORB still has the smallest max DD in that table and is still far behind the sample entry rules on win rate and P&L (engulfing made $697.90 on the same 10-share / ~86-day footing).
