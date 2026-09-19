# August 2026 1% equity risk: locked MA-cross vs hard 1% fill stop + MA-cross

Companion to `artifacts/ema9_macross_stop1.md`. Same Yahoo 15m AAPL+MSFT tape, `--start 2026-08-01 --end 2026-08-31`. A has **no live percent stop**; share count uses `stop_pct: 1.0` as a **reference R only**. D uses the same 1.0% R **and** a live `entry_pct` 1% stop at fill × 0.99 (never moves; not lock_plus). Engine totals below. **Identical** 14 / 57.14% / $2,998.96 (0 stop hits). Not invented.

Replay: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_nobe_macross_stop1.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_macross_stop1.json --report artifacts/ema9_aug2026_risk_macross_stop1.md`

# ORB vs sample-rule backtest comparison

- Generated (UTC): 2026-09-19T16:28:38.663341Z
- Configs: config/ema9_trend_risk.example.yaml, config/ema9_trend_risk_nobe_macross_stop1.example.yaml
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## Ranking by P&L % of starting equity

Figures are the engine totals for each book. They are **not** annualized and **not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.

| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close) | 14 | 57.14% | $2,998.96 | 2.999% | $2,510.94 | $604.79 | $-306.56 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (14 trades); ~31 calendar days |
| 2 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close, entry 1.0%) | 14 | 57.14% | $2,998.96 | 2.999% | $2,510.94 | $604.79 | $-306.56 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (14 trades); ~31 calendar days |

ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.

## Data windows and Yahoo limits

- Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. Requesting more than the cap returns HTTP 422. ORB needs 15m to build the opening range and 5m for probe/reversal, so its longest reliable Yahoo window is the 5m/15m 60-day cap.
- 5m and 15m history is the binding limit for ORB and for the 15m sample rules. The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer and its P&L% is not time-normalized against the 60-day books.
- Actual closed-bar windows downloaded:
- `AAPL 15Min: 1560 bars 2026-06-25 13:30:00+00:00 → 2026-09-18 19:45:00+00:00`
- `MSFT 15Min: 1560 bars 2026-06-25 13:30:00+00:00 → 2026-09-18 19:45:00+00:00`

## Monthly breakdown (realized P&L)

| Month | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close) | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close, entry 1.0%) |
| --- | ---: | ---: |
| 2026-08 | $2,998.96 (14t, 57.14%) | $2,998.96 (14t, 57.14%) |

# Per-book detail

- Generated (UTC): 2026-09-19T16:28:38.663341Z
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


## 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, MA-cross close, entry 1.0%)

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
- Exit is a hard 1% fill stop plus MA-cross at close (stop_mode: entry_pct and action.exit: ma_cross_close): after entry, leave when EMA(9) crosses SMA(20) against the position and fill at that bar's close — the same fill convention as ema_invalid / lower_high. Cross is EMA vs SMA close-to-close (not price vs MA). Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). Hard 1% stop is also live (stop_mode: entry_pct): initial stop is fill × (1 − 1/100); it never moves (not lock_plus). Whichever hits first wins: stop on this bar beats the pair-cross (stop is checked first). If the cross bar is also the flatten bar and the stop did not hit, ma_cross at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid.
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
- Entry-anchored stop (stop_mode: entry_pct): initial protective stop is 1% from the *fill* (next-bar open), not the signal-bar close. percent still uses the signal close. No percent take when take_profit_pct is omitted.
- Fixed entry stop (stop_mode: entry_pct): the initial fill stop never moves (not lock_plus). Exits are that stop, ma_cross_close, or session_flatten (or eod). Same-bar stop + pair-cross → stop (stop is checked first).

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
- Exit is a hard 1% fill stop plus MA-cross at close (stop_mode: entry_pct and action.exit: ma_cross_close): after entry, leave when EMA(9) crosses SMA(20) against the position and fill at that bar's close — the same fill convention as ema_invalid / lower_high. Cross is EMA vs SMA close-to-close (not price vs MA). Long: prev EMA >= prev SMA and curr EMA < curr SMA (cross-under). Hard 1% stop is also live (stop_mode: entry_pct): initial stop is fill × (1 − 1/100); it never moves (not lock_plus). Whichever hits first wins: stop on this bar beats the pair-cross (stop is checked first). If the cross bar is also the flatten bar and the stop did not hit, ma_cross at that close wins over session_flatten. Percent take-profit is ignored. No lock-at-+1%. No half-take. No pyramid.
- ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.
