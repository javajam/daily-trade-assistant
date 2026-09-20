# Locked day-trade book: range > last 3 + hard 1% fill stop

**Decision:** the primary AAPL+MSFT noon day-trade book is **range expansion plus a hard 1% fill stop** (`action.exit: range_expansion`, `stop_mode: entry_pct`, `stop_loss_pct: 1.0`), not unprotected range3 and not MA-cross at close.

Default configs: `config/ema9_trend.example.yaml` (10-share), `config/ema9_trend_risk.example.yaml` (1% equity risk at the live 1.0% fill stop). Same book on 5m: `config/ema9_trend_5m.example.yaml` / `config/ema9_trend_risk_5m.example.yaml`. 10-share sibling: `config/ema9_trend_bracket.example.yaml`. Named copies: `config/ema9_trend_bracket_nobe_range3_fixed1.example.yaml` / `config/ema9_trend_risk_nobe_range3_fixed1.example.yaml`.

## Book

- **Long-only** AAPL+MSFT
- Entry: price crosses above EMA(9), close > SMA(20), RSI(14) < 70
- Gates: `entry_cutoff` 12:00 ET, `flatten_by` 15:55 ET
- Exit (whichever first):
  1. Hard stop at **fill × 0.99** (`stop_mode: entry_pct`; never trails or lock-at-+1%)
  2. Completed bar after the fill has range (high − low) **strictly greater than** max of the previous 3 bars; fill at **that bar’s close**. Not armed on the entry/fill bar
  3. Session flatten 15:55
- Same-bar stop + range → **stop**. Same-bar range + flatten (no stop) → `range_expansion`
- No MA-cross exit, no `lock_plus`, no half-take, no pyramid, no volume filter

Pure range3 (no percent stop) stays as a comparison example: `config/ema9_trend_bracket_nobe_range3.example.yaml` / `config/ema9_trend_risk_nobe_range3.example.yaml`. MA-cross at close stays as `config/ema9_trend_bracket_nobe_macross.example.yaml` / `config/ema9_trend_risk_nobe_macross.example.yaml`. Prior adoption notes: `artifacts/ema9_range3_adopted.md`, `artifacts/ema9_macross_adopted.md`.

## Why this exit

Recorded Yahoo 15m AAPL+MSFT, 2026-06-25 → 2026-09-18, $100k, $0 friction. Not re-run for this adoption. Head-to-head: `artifacts/ema9_range3_fixed1.md`.

| Book | 10-share | August 2026 1% risk |
| --- | --- | --- |
| A then-locked pure range>last-3 | **54 / 75.93% / $696.66**, DD $115.38 | **16 / 87.50% / $6,008.19**, DD $2,028.83 |
| F range>last-3 + hard 1% | **55 / 74.55% / $682.32**, DD $99.05 | **identical** (0 stops) |

F does **not** beat A on P&L ($14.34 behind on 10-share). It only slightly costs pure range3 and cuts max DD. August is unchanged. Adopted because the user prioritizes protection.

## Paper / live adapters already in the repo

Updated when the Tradier sandbox path landed (`config/ema9_trend_tradier_sandbox.example.yaml`).

| Piece | What exists | What does not |
| --- | --- | --- |
| Broker | `AlpacaBroker` in `dta_bot/broker.py` — paper URL `https://paper-api.alpaca.markets` by default; live only if `allow_live` + `ALPACA_LIVE_TRADING` + `ALPACA_ALLOW_LIVE=I_UNDERSTAND`. Account, positions, market/limit, optional Alpaca **bracket** stop/take, cancel, `close_position`. `TradierBroker` in `dta_bot/tradier.py` — sandbox `https://sandbox.tradier.com/v1` by default; live `https://api.tradier.com/v1` only if `allow_live` + `TRADIER_LIVE_TRADING` + `TRADIER_ALLOW_LIVE=I_UNDERSTAND` + `tradier_endpoint: production`. Account, positions, list/place/cancel equity orders, preview, close. Entry+stop is market then a separate opposite-side `type=stop` (no Tradier bracket). | No IBKR, Schwab, or other brokers. |
| Dry-run | `DryRunBroker` wraps Alpaca or Tradier (or runs offline) and never sends orders. `build_broker()` is the only factory. | — |
| Keys | `ALPACA_API_KEY` / `ALPACA_API_SECRET` (or `APCA_*`). `TRADIER_ACCESS_TOKEN` / `TRADIER_ACCOUNT_ID` (placeholders in `.env.example` only). | Repo never ships real tokens. CI does not call Tradier. |
| Live bars | `AlpacaMarketData` (IEX), `YahooMarketData` (same Yahoo chart as backtest), `TradierMarketData` (timesales 1m/5m/15m + daily history), `FixtureMarketData`. `settings.data_source`: `alpaca` / `yahoo` / `tradier`. | Sandbox timesales is often empty — locked Tradier example uses **Yahoo bars + Tradier orders**. |
| Runner | `dta_bot run` / `evaluate`: noon entry, `range_expansion` flatten on the next poll after the expansion bar closes, `session_flatten` at `flatten_by`, kill switch. If `stop_loss_pct` is set, `bracket_prices()` attaches a stop on the entry order (Alpaca bracket or Tradier stop). | `lock_plus` / pyramid / half-take are backtest-only (live does not auto-add or scale out). |

## What a paper runner of this locked config needs

**Alpaca paper**

1. Copy `config/ema9_trend.example.yaml` → `config/ema9_trend.yaml` (gitignored). Keep `paper: true`, `allow_live: false`. Set `dry_run: false` or pass `--live-orders` (still Alpaca **paper** unless the live triple-gate is set).
2. Alpaca **paper** keys in `.env`. IEX feed is the default tape; it will not match the Yahoo backtest cache.
3. `python -m dta_bot run --config config/ema9_trend.yaml` (or `--once`). Poll is 60s. Kill switch: `data/KILL` or `DTA_KILL_SWITCH=1`.

**Tradier sandbox**

1. Token + account id from [web.tradier.com/user/api](https://web.tradier.com/user/api) into `.env` (`TRADIER_ACCESS_TOKEN`, `TRADIER_ACCOUNT_ID`).
2. `python -m dta_bot run --config config/ema9_trend_tradier_sandbox.example.yaml --live-orders` (sandbox unless the Tradier live triple-gate is set). Bars are Yahoo.
3. This repo does not verify that a given token works.

**Gaps vs backtest (both brokers)**

4. **Stop gap:** the paper order’s stop is `last_price × 0.99` at submit time (`bracket_prices` uses the signal-bar last, not the next-bar fill). Backtest `entry_pct` rebases to fill × 0.99 after the fill.
5. **Range / flatten fill gap:** live range exit is a **market** `close_position` on the next poll after the expansion bar closes — not that bar’s close. Session flatten is the same poll/clock path. Tradier `close_position` cancels open symbol orders (the stop) then markets out.
6. Risk sibling: `config/ema9_trend_risk.example.yaml` sizes from broker equity at the 1% stop. Same runner, same gaps. No separate Tradier risk YAML — copy and set `broker: tradier`.
