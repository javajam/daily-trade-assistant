# Locked range>last-3: 15m vs 5m (AAPL+MSFT)

Same locked noon book on both timeframes. **No MA-cross. No percent stop. No lock_plus. No half-take. No pyramid. No volume filter.**

## Convention

- **15m** is the locked default (`config/ema9_trend.example.yaml` / `config/ema9_trend_risk.example.yaml`).
- **5m** is the same rules with every indicator on 5m bars (`config/ema9_trend_5m.example.yaml` / `config/ema9_trend_risk_5m.example.yaml`).
- EMA 9 / SMA 20 / RSI 14 use the **same lengths** on both tapes. 5m values are computed on 5m closes, not resampled from 15m.
- Range-expansion exit uses that timeframe’s high − low vs the prior three bars of the **same** timeframe. Fill at that close. Not armed on the entry/fill bar.
- `entry_cutoff` 12:00 ET (skip when the next-bar fill would be at/after noon).
- `flatten_by` 15:55 ET: 15m flatten = **15:45 ET** bar close; 5m flatten = **15:50 ET** bar close.
- Same-bar range expansion + flatten → `range_expansion` (close-fill wins). On this tape every trade on both timeframes exited as `range_expansion` (0 flatten).
- Cooldown stays 60 wall-clock minutes.

