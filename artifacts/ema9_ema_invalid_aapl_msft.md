# 9 EMA trend: EMA-invalidation, AAPL/MSFT only (supporting)

Headline 15m vs 5m comparison including SOXL is `artifacts/ema9_ema_invalid_5m_vs_15m.md`. This file is the `--symbols AAPL,MSFT` replay (prior universe, same `exit: ema_invalid`).

# Engine ranking (AAPL/MSFT only)

- Generated (UTC): 2026-09-13T16:24:12.906308Z
- Configs: config/ema9_trend.example.yaml, config/ema9_trend_5m.example.yaml
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## Ranking by P&L % of starting equity

Figures are the engine totals for each book. They are **not** annualized and **not** size-normalized (ORB / engulfing use 10 shares; hammer uses 2% of equity). Yahoo 5m/15m history is capped at ~60 days; the 1h hammer book can span ~2 years.

| Rank | Book | Trades | Win rate | P&L $ | P&L % | Max DD | Avg win | Avg loss | Period | Caveat |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 5m engulfing-with-trend | 49 | 53.06% | $1,520.70 | 1.521% | $434.06 | $122.82 | $-72.73 | 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z | ~86 calendar days |
| 2 | 5m sample-entries | 286 | 32.52% | $1,480.65 | 1.481% | $450.24 | $39.88 | $-11.54 | 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z | ~86 calendar days |
| 3 | 5m combined | 286 | 32.52% | $1,480.65 | 1.481% | $450.24 | $39.88 | $-11.54 | 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z | ~86 calendar days |
| 4 | 15m ema9_trend | 154 | 40.26% | $1,461.69 | 1.462% | $159.00 | $36.85 | $-8.95 | 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z | ~86 calendar days |
| 5 | 15m sample-entries | 214 | 36.92% | $1,229.23 | 1.229% | $326.71 | $36.38 | $-12.18 | 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z | ~86 calendar days |
| 6 | 15m combined | 214 | 36.92% | $1,229.23 | 1.229% | $326.71 | $36.38 | $-12.18 | 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z | ~86 calendar days |
| 7 | 15m ema9_cross_raw | 243 | 35.80% | $1,190.60 | 1.191% | $227.20 | $30.99 | $-9.65 | 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z | ~86 calendar days |
| 8 | 15m engulfing-with-trend | 39 | 43.59% | $697.90 | 0.698% | $471.57 | $123.00 | $-63.32 | 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z | ~86 calendar days |
| 9 | 5m ema9_cross_raw | 485 | 30.93% | $623.08 | 0.623% | $156.27 | $16.15 | $-5.37 | 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z | ~86 calendar days |
| 10 | 5m ema9_trend | 328 | 32.01% | $394.66 | 0.395% | $184.32 | $16.01 | $-5.77 | 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z | ~86 calendar days |

ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.

## Data windows and Yahoo limits

- Yahoo Finance v8 regular-session bars (includePrePost=false, unadjusted OHLC). Retention caps in this downloader: 1m=7d, 5m/15m/30m=60d, 1h=2y. Requesting more than the cap returns HTTP 422. ORB needs 15m to build the opening range and 5m for probe/reversal, so its longest reliable Yahoo window is the 5m/15m 60-day cap.
- 5m and 15m history is the binding limit for ORB and for the 15m sample rules. The 1h hammer book can look back up to 2y on Yahoo, so its calendar window is longer and its P&L% is not time-normalized against the 60-day books.
- Actual closed-bar windows downloaded:
- `AAPL 15Min: 1560 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:45:00+00:00`
- `AAPL 5Min: 4677 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:55:00+00:00`
- `MSFT 15Min: 1560 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:45:00+00:00`
- `MSFT 5Min: 4676 bars 2026-06-17 13:30:00+00:00 → 2026-09-11 19:55:00+00:00`

# Per-book detail

- Generated (UTC): 2026-09-13T16:24:12.906308Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## 15m ema9_trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 154  (by symbol: {'AAPL': 77, 'MSFT': 77})
- Pattern hits in those signals: {'ema_cross': 154}
- Trades: 154  (by symbol: {'AAPL': 77, 'MSFT': 77})
- Wins / losses / scratch: 62 / 92 / 0
- Win rate: 40.26%
- Total P&L: $1,461.69 (1.462% of starting equity)
- Avg win: $36.85
- Avg loss: $-8.95
- Max drawdown: $159.00 (0.16%)
- Ending equity: $101,461.69
- Exit reasons: {'ema_invalid': 154}

## 15m ema9_cross_raw

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 243  (by symbol: {'MSFT': 118, 'AAPL': 125})
- Pattern hits in those signals: {'ema_cross': 243}
- Trades: 243  (by symbol: {'MSFT': 118, 'AAPL': 125})
- Wins / losses / scratch: 87 / 156 / 0
- Win rate: 35.80%
- Total P&L: $1,190.60 (1.191% of starting equity)
- Avg win: $30.99
- Avg loss: $-9.65
- Max drawdown: $227.20 (0.23%)
- Ending equity: $101,190.60
- Exit reasons: {'ema_invalid': 243}

## 15m engulfing-with-trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 94  (by symbol: {'AAPL': 50, 'MSFT': 44})
- Pattern hits in those signals: {'bullish_engulfing': 94}
- Trades: 39  (by symbol: {'MSFT': 19, 'AAPL': 20})
- Wins / losses / scratch: 17 / 22 / 0
- Win rate: 43.59%
- Total P&L: $697.90 (0.698% of starting equity)
- Avg win: $123.00
- Avg loss: $-63.32
- Max drawdown: $471.57 (0.47%)
- Ending equity: $100,697.90
- Exit reasons: {'stop': 22, 'take': 16, 'eod': 1}

