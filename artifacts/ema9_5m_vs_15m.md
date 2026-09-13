# 9 EMA trend: 5-minute vs 15-minute

- Generated (UTC): 2026-09-13T16:08:43.058130Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11 (15m last bar 19:45Z; 5m last bar 19:55Z)
- Bars: AAPL/MSFT 15m 1560/1560; AAPL/MSFT 5m 4677/4676
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares; stop 1.5%; take 3.0%; cooldown 60 wall-clock minutes
- Configs: `config/ema9_trend.example.yaml` (15m) and `config/ema9_trend_5m.example.yaml` (or `--timeframe 5m`)
- Replay 15m: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --source yahoo --output artifacts/ema9_vs_engulfing.json --report artifacts/ema9_vs_engulfing.md`
- Replay 5m: `python -m dta_bot backtest --config config/ema9_trend_5m.example.yaml --source yahoo --output artifacts/ema9_5m.json --report artifacts/ema9_5m.md`

Replaying **15m ema9_trend** on this tape reproduced the prior book exactly: **44 trades, 50.00%, $1,404.89**, max DD $407.70, avg win $123.61, avg loss $-62.59, exits stop 22 / take 21 / eod 1.

All 5m indicators (EMA9 cross, SMA20, RSI14) are computed on **5-minute** closes. Cooldown is still 60 minutes of clock time, not 60 five-minute bars.

Yahoo's downloader requests `range=60d` for 5m/15m (asking for more returns HTTP 422). On this run that request still returned the same calendar start as the prior 15m book (**2026-06-17**). Treat the documented ~60-day cap as the reliability limit; this window is what the v8 chart actually served.

**5m ema9_trend** took more trades than 15m (56 vs 44) from more signals (328 vs 154), with a slightly lower win rate (48.21% vs 50.00%), slightly less P&L ($1,305.23 vs $1,404.89), and a slightly larger max drawdown ($422.43 vs $407.70). Avg win/loss stay near the 1.5/3.0 bracket sizes; 5m booked more takes (26 vs 21) and more stops (28 vs 22).

On the **5m** tape, **engulfing-with-trend** beat filtered ema9: 49 trades, 53.06%, $1,520.70, max DD $434.06. That is the opposite ranking from 15m, where engulfing was 39 trades, 43.59%, $697.90. One window; do not treat this as a robustness study.

`sample-entries` / `combined` are **not** the comparison. Those books put multiple entry rules on one lot-per-symbol book. Isolated rows below are the ones to read.

## Side-by-side (requested books)

| | 15m ema9_trend | 5m ema9_trend | 5m engulfing-with-trend |
| --- | ---: | ---: | ---: |
| Trades | 44 | 56 | 49 |
| Win rate | 50.00% | 48.21% | 53.06% |
| P&L | $1,404.89 | $1,305.23 | $1,520.70 |
| Max DD | $407.70 | $422.43 | $434.06 |
| Avg win | $123.61 | $121.25 | $122.82 |
| Avg loss | $-62.59 | $-67.88 | $-72.73 |
| Takes vs stops | take 21, stop 22, eod 1 | take 26, stop 28, eod 2 | take 25, stop 23, eod 1 |

## Extra context (not the headline comparison)

| | 15m engulfing-with-trend | 15m ema9_cross_raw | 5m ema9_cross_raw |
| --- | ---: | ---: | ---: |
| Trades | 39 | 53 | 63 |
| Win rate | 43.59% | 49.06% | 46.03% |
| P&L | $697.90 | $1,236.03 | $996.80 |
| Max DD | $471.57 | $443.30 | $447.46 |
| Avg win | $123.00 | $122.49 | $110.52 |
| Avg loss | $-63.32 | $-72.17 | $-64.95 |
| Takes vs stops | take 16, stop 22, eod 1 | take 25, stop 27, eod 1 | take 28, stop 33, eod 2 |

Figures are engine totals, not annualized. Same ~86-day Yahoo window on both tapes; 5m/15m history is still documented as a ~60-day cap in the downloader.

# Per-book detail

## 15m ema9_trend (reproduced)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Signals: 154  (by symbol: {'AAPL': 77, 'MSFT': 77})
- Pattern hits in those signals: {'ema_cross': 154}
- Trades: 44  (by symbol: {'MSFT': 23, 'AAPL': 21})
- Wins / losses / scratch: 22 / 21 / 1
- Win rate: 50.00%
- Total P&L: $1,404.89 (1.405% of starting equity)
- Avg win: $123.61
- Avg loss: $-62.59
- Max drawdown: $407.70 (0.40%)
- Ending equity: $101,404.89
- Exit reasons: {'stop': 22, 'take': 21, 'eod': 1}

## 5m ema9_trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Signals: 328  (by symbol: {'MSFT': 167, 'AAPL': 161})
- Pattern hits in those signals: {'ema_cross': 328}
- Trades: 56  (by symbol: {'MSFT': 25, 'AAPL': 31})
- Wins / losses / scratch: 27 / 29 / 0
- Win rate: 48.21%
- Total P&L: $1,305.23 (1.305% of starting equity)
- Avg win: $121.25
- Avg loss: $-67.88
- Max drawdown: $422.43 (0.42%)
- Ending equity: $101,305.23
- Exit reasons: {'stop': 28, 'take': 26, 'eod': 2}

## 5m engulfing-with-trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
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

## 15m engulfing-with-trend (control)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
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

## 15m ema9_cross_raw

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Signals: 243  (by symbol: {'MSFT': 118, 'AAPL': 125})
- Pattern hits in those signals: {'ema_cross': 243}
- Trades: 53  (by symbol: {'MSFT': 25, 'AAPL': 28})
- Wins / losses / scratch: 26 / 27 / 0
- Win rate: 49.06%
- Total P&L: $1,236.03 (1.236% of starting equity)
- Avg win: $122.49
- Avg loss: $-72.17
- Max drawdown: $443.30 (0.44%)
- Ending equity: $101,236.03
- Exit reasons: {'stop': 27, 'take': 25, 'eod': 1}

## 5m ema9_cross_raw

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Signals: 485  (by symbol: {'AAPL': 242, 'MSFT': 243})
- Pattern hits in those signals: {'ema_cross': 485}
- Trades: 63  (by symbol: {'AAPL': 32, 'MSFT': 31})
- Wins / losses / scratch: 29 / 34 / 0
- Win rate: 46.03%
- Total P&L: $996.80 (0.997% of starting equity)
- Avg win: $110.52
- Avg loss: $-64.95
- Max drawdown: $447.46 (0.45%)
- Ending equity: $100,996.80
- Exit reasons: {'stop': 33, 'take': 28, 'eod': 2}

## Assumptions

- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries and close-signals fill at the next bar open of the finest rule timeframe.
- Stop/take are computed from the signal-bar close (same as live bracket_prices).
- If stop and take both trade in the fill bar, the stop is assumed to fill first.
- A gap through stop/take fills at that bar's open.
- One open lot per symbol (no pyramiding). A second signal while flat-in-symbol is skipped.
- Open lots still on the last bar are flattened at the last close (exit reason eod).
- Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
- Cooldown is wall-clock minutes (60) on both tapes.
- 5m and 15m books are separate; they do not share positions or an equity curve.
