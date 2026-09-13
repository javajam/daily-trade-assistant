# ORB BEFORE vs AFTER: hybrid touch + edge-band probe

- Generated (UTC): 2026-09-13T14:33:59Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC), cache replay
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars: AAPL 15m 1560 / 5m 4677; MSFT 15m 1560 / 5m 4676; SPY 15m 1560 / 5m 4680
- Same closed-bar window as the previous AFTER book (`artifacts/orb_probe_touch_comparison.md` / `artifacts/orb_backtest_results.md` from 2026-09-13T14:22:25Z)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares

Replaying **`probe_mode: edge_band`** on this download reproduced the older AFTER book exactly (39 trades, 33.33%, $14.63, max DD $49.25). Replaying **`probe_mode: touch`** reproduced the last AFTER book exactly (145 trades, 23.45%, $92.80, max DD $59.05). The AFTER column is the new example-config default (`probe_mode: touch_and_band`) on that same tape. Locked rules are unchanged: opposite-color next bar, entry at the following open, stop at the OR extreme, TP at the OR midpoint, one trade per symbol, entry strictly before 10:30 ET.

## Headline

| | `edge_band` | `touch` (last default) | AFTER (`touch_and_band`, new default) |
| --- | ---: | ---: | ---: |
| Probe | close inside 5% edge band | wick must touch OR extreme | touch OR extreme **and** close inside 5% band |
| Signals detected | 192 | 3062 | 153 |
| Trades | 39 | 145 | 31 |
| Wins / losses / scratch | 13 / 23 / 3 | 34 / 37 / 74 | 12 / 17 / 2 |
| **Win rate** | **33.33%** | **23.45%** | **38.71%** |
| **Total P&L** | **$14.63** (0.015%) | **$92.80** (0.093%) | **$27.67** (0.028%) |
| Avg win | $10.22 | $10.49 | $10.11 |
| Avg loss | $-5.14 | $-7.13 | $-5.51 |
| **Max drawdown** | **$49.25** (0.05%) | **$59.05** (0.06%) | **$46.45** (0.05%) |
| Ending equity | $100,014.63 | $100,092.80 | $100,027.67 |
| Exit reasons | take 16, stop 23 | take 55, stop 90 | take 14, stop 17 |
| Trades by symbol | AAPL 14, MSFT 15, SPY 10 | AAPL 43, MSFT 48, SPY 54 | AAPL 10, MSFT 13, SPY 8 |

Skipped on `edge_band` (still counted as signals, not trades): `entry_cutoff` 151, `max_trades_before_cutoff` 2.

Skipped on `touch`: `entry_cutoff` 2812, `max_trades_before_cutoff` 105.

Skipped on `touch_and_band`: `entry_cutoff` 120, `max_trades_before_cutoff` 2.

## What moved the numbers

`touch_and_band` is the intersection of the two older probes: the 5m wick must print the OR high or low, **and** the close must stay in the outer 5% of the range. That is stricter than either mode alone, so detected setups fell (192 / 3062 → 153) and taken trades fell (39 / 145 → 31).

Measured on this tape (not a forecast):

| Variant | Trades | Win rate | P&L | Max DD |
| --- | ---: | ---: | ---: | ---: |
| Last-but-one AFTER (`edge_band`, OR-extreme stop, 10:30 / max 1) | 39 | 33.33% | $14.63 | $49.25 |
| Last AFTER (`touch`, same stop + gate) | 145 | 23.45% | $92.80 | $59.05 |
| **New default (`touch_and_band`, same stop + gate)** | **31** | **38.71%** | **$27.67** | **$46.45** |

Win rate is the highest of the three (38.71% vs 33.33% / 23.45%) and max DD is the tightest ($46.45 vs $49.25 / $59.05). P&L sits between the two prior books ($14.63 → $27.67 ← $92.80) because the hybrid keeps some of the band book's selectivity while still finishing green. Scratches stayed low (2, vs 3 on `edge_band` and 74 on `touch`). This is one ~86-day Yahoo window on three symbols at 10 shares; it is not a claim that hybrid is a better rule.

## vs sample strategies (same prior Yahoo run)

Sample books below are from `artifacts/orb_vs_sample_comparison.md` (generated 2026-09-13T13:17:56Z). The 15m engulfing book shares this ~86-day 5m/15m window. Hammer / sample-entries / combined include the longer 1h SPY tape (~729d) and are **not** time-normalized. ORB and sample engines stay on separate books. Sizing is **not** equal: ORB and engulfing use 10 shares; hammer uses 2% of equity.

| Book | Trades | Win rate | P&L | Max DD | Window |
| --- | ---: | ---: | ---: | ---: | --- |
| sample-entries | 63 | 42.86% | $810.57 | $498.00 | longer (~729d) |
| engulfing-with-trend | 39 | 43.59% | $697.90 | $471.57 | ~86d (same 15m cap) |
| combined | 110 | 41.82% | $447.01 | $273.85 | longer (~729d) |
| hammer-oversold | 24 | 41.67% | $112.67 | $142.76 | longer (~729d) |
| ORB `touch` | 145 | 23.45% | $92.80 | $59.05 | ~86d |
| **ORB AFTER (`touch_and_band`)** | **31** | **38.71%** | **$27.67** | **$46.45** | ~86d |
| ORB `edge_band` | 39 | 33.33% | $14.63 | $49.25 | ~86d |
| evening-star-or-engulfing-exit | 0 | n/a | $0.00 | $0.00 | ~86d (exit-only) |

Hybrid ORB still has the smallest max DD in that table. Win rate is closer to the sample books than `touch` was, but P&L is still far behind the 10-share engulfing book ($697.90 on the same ~86-day footing).
