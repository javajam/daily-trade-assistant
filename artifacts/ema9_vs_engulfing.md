# 9 EMA trend vs engulfing-with-trend (same 15m tape)

- Generated (UTC): 2026-09-13T15:57:05.789259Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560 (same closed-bar window as the prior engulfing book)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares; stop 1.5%; take 3.0%; cooldown 60 minutes
- Config: `config/ema9_trend.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --source yahoo --output artifacts/ema9_vs_engulfing.json --report artifacts/ema9_vs_engulfing.md`

Replaying **engulfing-with-trend** on this tape reproduced the prior book exactly: **39 trades, 43.59%, $697.90**, max DD $471.57, avg win $123.00, avg loss $-63.32, exits stop 22 / take 16 / eod 1.

**ema9_trend** (bullish EMA9 cross + the same SMA20 / RSI14 filter) **beats** that control on this window: more P&L, higher win rate, slightly more trades, and a smaller max drawdown. Avg win/loss are nearly the same as engulfing (same 1.5/3.0 brackets); the extra money is mostly extra takes (21 vs 16) at a similar per-win size.

The **ema9_cross_raw** ablation (same cross and risk, no SMA/RSI filter) still beats engulfing but loses to the filtered book: more signals and trades, similar win rate, worse average loss, smaller P&L. The trend filter is doing useful work.

`sample-entries` / `combined` are **not** the comparison. Those books put all three entry rules on one lot-per-symbol book, so they mostly follow the first raw-cross fill. Use the isolated rows below.

## Side-by-side (isolated books)

| | ema9_trend | ema9_cross_raw (no filter) | engulfing-with-trend (control) |
| --- | ---: | ---: | ---: |
| Trigger | bullish close × EMA(9) | same, no SMA/RSI | bullish engulfing |
| Trend filter | close > SMA20 and RSI14 < 70 | none | close > SMA20 and RSI14 < 70 |
| Signals | 154 (AAPL 77, MSFT 77) | 243 (AAPL 125, MSFT 118) | 94 (AAPL 50, MSFT 44) |
| Trades | 44 (AAPL 21, MSFT 23) | 53 (AAPL 28, MSFT 25) | 39 (AAPL 20, MSFT 19) |
| Wins / losses / scratch | 22 / 21 / 1 | 26 / 27 / 0 | 17 / 22 / 0 |
| **Win rate** | **50.00%** | **49.06%** | **43.59%** |
| **Total P&L** | **$1,404.89** (1.405%) | **$1,236.03** (1.236%) | **$697.90** (0.698%) |
| Avg win | $123.61 | $122.49 | $123.00 |
| Avg loss | $-62.59 | $-72.17 | $-63.32 |
| **Max drawdown** | **$407.70** (0.40%) | **$443.30** (0.44%) | **$471.57** (0.47%) |
| Ending equity | $101,404.89 | $101,236.03 | $100,697.90 |
| Exit mix | stop 22, take 21, eod 1 | stop 27, take 25, eod 1 | stop 22, take 16, eod 1 |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window; do not treat this as a robustness study.

# Per-book detail

- Generated (UTC): 2026-09-13T15:57:05.789259Z
- Starting equity: $100,000.00
- Commission / slippage: commission=$0.00/fill, slippage=0.0%
- Data: Yahoo Finance v8 chart (unadjusted regular-session OHLC)

## ema9_trend

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
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

## ema9_cross_raw

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
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

## engulfing-with-trend

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

## sample-entries

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 491  (by symbol: {'MSFT': 239, 'AAPL': 252})
- Pattern hits in those signals: {'ema_cross': 397, 'bullish_engulfing': 94}
- Trades: 53  (by symbol: {'MSFT': 25, 'AAPL': 28})
- Wins / losses / scratch: 26 / 27 / 0
- Win rate: 49.06%
- Total P&L: $1,238.07 (1.238% of starting equity)
- Avg win: $122.49
- Avg loss: $-72.10
- Max drawdown: $443.30 (0.44%)
- Ending equity: $101,238.07
- Exit reasons: {'stop': 27, 'take': 25, 'eod': 1}

## combined

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Data source: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Signals: 491  (by symbol: {'MSFT': 239, 'AAPL': 252})
- Pattern hits in those signals: {'ema_cross': 397, 'bullish_engulfing': 94}
- Trades: 53  (by symbol: {'MSFT': 25, 'AAPL': 28})
- Wins / losses / scratch: 26 / 27 / 0
- Win rate: 49.06%
- Total P&L: $1,238.07 (1.238% of starting equity)
- Avg win: $122.49
- Avg loss: $-72.10
- Max drawdown: $443.30 (0.44%)
- Ending equity: $101,238.07
- Exit reasons: {'stop': 27, 'take': 25, 'eod': 1}

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
