# ORB BEFORE vs AFTER: 1R take-profit

- Generated (UTC): 2026-09-13T15:08:46Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC), fresh download then clipped
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars: AAPL 15m 1560 / 5m 4677; MSFT 15m 1560 / 5m 4676; SPY 15m 1560 / 5m 4680
- Same closed-bar window as the previous AFTER book (`artifacts/orb_reversal_in_range_first_profit_comparison.md` / `artifacts/orb_backtest_results.md` from 2026-09-13T14:50:42Z)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares

Replaying **`reversal_in_range: off` + `take_profit_mode: or_midpoint`** on this download reproduced the last hybrid midpoint book exactly (31 trades, 38.71%, $27.67, max DD $46.45). Replaying **`reversal_in_range: close` + `take_profit_mode: first_profitable_close`** reproduced the last AFTER book exactly (31 trades, 41.94%, $-74.17, max DD $81.00). The AFTER column is the new example-config default (`reversal_in_range: close`, `take_profit_mode: one_r`) on that same tape. Locked rules are unchanged: `touch_and_band` probe, opposite-color next bar, entry at the following open, stop at the OR extreme, one trade per symbol, entry strictly before 10:30 ET.

If stop and 1R (or midpoint / first-profit) both trade on the same bar, the stop fills first.

## Headline

| | BEFORE (first-profit default) | AFTER (new default) |
| --- | ---: | ---: |
| Reversal filter | close must sit inside OR (`or_low <= close <= or_high`) | same |
| Take profit | first signal-bar close that is strictly profitable vs entry | 1R from entry (R = `|entry − stop|`; long entry+R, short entry−R) |
| Signals detected | 152 | 152 |
| Trades | 31 | 31 |
| Wins / losses / scratch | 13 / 18 / 0 | 11 / 20 / 0 |
| **Win rate** | **41.94%** | **35.48%** |
| **Total P&L** | **$-74.17** (−0.074%) | **$-61.87** (−0.062%) |
| Avg win | $4.98 | $7.93 |
| Avg loss | $-7.72 | $-7.46 |
| **Max drawdown** | **$81.00** (0.08%) | **$88.33** (0.09%) |
| Ending equity | $99,925.83 | $99,938.13 |
| Exit reasons | take 13, stop 18 | take 11, stop 20 |
| Trades by symbol | AAPL 10, MSFT 13, SPY 8 | AAPL 10, MSFT 13, SPY 8 |

Skipped on BEFORE and AFTER (still counted as signals, not trades): `entry_cutoff` 119, `max_trades_before_cutoff` 2.

## What moved the numbers

The taken-trade set stayed 31 (same 10:30 / one-trade gate, same close-inside reversal filter). The P&L move is from `one_r` vs `first_profitable_close` on those fills.

Measured on this tape (not a forecast):

| Variant | Trades | Win rate | P&L | Max DD |
| --- | ---: | ---: | ---: | ---: |
| Last hybrid midpoint (`touch_and_band`, midpoint TP, no reversal-range filter) | 31 | 38.71% | $27.67 | $46.45 |
| Close-inside + midpoint (`reversal_in_range: close`, `or_midpoint`) | 31 | 38.71% | $27.67 | $46.45 |
| Last default (close-inside + first profitable close) | 31 | 41.94% | $-74.17 | $81.00 |
| **New default (close-inside + 1R)** | **31** | **35.48%** | **$-61.87** | **$88.33** |

1R waits for a full risk multiple instead of exiting on the first profitable close. Avg win rose ($4.98 → $7.93) and two first-profit winners never reached 1R, so they ran to the OR-extreme stop (takes 13 → 11, stops 18 → 20). Win rate fell (41.94% → 35.48%). The book is still red, but less so than first-profit ($-74.17 → $-61.87). Max DD widened ($81.00 → $88.33). Midpoint on this tape remains the only green book of the three take modes ($27.67, max DD $46.45).

This is one ~86-day Yahoo window on three symbols at 10 shares; it is not a claim that 1R is a better or worse rule outside this sample.
