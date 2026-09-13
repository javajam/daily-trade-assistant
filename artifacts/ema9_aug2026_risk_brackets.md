# ema9_trend August 2026 1% risk: noon price×EMA9 1.5/3.0 vs 1.0/2.0 (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:19:12.232701Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry (both): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70 — the older noon day-trade entry, **not** the EMA9×SMA20 pair-cross
- Session gates (both): `entry_cutoff` 12:00, `flatten_by` 15:55
- No break-even
- A. **stop 1.5% / take 3.0%**, `risk_pct` 1% at **stop_pct 1.5**: `config/ema9_trend_risk_nobe.example.yaml`
- B. **stop 1.0% / take 2.0%**, `risk_pct` 1% at **stop_pct 1.0**: `config/ema9_trend_risk_nobe_12.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe.example.yaml --compare-config config/ema9_trend_risk_nobe_12.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_brackets.json --report artifacts/ema9_aug2026_risk_brackets.md`

**Sizing.** Shares = floor((0.01 × equity) / ((stop_pct/100) × price)). Book B’s 1.0% stop therefore sizes ~1.5× Book A (A 134–219 shares; B 203–332). Max concurrent symbols: 1 on both books.

**Book A reproduced** the prior August no-BE 1% writeup: **15 trades, 73.33%, $3,194.05**, max DD $1,676.30. Signals 58 (AAPL 26, MSFT 32); skips already_in_position 15, entry_cutoff 24, insufficient_cash 4. Exits: **session_flatten 14 ($4,219.87)**, **stop 1 ($-1,025.83)**. Engine note: 4 size-time `insufficient_cash` skips.

**Book B (1.0/2.0, 1% at the 1.0% stop):** **14 trades, 71.43%, $3,820.50**, max DD $2,300.60. Same 58 signals; skips already_in_position 13, entry_cutoff 26, insufficient_cash 3. Exits: **session_flatten 12 ($2,822.11)**, **take 1 ($2,042.80)**, **stop 1 ($-1,044.41)**. Engine note: 3 size-time `insufficient_cash` plus **2 accepted signals skipped at fill** for insufficient cash (AAPL 2026-08-25 16:00 and 2026-08-27 16:00 — the next-morning 8/26 and 8/28 fills Book A kept).

Tighter brackets make more money here (**$626.45**) because each fill is larger and AAPL 2026-08-19 hits the 2% take ($2,042.80, 327 shares) instead of riding to the noon flatten ($1,120.61, 216 shares). That early take also frees MSFT 2026-08-19 11:00 ($53.75), which Book A skipped as `insufficient_cash`. The cost is a larger dollar drawdown and the two missed late-August AAPL flattens (Book A $708.47 + $553.78).

## Side-by-side

| | A. 1.5% / 3.0% (1% at 1.5% stop) | B. 1.0% / 2.0% (1% at 1.0% stop) |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | already_in_position 15, entry_cutoff 24, insufficient_cash 4 | already_in_position 13, entry_cutoff 26, insufficient_cash 3 |
| Trades | 15 (AAPL 7, MSFT 8) | 14 (AAPL 5, MSFT 9) |
| Wins / losses / scratch | 11 / 4 / 0 | 10 / 4 / 0 |
| **Win rate** | **73.33%** | **71.43%** |
| **Total P&L** | **$3,194.05** (3.194%) | **$3,820.50** (3.820%) |
| Avg win | $450.53 | $597.93 |
| Avg loss | $-440.45 | $-539.69 |
| **Max drawdown** | **$1,676.30** (1.63%) | **$2,300.60** (2.19%) |
| Ending equity | $103,194.05 | $103,820.50 |
| Qty range | 134–219 | 203–332 |
| Exit mix | **session_flatten 14**, stop 1 | **session_flatten 12**, take 1, stop 1 |
| **Exit P&L** | session_flatten **$4,219.87**; stop $-1,025.83 | session_flatten **$2,822.11**; take **$2,042.80**; stop $-1,044.41 |

