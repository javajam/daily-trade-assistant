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
        - ema_sma_cross: { ema_period: 9, sma_period: 20, timeframe: 15m, direction: bullish }
        - rsi: { period: 14, timeframe: 15m, below: 70 }        # above and/or below
        - volume: { period: 20, timeframe: 15m, multiplier: 1.2 }
        - volume_gt_prev: { timeframe: 15m }  # signal vol > previous bar (alias: volume: { vs: prev })
      # any: [ ... ]         # OR; groups nest
    action:
      type: buy | sell | close
      size: { type: shares | percent_equity | risk_pct, value: 10 }  # required for buy/sell
      # risk_pct: { type: risk_pct, equity_risk: 0.01, stop_pct: 1.5 }
      #   percent stop: shares = floor( (equity_risk * equity) / ((stop_pct/100) * price) )
      #   stop_mode sma20: R = signal-close − SMA20; shares = floor( (equity_risk * equity) / R )
      order: market | limit
      limit_offset_pct: 0.05
      exit: ema_invalid | ma_cross | lower_high | fixed_bracket   # default fixed_bracket
      exit_ema_period: 9                  # ema_invalid / ma_cross (alias: ema_period)
      exit_sma_period: 20                 # ma_cross (alias: sma_period)
      stop_mode: percent | sma20 | entry_pct | lock_plus | trail
      # percent = stop_loss_pct from signal-bar close (legacy)
      # sma20 = SMA at signal bar (fixed; not trailed)
      # entry_pct = stop_loss_pct from the *fill* (next-bar open); never moves
      # lock_plus = entry_pct initial; first touch of entry×(1+lock_trigger_pct/100)
      #   moves stop to entry×(1+lock_stop_pct/100) (live next bar)
      # trail = peak_since_entry × (1−trail_pct/100), ratchets up only
      stop_sma_period: 20                 # used when stop_mode is sma20
      stop_loss_pct: 1.5     # optional; used by percent / entry_pct / lock_plus / trail
      lock_trigger_pct: 1.0  # lock_plus; omit to use stop_loss_pct
      lock_stop_pct: 1.0     # lock_plus; omit to use stop_loss_pct
      trail_pct: 1.0         # trail; omit to use stop_loss_pct
      pyramid_on_lock: false # lock_plus only; add same share count at lock-arm print
      pyramid_add_pct: 0.5   # lock_plus only; add at fill×(1+pct/100), lock still at +lock
      take_anchor: signal    # signal = take from signal close; entry = take from fill
                             # forced to entry when pyramid_on_lock is true
      take_profit_pct: 3.0   # ignored when exit is ema_invalid, ma_cross, or lower_high; omit for stop-only
      breakeven_after_bars: 1            # 0/omit = off; 1 = next full candle after fill
      breakeven_requires_valid: true     # only arm if evaluation bar is still valid
      breakeven_valid: above_ema         # long: close > EMA(9); or always