- Tape: Yahoo 15m/5m unadjusted RTH — 2026-06-25T13:30:00Z start; 15m last closed bar 2026-09-18T19:45:00Z (AAPL/MSFT 1560 bars); 5m last closed bar 2026-09-18T19:55:00Z (AAPL 4678, MSFT 4676). 15m cache hit; 5m downloaded then cached.
- Starting equity: $100,000.00 · friction $0
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend.example.yaml --compare-config config/ema9_trend_5m.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_range3_5m_vs_15m.json --report artifacts/ema9_range3_5m_vs_15m.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --compare-config config/ema9_trend_risk_5m.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_range3_5m_vs_15m.json --report artifacts/ema9_aug2026_risk_range3_5m_vs_15m.md`

August 1% risk sizes both books with `stop_pct: 1.0` as a **reference R only**. No live percent stop.

Engine totals below. Not invented; not annualized.

## Reproduction

15m 10-share **54 / 75.93% / $696.66** matches the locked range3 writeup on this cache. August 1% 15m **16 / 87.50% / $6,008.19** also matches.

## Verdict

**5m does not beat 15m under the locked range>last-3 rules.**

10-share: 15m **54 / 75.93% / $696.66**, max DD $115.38. 5m is **115 / 51.30% / $271.66**, max DD $203.90. **$425.00 behind 15m.** All 115 5m exits are `range_expansion` ($271.66); 0 flatten. 5m prints more noon crosses (337 vs 160) and exits faster (already_in_position 0 vs 14), but the win rate falls (51.30% vs 75.93%). July 5m is **$-61.39** (29t, 55.17%) vs 15m **+$245.14** (16t, 68.75%).

August 2026 1% risk: 15m **16 / 87.50% / $6,008.19**, max DD $2,028.83. 5m is **43 / 44.19% / $3,421.21**, max DD $1,757.47. **Does not beat** ($2,586.98 behind). 5m AAPL 1% is 18t / 44.44% / **$-450.91** vs 15m 6t / 100% / $4,015.35.

## 1. 10-share full window

15m **reproduced**: **54 trades, 75.93%, $696.66**, max DD $115.38. Signals 160 (AAPL 81, MSFT 79). Skips: `entry_cutoff` 92, `already_in_position` 14. Exits: **range_expansion 54 ($696.66)**.

5m: **115 trades, 51.30%, $271.66**, max DD $203.90. Signals 337 (AAPL 170, MSFT 167). Skips: `entry_cutoff` 222. Exits: **range_expansion 115 ($271.66)**.

### Side-by-side (10-share)

| | 15m range>last-3 | 5m range>last-3 |
| --- | ---: | ---: |
| Signals | 160 (AAPL 81, MSFT 79) | 337 (AAPL 170, MSFT 167) |
| Skips | already_in_position 14, entry_cutoff 92 | entry_cutoff 222 |
| Trades | 54 (AAPL 26, MSFT 28) | 115 (AAPL 58, MSFT 57) |
| Wins / losses | 41 / 13 | 59 / 56 |
| **Win rate** | **75.93%** | **51.30%** |
| **Total P&L** | **$696.66 (0.697%)** | **$271.66 (0.272%)** |
| Avg win | $25.51 | $17.05 |
| Avg loss | $-26.86 | $-13.11 |
| **Max drawdown** | **$115.38 (0.11%)** | **$203.90 (0.20%)** |
| Ending equity | $100,696.66 | $100,271.66 |
| Exit mix | range_expansion 54 | range_expansion 115 |
| **Exit P&L** | range_expansion $696.66 (54) | range_expansion $271.66 (115) |

Entry fill is next-bar open on both. Neither book used session flatten on this window.

### Monthly (10-share)

| Month | 15m | 5m |
| --- | ---: | ---: |
| 2026-06 | $128.40 (5t, 60.00%) | $38.28 (9t, 66.67%) |
| 2026-07 | $245.14 (16t, 68.75%) | $-61.39 (29t, 55.17%) |
| 2026-08 | $276.41 (19t, 89.47%) | $167.02 (52t, 46.15%) |
| 2026-09 | $46.71 (14t, 71.43%) | $127.75 (25t, 52.00%) |

July is where 5m loses the tape. September is the only month 5m is ahead.

### By symbol (10-share)

| | 15m | 5m |
| --- | ---: | ---: |
| AAPL | 26t, 76.92%, $223.97 | 58t, 56.90%, $167.37 |
| MSFT | 28t, 75.00%, $472.70 | 57t, 45.61%, $104.29 |

## 2. August 2026 1% equity risk

| | 15m 1% | 5m 1% |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 125 (AAPL 53, MSFT 72) |
| Skips | entry_cutoff 35, already_in_position 3, insufficient_cash 3 | entry_cutoff 73, insufficient_cash 8 |
| Trades | 16 (AAPL 6, MSFT 10) | 43 (AAPL 18, MSFT 25) |
| Wins / losses | 14 / 2 | 19 / 24 |
| **Win rate** | **87.50%** | **44.19%** |
| **Total P&L** | **$6,008.19 (6.008%)** | **$3,421.21 (3.421%)** |
| Avg win | $537.84 | $556.68 |
| Avg loss | $-760.79 | $-298.15 |
| **Max drawdown** | **$2,028.83 (1.96%)** | **$1,757.47 (1.75%)** |
| Ending equity | $106,008.19 | $103,421.21 |
| Exit mix | range_expansion 16 | range_expansion 43 |
| **Exit P&L** | range_expansion $6,008.19 (16) | range_expansion $3,421.21 (43) |
| AAPL | 6t, 100.00%, $4,015.35 | 18t, 44.44%, $-450.91 |
| MSFT | 10t, 80.00%, $1,992.85 | 25t, 44.00%, $3,872.13 |

5m August max DD is lower ($1,757.47 vs $2,028.83) but P&L is not ahead. 5m AAPL 1% is a net loss; 5m MSFT is ahead of 15m MSFT ($3,872.13 vs $1,992.85) and still not enough.

## Fill conventions

| Leg | When | Fill |
| --- | --- | --- |
| Entry | Signal bar closes with a valid long setup before `entry_cutoff` | **Next bar open** of that timeframe |
| `range_expansion` | Completed bar **after the fill bar**: range > max of previous 3 | **That bar’s close** |
| `session_flatten` | Bar containing 15:55 ET if still open and no same-bar close-fill exit | That bar’s close (15m = 15:45 ET; 5m = 15:50 ET) |

Same-bar range expansion + flatten → **range_expansion**. Same-bar stop (if set) + range expansion → **stop**.

Full engine dumps: `artifacts/ema9_range3_5m_vs_15m.json`, `artifacts/ema9_aug2026_risk_range3_5m_vs_15m.json`.
