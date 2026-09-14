# Locked day-trade book: EMA9×below SMA20 at close

**Decision:** the primary AAPL+MSFT noon day-trade book is **pure MA-cross at close**, not lock-+1% and not lock + MA-cross.

Default configs: `config/ema9_trend.example.yaml` (10-share), `config/ema9_trend_risk.example.yaml` (1% equity risk, `stop_pct: 1.0` as a reference R only). Same book on 5m: `config/ema9_trend_5m.example.yaml` / `config/ema9_trend_risk_5m.example.yaml`. Named copies: `config/ema9_trend_bracket_nobe_macross.example.yaml` / `config/ema9_trend_risk_nobe_macross.example.yaml`.

## Book

- **Long-only** AAPL+MSFT
- Entry: price crosses above EMA(9), close > SMA(20), RSI(14) < 70
- Gates: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Exit: EMA(9) crosses below SMA(20) on a completed bar; fill at **that bar’s close** (`action.exit: ma_cross_close`)
- No `lock_plus`, no percent stop, no half-take, no pyramid, no volume filter

Lock-+1% stays as a comparison example: `config/ema9_trend_bracket_nobe_lock1.example.yaml` / `config/ema9_trend_risk_nobe_lock1.example.yaml`. Combo (lock + MA-cross) stays as `config/ema9_trend_bracket_nobe_lock1_macross.example.yaml`.

## Why this exit

Recorded Yahoo 15m AAPL+MSFT, 2026-06-17 → 2026-09-11, $100k, $0 friction. Not re-run for this adoption.

| Book | 10-share | August 2026 1% risk |
| --- | --- | --- |
| A lock-+1% | **51 / 60.78% / $301.49**, DD $130.76 | **15 / 73.33% / $5,489.78**, DD $2,743.31 |
| B MA-cross at close | **50 / 56.00% / $427.81**, DD $147.68 | **14 / 57.14% / $2,998.96**, DD $2,510.94 |
| C lock + MA-cross | **51 / 54.90% / $296.62**, DD $106.37 | **15 / 60.00% / $4,586.73**, DD $1,915.59 |

B **beats** A on the 10-share tape that defines the baseline ($126.32 ahead). C beats neither on that tape. August 1% risk still favors lock (B missed AAPL 2026-08-04 `lock_stop` +$1,007.60 on a cash skip). Head-to-head writeups: `artifacts/ema9_lock1_macross.md`, `artifacts/ema9_lock1_plus_macross.md`.
