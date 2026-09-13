# ema9_trend August 2026 1% risk — EMA9/SMA20 pair-cross RSI A vs B (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:05:24Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- A. **No RSI**: `config/ema9_trend_risk.example.yaml`
- B. **RSI14 &lt; 70**: `config/ema9_trend_risk_rsi.example.yaml`
- Session gates (both): `entry_cutoff` 12:00, `flatten_by` 15:55
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_rsi.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --output artifacts/ema9_aug2026_risk_rsi.json --report artifacts/ema9_aug2026_risk_rsi.md`

**Book A reproduced** the existing August pair-cross 1% writeup: **12 trades, 66.67%, $904.72**, max DD $1,707.30. Signals 32 (AAPL 19, MSFT 13); skips `entry_cutoff` 17, `insufficient_cash` 3. Exits: **ma_cross 8 ($-146.21)**, **session_flatten 4 ($1,050.93)**.

**Book B is the same book.** Every August pair-cross signal already had RSI14 &lt; 70. The five full-window RSI≥70 crosses (see `artifacts/ema9_ma_cross_rsi.md`) are all in July, outside this `--start/--end` window. Signal keys and trade keys match A exactly.

## Side-by-side

| | A. No RSI (August 1% risk) | B. RSI14 &lt; 70 (August 1% risk) |
| --- | ---: | ---: |
| Signals | 32 (AAPL 19, MSFT 13) | 32 (AAPL 19, MSFT 13) |
| Skips | entry_cutoff 17, insufficient_cash 3 | entry_cutoff 17, insufficient_cash 3 |
| Trades | 12 (AAPL 7, MSFT 5) | 12 (AAPL 7, MSFT 5) |
| Wins / losses / scratch | 8 / 4 / 0 | 8 / 4 / 0 |
| **Win rate** | **66.67%** | **66.67%** |
| **Total P&L** | **$904.72** (0.905%) | **$904.72** (0.905%) |
| **Max drawdown** | **$1,707.30** (1.69%) | **$1,707.30** (1.69%) |
| Exit mix | **ma_cross 8**, session_flatten 4 | **ma_cross 8**, session_flatten 4 |
| **Exit P&L** | ma_cross **$-146.21**; session_flatten **$1,050.93** | ma_cross **$-146.21**; session_flatten **$1,050.93** |

Figures are engine totals, not annualized. One August window on the Yahoo 15m tape. RSI14 &lt; 70 does not change this August 1% book.
