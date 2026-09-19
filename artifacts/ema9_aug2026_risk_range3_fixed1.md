# August 2026 1% equity risk: locked range>last-3 vs hard 1% fill stop + range>last-3

Companion to `artifacts/ema9_range3_fixed1.md`. Same Yahoo 15m AAPL+MSFT tape, `--start 2026-08-01 --end 2026-08-31`. A sizes 1% of equity at a 1.0% **reference R** (no live percent stop). F sizes at a **live** 1% fill stop (`stop_mode: entry_pct`). Engine totals below. Both **16 / 87.50% / $6,008.19**. 0 F stops. Not invented.

Replay: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_nobe_range3_fixed1.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_range3_fixed1.json --report artifacts/ema9_aug2026_risk_range3_fixed1.md`

# ORB vs sample-rule backtest comparison

- Generated (UTC): 2026-09-19T18:07:41.675676Z
- Configs: config/ema9_trend_risk.example.yaml, config/ema9_trend_risk_nobe_range3_fixed1.example.yaml
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## Ranking by P&L % of starting equity

Figures are the engine totals for each book. They are **not** annualized and **not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.

| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, range>last-3) | 16 | 87.50% | $6,008.19 | 6.008% | $2,028.83 | $537.84 | $-760.79 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (16 trades); ~31 calendar days |
| 2 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, range>last-3, entry 1.0%) | 16 | 87.50% | $6,008.19 | 6.008% | $2,028.83 | $537.84 | $-760.79 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (16 trades); ~31 calendar days |

ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.

## Data windows and Yahoo limits

- Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. Requesting more than the cap returns HTTP 422. ORB needs 15m to build the opening range and 5m for probe/reversal, so its longest reliable Yahoo window is the 5m/15m 60-day cap.
- 5m and 15m history is the binding limit for ORB and for the 15m sample rules. The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer and its P&L% is not time-normalized against the 60-day books.
- Actual closed-bar windows downloaded:
- `AAPL 15Min: 1560 bars 2026-06-25 13:30:00+00:00 → 2026-09-18 19:45:00+00:00`
- `MSFT 15Min: 1560 bars 2026-06-25 13:30:00+00:00 → 2026-09-18 19:45:00+00:00`

## Monthly breakdown (realized P&L)

| Month | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, range>last-3) | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, range>last-3, entry 1.0%) |
| --- | ---: | ---: |
| 2026-08 | $6,008.19 (16t, 87.50%) | $6,008.19 (16t, 87.50%) |

# Per-book detail

- Generated (UTC): 2026-09-19T18:07:41.675676Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, range>last-3)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 58  (by symbol: {'AAPL': 26, 'MSFT': 32})
- Pattern hits in those signals: {'ema_cross': 58}
- Trades: 16  (by symbol: {'MSFT': 10, 'AAPL': 6})
- Wins / losses / scratch: 14 / 2 / 0
- Win rate: 87.50%
- Total P&L: $6,008.19 (6.008% of starting equity)
- Avg win: $537.84
- Avg loss: $-760.79
- Max drawdown: $2,028.83 (1.96%)
- Ending equity: $106,008.19
- Exit reasons: {'range_expansion': 16}






- Skip reasons: {'entry_cutoff': 35, 'insufficient_cash': 3, 'already_in_position': 3}
- By side:
  - Long: 16 trades, 14 / 2 wins/losses, WR 87.50%, P&L $6,008.19
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is range expansion (action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars (equivalently larger than each of the last 3) and exit at that bar's close — the same fill convention as ema_invalid / lower_high. Do not arm on the entry bar. Need those prior bars in the series. Equal range stays valid. Optional stop_loss_pct is a catastrophic stop only (off when omitted). Percent take-profit is ignored. Same-bar stop + range expansion → stop. If the expansion bar is also the flatten bar, range_expansion at that close wins over session_flatten.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, range_expansion, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 35 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- Range-expansion exit (action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close (same fill convention as ema_invalid / lower_high). Equal range stays valid. Need those prior bars in the series. Same-bar stop + range expansion → stop. If the expansion bar is also the flatten bar, range_expansion at that close wins over session_flatten.
- 16 trade(s) exited as range_expansion (bar range > max of previous 3 bars, fill at that close).
- Exit P&L: range_expansion $6,008.19 (16 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 16  (wins 14 / losses 2)
- Win rate: 87.50%
- Total P&L: $6,008.19 (6.01% of starting equity)
- Ending equity: $106,008.19
- Best day (realized): 2026-08-19 $2,452.67 (2 trades)
- Worst day (realized): 2026-08-13 $-830.02 (1 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 16 | 87.50% | $6,008.19 | 6.01% | $106,008.19 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 4 | 100.00% | $1,891.92 | 1.89% | $101,891.92 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 4 | 50.00% | $-514.50 | -0.51% | $101,377.42 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 5 | 100.00% | $3,110.46 | 3.11% | $104,487.89 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 3 | 100.00% | $1,520.31 | 1.52% | $106,008.19 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 0 | n/a | $0.00 | 0.00% | $106,008.19 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-08-04 | 1 | 1 | 0 | $812.00 | 0.81% | $100,812.00 |
| 2026-08-05 | 1 | 1 | 0 | $283.62 | 0.28% | $101,095.62 |
| 2026-08-06 | 1 | 1 | 0 | $399.84 | 0.40% | $101,495.46 |
| 2026-08-07 | 1 | 1 | 0 | $396.46 | 0.40% | $101,891.92 |
| 2026-08-10 | 1 | 1 | 0 | $933.64 | 0.93% | $102,825.57 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $102,825.57 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $102,825.57 |
| 2026-08-13 | 1 | 0 | 1 | $-830.02 | -0.83% | $101,995.55 |
| 2026-08-14 | 2 | 1 | 1 | $-618.13 | -0.62% | $101,377.42 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $101,377.42 |
| 2026-08-18 | 1 | 1 | 0 | $35.17 | 0.04% | $101,412.60 |
| 2026-08-19 | 2 | 2 | 0 | $2,452.67 | 2.45% | $103,865.26 |
| 2026-08-20 | 1 | 1 | 0 | $3.27 | 0.00% | $103,868.53 |
| 2026-08-21 | 1 | 1 | 0 | $619.35 | 0.62% | $104,487.89 |
| 2026-08-24 | 1 | 1 | 0 | $244.58 | 0.24% | $104,732.47 |
| 2026-08-25 | 1 | 1 | 0 | $195.81 | 0.20% | $104,928.28 |
| 2026-08-26 | 1 | 1 | 0 | $1,079.91 | 1.08% | $106,008.19 |
| 2026-08-27 | 0 | 0 | 0 | $0.00 | 0.00% | $106,008.19 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $106,008.19 |
| 2026-08-31 | 0 | 0 | 0 | $0.00 | 0.00% | $106,008.19 |


## 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, range>last-3, entry 1.0%)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 58  (by symbol: {'AAPL': 26, 'MSFT': 32})
- Pattern hits in those signals: {'ema_cross': 58}
- Trades: 16  (by symbol: {'MSFT': 10, 'AAPL': 6})
- Wins / losses / scratch: 14 / 2 / 0
- Win rate: 87.50%
- Total P&L: $6,008.19 (6.008% of starting equity)
- Avg win: $537.84
- Avg loss: $-760.79
- Max drawdown: $2,028.83 (1.96%)
- Ending equity: $106,008.19
- Exit reasons: {'range_expansion': 16}






- Skip reasons: {'entry_cutoff': 35, 'insufficient_cash': 3, 'already_in_position': 3}
- By side:
  - Long: 16 trades, 14 / 2 wins/losses, WR 87.50%, P&L $6,008.19
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is a hard 1% fill stop plus range expansion (stop_mode: entry_pct and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars (equivalently larger than each of the last 3) and exit at that bar's close — the same fill convention as ema_invalid / lower_high. Do not arm on the entry bar. Need those prior bars in the series. Equal range stays valid. Hard 1% stop is also live (stop_mode: entry_pct): initial stop is fill × (1 − 1/100); it never moves (not lock_plus). Whichever hits first wins: stop on this bar beats range expansion (stop is checked first). If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, range_expansion, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 35 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- Range-expansion exit (action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close (same fill convention as ema_invalid / lower_high). Equal range stays valid. Need those prior bars in the series. Same-bar stop + range expansion → stop. If the expansion bar is also the flatten bar, range_expansion at that close wins over session_flatten.
- 16 trade(s) exited as range_expansion (bar range > max of previous 3 bars, fill at that close).
- Exit P&L: range_expansion $6,008.19 (16 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.
- Entry-anchored stop (stop_mode: entry_pct): initial protective stop is 1% from the *fill* (next-bar open), not the signal-bar close. percent still uses the signal close. No percent take when take_profit_pct is omitted.
- Fixed entry stop (stop_mode: entry_pct): the initial fill stop never moves (not lock_plus). Exits are that stop, range_expansion, or session_flatten (or eod). Same-bar stop + range expansion → stop (stop is checked first).

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 16  (wins 14 / losses 2)
- Win rate: 87.50%
- Total P&L: $6,008.19 (6.01% of starting equity)
- Ending equity: $106,008.19
- Best day (realized): 2026-08-19 $2,452.67 (2 trades)
- Worst day (realized): 2026-08-13 $-830.02 (1 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 16 | 87.50% | $6,008.19 | 6.01% | $106,008.19 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 4 | 100.00% | $1,891.92 | 1.89% | $101,891.92 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 4 | 50.00% | $-514.50 | -0.51% | $101,377.42 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 5 | 100.00% | $3,110.46 | 3.11% | $104,487.89 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 3 | 100.00% | $1,520.31 | 1.52% | $106,008.19 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 0 | n/a | $0.00 | 0.00% | $106,008.19 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-08-04 | 1 | 1 | 0 | $812.00 | 0.81% | $100,812.00 |
| 2026-08-05 | 1 | 1 | 0 | $283.62 | 0.28% | $101,095.62 |
| 2026-08-06 | 1 | 1 | 0 | $399.84 | 0.40% | $101,495.46 |
| 2026-08-07 | 1 | 1 | 0 | $396.46 | 0.40% | $101,891.92 |
| 2026-08-10 | 1 | 1 | 0 | $933.64 | 0.93% | $102,825.57 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $102,825.57 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $102,825.57 |
| 2026-08-13 | 1 | 0 | 1 | $-830.02 | -0.83% | $101,995.55 |
| 2026-08-14 | 2 | 1 | 1 | $-618.13 | -0.62% | $101,377.42 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $101,377.42 |
| 2026-08-18 | 1 | 1 | 0 | $35.17 | 0.04% | $101,412.60 |
| 2026-08-19 | 2 | 2 | 0 | $2,452.67 | 2.45% | $103,865.26 |
| 2026-08-20 | 1 | 1 | 0 | $3.27 | 0.00% | $103,868.53 |
| 2026-08-21 | 1 | 1 | 0 | $619.35 | 0.62% | $104,487.89 |
| 2026-08-24 | 1 | 1 | 0 | $244.58 | 0.24% | $104,732.47 |
| 2026-08-25 | 1 | 1 | 0 | $195.81 | 0.20% | $104,928.28 |
| 2026-08-26 | 1 | 1 | 0 | $1,079.91 | 1.08% | $106,008.19 |
| 2026-08-27 | 0 | 0 | 0 | $0.00 | 0.00% | $106,008.19 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $106,008.19 |
| 2026-08-31 | 0 | 0 | 0 | $0.00 | 0.00% | $106,008.19 |


## Assumptions

- CLI trade window 2026-08-01T04:00:00+00:00 → 2026-09-01T04:00:00+00:00 (America/New_York date bounds; prior bars used only for warmup).
- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is range expansion (action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars (equivalently larger than each of the last 3) and exit at that bar's close — the same fill convention as ema_invalid / lower_high. Do not arm on the entry bar. Need those prior bars in the series. Equal range stays valid. Optional stop_loss_pct is a catastrophic stop only (off when omitted). Percent take-profit is ignored. Same-bar stop + range expansion → stop. If the expansion bar is also the flatten bar, range_expansion at that close wins over session_flatten.
- If stop and take (or EMA-invalidation) both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open. EMA-invalidation, lower-high, range-expansion, and ma_cross_close exits fill at that completed bar's close. MA-cross (action.exit: ma_cross) exits fill at the next bar open after the opposing EMA/SMA pair-cross (long: EMA under SMA; short: EMA over SMA). ma_cross_close uses the same close-to-close EMA-vs-SMA pair-cross but fills at that bar's close. range_expansion leaves when the completed bar's range (high − low) is strictly greater than the max of the previous N bars (default 3), not on the entry bar.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- A second symbol may open at the same time when cash covers its sized notional; otherwise the later signal is skipped (insufficient_cash).
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, range_expansion, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Exit is a hard 1% fill stop plus range expansion (stop_mode: entry_pct and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars (equivalently larger than each of the last 3) and exit at that bar's close — the same fill convention as ema_invalid / lower_high. Do not arm on the entry bar. Need those prior bars in the series. Equal range stays valid. Hard 1% stop is also live (stop_mode: entry_pct): initial stop is fill × (1 − 1/100); it never moves (not lock_plus). Whichever hits first wins: stop on this bar beats range expansion (stop is checked first). If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid.
- ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.
