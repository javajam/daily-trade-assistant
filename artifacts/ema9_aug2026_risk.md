# ema9_trend — August 2026 live-style book ($100k, 1% risk)

Replay of a **$100,000** long-only book on **AAPL + MSFT** for **2026-08-01 through 2026-08-31** (RTH, America/New_York). Numbers are engine totals from Yahoo 15m bars. Nothing here is estimated.

## Locked settings

| Knob | Value |
| --- | --- |
| Strategy | 15m EMA(9) bullish cross + close > SMA20 + RSI14 < 70 |
| Exit | `fixed_bracket` — stop 1.5%, take 3.0% (not `ema_invalid`) |
| Universe | AAPL, MSFT (SOXL not in this book) |
| Starting equity | $100,000 |
| Sizing | `size: { type: risk_pct, equity_risk: 0.01, stop_pct: 1.5 }` |
| Share formula | `floor((0.01 * equity) / (0.015 * entry_price))` = `floor(equity / (1.5 * entry_price))` |
| Recalc | From marked-to-market equity at each signal; one lot per symbol |
| Both names open? | Allowed if cash covers the second notional; otherwise skip |
| Friction | $0 commission, 0% slippage |
| Config | `config/ema9_trend_risk.example.yaml` |
| Replay | `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --output artifacts/ema9_aug2026_risk.json --report artifacts/ema9_aug2026_risk.md` |

JSON: `artifacts/ema9_aug2026_risk.json`. The 10-share control is `artifacts/ema9_aug2026_10share.json` / `.md`.

## Yahoo window

Yahoo v8 15m regular-session bars (`includePrePost=false`, unadjusted OHLC) are capped at **60d** in this downloader. This run downloaded:

- AAPL 15m: 1560 closed bars, **2026-06-17 13:30Z → 2026-09-11 19:45Z**
- MSFT 15m: 1560 closed bars, same span

**August 2026 was not clipped.** Bars before 2026-08-01 were used only for SMA/RSI/EMA warmup (lookback 80). No new entries after the Aug 31 session. Open lots flatten at the last in-window mark (`eod`).

First RTH day in the month is **Mon 2026-08-03** (Aug 1–2 is the weekend). Last is **Mon 2026-08-31**. 21 session days.

## Monthly summary (1% risk)

| | |
| --- | ---: |
| Starting equity | $100,000.00 |
| Ending equity | $105,502.59 |
| **Total P&L** | **$5,502.59** |
| **Return** | **5.503%** |
| Max drawdown | $3,282.83 (3.13%) |
| Trades | 7 (AAPL 1, MSFT 6) |
| Wins / losses | 4 / 3 |
| **Win rate** | **57.14%** |
| Avg win | $2,035.18 |
| Avg loss | $-879.38 |
| Exit mix | take 4, stop 2, eod 1 |
| Best day (realized) | 2026-08-28 **$2,085.22** (1 trade) |
| Worst day (realized) | 2026-08-17 **$-1,050.45** (1 trade) |
| Signals | 58 (AAPL 26, MSFT 32) |

Signals that did not become trades: **29** `already_in_position` (same symbol still open), **22** `insufficient_cash` (the other name’s risk size would have spent more cash than was left). **Max concurrent symbols: 1. Ticks with both names open: 0.**

At these prices a 1% / 1.5% lot is about two-thirds of the book (first fill: 217 AAPL × $306.35 ≈ $66,478). The second name cannot open until the first lot is flat. That is why this month is almost entirely MSFT after the opening AAPL take.

Daily P&L in the tables below is **realized** (sum of trades whose exit falls on that NY date) as a percent of the $100k start. Equity EOD is mark-to-market and can move on days with 0 closed trades.

## Weekly

| Week | Trades | Win rate | P&L $ | P&L % | Equity EOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W32 (2026-08-03 → 2026-08-07) | 1 | 100.00% | $1,996.57 | 2.00% | $102,903.51 |
| 2026-W33 (2026-08-10 → 2026-08-14) | 2 | 50.00% | $998.52 | 1.00% | $102,657.38 |
| 2026-W34 (2026-08-17 → 2026-08-21) | 1 | 0.00% | $-1,050.45 | -1.05% | $102,222.06 |
| 2026-W35 (2026-08-24 → 2026-08-28) | 2 | 100.00% | $4,118.92 | 4.12% | $106,063.56 |
| 2026-W36 (2026-08-31 → 2026-08-31) | 1 | 0.00% | $-560.97 | -0.56% | $105,502.59 |

## Daily

