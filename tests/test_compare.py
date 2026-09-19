from datetime import datetime, timezone

from dta_bot.backtest import BacktestResult, RuleReport, Signal
from dta_bot.cli import main
from dta_bot.compare import (
    assumptions_orb,
    assumptions_rules,
    combined_book_effect,
    combined_book_label,
    format_comparison_md,
    format_monthly_side_by_side,
    format_side_by_side_table,
    pattern_hits_from_result,
    rank_books,
    rule_book_plan,
    run_rule_books,
    sample_size_caveat,
    session_gate_suffix,
    sizing_tag,
    universe_tag,
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
    assert any("ema_invalid" in n and "close < EMA" in n for n in notes)
    cfg = load_config("config/ema9_trend.example.yaml")
    ema_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, cfg)
    assert any("noon day-trade stack" in n and "EMA(9)" in n and "SMA(20)" in n for n in ema_notes)
    assert not any("Short: close crosses below EMA(9)" in n for n in ema_notes)
    assert not any("RSI(14) > 30" in n for n in ema_notes)
    assert any("ma_cross_close" in n and "close-to-close" in n for n in ema_notes)
    assert any("entry_cutoff=12:00" in n and "flatten_by=15:55" in n for n in ema_notes)
    assert not any("breakeven_after_bars: 1" in n for n in ema_notes)
    assert not any("stop_mode: lock_plus" in n for n in ema_notes)
    assert session_gate_suffix(cfg) == " (cutoff 12:00, flat 15:55, MA-cross close)"
    pair = load_config("config/ema9_trend_pair.example.yaml")
    pair_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, pair)
    assert any("ma_cross" in n and "EMA(9)" in n and "SMA(20)" in n for n in pair_notes)
    assert any("No RSI entry filter" in n for n in pair_notes)
    old = load_config("config/ema9_trend_bracket_nobe.example.yaml")
    old_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, old)
    assert any("fixed_bracket" in n for n in old_notes)
    assert session_gate_suffix(old) == " (cutoff 12:00, flat 15:55, 1.5/3.0)"
    tight = load_config("config/ema9_trend_bracket_nobe_12.example.yaml")
    assert session_gate_suffix(tight) == " (cutoff 12:00, flat 15:55, 1.0/2.0)"
    risk = load_config("config/ema9_trend_risk_nobe.example.yaml")
    assert session_gate_suffix(risk) == " (cutoff 12:00, flat 15:55, 1.5/3.0)"
    risk12 = load_config("config/ema9_trend_risk_nobe_12.example.yaml")
    assert session_gate_suffix(risk12) == " (cutoff 12:00, flat 15:55, 1.0/2.0)"
    rsi_cfg = load_config("config/ema9_trend_bracket_rsi.example.yaml")
    rsi_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, rsi_cfg)
    assert any("RSI filter on (RSI14 < 70)" in n for n in rsi_notes)
    assert any("rsi: { period: 14, below: 70 }" in n for n in rsi_notes)
    assert any("same threshold as the default noon price-cross book" in n for n in rsi_notes)
    sixty = load_config("config/ema9_trend_bracket_rsi60.example.yaml")
    sixty_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, sixty)
    assert any("RSI filter on (RSI14 < 60)" in n and "tighter than the default noon" in n for n in sixty_notes)


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
    assert labels == ["ema9_trend"]
    five = load_config("config/ema9_trend_5m.example.yaml")
    assert [label for label, _ids, _note in rule_book_plan(five)] == labels


