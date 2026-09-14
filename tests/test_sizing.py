import pytest

from dta_bot.config import ActionSpec, SizeSpec
from dta_bot.models import Account
from dta_bot.sizing import bracket_prices, build_order, risk_distance, shares_for, sma_stop_valid


def _acct(equity: float = 100_000) -> Account:
    return Account(equity=equity, cash=equity, buying_power=equity, status="ACTIVE")


def test_shares_direct():
    action = ActionSpec(type="buy", size=SizeSpec(type="shares", value=10))
    assert shares_for(action, _acct(), 50.0) == 10


def test_percent_equity():
    action = ActionSpec(type="buy", size=SizeSpec(type="percent_equity", value=2))
    # 2% of 100k = 2000 / 50 = 40
    assert shares_for(action, _acct(), 50.0) == 40


def test_percent_rounds_down_and_rejects_zero():
    action = ActionSpec(type="buy", size=SizeSpec(type="percent_equity", value=0.01))
    with pytest.raises(ValueError, match="0 shares"):
        shares_for(action, _acct(1000), 500.0)


def test_bracket_buy():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="shares", value=1),
        stop_loss_pct=10,
        take_profit_pct=20,
    )
    stop, take = bracket_prices(action, 100.0, "buy")
    assert stop == pytest.approx(90.0)
    assert take == pytest.approx(120.0)


def test_lower_high_ignores_percent_take_and_has_no_stop_when_omitted():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="shares", value=1),
        exit="lower_high",
        take_profit_pct=20,
    )
    assert bracket_prices(action, 100.0, "buy") == (None, None)
    with_stop = ActionSpec(
        type="buy",
        size=SizeSpec(type="shares", value=1),
        exit="lower_high",
        stop_loss_pct=10,
        take_profit_pct=20,
    )
    stop, take = bracket_prices(with_stop, 100.0, "buy")
    assert stop == pytest.approx(90.0)
    assert take is None


def test_ema_invalid_ignores_percent_take_keeps_optional_stop():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="shares", value=1),
        exit="ema_invalid",
        stop_loss_pct=10,
        take_profit_pct=20,
    )
    stop, take = bracket_prices(action, 100.0, "buy")
    assert stop == pytest.approx(90.0)
    assert take is None
    off = ActionSpec(type="buy", size=SizeSpec(type="shares", value=1), exit="ema_invalid")
    assert bracket_prices(off, 100.0, "buy") == (None, None)


def test_ma_cross_ignores_percent_take_keeps_stop():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="shares", value=1),
        exit="ma_cross",
        stop_loss_pct=1.5,
        take_profit_pct=3.0,
        exit_ema_period=9,
        exit_sma_period=20,
    )
    stop, take = bracket_prices(action, 100.0, "buy")
    assert stop == pytest.approx(98.5)
    assert take is None


def test_risk_pct_matches_locked_formula():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="risk_pct", equity_risk=0.01, stop_pct=1.5),
        stop_loss_pct=1.5,
        take_profit_pct=3.0,
    )
    # floor( (0.01 * 100000) / (0.015 * 200) ) = floor(100000 / (1.5 * 200)) = 333
    assert shares_for(action, _acct(100_000), 200.0) == 333
    # Recalculate from a later equity print.
    assert shares_for(action, _acct(101_500), 210.0) == 322


def test_risk_pct_tighter_stop_sizes_more_shares():
    wide = ActionSpec(
        type="buy",
        size=SizeSpec(type="risk_pct", equity_risk=0.01, stop_pct=1.5),
        stop_loss_pct=1.5,
        take_profit_pct=3.0,
    )
    tight = ActionSpec(
        type="buy",
        size=SizeSpec(type="risk_pct", equity_risk=0.01, stop_pct=1.0),
        stop_loss_pct=1.0,
        take_profit_pct=2.0,
    )
    # Same 1% equity risk: 1.0% stop → floor(1000 / (0.01 * 200)) = 500
    assert shares_for(wide, _acct(100_000), 200.0) == 333
    assert shares_for(tight, _acct(100_000), 200.0) == 500


def test_risk_pct_uses_action_stop_when_size_omits_it():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="risk_pct", equity_risk=0.01),
        stop_loss_pct=1.5,
    )
    assert shares_for(action, _acct(100_000), 200.0) == 333


def test_risk_pct_rejects_missing_stop_and_zero_shares():
    missing = ActionSpec(type="buy", size=SizeSpec(type="risk_pct", equity_risk=0.01))
    with pytest.raises(ValueError, match="stop_pct"):
        shares_for(missing, _acct(), 50.0)
    tiny = ActionSpec(
        type="buy",
        size=SizeSpec(type="risk_pct", equity_risk=0.01, stop_pct=1.5),
    )
    with pytest.raises(ValueError, match="0 shares"):
        shares_for(tiny, _acct(100), 200.0)


def test_risk_pct_equity_risk_must_be_a_fraction():
    with pytest.raises(ValueError, match="fraction"):
        SizeSpec(type="risk_pct", equity_risk=1.5, stop_pct=1.5)


def test_sma20_bracket_uses_signal_sma_not_percent():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="shares", value=10),
        stop_mode="sma20",
        take_profit_pct=2.0,
    )
    stop, take = bracket_prices(action, 100.0, "buy", sma_value=98.5)
    assert stop == pytest.approx(98.5)
    assert take == pytest.approx(102.0)
    invalid = bracket_prices(action, 100.0, "buy", sma_value=100.4)
    assert invalid == (None, pytest.approx(102.0))
    missing = bracket_prices(action, 100.0, "buy")
    assert missing[0] is None
    notake = ActionSpec(type="buy", size=SizeSpec(type="shares", value=10), stop_mode="sma20")
    stop_only, take_only = bracket_prices(notake, 100.0, "buy", sma_value=97.0)
    assert stop_only == pytest.approx(97.0)
    assert take_only is None


def test_sma_stop_valid_and_risk_distance():
    assert sma_stop_valid("buy", 100.0, 98.0) is True
    assert sma_stop_valid("buy", 100.0, 100.0) is False
    assert sma_stop_valid("buy", 100.0, 101.0) is False
    assert sma_stop_valid("sell", 100.0, 102.0) is True
    assert risk_distance("buy", 200.0, 197.0) == pytest.approx(3.0)
    assert risk_distance("buy", 200.0, 201.0) is None


def test_risk_pct_sma20_uses_entry_to_sma_distance():
    action = ActionSpec(
        type="buy",
        size=SizeSpec(type="risk_pct", equity_risk=0.01),
        stop_mode="sma20",
        take_profit_pct=2.0,
    )
    # R = 200 - 197 = 3; floor(1000 / 3) = 333
    assert shares_for(action, _acct(100_000), 200.0, stop_price=197.0) == 333
    tighter = shares_for(action, _acct(100_000), 200.0, stop_price=199.0)
    assert tighter == 1000
    with pytest.raises(ValueError, match="SMA stop"):
        shares_for(action, _acct(100_000), 200.0, stop_price=201.0)
    with pytest.raises(ValueError, match="stop_price"):
        shares_for(action, _acct(100_000), 200.0)


def test_build_market_buy_order():
    action = ActionSpec(type="buy", size=SizeSpec(type="shares", value=5), stop_loss_pct=2)
    order = build_order(symbol="AAPL", action=action, account=_acct(), last_price=100.0, position=None)
    assert order is not None
    assert order.side == "buy"
    assert order.qty == 5
    assert order.stop_loss_price == pytest.approx(98.0)