```

**Patterns:** `doji`, `bullish_engulfing`, `bearish_engulfing`, `hammer`, `inverted_hammer`, `shooting_star`, `morning_star`, `evening_star`, `three_white_soldiers`, `three_black_crows`.

**MA cross:** `ema_cross` / `sma_cross` with `direction: bullish` or `bearish`. Bullish = previous close ≤ previous MA and current close > current MA (each MA is computed through that bar). **EMA vs SMA:** `ema_sma_cross` with `ema_period` / `sma_period` (bullish = previous EMA ≤ previous SMA and current EMA > current SMA). Level compares (`sma` / `ema` + `compare: above|below`) still mean “close vs the current MA only.”

`python -m dta_bot patterns` prints the list. Detectors always use **closed** bars (the in-progress candle is dropped).

### Refined EMA9 day-trade (sample strategy)

`config/ema9_trend.example.yaml` is the **noon day-trade** book on **AAPL / MSFT** (not TSLA/MU, SPY/QQQ, or NVDA/AMD). Default stop management is **lock-+1%**. Both sides are enabled in YAML (`ema9_trend` long + `ema9_trend_short`). One position per symbol — long or short, not both. An opposite signal while that symbol is already in a trade is skipped (`opposite_signal_in_trade`). Disable a side with `enabled: false`. SOXL is optional (`config/ema9_trend_bracket_soxl.example.yaml`, `config/ema9_trend_risk_soxl.example.yaml`). Long-only SPY/QQQ (shorts parked): `config/ema9_trend_spy_qqq.example.yaml` / `config/ema9_trend_risk_spy_qqq.example.yaml`. Long-only NVDA/AMD (shorts parked): `config/ema9_trend_nvda_amd.example.yaml` / `config/ema9_trend_risk_nvda_amd.example.yaml`.

1. **Long entry** — price crosses **above EMA(9)** AND close **> SMA(20)** AND **RSI(14) < 70** on the signal timeframe (default 15m). Fill at the **next bar open**.
2. **Short entry** — price crosses **below EMA(9)** AND close **< SMA(20)**. **No RSI** on shorts. Same fill (next bar open).
3. **Long stop** — `stop_mode: lock_plus` (default on the long). Initial **fill × 0.99**; first touch of **fill × 1.01** (bar high ≥ that print) locks the stop there. The locked stop is live from the **next** bar; a same-bar pullback after the tag still uses the initial 1% stop. A later hit is `lock_stop`.
4. **Short cover / exits** — no `lock_plus` and no percent stop on shorts (`stop_loss_pct` omitted; optional catastrophic stop is off). Cover when **EMA(9) crosses above SMA(20)** (`action.exit: ma_cross`) and flatten at the **next bar open**, or `session_flatten`. Longs have no take-profit: stop / `lock_stop` / `session_flatten`.
5. **Break-even is off** (`breakeven_after_bars` omitted / 0).
6. **Optional stop siblings** (same entry / session): fixed 1% from the fill (`stop_mode: entry_pct`, `config/ema9_trend_bracket_nobe_fixed1.example.yaml`); trail 1% from peak since entry (`stop_mode: trail`, `config/ema9_trend_bracket_nobe_trail1.example.yaml`). Matching 1% risk YAMLs: `config/ema9_trend_risk_nobe_fixed1.example.yaml`, `config/ema9_trend_risk_nobe_trail1.example.yaml` (lock risk is the default `config/ema9_trend_risk.example.yaml`). **Lock-+1% + add-at-+0.5%** (no take: add the same share count at original fill × 1.005, then lock at +1% on the full lot): `config/ema9_trend_bracket_nobe_lock1_add05.example.yaml` / `config/ema9_trend_risk_nobe_lock1_add05.example.yaml`. A bar that gaps through both prints adds first, then locks. Writeup: `artifacts/ema9_lock1_add05.md`. **Lock-+1% + pyramid + 2% fill take** (add the same share count when the +1% lock arms; stop stays at original fill × 1.01 on the full lot; take the entire position at original fill × 1.02; no volume filter): `config/ema9_trend_bracket_nobe_lock1_pyramid2.example.yaml` / `config/ema9_trend_risk_nobe_lock1_pyramid2.example.yaml`. Add fill: open if the bar gaps through fill × 1.01, else the trigger. Cash for the add is not reserved at entry. Live does not auto-add. Same Yahoo 15m AAPL+MSFT tape: 10-share **51 trades, 58.82%, $284.79**, max DD $137.13 vs lock-+1% **51 / 60.78% / $301.49** — all 20 lock-arm events added (0 cash skips); only 1 `take_2pct`. Pyramid+2% does **not** beat lock-+1% on that window. August 2026 1% risk **15 / 73.33% / $6,630.33** vs **15 / 73.33% / $5,489.78**, but **0 of 6 adds filled** (cash skip; the extra is the 2% take on the original lot). Writeup: `artifacts/ema9_lock1_pyramid2.md`. **Lock-+1% + vol>prev only** (same lock exit; signal volume > previous bar): `config/ema9_trend_bracket_nobe_lock1_vol.example.yaml` / `config/ema9_trend_risk_nobe_lock1_vol.example.yaml`. Same tape 10-share **33 trades, 60.61%, $182.91**, max DD $183.54 vs lock-+1% **51 / 60.78% / $301.49** — volume does **not** improve lock-+1% (the 21 filtered fills were net +$152.04). August 1% risk **11 / 72.73% / $3,613.53** vs **15 / 73.33% / $5,489.78**. Writeup: `artifacts/ema9_lock1_vol.md`. **Lower-high + vol>prev** (no lock-+1% / percent stop; signal volume > previous bar; exit at the completed bar close on a lower high): `config/ema9_trend_bracket_nobe_lh_vol.example.yaml` / `config/ema9_trend_risk_nobe_lh_vol.example.yaml`. Risk sizing uses `stop_pct: 1.0` as a reference R only (1% of entry). Same Yahoo 15m AAPL+MSFT tape: 10-share **34 trades, 55.88%, $130.91**, max DD $179.48 (all 34 `lower_high`; 0 flatten) vs lock-+1% **51 / 60.78% / $301.49**. August 2026 1% risk **12 trades, 58.33%, $1,059.41**, max DD $881.79 vs lock-+1% **15 / 73.33% / $5,489.78**. Writeup: `artifacts/ema9_lh_vol.md`.
7. **Prior pair-cross product** — EMA(9) crosses over SMA(20), flatten next open on cross-under, 1.5% stop: `config/ema9_trend_pair.example.yaml`. 1% risk / 5m siblings: `config/ema9_trend_risk_pair.example.yaml`, `config/ema9_trend_5m_pair.example.yaml`. Optional RSI on that pair-cross: `config/ema9_trend_bracket_rsi.example.yaml` / `config/ema9_trend_bracket_rsi60.example.yaml`. Older noon 1.5/3.0 brackets: `config/ema9_trend_bracket_nobe.example.yaml`. Tight 1.0/2.0 (`stop_mode: percent`): `config/ema9_trend_bracket_nobe_12.example.yaml`. **SMA20 stop** (`stop_mode: sma20`): `config/ema9_trend_bracket_sma20.example.yaml` / `config/ema9_trend_bracket_sma20_notake.example.yaml`. Writeups: `artifacts/ema9_stop_manage.md`, `artifacts/ema9_lock_5m_vs_15m.md`, `artifacts/ema9_aug2026_risk_stop_manage.md`.

YAML fields (long): `stop_mode: lock_plus`, `stop_loss_pct: 1.0`, `lock_trigger_pct: 1.0`, `lock_stop_pct: 1.0`. Shorts omit those and set `exit: ma_cross`. Paper / `dry_run` defaults; no live. 60-minute wall-clock cooldown.

**Session gates** (America/New_York, on in the ema9 example configs — set either to `null` / `off` to disable):

- `entry_cutoff: "12:00"` — skip a signal when the next-bar **fill** (bar open) would be at/after noon ET. Prior gated books: `13:00` (`config/ema9_trend_bracket_1300.example.yaml`) and `15:15` (`config/ema9_trend_bracket_1515.example.yaml`).
- `flatten_by: "15:55"` — force-flat at the close of the bar that contains 3:55 PM ET. On **15m** RTH bars opening `:00,:15,:30,:45` that is the **15:45 ET bar close** (last regular 15m bar before 16:00, labeled as the end-of-day flatten aligned with “by 15:55”). On **5m** that is the **15:50 ET bar close** (last 5m bar that completes at/before 15:55). Stop / EMA-invalid / a same-bar MA-cross signal still win if they hit first; MA-cross fills at the next open, so a flatten-bar close is `session_flatten`. Exit reason: `session_flatten`.
- Overnight control: `config/ema9_trend_bracket_overnight.example.yaml`.

`config/ema9_trend_risk.example.yaml` is the same 15m noon long + short + lock-+1% on **AAPL / MSFT only** and sizes each entry to risk ~1% of current equity at the 1.0% initial fill stop (`size.type: risk_pct`). Both names may be open at once when cash covers the second notional; otherwise the later signal is skipped. One position per symbol (long or short). `--start` / `--end` bound the trade window (prior bars stay for SMA/EMA warmup):

```bash
python -m dta_bot backtest --config config/ema9_trend_risk.example.yaml --source yahoo \
  --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk.json --report artifacts/ema9_aug2026_risk.md
