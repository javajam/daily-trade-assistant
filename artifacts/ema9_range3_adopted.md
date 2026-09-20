# Locked day-trade book: range > last 3 bars

Superseded as the default: the locked book is now range>last-3 **plus** a hard 1% fill stop. See `artifacts/ema9_range3_fixed1_adopted.md`. This note is the prior adoption (unprotected range3).

**Decision (then):** the primary AAPL+MSFT noon day-trade book is **range expansion** (`action.exit: range_expansion`), not MA-cross at close.

Default configs: `config/ema9_trend.example.yaml` (10-share), `config/ema9_trend_risk.example.yaml` (1% equity risk, `stop_pct: 1.0` as a reference R only). Same book on 5m: `config/ema9_trend_5m.example.yaml` / `config/ema9_trend_risk_5m.example.yaml`. 10-share sibling: `config/ema9_trend_bracket.example.yaml`. Named copies: `config/ema9_trend_bracket_nobe_range3.example.yaml` / `config/ema9_trend_risk_nobe_range3.example.yaml`.

## Book

- **Long-only** AAPL+MSFT
- Entry: price crosses above EMA(9), close > SMA(20), RSI(14) < 70
- Gates: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Exit: completed bar after the fill has range (high − low) **strictly greater than** max of the previous 3 bars; fill at **that bar’s close**. Not armed on the entry/fill bar.
- No MA-cross exit, no `lock_plus`, no percent stop, no half-take, no pyramid, no volume filter
- Same-bar range expansion + flatten → `range_expansion` (close-fill wins)

MA-cross at close stays as a comparison example: `config/ema9_trend_bracket_nobe_macross.example.yaml` / `config/ema9_trend_risk_nobe_macross.example.yaml`. Prior adoption note: `artifacts/ema9_macross_adopted.md`.

## Why this exit

Recorded Yahoo 15m AAPL+MSFT, 2026-06-25 → 2026-09-18, $100k, $0 friction. Not re-run for this adoption. Head-to-head: `artifacts/ema9_range3.md`.

| Book | 10-share | August 2026 1% risk |
| --- | --- | --- |
| A then-locked MA-cross at close | **50 / 58.00% / $560.31**, DD $147.68 | **14 / 57.14% / $2,998.96**, DD $2,510.94 |
| E range > last 3 | **54 / 75.93% / $696.66**, DD $115.38 | **16 / 87.50% / $6,008.19**, DD $2,028.83 |

E **beats** A on both required runs ($136.35 / $3,009.23 ahead). All E exits on that tape were `range_expansion` (0 flatten).
