# ORB vs sample-rule backtest comparison

- Generated (UTC): 2026-09-19T16:07:45.007523Z
- Configs: config/ema9_trend_risk.example.yaml, config/ema9_trend_risk_nobe_pair_slope.example.yaml
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## Ranking by P&L % of starting equity

Figures are the engine totals for each book. They are **not** annualized and **not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.

| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close) | 14 | 57.14% | $2,998.96 | 2.999% | $2,510.94 | $604.79 | $-306.56 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (14 trades); ~31 calendar days |
| 2 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close, pair-cross SMA flat/rising) | 10 | 70.00% | $1,504.39 | 1.504% | $2,879.23 | $508.03 | $-683.95 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (10 trades); ~31 calendar days |

ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.

## Data windows and Yahoo limits

- Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. Requesting more than the cap returns HTTP 422. ORB needs 15m to build the opening range and 5m for probe/reversal, so its longest reliable Yahoo window is the 5m/15m 60-day cap.
- 5m and 15m history is the binding limit for ORB and for the 15m sample rules. The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer and its P&L% is not time-normalized against the 60-day books.
- Actual closed-bar windows downloaded:
- `AAPL 15Min: 1560 bars 2026-06-25 13:30:00+00:00 → 2026-09-18 19:45:00+00:00`
- `MSFT 15Min: 1560 bars 2026-06-25 13:30:00+00:00 → 2026-09-18 19:45:00+00:00`

## Monthly breakdown (realized P&L)

| Month | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close) | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close, pair-cross SMA flat/rising) |
| --- | ---: | ---: |
| 2026-08 | $2,998.96 (14t, 57.14%) | $1,504.39 (10t, 70.00%) |

# Per-book detail

- Generated (UTC): 2026-09-19T16:07:45.007523Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 58  (by symbol: {'AAPL': 26, 'MSFT': 32})
- Pattern hits in those signals: {'ema_cross': 58}
- Trades: 14  (by symbol: {'MSFT': 8, 'AAPL': 6})
- Wins / losses / scratch: 8 / 6 / 0
- Win rate: 57.14%
- Total P&L: $2,998.96 (2.999% of starting equity)
- Avg win: $604.79
- Avg loss: $-306.56
- Max drawdown: $2,510.94 (2.44%)
- Ending equity: $102,998.96
- Exit reasons: {'ma_cross': 10, 'session_flatten': 4}






