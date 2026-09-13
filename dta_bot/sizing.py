"""Translate action size specs into share quantities and optional bracket prices."""

from __future__ import annotations

import math
from typing import Optional

from dta_bot.config import ActionSpec
from dta_bot.models import Account, OrderRequest, Position, Side


def stop_pct_for(action: ActionSpec) -> Optional[float]:
    """Stop distance in percent (1.5 = 1.5%) for risk_pct sizing."""
    if action.size is not None and action.size.stop_pct:
        return action.size.stop_pct
    if action.stop_loss_pct:
        return action.stop_loss_pct
    return None


def shares_for(action: ActionSpec, account: Account, last_price: float) -> float:
    if action.type == "close":
        return 0.0
    assert action.size is not None
    if last_price <= 0:
        raise ValueError("last_price must be positive")
    if action.size.type == "shares":
        qty = action.size.value
    elif action.size.type == "percent_equity":
        notional = account.equity * (action.size.value / 100.0)
        qty = notional / last_price
    elif action.size.type == "risk_pct":
        risk_frac = action.size.equity_risk
        if risk_frac is None:
            raise ValueError("risk_pct sizing requires equity_risk")
        stop_pct = stop_pct_for(action)
        if stop_pct is None or stop_pct <= 0:
            raise ValueError("risk_pct sizing requires stop_pct or action.stop_loss_pct")
        # shares = floor( (equity_risk * equity) / ((stop_pct/100) * price) )
        #        = floor( equity / ((stop_pct / (100 * equity_risk)) * price) )
        # With equity_risk=0.01 and stop_pct=1.5: floor(equity / (1.5 * price))
        qty = (risk_frac * account.equity) / ((stop_pct / 100.0) * last_price)
    else:
        raise ValueError(f"unknown size type {action.size.type!r}")
    qty = math.floor(qty)
    if qty < 1:
        raise ValueError(
            f"size rounds to 0 shares (equity={account.equity:.2f} price={last_price:.4f})"
        )
    return float(qty)


def buy_notional(qty: float, price: float, commission: float = 0.0) -> float:
    return qty * price + commission


def limit_price(action: ActionSpec, last_price: float, side: Side) -> Optional[float]:
    if action.order != "limit":
        return None
    offset = action.limit_offset_pct or 0.0
    if side == "buy":
        return last_price * (1.0 + offset / 100.0)
    return last_price * (1.0 - offset / 100.0)


def bracket_prices(action: ActionSpec, last_price: float, side: Side) -> tuple[Optional[float], Optional[float]]:
    stop = None
    take = None
    if action.stop_loss_pct:
        if side == "buy":
            stop = last_price * (1.0 - action.stop_loss_pct / 100.0)
        else:
            stop = last_price * (1.0 + action.stop_loss_pct / 100.0)
    # ema_invalid / ma_cross hold until the MA signal; ignore % take.
    if action.exit not in {"ema_invalid", "ma_cross"} and action.take_profit_pct:
        if side == "buy":
            take = last_price * (1.0 + action.take_profit_pct / 100.0)
        else:
            take = last_price * (1.0 - action.take_profit_pct / 100.0)
    return stop, take


def build_order(
    *,
    symbol: str,
    action: ActionSpec,
    account: Account,
    last_price: float,
    position: Optional[Position],
    client_order_id: Optional[str] = None,
) -> Optional[OrderRequest]:
    if action.type == "close":
        return None  # runner uses close_position()
    side: Side = "buy" if action.type == "buy" else "sell"
    qty = shares_for(action, account, last_price)
    stop, take = bracket_prices(action, last_price, side)
    return OrderRequest(
        symbol=symbol,
        side=side,
        qty=qty,
        order_type=action.order,
        time_in_force=action.time_in_force,
        limit_price=limit_price(action, last_price, side),
        stop_loss_price=stop,
        take_profit_price=take,
        client_order_id=client_order_id,
    )
