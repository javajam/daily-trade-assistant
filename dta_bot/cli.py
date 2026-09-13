"""CLI: evaluate, run, pause/resume, validate, status."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from dta_bot.backtest import format_report_md, write_results_json
from dta_bot.broker import build_broker, resolve_api_keys, resolve_trading_url
from dta_bot.config import (
    BotConfig,
    condition_timeframes,
    load_config,
    restrict_universe,
    timeframe_label,
)
from dta_bot.compare import (
    MULTI_ENGINE_NOTE,
    assumptions_orb,
    assumptions_rules,
    data_window_notes,
    format_comparison_md,
    rank_books,
    run_orb_book,
    run_rule_books,
)
from dta_bot.history import download_pairs, drop_empty_prints, drop_still_forming, series_span
from dta_bot.period_stats import parse_trade_bound
from dta_bot.killswitch import is_active, pause, reason as kill_reason, resume
from dta_bot.logging_setup import setup_logging
from dta_bot.market_data import FixtureMarketData, build_market_data
from dta_bot.orb_config import OrbBotConfig, load_orb_config, peek_config_kind
from dta_bot.patterns import PATTERN_NAMES
from dta_bot.runner import run_loop, run_orb_loop
from dta_bot.state import load_state


def _add_shared(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--config",
        default="config/rules.example.yaml",
        help="Path to YAML/JSON rules file (default: config/rules.example.yaml)",
    )
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument(
        "--timeframe",
        default=None,
        help="Rewrite every rule condition to this bar size (e.g. 5m or 15m). "
        "Cooldown stays wall-clock minutes. Ignored for ORB configs.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dta-bot",
        description="Alpaca paper-trading rules bot with candlestick pattern support.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Evaluate on an interval and (optionally) place paper orders")
    _add_shared(run)
    run.add_argument("--once", action="store_true", help="Single cycle then exit")
    run.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate and log decisions but never submit orders",
    )
    run.add_argument(
        "--live-orders",
        action="store_true",
        help="Allow submitting orders (still paper unless live gates are set)",
    )
    run.add_argument("--fixture", help="Evaluate against a local OHLCV JSON fixture instead of Alpaca data")

    ev = sub.add_parser("evaluate", help="Dry-run one cycle (alias for run --once --dry-run)")
    _add_shared(ev)
    ev.add_argument("--fixture", help="Local OHLCV JSON fixture")

    val = sub.add_parser("validate", help="Load and print the rule config")
    _add_shared(val)

    st = sub.add_parser("status", help="Show paper/live gates, kill switch, and credentials")
    _add_shared(st)

    pause_p = sub.add_parser("pause", help="Create the kill-switch file (blocks new orders)")
    _add_shared(pause_p)

    resume_p = sub.add_parser("resume", help="Remove the kill-switch file")
    _add_shared(resume_p)

    pats = sub.add_parser("patterns", help="List built-in candlestick patterns")
    pats.add_argument("--verbose", "-v", action="store_true")

    bt = sub.add_parser("backtest", help="Replay rules on historical OHLCV (Yahoo or Alpaca)")
    _add_shared(bt)
    bt.add_argument("--source", default="auto", choices=["auto", "yahoo", "alpaca"], help="OHLCV source (auto=Alpaca if keys else Yahoo)")
    bt.add_argument("--fixture", help="Local OHLCV JSON fixture (skips download)")
    bt.add_argument("--starting-equity", type=float, default=100_000.0)
    bt.add_argument("--commission", type=float, default=0.0)
    bt.add_argument("--slippage-pct", type=float, default=0.0)
    bt.add_argument("--cache-dir", default="data/ohlcv")
    bt.add_argument("--output", default="artifacts/backtest_results.json")
    bt.add_argument("--report", default="artifacts/backtest_results.md")
    bt.add_argument(
        "--compare-config",
        action="append",
        default=[],
        help="Additional YAML/JSON config to run in the same comparison (repeatable). "
        "Use to put ORB and the sample rules on one report. Books stay separate.",
    )
    bt.add_argument(
        "--combined-only",
        action="store_true",
        help="Skip per-rule isolated books; run the full rule set once",
    )
    bt.add_argument(
        "--symbols",
        default=None,
        help="Comma-separated universe override for this run (e.g. SOXL or AAPL,MSFT).",
    )
    bt.add_argument(
        "--breakout",
        action="append",
        default=[],
        help="Also run an isolated book for this symbol (repeatable). "
        "Default target rule is ema9_trend when present.",
    )
    bt.add_argument(
        "--start",
        default=None,
        help="Trade-window start (YYYY-MM-DD, America/New_York midnight). "
        "Bars before this stay for indicator warmup; no new entries before it.",
    )
    bt.add_argument(
        "--end",
        default=None,
        help="Trade-window end date inclusive (YYYY-MM-DD, America/New_York). "
        "No new entries after this session; open lots flatten at the last in-window mark.",
    )
    return parser


def _dry_run_flag(args: argparse.Namespace, config_dry: bool) -> bool:
    if getattr(args, "cmd", None) == "evaluate":
        return True
    if getattr(args, "dry_run", False):
        return True
    if getattr(args, "live_orders", False):
        return False
    return config_dry


def _load_any(path: str, timeframe: str | None = None) -> tuple[str, BotConfig | OrbBotConfig]:
    kind = peek_config_kind(path)
    if kind == "orb":
        return kind, load_orb_config(path)
    return kind, load_config(path, timeframe=timeframe)


def cmd_validate(args: argparse.Namespace) -> int:
    kind, cfg = _load_any(args.config, timeframe=getattr(args, "timeframe", None))
    print(f"Loaded {args.config} ({kind})")
    print(f"  settings.paper={cfg.settings.paper} allow_live={cfg.settings.allow_live} dry_run={cfg.settings.dry_run}")
    print(f"  universe={cfg.universe or '(per-rule)'}")
    if isinstance(cfg, OrbBotConfig):
        print(
            f"  orb_timeframe={cfg.orb.orb_timeframe} signal_timeframe={cfg.orb.signal_timeframe} "
            f"probe_mode={cfg.orb.probe_mode} edge_pct={cfg.orb.edge_pct} "
            f"session={cfg.orb.session_open} {cfg.orb.session_timezone}"
        )
        print(
            f"  on_open_position={cfg.orb.on_open_position} "
            f"reversal_in_range={cfg.orb.reversal_in_range} "
            f"take_profit_mode={cfg.orb.take_profit_mode} "
            f"ema_filter={cfg.orb.ema_filter} ema_period={cfg.orb.ema_period} "
            f"stop_mode={cfg.orb.stop_mode} min_or_height_pct={cfg.orb.min_or_height_pct} "
            f"entry_cutoff={cfg.orb.entry_cutoff} "
            f"max_trades_before_cutoff={cfg.orb.max_trades_before_cutoff} "
            f"allow_entries_after_cutoff={cfg.orb.allow_entries_after_cutoff} "
            f"sizing={cfg.sizing.type} {cfg.sizing.value}"
        )
        return 0
    print(f"  rules={len(cfg.rules)}")
    print(
        f"  session={cfg.settings.session_timezone} "
        f"entry_cutoff={cfg.settings.entry_cutoff} "
        f"flatten_by={cfg.settings.flatten_by}"
    )
    for rule in cfg.rules:
        syms = cfg.symbols_for(rule)
        tfs = ",".join(sorted(condition_timeframes(rule.when)))
        size = rule.action.size
        size_txt = ""
        if size is not None:
            if size.type == "risk_pct":
                size_txt = (
                    f" size=risk_pct equity_risk={size.equity_risk} "
                    f"stop_pct={size.stop_pct or rule.action.stop_loss_pct}"
                )
            else:
                size_txt = f" size={size.type} {size.value}"
        be_txt = ""
        if rule.action.breakeven_after_bars:
            be_txt = (
                f" breakeven_after_bars={rule.action.breakeven_after_bars}"
                f" requires_valid={rule.action.breakeven_requires_valid}"
                f" valid={rule.action.breakeven_valid}"
            )
        ma_txt = ""
        if rule.action.exit == "ma_cross":
            ma_txt = (
                f" ema_period={rule.action.exit_ema_period}"
                f" sma_period={rule.action.exit_sma_period}"
            )
        print(
            f"    - {rule.id}: enabled={rule.enabled} symbols={syms} "
            f"action={rule.action.type} exit={rule.action.exit} "
            f"cooldown={rule.cooldown_minutes}m tf={tfs}{size_txt}{be_txt}{ma_txt}"
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    kind, cfg = _load_any(args.config, timeframe=getattr(args, "timeframe", None))
    url, mode = resolve_trading_url(allow_live=cfg.settings.allow_live)
    key, secret = resolve_api_keys()
    print(f"config:          {args.config} ({kind})")
    print(f"trading mode:    {mode} ({url})")
    print(f"allow_live yaml: {cfg.settings.allow_live}")
    print(f"yaml dry_run:    {cfg.settings.dry_run}")
    print(f"api key present: {bool(key)}")
    print(f"api secret set:  {bool(secret)}")
    print(f"kill switch:     {kill_reason(cfg.settings.kill_switch_file) or 'off'}")
    print(f"state file:      {cfg.settings.state_file}")
    print(f"patterns:        {', '.join(PATTERN_NAMES)}")
    if isinstance(cfg, OrbBotConfig):
        print(
            f"orb:             {cfg.orb.orb_timeframe} OR → {cfg.orb.signal_timeframe} signals, "
            f"probe_mode={cfg.orb.probe_mode}, edge_pct={cfg.orb.edge_pct}, "
            f"on_open_position={cfg.orb.on_open_position}"
        )
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    _kind, cfg = _load_any(args.config)
    path = pause(cfg.settings.kill_switch_file)
    print(f"Paused. Kill switch file: {path}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    _kind, cfg = _load_any(args.config)
    if resume(cfg.settings.kill_switch_file):
        print("Resumed. Kill switch file removed.")
    else:
        print("Kill switch file was not present (already live).")
    if is_active(cfg.settings.kill_switch_file):
        print(f"Note: still paused via env: {kill_reason(cfg.settings.kill_switch_file)}")
    return 0


def _load_backtest_bars(
    args: argparse.Namespace,
    configs: list[BotConfig | OrbBotConfig],
    now: datetime,
) -> tuple[dict, dict[str, str], list[str], str]:
    pairs: set[tuple[str, str]] = set()
    for cfg in configs:
        pairs |= cfg.all_symbol_timeframes()
    if args.fixture:
        fixture = FixtureMarketData(args.fixture)
        bars = {}
        sources = {}
        for symbol, tf in sorted(pairs):
            try:
                bars[(symbol, tf)] = fixture.get_bars(symbol, tf, limit=10_000_000)
                sources[f"{symbol}:{tf}"] = f"fixture:{args.fixture}"
            except KeyError:
                bars[(symbol, tf)] = []
                sources[f"{symbol}:{tf}"] = f"fixture:{args.fixture} (missing)"
        source_label = f"fixture {args.fixture}"
    else:
        feed = next((cfg.settings.data_feed for cfg in configs), "iex")
        bars, sources = download_pairs(
            pairs,
            source=args.source,
            feed=feed,
            cache_dir=args.cache_dir,
        )
        if args.source == "alpaca" or (
            args.source == "auto" and any(str(v).startswith("alpaca") for v in sources.values())
        ):
            source_label = "Alpaca market data (raw, configured feed)"
        else:
            source_label = "Yahoo Finance v8 chart (unadjusted regular-session OHLC)"

    for key, series in list(bars.items()):
        bars[key] = drop_empty_prints(drop_still_forming(series, key[1], now=now))

    spans = []
    for (symbol, tf), series in sorted(bars.items()):
        start, end = series_span(series)
        spans.append(f"{symbol} {tf}: {len(series)} bars {start} → {end}")
        print(f"  data {symbol} {tf}: {len(series)} closed bars ({start} → {end})")
    return bars, sources, spans, source_label


def cmd_backtest(args: argparse.Namespace) -> int:
    paths = [args.config, *list(args.compare_config or [])]
    loaded: list[tuple[str, str, BotConfig | OrbBotConfig]] = []
    override_tf = getattr(args, "timeframe", None)
    symbol_filter = None
    raw_symbols = getattr(args, "symbols", None)
    if raw_symbols:
        symbol_filter = [s.strip().upper() for s in str(raw_symbols).split(",") if s.strip()]
    for path in paths:
        kind, cfg = _load_any(path, timeframe=override_tf)
        if symbol_filter and isinstance(cfg, BotConfig):
            cfg = restrict_universe(cfg, symbol_filter)
        loaded.append((path, kind, cfg))
    now = datetime.now(timezone.utc)
    bars, sources, spans, source_label = _load_backtest_bars(
        args, [cfg for _path, _kind, cfg in loaded], now
    )

    friction = f"commission=${args.commission:.2f}/fill, slippage={args.slippage_pct}%"
    comparing = len(loaded) > 1
    runs: list[dict] = []
    assumption_blocks: list[str] = []
    trade_start = parse_trade_bound(getattr(args, "start", None))
    trade_end = parse_trade_bound(getattr(args, "end", None), end=True)
    if trade_start or trade_end:
        assumption_blocks.append(
            "CLI trade window "
            f"{trade_start.isoformat() if trade_start else 'tape start'} → "
            f"{trade_end.isoformat() if trade_end else 'tape end'} "
            "(America/New_York date bounds; prior bars used only for warmup)."
        )

    for path, kind, cfg in loaded:
        if isinstance(cfg, OrbBotConfig):
            notes = assumptions_orb(friction, args.starting_equity, cfg)
            assumption_blocks.extend(notes)
            print(f"\n=== backtest orb_reversal ({path}) ===")
            compact = run_orb_book(
                cfg,
                bars,
                starting_equity=args.starting_equity,
                commission=args.commission,
                slippage_pct=args.slippage_pct,
                data_source=source_label,
                notes=notes,
            )
            r = compact["report"]
            print(
                f"  signals={r['signals']} trades={r['trades']} win_rate={r['win_rate_pct']} "
                f"pnl=${r['total_pnl']:.2f} ({r['total_pnl_pct']:.3f}%) "
                f"dd=${r['max_drawdown']} ({r['max_drawdown_pct']})"
            )
            for trade in compact["trades"]:
                print(
                    f"    {trade['side']} {trade['symbol']} qty={trade['qty']:g} "
                    f"in={trade['entry_price']:.4f} out={trade['exit_price']:.4f} "
                    f"pnl=${trade['pnl']:.2f} ({trade['exit_reason']})"
                )
            runs.append(compact)
            continue

        assert isinstance(cfg, BotConfig)
        notes = assumptions_rules(friction, args.starting_equity, cfg)
        assumption_blocks.extend(notes)
        books = run_rule_books(
            cfg,
            bars,
            starting_equity=args.starting_equity,
            commission=args.commission,
            slippage_pct=args.slippage_pct,
            data_source=source_label,
            assumptions=notes,
            combined_only=args.combined_only,
            include_entries_only=not args.combined_only,
            label_prefix=timeframe_label(cfg),
            breakout_symbols=list(args.breakout or []),
            trade_start=trade_start,
            trade_end=trade_end,
        )
        for compact in books:
            r = compact["report"]
            print(f"\n=== backtest {compact['label']} ({path}) ===")
            print(
                f"  signals={r['signals']} trades={r['trades']} win_rate={r['win_rate_pct']} "
                f"pnl=${r['total_pnl']:.2f} ({r['total_pnl_pct']:.3f}%) "
                f"dd=${r['max_drawdown']} ({r['max_drawdown_pct']})"
            )
            runs.append(compact)

    # Deduplicate assumption lines while keeping order (ORB + rules share fill notes).
    seen: set[str] = set()
    assumptions: list[str] = []
    for item in assumption_blocks:
        if item not in seen:
            seen.add(item)
            assumptions.append(item)
    if comparing:
        assumptions.append(MULTI_ENGINE_NOTE)

    window_notes = data_window_notes(spans, sources)
    comparison = rank_books(runs)
    payload = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "config": args.config,
        "configs": paths,
        "starting_equity": args.starting_equity,
        "friction": friction,
        "data_source": source_label,
        "data_spans": spans,
        "sources": sources,
        "assumptions": assumptions,
        "window_notes": window_notes,
        "comparison": comparison,
        "trade_start": trade_start.isoformat() if trade_start else None,
        "trade_end": trade_end.isoformat() if trade_end else None,
        "runs": runs,
    }
    if comparing and args.output == "artifacts/backtest_results.json":
        args.output = "artifacts/orb_vs_sample_comparison.json"
    if comparing and args.report == "artifacts/backtest_results.md":
        args.report = "artifacts/orb_vs_sample_comparison.md"
    write_results_json(args.output, payload)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = format_comparison_md(payload) if comparing else format_report_md(payload)
    report_path.write_text(report_text, encoding="utf-8")
    if comparing:
        print("\n=== ranking by P&L % ===")
        for row in comparison:
            print(
                f"  {row['rank']}. {row['label']}: "
                f"{row['total_pnl_pct']:.3f}% (${row['total_pnl']:.2f}) "
                f"trades={row['trades']} [{row['caveat']}]"
            )
    print(f"\nWrote {args.output}")
    print(f"Wrote {args.report}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    _kind, cfg = _load_any(args.config, timeframe=getattr(args, "timeframe", None))
    dry = _dry_run_flag(args, cfg.settings.dry_run)
    fixture = getattr(args, "fixture", None)
    data = FixtureMarketData(fixture) if fixture else build_market_data(
        feed=cfg.settings.data_feed, fixture=None
    )
    broker = build_broker(allow_live=cfg.settings.allow_live, dry_run=dry)
    state = load_state(cfg.settings.state_file)
    once = bool(getattr(args, "once", False) or args.cmd == "evaluate")
    if isinstance(cfg, OrbBotConfig):
        # evaluate --fixture scans the whole tape so the demo shows every setup.
        # live/paper run only fires when the latest closed signal bar is the reversal.
        scan_all = args.cmd == "evaluate"
        run_orb_loop(
            cfg,
            broker=broker,
            data=data,
            state=state,
            dry_run=dry,
            once=once,
            scan_all=scan_all,
        )
        return 0
    assert isinstance(cfg, BotConfig)
    run_loop(cfg, broker=broker, data=data, state=state, dry_run=dry, once=once)
    return 0


def main(argv: list[str] | None = None) -> int:
    # Load .env if present, without requiring it.
    env_path = Path(".env")
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except ImportError:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(verbose=getattr(args, "verbose", False))

    if args.cmd == "patterns":
        for name in PATTERN_NAMES:
            print(name)
        return 0
    if args.cmd == "validate":
        return cmd_validate(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "pause":
        return cmd_pause(args)
    if args.cmd == "resume":
        return cmd_resume(args)
    if args.cmd in {"run", "evaluate"}:
        return cmd_run(args)
    if args.cmd == "backtest":
        return cmd_backtest(args)
    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
