# ema9_trend AAPL+MSFT: does EMA9×below SMA20 at close beat plain lock-+1%?

Same entry / gates as the lock-+1% default. **No volume filter. No half-take. No pyramid. No lock-+1%. No live percent stop.** B exits when **EMA(9) crosses below SMA(20)** on a completed 15m bar after entry and fills at **that bar’s close**.

- Tape: Yahoo 15m unadjusted RTH, 2026-06-17T13:30:00Z → 2026-09-11T19:45:00Z (AAPL/MSFT 1560 closed bars each)
- Starting equity: $100,000.00 · friction $0
- Session: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET (15m flatten = 15:45 ET bar close)
- Entry (both): close crosses above EMA(9) AND close > SMA(20) AND RSI(14) < 70
- A exit: `stop_mode: lock_plus` — initial fill × 0.99; first touch of fill × 1.01 locks the stop there. No take.
- B exit:
  1. Cross is **EMA vs SMA close-to-close**, not price vs MA. Long: prev EMA ≥ prev SMA and curr EMA < curr SMA (`action.exit: ma_cross_close`).
  2. Fill at that completed bar’s **close** (same convention as `ema_invalid` / `lower_high`). Exit reason `ma_cross`.
  3. Existing next-open `ma_cross` is unchanged (shorts / pair-cross books).
  4. No live `%` stop. No lock. No take. Session flatten still applies.
  5. If the cross bar is also the flatten bar, **`ma_cross` at that close wins** over `session_flatten`. Next-open `ma_cross` would still lose to flatten on that bar.
- Replay 10-share: `python -m dta_bot backtest --config config/ema9_trend_bracket_nobe_lock1.example.yaml --compare-config config/ema9_trend_bracket_nobe_macross.example.yaml --source yahoo --combined-only --symbols AAPL,MSFT --output artifacts/ema9_lock1_macross.json --report artifacts/ema9_lock1_macross.md`
- Replay August 1% risk: `python -m dta_bot backtest --config config/ema9_trend_risk_nobe_lock1.example.yaml --compare-config config/ema9_trend_risk_nobe_macross.example.yaml --source yahoo --start 2026-08-01 --end 2026-08-31 --combined-only --symbols AAPL,MSFT --output artifacts/ema9_aug2026_risk_lock1_macross.json --report artifacts/ema9_aug2026_risk_lock1_macross.md`

August 1% risk sizes B with `stop_pct: 1.0` as a **reference R only** (1% of entry): `shares = floor((0.01 × equity) / (0.01 × price))`. No live 1% stop is placed.

Engine totals below. Not invented; not annualized.

## Verdict

**Yes on the 10-share tape that defines the baseline. No on August 2026 1% equity risk.**

10-share full window: A **reproduced 51 / 60.78% / $301.49**. B is **50 / 56.00% / $427.81**, max DD $147.68 vs $130.76. **$126.32 ahead of A** on P&L, with a lower win rate and a slightly worse drawdown. Exit mix: **`ma_cross` 37 ($-123.01)** / **`session_flatten` 13 ($550.83)**. One of those 37 `ma_cross` fills landed on the flatten bar (MSFT 2026-08-04 15:45 ET close); close-fill won.

August 1% risk: A **reproduced 15 / 73.33% / $5,489.78**. B is **14 / 57.14% / $2,998.96**, max DD $2,510.94 vs $2,743.31. **Does not beat** ($2,490.82 behind). B missed AAPL 2026-08-04 15:45Z (A `lock_stop` **+$1,007.60**) — still in MSFT until the flatten-bar pair-cross, so the AAPL notional failed the cash check. On the 14 paired fills B is still **$1,483.22 behind** (lock_stops that became earlier `ma_cross` cuts).

## 1. 10-share full window

A (lock-+1%) **reproduced**: **51 trades, 60.78%, $301.49**, max DD $130.76.

