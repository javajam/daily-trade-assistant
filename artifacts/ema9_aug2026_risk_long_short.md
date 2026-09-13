# EMA9 August 2026 1% risk — long vs short vs combined (AAPL+MSFT)

Companion to `artifacts/ema9_long_short_15m.md` (full-window 10-share A/B/C plus this August section).

- Generated (UTC): 2026-09-13T23:32:48Z
- Tape: Yahoo Finance v8 chart, same 15m download as the full-window book (AAPL/MSFT 1560 bars, 2026-06-17 → 2026-09-11)
- Trade window: **2026-08-01 → 2026-08-31** America/New_York (21 sessions; first RTH day 2026-08-03)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Config: `config/ema9_trend_risk.example.yaml` (shorts enabled)
- Size: 1% equity risk at the 1.0% initial fill stop

| | A. Long-only 1% | B. Short-only 1% | C. Long+short 1% |
| --- | ---: | ---: | ---: |
| Trades | 15 | 20 | 29 |
| **Win rate** | **73.33%** | **45.00%** | **55.17%** |
| **Total P&L** | **$5,489.78** | **$-2,879.01** | **$1,533.99** |
| **Max drawdown** | **$2,743.31** | **$6,304.92** | **$4,117.37** |
| Combined by side | — | — | long 10t 70.00% $3,464.69; short 19t 47.37% $-1,930.70 |
| Opposite skips | — | — | 23 `opposite_signal_in_trade` |

A **reproduced** the prior August 15m 1% lock-+1% long book (15 / 73.33% / $5,489.78). JSON: `artifacts/ema9_aug2026_risk_long_short.json`.
