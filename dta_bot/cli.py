"""CLI: evaluate, run, pause/resume, validate, status."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from dta_bot.backtest import format_report_md, restrict_config, run_backtest, write_results_json
from dta_bot.broker import build_broker, resolve_api_keys, resolve_trading_url
from dta_bot.config import BotConfig, load_config
from dta_bot.history import download_pairs, drop_empty_prints, drop_still_forming, series_span
from dta_bot.killswitch import is_active, pause, reason as kill_reason, resume
from dta_bot.logging_setup import setup_logging
from dta_bot.market_data import FixtureMarketData, build_market_data
from dta_bot.orb_backtest import run_orb_backtest
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
        "--combined-only",
        action="store_true",
        help="Skip per-rule isolated books; run the full rule set once",
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


def _load_any(path: str) -> tuple[str, BotConfig | OrbBotConfig]:
    kind = peek_config_kind(path)
    if kind == "orb":
        return kind, load_orb_config(path)
    return kind, load_config(path)


def cmd_validate(args: argparse.Namespace) -> int:
    kind, cfg = _load_any(args.config)
    print(f"Loaded {args.config} ({kind})")
    print(f"  settings.paper={cfg.settings.paper} allow_live={cfg.settings.allow_live} dry_run={cfg.settings.dry_run}")
    print(f"  universe={cfg.universe or '(per-rule)'}")
    if isinstance(cfg, OrbBotConfig):
        print(
            f"  orb_timeframe={cfg.orb.orb_timeframe} signal_timeframe={cfg.orb.signal_timeframe} "
            f"edge_pct={cfg.orb.edge_pct} session={cfg.orb.session_open} {cfg.orb.session_timezone}"
        )
        print(
            f"  on_open_position={cfg.orb.on_open_position} take_profit={cfg.orb.take_profit} "
            f"sizing={cfg.sizing.type} {cfg.sizing.value}"
        )
        return 0
    print(f"  rules={len(cfg.rules)}")
    for rule in cfg.rules:
        syms = cfg.symbols_for(rule)
        print(
            f"    - {rule.id}: enabled={rule.enabled} symbols={syms} "
            f"action={rule.action.type} cooldown={rule.cooldown_minutes}m"
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    kind, cfg = _load_any(args.config)
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
            f"edge_pct={cfg.orb.edge_pct}, on_open_position={cfg.orb.on_open_position}"
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


def cmd_backtest(args: argparse.Namespace) -> int:
    _kind, cfg = _load_any(args.config)
    now = datetime.now(timezone.utc)
    if args.fixture:
        fixture = FixtureMarketData(args.fixture)
        bars = {}
        sources = {}
        for symbol, tf in sorted(cfg.all_symbol_timeframes()):
            bars[(symbol, tf)] = fixture.get_bars(symbol, tf, limit=10_000_000)
            sources[f"{symbol}:{tf}"] = f"fixture:{args.fixture}"
        source_label = f"fixture {args.fixture}"
    else:
        bars, sources = download_pairs(
            cfg.all_symbol_timeframes(),
            source=args.source,
            feed=cfg.settings.data_feed,
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

    friction = f"commission=${args.commission:.2f}/fill, slippage={args.slippage_pct}%"
    if isinstance(cfg, OrbBotConfig):
        assumptions = [
            "Opening range is the first orb_timeframe bar at/after 9:30 America/New_York (configurable).",
            "After the OR candle is complete, probe/reversal evaluation uses the signal timeframe.",
            "Probe = signal-bar close inside the 5% (configurable) edge band under the OR high or above the OR low.",
            "Reversal = the next signal bar, opposite color (top+bearish → short, bottom+bullish → long).",
            "Entry fills at the open of the bar after the reversal candle.",
            "Stop is the reversal candle extreme; take-profit is the OR midpoint (v1; A/B tested later).",
            "Multiple trades are allowed (no daily cap). One open position per symbol; new signals skip while in a position unless on_open_position=replace.",
            "If stop and take both trade in the fill bar, the stop is assumed to fill first.",
            "A gap through stop/take fills at that bar's open.",
            "Open lots still on the last bar are flattened at the last close (exit reason eod).",
            "Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.",
            friction,
            f"Starting equity ${args.starting_equity:,.2f}.",
        ]
        print("\n=== backtest orb_reversal ===")
        result = run_orb_backtest(
            cfg,
            bars,
            starting_equity=args.starting_equity,
            commission=args.commission,
            slippage_pct=args.slippage_pct,
            label="orb_reversal",
            data_source=source_label,
            notes=assumptions,
        )
        r = result.report
        print(
            f"  signals={r.signals} trades={r.trades} win_rate={r.win_rate_pct} "
            f"pnl=${r.total_pnl:.2f} ({r.total_pnl_pct:.3f}%) "
            f"dd=${r.max_drawdown} ({r.max_drawdown_pct})"
        )
        for trade in result.trades:
            print(
                f"    {trade.side} {trade.symbol} qty={trade.qty:g} "
                f"in={trade.entry_price:.4f} out={trade.exit_price:.4f} "
                f"pnl=${trade.pnl:.2f} ({trade.exit_reason})"
            )
        payload_run = result.to_dict()
        payload_run["pattern_hits"] = {"orb_reversal": r.signals}
        runs = [payload_run]
        compact_runs = [
            {
                "label": payload_run["label"],
                "report": payload_run["report"],
                "bars_used": payload_run["bars_used"],
                "pattern_hits": payload_run.get("pattern_hits"),
                "trades": payload_run["trades"],
                "signals": [
                    {
                        k: sig[k]
                        for k in (
                            "rule_id",
                            "symbol",
                            "action_type",
                            "signal_time",
                            "accepted",
                            "skip_reason",
                        )
                    }
                    for sig in payload_run["signals"]
                ],
            }
        ]
        payload = {
            "generated_at": now.isoformat().replace("+00:00", "Z"),
            "config": args.config,
            "starting_equity": args.starting_equity,
            "friction": friction,
            "data_source": source_label,
            "data_spans": spans,
            "sources": sources,
            "assumptions": assumptions,
            "runs": compact_runs,
        }
        write_results_json(args.output, payload)
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(format_report_md(payload), encoding="utf-8")
        print(f"\nWrote {args.output}")
        print(f"Wrote {args.report}")
        return 0

    assumptions = [
        "Signals come from the live evaluate_rule path (same pattern/SMA/RSI/volume detectors).",
        "A rule is evaluated when any of its referenced timeframes prints a newly closed bar.",
        "Entries and close-signals fill at the next bar open of the finest rule timeframe.",
        "Stop/take are computed from the signal-bar close (same as live bracket_prices).",
        "If stop and take both trade in the fill bar, the stop is assumed to fill first.",
        "A gap through stop/take fills at that bar's open.",
        "One open lot per symbol (no pyramiding). A second signal while flat-in-symbol is skipped.",
        "Open lots still on the last bar are flattened at the last close (exit reason eod).",
        "Regular-session Yahoo bars when the source is Yahoo (includePrePost=false), unadjusted OHLC.",
        friction,
        f"Starting equity ${args.starting_equity:,.2f}.",
    ]

    assert isinstance(cfg, BotConfig)
    run_ids: list[list[str] | None]
    if args.combined_only:
        run_ids = [None]
    else:
        run_ids = [[r.id] for r in cfg.rules] + [None]

    runs = []
    for ids in run_ids:
        subset = restrict_config(cfg, ids)
        tag = "combined" if ids is None else ids[0]
        notes = list(assumptions)
        if ids is not None and subset.rules and subset.rules[0].action.type == "close":
            notes.append(
                "Exit-only rule: isolated book has no entries, so P&L is $0. "
                "Signal count is how often the pattern would have fired; "
                "the combined book uses those fires to flatten longs from the entry rules."
            )
        print(f"\n=== backtest {tag} ===")
        result = run_backtest(
            subset,
            bars,
            starting_equity=args.starting_equity,
            commission=args.commission,
            slippage_pct=args.slippage_pct,
            label=tag,
            data_source=source_label,
            notes=notes,
        )
        r = result.report
        print(
            f"  signals={r.signals} trades={r.trades} win_rate={r.win_rate_pct} "
            f"pnl=${r.total_pnl:.2f} ({r.total_pnl_pct:.3f}%) "
            f"dd=${r.max_drawdown} ({r.max_drawdown_pct})"
        )
        payload_run = result.to_dict()
        hits: dict[str, int] = {}
        for sig in result.signals:
            for name in (
                "bullish_engulfing",
                "bearish_engulfing",
                "evening_star",
                "hammer",
            ):
                if f"{name} matched" in sig.reason:
                    hits[name] = hits.get(name, 0) + 1
        payload_run["pattern_hits"] = hits
        runs.append(payload_run)

    compact_runs = []
    for run in runs:
        compact_runs.append(
            {
                "label": run["label"],
                "report": run["report"],
                "bars_used": run["bars_used"],
                "pattern_hits": run.get("pattern_hits"),
                "trades": run["trades"],
                "signals": [
                    {
                        k: sig[k]
                        for k in (
                            "rule_id",
                            "symbol",
                            "action_type",
                            "signal_time",
                            "accepted",
                            "skip_reason",
                        )
                    }
                    for sig in run["signals"]
                ],
            }
        )
    payload = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "config": args.config,
        "starting_equity": args.starting_equity,
        "friction": friction,
        "data_source": source_label,
        "data_spans": spans,
        "sources": sources,
        "assumptions": assumptions,
        "runs": compact_runs,
    }
    write_results_json(args.output, payload)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(format_report_md(payload), encoding="utf-8")
    print(f"\nWrote {args.output}")
    print(f"Wrote {args.report}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    _kind, cfg = _load_any(args.config)
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