B (EMA9×below SMA20 at close): **50 trades, 56.00%, $427.81**, max DD $147.68. **$126.32 ahead of A.**

| | A. Lock +1% | B. MA-cross at close |
| --- | ---: | ---: |
| Signals | 154 (AAPL 77, MSFT 77) | 154 (AAPL 77, MSFT 77) |
| Skips | already_in_position 28, entry_cutoff 75 | already_in_position 35, entry_cutoff 69 |
| Trades | 51 (AAPL 23, MSFT 28) | 50 (AAPL 22, MSFT 28) |
| Wins / losses / scratch | 31 / 20 / 0 | 28 / 22 / 0 |
| **Win rate** | **60.78%** | **56.00%** |
| **Total P&L** | **$301.49 (0.301%)** | **$427.81 (0.428%)** |
| Avg win | $27.05 | $30.99 |
| Avg loss | -$26.85 | -$19.99 |
| **Max drawdown** | **$130.76 (0.13%)** | **$147.68 (0.15%)** |
| Ending equity | $100,301.49 | $100,427.81 |
| Exit mix | lock_stop 20, stop 13, session_flatten 18 | ma_cross 37, session_flatten 13 |
| Lock armed | 20 | 0 (no lock / no % stop) |
| **Exit P&L** | lock_stop $684.73 (20); stop -$459.59 (13); session_flatten $76.35 (18) | ma_cross $-123.01 (37); session_flatten $550.83 (13) |

Same 154 signals. B occupies the symbol longer (35 `already_in_position` vs 28), so it takes one fewer fill: AAPL 2026-07-17 14:45Z. A’s 13:30Z lot had already `stop`’d ($-33.25) so A re-entered and `stop`’d again ($-33.31). B’s 13:30Z lot stayed open until 16:30Z `ma_cross` ($-7.95). Missing that second same-day stop helped B.

50 paired `(symbol, entry_time)` fills. Reason map (A → B):

| A exit → B exit | n |
| --- | ---: |
| lock_stop → ma_cross | 12 |
| lock_stop → session_flatten | 8 |
| stop → ma_cross | 12 |
| session_flatten → ma_cross | 13 |
| session_flatten → session_flatten | 5 |

The P&L lift is mostly **no hard 1% stop** plus **runners that never printed an EMA×SMA cross-under** and rode to flatten ($550.83 vs A’s flatten $76.35). Converting 12 `stop`s to `ma_cross` usually cut the loss (AAPL 2026-07-17 13:30Z $-33.25 → $-7.95). The cost is 12 `lock_stop`s cut earlier as `ma_cross` and a lower win rate.

One flatten-bar pair-cross: MSFT 2026-08-04, exit 20:00Z (15:45 ET bar close), reason **`ma_cross` +$17.40** — close-fill won over `session_flatten`.

### Monthly (10-share)

| Month | A. Lock +1% | B. MA-cross at close |
| --- | ---: | ---: |
| 2026-06 | $-18.75 (10t, 40.00%) | $68.26 (10t, 40.00%) |
| 2026-07 | $71.56 (17t, 64.71%) | $235.45 (16t, 62.50%) |
| 2026-08 | $304.88 (18t, 77.78%) | $192.46 (18t, 66.67%) |
| 2026-09 | $-56.20 (6t, 33.33%) | $-68.35 (6t, 33.33%) |

June and July are where B pulls ahead. August is where lock-+1% is better on this 10-share tape ($304.88 vs $192.46) — the same month the 1% risk book then fails to beat.

### By symbol (10-share)

| | A. Lock +1% | B. MA-cross at close |
| --- | ---: | ---: |
| AAPL | 23t, 52.17%, $6.36 (stop 8 / lock_stop 8 / flatten 7) | 22t, 50.00%, $129.13 (ma_cross 17 / flatten 5) |
| MSFT | 28t, 67.86%, $295.12 (lock_stop 12 / flatten 11 / stop 5) | 28t, 60.71%, $298.68 (ma_cross 20 / flatten 8) |

