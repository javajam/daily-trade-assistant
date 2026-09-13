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

Unit tests cover every pattern (synthetic OHLC), AND/OR + cooldown + idempotency, example-config load, sizing, kill switch, and the paper/live URL gates.

---

Built as a private personal tool. The journal has no backend. The bot talks only to Alpaca when you give it keys, and only to the **paper** endpoint unless you deliberately unlock live trading.
