# Daily Trade Assistant

Personal stock trading companion with two parts that share this repo:

1. **Journal (browser)** — pre-market checklist, live session logging, post-market review, and performance stats. Data stays in `localStorage`.
2. **Paper rules bot (CLI)** — evaluates human-editable YAML rules (including candlestick patterns on specific timeframes) and can place **Alpaca paper** orders. Live trading is off by default and hard to enable by accident.

---

## Journal (existing)

- **Pre-Market** — Checklist + watchlist/levels + daily plan notes
- **Market Open** — Quick trade logger + today's trades + session notes
- **Post-Market** — Review checklist + daily summary journal
- **Performance** — Win rate, total P&L, average win/loss, cumulative P&L chart, full trade log

All journal data is stored **locally in your browser**. Nothing is sent anywhere.

### How to use the journal

1. Open `index.html` in any modern browser (Chrome, Firefox, Edge, Safari).
2. Or serve it locally:

   ```bash
   npx serve .
   ```

3. Start checking off your pre-market items and logging trades.

**Export / Backup** — use the **Export** button in the header to download a JSON backup.

**Reset** — the **Reset** button clears everything. Use carefully.

---

## Paper-trading rules bot

Python package `dta_bot`. Rules live in YAML (or JSON), not in code. The runner logs **why** every rule matched or missed (pattern, bars, SMA/RSI/volume) and **why** it would buy, sell, or flatten.

### Features

- Alpaca **paper** client: account, positions, market/limit orders (optional bracket stop/take), cancel, close.
- OHLCV bars from Alpaca market data (IEX by default) or a local fixture file.
- Candlestick detectors on the last N **closed** bars of a timeframe (`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`):
  bullish/bearish engulfing, hammer, inverted hammer, shooting star, doji, morning star, evening star, three white soldiers, three black crows.
- Rule engine: nested **AND** (`all`) / **OR** (`any`), pattern + SMA/EMA + EMA/SMA **cross** + RSI + volume, symbol universe, per-symbol cooldown, idempotent (same bar cannot fire twice).
- CLI scheduler (`run`) or one-shot (`evaluate` / `run --once`).
- Kill switch that stops **new orders** immediately.
- Secrets via environment variables only.

### Get Alpaca paper keys