B’s AAPL lift is avoiding A’s stop cluster. MSFT is nearly a wash in dollars with a lower win rate.

## 2. August 2026 1% equity risk (both books)

Same tape, `--start 2026-08-01 --end 2026-08-31`. Lock-+1% **reproduced**: **15 trades, 73.33%, $5,489.78**, max DD $2,743.31 (6 `lock_stop` / 8 `session_flatten` / 1 stop). B: **14 trades, 57.14%, $2,998.96**, max DD $2,510.94. **Does not beat.**

B has no live percent stop. Share count uses `equity_risk: 0.01` and `stop_pct: 1.0` as a reference R (1% of entry). Qty 200–328 vs A’s 203–337.

| | A. Lock +1% 1% risk | B. MA-cross at close 1% risk |
| --- | ---: | ---: |
| Signals | 58 (AAPL 26, MSFT 32) | 58 (AAPL 26, MSFT 32) |
| Skips | entry_cutoff 28, already_in_position 11, insufficient_cash 3 | entry_cutoff 28, already_in_position 11, insufficient_cash 4 |
| Fill-time cash skips | 1 | 1 |
| Trades | 15 (AAPL 7, MSFT 8) | 14 (AAPL 6, MSFT 8) |
| Wins / losses / scratch | 11 / 4 / 0 | 8 / 6 / 0 |
| **Win rate** | **73.33%** | **57.14%** |
| **Total P&L** | **$5,489.78 (5.490%)** | **$2,998.96 (2.999%)** |
| Avg win | $697.61 | $604.79 |
| Avg loss | -$546.00 | -$306.56 |
| **Max drawdown** | **$2,743.31 (2.58%)** | **$2,510.94 (2.44%)** |
| Ending equity | $105,489.78 | $102,998.96 |
| Exit mix | lock_stop 6, session_flatten 8, stop 1 | ma_cross 10, session_flatten 4 |
| **Exit P&L** | lock_stop $5,623.20 (6); session_flatten $917.28 (8); stop $-1,050.69 (1) | ma_cross $-75.78 (10); session_flatten $3,074.74 (4) |

The missed fill is AAPL 2026-08-04 15:45Z. A’s MSFT 14:00Z had already `lock_stop`’d at 15:00Z (+$996.89), freeing cash for AAPL (`lock_stop` +$1,007.60). B’s MSFT 14:00Z stayed open until the 15:45 ET flatten bar and exited `ma_cross` +$353.22 (same-bar pair-cross; close-fill won). AAPL 15:45Z then failed the cash check.

On the 14 paired fills B is still behind: several A `lock_stop` / flatten runners were cut as `ma_cross` (MSFT 2026-08-10 A +$1,035.65 → B +$93.00; AAPL 2026-08-05 A flatten +$683.10 → B `ma_cross` -$189.54). Offsets include converting AAPL 2026-08-20’s `stop` -$1,050.69 into `ma_cross` -$265.60.

### By symbol (August 1% risk)

| | A. Lock +1% | B. MA-cross at close |
| --- | ---: | ---: |
| AAPL | 7t, 71.43%, $2,665.05 (lock_stop 3 / flatten 3 / stop 1) | 6t, 50.00%, $1,777.00 (ma_cross 5 / flatten 1) |
| MSFT | 8t, 75.00%, $2,824.73 (lock_stop 3 / flatten 5) | 8t, 62.50%, $1,221.96 (ma_cross 5 / flatten 3) |

## Configs

- A 10-share: `config/ema9_trend_bracket_nobe_lock1.example.yaml`
- B 10-share: `config/ema9_trend_bracket_nobe_macross.example.yaml`
- A 1% risk: `config/ema9_trend_risk_nobe_lock1.example.yaml`
- B 1% risk: `config/ema9_trend_risk_nobe_macross.example.yaml` (`stop_pct: 1.0` reference R only; `stop_loss_pct` omitted)
