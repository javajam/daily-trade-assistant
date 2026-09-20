# ORB vs sample-rule backtest comparison

- Generated (UTC): 2026-09-20T13:59:54.973662Z
- Configs: config/ema9_trend_bracket_nobe_range3_fixed1_nocutoff.example.yaml, config/ema9_trend_bracket_nobe_range3_atr1.example.yaml, config/ema9_trend_bracket_nobe_range3_atr15.example.yaml
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## Ranking by P&L % of starting equity

Figures are the engine totals for each book. They are **not** annualized and **not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.

| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, entry 1.0%) | 82 | 31.71% | $-65.58 | -0.066% | $259.15 | $24.25 | $-12.66 | 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z | ~85 calendar days |
| 2 | 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, ATR14×1) | 81 | 39.51% | $-178.84 | -0.179% | $396.83 | $24.94 | $-20.35 | 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z | ~85 calendar days |
| 3 | 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, ATR14×1.5) | 78 | 41.03% | $-322.94 | -0.323% | $449.85 | $24.85 | $-24.84 | 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z | ~85 calendar days |

ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.

## Data windows and Yahoo limits

- Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. Requesting more than the cap returns HTTP 422. ORB needs 15m to build the opening range and 5m for probe/reversal, so its longest reliable Yahoo window is the 5m/15m 60-day cap.
- 5m and 15m history is the binding limit for ORB and for the 15m sample rules. The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer and its P&L% is not time-normalized against the 60-day books.
- Actual closed-bar windows downloaded:
- `SOXL 15Min: 1560 bars 2026-06-25 13:30:00+00:00 → 2026-09-18 19:45:00+00:00`

## Monthly breakdown (realized P&L)

| Month | 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, entry 1.0%) | 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, ATR14×1) | 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, ATR14×1.5) |
| --- | ---: | ---: | ---: |
| 2026-06 | $83.97 (4t, 25.00%) | $33.21 (4t, 50.00%) | $-29.85 (4t, 50.00%) |
| 2026-07 | $28.64 (25t, 32.00%) | $30.09 (25t, 44.00%) | $27.52 (24t, 50.00%) |
| 2026-08 | $-106.15 (35t, 32.35%) | $-184.13 (34t, 36.36%) | $-242.83 (32t, 35.48%) |
| 2026-09 | $-72.04 (18t, 33.33%) | $-58.01 (18t, 38.89%) | $-77.79 (18t, 38.89%) |

# Per-book detail

- Generated (UTC): 2026-09-20T13:59:54.973662Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, entry 1.0%)