```

The 10-share control on the same window is `config/ema9_trend_bracket.example.yaml` (same as `config/ema9_trend.example.yaml`). The 5m 1% sibling is `config/ema9_trend_risk_5m.example.yaml`. The prior pair-cross 1% book with the RSI14 < 70 filter is `config/ema9_trend_risk_rsi.example.yaml`.

Bar size is `settings.timeframe` (default **15m**). The same rules on 5-minute bars (every indicator on 5m; cooldown still 60 minutes; `flatten_by` 15:55 maps to the **15:50 ET** 5m bar close):

```bash
python -m dta_bot backtest --config config/ema9_trend.example.yaml --timeframe 5m --source yahoo
# or
python -m dta_bot backtest --config config/ema9_trend.example.yaml \
  --compare-config config/ema9_trend_5m.example.yaml --source yahoo \
  --combined-only --symbols AAPL,MSFT \
  --output artifacts/ema9_lock_5m_vs_15m.json --report artifacts/ema9_lock_5m_vs_15m.md
```

```bash
python -m dta_bot validate --config config/ema9_trend.example.yaml
python -m dta_bot backtest --config config/ema9_trend.example.yaml --source yahoo \
  --output artifacts/ema9_long_short_15m.json --report artifacts/ema9_long_short_15m.md
