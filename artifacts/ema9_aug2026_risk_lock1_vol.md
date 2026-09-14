# ORB vs sample-rule backtest comparison

- Generated (UTC): 2026-09-14T01:20:14.561287Z
- Configs: config/ema9_trend_risk_nobe_lock1.example.yaml, config/ema9_trend_risk_nobe_lock1_vol.example.yaml
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## Ranking by P&L % of starting equity

Figures are the engine totals for each book. They are **not** annualized and **not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.

| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, lock +1.0%) | 15 | 73.33% | $5,489.78 | 5.490% | $2,743.31 | $697.61 | $-546.00 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (15 trades); ~31 calendar days |
| 2 | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, lock +1.0%, vol>prev) | 11 | 72.73% | $3,613.53 | 3.614% | $1,436.03 | $641.09 | $-505.07 | 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z | small sample (11 trades); ~31 calendar days |

ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.

## Data windows and Yahoo limits

- Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. Requesting more than the cap returns HTTP 422. ORB needs 15m to build the opening range and 5m for probe/reversal, so its longest reliable Yahoo window is the 5m/15m 60-day cap.
- 5m and 15m history is the binding limit for ORB and for the 15m sample rules. The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer and its P&L% is not time-normalized against the 60-day books.
- Actual closed-bar windows downloaded:
- `AAPL 15Min: 1560 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:45:00+00:00`
- `MSFT 15Min: 1560 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:45:00+00:00`

## Monthly breakdown (realized P&L)

| Month | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, lock +1.0%) | 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, lock +1.0%, vol>prev) |
| --- | ---: | ---: |
| 2026-08 | $5,489.78 (15t, 73.33%) | $3,613.53 (11t, 72.73%) |

# Per-book detail

- Generated (UTC): 2026-09-14T01:20:14.561287Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, lock +1.0%)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 58  (by symbol: {'AAPL': 26, 'MSFT': 32})
- Pattern hits in those signals: {'ema_cross': 58}
- Trades: 15  (by symbol: {'MSFT': 8, 'AAPL': 7})
- Wins / losses / scratch: 11 / 4 / 0
- Win rate: 73.33%
- Total P&L: $5,489.78 (5.490% of starting equity)
- Avg win: $697.61
- Avg loss: $-546.00
- Max drawdown: $2,743.31 (2.58%)
- Ending equity: $105,489.78
- Exit reasons: {'lock_stop': 6, 'session_flatten': 8, 'stop': 1}

- Lock armed: 6