def test_combined_only_labels_include_universe_and_size():
    ten = load_config("config/ema9_trend.example.yaml")
    risk = load_config("config/ema9_trend_risk.example.yaml")
    tsla = load_config("config/ema9_trend_tsla_mu.example.yaml")
    tsla_risk = load_config("config/ema9_trend_risk_tsla_mu.example.yaml")
    spy = load_config("config/ema9_trend_spy_qqq.example.yaml")
    spy_risk = load_config("config/ema9_trend_risk_spy_qqq.example.yaml")
    nvda = load_config("config/ema9_trend_nvda_amd.example.yaml")
    nvda_risk = load_config("config/ema9_trend_risk_nvda_amd.example.yaml")
    meta = load_config("config/ema9_trend_aapl_msft_meta.example.yaml")
    meta_risk = load_config("config/ema9_trend_risk_aapl_msft_meta.example.yaml")
    assert universe_tag(ten) == "AAPL+MSFT"
    assert universe_tag(tsla) == "TSLA+MU"
    assert universe_tag(spy) == "SPY+QQQ"
    assert universe_tag(nvda) == "NVDA+AMD"
    assert universe_tag(meta) == "AAPL+MSFT+META"
    assert sizing_tag(ten) == "10-share"
    assert sizing_tag(risk) == "1% risk"
    assert combined_book_label(ten) == "AAPL+MSFT 10-share"
    assert combined_book_label(risk) == "AAPL+MSFT 1% risk"
    assert combined_book_label(tsla) == "TSLA+MU 10-share"
    assert combined_book_label(tsla_risk) == "TSLA+MU 1% risk"
    assert combined_book_label(spy) == "SPY+QQQ 10-share"
    assert combined_book_label(spy_risk) == "SPY+QQQ 1% risk"
    assert combined_book_label(nvda) == "NVDA+AMD 10-share"
    assert combined_book_label(nvda_risk) == "NVDA+AMD 1% risk"
    assert combined_book_label(meta) == "AAPL+MSFT+META 10-share"
    assert combined_book_label(meta_risk) == "AAPL+MSFT+META 1% risk"
    assert [label for label, _ids, _note in rule_book_plan(tsla, combined_only=True)] == [
        "TSLA+MU 10-share"
    ]
    gated = " (cutoff 12:00, flat 15:55, lock +1.0%)"
    runs = run_rule_books(
        tsla,
        {},
        starting_equity=100_000,
        commission=0.0,
        slippage_pct=0.0,
        data_source="fixture",
        assumptions=["x"],
        label_prefix="15m",
        combined_only=True,
    )
    assert [block["label"] for block in runs] == [f"15m TSLA+MU 10-share{gated}"]


def test_format_monthly_side_by_side_lists_each_month():
    left = {
        "label": "TSLA+MU 10-share",
        "period_stats": {
            "months": [
                {
                    "year": 2026,
                    "calendar_month": 7,
                    "pnl": 10.0,
                    "trades": 2,
                    "win_rate_pct": 50.0,
                },
                {
                    "year": 2026,
                    "calendar_month": 8,
                    "pnl": -5.0,
                    "trades": 1,
                    "win_rate_pct": 0.0,
                },
            ]
        },
    }
    right = {
        "label": "AAPL+MSFT 10-share",
        "period_stats": {
            "months": [
                {
                    "year": 2026,
                    "calendar_month": 8,
                    "pnl": 20.0,
                    "trades": 3,
                    "win_rate_pct": 66.67,
                }
            ]
        },
    }
    table = "\n".join(format_monthly_side_by_side([left, right]))
    assert "| 2026-07 | $10.00 (2t, 50.00%) | — |" in table
    assert "| 2026-08 | $-5.00 (1t, 0.00%) | $20.00 (3t, 66.67%) |" in table