- Skip reasons: {'entry_cutoff': 28, 'insufficient_cash': 4, 'already_in_position': 11}
- By side:
  - Long: 14 trades, 8 / 6 wins/losses, WR 57.14%, P&L $2,998.96
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is MA-cross at close (action.exit: ma_cross_close): after entry, on each completed signal-timeframe bar, leave when EMA(9) crosses SMA(20) against the position and fill at that bar's close — the same fill convention as ema_invalid / lower_high. Cross is EMA vs SMA close-to-close (not price vs MA). Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). Optional stop_loss_pct is a catastrophic stop only (off when omitted). Percent take-profit is ignored. Same-bar stop + cross → stop. If the cross bar is also the flatten bar, ma_cross at that close wins over session_flatten.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 28 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 4 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).
- MA-cross-at-close exit (action.exit: ma_cross_close): after entry, on each completed signal-timeframe bar, leave when EMA(9) crosses SMA(20) against the position and fill at that bar's close (same convention as ema_invalid / lower_high). Cross is EMA vs SMA close-to-close, not price vs MA. Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). Same-bar stop / lock_stop + cross → stop (stop is checked first). A same-bar lock-arm touch + pair-cross (low stays above the live stop) exits as ma_cross at that close and does not arm the lock. If the cross bar is also the flatten bar, ma_cross at that close wins over session_flatten.
- 10 trade(s) exited as ma_cross (EMA/SMA pair-cross against the position, fill at that bar's close).
- Exit P&L: ma_cross $-75.78 (10 trade(s)); session_flatten $3,074.74 (4 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 14  (wins 8 / losses 6)
- Win rate: 57.14%
- Total P&L: $2,998.96 (3.00% of starting equity)
- Ending equity: $102,998.96
- Best day (realized): 2026-08-06 $1,337.77 (1 trades)
- Worst day (realized): 2026-08-13 $-727.76 (1 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 14 | 57.14% | $2,998.96 | 3.00% | $102,998.96 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 4 | 50.00% | $1,355.17 | 1.36% | $101,355.17 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 3 | 33.33% | $-1,004.42 | -1.00% | $100,350.75 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 4 | 50.00% | $838.24 | 0.84% | $101,188.99 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 3 | 100.00% | $1,809.97 | 1.81% | $102,998.96 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 0 | n/a | $0.00 | 0.00% | $102,998.96 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-08-04 | 1 | 1 | 0 | $353.22 | 0.35% | $100,353.22 |
| 2026-08-05 | 1 | 0 | 1 | $-189.54 | -0.19% | $100,163.69 |
| 2026-08-06 | 1 | 1 | 0 | $1,337.77 | 1.34% | $101,501.46 |
| 2026-08-07 | 1 | 0 | 1 | $-146.28 | -0.15% | $101,355.17 |
| 2026-08-10 | 1 | 1 | 0 | $93.00 | 0.09% | $101,448.17 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $101,448.17 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $101,448.17 |
| 2026-08-13 | 1 | 0 | 1 | $-727.76 | -0.73% | $100,720.41 |
| 2026-08-14 | 1 | 0 | 1 | $-369.66 | -0.37% | $100,350.75 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $100,350.75 |
| 2026-08-18 | 1 | 1 | 0 | $113.88 | 0.11% | $100,464.63 |
| 2026-08-19 | 1 | 1 | 0 | $1,130.45 | 1.13% | $101,595.07 |
| 2026-08-20 | 1 | 0 | 1 | $-265.60 | -0.27% | $101,329.48 |
| 2026-08-21 | 1 | 0 | 1 | $-140.49 | -0.14% | $101,188.99 |
| 2026-08-24 | 1 | 1 | 0 | $186.88 | 0.19% | $101,375.87 |
| 2026-08-25 | 1 | 1 | 0 | $562.00 | 0.56% | $101,937.87 |
| 2026-08-26 | 1 | 1 | 0 | $1,061.09 | 1.06% | $102,998.96 |
| 2026-08-27 | 0 | 0 | 0 | $0.00 | 0.00% | $102,998.96 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $102,998.96 |
| 2026-08-31 | 0 | 0 | 0 | $0.00 | 0.00% | $102,998.96 |


## 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close, pair-cross SMA flat/rising)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 16  (by symbol: {'AAPL': 9, 'MSFT': 7})
- Pattern hits in those signals: {'ema_sma_cross': 16}
- Trades: 10  (by symbol: {'MSFT': 5, 'AAPL': 5})
- Wins / losses / scratch: 7 / 3 / 0
- Win rate: 70.00%
- Total P&L: $1,504.39 (1.504% of starting equity)
- Avg win: $508.03
- Avg loss: $-683.95
- Max drawdown: $2,879.23 (2.84%)
- Ending equity: $101,504.39
- Exit reasons: {'ma_cross': 8, 'session_flatten': 2}






- Skip reasons: {'entry_cutoff': 5, 'insufficient_cash': 1}
- By side:
  - Long: 10 trades, 7 / 3 wins/losses, WR 70.00%, P&L $1,504.39
- Entry is the noon day-trade stack on the signal timeframe (Long: EMA(9) crosses above SMA(20) close-to-close (prev EMA <= prev SMA and curr EMA > curr SMA — the inverse of the ma_cross_close exit) AND SMA(20) on the signal bar is flat or rising (SMA20[curr] >= SMA20[prev]). No RSI. No price-cross-above-EMA9 filter). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is MA-cross at close (action.exit: ma_cross_close): after entry, on each completed signal-timeframe bar, leave when EMA(9) crosses SMA(20) against the position and fill at that bar's close — the same fill convention as ema_invalid / lower_high. Cross is EMA vs SMA close-to-close (not price vs MA). Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). Optional stop_loss_pct is a catastrophic stop only (off when omitted). Percent take-profit is ignored. Same-bar stop + cross → stop. If the cross bar is also the flatten bar, ma_cross at that close wins over session_flatten.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 5 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 2 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).
- MA-cross-at-close exit (action.exit: ma_cross_close): after entry, on each completed signal-timeframe bar, leave when EMA(9) crosses SMA(20) against the position and fill at that bar's close (same convention as ema_invalid / lower_high). Cross is EMA vs SMA close-to-close, not price vs MA. Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). Same-bar stop / lock_stop + cross → stop (stop is checked first). A same-bar lock-arm touch + pair-cross (low stays above the live stop) exits as ma_cross at that close and does not arm the lock. If the cross bar is also the flatten bar, ma_cross at that close wins over session_flatten.
- 8 trade(s) exited as ma_cross (EMA/SMA pair-cross against the position, fill at that bar's close).
- Exit P&L: ma_cross $390.77 (8 trade(s)); session_flatten $1,113.62 (2 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 10  (wins 7 / losses 3)
- Win rate: 70.00%
- Total P&L: $1,504.39 (1.50% of starting equity)
- Ending equity: $101,504.39
- Best day (realized): 2026-08-19 $1,109.38 (1 trades)
- Worst day (realized): 2026-08-05 $-990.14 (1 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 10 | 70.00% | $1,504.39 | 1.50% | $101,504.39 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 2 | 50.00% | $-636.92 | -0.64% | $99,363.08 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 2 | 50.00% | $-622.28 | -0.62% | $98,740.80 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 1 | 100.00% | $1,109.38 | 1.11% | $99,850.18 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 5 | 80.00% | $1,654.20 | 1.65% | $101,504.39 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 0 | n/a | $0.00 | 0.00% | $101,504.39 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-08-04 | 1 | 1 | 0 | $353.22 | 0.35% | $100,353.22 |
| 2026-08-05 | 1 | 0 | 1 | $-990.14 | -0.99% | $99,363.08 |
| 2026-08-06 | 0 | 0 | 0 | $0.00 | 0.00% | $99,363.08 |
| 2026-08-07 | 0 | 0 | 0 | $0.00 | 0.00% | $99,363.08 |
| 2026-08-10 | 1 | 1 | 0 | $91.14 | 0.09% | $99,454.22 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $99,454.22 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $99,454.22 |
| 2026-08-13 | 1 | 0 | 1 | $-713.42 | -0.71% | $98,740.80 |
| 2026-08-14 | 0 | 0 | 0 | $0.00 | 0.00% | $98,740.80 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $98,740.80 |
| 2026-08-18 | 0 | 0 | 0 | $0.00 | 0.00% | $98,740.80 |
| 2026-08-19 | 1 | 1 | 0 | $1,109.38 | 1.11% | $99,850.18 |
| 2026-08-20 | 0 | 0 | 0 | $0.00 | 0.00% | $99,850.18 |
| 2026-08-21 | 0 | 0 | 0 | $0.00 | 0.00% | $99,850.18 |
| 2026-08-24 | 1 | 1 | 0 | $155.80 | 0.16% | $100,005.99 |
| 2026-08-25 | 1 | 1 | 0 | $440.64 | 0.44% | $100,446.63 |
| 2026-08-26 | 1 | 1 | 0 | $672.98 | 0.67% | $101,119.61 |
| 2026-08-27 | 1 | 0 | 1 | $-348.28 | -0.35% | $100,771.32 |
| 2026-08-28 | 1 | 1 | 0 | $733.06 | 0.73% | $101,504.39 |
| 2026-08-31 | 0 | 0 | 0 | $0.00 | 0.00% | $101,504.39 |


## Assumptions

- CLI trade window 2026-08-01T04:00:00+00:00 → 2026-09-01T04:00:00+00:00 (America/New_York date bounds; prior bars used only for warmup).
- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Exit is MA-cross at close (action.exit: ma_cross_close): after entry, on each completed signal-timeframe bar, leave when EMA(9) crosses SMA(20) against the position and fill at that bar's close — the same fill convention as ema_invalid / lower_high. Cross is EMA vs SMA close-to-close (not price vs MA). Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). Short: prev EMA <= prev SMA and curr EMA > curr SMA (cross-over / cover). Optional stop_loss_pct is a catastrophic stop only (off when omitted). Percent take-profit is ignored. Same-bar stop + cross → stop. If the cross bar is also the flatten bar, ma_cross at that close wins over session_flatten.
- If stop and take (or EMA-invalidation) both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open. EMA-invalidation, lower-high, and ma_cross_close exits fill at that completed bar's close. MA-cross (action.exit: ma_cross) exits fill at the next bar open after the opposing EMA/SMA pair-cross (long: EMA under SMA; short: EMA over SMA). ma_cross_close uses the same close-to-close EMA-vs-SMA pair-cross but fills at that bar's close.
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- A second symbol may open at the same time when cash covers its sized notional; otherwise the later signal is skipped (insufficient_cash).
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/ma_cross_close/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid, lower_high, and ma_cross_close fill at that close, so the signal exit wins over session_flatten). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Entry is the noon day-trade stack on the signal timeframe (Long: EMA(9) crosses above SMA(20) close-to-close (prev EMA <= prev SMA and curr EMA > curr SMA — the inverse of the ma_cross_close exit) AND SMA(20) on the signal bar is flat or rising (SMA20[curr] >= SMA20[prev]). No RSI. No price-cross-above-EMA9 filter). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.