- Skip reasons: {'entry_cutoff': 28, 'already_in_position': 11, 'insufficient_cash': 3}
- By side:
  - Long: 15 trades, 11 / 4 wins/losses, WR 73.33%, P&L $5,489.78
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Lock-plus stop (stop_mode: lock_plus): initial stop is 1% from the fill (long: below; short: above). First trade/touch of entry×(1+1/100) for a long (bar high ≥ that print) or entry×(1−1/100) for a short (bar low ≤ that print) moves the stop to that same print and leaves it. The locked stop is live from the next bar; same-bar pullback after the tag uses the initial stop. A later hit of the locked stop is lock_stop. take_profit_pct is omitted (stop variant or session_flatten only; no % take).
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid and lower_high fill at that close). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 28 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 8 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).
- Exit P&L: lock_stop $5,623.20 (6 trade(s)); session_flatten $917.28 (8 trade(s)); stop $-1,050.69 (1 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.
- Entry-anchored stop (stop_mode: lock_plus): initial protective stop is 1% from the *fill* (next-bar open), not the signal-bar close. percent still uses the signal close. No percent take when take_profit_pct is omitted.
- Lock-plus (stop_mode: lock_plus) on longs only: first trade/touch of entry×(1+1/100) (bar high ≥ that print) moves the stop there and leaves it. Shorts have no percent / lock_plus stop. The locked stop is live from the next bar; same-bar pullback after the tag still uses the initial 1% protective stop. Later hit of the locked stop is exit reason lock_stop. Session flatten covers longs and shorts.
- 6 trade(s) armed the +lock; 6 exited as lock_stop.

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 15  (wins 11 / losses 4)
- Win rate: 73.33%
- Total P&L: $5,489.78 (5.49% of starting equity)
- Ending equity: $105,489.78
- Best day (realized): 2026-08-04 $2,004.49 (2 trades)
- Worst day (realized): 2026-08-20 $-1,050.69 (1 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 15 | 73.33% | $5,489.78 | 5.49% | $105,489.78 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 5 | 100.00% | $3,745.45 | 3.75% | $103,745.45 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 3 | 33.33% | $170.36 | 0.17% | $103,915.81 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 4 | 75.00% | $395.20 | 0.40% | $104,311.01 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 3 | 66.67% | $1,178.77 | 1.18% | $105,489.78 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 0 | n/a | $0.00 | 0.00% | $105,489.78 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-08-04 | 2 | 2 | 0 | $2,004.49 | 2.00% | $102,004.49 |
| 2026-08-05 | 1 | 1 | 0 | $683.10 | 0.68% | $102,687.59 |
| 2026-08-06 | 1 | 1 | 0 | $673.94 | 0.67% | $103,361.53 |
| 2026-08-07 | 1 | 1 | 0 | $383.92 | 0.38% | $103,745.45 |
| 2026-08-10 | 1 | 1 | 0 | $1,035.65 | 1.04% | $104,781.10 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $104,781.10 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $104,781.10 |
| 2026-08-13 | 1 | 0 | 1 | $-225.75 | -0.23% | $104,555.35 |
| 2026-08-14 | 1 | 0 | 1 | $-639.54 | -0.64% | $103,915.81 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $103,915.81 |
| 2026-08-18 | 1 | 1 | 0 | $117.71 | 0.12% | $104,033.52 |
| 2026-08-19 | 1 | 1 | 0 | $1,037.93 | 1.04% | $105,071.46 |
| 2026-08-20 | 1 | 0 | 1 | $-1,050.69 | -1.05% | $104,020.76 |
| 2026-08-21 | 1 | 1 | 0 | $290.25 | 0.29% | $104,311.01 |
| 2026-08-24 | 1 | 0 | 1 | $-268.00 | -0.27% | $104,043.02 |
| 2026-08-25 | 1 | 1 | 0 | $575.58 | 0.58% | $104,618.60 |
| 2026-08-26 | 1 | 1 | 0 | $871.18 | 0.87% | $105,489.78 |
| 2026-08-27 | 0 | 0 | 0 | $0.00 | 0.00% | $105,489.78 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $105,489.78 |
| 2026-08-31 | 0 | 0 | 0 | $0.00 | 0.00% | $105,489.78 |


## 15m AAPL+MSFT 1% risk (cutoff 12:00, flat 15:55, lock +1.0%, vol>prev)

- Period: 2026-08-01T04:00:00Z → 2026-09-01T03:59:59.999999Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 43  (by symbol: {'AAPL': 19, 'MSFT': 24})
- Pattern hits in those signals: {'ema_cross': 43}
- Trades: 11  (by symbol: {'AAPL': 5, 'MSFT': 6})
- Wins / losses / scratch: 8 / 3 / 0
- Win rate: 72.73%
- Total P&L: $3,613.53 (3.614% of starting equity)
- Avg win: $641.09
- Avg loss: $-505.07
- Max drawdown: $1,436.03 (1.40%)
- Ending equity: $103,613.53
- Exit reasons: {'session_flatten': 6, 'lock_stop': 4, 'stop': 1}

- Lock armed: 4

- Skip reasons: {'entry_cutoff': 21, 'already_in_position': 10}
- By side:
  - Long: 11 trades, 8 / 3 wins/losses, WR 72.73%, P&L $3,613.53
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70 AND signal-bar volume > previous-bar volume). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Lock-plus stop (stop_mode: lock_plus): initial stop is 1% from the fill (long: below; short: above). First trade/touch of entry×(1+1/100) for a long (bar high ≥ that print) or entry×(1−1/100) for a short (bar low ≤ that print) moves the stop to that same print and leaves it. The locked stop is live from the next bar; same-bar pullback after the tag uses the initial stop. A later hit of the locked stop is lock_stop. take_profit_pct is omitted (stop variant or session_flatten only; no % take).
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid and lower_high fill at that close). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Session gates (America/New_York): entry_cutoff=12:00 (skip signals whose next-bar fill is at/after that clock); flatten_by=15:55 (force flat at the close of the bar containing that clock: 15m RTH → 15:45 ET bar close when flatten_by is 15:55; 5m RTH → 15:50 ET bar close, the last 5m bar that completes at/before 15:55).
- 21 signal(s) skipped as entry_cutoff (12:00 America/New_York; fill would be at/after the cutoff).
- 6 trade(s) exited as session_flatten (time-exit at the flatten bar close; flatten_by 15:55 America/New_York).
- Exit P&L: lock_stop $3,472.58 (4 trade(s)); session_flatten $1,172.59 (6 trade(s)); stop $-1,031.65 (1 trade(s)).
- One lot per symbol (long or short, not both); both names may be open at once if cash covers the second risk-sized entry, otherwise the later signal is skipped. An opposite-side signal while that symbol is already in a trade is skipped (opposite_signal_in_trade). Max concurrent symbols this run: 1. Ticks with 2+ names open: 0.
- Entry-anchored stop (stop_mode: lock_plus): initial protective stop is 1% from the *fill* (next-bar open), not the signal-bar close. percent still uses the signal close. No percent take when take_profit_pct is omitted.
- Lock-plus (stop_mode: lock_plus) on longs only: first trade/touch of entry×(1+1/100) (bar high ≥ that print) moves the stop there and leaves it. Shorts have no percent / lock_plus stop. The locked stop is live from the next bar; same-bar pullback after the tag still uses the initial 1% protective stop. Later hit of the locked stop is exit reason lock_stop. Session flatten covers longs and shorts.
- 4 trade(s) armed the +lock; 4 exited as lock_stop.

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 11  (wins 8 / losses 3)
- Win rate: 72.73%
- Total P&L: $3,613.53 (3.61% of starting equity)
- Ending equity: $103,613.53
- Best day (realized): 2026-08-10 $1,010.39 (1 trades)
- Worst day (realized): 2026-08-20 $-1,031.65 (1 trades)

