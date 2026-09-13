# 9 EMA trend: EMA-invalidation exit, 5-minute vs 15-minute

- Generated (UTC): 2026-09-13T16:22:57.376362Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11 (15m last bar 19:45Z; 5m last bar 19:55Z)
- Bars: AAPL/MSFT/SOXL 15m 1560/1560/1560; AAPL/MSFT/SOXL 5m 4677/4676/4680
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Sizing: 10 shares; **exit `ema_invalid`** (long stays in until a signal-timeframe bar **closes < EMA(9)**; flatten at that close; close == EMA9 stays valid). No 1.5/3.0 bracket. Catastrophic `stop_loss_pct` off. Cooldown 60 wall-clock minutes.
- Configs: `config/ema9_trend.example.yaml` (15m) and `config/ema9_trend_5m.example.yaml` (or `--timeframe 5m`)
- Replay 15m+5m: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_5m.example.yaml --source yahoo --breakout SOXL --output artifacts/ema9_ema_invalid_5m_vs_15m.json --report artifacts/ema9_ema_invalid_5m_vs_15m.md`
- Isolated AAPL/MSFT (same exit, prior universe): `--symbols AAPL,MSFT` → `artifacts/ema9_ema_invalid_aapl_msft.json`

Entry is unchanged: bullish close-across-EMA(9) + close > SMA20 + RSI14 < 70. On this tape that produced the **same signal counts** as the prior fixed-bracket books for AAPL/MSFT (15m 154, 5m 328) plus new SOXL signals (15m 86, 5m 170). With EMA-invalidation, every one of those signals filled (signals = trades): a new bullish cross cannot print while still long unless price tags EMA without closing through it, and that did not skip any fill here.

All 5m indicators (EMA9 cross, SMA20, RSI14, and the exit EMA) are computed on **5-minute** closes. Cooldown is still 60 minutes of clock time, not 60 five-minute bars.

Yahoo's downloader requests `range=60d` for 5m/15m (asking for more returns HTTP 422). On this run that request still returned the same calendar start as the prior books (**2026-06-17**). Treat the documented ~60-day cap as the reliability limit; this window is what the v8 chart actually served.

**15m ema9_trend** on the full AAPL/MSFT/SOXL set finished **ahead of 5m**: 240 trades, 36.25%, **$626.64**, max DD $850.25 vs 5m 498 trades, 30.72%, **$-312.80**, max DD $722.18. Both books exited **only** on `ema_invalid` (no stops, no takes, no eod leftover). 5m took about 2× the trades with smaller average wins and losses (shorter holds on a finer clock).

**SOXL is the drag on both clocks.** Isolated SOXL (own equity curve): 15m 86 trades, 29.07%, **$-835.05**, max DD $952.43; 5m 170 trades, 28.24%, **$-707.46**, max DD $911.33. Closed-trade P&L on the three-name book equals AAPL+MSFT trade P&L plus the isolated SOXL P&L (15m $1,461.69 + $-835.05 = $626.64; 5m $394.66 + $-707.46 = $-312.80). Combined max DD is **not** the sum of the isolated DDs because the lots share one equity curve.

On the **prior AAPL/MSFT universe** (no SOXL), EMA-invalid 15m was 154 trades, 40.26%, $1,461.69, max DD $159.00 — slightly more P&L than the old 1.5/3.0 book ($1,404.89) with far more trades and a smaller dollar drawdown, but much smaller average wins. EMA-invalid 5m AAPL/MSFT was 328 trades, 32.01%, $394.66, max DD $184.32 — **worse** P&L than the old 5m brackets ($1,305.23). Adding SOXL then cuts 15m P&L and flips 5m red.

Replaying **`exit: fixed_bracket`** with 1.5/3.0 on AAPL/MSFT **reproduced the prior books exactly**: 15m 44 trades, 50.00%, $1,404.89, max DD $407.70, take 21 / stop 22 / eod 1; 5m 56 trades, 48.21%, $1,305.23, max DD $422.43, take 26 / stop 28 / eod 2.

`sample-entries` / `combined` are **not** the comparison. Those books put multiple entry rules on one lot-per-symbol book. Isolated rows below are the ones to read. One window; do not treat this as a robustness study. 10-share sizing on SOXL (a 3× semiconductor ETF) also makes each tick worth more dollars than AAPL/MSFT.

## Side-by-side (requested books)

| | 15m ema9_trend AAPL/MSFT/SOXL | 5m ema9_trend AAPL/MSFT/SOXL | 15m ema9_trend SOXL | 5m ema9_trend SOXL |
| --- | ---: | ---: | ---: | ---: |
| Trades | 240 | 498 | 86 | 170 |
| Win rate | 36.25% | 30.72% | 29.07% | 28.24% |
| P&L | $626.64 | $-312.80 | $-835.05 | $-707.46 |
| Max DD | $850.25 | $722.18 | $952.43 | $911.33 |
| Avg win | $44.65 | $21.47 | $63.98 | $33.41 |
| Avg loss | $-21.43 | $-10.43 | $-40.57 | $-18.94 |
| Exits | ema_invalid 240 | ema_invalid 498 | ema_invalid 86 | ema_invalid 170 |

## Extra context (not the headline comparison)

| | 15m AAPL/MSFT only | 5m AAPL/MSFT only | 15m fixed-bracket AAPL/MSFT (reproduced) | 5m fixed-bracket AAPL/MSFT (reproduced) |
| --- | ---: | ---: | ---: | ---: |
| Trades | 154 | 328 | 44 | 56 |
| Win rate | 40.26% | 32.01% | 50.00% | 48.21% |
| P&L | $1,461.69 | $394.66 | $1,404.89 | $1,305.23 |
| Max DD | $159.00 | $184.32 | $407.70 | $422.43 |
| Avg win | $36.85 | $16.01 | $123.61 | $121.25 |
| Avg loss | $-8.95 | $-5.77 | $-62.59 | $-67.88 |
| Exits | ema_invalid 154 | ema_invalid 328 | take 21, stop 22, eod 1 | take 26, stop 28, eod 2 |

# Per-book detail

## 15m ema9_trend (AAPL / MSFT / SOXL)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560, 'SOXL:15Min': 1560}
- Signals: 240  (by symbol: {'SOXL': 86, 'AAPL': 77, 'MSFT': 77})
- Pattern hits in those signals: {'ema_cross': 240}
- Trades: 240  (by symbol: {'SOXL': 86, 'AAPL': 77, 'MSFT': 77})
- Wins / losses / scratch: 87 / 152 / 1
- Win rate: 36.25%
- Total P&L: $626.64 (0.627% of starting equity)
- Avg win: $44.65
- Avg loss: $-21.43
- Max drawdown: $850.25 (0.85%)
- Ending equity: $100,626.64
- Exit reasons: {'ema_invalid': 240}
- Trade P&L by symbol (not isolated DDs): AAPL $464.40 (77, 36.36%); MSFT $997.29 (77, 44.16%); SOXL $-835.05 (86, 29.07%)

## 5m ema9_trend (AAPL / MSFT / SOXL)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676, 'SOXL:5Min': 4680}
- Signals: 498  (by symbol: {'SOXL': 170, 'MSFT': 167, 'AAPL': 161})
- Pattern hits in those signals: {'ema_cross': 498}
- Trades: 498  (by symbol: {'SOXL': 170, 'MSFT': 167, 'AAPL': 161})
- Wins / losses / scratch: 153 / 345 / 0
- Win rate: 30.72%
- Total P&L: $-312.80 (-0.313% of starting equity)
- Avg win: $21.47
- Avg loss: $-10.43
- Max drawdown: $722.18 (0.72%)
- Ending equity: $99,687.20
- Exit reasons: {'ema_invalid': 498}
- Trade P&L by symbol (not isolated DDs): AAPL $244.22 (161, 37.27%); MSFT $150.44 (167, 26.95%); SOXL $-707.46 (170, 28.24%)

## 15m ema9_trend SOXL (isolated book)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'SOXL:15Min': 1560}
- Signals: 86  (by symbol: {'SOXL': 86})
- Pattern hits in those signals: {'ema_cross': 86}
- Trades: 86  (by symbol: {'SOXL': 86})
- Wins / losses / scratch: 25 / 60 / 1
- Win rate: 29.07%
- Total P&L: $-835.05 (-0.835% of starting equity)
- Avg win: $63.98
- Avg loss: $-40.57
- Max drawdown: $952.43 (0.95%)
- Ending equity: $99,164.95
- Exit reasons: {'ema_invalid': 86}

## 5m ema9_trend SOXL (isolated book)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'SOXL:5Min': 4680}
- Signals: 170  (by symbol: {'SOXL': 170})
- Pattern hits in those signals: {'ema_cross': 170}
- Trades: 170  (by symbol: {'SOXL': 170})
- Wins / losses / scratch: 48 / 122 / 0
- Win rate: 28.24%
- Total P&L: $-707.46 (-0.707% of starting equity)
- Avg win: $33.41
- Avg loss: $-18.94
- Max drawdown: $911.33 (0.91%)
- Ending equity: $99,292.54
- Exit reasons: {'ema_invalid': 170}

## 15m ema9_trend AAPL/MSFT only (prior universe, extra)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z
- Bars used: {'AAPL:15Min': 1560, 'MSFT:15Min': 1560}
- Signals: 154  (by symbol: {'AAPL': 77, 'MSFT': 77})
- Trades: 154  (by symbol: {'AAPL': 77, 'MSFT': 77})
- Wins / losses / scratch: 62 / 92 / 0
- Win rate: 40.26%
- Total P&L: $1,461.69 (1.462% of starting equity)
- Avg win: $36.85
- Avg loss: $-8.95
- Max drawdown: $159.00 (0.16%)
- Ending equity: $101,461.69
- Exit reasons: {'ema_invalid': 154}

## 5m ema9_trend AAPL/MSFT only (prior universe, extra)

- Period: 2026-06-17T13:30:00Z → 2026-09-11T19:55:00Z
- Bars used: {'AAPL:5Min': 4677, 'MSFT:5Min': 4676}
- Signals: 328  (by symbol: {'MSFT': 167, 'AAPL': 161})
- Trades: 328  (by symbol: {'MSFT': 167, 'AAPL': 161})
- Wins / losses / scratch: 105 / 223 / 0
- Win rate: 32.01%
- Total P&L: $394.66 (0.395% of starting equity)
- Avg win: $16.01
- Avg loss: $-5.77
- Max drawdown: $184.32 (0.18%)
- Ending equity: $100,394.66
- Exit reasons: {'ema_invalid': 328}

## Assumptions

- Signals come from the live evaluate_rule path (same pattern/SMA/EMA/RSI/volume/MA-cross detectors).
- A rule is evaluated when any of its referenced timeframes prints a newly closed bar.
- Entries fill at the next bar open of the finest rule timeframe.
- `exit: ema_invalid` holds a long until a signal-timeframe bar closes < EMA(9) and exits at that close. Close == EMA9 does not invalidate. Optional `stop_loss_pct` is a catastrophic stop only (off here). Percent take is ignored.
- If a catastrophic stop and EMA-invalidation both trade in the same bar, the stop is assumed to fill first.
- One open lot per symbol (no pyramiding). A second signal while flat-in-symbol is skipped.
- Open lots still on the last bar are flattened at the last close (exit reason eod). None remained on these books.
- Isolated SOXL / AAPL+MSFT books are their own equity curves, not a filter of the three-name book’s drawdown.
- Regular-session Yahoo bars (includePrePost=false), unadjusted OHLC.
- commission=$0.00/fill, slippage=0.0%
- Starting equity $100,000.00.
- Cooldown is wall-clock minutes (60) on both tapes.
- 5m and 15m books are separate; they do not share positions or an equity curve.