```

Copy to `config/ema9_trend.yaml` or `config/ema9_trend_5m.yaml` (gitignored) to paper the default lock-+1% long+short book. Long-only SPY/QQQ (shorts parked):

```bash
python -m dta_bot validate --config config/ema9_trend_spy_qqq.example.yaml
python -m dta_bot backtest --config config/ema9_trend_spy_qqq.example.yaml --source yahoo \
  --compare-config config/ema9_trend_bracket.example.yaml --combined-only \
  --output artifacts/ema9_spy_qqq_15m.json --report artifacts/ema9_spy_qqq_15m.md
python -m dta_bot backtest --config config/ema9_trend_risk_spy_qqq.example.yaml --source yahoo \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk_spy_qqq.json --report artifacts/ema9_aug2026_risk_spy_qqq.md
```

Long-only NVDA/AMD (shorts parked), same noon stack, compared to AAPL+MSFT and SPY+QQQ on the same tape:

```bash
python -m dta_bot validate --config config/ema9_trend_nvda_amd.example.yaml
python -m dta_bot backtest --config config/ema9_trend_nvda_amd.example.yaml --source yahoo \
  --compare-config config/ema9_trend_bracket.example.yaml \
  --compare-config config/ema9_trend_spy_qqq.example.yaml --combined-only \
  --output artifacts/ema9_nvda_amd_15m.json --report artifacts/ema9_nvda_amd_15m.md
python -m dta_bot backtest --config config/ema9_trend_risk_nvda_amd.example.yaml --source yahoo \
  --compare-config config/ema9_trend_risk_nobe_lock1.example.yaml \
  --compare-config config/ema9_trend_risk_spy_qqq.example.yaml \
  --start 2026-08-01 --end 2026-08-31 --combined-only \
  --output artifacts/ema9_aug2026_risk_nvda_amd.json --report artifacts/ema9_aug2026_risk_nvda_amd.md