### By calendar month

| Month | Sessions | Trades | Win rate | P&L $ | P&L % | Equity EOM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08 (2026-08-03 → 2026-08-31) | 21 | 11 | 72.73% | $3,613.53 | 3.61% | $103,613.53 |

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 2 | 100.00% | $1,329.60 | 1.33% | $101,329.60 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 3 | 66.67% | $925.28 | 0.93% | $102,254.88 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 3 | 66.67% | $198.74 | 0.20% | $102,453.61 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 3 | 66.67% | $1,159.91 | 1.16% | $103,613.53 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 0 | n/a | $0.00 | 0.00% | $103,613.53 |

### Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,000.00 |
| 2026-08-05 | 1 | 1 | 0 | $668.61 | 0.67% | $100,668.61 |
| 2026-08-06 | 1 | 1 | 0 | $660.98 | 0.66% | $101,329.60 |
| 2026-08-07 | 0 | 0 | 0 | $0.00 | 0.00% | $101,329.60 |
| 2026-08-10 | 1 | 1 | 0 | $1,010.39 | 1.01% | $102,339.99 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $102,339.99 |
| 2026-08-12 | 0 | 0 | 0 | $0.00 | 0.00% | $102,339.99 |
| 2026-08-13 | 1 | 0 | 1 | $-220.38 | -0.22% | $102,119.61 |
| 2026-08-14 | 1 | 1 | 0 | $135.27 | 0.14% | $102,254.88 |
| 2026-08-17 | 0 | 0 | 0 | $0.00 | 0.00% | $102,254.88 |
| 2026-08-18 | 0 | 0 | 0 | $0.00 | 0.00% | $102,254.88 |
| 2026-08-19 | 1 | 1 | 0 | $945.53 | 0.95% | $103,200.41 |
| 2026-08-20 | 1 | 0 | 1 | $-1,031.65 | -1.03% | $102,168.76 |
| 2026-08-21 | 1 | 1 | 0 | $284.85 | 0.28% | $102,453.61 |
| 2026-08-24 | 1 | 0 | 1 | $-263.20 | -0.26% | $102,190.42 |
| 2026-08-25 | 1 | 1 | 0 | $567.43 | 0.57% | $102,757.85 |
| 2026-08-26 | 1 | 1 | 0 | $855.67 | 0.86% | $103,613.53 |
| 2026-08-27 | 0 | 0 | 0 | $0.00 | 0.00% | $103,613.53 |
| 2026-08-28 | 0 | 0 | 0 | $0.00 | 0.00% | $103,613.53 |
| 2026-08-31 | 0 | 0 | 0 | $0.00 | 0.00% | $103,613.53 |


