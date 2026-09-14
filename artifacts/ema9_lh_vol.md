# ema9_trend AAPL+MSFT: lock-+1% vs lower-high + volume filter

- Generated from Yahoo 15m replay (unadjusted regular-session OHLC)
- Tape: 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed 15m bars each)
- Starting equity: $100,000.00
- Friction: commission=$0.00/fill, slippage=0.0%
- Session gates (both books): `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_lh_vol.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lh_vol.json --report artifacts/ema9_lh_vol.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_lh_vol.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lh_vol.json --report artifacts/ema9_aug2026_risk_lh_vol.md`

## Rule delta

| | A. Lock-+1% (baseline) | B. Lower-high + vol>prev (new) |
| --- | --- | --- |
| Entry | close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70 | same, **plus** signal-bar volume > previous-bar volume |
| Stop | initial fill × 0.99; first touch of fill × 1.01 locks the stop there (`lock_plus`) | **none** (no live percent stop) |
| Primary exit | stop / `lock_stop` / `session_flatten` | **lower high** on a completed 15m bar after entry: current high < previous high; fill at **that bar's close** (same convention as `ema_invalid`) |
| Session flatten | 15:55 ET hard flat | same hard flat; if the flatten bar is also a lower high, `lower_high` at that close wins |

Risk sizing on the August books uses `size.type: risk_pct`, `equity_risk: 0.01`, `stop_pct: 1.0` as a **reference R only** (1% of entry price). Share count is `floor((0.01 × equity) / (0.01 × price))` so it stays comparable to lock-+1%. The new risk YAML does **not** place a live 1% stop.

## 1. Baseline reproduced (10-share lock-+1%)

**51 trades, 60.78%, $301.49**, max DD $130.76. Matches the expected Yahoo ~2026-06-17→2026-09-11 lock-+1% book (~51 / ~$301.49 / ~60.78%).

Signals 154 (AAPL 77, MSFT 77). Skips: `entry_cutoff` 75, `already_in_position` 28. Exits: **lock_stop 20 ($684.73)**, **stop 13 ($-459.59)**, **session_flatten 18 ($76.35)**. 20 armed the +1% lock; all 20 then exited as `lock_stop`.

## 2. New rules, same tape (10-share)

**34 trades, 55.88%, $130.91**, max DD $179.48. Volume filter cut signals 154 → 101 (AAPL 49, MSFT 52). 67 leftover signals skipped as `entry_cutoff` (no `already_in_position` — lower-high frees the symbol before the next noon setup stacks).

**Exit mix: `lower_high` 34 ($130.91). `session_flatten` 0.** Every filled lot printed a lower high before (or on) the flatten bar, so the close-of-bar lower-high exit always won.

Lower-high + volume **does not beat** lock-+1% on this window: **$170.58 behind**, lower win rate, wider drawdown.

### Side-by-side (10-share, full Yahoo window)

| | A. Lock +1% | B. Lower-high + vol>prev |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 101 (AAPL 49, MSFT 52) |
| Skips | already_in_position 28, entry_cutoff 75 | entry_cutoff 67 |
| Trades | 51 (AAPL 23, MSFT 28) | 34 (AAPL 14, MSFT 20) |
| Wins / losses / scratch | 31 / 20 / 0 | 19 / 15 / 0 |
| **Win rate** | **60.78%** | **55.88%** |
| **Total P&L** | **$301.49 (0.301%)** | **$130.91 (0.131%)** |
| Avg win | $27.05 | $20.70 |
| Avg loss | -$26.85 | -$17.50 |
| **Max drawdown** | **$130.76 (0.13%)** | **$179.48 (0.18%)** |
| Ending equity | $100,301.49 | $100,130.91 |
| Exit mix | lock_stop 20, stop 13, session_flatten 18 | lower_high 34, session_flatten 0 |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); session_flatten $76.35 (18) | lower_high $130.91 (34) |

Figures are engine totals, not annualized. One ~86-day Yahoo 15m window. 10 shares, $0 friction.

### Monthly (10-share)

| Month | A. Lock +1% | B. Lower-high + vol>prev |
| --- | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $119.30 (4t, 75.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $22.89 (14t, 57.14%) |
| 2026-08 | $304.88 (18t, 77.78%) | $38.12 (13t, 53.85%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-49.40 (3t, 33.33%) |

June is the only month B is ahead (fewer, better trades). August is where lock-+1% pulls away ($304.88 vs $38.12).

### By symbol (10-share)

| | A. Lock +1% | B. Lower-high + vol>prev |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 (stop 8 / lock_stop 8 / flatten 7) | 14t, 50.00%, $8.27 (lower_high 14) |
| MSFT | 28t, 67.86%, $295.12 (lock_stop 12 / flatten 11 / stop 5) | 20t, 60.00%, $122.64 (lower_high 20) |

MSFT carries both books. Lock-+1% keeps more of the MSFT runners via `lock_stop` / flatten; lower-high cuts them at the first down-high close.

## 3. August 2026 1% equity risk (both books)

Same tape, `--start 2026-08-01 --end 2026-08-31`. Lock-+1% **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31 (6 `lock_stop` / 8 `session_flatten` / 1 stop). New book: **12 trades, 58.33%, $1,059.41**, max DD $881.79. All 12 new-book exits are `lower_high` (0 flatten).

| | A. Lock +1% 1% risk | B. Lower-high + vol>prev 1% risk |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 43 (AAPL 19, MSFT 24) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 30 |
| Trades | 15 (AAPL 7, MSFT 8) | 12 (AAPL 5, MSFT 7) |
| Wins / losses | 11 / 4 | 7 / 5 |
| **Win rate** | **73.33%** | **58.33%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$1,059.41 (1.059%)** |
| Avg win | $697.61 | $229.37 |
| Avg loss | -$546.00 | -$109.24 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$881.79 (0.87%)** |
| Ending equity | $105,489.78 | $101,059.41 |
| Exit mix | lock_stop 6, session_flatten 8, stop 1 | lower_high 12, session_flatten 0 |
| **Exit P&L** | lock_stop $5,623.20 (6); session_flatten $917.28 (8); stop -$1,050.69 (1) | lower_high $1,059.41 (12) |
| AAPL | 7t, 71.43%, $2,665.05 | 5t, 60.00%, $646.67 |
| MSFT | 8t, 75.00%, $2,824.73 | 7t, 57.14%, $412.74 |

August 1% risk is a small sample. Lock-+1% is **$4,430.37 ahead**. The new book has a tighter drawdown because lower-high never lets a runner (or a 1% stop hit) extend; it also never collects the lock-stop / flatten winners that dominate August on the baseline.

## Verdict

On this Yahoo 15m AAPL+MSFT tape, **lower-high + volume does not beat lock-+1%**. The volume filter drops about a third of the EMA9-cross signals (154 → 101 full window; 58 → 43 in August). The lower-high exit then closes every filled lot at the first completed down-high, so nothing reaches `session_flatten` and the August lock-stop runners disappear. Lock-+1% remains ahead on trade count, win rate, and P&L on both the 10-share full window and the August 1% risk book.

Full engine dumps: `artifacts/ema9_lh_vol.json`, `artifacts/ema9_aug2026_risk_lh_vol.json` (August narrative also in `artifacts/ema9_aug2026_risk_lh_vol.md`).
