from datetime import datetime, timezone

from dta_bot.backtest import BacktestResult, RuleReport, Signal
from dta_bot.cli import main
from dta_bot.compare import (
    assumptions_orb,
    assumptions_rules,
    combined_book_effect,
    format_comparison_md,
    pattern_hits_from_result,
    rank_books,
    rule_book_plan,
    sample_size_caveat,
)
from dta_bot.config import load_config
from dta_bot.orb_config import load_orb_config


def _run(label: str, pnl_pct: float, trades: int, *, exit_only: bool = False, days: int = 60):
    notes = ["Exit-only rule: isolated book has no entries, so P&L is $0."] if exit_only else []
    return {
        "label": label,
        "report": {
            "rule_id": label,
            "signals": trades,
            "trades": trades,
            "wins": trades // 2,
            "losses": trades - trades // 2,
            "breakeven": 0,
            "win_rate_pct": 50.0 if trades else None,
            "total_pnl": pnl_pct * 1000.0,
            "total_pnl_pct": pnl_pct,
            "max_drawdown": 10.0,
            "max_drawdown_pct": 0.01,
            "avg_win": 2.0 if trades else None,
            "avg_loss": -1.0 if trades else None,
            "starting_equity": 100_000.0,
            "ending_equity": 100_000.0 + pnl_pct * 1000.0,
            "period_start": "2026-07-15T13:30:00Z",
            "period_end": f"2026-{7 + (days // 30):02d}-15T19:45:00Z" if days < 300 else "2026-09-11T19:30:00Z",
            "data_source": "Yahoo Finance v8 chart (unadjusted regular-session OHLC)",
            "notes": notes,
            "exit_reasons": {},
            "signals_by_symbol": {},
            "trades_by_symbol": {},
        },
    }


def test_assumptions_orb_document_new_defaults():
    cfg = load_orb_config("config/orb_reversal.example.yaml")
    notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, cfg)
    assert any("opening-range extreme" in n for n in notes)
    assert any("ema_cross" in n and "close < EMA" in n for n in notes)
    assert any("EMA" in n and "ema_filter: true" in n for n in notes)
    assert any("or_low <= close <= or_high" in n for n in notes)
    assert any("touch_and_band" in n and "high >= OR high" in n and "edge band" in n for n in notes)
    assert any("10:30" in n and "America/New_York" in n for n in notes)
    assert any("min_or_height_pct" in n and "or_open" in n and "1%" in n for n in notes)
    touch = cfg.model_copy(update={"orb": cfg.orb.model_copy(update={"probe_mode": "touch"})})
    touch_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, touch)
    assert any("probe_mode: touch)" in n and "high >= OR high" in n for n in touch_notes)
    band = cfg.model_copy(update={"orb": cfg.orb.model_copy(update={"probe_mode": "edge_band"})})
    band_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, band)
    assert any("edge_band" in n and "5%" in n for n in band_notes)
    old = cfg.model_copy(
        update={"orb": cfg.orb.model_copy(update={"stop_mode": "reversal_candle", "entry_cutoff": None})}
    )
    old_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, old)
    assert any("reversal candle extreme" in n for n in old_notes)
    assert any("no clock cutoff" in n for n in old_notes)
    mid = cfg.model_copy(
        update={"orb": cfg.orb.model_copy(update={"take_profit_mode": "or_midpoint", "reversal_in_range": "off"})}
    )
    mid_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, mid)
    assert any("or_midpoint" in n and "OR midpoint" in n for n in mid_notes)
    one_r = cfg.model_copy(
        update={"orb": cfg.orb.model_copy(update={"take_profit_mode": "one_r", "reversal_in_range": "off"})}
    )
    one_r_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, one_r)
    assert any("one_r" in n and "entry + R" in n for n in one_r_notes)
    assert any("in-range filter is off" in n for n in one_r_notes)
    off_ema = cfg.model_copy(update={"orb": cfg.orb.model_copy(update={"ema_filter": False})})
    off_ema_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, off_ema)
    assert any("EMA filter is off" in n for n in off_ema_notes)
    first = cfg.model_copy(
        update={"orb": cfg.orb.model_copy(update={"take_profit_mode": "first_profitable_close"})}
    )
    first_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, first)
    assert any("first_profitable_close" in n and "close > entry" in n for n in first_notes)
    quiet = cfg.model_copy(update={"orb": cfg.orb.model_copy(update={"min_or_height_pct": None})})
    quiet_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, quiet)
    assert any("High-vol gate is off" in n for n in quiet_notes)
    body = cfg.model_copy(update={"orb": cfg.orb.model_copy(update={"reversal_in_range": "body"})})
    body_notes = assumptions_orb("commission=$0.00/fill, slippage=0.0%", 100_000.0, body)
    assert any("fully inside" in n and "body" in n for n in body_notes)


def test_assumptions_rules_mention_ma_cross():
    notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0)
    assert any("MA-cross" in n for n in notes)