| Date | Trades | Wins | Losses | P&L $ | P&L % | Equity EOD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0 | 0 | 0 | $0.00 | 0.00% | $99,331.64 |
| 2026-08-04 | 0 | 0 | 0 | $0.00 | 0.00% | $100,659.68 |
| 2026-08-05 | 0 | 0 | 0 | $0.00 | 0.00% | $100,991.69 |
| 2026-08-06 | 1 | 1 | 0 | $1,996.57 | 2.00% | $102,899.40 |
| 2026-08-07 | 0 | 0 | 0 | $0.00 | 0.00% | $102,903.51 |
| 2026-08-10 | 1 | 1 | 0 | $2,025.23 | 2.03% | $104,127.97 |
| 2026-08-11 | 0 | 0 | 0 | $0.00 | 0.00% | $103,832.05 |
| 2026-08-12 | 1 | 0 | 1 | $-1,026.71 | -1.03% | $102,995.09 |
| 2026-08-13 | 0 | 0 | 0 | $0.00 | 0.00% | $102,847.81 |
| 2026-08-14 | 0 | 0 | 0 | $0.00 | 0.00% | $102,657.38 |
| 2026-08-17 | 1 | 0 | 1 | $-1,050.45 | -1.05% | $101,944.64 |
| 2026-08-18 | 0 | 0 | 0 | $0.00 | 0.00% | $102,021.83 |
| 2026-08-19 | 0 | 0 | 0 | $0.00 | 0.00% | $102,381.39 |
| 2026-08-20 | 0 | 0 | 0 | $0.00 | 0.00% | $101,944.14 |
| 2026-08-21 | 0 | 0 | 0 | $0.00 | 0.00% | $102,222.06 |
| 2026-08-24 | 0 | 0 | 0 | $0.00 | 0.00% | $102,784.64 |
| 2026-08-25 | 0 | 0 | 0 | $0.00 | 0.00% | $103,371.21 |
| 2026-08-26 | 1 | 1 | 0 | $2,033.70 | 2.03% | $104,223.34 |
| 2026-08-27 | 0 | 0 | 0 | $0.00 | 0.00% | $105,442.74 |
| 2026-08-28 | 1 | 1 | 0 | $2,085.22 | 2.09% | $106,063.56 |
| 2026-08-31 | 1 | 0 | 1 | $-560.97 | -0.56% | $105,502.59 |

## Trade blotter (1% risk)

Times are UTC as stored by the engine (EDT = UTC−4 in August). Qty is recalculated from equity at the signal.

| Symbol | Qty | Entry (UTC) | Entry $ | Exit (UTC) | Exit $ | P&L $ | Reason |
| --- | ---: | --- | ---: | --- | ---: | ---: | --- |
| AAPL | 217 | 2026-08-03 16:30Z | 306.3500 | 2026-08-06 13:45Z | 315.5508 | +1,996.57 | take |
| MSFT | 137 | 2026-08-06 13:45Z | 493.2700 | 2026-08-10 13:45Z | 508.0527 | +2,025.23 | take |
| MSFT | 137 | 2026-08-10 13:45Z | 505.1950 | 2026-08-12 13:45Z | 497.7008 | −1,026.71 | stop |
| MSFT | 137 | 2026-08-13 13:45Z | 497.8850 | 2026-08-17 13:45Z | 490.2175 | −1,050.45 | stop |
| MSFT | 141 | 2026-08-18 14:15Z | 481.3825 | 2026-08-26 14:00Z | 495.8059 | +2,033.70 | take |
| MSFT | 140 | 2026-08-26 16:15Z | 494.4200 | 2026-08-28 13:45Z | 509.3144 | +2,085.22 | take |
| MSFT | 138 | 2026-08-31 17:00Z | 511.3850 | 2026-08-31 20:00Z | 507.3200 | −560.97 | eod |

First lot check: `floor(100000 / (1.5 * 306.35)) = floor(217.615) = 217`. Later MSFT sizes move with equity (137 → 141 → 140 → 138).

The August 31 MSFT long was still open at the 16:00 ET close and was flattened there (`eod`), not at the 1.5% stop.

## Same month, old fixed 10-share sizing

Same tape, same window, same entry/exit (`config/ema9_trend_bracket.example.yaml`). Only the share count changes.

| | 1% risk | 10 shares |
| --- | ---: | ---: |
| Trades | 7 (AAPL 1 / MSFT 6) | 11 (AAPL 5 / MSFT 6) |
| Win rate | 57.14% | 54.55% |
| Total P&L | **$5,502.59** (5.503%) | **$430.47** (0.430%) |
| Max DD | $3,282.83 (3.13%) | $251.10 (0.25%) |
| Ending equity | $105,502.59 | $100,430.47 |
| Avg win / avg loss | $2,035.18 / $-879.38 | $119.52 / $-57.34 |
| Exits | take 4, stop 2, eod 1 | take 6, stop 4, eod 1 |
| Both names open | never (22 cash skips) | yes (max 2; 7 ticks) |
| Best / worst day | Aug 28 $2,085.22 / Aug 17 $-1,050.45 | Aug 28 $242.40 / Aug 17 $-76.68 |

The 10-share book took the same six MSFT swings plus four extra AAPL fills the risk book could not fund, and it also got the Aug 3 MSFT entry while AAPL was already open. Dollar P&L is larger on the risk book because each lot is ~14–22× the 10-share notional; drawdown scales the same way. This is one month on two names, not a robustness study.

## Assumptions (engine)

- Signals use the live `evaluate_rule` path (same EMA-cross / SMA / RSI detectors).
- Entries fill at the next 15m open. Stop/take are computed from the signal-bar close. Same-bar stop+take → stop. A gap through a level fills at the open.
- One lot per symbol; no pyramiding.
- $0 commission / 0% slippage.
- Open lots still on the last August bar flatten at that close (`eod`).
