# ema9_trend 10-share: EMA9/SMA20 pair-cross RSI ablation (AAPL/MSFT)

- Generated (UTC): 2026-09-13T22:05:17.300784Z
- Tape: Yahoo Finance v8 chart (unadjusted regular-session OHLC)
- Window: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (~86 calendar days)
- Bars: AAPL 15m 1560; MSFT 15m 1560
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- A. **No RSI** (current default): `config/ema9_trend_bracket.example.yaml`
- B. **RSI14 &lt; 70**: `config/ema9_trend_bracket_rsi.example.yaml` — `rsi: { period: 14, below: 70 }` beside `ema_sma_cross`
- C. **RSI14 &lt; 60**: `config/ema9_trend_bracket_rsi60.example.yaml`
- Session gates (all): `entry_cutoff` 12:00, `flatten_by` 15:55 America/New_York
- Replay: `python -m dta_bot backtest --config config/ema9_trend_bracket.example.yaml --compare-config config/ema9_trend_bracket_rsi.example.yaml --compare-config config/ema9_trend_bracket_rsi60.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_ma_cross_rsi.json --report artifacts/ema9_ma_cross_rsi.md`

**Fill convention:** entries and MA-cross exits fill at the next bar open. Same-bar 1.5% stop still wins. If the EMA/SMA cross-under print is also the flatten bar, `session_flatten` at that close wins. RSI is evaluated on the closed 15m signal bar (same Wilder RSI14 as the old noon book). Signals that fail RSI never fire, so they do not appear as skips.

**Book A reproduced** the PR #19 pair-cross full-window tape exactly: **44 trades, 54.55%, $349.33**, max DD $131.87. Same 98 pair-cross signals (AAPL 52, MSFT 46); **54 skipped as `entry_cutoff`**. Exits: **ma_cross 28 ($-84.50)**, **session_flatten 14 ($451.13)**, stop 2 ($-17.29).

**Book B (RSI14 &lt; 70)** cut **5** pair-cross signals, all in July, all accepted fills on Book A. Remaining: **93 signals** (AAPL 49, MSFT 44), still **54 `entry_cutoff`**, **39 trades, 51.28%, $214.23**, max DD $142.76. The five dropped trades were net **+$135.10** (three session-flatten, two ma_cross). Same two stops as A.

**Book C (RSI14 &lt; 60)** cut another 20 signals vs B (2 of those were already `entry_cutoff`). **73 signals, 21 trades, 33.33%, $31.18**, max DD $131.87. Session-flatten P&L falls from $451.13 (A) / $356.93 (B) to $203.98.

RSI14 &lt; 70 on this tape removes the richer morning crosses, not the losers. Tightening to 60 removes most of the remaining noon-flatten winners.

## Side-by-side

| | A. No RSI (PR #19 default) | B. RSI14 &lt; 70 | C. RSI14 &lt; 60 |
| --- | ---: | ---: | ---: |
| Signals | 98 (AAPL 52, MSFT 46) | 93 (AAPL 49, MSFT 44) | 73 (AAPL 40, MSFT 33) |
| Skips | **entry_cutoff 54** | **entry_cutoff 54** | **entry_cutoff 52** |
| Trades | 44 (AAPL 26, MSFT 18) | 39 (AAPL 23, MSFT 16) | 21 (AAPL 15, MSFT 6) |
| Wins / losses / scratch | 24 / 20 / 0 | 20 / 19 / 0 | 7 / 14 / 0 |
| **Win rate** | **54.55%** | **51.28%** | **33.33%** |
| **Total P&L** | **$349.33** (0.349%) | **$214.23** (0.214%) | **$31.18** (0.031%) |
| Avg win | $28.27 | $26.81 | $32.37 |
| Avg loss | $-16.46 | $-16.94 | $-13.96 |
| **Max drawdown** | **$131.87** (0.13%) | **$142.76** (0.14%) | **$131.87** (0.13%) |
| Ending equity | $100,349.33 | $100,214.23 | $100,031.18 |
| Exit mix | **ma_cross 28**, session_flatten 14, stop 2 | **ma_cross 26**, session_flatten 11, stop 2 | **ma_cross 14**, session_flatten 5, stop 2 |
| **Exit P&L** | ma_cross **$-84.50**; session_flatten **$451.13**; stop $-17.29 | ma_cross **$-125.40**; session_flatten **$356.93**; stop $-17.29 | ma_cross **$-155.50**; session_flatten **$203.98**; stop $-17.29 |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window.

### Five Book A trades that fail RSI14 &lt; 70

| Symbol | Entry (ET) | Exit (ET) | Reason | P&L |
| --- | --- | --- | --- | ---: |
| AAPL | 2026-07-01 09:45 | 2026-07-01 15:15 | ma_cross | $35.70 |
| AAPL | 2026-07-02 09:45 | 2026-07-02 16:00 | session_flatten | $78.40 |
| AAPL | 2026-07-27 09:45 | 2026-07-27 14:00 | ma_cross | $5.20 |
| MSFT | 2026-07-27 09:45 | 2026-07-27 16:00 | session_flatten | $-7.30 |
| MSFT | 2026-07-30 09:45 | 2026-07-30 16:00 | session_flatten | $23.10 |

Net of these five: **+$135.10**. Book A $349.33 − Book B $214.23 = $135.10.

August 1% risk A vs B on the same tape is **identical** (all five RSI≥70 crosses are in July): see `artifacts/ema9_aug2026_risk_rsi.md`.