def test_pattern_hits_count_ema_cross():
    ts = datetime(2026, 9, 11, tzinfo=timezone.utc)
    result = BacktestResult(
        label="ema9_trend",
        report=RuleReport(
            rule_id="ema9_trend",
            signals=1,
            trades=0,
            wins=0,
            losses=0,
            breakeven=0,
            win_rate_pct=None,
            total_pnl=0.0,
            total_pnl_pct=0.0,
            avg_win=None,
            avg_loss=None,
            max_drawdown=0.0,
            max_drawdown_pct=0.0,
            starting_equity=100_000.0,
            ending_equity=100_000.0,
            period_start=None,
            period_end=None,
            data_source="fixture",
        ),
        trades=[],
        signals=[
            Signal(
                rule_id="ema9_trend",
                symbol="AAPL",
                action_type="buy",
                signal_time=ts,
                bar_ts=None,
                reason="ema_cross matched (bullish): prev close 10.0000 vs EMA9 10.0000",
                accepted=True,
            )
        ],
        equity_curve=[],
    )
    assert pattern_hits_from_result(result) == {"ema_cross": 1}


def test_ema9_rule_book_plan_isolates_each_entry():
    cfg = load_config("config/ema9_trend.example.yaml")
    labels = [label for label, _ids, _note in rule_book_plan(cfg)]
    assert labels[:3] == ["ema9_trend", "ema9_cross_raw", "engulfing-with-trend"]
    assert "sample-entries" in labels
    assert "combined" in labels


def test_rule_book_plan_includes_entries_and_combined():
    cfg = load_config("config/rules.example.yaml")
    labels = [label for label, _ids, _note in rule_book_plan(cfg)]
    assert labels == [
        "engulfing-with-trend",
        "hammer-oversold",
        "evening-star-or-engulfing-exit",
        "sample-entries",
        "combined",
    ]
    entries = next(ids for label, ids, _ in rule_book_plan(cfg) if label == "sample-entries")
    assert entries == ["engulfing-with-trend", "hammer-oversold"]


def test_rank_books_sorts_by_pnl_pct_desc():
    runs = [
        _run("orb_reversal", -0.2, 12),
        _run("engulfing-with-trend", 0.7, 39),
        _run("evening-star-or-engulfing-exit", 0.0, 0, exit_only=True),
        _run("hammer-oversold", 0.1, 24),
    ]
    ranked = rank_books(runs)
    assert [row["label"] for row in ranked] == [
        "engulfing-with-trend",
        "hammer-oversold",
        "evening-star-or-engulfing-exit",
        "orb_reversal",
    ]
    assert ranked[0]["rank"] == 1
    assert ranked[0]["total_pnl_pct"] == 0.7
    assert "small sample" in ranked[-1]["caveat"]
    assert "exit-only" in ranked[2]["caveat"]


def test_sample_size_caveat_flags_long_window():
    report = {
        "trades": 24,
        "notes": [],
        "rule_id": "hammer-oversold",
        "period_start": "2024-09-12T13:30:00Z",
        "period_end": "2026-09-11T19:30:00Z",
    }
    caveat = sample_size_caveat(report)
    assert "small sample (24 trades)" in caveat
    assert "longer window" in caveat


def test_combined_book_effect_states_delta():
    runs = [
        _run("sample-entries", 0.811, 63),
        _run("combined", 0.447, 110),
        _run("evening-star-or-engulfing-exit", 0.0, 0, exit_only=True),
    ]
    runs[0]["report"]["total_pnl"] = 810.57
    runs[1]["report"]["total_pnl"] = 447.01
    runs[1]["report"]["exit_reasons"] = {"close_signal": 81, "stop": 16, "take": 13}
    runs[2]["report"]["signals"] = 560
    text = combined_book_effect(runs)
    assert text is not None
    assert "$810.57" in text
    assert "$447.01" in text
    assert "560 isolated fires" in text
    assert "81 lots" in text


def test_format_comparison_md_contains_table_and_engine_note():
    runs = [_run("orb_reversal", 0.12, 8), _run("engulfing-with-trend", 0.70, 39)]
    payload = {
        "generated_at": "2026-09-13T00:00:00Z",
        "configs": ["config/orb_reversal.example.yaml", "config/rules.example.yaml"],
        "starting_equity": 100_000.0,
        "friction": "commission=$0.00/fill, slippage=0.0%",
        "data_source": "Yahoo Finance v8 chart (unadjusted regular-session OHLC)",
        "comparison": rank_books(runs),
        "runs": runs,
        "window_notes": ["Yahoo 5m/15m cap is 60d."],
        "assumptions": ["Starting equity $100,000.00."],
    }
    md = format_comparison_md(payload)
    assert "# ORB vs sample-rule backtest comparison" in md
    assert "| Rank | Book |" in md
    assert "engulfing-with-trend" in md
    assert "orb_reversal" in md
    assert "separate engines" in md
    assert "Yahoo 5m/15m cap is 60d." in md


def test_cli_compare_fixtures(tmp_path):
    out = tmp_path / "cmp.json"
    report = tmp_path / "cmp.md"
    rc = main(
        [
            "backtest",
            "--config",
            "config/orb_reversal.example.yaml",
            "--compare-config",
            "config/rules.example.yaml",
            "--fixture",
            "config/orb_sample_bars.json",
            "--output",
            str(out),
            "--report",
            str(report),
        ]
    )
    assert rc == 0
    text = report.read_text(encoding="utf-8")
    assert "orb_reversal" in text
    assert "Ranking by P&L %" in text
    payload = out.read_text(encoding="utf-8")
    assert "sample-entries" in payload
    assert "evening-star-or-engulfing-exit" in payload
