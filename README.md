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
- Rule engine: nested **AND** (`all`) / **OR** (`any`), pattern + SMA/EMA + RSI + volume, symbol universe, per-symbol cooldown, idempotent (same bar cannot fire twice).
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
        - rsi: { period: 14, timeframe: 15m, below: 70 }        # above and/or below
        - volume: { period: 20, timeframe: 15m, multiplier: 1.2 }
      # any: [ ... ]         # OR; groups nest
    action:
      type: buy | sell | close
      size: { type: shares | percent_equity, value: 10 }  # required for buy/sell
      order: market | limit
      limit_offset_pct: 0.05
      stop_loss_pct: 1.5     # optional Alpaca bracket
      take_profit_pct: 3.0
```

**Patterns:** `doji`, `bullish_engulfing`, `bearish_engulfing`, `hammer`, `inverted_hammer`, `shooting_star`, `morning_star`, `evening_star`, `three_white_soldiers`, `three_black_crows`.

`python -m dta_bot patterns` prints the list. Detectors always use **closed** bars (the in-progress candle is dropped).

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
5. **Entry** — fill at the **open of the bar after the reversal**.
6. **Stop** — default `orb.stop_mode: orb_extreme`: long → opening-range low; short → opening-range high. Set `reversal_candle` to restore the previous stop at the reversal candle extreme.
7. **Take profit** — default `orb.take_profit_mode: first_profitable_close`: after entry, exit at the close of the first signal-timeframe bar that is strictly profitable vs entry (long: `close > entry`; short: `close < entry`). Set `or_midpoint` to restore the previous OR-midpoint target. If stop and first-profit (or midpoint) both trade on the same bar, the stop fills first.
8. **Frequency** — default is **at most one entry per symbol per session, and only if that entry is before 10:30 America/New_York** (`entry_cutoff: "10:30"`, `max_trades_before_cutoff: 1`, `allow_entries_after_cutoff: false`). No new entries at/after 10:30. Still **one open position per symbol**; a new signal is **skipped** while that symbol is still in a trade (`orb.on_open_position: skip`). Set `replace` to close/replace. Set `allow_entries_after_cutoff: true` to also take post-cutoff signals, or `entry_cutoff: null` to drop the clock gate.
9. **Universe** — YAML list (example: AAPL, MSFT, SPY). A morning screener will populate this later; edit the list by hand for now.

Paper-only defaults: `settings.paper: true`, `allow_live: false`, `dry_run: true`. Live trading still requires the same triple gate as the rules bot.

### Configure symbols and knobs

Copy `config/orb_reversal.example.yaml` to `config/orb_reversal.yaml` (gitignored) and edit:

```yaml
universe:
  - AAPL
  - MSFT
  - SPY
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
  take_profit_mode: first_profitable_close  # first_profitable_close | or_midpoint
  stop_mode: orb_extreme      # orb_extreme | reversal_candle
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

The sample tape is one RTH Friday: **AAPL** top-edge hybrid probe fade short (touch OR high and close in the 5% band; reversal close inside the OR; stop = opening-range high 104; first profitable 5m close is the take), **MSFT** bottom-edge hybrid probe fade long (touch OR low and close in the 5% band; reversal close inside the OR; stop = opening-range low 200; first profitable 5m close is the take), **SPY** no trade (no qualifying probe, then a same-color “reversal”). Both fixture entries are before 10:30 ET, so they pass the default morning gate.

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
