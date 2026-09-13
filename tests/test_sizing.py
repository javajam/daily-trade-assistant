import pytest

from dta_bot.config import ActionSpec, SizeSpec
from dta_bot.models import Account
from dta_bot.sizing import bracket_prices, build_order, shares_for


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


def test_build_market_buy_order():
    action = ActionSpec(type="buy", size=SizeSpec(type="shares", value=5), stop_loss_pct=2)
    order = build_order(symbol="AAPL", action=action, account=_acct(), last_price=100.0, position=None)
    assert order is not None
    assert order.side == "buy"
    assert order.qty == 5
    assert order.stop_loss_price == pytest.approx(98.0)