1. Create a free account at [alpaca.markets](https://alpaca.markets).
2. Open the **Paper Trading** dashboard: [app.alpaca.markets/paper/dashboard/overview](https://app.alpaca.markets/paper/dashboard/overview).
3. Generate an API key pair. These keys only talk to `https://paper-api.alpaca.markets`.
4. Copy `.env.example` to `.env` and set `ALPACA_API_KEY` / `ALPACA_API_SECRET`. Never commit `.env`.

Paper accounts typically receive the **IEX** market-data feed (`settings.data_feed: iex`).

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# or: pip install -e ".[dev]"
cp .env.example .env   # then paste paper keys
```

### Paper mode (default)

The trading URL is `https://paper-api.alpaca.markets` unless **all** of the following are set (any missing piece stays on paper):

| Gate | Default |
|------|---------|
| `settings.allow_live` in YAML | `false` |
| env `ALPACA_LIVE_TRADING` | unset / false |
| env `ALPACA_ALLOW_LIVE` | must equal `I_UNDERSTAND` |
| API keys | must be **live** keys if you somehow pass the gates |

Do not invent or commit live brokerage credentials. This repo never ships any.

### Dry-run without placing orders

The example config has `dry_run: true`. `evaluate` is always dry-run.

**No API keys needed** — use the bundled synthetic bars (two of the three sample rules fire):

```bash
python -m dta_bot evaluate --config config/rules.example.yaml --fixture config/sample_bars.json
```

With paper keys, evaluate against live IEX bars but still do not order:

```bash
python -m dta_bot evaluate --config config/rules.example.yaml
# or
python -m dta_bot run --config config/rules.example.yaml --once --dry-run
```

You should see `[FIRE]` / `[NO]` lines that name the rule, pattern, timeframe, and the exact OHLC bars.

To actually submit **paper** orders: set `dry_run: false` in YAML **or** pass `--live-orders` (still paper unless the live gates above pass).

```bash
python -m dta_bot run --config config/rules.yaml --live-orders
```

### Kill switch / pause

Stops new orders immediately (evaluations still log what *would* have fired):

```bash
python -m dta_bot pause --config config/rules.example.yaml
# creates data/KILL

python -m dta_bot resume --config config/rules.example.yaml
```

Or set `DTA_KILL_SWITCH=1` in the environment. Either the file or the env flag is enough.

### Add a rule

1. Copy `config/rules.example.yaml` to `config/rules.yaml` (gitignored).
2. Add an entry under `rules:` with a unique `id`.
3. `python -m dta_bot validate --config config/rules.yaml`
4. Dry-run once, then enable orders only when you are happy with the logs.

```yaml
  - id: my-doji-fade
    enabled: true
    symbols: [SPY]
    cooldown_minutes: 45
    when:
      all:
        - pattern: doji
          timeframe: 5m
        - ema:
            period: 9
            timeframe: 5m
            compare: below
        - ema_cross:
            period: 9
            timeframe: 5m
            direction: bearish
        - rsi:
            period: 14
            timeframe: 5m
            above: 60
    action:
      type: sell
      size: { type: percent_equity, value: 1 }
      order: market
      stop_loss_pct: 0.8
      take_profit_pct: 1.2
```

### Rule config schema

```yaml
settings:
  paper: true
  allow_live: false          # keep false
  dry_run: true
  poll_interval_seconds: 60
  kill_switch_file: data/KILL
  state_file: data/state.json
  max_open_positions: 5
  data_feed: iex
  lookback_bars: 80
  session_timezone: America/New_York   # optional session clock
  entry_cutoff: "12:00"                # skip fills at/after this clock; null = off
  flatten_by: "15:55"                  # force-flat at flatten-bar close; null = off

universe: [AAPL, MSFT, SPY]  # default symbols; a rule may override

rules:
  - id: unique-name
    enabled: true
    symbols: [AAPL]          # optional
    cooldown_minutes: 60     # per rule+symbol after a fire
    when:                    # AND/OR tree
      all:                   # every child
        - pattern: bullish_engulfing
          timeframe: 15m
        - sma: { period: 20, timeframe: 15m, compare: above }   # or ema
        - ema_cross: { period: 9, timeframe: 15m, direction: bullish }  # or sma_cross
        - rsi: { period: 14, timeframe: 15m, below: 70 }        # above and/or below
        - volume: { period: 20, timeframe: 15m, multiplier: 1.2 }
      # any: [ ... ]         # OR; groups nest
    action:
      type: buy | sell | close
      size: { type: shares | percent_equity | risk_pct, value: 10 }  # required for buy/sell
      # risk_pct: { type: risk_pct, equity_risk: 0.01, stop_pct: 1.5 }
      #   shares = floor( (equity_risk * equity) / ((stop_pct/100) * price) )
      order: market | limit
      limit_offset_pct: 0.05
      exit: ema_invalid | fixed_bracket   # default fixed_bracket
      exit_ema_period: 9                  # used when exit is ema_invalid
      stop_loss_pct: 1.5     # optional; catastrophic-only when exit is ema_invalid
      take_profit_pct: 3.0   # ignored when exit is ema_invalid
      breakeven_after_bars: 1            # 0/omit = off; 1 = next full candle after fill
      breakeven_requires_valid: true     # only arm if evaluation bar is still valid
      breakeven_valid: above_ema         # long: close > EMA(9); or always
```

**Patterns:** `doji`, `bullish_engulfing`, `bearish_engulfing`, `hammer`, `inverted_hammer`, `shooting_star`, `morning_star`, `evening_star`, `three_white_soldiers`, `three_black_crows`.

**MA cross:** `ema_cross` / `sma_cross` with `direction: bullish` or `bearish`. Bullish = previous close ≤ previous MA and current close > current MA (each MA is computed through that bar). Level compares (`sma` / `ema` + `compare: above|below`) still mean “close vs the current MA only.”

`python -m dta_bot patterns` prints the list. Detectors always use **closed** bars (the in-progress candle is dropped).

### 9 EMA trend (sample strategy)

`config/ema9_trend.example.yaml` is a long-only book on **AAPL / MSFT**. SOXL is optional (`config/ema9_trend_bracket_soxl.example.yaml`, `config/ema9_trend_risk_soxl.example.yaml`). Entry reuses the engulfing-with-trend filter: close above SMA(20), RSI(14) below 70, buy 10 shares, 60-minute **wall-clock** cooldown. The trigger is a bullish **EMA(9) cross** instead of a bullish engulfing candle.

Default exit is **`action.exit: ema_invalid`**: stay in the long until a signal-timeframe bar **closes < EMA(9)** and flatten at that close. Close == EMA9 stays valid. There is no 1.5%/3.0% bracket on the 9 EMA rules. Optional `stop_loss_pct` is a catastrophic stop only and is **off** in the example configs. Set `exit: fixed_bracket` plus `stop_loss_pct` / `take_profit_pct` to restore the old brackets. Paper / `dry_run` defaults; no live.

**Session gates** (America/New_York, on in the ema9 example configs):

- `entry_cutoff: "12:00"` — skip a signal when the next-bar **fill** (bar open) would be at/after noon ET. Prior gated books: `13:00` (`config/ema9_trend_bracket_1300.example.yaml`) and `15:15` (`config/ema9_trend_bracket_1515.example.yaml`).
- `flatten_by: "15:55"` — force-flat at the close of the bar that contains 3:55 PM ET. On **15m** RTH bars opening `:00,:15,:30,:45` that is the **15:45 ET bar close** (last regular 15m bar before 16:00, labeled as the end-of-day flatten aligned with “by 15:55”). On **5m** that is the **15:50 ET bar close** (last 5m bar that completes at/before 15:55). Stop/take/EMA-invalid on that bar still win if they hit first. Exit reason: `session_flatten`.
- Set either knob to `null` / `off` to disable it (overnight control: `config/ema9_trend_bracket_overnight.example.yaml`).

The 10-share and 1% risk books (`config/ema9_trend_bracket.example.yaml`, `config/ema9_trend_risk.example.yaml`) keep **`exit: fixed_bracket`** (initial stop 1.5% / take 3.0%) plus a **one-bar break-even**: after the fill, wait for one complete signal-timeframe bar after the entry bar; at that close, if the long is still valid (`close > EMA(9)`), move the stop to entry and leave it there. If not valid, keep the 1.5% stop. Prior 12:00 book without BE: `config/ema9_trend_bracket_nobe.example.yaml`.

`config/ema9_trend_risk.example.yaml` is the same 15m entry on **AAPL / MSFT only** and sizes each long to risk ~1% of current equity at the 1.5% stop (`size.type: risk_pct`). Both names may be open at once when cash covers the second notional; otherwise the later signal is skipped. `--start` / `--end` bound the trade window (prior bars stay for SMA/RSI/EMA warmup):

```bash
python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --source yahoo \
  --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk.json --report artifacts/ema9_aug2026_risk.md
```

The 10-share control on the same window is `config/ema9_trend_bracket.example.yaml`.

Bar size is `settings.timeframe` (default **15m**). The same rules on 5-minute bars (every indicator on 5m; cooldown still 60 minutes):

```bash
python -m dta_bot backtest --config config/ema9_trend.example.yaml --timeframe 5m --source yahoo
# or
python -m dta_bot backtest --config config/ema9_trend_5m.example.yaml --source yahoo \
  --output artifacts/ema9_ema_invalid_5m.json --report artifacts/ema9_ema_invalid_5m.md
```

The same file also ships `ema9_cross_raw` (cross, no trend filter, same EMA-invalid exit) and `engulfing-with-trend` (the control, still 1.5/3.0 brackets) so one backtest is a head-to-head on the same tape:

```bash
python -m dta_bot validate --config config/ema9_trend.example.yaml
python -m dta_bot backtest --config config/ema9_trend.example.yaml --source yahoo \
  --output artifacts/ema9_ema_invalid.json --report artifacts/ema9_ema_invalid.md
```

Copy to `config/ema9_trend.yaml` or `config/ema9_trend_5m.yaml` (gitignored) and disable the ablation/control rules if you only want to paper the 9 EMA book.

On the Yahoo window 2026-06-17 → 2026-09-11, **EMA-invalidation** isolated books were: **15m AAPL/MSFT/SOXL 240 trades, 36.25%, $626.64**, max DD $850.25; **5m AAPL/MSFT/SOXL 498 trades, 30.72%, $-312.80**, max DD $722.18. Isolated SOXL: 15m 86 trades, 29.07%, $-835.05; 5m 170 trades, 28.24%, $-707.46. AAPL/MSFT only (same exit): 15m 154 / 40.26% / $1,461.69; 5m 328 / 32.01% / $394.66. Writeup: `artifacts/ema9_ema_invalid_5m_vs_15m.md`.

August 2026 only (2026-08-01 → 2026-08-31 RTH, same Yahoo 15m tape, AAPL/MSFT, `exit: fixed_bracket` 1.5/3.0, one-bar BE, $100k start) **with 12:00 / 15:55 session gates**: **1% equity-risk 16 trades, 31.25%, $3,188.15**, max DD $1,058.87, **15 of 16 armed BE**, **11 `breakeven_stop`**, 5 `session_flatten`. Prior 12:00 August without BE: 15 trades, 73.33%, $3,194.05, max DD $1,676.30. Prior 15:15 gated August: 19 trades, 68.42%, $2,595.50, max DD $1,668.34. Prior 13:00 gated August: 17 trades, 70.59%, $3,022.49, max DD $1,663.57. Prior overnight August (gates off): 7 trades, 57.14%, $5,502.59, max DD $3,282.83. Adding SOXL to the August 1% book (pre-BE writeup): **24 trades, 45.83%, $-4,120.21**, max DD $5,533.16 (isolated SOXL 15 trades, 13.33%, $-6,805.96). Writeups: `artifacts/ema9_aug2026_risk.md`, `artifacts/ema9_aug2026_risk_soxl.md`.

Full-window **15m 10-share** AAPL/MSFT (1.5/3.0) on the same tape 2026-06-17 → 2026-09-11: overnight **44 trades, 50.00%, $1,404.89**, max DD $407.70 (reproduced); 13:00 / 15:55 **64 trades, 60.94%, $419.25**, max DD $298.92, **54 of 64 `session_flatten`**, 33 `entry_cutoff` skips (reproduced); 15:15 / 15:55 **83 trades, 55.42%, $380.60**, max DD $298.92, **72 of 83 `session_flatten`**, 8 `entry_cutoff` skips (reproduced); **12:00 / 15:55 without BE 50 trades, 62.00%, $453.00**, max DD $207.70, **41 of 50 `session_flatten`**, 55 `entry_cutoff` skips (reproduced); **12:00 / 15:55 + one-bar BE 51 trades, 31.37%, $349.70**, max DD $199.67, **40 armed BE / 27 `breakeven_stop`**, 19 `session_flatten`. Same window with SOXL added (pre-BE writeup): **86 trades, 47.67%, $572.83**, max DD $225.05 (isolated SOXL 36 trades, 27.78%, $119.83). Writeups: `artifacts/ema9_breakeven.md`, `artifacts/ema9_session_gates.md`, `artifacts/ema9_session_gates_soxl.md`.

Prior **fixed-bracket** AAPL/MSFT books (1.5/3.0, overnight) on the same tape: **15m 44 trades, 50.00%, $1,404.89**; **5m 56 trades, 48.21%, $1,305.23**. Writeups: `artifacts/ema9_vs_engulfing.md`, `artifacts/ema9_5m_vs_15m.md`. Yahoo 5m/15m history is still documented as a ~60-day cap.

### CLI

```bash
python -m dta_bot validate --config config/rules.example.yaml
python -m dta_bot status --config config/rules.example.yaml
python -m dta_bot evaluate --config config/rules.example.yaml --fixture config/sample_bars.json
python -m dta_bot run --once --dry-run
python -m dta_bot run                    # interval loop; honors yaml dry_run
python -m dta_bot pause
python -m dta_bot resume
python -m dta_bot patterns
```

After `pip install -e .` the same commands work as `dta-bot ...`.

State (cooldowns + last-fired bar keys) is stored in `data/state.json` so a restart will not double-fire the same candle.

### Tests

```bash
python -m pytest
```

Unit tests cover every pattern (synthetic OHLC), AND/OR + cooldown + idempotency, example-config load, sizing, kill switch, the paper/live URL gates, and the ORB edge-fade state machine (zones, probe/reversal, entry/stop/target).

---

## ORB edge-fade / reversal

A second YAML strategy (`strategy: orb_reversal`) fades failed probes of the opening-range high/low. It uses dedicated helpers (OR builder, edge zones, probe → reversal state machine) and the same paper/live gates, sizing, broker, and backtest fill simulator as the rules bot.

### Rules (v1, locked)

1. **Opening range** — first `orb_timeframe` candle at or after US RTH open **9:30 America/New_York**. Default **15m** (9:30–9:45 ET high/low). Change `orb.orb_timeframe` to `5m` / `15m` / `30m` in YAML; no code change.
2. After that candle is fully formed, evaluate **`signal_timeframe`** bars (default **5m**).
3. **Probe** — default `orb.probe_mode: touch_and_band`: the signal bar must **touch** the OR extreme **and** **close** inside the edge band (`edge_pct`, default `0.05` of OR height). Top (potential short): `high >= or_high` and close in `[or_high - band, or_high]`. Bottom (potential long): `low <= or_low` and close in `[or_low, or_low + band]`. Set `probe_mode: touch` for the wick-only rule (close-in-band not required). Set `probe_mode: edge_band` to restore the previous close-in-zone rule without requiring a touch.
4. **Reversal** — the **next** signal bar, opposite color: top + bearish → **short**; bottom + bullish → **long**. Same-color or doji = no trade. Default `orb.reversal_in_range: close` also requires `or_low <= close <= or_high`. If the reversal closes outside the OR, do not enter. Set `body` to require high and low both inside the OR (stricter fully-inside mode). Set `off` to skip the in-range filter.
5. **EMA filter** — default `orb.ema_filter: true`, `orb.ema_period: 9`. Compute EMA(period) on **signal-timeframe** closes through the reversal bar (inclusive). Long: reversal `close > ema9`; short: `close < ema9`. Set `ema_require_open: true` to also require the reversal open on the same side of the EMA (default is close only). If EMA cannot be computed (fewer than `ema_period` closes), skip the entry. Set `ema_filter: false` to disable.
6. **Entry** — fill at the **open of the bar after the reversal**.
7. **Stop** — default `orb.stop_mode: orb_extreme`: long → opening-range low; short → opening-range high. Set `reversal_candle` to restore the previous stop at the reversal candle extreme.
8. **Take profit** — default `orb.take_profit_mode: ema_cross`: exit at the close of the first signal-timeframe bar after entry whose close is on the other side of the same EMA used by the entry filter (long: `close < ema9`; short: `close > ema9`). Set `or_midpoint` for `(or_high + or_low) / 2`. Set `one_r` for a 1R target (R = |entry − stop|; long TP = entry + R; short TP = entry − R). Set `first_profitable_close` to exit at the close of the first signal-timeframe bar that is strictly profitable vs entry (long: `close > entry`; short: `close < entry`). If stop and take (EMA-cross, 1R, midpoint, or first-profit) both trade on the same bar, the stop fills first.
9. **High-vol gate** — default `orb.min_or_height_pct: 0.01` (1%). Trade only when `(or_high − or_low) / or_open >= 1%`. Denominator is the **OR candle open**; if that print is missing, fall back to the **OR midpoint**. Below the threshold, skip the symbol for that session (no entries). Set `0` / `null` to disable.
10. **Frequency** — default is **at most one entry per symbol per session, and only if that entry is before 10:30 America/New_York** (`entry_cutoff: "10:30"`, `max_trades_before_cutoff: 1`, `allow_entries_after_cutoff: false`). No new entries at/after 10:30. Still **one open position per symbol**; a new signal is **skipped** while that symbol is still in a trade (`orb.on_open_position: skip`). Set `replace` to close/replace. Set `allow_entries_after_cutoff: true` to also take post-cutoff signals, or `entry_cutoff: null` to drop the clock gate.
11. **Universe** — YAML list (example: AAPL, MSFT, SPY, SOXL). A morning screener will populate this later; edit the list by hand for now.

Paper-only defaults: `settings.paper: true`, `allow_live: false`, `dry_run: true`. Live trading still requires the same triple gate as the rules bot.

### Configure symbols and knobs

Copy `config/orb_reversal.example.yaml` to `config/orb_reversal.yaml` (gitignored) and edit:

```yaml
universe:
  - AAPL
  - MSFT
  - SPY
  - SOXL
  # add/remove tickers; a morning screener will populate this later

orb:
  session_open: "09:30"
  session_timezone: America/New_York
  orb_timeframe: 15m          # 5m / 15m / 30m
  signal_timeframe: 5m
  probe_mode: touch_and_band  # touch_and_band | touch | edge_band
  edge_pct: 0.05              # used by touch_and_band / edge_band; fraction of OR height (not "5")
  on_open_position: skip      # skip | replace
  reversal_in_range: close    # close | body | off
  take_profit_mode: ema_cross    # ema_cross | or_midpoint | one_r | first_profitable_close
  ema_filter: true            # reversal close vs EMA(ema_period) on signal TF
  ema_period: 9
  ema_require_open: false     # also require open on the same side of the EMA
  stop_mode: orb_extreme      # orb_extreme | reversal_candle
  min_or_height_pct: 0.01     # 1% of OR open; 0 / null disables
  entry_cutoff: "10:30"       # America/New_York; null disables the clock gate
  max_trades_before_cutoff: 1 # per symbol per session
  allow_entries_after_cutoff: false

sizing:
  type: shares                # or percent_equity
  value: 10
```

### Dry-run on the bundled fixture (no API keys)

```bash
python -m dta_bot validate --config config/orb_reversal.example.yaml
python -m dta_bot evaluate --config config/orb_reversal.example.yaml --fixture config/orb_sample_bars.json
python -m dta_bot backtest --config config/orb_reversal.example.yaml --fixture config/orb_sample_bars.json
```

The sample tape is one RTH Friday: **AAPL** top-edge hybrid probe fade short (touch OR high and close in the 5% band; reversal close inside the OR and below EMA9; stop = opening-range high 104; take = first post-entry 5m close above EMA9), **MSFT** bottom-edge hybrid probe fade long (touch OR low and close in the 5% band; reversal close inside the OR and above EMA9; stop = opening-range low 200; take = first post-entry 5m close below EMA9), **SPY** no trade (no qualifying probe, then a same-color “reversal”). Both fixture entries are before 10:30 ET, so they pass the default morning gate.

Yahoo (no Alpaca keys) or Alpaca paper data:

```bash
python -m dta_bot backtest --config config/orb_reversal.example.yaml --source yahoo
```

Compare ORB with the three sample rules on one report (separate books — the engines do not share positions):

```bash
python -m dta_bot backtest \
  --config config/orb_reversal.example.yaml \
  --compare-config config/rules.example.yaml \
  --source yahoo \
  --starting-equity 100000 \
  --output artifacts/orb_vs_sample_comparison.json \
  --report artifacts/orb_vs_sample_comparison.md
```

Yahoo history is short on fast bars: **5m/15m/30m ≈ 60 days**, **1h ≈ 2 years**. ORB needs 15m for the opening range and 5m for signals, so its longest reliable Yahoo window is that 60-day cap. The 1h hammer book can look back further; P&L% is not time-normalized across books.

`evaluate` scans the whole fixture and prints `[FIRE]` / `[NO]`. The live/paper `run` loop only acts when the **latest closed signal bar is the reversal** (so a market order lands on the next bar’s open). `run` still defaults to dry-run unless you pass `--live-orders` (paper unless the live gates are set).

---

Built as a private personal tool. The journal has no backend. The bot talks only to Alpaca when you give it keys, and only to the **paper** endpoint unless you deliberately unlock live trading.