## Assumptions

- CLI trade window 2026-08-01T04:00:00+00:00 → 2026-09-01T04:00:00+00:00 (America/New_York date bounds; prior bars used only for warmup).
- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- Lock-plus stop (stop_mode: lock_plus): initial stop is 1% from the fill (long: below; short: above). First trade/touch of entry×(1+1/100) for a long (bar high ≥ that print) or entry×(1−1/100) for a short (bar low ≤ that print) moves the stop to that same print and leaves it. The locked stop is live from the next bar; same-bar pullback after the tag uses the initial stop. A later hit of the locked stop is lock_stop. take_profit_pct is omitted (stop variant or session_flatten only; no % take).
- If stop and take (or EMA-invalidation) both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open. EMA-invalidation and lower-high exits fill at that completed bar's close. MA-cross exits fill at the next bar open after the opposing EMA/SMA pair-cross (long: EMA under SMA; short: EMA over SMA).
- One open lot per symbol (no pyramiding; long or short, not both). A second signal while that symbol is already open is skipped (already_in_position, or opposite_signal_in_trade when the new side is the other way).
- A second symbol may open at the same time when cash covers its sized notional; otherwise the later signal is skipped (insufficient_cash).
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Session gates (America/New_York): entry_cutoff=12:00 skips a signal when the next-bar fill (bar open) is at/after that clock. flatten_by=15:55 force-flats at the close of the bar that contains that clock (exit reason session_flatten): 15m RTH bars opening :00,:15,:30,:45 flatten on the 15:45 ET bar close when flatten_by is 15:55 (last regular 15m bar, aligned with “by 15:55”); 5m flattens on the 15:50 ET bar close (last 5m bar that completes at/before 15:55). Stop/take/ema_invalid/lower_high/ma_cross-on-this-bar still win if they hit first (ma_cross fills at the next open, so a same-bar flatten_by close wins; ema_invalid and lower_high fill at that close). Set entry_cutoff / flatten_by to null / off to restore overnight holds.
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00. Size types: shares, percent_equity, or risk_pct (percent stop: shares = floor((equity_risk * equity) / ((stop_pct/100) * price)); stop_mode sma20: R = signal-bar close − SMA20, shares = floor((equity_risk * equity) / R)).
- Entry is the noon day-trade stack on the signal timeframe (Long: close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70 AND signal-bar volume > previous-bar volume). Fill at the next bar open. One position per symbol (long or short, not both); an opposite signal while in a trade is skipped (opposite_signal_in_trade).
- ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.