Figures are engine totals, not annualized. One August window on the Yahoo 15m tape. Small samples (15 and 14 trades).

### Book A trades (August 1% at 1.5% stop)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 135 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $234.90 |
| 2 | AAPL | 216 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $447.12 |
| 3 | MSFT | 136 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $896.24 |
| 4 | AAPL | 216 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $250.53 |
| 5 | MSFT | 134 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $103.85 |
| 6 | MSFT | 136 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-146.20 |
| 7 | MSFT | 136 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-416.16 |
| 8 | MSFT | 140 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $76.65 |
| 9 | AAPL | 216 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 16:00 ET @ 316.88 | session_flatten | $1,120.61 |
| 10 | AAPL | 215 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 16:00 ET @ 312.66 | stop | $-1,025.83 |
| 11 | MSFT | 140 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $189.00 |
| 12 | AAPL | 217 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-173.60 |
| 13 | MSFT | 138 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $374.67 |
| 14 | AAPL | 219 | 2026-08-26 09:30 ET @ 310.24 | 2026-08-26 16:00 ET @ 313.48 | session_flatten | $708.47 |
| 15 | AAPL | 217 | 2026-08-28 09:30 ET @ 317.09 | 2026-08-28 16:00 ET @ 319.64 | session_flatten | $553.78 |

### Book B trades (August 1% at 1.0% stop)

| # | Symbol | Qty | Entry | Exit | Reason | P&L |
| ---: | --- | ---: | --- | --- | --- | ---: |
| 1 | MSFT | 203 | 2026-08-04 10:00 ET @ 491.08 | 2026-08-04 16:00 ET @ 492.82 | session_flatten | $353.22 |
| 2 | AAPL | 324 | 2026-08-05 10:45 ET @ 308.85 | 2026-08-05 16:00 ET @ 310.92 | session_flatten | $670.68 |
| 3 | MSFT | 204 | 2026-08-06 09:45 ET @ 493.27 | 2026-08-06 16:00 ET @ 499.86 | session_flatten | $1,344.36 |
| 4 | AAPL | 327 | 2026-08-07 10:15 ET @ 312.14 | 2026-08-07 16:00 ET @ 313.30 | session_flatten | $379.28 |
| 5 | MSFT | 203 | 2026-08-10 09:45 ET @ 505.20 | 2026-08-10 16:00 ET @ 505.97 | session_flatten | $157.32 |
| 6 | MSFT | 206 | 2026-08-13 09:45 ET @ 497.89 | 2026-08-13 16:00 ET @ 496.81 | session_flatten | $-221.45 |
| 7 | MSFT | 205 | 2026-08-14 10:00 ET @ 498.48 | 2026-08-14 16:00 ET @ 495.42 | session_flatten | $-627.30 |
| 8 | MSFT | 212 | 2026-08-18 10:15 ET @ 481.38 | 2026-08-18 16:00 ET @ 481.93 | session_flatten | $116.07 |
| 9 | AAPL | 327 | 2026-08-19 09:45 ET @ 311.69 | 2026-08-19 11:00 ET @ 317.94 | take | $2,042.80 |
| 10 | MSFT | 215 | 2026-08-19 11:00 ET @ 484.23 | 2026-08-19 16:00 ET @ 484.48 | session_flatten | $53.75 |
| 11 | AAPL | 328 | 2026-08-20 11:00 ET @ 317.43 | 2026-08-20 15:30 ET @ 314.25 | stop | $-1,044.41 |
| 12 | MSFT | 214 | 2026-08-21 09:45 ET @ 482.00 | 2026-08-21 16:00 ET @ 483.35 | session_flatten | $288.90 |
| 13 | AAPL | 332 | 2026-08-24 09:45 ET @ 311.15 | 2026-08-24 16:00 ET @ 310.35 | session_flatten | $-265.60 |
| 14 | MSFT | 211 | 2026-08-25 09:45 ET @ 488.79 | 2026-08-25 16:00 ET @ 491.50 | session_flatten | $572.86 |