- Period: 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z
- Bars used: {'SOXL:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 84  (by symbol: {'SOXL': 84})
- Pattern hits in those signals: {'ema_cross': 84}
- Trades: 82  (by symbol: {'SOXL': 82})
- Wins / losses / scratch: 26 / 55 / 1
- Win rate: 31.71%
- Total P&L: $-65.58 (-0.066% of starting equity)
- Avg win: $24.25
- Avg loss: $-12.66
- Max drawdown: $259.15 (0.26%)
- Ending equity: $99,934.42
- Exit reasons: {'stop': 47, 'range_expansion': 29, 'session_flatten': 6}






- Skip reasons: {'already_in_position': 2}
- By side:
  - Long: 82 trades, 26 / 55 wins/losses, WR 31.71%, P&L $-65.58
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is a hard 1% fill stop plus range expansion (stop_mode: entry_pct and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars (equivalently larger than each of the last 3) and exit at that bar's close — the same fill convention as ema_invalid / lower_high. Do not arm on the entry bar. Need those prior bars in the series. Equal range stays valid. Hard 1% stop is also live (stop_mode: entry_pct): initial stop is fill × (1 − 1/100); it never moves (not lock_plus). Whichever hits first wins: stop on this bar beats range expansion (stop is checked first). If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid. Expansion bars with body/range <= 0.1 (doji) do not fire; wait for a later non-doji expansion, the protective stop, or flatten.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=off skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, range_expansion, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=off (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 6 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).
- Range-expansion exit (action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close (same fill convention as ema_invalid / lower_high). Equal range stays valid. Need those prior bars in the series. Same-bar stop + range expansion → stop. If the expansion bar is also the flatten bar, range_expansion at that close wins over session_flatten. Expansion bars with body/range <= 0.1 (doji) do not fire the range exit; wait for a later non-doji expansion, the protective stop, or flatten.
- 29 trade(s) exited as range_expansion (bar range > max of previous 3 bars, fill at that close).
- Exit P&L: range_expansion $593.69 (29 trade(s)); session_flatten $4.45 (6 trade(s)); stop $-663.71 (47 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.
- Entry-anchored stop (stop_mode: entry_pct): initial protective stop is 1% from the *fill* (next-bar open), not the signal-bar close. percent still uses the signal close. No percent take when take_profit_pct is omitted.
- Fixed entry stop (stop_mode: entry_pct): the initial fill stop never moves (not lock_plus). Exits are that stop, range_expansion, or session_flatten (or eod). Same-bar stop + range expansion → stop (stop is checked first).

### Monthly

- Month: 2026-06-25 → 2026-09-18
- Session days: 60
- Trades: 82  (wins 26 / losses 55)
- Win rate: 32.10%
- Total P&L: $-65.58 (-0.07% of starting equity)
- Ending equity: $99,934.42
- Best day (realized): 2026-06-29 $128.75 (2 trades)
- Worst day (realized): 2026-06-26 $-44.78 (2 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (2026-06-25 → 2026-06-30) | 4 | 4 | 25.00% | $83.97 | 0.08% | $100,083.97 |
| 2026-07 (2026-07-01 → 2026-07-31) | 22 | 25 | 32.00% | $28.64 | 0.03% | $100,112.61 |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 35 | 32.35% | $-106.15 | -0.11% | $100,006.46 |
| 2026-09 (2026-09-01 → 2026-09-18) | 13 | 18 | 33.33% | $-72.04 | -0.07% | $99,934.42 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W26 (2026-06-25 → 2026-06-26) | 2 | 0.00% | $-44.78 | -0.04% | $99,955.22 |
| 2026-W27 (2026-06-29 → 2026-07-02) | 3 | 33.33% | $106.40 | 0.11% | $100,061.62 |
| 2026-W28 (2026-07-06 → 2026-07-10) | 5 | 20.00% | $25.12 | 0.03% | $100,086.74 |
| 2026-W29 (2026-07-13 → 2026-07-17) | 3 | 33.33% | $-18.05 | -0.02% | $100,068.69 |
| 2026-W30 (2026-07-20 → 2026-07-24) | 9 | 44.44% | $-33.44 | -0.03% | $100,035.26 |
| 2026-W31 (2026-07-27 → 2026-07-31) | 7 | 28.57% | $77.35 | 0.08% | $100,112.61 |
| 2026-W32 (2026-08-03 → 2026-08-07) | 11 | 27.27% | $-44.66 | -0.04% | $100,067.94 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 7 | 42.86% | $18.50 | 0.02% | $100,086.44 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 6 | 33.33% | $-19.95 | -0.02% | $100,066.49 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 8 | 14.29% | $-62.19 | -0.06% | $100,004.31 |
| 2026-W36 (2026-08-31 → 2026-09-04) | 8 | 62.50% | $3.85 | 0.00% | $100,008.16 |
| 2026-W37 (2026-09-08 → 2026-09-11) | 6 | 16.67% | $-57.00 | -0.06% | $99,951.16 |
| 2026-W38 (2026-09-14 → 2026-09-18) | 7 | 28.57% | $-16.74 | -0.02% | $99,934.42 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06-25 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-06-26 | 2 | 0 | 2 | $-44.78 | -0.04% | $99,955.22 |
| 2026-06-29 | 2 | 1 | 1 | $128.75 | 0.13% | $100,083.97 |
| 2026-06-30 | 0 | 0 | 0 | $0.00 | 0.00% | $100,083.97 |
| 2026-07-01 | 0 | 0 | 0 | $0.00 | 0.00% | $100,083.97 |
| 2026-07-02 | 1 | 0 | 1 | $-22.35 | -0.02% | $100,061.62 |
| 2026-07-06 | 1 | 0 | 1 | $-19.72 | -0.02% | $100,041.90 |
| 2026-07-07 | 0 | 0 | 0 | $0.00 | 0.00% | $100,041.90 |
| 2026-07-08 | 2 | 1 | 1 | $67.67 | 0.07% | $100,109.57 |
| 2026-07-09 | 1 | 0 | 1 | $-19.98 | -0.02% | $100,089.59 |
| 2026-07-10 | 1 | 0 | 1 | $-2.85 | -0.00% | $100,086.74 |
| 2026-07-13 | 0 | 0 | 0 | $0.00 | 0.00% | $100,086.74 |
| 2026-07-14 | 1 | 1 | 0 | $10.70 | 0.01% | $100,097.44 |
| 2026-07-15 | 1 | 0 | 1 | $-16.28 | -0.02% | $100,081.16 |
| 2026-07-16 | 0 | 0 | 0 | $0.00 | 0.00% | $100,081.16 |
| 2026-07-17 | 1 | 0 | 1 | $-12.47 | -0.01% | $100,068.69 |
| 2026-07-20 | 3 | 1 | 2 | $-22.75 | -0.02% | $100,045.94 |
| 2026-07-21 | 2 | 1 | 1 | $-13.95 | -0.01% | $100,031.99 |
| 2026-07-22 | 3 | 2 | 1 | $18.89 | 0.02% | $100,050.88 |
| 2026-07-23 | 1 | 0 | 1 | $-15.62 | -0.02% | $100,035.26 |
| 2026-07-24 | 0 | 0 | 0 | $0.00 | 0.00% | $100,035.26 |
| 2026-07-27 | 0 | 0 | 0 | $0.00 | 0.00% | $100,035.26 |
| 2026-07-28 | 1 | 1 | 0 | $44.90 | 0.04% | $100,080.16 |
| 2026-07-29 | 0 | 0 | 0 | $0.00 | 0.00% | $100,080.16 |
| 2026-07-30 | 3 | 1 | 2 | $68.20 | 0.07% | $100,148.35 |
| 2026-07-31 | 3 | 0 | 3 | $-35.75 | -0.04% | $100,112.61 |
| 2026-08-03 | 2 | 1 | 1 | $19.28 | 0.02% | $100,131.88 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,131.88 |
| 2026-08-05 | 2 | 0 | 2 | $-27.40 | -0.03% | $100,104.48 |
| 2026-08-06 | 3 | 0 | 3 | $-41.05 | -0.04% | $100,063.43 |
| 2026-08-07 | 4 | 2 | 2 | $4.51 | 0.00% | $100,067.94 |
| 2026-08-10 | 2 | 0 | 2 | $-28.12 | -0.03% | $100,039.82 |
| 2026-08-11 | 2 | 0 | 2 | $-26.98 | -0.03% | $100,012.84 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $100,012.84 |
| 2026-08-13 | 2 | 2 | 0 | $59.25 | 0.06% | $100,072.09 |
| 2026-08-14 | 1 | 1 | 0 | $14.35 | 0.01% | $100,086.44 |
| 2026-08-17 | 1 | 0 | 1 | $-15.43 | -0.02% | $100,071.02 |
| 2026-08-18 | 1 | 1 | 0 | $30.10 | 0.03% | $100,101.12 |
| 2026-08-19 | 1 | 0 | 1 | $-12.15 | -0.01% | $100,088.97 |
| 2026-08-20 | 2 | 0 | 2 | $-24.38 | -0.02% | $100,064.58 |
| 2026-08-21 | 1 | 1 | 0 | $1.91 | 0.00% | $100,066.49 |
| 2026-08-24 | 2 | 0 | 2 | $-22.72 | -0.02% | $100,043.77 |
| 2026-08-25 | 2 | 0 | 2 | $-23.36 | -0.02% | $100,020.41 |
| 2026-08-26 | 2 | 1 | 1 | $-3.76 | -0.00% | $100,016.65 |
| 2026-08-27 | 2 | 0 | 1 | $-12.34 | -0.01% | $100,004.31 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $100,004.31 |
| 2026-08-31 | 3 | 2 | 1 | $2.15 | 0.00% | $100,006.46 |
| 2026-09-01 | 1 | 1 | 0 | $1.55 | 0.00% | $100,008.01 |
| 2026-09-02 | 2 | 1 | 1 | $3.40 | 0.00% | $100,011.41 |
| 2026-09-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,011.41 |
| 2026-09-04 | 2 | 1 | 1 | $-3.25 | -0.00% | $100,008.16 |
| 2026-09-08 | 1 | 0 | 1 | $-12.59 | -0.01% | $99,995.57 |
| 2026-09-09 | 2 | 0 | 2 | $-22.18 | -0.02% | $99,973.40 |
| 2026-09-10 | 1 | 0 | 1 | $-11.63 | -0.01% | $99,961.76 |
| 2026-09-11 | 2 | 1 | 1 | $-10.60 | -0.01% | $99,951.16 |
| 2026-09-14 | 0 | 0 | 0 | $0.00 | 0.00% | $99,951.16 |
| 2026-09-15 | 2 | 1 | 1 | $-7.79 | -0.01% | $99,943.38 |
| 2026-09-16 | 2 | 0 | 2 | $-17.73 | -0.02% | $99,925.65 |
| 2026-09-17 | 2 | 1 | 1 | $8.97 | 0.01% | $99,934.62 |
| 2026-09-18 | 1 | 0 | 1 | $-0.20 | -0.00% | $99,934.42 |


## 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, ATR14×1)

- Period: 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z
- Bars used: {'SOXL:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 84  (by symbol: {'SOXL': 84})
- Pattern hits in those signals: {'ema_cross': 84}
- Trades: 81  (by symbol: {'SOXL': 81})
- Wins / losses / scratch: 32 / 48 / 1
- Win rate: 39.51%
- Total P&L: $-178.84 (-0.179% of starting equity)
- Avg win: $24.94
- Avg loss: $-20.35
- Max drawdown: $396.83 (0.40%)
- Ending equity: $99,821.16
- Exit reasons: {'stop': 31, 'range_expansion': 41, 'session_flatten': 9}






- Skip reasons: {'already_in_position': 3}
- By side:
  - Long: 81 trades, 32 / 48 wins/losses, WR 39.51%, P&L $-178.84
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is a Wilder ATR(14)×1 fill stop plus range expansion (stop_mode: atr and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close. ATR is computed through the closed signal/entry bar (true range = max(H−L, |H−prev close|, |L−prev close|); seed = SMA of the first 14 TRs, then ATR = (prev_ATR×(14−1) + TR) / 14). Stop is fill − 1×ATR (long); it never trails. Whichever hits first wins: stop on this bar beats range expansion. If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid. No min/max stop-distance floor. Expansion bars with body/range <= 0.1 (doji) do not fire; wait for a later non-doji expansion, the protective stop, or flatten.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=off skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, range_expansion, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=off (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 9 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).
- Range-expansion exit (action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close (same fill convention as ema_invalid / lower_high). Equal range stays valid. Need those prior bars in the series. Same-bar stop + range expansion → stop. If the expansion bar is also the flatten bar, range_expansion at that close wins over session_flatten. Expansion bars with body/range <= 0.1 (doji) do not fire the range exit; wait for a later non-doji expansion, the protective stop, or flatten.
- 41 trade(s) exited as range_expansion (bar range > max of previous 3 bars, fill at that close).
- Exit P&L: range_expansion $675.19 (41 trade(s)); session_flatten $14.75 (9 trade(s)); stop $-868.78 (31 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.
- ATR stop (stop_mode: atr): Wilder ATR(14) is computed through the closed signal/entry bar (true range = max(H−L, |H−prev close|, |L−prev close|); seed = SMA of the first 14 TRs, then ATR = (prev_ATR×(14−1) + TR) / 14). Protective stop is fill − 1×ATR (long) or fill + 1×ATR (short). The dollar distance is taken from the signal-bar ATR and applied to the next-bar fill; it never trails. Signals skip when ATR is unavailable (atr_unavailable). Fills skip when that stop is not beyond the fill. No min/max stop-distance floor.
- 0 signal(s) skipped as atr_unavailable.

### Monthly

- Month: 2026-06-25 → 2026-09-18
- Session days: 60
- Trades: 81  (wins 32 / losses 48)
- Win rate: 40.00%
- Total P&L: $-178.84 (-0.18% of starting equity)
- Ending equity: $99,821.16
- Best day (realized): 2026-06-29 $159.33 (2 trades)
- Worst day (realized): 2026-06-26 $-126.12 (2 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (2026-06-25 → 2026-06-30) | 4 | 4 | 50.00% | $33.21 | 0.03% | $100,033.21 |
| 2026-07 (2026-07-01 → 2026-07-31) | 22 | 25 | 44.00% | $30.09 | 0.03% | $100,063.30 |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 34 | 36.36% | $-184.13 | -0.18% | $99,879.17 |
| 2026-09 (2026-09-01 → 2026-09-18) | 13 | 18 | 38.89% | $-58.01 | -0.06% | $99,821.16 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W26 (2026-06-25 → 2026-06-26) | 2 | 0.00% | $-126.12 | -0.13% | $99,873.88 |
| 2026-W27 (2026-06-29 → 2026-07-02) | 3 | 66.67% | $103.30 | 0.10% | $99,977.17 |
| 2026-W28 (2026-07-06 → 2026-07-10) | 5 | 60.00% | $162.39 | 0.16% | $100,139.56 |
| 2026-W29 (2026-07-13 → 2026-07-17) | 3 | 66.67% | $4.48 | 0.00% | $100,144.04 |
| 2026-W30 (2026-07-20 → 2026-07-24) | 9 | 44.44% | $-134.85 | -0.13% | $100,009.20 |
| 2026-W31 (2026-07-27 → 2026-07-31) | 7 | 28.57% | $54.10 | 0.05% | $100,063.30 |
| 2026-W32 (2026-08-03 → 2026-08-07) | 10 | 40.00% | $-72.94 | -0.07% | $99,990.37 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 7 | 42.86% | $-21.77 | -0.02% | $99,968.60 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 6 | 33.33% | $-24.28 | -0.02% | $99,944.31 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 8 | 14.29% | $-66.99 | -0.07% | $99,877.32 |
| 2026-W36 (2026-08-31 → 2026-09-04) | 8 | 62.50% | $3.76 | 0.00% | $99,881.08 |
| 2026-W37 (2026-09-08 → 2026-09-11) | 6 | 33.33% | $-46.61 | -0.05% | $99,834.46 |
| 2026-W38 (2026-09-14 → 2026-09-18) | 7 | 28.57% | $-13.30 | -0.01% | $99,821.16 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06-25 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-06-26 | 2 | 0 | 2 | $-126.12 | -0.13% | $99,873.88 |
| 2026-06-29 | 2 | 2 | 0 | $159.33 | 0.16% | $100,033.21 |
| 2026-06-30 | 0 | 0 | 0 | $0.00 | 0.00% | $100,033.21 |
| 2026-07-01 | 0 | 0 | 0 | $0.00 | 0.00% | $100,033.21 |
| 2026-07-02 | 1 | 0 | 1 | $-56.04 | -0.06% | $99,977.17 |
| 2026-07-06 | 1 | 1 | 0 | $56.49 | 0.06% | $100,033.67 |
| 2026-07-07 | 0 | 0 | 0 | $0.00 | 0.00% | $100,033.67 |
| 2026-07-08 | 2 | 2 | 0 | $145.89 | 0.15% | $100,179.56 |
| 2026-07-09 | 1 | 0 | 1 | $-37.15 | -0.04% | $100,142.41 |
| 2026-07-10 | 1 | 0 | 1 | $-2.85 | -0.00% | $100,139.56 |
| 2026-07-13 | 0 | 0 | 0 | $0.00 | 0.00% | $100,139.56 |
| 2026-07-14 | 1 | 1 | 0 | $10.70 | 0.01% | $100,150.26 |
| 2026-07-15 | 1 | 1 | 0 | $27.50 | 0.03% | $100,177.76 |
| 2026-07-16 | 0 | 0 | 0 | $0.00 | 0.00% | $100,177.76 |
| 2026-07-17 | 1 | 0 | 1 | $-33.72 | -0.03% | $100,144.04 |
| 2026-07-20 | 3 | 1 | 2 | $-71.50 | -0.07% | $100,072.54 |
| 2026-07-21 | 2 | 1 | 1 | $-39.15 | -0.04% | $100,033.40 |
| 2026-07-22 | 3 | 2 | 1 | $4.48 | 0.00% | $100,037.87 |
| 2026-07-23 | 1 | 0 | 1 | $-28.68 | -0.03% | $100,009.20 |
| 2026-07-24 | 0 | 0 | 0 | $0.00 | 0.00% | $100,009.20 |
| 2026-07-27 | 0 | 0 | 0 | $0.00 | 0.00% | $100,009.20 |
| 2026-07-28 | 1 | 1 | 0 | $44.90 | 0.04% | $100,054.10 |
| 2026-07-29 | 0 | 0 | 0 | $0.00 | 0.00% | $100,054.10 |
| 2026-07-30 | 3 | 1 | 2 | $71.69 | 0.07% | $100,125.78 |
| 2026-07-31 | 3 | 0 | 3 | $-62.48 | -0.06% | $100,063.30 |
| 2026-08-03 | 2 | 1 | 1 | $-7.81 | -0.01% | $100,055.49 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,055.49 |
| 2026-08-05 | 2 | 1 | 1 | $-18.02 | -0.02% | $100,037.47 |
| 2026-08-06 | 2 | 0 | 2 | $-34.68 | -0.03% | $100,002.79 |
| 2026-08-07 | 4 | 2 | 2 | $-12.43 | -0.01% | $99,990.37 |
| 2026-08-10 | 2 | 0 | 2 | $-50.46 | -0.05% | $99,939.91 |
| 2026-08-11 | 2 | 0 | 2 | $-44.91 | -0.04% | $99,895.00 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $99,895.00 |
| 2026-08-13 | 2 | 2 | 0 | $59.25 | 0.06% | $99,954.25 |
| 2026-08-14 | 1 | 1 | 0 | $14.35 | 0.01% | $99,968.60 |
| 2026-08-17 | 1 | 0 | 1 | $-15.74 | -0.02% | $99,952.86 |
| 2026-08-18 | 1 | 1 | 0 | $30.10 | 0.03% | $99,982.96 |
| 2026-08-19 | 1 | 0 | 1 | $-9.10 | -0.01% | $99,973.86 |
| 2026-08-20 | 2 | 0 | 2 | $-31.45 | -0.03% | $99,942.41 |
| 2026-08-21 | 1 | 1 | 0 | $1.91 | 0.00% | $99,944.31 |
| 2026-08-24 | 2 | 0 | 2 | $-21.07 | -0.02% | $99,923.25 |
| 2026-08-25 | 2 | 0 | 2 | $-32.47 | -0.03% | $99,890.78 |
| 2026-08-26 | 2 | 1 | 1 | $-3.87 | -0.00% | $99,886.92 |
| 2026-08-27 | 2 | 0 | 1 | $-9.60 | -0.01% | $99,877.32 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $99,877.32 |
| 2026-08-31 | 3 | 2 | 1 | $1.85 | 0.00% | $99,879.17 |
| 2026-09-01 | 1 | 1 | 0 | $1.55 | 0.00% | $99,880.72 |
| 2026-09-02 | 2 | 1 | 1 | $3.40 | 0.00% | $99,884.12 |
| 2026-09-03 | 0 | 0 | 0 | $0.00 | 0.00% | $99,884.12 |
| 2026-09-04 | 2 | 1 | 1 | $-3.04 | -0.00% | $99,881.08 |
| 2026-09-08 | 1 | 0 | 1 | $-15.03 | -0.02% | $99,866.04 |
| 2026-09-09 | 2 | 1 | 1 | $-5.60 | -0.01% | $99,860.44 |
| 2026-09-10 | 1 | 0 | 1 | $-10.92 | -0.01% | $99,849.52 |
| 2026-09-11 | 2 | 1 | 1 | $-15.06 | -0.02% | $99,834.46 |
| 2026-09-14 | 0 | 0 | 0 | $0.00 | 0.00% | $99,834.46 |
| 2026-09-15 | 2 | 1 | 1 | $-5.55 | -0.01% | $99,828.91 |
| 2026-09-16 | 2 | 0 | 2 | $-16.53 | -0.02% | $99,812.39 |
| 2026-09-17 | 2 | 1 | 1 | $8.97 | 0.01% | $99,821.36 |
| 2026-09-18 | 1 | 0 | 1 | $-0.20 | -0.00% | $99,821.16 |


## 15m SOXL 10-share (flat 15:55, range>last-3, skip-doji, ATR14×1.5)

- Period: 2026-06-25T13:30:00Z → 2026-09-18T19:45:00Z
- Bars used: {'SOXL:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 84  (by symbol: {'SOXL': 84})
- Pattern hits in those signals: {'ema_cross': 84}
- Trades: 78  (by symbol: {'SOXL': 78})
- Wins / losses / scratch: 32 / 45 / 1
- Win rate: 41.03%
- Total P&L: $-322.94 (-0.323% of starting equity)
- Avg win: $24.85
- Avg loss: $-24.84
- Max drawdown: $449.85 (0.45%)
- Ending equity: $99,677.06
- Exit reasons: {'stop': 21, 'range_expansion': 48, 'session_flatten': 9}






- Skip reasons: {'already_in_position': 6}
- By side:
  - Long: 78 trades, 32 / 45 wins/losses, WR 41.03%, P&L $-322.94
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is a Wilder ATR(14)×1.5 fill stop plus range expansion (stop_mode: atr and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close. ATR is computed through the closed signal/entry bar (true range = max(H−L, |H−prev close|, |L−prev close|); seed = SMA of the first 14 TRs, then ATR = (prev_ATR×(14−1) + TR) / 14). Stop is fill − 1.5×ATR (long); it never trails. Whichever hits first wins: stop on this bar beats range expansion. If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid. No min/max stop-distance floor. Expansion bars with body/range <= 0.1 (doji) do not fire; wait for a later non-doji expansion, the protective stop, or flatten.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=off skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, range_expansion, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=off (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 9 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).
- Range-expansion exit (action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close (same fill convention as ema_invalid / lower_high). Equal range stays valid. Need those prior bars in the series. Same-bar stop + range expansion → stop. If the expansion bar is also the flatten bar, range_expansion at that close wins over session_flatten. Expansion bars with body/range <= 0.1 (doji) do not fire the range exit; wait for a later non-doji expansion, the protective stop, or flatten.
- 48 trade(s) exited as range_expansion (bar range > max of previous 3 bars, fill at that close).
- Exit P&L: range_expansion $556.73 (48 trade(s)); session_flatten $14.75 (9 trade(s)); stop $-894.43 (21 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.
- ATR stop (stop_mode: atr): Wilder ATR(14) is computed through the closed signal/entry bar (true range = max(H−L, |H−prev close|, |L−prev close|); seed = SMA of the first 14 TRs, then ATR = (prev_ATR×(14−1) + TR) / 14). Protective stop is fill − 1.5×ATR (long) or fill + 1.5×ATR (short). The dollar distance is taken from the signal-bar ATR and applied to the next-bar fill; it never trails. Signals skip when ATR is unavailable (atr_unavailable). Fills skip when that stop is not beyond the fill. No min/max stop-distance floor.
- 0 signal(s) skipped as atr_unavailable.

### Monthly

- Month: 2026-06-25 → 2026-09-18
- Session days: 60
- Trades: 78  (wins 32 / losses 45)
- Win rate: 41.56%
- Total P&L: $-322.94 (-0.32% of starting equity)
- Ending equity: $99,677.06
- Best day (realized): 2026-06-29 $159.33 (2 trades)
- Worst day (realized): 2026-06-26 $-189.18 (2 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06 (2026-06-25 → 2026-06-30) | 4 | 4 | 50.00% | $-29.85 | -0.03% | $99,970.15 |
| 2026-07 (2026-07-01 → 2026-07-31) | 22 | 24 | 50.00% | $27.52 | 0.03% | $99,997.67 |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 32 | 35.48% | $-242.83 | -0.24% | $99,754.84 |
| 2026-09 (2026-09-01 → 2026-09-18) | 13 | 18 | 38.89% | $-77.79 | -0.08% | $99,677.06 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W26 (2026-06-25 → 2026-06-26) | 2 | 0.00% | $-189.18 | -0.19% | $99,810.82 |
| 2026-W27 (2026-06-29 → 2026-07-02) | 3 | 66.67% | $75.28 | 0.08% | $99,886.10 |
| 2026-W28 (2026-07-06 → 2026-07-10) | 5 | 60.00% | $143.81 | 0.14% | $100,029.90 |
| 2026-W29 (2026-07-13 → 2026-07-17) | 3 | 66.67% | $-12.37 | -0.01% | $100,017.53 |
| 2026-W30 (2026-07-20 → 2026-07-24) | 8 | 62.50% | $-79.15 | -0.08% | $99,938.39 |
| 2026-W31 (2026-07-27 → 2026-07-31) | 7 | 28.57% | $59.29 | 0.06% | $99,997.67 |
| 2026-W32 (2026-08-03 → 2026-08-07) | 9 | 33.33% | $-73.92 | -0.07% | $99,923.75 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 6 | 50.00% | $-34.84 | -0.03% | $99,888.90 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 6 | 33.33% | $-42.83 | -0.04% | $99,846.08 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 8 | 14.29% | $-93.08 | -0.09% | $99,752.99 |
| 2026-W36 (2026-08-31 → 2026-09-04) | 8 | 62.50% | $0.30 | 0.00% | $99,753.29 |
| 2026-W37 (2026-09-08 → 2026-09-11) | 6 | 33.33% | $-58.12 | -0.06% | $99,695.17 |
| 2026-W38 (2026-09-14 → 2026-09-18) | 7 | 28.57% | $-18.12 | -0.02% | $99,677.06 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-06-25 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-06-26 | 2 | 0 | 2 | $-189.18 | -0.19% | $99,810.82 |
| 2026-06-29 | 2 | 2 | 0 | $159.33 | 0.16% | $99,970.15 |
| 2026-06-30 | 0 | 0 | 0 | $0.00 | 0.00% | $99,970.15 |
| 2026-07-01 | 0 | 0 | 0 | $0.00 | 0.00% | $99,970.15 |
| 2026-07-02 | 1 | 0 | 1 | $-84.06 | -0.08% | $99,886.10 |
| 2026-07-06 | 1 | 1 | 0 | $56.49 | 0.06% | $99,942.59 |
| 2026-07-07 | 0 | 0 | 0 | $0.00 | 0.00% | $99,942.59 |
| 2026-07-08 | 2 | 2 | 0 | $145.89 | 0.15% | $100,088.48 |
| 2026-07-09 | 1 | 0 | 1 | $-55.73 | -0.06% | $100,032.75 |
| 2026-07-10 | 1 | 0 | 1 | $-2.85 | -0.00% | $100,029.90 |
| 2026-07-13 | 0 | 0 | 0 | $0.00 | 0.00% | $100,029.90 |
| 2026-07-14 | 1 | 1 | 0 | $10.70 | 0.01% | $100,040.60 |
| 2026-07-15 | 1 | 1 | 0 | $27.50 | 0.03% | $100,068.10 |
| 2026-07-16 | 0 | 0 | 0 | $0.00 | 0.00% | $100,068.10 |
| 2026-07-17 | 1 | 0 | 1 | $-50.57 | -0.05% | $100,017.53 |
| 2026-07-20 | 3 | 1 | 2 | $-110.40 | -0.11% | $99,907.13 |
| 2026-07-21 | 2 | 1 | 1 | $-11.76 | -0.01% | $99,895.37 |
| 2026-07-22 | 2 | 2 | 0 | $33.21 | 0.03% | $99,928.59 |
| 2026-07-23 | 1 | 1 | 0 | $9.80 | 0.01% | $99,938.39 |
| 2026-07-24 | 0 | 0 | 0 | $0.00 | 0.00% | $99,938.39 |
| 2026-07-27 | 0 | 0 | 0 | $0.00 | 0.00% | $99,938.39 |
| 2026-07-28 | 1 | 1 | 0 | $44.90 | 0.04% | $99,983.29 |
| 2026-07-29 | 0 | 0 | 0 | $0.00 | 0.00% | $99,983.29 |
| 2026-07-30 | 3 | 1 | 2 | $71.69 | 0.07% | $100,054.97 |
| 2026-07-31 | 3 | 0 | 3 | $-57.30 | -0.06% | $99,997.67 |
| 2026-08-03 | 2 | 1 | 1 | $12.90 | 0.01% | $100,010.57 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,010.57 |
| 2026-08-05 | 1 | 0 | 1 | $-7.25 | -0.01% | $100,003.32 |
| 2026-08-06 | 2 | 0 | 2 | $-51.55 | -0.05% | $99,951.77 |
| 2026-08-07 | 4 | 2 | 2 | $-28.02 | -0.03% | $99,923.75 |
| 2026-08-10 | 2 | 0 | 2 | $-75.69 | -0.08% | $99,848.06 |
| 2026-08-11 | 1 | 0 | 1 | $-32.75 | -0.03% | $99,815.30 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $99,815.30 |
| 2026-08-13 | 2 | 2 | 0 | $59.25 | 0.06% | $99,874.55 |
| 2026-08-14 | 1 | 1 | 0 | $14.35 | 0.01% | $99,888.90 |
| 2026-08-17 | 1 | 0 | 1 | $-23.61 | -0.02% | $99,865.30 |
| 2026-08-18 | 1 | 1 | 0 | $30.10 | 0.03% | $99,895.40 |
| 2026-08-19 | 1 | 0 | 1 | $-9.10 | -0.01% | $99,886.30 |
| 2026-08-20 | 2 | 0 | 2 | $-42.13 | -0.04% | $99,844.17 |
| 2026-08-21 | 1 | 1 | 0 | $1.91 | 0.00% | $99,846.08 |
| 2026-08-24 | 2 | 0 | 2 | $-27.40 | -0.03% | $99,818.68 |
| 2026-08-25 | 2 | 0 | 2 | $-41.64 | -0.04% | $99,777.04 |
| 2026-08-26 | 2 | 1 | 1 | $-9.65 | -0.01% | $99,767.39 |
| 2026-08-27 | 2 | 0 | 1 | $-14.39 | -0.01% | $99,752.99 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $99,752.99 |
| 2026-08-31 | 3 | 2 | 1 | $1.85 | 0.00% | $99,754.84 |
| 2026-09-01 | 1 | 1 | 0 | $1.55 | 0.00% | $99,756.39 |
| 2026-09-02 | 2 | 1 | 1 | $3.40 | 0.00% | $99,759.79 |
| 2026-09-03 | 0 | 0 | 0 | $0.00 | 0.00% | $99,759.79 |
| 2026-09-04 | 2 | 1 | 1 | $-6.50 | -0.01% | $99,753.29 |
| 2026-09-08 | 1 | 0 | 1 | $-12.75 | -0.01% | $99,740.54 |
| 2026-09-09 | 2 | 1 | 1 | $-5.60 | -0.01% | $99,734.94 |
| 2026-09-10 | 1 | 0 | 1 | $-16.38 | -0.02% | $99,718.56 |
| 2026-09-11 | 2 | 1 | 1 | $-23.39 | -0.02% | $99,695.17 |
| 2026-09-14 | 0 | 0 | 0 | $0.00 | 0.00% | $99,695.17 |
| 2026-09-15 | 2 | 1 | 1 | $-5.55 | -0.01% | $99,689.62 |
| 2026-09-16 | 2 | 0 | 2 | $-21.34 | -0.02% | $99,668.28 |
| 2026-09-17 | 2 | 1 | 1 | $8.97 | 0.01% | $99,677.26 |
| 2026-09-18 | 1 | 0 | 1 | $-0.20 | -0.00% | $99,677.06 |


## Assumptions

- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is a hard 1% fill stop plus range expansion (stop_mode: entry_pct and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars (equivalently larger than each of the last 3) and exit at that bar's close — the same fill convention as ema_invalid / lower_high. Do not arm on the entry bar. Need those prior bars in the series. Equal range stays valid. Hard 1% stop is also live (stop_mode: entry_pct): initial stop is fill × (1 − 1/100); it never moves (not lock_plus). Whichever hits first wins: stop on this bar beats range expansion (stop is checked first). If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid. Expansion bars with body/range <= 0.1 (doji) do not fire; wait for a later non-doji expansion, the protective stop, or flatten.
- If stop and take (or EMA-invalidation) both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open. EMA-invalidation, lower-high, range-expansion, and ma_cross_close exits fill at that completed bar's close. MA-cross (action.exit: ma_cross) exits fill at the next bar open after the opposing EMA/SMA pair-cross (long: EMA under SMA; short: EMA over SMA). ma_cross_close uses the same close-to-close EMA-vs-SMA pair-cross but fills at that bar's close. range_expansion leaves when the completed bar's range (high − low) is strictly greater than the max of the previous N bars (default 3), not on the entry bar.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- A second symbol may open at the same time when cash covers its sized notional; otherwise the later signal is skipped (insufficient_cash).
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Session gates (America/New_York): entry_cutoff=off skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/range_expansion/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, range_expansion, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Exit is a Wilder ATR(14)×1 fill stop plus range expansion (stop_mode: atr and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close. ATR is computed through the closed signal/entry bar (true range = max(H−L, |H−prev close|, |L−prev close|); seed = SMA of the first 14 TRs, then ATR = (prev_ATR×(14−1) + TR) / 14). Stop is fill − 1×ATR (long); it never trails. Whichever hits first wins: stop on this bar beats range expansion. If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid. No min/max stop-distance floor. Expansion bars with body/range <= 0.1 (doji) do not fire; wait for a later non-doji expansion, the protective stop, or flatten.
- Exit is a Wilder ATR(14)×1.5 fill stop plus range expansion (stop_mode: atr and action.exit: range_expansion): after entry, on each completed signal-timeframe bar *after the entry/fill bar*, leave when that bar's range (high − low) is strictly greater than the max range of the previous 3 bars and exit at that bar's close. ATR is computed through the closed signal/entry bar (true range = max(H−L, |H−prev close|, |L−prev close|); seed = SMA of the first 14 TRs, then ATR = (prev_ATR×(14−1) + TR) / 14). Stop is fill − 1.5×ATR (long); it never trails. Whichever hits first wins: stop on this bar beats range expansion. If the expansion bar is also the flatten bar and the stop did not hit, range_expansion at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid. No min/max stop-distance floor. Expansion bars with body/range <= 0.1 (doji) do not fire; wait for a later non-doji expansion, the protective stop, or flatten.
- ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.
