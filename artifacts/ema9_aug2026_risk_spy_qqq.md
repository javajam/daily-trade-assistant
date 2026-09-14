# ema9_trend August 2026 1% risk — SPY+QQQ long-only vs AAPL+MSFT

- Generated (UTC): 2026-09-13T23:59:25.835551Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: SPY 15m 1560; QQQ 15m 1560; AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry: 15m close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill next open.
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 (15m flatten = 15:45 ET bar close)
- Stop: `stop_mode: lock_plus` — initial fill×0.99; lock at fill×1.01 (live next bar). No take-profit.
- Size: 1% equity risk at `stop_pct` 1.0 — `shares = floor((0.01 * equity) / (0.01 * entry_price))`
- Shorts parked. Configs: `config/ema9_trend_risk_spy_qqq.example.yaml`, `config/ema9_trend_risk_nobe_lock1.example.yaml`
- Full-window 10-share writeup: `artifacts/ema9_spy_qqq_15m.md`
- Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_risk_spy_qqq.example.yaml \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk_spy_qqq.json \
  --report artifacts/ema9_aug2026_risk_spy_qqq.md
```

Engine totals only. Not annualized. One August window on the Yahoo 15m tape.

## Totals

| | SPY+QQQ 1% risk | AAPL+MSFT 1% risk |
| --- | ---: | ---: |
| Signals | 45 (SPY 24, QQQ 21) | 58 (MSFT 32, AAPL 26) |
| Skips | entry_cutoff 18, insufficient_cash 8, already_in_position 7 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 |
| Trades | 12 (SPY 10, QQQ 2) | 15 (MSFT 8, AAPL 7) |
| Wins / losses | 4 / 8 | 11 / 4 |
| **Win rate** | **33.33%** | **73.33%** |
| **Total P&L** | **$-515.42 (−0.515%)** | **$5,489.78 (5.490%)** |
| Avg win | $305.66 | $697.61 |
| Avg loss | $-217.26 | $-546.00 |
| **Max drawdown** | **$1,674.93 (1.66%)** | **$2,743.31 (2.58%)** |
| Ending equity | $99,484.58 | $105,489.78 |
| Exit mix | session_flatten 11, lock_stop 1 | session_flatten 8, lock_stop 6, stop 1 |
| Lock armed | 1 | 6 |
| **Exit P&L** | lock_stop $993.83; session_flatten $-1,509.25 | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 |
| Size | 129–144 shares | AAPL 329–337; MSFT 203–215 |
| Max concurrent | 1 | 1 |

AAPL+MSFT **reproduced** the prior August lock-+1% 1% risk book: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

SPY+QQQ is red. One QQQ lock (2026-08-03) made $993.83; the other eleven exits are session flattens ($-1,509.25). No initial 1% stop fired. A ~$700–770 name at a 1% stop sizes near full equity, so only one name can be open (**8** `insufficient_cash` skips). QQQ: 2 trades, 1 win, **$611.67**. SPY: 10 trades, 3 wins, **$-1,127.10**.

Best day: 2026-08-03 **$993.83**. Worst day: 2026-08-11 **$-409.50**. Peak equity **$100,993.83**, then bleed to $99,484.58.

### Weekly (SPY+QQQ)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W32 (08-03 → 08-07) | 3 | 66.67% | $750.73 | $100,750.73 |
| 2026-W33 (08-10 → 08-14) | 4 | 0.00% | $-927.86 | $99,822.87 |
| 2026-W34 (08-17 → 08-21) | 2 | 50.00% | $-67.87 | $99,755.00 |
| 2026-W35 (08-24 → 08-28) | 3 | 33.33% | $-270.43 | $99,484.58 |
| 2026-W36 (08-31) | 0 | n/a | $0.00 | $99,484.58 |

### Trades (SPY+QQQ)

| # | Symbol | Qty | Entry (ET) | Exit (ET) | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | QQQ | 144 | 2026-08-03 09:45 @ 690.16 | 2026-08-03 11:15 @ 697.06 | lock_stop | $993.83 |
| 2 | SPY | 130 | 2026-08-06 10:15 @ 771.53 | 2026-08-06 16:00 @ 768.53 | session_flatten | $-390.00 |
| 3 | SPY | 130 | 2026-08-07 09:45 @ 771.99 | 2026-08-07 16:00 @ 773.12 | session_flatten | $146.90 |
| 4 | SPY | 130 | 2026-08-10 11:15 @ 773.82 | 2026-08-10 16:00 @ 773.07 | session_flatten | $-97.50 |
| 5 | SPY | 130 | 2026-08-11 11:00 @ 773.63 | 2026-08-11 16:00 @ 770.48 | session_flatten | $-409.50 |
| 6 | SPY | 129 | 2026-08-12 09:45 @ 772.82 | 2026-08-12 16:00 @ 772.52 | session_flatten | $-38.70 |
| 7 | QQQ | 136 | 2026-08-14 09:45 @ 733.86 | 2026-08-14 16:00 @ 731.05 | session_flatten | $-382.16 |
| 8 | SPY | 129 | 2026-08-19 09:45 @ 770.11 | 2026-08-19 16:00 @ 769.09 | session_flatten | $-131.57 |
| 9 | SPY | 130 | 2026-08-21 09:45 @ 765.16 | 2026-08-21 16:00 @ 765.65 | session_flatten | $63.71 |
| 10 | SPY | 130 | 2026-08-25 09:45 @ 766.15 | 2026-08-25 16:00 @ 765.84 | session_flatten | $-40.95 |
| 11 | SPY | 130 | 2026-08-26 11:00 @ 765.87 | 2026-08-26 16:00 @ 766.01 | session_flatten | $18.20 |
| 12 | SPY | 129 | 2026-08-28 10:30 @ 771.30 | 2026-08-28 16:00 @ 769.38 | session_flatten | $-247.68 |

JSON: `artifacts/ema9_aug2026_risk_spy_qqq.json`.
