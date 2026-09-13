# ORB BEFORE vs AFTER: reversal in-range + first-profitable-close take

- Generated (UTC): 2026-09-13T15:05:00Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC), fresh download then clipped
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars: AAPL 15m 1560 / 5m 4677; MSFT 15m 1560 / 5m 4676; SPY 15m 1560 / 5m 4680
- Same closed-bar window as the previous AFTER book (`artifacts/orb_probe_touch_and_band_comparison.md` / `artifacts/orb_backtest_results.md` from 2026-09-13T14:33:59Z)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares

Replaying **`reversal_in_range: off` + `take_profit_mode: or_midpoint`** on this download reproduced the last hybrid AFTER book exactly (31 trades, 38.71%, $27.67, max DD $46.45). The AFTER column is the new example-config default (`reversal_in_range: close`, `take_profit_mode: first_profitable_close`) on that same tape. Locked rules are unchanged: `touch_and_band` probe, opposite-color next bar, entry at the following open, stop at the OR extreme, one trade per symbol, entry strictly before 10:30 ET.

If stop and first-profit (or midpoint) both trade on the same bar, the stop fills first.

## Headline

| | BEFORE (last hybrid default) | AFTER (new default) |
| --- | ---: | ---: |
| Reversal filter | none (opposite color only) | close must sit inside OR (`or_low <= close <= or_high`) |
| Take profit | OR midpoint | first signal-bar close that is strictly profitable vs entry |
| Signals detected | 153 | 152 |
| Trades | 31 | 31 |
| Wins / losses / scratch | 12 / 17 / 2 | 13 / 18 / 0 |
| **Win rate** | **38.71%** | **41.94%** |
| **Total P&L** | **$27.67** (0.028%) | **$-74.17** (−0.074%) |
| Avg win | $10.11 | $4.98 |
| Avg loss | $-5.51 | $-7.72 |
| **Max drawdown** | **$46.45** (0.05%) | **$81.00** (0.08%) |
| Ending equity | $100,027.67 | $99,925.83 |
| Exit reasons | take 14, stop 17 | take 13, stop 18 |
| Trades by symbol | AAPL 10, MSFT 13, SPY 8 | AAPL 10, MSFT 13, SPY 8 |

Skipped on BEFORE (still counted as signals, not trades): `entry_cutoff` 120, `max_trades_before_cutoff` 2.

Skipped on AFTER: `entry_cutoff` 119, `max_trades_before_cutoff` 2.

## What moved the numbers

The close-inside reversal filter dropped one SPY setup (signals 153 → 152). That setup was already past the 10:30 gate, so the taken-trade set stayed 31. Replaying **close-inside + OR-midpoint** on this tape reproduced the BEFORE book exactly (31 / 38.71% / $27.67 / $46.45). The P&L move is from `first_profitable_close`, not from the range filter.

Measured on this tape (not a forecast):

| Variant | Trades | Win rate | P&L | Max DD |
| --- | ---: | ---: | ---: | ---: |
| Last AFTER (`touch_and_band`, midpoint TP, no reversal-range filter) | 31 | 38.71% | $27.67 | $46.45 |
| Close-inside only (`reversal_in_range: close`, midpoint TP) | 31 | 38.71% | $27.67 | $46.45 |
| **New default (close-inside + first profitable close)** | **31** | **41.94%** | **$-74.17** | **$81.00** |
| Stricter fully-inside (`reversal_in_range: body` + first profitable close) | 9 | 55.56% | $-31.28 | $37.48 |

First-profit exits clip winners at the first green/red close instead of waiting for the OR midpoint. Avg win fell ($10.11 → $4.98) and avg loss widened ($-5.51 → $-7.72) because losers still travel to the OR-extreme stop. Scratches disappeared (2 → 0). Win rate ticked up (38.71% → 41.94%) on the same 31 fills, but the book finished red.

`body` (high and low both inside the OR) is much stricter: 9 trades, 55.56% win rate, still red on this tape ($-31.28) with a tighter max DD ($37.48). Default stays **close-inside**.

This is one ~86-day Yahoo window on three symbols at 10 shares; it is not a claim that first-profit is a better or worse rule outside this sample.
