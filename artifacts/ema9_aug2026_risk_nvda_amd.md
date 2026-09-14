# ema9_trend August 2026 1% risk — NVDA+AMD long-only vs AAPL+MSFT and SPY+QQQ

- Generated (UTC): 2026-09-14T00:42:22.160560Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC, `includePrePost=false`)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: NVDA 15m 1560; AMD 15m 1560; AAPL 15m 1560; MSFT 15m 1560; SPY 15m 1560; QQQ 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry: 15m close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70. Fill next open.
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 (15m flatten = 15:45 ET bar close)
- Stop: `stop_mode: lock_plus` — initial fill×0.99; lock at fill×1.01 (live next bar). No take-profit.
- Size: 1% equity risk at `stop_pct` 1.0 — `shares = floor((0.01 * equity) / (0.01 * entry_price))`
- Shorts parked. Configs: `config/ema9_trend_risk_nvda_amd.example.yaml`, `config/ema9_trend_risk_nobe_lock1.example.yaml`, `config/ema9_trend_risk_spy_qqq.example.yaml`
- Full-window 10-share writeup: `artifacts/ema9_nvda_amd_15m.md`
- Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_risk_nvda_amd.example.yaml \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --compare-config config/ema9_trend_risk_spy_qqq.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk_nvda_amd.json \
  --report artifacts/ema9_aug2026_risk_nvda_amd.md
```

Engine totals only. Not annualized. One August window on the Yahoo 15m tape.

## Totals

| | NVDA+AMD 1% risk | AAPL+MSFT 1% risk | SPY+QQQ 1% risk |
| --- | ---: | ---: | ---: |
| Signals | 48 (AMD 25, NVDA 23) | 58 (MSFT 32, AAPL 26) | 45 (SPY 24, QQQ 21) |
| Skips | entry_cutoff 24, already_in_position 4, insufficient_cash 2 | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 18, insufficient_cash 8, already_in_position 7 |
| Trades | 16 (NVDA 8, AMD 8) | 15 (MSFT 8, AAPL 7) | 12 (SPY 10, QQQ 2) |
| Wins / losses | 4 / 12 | 11 / 4 | 4 / 8 |
| **Win rate** | **25.00%** | **73.33%** | **33.33%** |
| **Total P&L** | **$-7,292.55 (−7.293%)** | **$5,489.78 (5.490%)** | **$-515.42 (−0.515%)** |
| Avg win | $919.21 | $697.61 | $305.66 |
| Avg loss | $-914.12 | $-546.00 | $-217.26 |
| **Max drawdown** | **$8,311.13 (8.23%)** | **$2,743.31 (2.58%)** | **$1,674.93 (1.66%)** |
| Ending equity | $92,707.45 | $105,489.78 | $99,484.58 |
| Exit mix | stop 11, lock_stop 4, session_flatten 1 | session_flatten 8, lock_stop 6, stop 1 | session_flatten 11, lock_stop 1 |
| Lock armed | 4 | 6 | 1 |
| **Exit P&L** | lock_stop $3,676.85; session_flatten $-240.35; stop $-10,729.05 | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 | lock_stop $993.83; session_flatten $-1,509.25 |
| Size | NVDA 437–494; AMD 197–209 | AAPL 329–337; MSFT 203–215 | 129–144 shares |
| Max concurrent | 1 | 1 | 1 |

AAPL+MSFT **reproduced** the prior August lock-+1% 1% risk book: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

SPY+QQQ **reproduced** the prior August index risk book: **12 trades, 33.33%, $-515.42**, max DD $1,674.93.

NVDA+AMD is red. Four locks made $3,676.85; eleven initial 1% stops cost **$-10,729.05**; one session flatten lost $-240.35. A ~$210 / ~$480 name at a 1% stop sizes near full equity, so only one name can be open (**2** `insufficient_cash` skips). NVDA: 8 trades, 3 wins, **$-1,351.07**. AMD: 8 trades, 1 win, **$-5,941.48**.

Best day: 2026-08-12 **$987.09**. Worst day: 2026-08-25 **$-1,936.96**. Peak equity **$100,973.18** after the first NVDA lock, then bleed to $92,707.45.

### Weekly (NVDA+AMD)

| Week | Trades | Win rate | P&L | Equity EOW |
| --- | ---: | ---: | ---: | ---: |
| 2026-W32 (08-03 → 08-07) | 3 | 66.67% | $836.09 | $100,836.09 |
| 2026-W33 (08-10 → 08-14) | 5 | 20.00% | $-2,251.01 | $98,585.08 |
| 2026-W34 (08-17 → 08-21) | 2 | 50.00% | $-135.24 | $98,449.84 |
| 2026-W35 (08-24 → 08-28) | 5 | 0.00% | $-4,809.69 | $93,640.15 |
| 2026-W36 (08-31) | 1 | 0.00% | $-932.70 | $92,707.45 |

### Trades (NVDA+AMD)

| # | Symbol | Qty | Entry (ET) | Exit (ET) | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | NVDA | 494 | 2026-08-03 10:00 @ 202.23 | 2026-08-03 10:30 @ 204.20 | lock_stop | $973.18 |
| 2 | NVDA | 454 | 2026-08-06 09:45 @ 222.06 | 2026-08-06 10:30 @ 219.84 | stop | $-1,008.15 |
| 3 | NVDA | 449 | 2026-08-07 09:45 @ 222.27 | 2026-08-07 11:45 @ 224.21 | lock_stop | $871.06 |
| 4 | AMD | 209 | 2026-08-10 10:15 @ 480.43 | 2026-08-10 10:30 @ 475.63 | stop | $-1,004.10 |
| 5 | NVDA | 452 | 2026-08-11 09:45 @ 220.56 | 2026-08-11 12:15 @ 218.35 | stop | $-996.93 |
| 6 | NVDA | 446 | 2026-08-12 09:45 @ 221.32 | 2026-08-12 10:15 @ 223.53 | lock_stop | $987.09 |
| 7 | AMD | 202 | 2026-08-13 09:45 @ 493.42 | 2026-08-13 15:15 @ 488.49 | stop | $-996.71 |
| 8 | NVDA | 437 | 2026-08-14 09:45 @ 225.71 | 2026-08-14 16:00 @ 225.16 | session_flatten | $-240.35 |
| 9 | AMD | 208 | 2026-08-20 09:45 @ 471.52 | 2026-08-20 10:00 @ 466.80 | stop | $-980.76 |
| 10 | AMD | 208 | 2026-08-21 11:15 @ 468.21 | 2026-08-21 15:30 @ 472.28 | lock_stop | $845.52 |
| 11 | AMD | 208 | 2026-08-24 09:30 @ 467.98 | 2026-08-24 09:45 @ 463.30 | stop | $-973.39 |
| 12 | NVDA | 458 | 2026-08-25 09:45 @ 212.64 | 2026-08-25 11:15 @ 210.51 | stop | $-973.89 |
| 13 | NVDA | 456 | 2026-08-25 11:30 @ 211.20 | 2026-08-25 14:15 @ 209.09 | stop | $-963.07 |
| 14 | AMD | 197 | 2026-08-26 11:30 @ 484.29 | 2026-08-26 16:00 @ 479.45 | stop | $-954.05 |
| 15 | AMD | 199 | 2026-08-28 10:00 @ 475.02 | 2026-08-28 12:00 @ 470.27 | stop | $-945.29 |
| 16 | AMD | 198 | 2026-08-31 10:00 @ 471.06 | 2026-08-31 11:15 @ 466.35 | stop | $-932.70 |

JSON: `artifacts/ema9_aug2026_risk_nvda_amd.json`.