def test_run_rule_books_prefixes_and_soxl_breakout():
    cfg = load_config("config/ema9_trend_bracket_soxl.example.yaml")
    runs = run_rule_books(
        cfg,
        {},
        starting_equity=100_000,
        commission=0.0,
        slippage_pct=0.0,
        data_source="fixture",
        assumptions=["x"],
        label_prefix="15m",
        breakout_symbols=["SOXL"],
    )
    labels = [block["label"] for block in runs]
    gated = " (cutoff 12:00, flat 15:55, MA-cross)"
    assert f"15m ema9_trend{gated}" in labels
    assert f"15m ema9_trend SOXL{gated}" in labels
    meta = load_config("config/ema9_trend_aapl_msft_meta.example.yaml")
    meta_runs = run_rule_books(
        meta,
        {},
        starting_equity=100_000,
        commission=0.0,
        slippage_pct=0.0,
        data_source="fixture",
        assumptions=["x"],
        combined_only=True,
        breakout_symbols=["META"],
    )
    meta_labels = [block["label"] for block in meta_runs]
    meta_gated = " (cutoff 12:00, flat 15:55, lock +1.0%)"
    assert f"AAPL+MSFT+META 10-share{meta_gated}" in meta_labels
    assert f"ema9_trend META{meta_gated}" in meta_labels
    rsi_cfg = load_config("config/ema9_trend_bracket_rsi.example.yaml")
    rsi_runs = run_rule_books(
        rsi_cfg,
        {},
        starting_equity=100_000,
        commission=0.0,
        slippage_pct=0.0,
        data_source="fixture",
        assumptions=["x"],
        label_prefix="15m",
    )
    rsi_labels = [block["label"] for block in rsi_runs]
    assert "15m ema9_trend (cutoff 12:00, flat 15:55, MA-cross, RSI14 < 70)" in rsi_labels
    nobe = load_config("config/ema9_trend_bracket_nobe.example.yaml")
    nobe_runs = run_rule_books(
        nobe,
        {},
        starting_equity=100_000,
        commission=0.0,
        slippage_pct=0.0,
        data_source="fixture",
        assumptions=["x"],
        label_prefix="15m",
    )
    nobe_labels = [block["label"] for block in nobe_runs]
    assert "15m ema9_trend (cutoff 12:00, flat 15:55, 1.5/3.0)" in nobe_labels
    nobe12 = load_config("config/ema9_trend_bracket_nobe_12.example.yaml")
    nobe12_runs = run_rule_books(
        nobe12,
        {},
        starting_equity=100_000,
        commission=0.0,
        slippage_pct=0.0,
        data_source="fixture",
        assumptions=["x"],
        label_prefix="15m",
    )
    assert "15m ema9_trend (cutoff 12:00, flat 15:55, 1.0/2.0)" in [
        block["label"] for block in nobe12_runs
    ]
    sma20 = load_config("config/ema9_trend_bracket_sma20.example.yaml")
    assert session_gate_suffix(sma20) == " (cutoff 12:00, flat 15:55, SMA20/2.0)"
    sma20_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, sma20)
    assert any("stop_mode: sma20" in n and "SMA(20)" in n for n in sma20_notes)
    assert any("R = signal-bar close − SMA20" in n for n in sma20_notes)
    notake = load_config("config/ema9_trend_bracket_sma20_notake.example.yaml")
    assert session_gate_suffix(notake) == " (cutoff 12:00, flat 15:55, SMA20 stop)"
    sma20_runs = run_rule_books(
        sma20,
        {},
        starting_equity=100_000,
        commission=0.0,
        slippage_pct=0.0,
        data_source="fixture",
        assumptions=["x"],
        label_prefix="15m",
    )
    assert "15m ema9_trend (cutoff 12:00, flat 15:55, SMA20/2.0)" in [
        block["label"] for block in sma20_runs
    ]
    fixed1 = load_config("config/ema9_trend_bracket_nobe_fixed1.example.yaml")
    lock1 = load_config("config/ema9_trend_bracket_nobe_lock1.example.yaml")
    trail1 = load_config("config/ema9_trend_bracket_nobe_trail1.example.yaml")
    assert session_gate_suffix(fixed1) == " (cutoff 12:00, flat 15:55, entry 1.0%)"
    assert session_gate_suffix(lock1) == " (cutoff 12:00, flat 15:55, lock +1.0%)"
    assert session_gate_suffix(trail1) == " (cutoff 12:00, flat 15:55, trail 1.0%)"
    add05 = load_config("config/ema9_trend_bracket_nobe_lock1_add05.example.yaml")
    assert session_gate_suffix(add05) == " (cutoff 12:00, flat 15:55, lock +1.0% add@0.5%)"
    add05_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, add05)
    assert any("pyramid_add_pct" in n and "0.5" in n and "adds first" in n for n in add05_notes)
    half = load_config("config/ema9_trend_bracket_nobe_lock1_half.example.yaml")
    assert session_gate_suffix(half) == " (cutoff 12:00, flat 15:55, lock +1.0% half-take)"
    half_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, half)
    assert any("partial_take_on_lock" in n and "floor(half)" in n for n in half_notes)
    assert any("Size 1 skips" in n for n in half_notes)
    half_be = load_config("config/ema9_trend_bracket_nobe_lock1_half_be.example.yaml")
    assert session_gate_suffix(half_be) == " (cutoff 12:00, flat 15:55, lock +1.0% half-take BE)"
    half_be_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, half_be)
    assert any("partial_take_be" in n and "break-even" in n for n in half_be_notes)
    assert any("fill × 1.00" in n for n in half_be_notes)
    pyr2 = load_config("config/ema9_trend_bracket_nobe_lock1_pyramid2.example.yaml")
    assert session_gate_suffix(pyr2) == " (cutoff 12:00, flat 15:55, lock +1.0% pyramid/2.0)"
    pyr_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, pyr2)
    assert any("pyramid_on_lock" in n and "take_2pct" in n for n in pyr_notes)
    assert any("take_anchor: entry" in n for n in pyr_notes)
    lock1_vol = load_config("config/ema9_trend_bracket_nobe_lock1_vol.example.yaml")
    assert session_gate_suffix(lock1_vol) == " (cutoff 12:00, flat 15:55, lock +1.0%, vol>prev)"
    lock_vol_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, lock1_vol)
    assert any("signal-bar volume > previous-bar volume" in n for n in lock_vol_notes)
    assert any("stop_mode: lock_plus" in n and "entry×(1+1/100)" in n for n in lock_vol_notes)
    lh_vol = load_config("config/ema9_trend_bracket_nobe_lh_vol.example.yaml")
    assert session_gate_suffix(lh_vol) == " (cutoff 12:00, flat 15:55, lower-high, vol>prev)"
    lh_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, lh_vol)
    assert any("lower-high" in n and "previous bar's high" in n for n in lh_notes)
    assert any("signal-bar volume > previous-bar volume" in n for n in lh_notes)
    macross = load_config("config/ema9_trend_bracket_nobe_macross.example.yaml")
    assert session_gate_suffix(macross) == " (cutoff 12:00, flat 15:55, MA-cross close)"
    macross_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, macross)
    assert any("ma_cross_close" in n and "close-to-close" in n for n in macross_notes)
    assert any("that close wins" in n for n in macross_notes)
    assert not any("signal-bar volume > previous-bar volume" in n for n in macross_notes)
    pair_slope = load_config("config/ema9_trend_bracket_nobe_pair_slope.example.yaml")
    assert session_gate_suffix(pair_slope) == (
        " (cutoff 12:00, flat 15:55, MA-cross close, pair-cross SMA flat/rising)"
    )
    slope_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, pair_slope)
    assert any("EMA(9) crosses above SMA(20) close-to-close" in n for n in slope_notes)
    assert any("SMA20[curr] >= SMA20[prev]" in n for n in slope_notes)
    assert any("No RSI" in n and "No price-cross-" in n for n in slope_notes)
    assert any("Fill at the next bar open" in n for n in slope_notes)
    assert not any("close crosses above EMA(9)" in n for n in slope_notes)
    pair_ema = load_config("config/ema9_trend_bracket_nobe_pair_ema_slope.example.yaml")
    assert session_gate_suffix(pair_ema) == (
        " (cutoff 12:00, flat 15:55, MA-cross close, pair-cross EMA flat/rising)"
    )
    ema_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, pair_ema)
    assert any("EMA(9) crosses above SMA(20) close-to-close" in n for n in ema_notes)
    assert any("EMA9[curr] >= EMA9[prev]" in n for n in ema_notes)
    assert any("No SMA20 slope filter" in n for n in ema_notes)
    assert not any("SMA20[curr] >= SMA20[prev]" in n for n in ema_notes)
    assert any("Fill at the next bar open" in n for n in ema_notes)
    assert not any("close crosses above EMA(9)" in n for n in ema_notes)
    combo = load_config("config/ema9_trend_bracket_nobe_lock1_macross.example.yaml")
    assert session_gate_suffix(combo) == (
        " (cutoff 12:00, flat 15:55, MA-cross close, lock +1.0%)"
    )
    combo_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, combo)
    assert any("lock-+1%" in n and "ma_cross_close" in n for n in combo_notes)
    assert any("stop is checked first" in n for n in combo_notes)
    assert not any("signal-bar volume > previous-bar volume" in n for n in combo_notes)
    lock_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, lock1)
    assert any("stop_mode: lock_plus" in n and "entry×(1+1/100)" in n for n in lock_notes)
    trail_notes = assumptions_rules("commission=$0.00/fill, slippage=0.0%", 100_000.0, trail1)
    assert any("stop_mode: trail" in n and "peak_price_since_entry" in n for n in trail_notes)
    soxl = next(block for block in runs if block["label"] == f"15m ema9_trend SOXL{gated}")
    assert soxl["report"]["trades"] == 0
    assert any("Isolated SOXL" in n for n in soxl["report"]["notes"])


