# ema9_trend August 2026 1% risk: 1.0/2.0 percent vs SMA20 stop (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:33:03Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Trade window: 2026-08-01 → 2026-08-31 America/New_York (warmup bars from 2026-06-17)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Entry (all): 15m close crosses **above EMA(9)** AND close > SMA(20) AND RSI(14) < 70 — the older noon day-trade entry, **not** the EMA9×SMA20 pair-cross
- Session gates (all): `entry_cutoff` 12:00, `flatten_by` 15:55
- No break-even
- A. **stop 1.0% / take 2.0%**, `risk_pct` 1% at **stop_pct 1.0** (`stop_mode: percent`): `config/ema9_trend_risk_nobe_12.example.yaml`
- B. **SMA20 stop + 2% take**, `risk_pct` 1% with **R = signal-close − SMA20** (`stop_mode: sma20`): `config/ema9_trend_risk_sma20.example.yaml`
- C. **SMA20 stop, no % take**, same R: `config/ema9_trend_risk_sma20_notake.example.yaml`
- Replay: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_12.example.yaml --compare-config config/ema9_trend_risk_sma20.example.yaml --compare-config config/ema9_trend_risk_sma20_notake.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_sma20.json --report artifacts/ema9_aug2026_risk_sma20.md`

**Sizing.** Percent book: shares = floor((0.01 × equity) / ((stop_pct/100) × price)). SMA20 books: shares = floor((0.01 × equity) / R) where **R = signal-bar close − SMA20** (same reference price the percent book uses for `stop_pct`). Fill is the next-bar open; if that open is at/below SMA20 the lot is skipped.

**Book A reproduced** the prior August 1.0/2.0 1% writeup: **14 trades, 71.43%, $3,820.50**, max DD $2,300.60. Signals 58 (AAPL 26, MSFT 32); skips already_in_position 13, entry_cutoff 26, insufficient_cash 3. Exits: **session_flatten 12 ($2,822.11)**, **take 1 ($2,042.80)**, **stop 1 ($-1,044.41)**. Qty 203–332. Engine note: 3 size-time `insufficient_cash` plus 2 accepted signals skipped at fill for insufficient cash.

**Books B and C did not fill.** Same 58 August signals; **0 trades**, **0 `sma20_above_entry`**, **0 `sma20_unavailable`**. Skips: **entry_cutoff 37**, **insufficient_cash 21** (AAPL 9, MSFT 12). Every in-window signal that cleared the noon cutoff failed the cash check.

That is the SMA20 R, not a tape miss. Entry already requires close > SMA20, so R is the residual gap — often well under 1% of price (on the full-window 10-share SMA20 book the 28 stop-outs averaged **0.33% / $1.27**). `floor(1000 / R)` then asks for hundreds-to-thousands of shares (AAPL ~$310 × 500–2000+ shares is $155k–$620k+). $100k cash cannot cover that notional, so the engine skips. The 1.0% percent book sizes ~203–332 shares because its R is forced to 1% of price.

No percent fallback is applied. A later book could cap shares or require a minimum R; v1 does not.

## Side-by-side

| | A. 1.0% / 2.0% (1% at 1.0% stop) | B. SMA20 / 2.0% (1% at SMA20 R) | C. SMA20 stop only (1% at SMA20 R) |
| --- | ---: | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | already_in_position 13, entry_cutoff 26, insufficient_cash 3 | entry_cutoff 37, insufficient_cash 21 | entry_cutoff 37, insufficient_cash 21 |
| Trades | 14 (AAPL 5, MSFT 9) | **0** | **0** |
| Wins / losses / scratch | 10 / 4 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| **Win rate** | **71.43%** | n/a | n/a |
| **Total P&L** | **$3,820.50** (3.820%) | **$0.00** | **$0.00** |
| **Max drawdown** | **$2,300.60** (2.19%) | $0.00 | $0.00 |
| Qty range | 203–332 | — | — |
| Exit mix | **session_flatten 12**, take 1, stop 1 | — | — |

Figures are engine totals, not annualized. One August window on the Yahoo 15m tape. Book A is a small sample (14 trades). B/C have no closed trades.

### Book A trades (August 1% at 1.0% stop)

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