## 15m sample-entries

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 491  (by symbol: {'MSFT': 239, 'AAPL': 252})
- Pattern hits in those signals: {'ema_cross': 397, 'bullish_engulfing': 94}
- Trades: 214  (by symbol: {'MSFT': 112, 'AAPL': 102})
- Wins / losses / scratch: 79 / 135 / 0
- Win rate: 36.92%
- Total P&L: $1,229.23 (1.229% of starting equity)
- Avg win: $36.38
- Avg loss: $-12.18
- Max drawdown: $326.71 (0.33%)
- Ending equity: $101,229.23
- Exit reasons: {'ema_invalid': 204, 'stop': 5, 'take': 5}

## 15m combined

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 491  (by symbol: {'MSFT': 239, 'AAPL': 252})
- Pattern hits in those signals: {'ema_cross': 397, 'bullish_engulfing': 94}
- Trades: 214  (by symbol: {'MSFT': 112, 'AAPL': 102})
- Wins / losses / scratch: 79 / 135 / 0
- Win rate: 36.92%
- Total P&L: $1,229.23 (1.229% of starting equity)
- Avg win: $36.38
- Avg loss: $-12.18
- Max drawdown: $326.71 (0.33%)
- Ending equity: $101,229.23
- Exit reasons: {'ema_invalid': 204, 'stop': 5, 'take': 5}

## 5m ema9_trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 328  (by symbol: {'MSFT': 167, 'AAPL': 161})
- Pattern hits in those signals: {'ema_cross': 328}
- Trades: 328  (by symbol: {'MSFT': 167, 'AAPL': 161})
- Wins / losses / scratch: 105 / 223 / 0
- Win rate: 32.01%
- Total P&L: $394.66 (0.395% of starting equity)
- Avg win: $16.01
- Avg loss: $-5.77
- Max drawdown: $184.32 (0.18%)
- Ending equity: $100,394.66
- Exit reasons: {'ema_invalid': 328}

## 5m ema9_cross_raw

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 485  (by symbol: {'AAPL': 242, 'MSFT': 243})
- Pattern hits in those signals: {'ema_cross': 485}
- Trades: 485  (by symbol: {'AAPL': 242, 'MSFT': 243})
- Wins / losses / scratch: 150 / 335 / 0
- Win rate: 30.93%
- Total P&L: $623.08 (0.623% of starting equity)
- Avg win: $16.15
- Avg loss: $-5.37
- Max drawdown: $156.27 (0.16%)
- Ending equity: $100,623.08
- Exit reasons: {'ema_invalid': 485}

## 5m engulfing-with-trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 233  (by symbol: {'MSFT': 117, 'AAPL': 116})
- Pattern hits in those signals: {'bullish_engulfing': 233}
- Trades: 49  (by symbol: {'MSFT': 22, 'AAPL': 27})
- Wins / losses / scratch: 26 / 23 / 0
- Win rate: 53.06%
- Total P&L: $1,520.70 (1.521% of starting equity)
- Avg win: $122.82
- Avg loss: $-72.73
- Max drawdown: $434.06 (0.43%)
- Ending equity: $101,520.70
- Exit reasons: {'stop': 23, 'take': 25, 'eod': 1}

## 5m sample-entries

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 1046  (by symbol: {'AAPL': 519, 'MSFT': 527})
- Pattern hits in those signals: {'ema_cross': 813, 'bullish_engulfing': 233}
- Trades: 286  (by symbol: {'AAPL': 155, 'MSFT': 131})
- Wins / losses / scratch: 93 / 193 / 0
- Win rate: 32.52%
- Total P&L: $1,480.65 (1.481% of starting equity)
- Avg win: $39.88
- Avg loss: $-11.54
- Max drawdown: $450.24 (0.44%)
- Ending equity: $101,480.65
- Exit reasons: {'ema_invalid': 247, 'stop': 20, 'take': 18, 'eod': 1}

## 5m combined

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 1046  (by symbol: {'AAPL': 519, 'MSFT': 527})
- Pattern hits in those signals: {'ema_cross': 813, 'bullish_engulfing': 233}
- Trades: 286  (by symbol: {'AAPL': 155, 'MSFT': 131})
- Wins / losses / scratch: 93 / 193 / 0
- Win rate: 32.52%
- Total P&L: $1,480.65 (1.481% of starting equity)
- Avg win: $39.88
- Avg loss: $-11.54
- Max drawdown: $450.24 (0.44%)
- Ending equity: $101,480.65
- Exit reasons: {'ema_invalid': 247, 'stop': 20, 'take': 18, 'eod': 1}

## Assumptions

- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Mixed exits: ema_invalid holds until a signal-timeframe close < EMA(9) (exit at that close; equals EMA stays valid). fixed_bracket uses stop_loss_pct / take_profit_pct from the signal-bar close. Same-bar stop + EMA-invalid → stop.
- If stop and take (or EMA-invalidation) both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open. EMA-invalidation fills at the invalidating close.
- One open lot per symbol (no pyramiding). A second signal while flat-in-symbol is skipped.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
- ORB and the sample rules use separate engines and are not merged into one shared-position book. Ranking is apples-to-apples across isolated (and sample combined) books, not a single multi-strategy portfolio.