def test_format_side_by_side_table_lists_requested_metrics():
    left = {
        "report": {
            "trades": 44,
            "win_rate_pct": 50.0,
            "total_pnl": 1404.89,
            "max_drawdown": 407.70,
            "avg_win": 123.61,
            "avg_loss": -62.59,
            "exit_reasons": {"stop": 22, "take": 21, "eod": 1},
        }
    }
    right = {
        "report": {
            "trades": 10,
            "win_rate_pct": 40.0,
            "total_pnl": 100.0,
            "max_drawdown": 50.0,
            "avg_win": 40.0,
            "avg_loss": -20.0,
            "exit_reasons": {"stop": 6, "take": 4},
        }
    }
    lines = format_side_by_side_table(
        [("15m ema9_trend", left), ("5m ema9_trend", right)]
    )
    text = "\n".join(lines)
    assert "| Signals |" in text
    assert "| Skips |" in text
    assert "| Trades | 44 | 10 |" in text
    assert "| Win rate | 50.00% | 40.00% |" in text
    assert "| P&L | $1,404.89 | $100.00 |" in text
    assert "| Max DD | $407.70 | $50.00 |" in text
    assert "take 21, stop 22, eod 1" in text
    assert "take 4, stop 6" in text
    assert "| BE armed | 0 | 0 |" in text
    mixed = {
        "report": {
            "trades": 8,
            "win_rate_pct": 50.0,
            "total_pnl": 10.0,
            "max_drawdown": 4.0,
            "avg_win": 5.0,
            "avg_loss": -2.5,
            "exit_reasons": {"ema_invalid": 7, "eod": 1},
        }
    }
    ema_lines = "\n".join(format_side_by_side_table([("15m ema9_trend", mixed)]))
    assert "ema_invalid 7, take 0, stop 0, eod 1" in ema_lines
    sess = {
        "report": {
            "trades": 3,
            "win_rate_pct": 33.0,
            "total_pnl": 1.0,
            "max_drawdown": 2.0,
            "avg_win": 4.0,
            "avg_loss": -1.5,
            "exit_reasons": {"take": 1, "stop": 1, "session_flatten": 1},
        }
    }
    sess_lines = "\n".join(format_side_by_side_table([("gated", sess)]))
    assert "take 1, stop 1, session_flatten 1" in sess_lines


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
