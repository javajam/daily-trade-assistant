# EOD green + RSI(14) — Tradier sandbox sleeve

Add-on to the locked EMA9 noon book. Paper on Tradier sandbox with Yahoo 15m bars.

## Rules (v1)

| Piece | Spec |
|------|------|
| Universe | AAPL, 10 shares |
| Signal | Completed **15:30 ET** 15m bar is **green** (`close > open`) and **RSI(14) < 70** |
| Entry | Next opportunity = **15:45 ET bar open** (backtest next-bar open; live market once 15:30 is confirmed) |
| Stop | Hard **fill × 0.995 (−0.5%)**, `stop_mode: entry_pct` — never moves |
| Flatten | `flatten_by: "15:55"` → **15:45 bar close (16:00 ET)** on 15m. Live also flats at wall clock ≥ 15:55. |
| Once / session | Only the 15:30 bar can match `bar.open_at`; same-bar `already_fired` + 60m cooldown |
| Not included | SMA20, volume/range filters, break-of-high, prior-low stop, noon `entry_cutoff` |

Config: `config/eod_green_rsi_tradier_sandbox.example.yaml`  
Day book (do not change): `config/ema9_trend_tradier_sandbox.example.yaml`

Use a **separate process** and this file’s `state_file` (`data/state_eod_green_rsi.json`) so fire keys do not collide with the noon book.

## Validate and dry-run

```bash
python -m dta_bot validate --config config/eod_green_rsi_tradier_sandbox.example.yaml
python -m dta_bot status  --config config/eod_green_rsi_tradier_sandbox.example.yaml
python -m dta_bot run --config config/eod_green_rsi_tradier_sandbox.example.yaml --once --dry-run
```

`dry_run: true` (YAML default) and `--once --dry-run` log `[FIRE]` / `[NO]` only — **no sandbox orders**. `tradier_preview: true` still applies if you later send `--live-orders`.

## Sandbox orders (still not production)

```bash
# second terminal Monday, alongside the noon book:
python -m dta_bot run --config config/eod_green_rsi_tradier_sandbox.example.yaml --live-orders
```

Needs `TRADIER_ACCESS_TOKEN` + `TRADIER_ACCOUNT_ID` in `.env`. `--live-orders` stays on `https://sandbox.tradier.com/v1` unless the live triple-gate is set.

## Paper vs backtest

Same as the noon Tradier sleeve: the live stop is computed from the **15:30 close** at submit time; backtest rebases to the **15:45 open**. Flatten / stop-out is a market `close_position` on the next 60s poll after the trigger.
