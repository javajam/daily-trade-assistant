"""Alpaca trading client. Paper endpoint is the default and hard to override."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Optional, Protocol

import httpx

from dta_bot.models import Account, OrderRequest, OrderResult, Position

log = logging.getLogger("dta_bot.broker")

PAPER_TRADING_URL = "https://paper-api.alpaca.markets"
LIVE_TRADING_URL = "https://api.alpaca.markets"

# Live trading requires ALL of these. Any missing piece keeps us on paper.
LIVE_ENV_FLAG = "ALPACA_LIVE_TRADING"
LIVE_CONFIRM_ENV = "ALPACA_ALLOW_LIVE"
LIVE_CONFIRM_VALUE = "I_UNDERSTAND"


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def resolve_api_keys() -> tuple[Optional[str], Optional[str]]:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("APCA_API_SECRET_KEY")
    return key, secret


def resolve_trading_url(*, allow_live: bool) -> tuple[str, str]:
    """Return (base_url, mode). Mode is 'paper' unless every live gate is set."""
    env_live = _env_truthy(LIVE_ENV_FLAG)
    confirm = os.getenv(LIVE_CONFIRM_ENV, "")
    if allow_live and env_live and confirm == LIVE_CONFIRM_VALUE:
        log.warning("LIVE trading URL selected — real money. Triple-gate passed.")
        return LIVE_TRADING_URL, "live"
    if allow_live or env_live or confirm:
        log.warning(
            "Live trading requested incompletely "
            "(allow_live=%s %s=%s %s=%s) — staying on PAPER.",
            allow_live,
            LIVE_ENV_FLAG,
            os.getenv(LIVE_ENV_FLAG),
            LIVE_CONFIRM_ENV,
            "set" if confirm else "unset",
        )
    return PAPER_TRADING_URL, "paper"


class Broker(Protocol):
    mode: str

    def get_account(self) -> Account: ...
    def get_positions(self) -> list[Position]: ...
    def submit_order(self, order: OrderRequest) -> OrderResult: ...
    def cancel_order(self, order_id: str) -> None: ...
    def cancel_all_orders(self) -> None: ...
    def close_position(self, symbol: str) -> dict[str, Any]: ...


class AlpacaBroker:
    """Thin REST client for account / positions / orders."""

    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        base_url: str = PAPER_TRADING_URL,
        mode: str = "paper",
        timeout: float = 15.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        if mode == "live" and "paper-api" in base_url:
            raise RuntimeError("Refusing live mode against the paper endpoint")
        if mode != "live" and "paper-api" not in base_url and "localhost" not in base_url:
            # Extra belt: a paper-mode client must not silently hit live.
            raise RuntimeError(
                f"Paper mode refuses non-paper trading URL {base_url!r}. "
                "Enable live only via allow_live + ALPACA_LIVE_TRADING + "
                f"{LIVE_CONFIRM_ENV}={LIVE_CONFIRM_VALUE}."
            )
        self.mode = mode
        self.base_url = base_url.rstrip("/")
        self._own_client = client is None
        self._client = client or httpx.Client(
            base_url=self.base_url,
            headers={
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": api_secret,
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(f"Alpaca {method} {path} -> {resp.status_code}: {resp.text}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def get_account(self) -> Account:
        data = self._request("GET", "/v2/account")
        return Account(
            equity=float(data.get("equity") or 0),
            cash=float(data.get("cash") or 0),
            buying_power=float(data.get("buying_power") or 0),
            status=str(data.get("status") or ""),
            account_number=str(data.get("account_number") or ""),
            pattern_day_trader=bool(data.get("pattern_day_trader")),
        )

    def get_positions(self) -> list[Position]:
        data = self._request("GET", "/v2/positions")
        out: list[Position] = []
        for row in data or []:
            out.append(
                Position(
                    symbol=row["symbol"],
                    qty=float(row.get("qty") or 0),
                    side=str(row.get("side") or "long"),
                    avg_entry_price=float(row.get("avg_entry_price") or 0),
                    market_value=float(row.get("market_value") or 0),
                    unrealized_pl=float(row.get("unrealized_pl") or 0),
                )
            )
        return out

    def submit_order(self, order: OrderRequest) -> OrderResult:
        payload: dict[str, Any] = {
            "symbol": order.symbol,
            "qty": str(order.qty),
            "side": order.side,
            "type": order.order_type,
            "time_in_force": order.time_in_force,
            "client_order_id": order.client_order_id or f"dta-{uuid.uuid4().hex[:16]}",
        }
        if order.order_type == "limit":
            if order.limit_price is None:
                raise ValueError("limit order requires limit_price")
            payload["limit_price"] = str(round(order.limit_price, 2))
        if order.stop_loss_price or order.take_profit_price:
            payload["order_class"] = "bracket"
            if order.take_profit_price:
                payload["take_profit"] = {"limit_price": str(round(order.take_profit_price, 2))}
            if order.stop_loss_price:
                payload["stop_loss"] = {"stop_price": str(round(order.stop_loss_price, 2))}
        log.info("Submitting %s order: %s", self.mode, payload)
        data = self._request("POST", "/v2/orders", json=payload)
        return OrderResult(
            id=str(data.get("id") or ""),
            symbol=str(data.get("symbol") or order.symbol),
            side=str(data.get("side") or order.side),
            qty=float(data.get("qty") or order.qty),
            status=str(data.get("status") or "submitted"),
            submitted=True,
            raw=data if isinstance(data, dict) else {},
        )

    def cancel_order(self, order_id: str) -> None:
        self._request("DELETE", f"/v2/orders/{order_id}")

    def cancel_all_orders(self) -> None:
        self._request("DELETE", "/v2/orders")

    def close_position(self, symbol: str) -> dict[str, Any]:
        data = self._request("DELETE", f"/v2/positions/{symbol}")
        return data if isinstance(data, dict) else {}


class DryRunBroker:
    """Satisfies Broker but never sends orders. Used for --dry-run."""

    def __init__(self, inner: Optional[AlpacaBroker] = None, equity: float = 100_000.0) -> None:
        self.inner = inner
        self.mode = f"dry-run/{inner.mode if inner else 'offline'}"
        self._equity = equity
        self.submitted: list[OrderRequest] = []

    def get_account(self) -> Account:
        if self.inner:
            return self.inner.get_account()
        return Account(equity=self._equity, cash=self._equity, buying_power=self._equity, status="ACTIVE")

    def get_positions(self) -> list[Position]:
        if self.inner:
            return self.inner.get_positions()
        return []

    def submit_order(self, order: OrderRequest) -> OrderResult:
        self.submitted.append(order)
        log.info("DRY-RUN would submit %s %s x%s %s", order.side, order.symbol, order.qty, order.order_type)
        return OrderResult(
            id="dry-run",
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            status="dry_run",
            submitted=False,
        )

    def cancel_order(self, order_id: str) -> None:
        log.info("DRY-RUN would cancel order %s", order_id)

    def cancel_all_orders(self) -> None:
        log.info("DRY-RUN would cancel all open orders")

    def close_position(self, symbol: str) -> dict[str, Any]:
        log.info("DRY-RUN would close position %s", symbol)
        return {"dry_run": True, "symbol": symbol}


def build_broker(*, allow_live: bool, dry_run: bool) -> Broker:
    url, mode = resolve_trading_url(allow_live=allow_live)
    key, secret = resolve_api_keys()
    inner: Optional[AlpacaBroker] = None
    if key and secret:
        inner = AlpacaBroker(api_key=key, api_secret=secret, base_url=url, mode=mode)
    elif not dry_run:
        raise RuntimeError(
            "ALPACA_API_KEY / ALPACA_API_SECRET are required to place orders. "
            "Use --dry-run or a --fixture file to evaluate without credentials."
        )
    if dry_run:
        return DryRunBroker(inner=inner)
    assert inner is not None
    return inner
