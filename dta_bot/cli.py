"""CLI: evaluate, run, pause/resume, validate, status."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dta_bot.broker import build_broker, resolve_api_keys, resolve_trading_url
from dta_bot.config import load_config
from dta_bot.killswitch import is_active, pause, reason as kill_reason, resume
from dta_bot.logging_setup import setup_logging
from dta_bot.market_data import FixtureMarketData, build_market_data
from dta_bot.patterns import PATTERN_NAMES
from dta_bot.runner import run_loop
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
    return parser


def _dry_run_flag(args: argparse.Namespace, config_dry: bool) -> bool:
    if getattr(args, "cmd", None) == "evaluate":
        return True
    if getattr(args, "dry_run", False):
        return True
    if getattr(args, "live_orders", False):
        return False
    return config_dry


def cmd_validate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    print(f"Loaded {args.config}")
    print(f"  settings.paper={cfg.settings.paper} allow_live={cfg.settings.allow_live} dry_run={cfg.settings.dry_run}")
    print(f"  universe={cfg.universe or '(per-rule)'}")
    print(f"  rules={len(cfg.rules)}")
    for rule in cfg.rules:
        syms = cfg.symbols_for(rule)
        print(
            f"    - {rule.id}: enabled={rule.enabled} symbols={syms} "
            f"action={rule.action.type} cooldown={rule.cooldown_minutes}m"
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    url, mode = resolve_trading_url(allow_live=cfg.settings.allow_live)
    key, secret = resolve_api_keys()
    print(f"config:          {args.config}")
    print(f"trading mode:    {mode} ({url})")
    print(f"allow_live yaml: {cfg.settings.allow_live}")
    print(f"yaml dry_run:    {cfg.settings.dry_run}")
    print(f"api key present: {bool(key)}")
    print(f"api secret set:  {bool(secret)}")
    print(f"kill switch:     {kill_reason(cfg.settings.kill_switch_file) or 'off'}")
    print(f"state file:      {cfg.settings.state_file}")
    print(f"patterns:        {', '.join(PATTERN_NAMES)}")
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    path = pause(cfg.settings.kill_switch_file)
    print(f"Paused. Kill switch file: {path}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    if resume(cfg.settings.kill_switch_file):
        print("Resumed. Kill switch file removed.")
    else:
        print("Kill switch file was not present (already live).")
    if is_active(cfg.settings.kill_switch_file):
        print(f"Note: still paused via env: {kill_reason(cfg.settings.kill_switch_file)}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    dry = _dry_run_flag(args, cfg.settings.dry_run)
    fixture = getattr(args, "fixture", None)
    data = FixtureMarketData(fixture) if fixture else build_market_data(
        feed=cfg.settings.data_feed, fixture=None
    )
    broker = build_broker(allow_live=cfg.settings.allow_live, dry_run=dry)
    state = load_state(cfg.settings.state_file)
    once = bool(getattr(args, "once", False) or args.cmd == "evaluate")
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
    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
