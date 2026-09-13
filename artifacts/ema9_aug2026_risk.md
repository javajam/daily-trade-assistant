# ema9_trend August 2026 1% risk book with one-bar break-even (AAPL/MSFT)

- Generated (UTC): 2026-09-13T20:20:12.994835Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Config: `config/ema9_trend_risk.example.yaml` (15m EMA9 + SMA20 + RSI14 < 70, stop 1.5% / take 3.0%, risk 1% of equity at the 1.5% stop, `breakeven_after_bars: 1`, `breakeven_requires_valid: true`, `breakeven_valid: above_ema`)
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --output artifacts/ema9_aug2026_risk.json --report artifacts/ema9_aug2026_risk.md`

**Break-even rule:** after the fill, wait for one complete 15m bar after the entry bar. At that close, if still valid (`close > EMA(9)`), move the stop to entry and leave it there. If not valid, keep the 1.5% stop.

August with BE: **16 trades, 31.25%, $3,188.15**, max DD $1,058.87. **15 of 16 trades armed break-even; 11 exited as `breakeven_stop`**. Remaining exits: session_flatten 5. Skips: entry_cutoff 32, already_in_position 6, insufficient_cash 4. Max concurrent symbols: 1.

Prior 12:00 August 1% book **without** BE (same tape, previous writeup): **15 trades, 73.33%, $3,194.05**, max DD $1,676.30, 14 of 15 `session_flatten`. BE is nearly P&L-neutral on this month ($-5.90 vs that book) and cuts max DD by $617.43. Win rate drops because 8 scratches are not wins. One extra fill because a BE exit freed the symbol.

## Totals

| | August 1% risk + BE |
| --- | ---: |
| Signals | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 32, already_in_position 6, insufficient_cash 4 |
| Trades | 16 (AAPL 8, MSFT 8) |
| Wins / losses / scratch | 5 / 3 / 8 |
| **Win rate** | **31.25%** |
| **Total P&L** | **$3,188.15** (3.188%) |
| Avg win | $666.85 |
| Avg loss | $-48.70 |
| **Max drawdown** | **$1,058.87** (1.04%) |
| Ending equity | $103,188.15 |
| Exit mix | **breakeven_stop 11**, session_flatten 5 |
| **BE armed** | **15** |
| **BE stop hit** | **11** |

Figures are engine totals, not annualized. One August window on the Yahoo 15m tape.

### Trades

| # | Symbol | Qty | Entry | Exit | Reason | P&L | BE armed |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | MSFT | 135 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $234.90 | Y |
| 2 | AAPL | 216 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 11:30 ET @ 308.85 | breakeven_stop | $0.00 | Y |
| 3 | MSFT | 135 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $889.65 | Y |
| 4 | AAPL | 215 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 12:00 ET @ 312.14 | breakeven_stop | $0.00 | Y |
| 5 | MSFT | 133 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 14:15 ET @ 505.20 | breakeven_stop | $0.00 | Y |
| 6 | MSFT | 135 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 10:45 ET @ 497.89 | breakeven_stop | $0.00 | Y |
| 7 | MSFT | 135 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 11:00 ET @ 498.48 | breakeven_stop | $0.00 | Y |
| 8 | AAPL | 220 | 2026-08-14 11:00 ET @ 305.16 | 2026-08-14 12:30 ET @ 305.16 | breakeven_stop | $0.00 | Y |
| 9 | MSFT | 140 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 11:00 ET @ 481.14 | breakeven_stop | $-33.95 | Y |
| 10 | AAPL | 216 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $1,120.61 | Y |
| 11 | AAPL | 214 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 11:45 ET @ 317.23 | breakeven_stop | $-42.82 | Y |
| 12 | MSFT | 141 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 10:45 ET @ 482.00 | breakeven_stop | $0.00 | Y |
| 13 | AAPL | 218 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 14:45 ET @ 311.15 | breakeven_stop | $0.00 | Y |
| 14 | MSFT | 139 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $377.38 |  |
| 15 | AAPL | 220 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $711.70 | Y |
| 16 | AAPL | 218 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 10:15 ET @ 316.77 | breakeven_stop | $-69.33 | Y |

### Monthly

- Month: 2026-08
- Session days: 21
- Trades: 16  (wins 5 / losses 3)
- Win rate (excluding scratches): 62.50%
- Total P&L: $3,188.15 (3.19% of starting equity)
- Ending equity: $103,188.15
- Best day (realized): 2026-08-19 $1,120.61 (1 trade)
- Worst day (realized): 2026-08-28 $-69.33 (1 trade)

### Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 4 | 100.00% | $1,124.55 | 1.12% | $101,124.55 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 4 | n/a | $0.00 | 0.00% | $101,124.55 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 4 | 33.33% | $1,043.84 | 1.04% | $102,168.39 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 4 | 66.67% | $1,019.76 | 1.02% | $103,188.15 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 0 | n/a | $0.00 | 0.00% | $103,188.15 |