```

Current product on the Yahoo window 2026-06-17 → 2026-09-11 (15m, AAPL/MSFT, 12:00 / 15:55, $100k start): **A long-only 51 trades, 60.78%, $301.49**, max DD $130.76 (reproduced; RSI<70 + lock-+1% unchanged); **B cover-only short** (no RSI, no stop, MA-cross cover) **44 trades, 43.18%, $-66.41**, max DD $348.72; **C long+cover-only short 74 trades, 54.05%, $37.26**, max DD $296.58 (42 `opposite_signal_in_trade` skips; combined long 37t $177.86 / short 37t $-140.60). **Prior short-only** (RSI>30, lock_plus, no MA-cross cover) was **41 trades, 53.66%, $96.19**. Writeup: `artifacts/ema9_long_short_15m.md`. Same tape, **SPY+QQQ long-only** (shorts parked): 10-share **58 trades, 46.55%, $-334.30**, max DD $669.37 (43 `session_flatten` / 9 stop / 6 `lock_stop`; 6 armed). August 2026 1% equity-risk (`stop_pct` 1.0) **12 trades, 33.33%, $-515.42**, max DD $1,674.93 (11 `session_flatten` / 1 `lock_stop`; 8 `insufficient_cash`). AAPL+MSFT lock-+1% on the same windows **reproduced** (10-share $301.49; August 1% **15 trades, 73.33%, $5,489.78**). Writeup: `artifacts/ema9_spy_qqq_15m.md`. Same tape, **NVDA+AMD long-only** (shorts parked): 10-share **65 trades, 40.00%, $-526.40**, max DD $600.73 (35 stop / 23 `lock_stop` / 7 `session_flatten`; 25 armed). August 2026 1% equity-risk (`stop_pct` 1.0) **16 trades, 25.00%, $-7,292.55**, max DD $8,311.13 (11 stop / 4 `lock_stop` / 1 `session_flatten`; 2 `insufficient_cash`). AAPL+MSFT and SPY+QQQ lock-+1% on the same windows **reproduced** (10-share $301.49 / $-334.30; August 1% $5,489.78 / $-515.42). Writeup: `artifacts/ema9_nvda_amd_15m.md`. Prior long-only noon price-cross + lock-+1% 10-share: **51 trades, 60.78%, $301.49**, max DD $130.76 (20 `lock_stop` / 13 stop / 18 `session_flatten`; 20 armed). Same rules on **5m: 91 trades, 51.65%, $238.31**, max DD $264.56 (28 `lock_stop` / 20 stop / 43 `session_flatten`; 29 armed). Writeup: `artifacts/ema9_lock_5m_vs_15m.md`. Prior **EMA(9)/SMA(20) pair-cross 10-share (no RSI) 44 trades, 54.55%, $349.33**, max DD $131.87. Exit P&L: **ma_cross 28 ($-84.50)**, **session_flatten 14 ($451.13)**, stop 2 ($-17.29). Same tape **with RSI14 < 70: 39 trades, 51.28%, $214.23**, max DD $142.76 (5 July signals dropped, net +$135.10). **RSI14 < 60: 21 trades, 33.33%, $31.18**. Prior noon price-cross book (old entry, 1.5/3.0, no BE) **reproduced** on the same tape: **50 trades, 62.00%, $453.00**, max DD $207.70, 41 of 50 `session_flatten`. Same old entry, tighter **1.0/2.0** brackets: **51 trades, 56.86%, $462.18**, max DD $149.36 (8 takes / 13 stops / 30 session_flatten). Same old entry, **SMA20 signal-bar stop + 2% take**: **51 trades, 39.22%, $270.16**, max DD $138.22 (6 takes / 28 stops / 17 session_flatten; 3 fills skipped when next open ≤ SMA20). **SMA20 stop, no % take**: **51 trades, 39.22%, $284.39**, max DD $141.52 (28 stops / 23 session_flatten). Same old entry, **no % take**, stop from the *fill*: **fixed 1% (`entry_pct`) 51 trades, 56.86%, $364.05**, max DD $186.89 (14 stops / 37 session_flatten); **lock to +1% (`lock_plus`) 51 trades, 60.78%, $301.49**, max DD $130.76 (20 lock_stop / 13 stop / 18 session_flatten; 20 armed); **trail 1% (`trail`) 51 trades, 54.90%, $253.40**, max DD $117.41 (37 trail_stop / 14 session_flatten; 49 ratcheted). Writeups: `artifacts/ema9_ma_cross.md`, `artifacts/ema9_ma_cross_rsi.md`, `artifacts/ema9_brackets_12_vs_153.md`, `artifacts/ema9_sma20_stop.md`, `artifacts/ema9_stop_manage.md`.

August 2026 1% equity-risk shorts were **not re-run** for the cover-only exit: there is no stop R, so `risk_pct` cannot size the short. Isolated August 10-share cover-only shorts (full-window monthly row): 20 trades, 40.00%, $-159.74. Prior long-only August 1% (unchanged long) reproduced **15 trades, 73.33%, $5,489.78**. Writeup: `artifacts/ema9_long_short_15m.md`. Prior long-only **15m 1% equity-risk lock-+1% 15 trades, 73.33%, $5,489.78**, max DD $2,743.31 (6 `lock_stop` / 8 `session_flatten` / 1 stop). **5m 1% risk 26 trades, 57.69%, $4,061.83**, max DD $3,441.69 (8 `lock_stop` / 13 `session_flatten` / 5 stop; 9 armed). Writeup: `artifacts/ema9_aug2026_risk_lock_5m_vs_15m.md`. Prior pair-cross + 1.5% stop **1% equity-risk (no RSI) 12 trades, 66.67%, $904.72**, max DD $1,707.30. Exit P&L: **ma_cross 8 ($-146.21)**, **session_flatten 4 ($1,050.93)**. **RSI14 < 70 is identical on this August window** (the five RSI≥70 pair-crosses are all in July). Sizing still works (131–219 shares; 3 `insufficient_cash` skips; max concurrent 1). Restored old-entry August 1% (price×EMA9 + SMA20 + RSI, no BE, `stop_pct` matches the stop): **1.5/3.0 reproduced 15 trades, 73.33%, $3,194.05**, max DD $1,676.30; **1.0/2.0 14 trades, 71.43%, $3,820.50**, max DD $2,300.60. Same window **SMA20-stop 1% risk** (R = signal-close − SMA20): **0 trades** — 21 of 58 signals skipped as `insufficient_cash` (R is typically ≪ 1% of price, so share count exceeds $100k cash). Same old entry, **no % take**, 1% risk at a matching 1.0% fill stop: **fixed 1% 14 trades, 71.43%, $4,500.84**, max DD $2,289.59 (13 session_flatten / 1 stop); **lock to +1% 15 trades, 73.33%, $5,489.78**, max DD $2,743.31 (6 lock_stop / 8 session_flatten / 1 stop); **trail 1% 14 trades, 50.00%, $2,071.50**, max DD $2,552.41 (11 trail_stop / 3 session_flatten). Writeups: `artifacts/ema9_aug2026_risk.md`, `artifacts/ema9_aug2026_risk_rsi.md`, `artifacts/ema9_aug2026_risk_brackets.md`, `artifacts/ema9_aug2026_risk_sma20.md`, `artifacts/ema9_aug2026_risk_stop_manage.md`.

On the same Yahoo window, older **EMA-invalidation** isolated books were: **15m AAPL/MSFT/SOXL 240 trades, 36.25%, $626.64**, max DD $850.25; **5m AAPL/MSFT/SOXL 498 trades, 30.72%, $-312.80**, max DD $722.18. Isolated SOXL: 15m 86 trades, 29.07%, $-835.05; 5m 170 trades, 28.24%, $-707.46. AAPL/MSFT only (same exit): 15m 154 / 40.26% / $1,461.69; 5m 328 / 32.01% / $394.66. Writeup: `artifacts/ema9_ema_invalid_5m_vs_15m.md`.

Prior August 2026 1% books (old entry, 1.5/3.0, 12:00 / 15:55): **with one-bar BE 16 trades, 31.25%, $3,188.15**, max DD $1,058.87, **15 of 16 armed BE**, **11 `breakeven_stop`**, 5 `session_flatten`. Without BE **reproduced** on the restored risk YAML: 15 trades, 73.33%, $3,194.05, max DD $1,676.30. Same window **1.0/2.0 at a matching 1.0% stop_pct: 14 trades, 71.43%, $3,820.50**, max DD $2,300.60. Prior 15:15 gated August: 19 trades, 68.42%, $2,595.50, max DD $1,668.34. Prior 13:00 gated August: 17 trades, 70.59%, $3,022.49, max DD $1,663.57. Prior overnight August (gates off): 7 trades, 57.14%, $5,502.59, max DD $3,282.83. Adding SOXL to the August 1% book (pre-BE writeup): **24 trades, 45.83%, $-4,120.21**, max DD $5,533.16 (isolated SOXL 15 trades, 13.33%, $-6,805.96). Writeups: `artifacts/ema9_aug2026_risk_soxl.md`.

Prior full-window **15m 10-share** AAPL/MSFT (old entry, 1.5/3.0) on the same tape 2026-06-17 → 2026-09-11: overnight **44 trades, 50.00%, $1,404.89**, max DD $407.70 (reproduced); 13:00 / 15:55 **64 trades, 60.94%, $419.25**, max DD $298.92, **54 of 64 `session_flatten`**, 33 `entry_cutoff` skips (reproduced); 15:15 / 15:55 **83 trades, 55.42%, $380.60**, max DD $298.92, **72 of 83 `session_flatten`**, 8 `entry_cutoff` skips (reproduced); **12:00 / 15:55 without BE 50 trades, 62.00%, $453.00**, max DD $207.70, **41 of 50 `session_flatten`**, 55 `entry_cutoff` skips (reproduced again vs the pair-cross book); **12:00 / 15:55 + one-bar BE 51 trades, 31.37%, $349.70**, max DD $199.67, **40 armed BE / 27 `breakeven_stop`**, 19 `session_flatten`. Same window with SOXL added (pre-BE writeup): **86 trades, 47.67%, $572.83**, max DD $225.05 (isolated SOXL 36 trades, 27.78%, $119.83). Writeups: `artifacts/ema9_breakeven.md`, `artifacts/ema9_session_gates.md`, `artifacts/ema9_session_gates_soxl.md`.

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
