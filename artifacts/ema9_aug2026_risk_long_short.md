# EMA9 August 2026 1% risk — long vs simplified short vs combined

- Generated (UTC): 2026-09-13T23:44:36.377260Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC). August run used the 15m cache written by the full-window download (`data/ohlcv/AAPL_15Min.json`, `data/ohlcv/MSFT_15Min.json`).
- Downloaded tape: **2026-06-17 → 2026-09-11** (1560 closed 15m bars each).
- Trade window: **2026-08-01 → 2026-08-31** (21 NY sessions; 2026-08-03 first RTH). Prior bars kept for SMA/EMA warmup.
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Universe: **AAPL+MSFT**
- Session gates: `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York
- Config: `config/ema9_trend_risk.example.yaml` (1% equity risk at the 1.0% initial fill stop; `lock_plus`)

**Long (A):** unchanged (price-cross above EMA9 + SMA20 + RSI14 < 70; lock-+1%).

**Short (B, new):** bearish price-cross below EMA9 + close < SMA20. **No RSI.** Cover on EMA(9) over SMA(20) at the next bar open. `lock_plus` mirror and session flatten still apply.

Replay:

```
python -m dta_bot backtest \
  --config config/ema9_trend_risk.example.yaml \
  --source yahoo --start 2026-08-01 --end 2026-08-31 \
  --output artifacts/ema9_aug2026_risk_long_short.json \
  --report artifacts/ema9_aug2026_risk_long_short.md
```

Full-window 10-share A/B/C: `artifacts/ema9_long_short_15m.md`.

| | A. Long-only 1% | B. New short-only 1% | C. Long+new short 1% |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 47 (AAPL 25, MSFT 22) | 105 (AAPL 51, MSFT 54) |
| Skips | already_in_position 11, entry_cutoff 28, insufficient_cash 3 | already_in_position 8, entry_cutoff 18 | already_in_position 13, entry_cutoff 44, **opposite_signal_in_trade 15**, insufficient_cash 1 |
| Trades | 15 (MSFT 8, AAPL 7) | 21 (AAPL 9, MSFT 12) | 30 (MSFT 18, AAPL 12) |
| Wins / losses | 11 / 4 | 8 / 13 | 15 / 15 |
| **Win rate** | **73.33%** | **38.10%** | **50.00%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$-3,505.00 (−3.505%)** | **$887.15 (0.887%)** |
| Avg win | $697.61 | $553.24 | $660.94 |
| Avg loss | $-546.00 | $-610.07 | $-601.80 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$6,309.57 (6.20%)** | **$4,002.83 (3.85%)** |
| Ending equity | $105,489.78 | $96,495.00 | $100,887.15 |
| Exit mix | lock_stop 6, session_flatten 8, stop 1 | ma_cross 11, stop 5, lock_stop 4, session_flatten 1 | ma_cross 11, lock_stop 9, stop 5, session_flatten 5 |
| Lock armed | 6 | 4 | 9 |
| **Exit P&L** | lock_stop $5,623.20; session_flatten $917.28; stop $-1,050.69 | lock_stop $3,742.47; session_flatten $371.91; ma_cross $-2,667.64; stop $-4,951.74 | lock_stop $8,546.55; session_flatten $198.83; ma_cross $-2,756.37; stop $-5,101.86 |

**A reproduced** the prior August 15m 1% lock-+1% long book exactly: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31.

**B vs prior August short 1%** (RSI>30, no MA-cross cover): **20 trades, 45.00%, $-2,879.01**, max DD $6,304.92 (46 signals). New short: **21 trades, 38.10%, $-3,505.00**, max DD $6,309.57 (47 signals). **11 `ma_cross` covers lost $2,667.64.**

**C vs prior combined 1%:** prior was **29 trades, 55.17%, $1,533.99**, max DD $4,117.37 (23 opposite skips). New combined: **30 trades, 50.00%, $887.15**, max DD $4,002.83 (15 opposite skips). Isolated A+B = 36 trades / $1,984.78; combined is not that sum.

### Combined by side

| Side | Trades | Wins / losses | Win rate | P&L |
| --- | ---: | ---: | ---: | ---: |
| Long | 10 | 7 / 3 | 70.00% | $3,462.55 |
| Short | 20 | 8 / 12 | 40.00% | $-2,575.40 |

Max DD by side is the isolated 1% book: long **$2,743.31**, short **$6,309.57**. Combined max DD is **$4,002.83**.
