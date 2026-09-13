# ema9_trend August 2026 1% risk — EMA9/SMA20 pair-cross (AAPL/MSFT)

- Generated (UTC): 2026-09-13T21:52:07.786905Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Config: `config/ema9_trend_risk.example.yaml` (15m EMA(9) cross over SMA(20); `exit: ma_cross` next-bar-open flatten on cross-under; stop 1.5%; no take-profit; no break-even; risk 1% of equity at the 1.5% stop)
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --output artifacts/ema9_aug2026_risk.json --report artifacts/ema9_aug2026_risk.md`

**Sizing still works.** `risk_pct` sized every accepted fill (131–219 shares). Max concurrent symbols: 1. Three signals skipped as `insufficient_cash` (a second name would have needed ~2/3 of equity at the 1.5% stop). No `size_zero`.

August pair-cross 1% book: **12 trades, 66.67%, $904.72**, max DD $1,707.30. Exits: **ma_cross 8 ($-146.21)**, **session_flatten 4 ($1,050.93)**. Skips: entry_cutoff 17, insufficient_cash 3. Signals: 32 (AAPL 19, MSFT 13).

Prior August 1% writeups on the **old entry** (price crosses EMA9 + SMA20 + RSI, 1.5/3.0) are not re-run here because that risk YAML was replaced. Those earlier writeups (same Yahoo 15m tape, 12:00 / 15:55) were: **with one-bar BE 16 trades, 31.25%, $3,188.15**, max DD $1,058.87; **without BE 15 trades, 73.33%, $3,194.05**, max DD $1,676.30. The new pair-cross August book is a different entry/exit, not a BE toggle on the old signals.

## Totals

| | August 1% risk, EMA9/SMA20 pair-cross |
| --- | ---: |
| Signals | 32 (AAPL 19, MSFT 13) |
| Skips | entry_cutoff 17, insufficient_cash 3 |
| Trades | 12 (AAPL 7, MSFT 5) |
| Wins / losses / scratch | 8 / 4 / 0 |
| **Win rate** | **66.67%** |
| **Total P&L** | **$904.72** (0.905%) |
| Avg win | $305.33 |
| Avg loss | $-384.48 |
| **Max drawdown** | **$1,707.30** (1.69%) |
| Ending equity | $100,904.72 |
| Exit mix | **ma_cross 8**, session_flatten 4 |
| **Exit P&L** | ma_cross **$-146.21**; session_flatten **$1,050.93** |

Figures are engine totals, not annualized. One August window on the Yahoo 15m tape.

### Trades

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 135 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $234.90 |
| 2 | AAPL | 214 | 2026-08-05 11:00 ET @ 311.34 | 2026-08-05 11:45 ET @ 308.27 | ma_cross | $-658.03 |
| 3 | MSFT | 131 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 14:00 ET @ 505.62 | ma_cross | $56.33 |
| 4 | AAPL | 219 | 2026-08-13 09:30 ET @ 304.26 | 2026-08-13 13:15 ET @ 303.08 | ma_cross | $-257.98 |
| 5 | MSFT | 137 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $75.01 |
| 6 | AAPL | 212 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 14:00 ET @ 315.19 | ma_cross | $742.00 |
| 7 | AAPL | 209 | 2026-08-20 09:45 ET @ 318.48 | 2026-08-20 13:45 ET @ 316.60 | ma_cross | $-392.92 |
| 8 | MSFT | 136 | 2026-08-24 10:00 ET @ 486.91 | 2026-08-24 14:45 ET @ 487.71 | ma_cross | $108.80 |
| 9 | MSFT | 136 | 2026-08-25 11:15 ET @ 489.34 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $293.76 |
| 10 | AAPL | 214 | 2026-08-26 09:45 ET @ 311.39 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $447.26 |
| 11 | AAPL | 213 | 2026-08-27 11:30 ET @ 314.65 | 2026-08-27 15:30 ET @ 313.58 | ma_cross | $-228.98 |
| 12 | AAPL | 210 | 2026-08-28 09:45 ET @ 317.28 | 2026-08-28 14:45 ET @ 319.59 | ma_cross | $484.57 |
