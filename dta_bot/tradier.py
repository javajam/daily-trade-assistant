"""Tradier trading client. Sandbox is the default and hard to override."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from dta_bot.models import Account, Bar, OrderRequest, OrderResult, Position
from dta_bot.timeframes import drop_incomplete, duration, normalize

log = logging.getLogger("dta_bot.tradier")

SANDBOX_TRADING_URL = "https://sandbox.tradier.com/v1"
PRODUCTION_TRADING_URL = "https://api.tradier.com/v1"

LIVE_ENV_FLAG = "TRADIER_LIVE_TRADING"
LIVE_CONFIRM_ENV = "TRADIER_ALLOW_LIVE"
LIVE_CONFIRM_VALUE = "I_UNDERSTAND"


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def resolve_tradier_creds() -> tuple[Optional[str], Optional[str]]:
    token = (
        os.getenv("TRADIER_ACCESS_TOKEN")
        or os.getenv("TRADIER_TOKEN")
        or os.getenv("TRADIER_API_TOKEN")
    )
    account = os.getenv("TRADIER_ACCOUNT_ID") or os.getenv("TRADIER_ACCOUNT")
    if token:
        token = token.strip()
    if account:
        account = account.strip()
    return token or None, account or None


def resolve_tradier_url(
    *,
    allow_live: bool,
    endpoint: Optional[str] = None,
    base_url: Optional[str] = None,
) -> tuple[str, str]:
    """Return (base_url, mode). Mode is 'sandbox' unless every live gate is set.

    ``endpoint`` is ``sandbox`` / ``production`` from YAML. An explicit
    production URL or endpoint still requires the live triple-gate.
    """
    env_live = _env_truthy(LIVE_ENV_FLAG)
    confirm = os.getenv(LIVE_CONFIRM_ENV, "")
    want_prod = (endpoint or "").strip().lower() in {"production", "live", "prod"}
    if base_url:
        host = (urlparse(base_url).hostname or "").lower()
        if "sandbox" not in host and host not in {"localhost", "127.0.0.1"}:
            want_prod = True
    if allow_live and env_live and confirm == LIVE_CONFIRM_VALUE and want_prod:
        log.warning("LIVE Tradier URL selected — real money. Triple-gate passed.")
        url = (base_url or PRODUCTION_TRADING_URL).rstrip("/")
        return url, "live"
    if allow_live or env_live or confirm or want_prod:
        log.warning(
            "Tradier live/production requested incompletely "
            "(allow_live=%s %s=%s %s=%s endpoint=%s) — staying on SANDBOX.",
            allow_live,
            LIVE_ENV_FLAG,
            os.getenv(LIVE_ENV_FLAG),
            LIVE_CONFIRM_ENV,
            "set" if confirm else "unset",
            endpoint,
        )
    if base_url and "sandbox" in (urlparse(base_url).hostname or "").lower():
        return base_url.rstrip("/"), "sandbox"
    return SANDBOX_TRADING_URL, "sandbox"


def _as_list(payload: Any, *path: str) -> list[dict[str, Any]]:
    node: Any = payload
    for key in path:
        if not isinstance(node, dict):
            return []
        node = node.get(key)
        if node is None:
            return []
    if node is None:
        return []
    if isinstance(node, list):
        return [row for row in node if isinstance(row, dict)]
    if isinstance(node, dict):
        return [node]
    return []


def _host_is_sandbox(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return "sandbox" in host or host in {"localhost", "127.0.0.1"}


class TradierBroker:
    """Thin REST client for Tradier account / positions / orders."""

    def __init__(
        self,
        *,
        access_token: str,
        account_id: str,
        base_url: str = SANDBOX_TRADING_URL,
        mode: str = "sandbox",
        preview: bool = True,
        timeout: float = 15.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        if mode == "live" and _host_is_sandbox(base_url):
            raise RuntimeError("Refusing live mode against the Tradier sandbox endpoint")
        if mode != "live" and not _host_is_sandbox(base_url):
            raise RuntimeError(
                f"Sandbox/paper mode refuses non-sandbox Tradier URL {base_url!r}. "
                "Enable production only via allow_live + TRADIER_LIVE_TRADING + "
                f"{LIVE_CONFIRM_ENV}={LIVE_CONFIRM_VALUE} and tradier_endpoint: production."
            )
        self.mode = mode
        self.account_id = account_id
        self.preview = preview
        self.base_url = base_url.rstrip("/")
        self._own_client = client is None
        # Absolute URLs — do not set httpx base_url (a leading "/" path
        # would drop the /v1 prefix on sandbox.tradier.com/v1).
        self._client = client or httpx.Client(
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}{path if path.startswith('/') else '/' + path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._client.request(method, self._url(path), **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(f"Tradier {method} {path} -> {resp.status_code}: {resp.text}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def get_account(self) -> Account:
        data = self._request("GET", f"/accounts/{self.account_id}/balances")
        bal = data.get("balances") if isinstance(data, dict) else None
        if not isinstance(bal, dict):
            bal = data if isinstance(data, dict) else {}
        cash = bal.get("total_cash")
        if cash is None and isinstance(bal.get("cash"), dict):
            cash = bal["cash"].get("cash_available")
        buying = bal.get("stock_buying_power")
        if buying is None and isinstance(bal.get("margin"), dict):
            buying = bal["margin"].get("stock_buying_power")
        if buying is None:
            buying = bal.get("option_buying_power")
        pdt = bal.get("pdt")
        is_pdt = bool(pdt.get("day_trades")) if isinstance(pdt, dict) else False
        return Account(
            equity=float(bal.get("total_equity") or 0),
            cash=float(cash or 0),
            buying_power=float(buying or 0),
            status=str(bal.get("account_type") or bal.get("status") or ""),
            account_number=str(bal.get("account_number") or self.account_id),
            pattern_day_trader=is_pdt,
        )

    def get_positions(self) -> list[Position]:
        data = self._request("GET", f"/accounts/{self.account_id}/positions")
        out: list[Position] = []
        for row in _as_list(data, "positions", "position"):
            qty = float(row.get("quantity") or 0)
            cost = float(row.get("cost_basis") or 0)
            avg = abs(cost / qty) if qty else 0.0
            close = row.get("close_price") or row.get("last")
            mkt = float(close) * qty if close not in (None, "") else 0.0
            out.append(
                Position(
                    symbol=str(row.get("symbol") or "").upper(),
                    qty=abs(qty),
                    side="long" if qty >= 0 else "short",
                    avg_entry_price=avg,
                    market_value=mkt,
                    unrealized_pl=float(row.get("gain_loss") or 0),
                )
            )
        return [p for p in out if p.symbol]

    def list_orders(self) -> list[dict[str, Any]]:
        data = self._request("GET", f"/accounts/{self.account_id}/orders")
        rows = _as_list(data, "orders", "order")
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "id": str(row.get("id") or ""),
                    "symbol": str(row.get("symbol") or "").upper(),
                    "side": str(row.get("side") or ""),
                    "qty": row.get("quantity") or row.get("exec_quantity"),
                    "status": str(row.get("status") or ""),
                    "type": str(row.get("type") or ""),
                    "raw": row,
                }
            )
        return out

    def _order_form(self, order: OrderRequest, *, as_stop: bool = False) -> dict[str, str]:
        qty = int(round(float(order.qty)))
        if qty <= 0:
            raise ValueError("Tradier equity orders need a positive share count")
        duration = "gtc" if str(order.time_in_force).lower() == "gtc" else "day"
        form: dict[str, str] = {
            "class": "equity",
            "symbol": order.symbol.upper(),
            "quantity": str(qty),
            "duration": duration,
        }
        if as_stop:
            if order.stop_loss_price is None:
                raise ValueError("stop order requires stop_loss_price")
            form["side"] = "sell" if order.side == "buy" else "buy"
            form["type"] = "stop"
            form["stop"] = f"{float(order.stop_loss_price):.2f}"
        else:
            form["side"] = order.side
            form["type"] = "limit" if order.order_type == "limit" else "market"
            if order.order_type == "limit":
                if order.limit_price is None:
                    raise ValueError("limit order requires limit_price")
                form["price"] = f"{float(order.limit_price):.2f}"
        if order.client_order_id:
            form["tag"] = order.client_order_id[:255]
        return form

    def preview_order(self, order: OrderRequest, *, as_stop: bool = False) -> dict[str, Any]:
        form = self._order_form(order, as_stop=as_stop)
        log.info("Previewing %s Tradier order: %s", self.mode, form)
        data = self._request(
            "POST",
            f"/accounts/{self.account_id}/orders/preview",
            data=form,
        )
        return data if isinstance(data, dict) else {"raw": data}

    def _place(self, form: dict[str, str]) -> dict[str, Any]:
        log.info("Submitting %s Tradier order: %s", self.mode, form)
        data = self._request(
            "POST",
            f"/accounts/{self.account_id}/orders",
            data=form,
        )
        return data if isinstance(data, dict) else {"raw": data}

    def submit_order(self, order: OrderRequest) -> OrderResult:
        entry_form = self._order_form(order, as_stop=False)
        preview_raw: dict[str, Any] = {}
        if self.preview:
            preview_raw = self.preview_order(order, as_stop=False)
        data = self._place(entry_form)
        placed = data.get("order") if isinstance(data.get("order"), dict) else data
        stop_raw: dict[str, Any] = {}
        if order.stop_loss_price:
            stop_form = self._order_form(order, as_stop=True)
            if self.preview:
                self.preview_order(order, as_stop=True)
            stop_raw = self._place(stop_form)
        return OrderResult(
            id=str(placed.get("id") or ""),
            symbol=str(placed.get("symbol") or order.symbol),
            side=str(placed.get("side") or order.side),
            qty=float(placed.get("quantity") or order.qty),
            status=str(placed.get("status") or "submitted"),
            submitted=True,
            raw={"entry": data, "preview": preview_raw, "stop": stop_raw},
        )

    def cancel_order(self, order_id: str) -> None:
        self._request("DELETE", f"/accounts/{self.account_id}/orders/{order_id}")

    def cancel_all_orders(self) -> None:
        for row in self.list_orders():
            status = str(row.get("status") or "").lower()
            if status in {"filled", "expired", "canceled", "cancelled", "rejected"}:
                continue
            oid = row.get("id")
            if oid:
                self.cancel_order(str(oid))

    def close_position(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper()
        for row in self.list_orders():
            if str(row.get("symbol") or "").upper() != symbol:
                continue
            status = str(row.get("status") or "").lower()
            if status in {"filled", "expired", "canceled", "cancelled", "rejected"}:
                continue
            if row.get("id"):
                self.cancel_order(str(row["id"]))
        pos = next((p for p in self.get_positions() if p.symbol == symbol), None)
        if pos is None or pos.qty <= 0:
            return {"symbol": symbol, "closed": False, "reason": "no_position"}
        flatten = OrderRequest(
            symbol=symbol,
            side="sell" if str(pos.side).lower() in {"long", "buy"} else "buy",
            qty=pos.qty,
            order_type="market",
        )
        result = self.submit_order(flatten)
        return {"symbol": symbol, "closed": True, "order": result.raw}


# timesales supports 1min / 5min / 15min. Daily uses /markets/history.
TRADIER_TIMESALES_INTERVAL = {
    "1Min": "1min",
    "5Min": "5min",
    "15Min": "15min",
}


def parse_tradier_timesales(payload: Any) -> list[Bar]:
    """Turn Tradier timesales JSON into oldest-first Bar rows."""
    rows = _as_list(payload, "series", "data")
    bars: list[Bar] = []
    for row in rows:
        ts = _parse_tradier_ts(row)
        if ts is None:
            continue
        o, h, l, c = row.get("open"), row.get("high"), row.get("low"), row.get("close")
        if o is None or h is None or l is None or c is None:
            continue
        bars.append(
            Bar(
                timestamp=ts,
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=float(row.get("volume") or 0),
            )
        )
    bars.sort(key=lambda b: b.timestamp)
    return bars


def parse_tradier_history(payload: Any) -> list[Bar]:
    rows = _as_list(payload, "history", "day")
    bars: list[Bar] = []
    for row in rows:
        ts = _parse_tradier_ts(row)
        if ts is None:
            continue
        o, h, l, c = row.get("open"), row.get("high"), row.get("low"), row.get("close")
        if o is None or h is None or l is None or c is None:
            continue
        bars.append(
            Bar(
                timestamp=ts,
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=float(row.get("volume") or 0),
            )
        )
    bars.sort(key=lambda b: b.timestamp)
    return bars


def _parse_tradier_ts(row: dict[str, Any]) -> Optional[datetime]:
    raw = row.get("timestamp")
    if raw not in (None, ""):
        try:
            return datetime.fromtimestamp(int(raw), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass
    text = row.get("time") or row.get("date")
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class TradierMarketData:
    """Tradier timesales (1m/5m/15m) or daily history. Needs a Bearer token.

    Sandbox timesales is often empty or delayed — prefer Yahoo for the paper
    runner unless you explicitly set ``data_source: tradier``.
    """

    def __init__(
        self,
        *,
        access_token: str,
        base_url: str = SANDBOX_TRADING_URL,
        timeout: float = 15.0,
        client: Optional[httpx.Client] = None,
        now: Optional[datetime] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._now = now
        self._own = client is None
        self._client = client or httpx.Client(
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        if self._own:
            self._client.close()

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}{path if path.startswith('/') else '/' + path}"

    def get_bars(self, symbol: str, timeframe: str, limit: int = 80) -> list[Bar]:
        tf = normalize(timeframe)
        now = self._now or datetime.now(timezone.utc)
        if tf in TRADIER_TIMESALES_INTERVAL:
            span = duration(tf) * max(limit, 20) * 4
            start = (now - span).strftime("%Y-%m-%d %H:%M")
            resp = self._client.get(
                self._url("/markets/timesales"),
                params={
                    "symbol": symbol.upper(),
                    "interval": TRADIER_TIMESALES_INTERVAL[tf],
                    "start": start,
                    "session_filter": "open",
                },
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Tradier timesales {symbol} {tf} -> {resp.status_code}: {resp.text}"
                )
            bars = parse_tradier_timesales(resp.json())
        elif tf == "1Day":
            start = (now - timedelta(days=max(limit * 2, 40))).strftime("%Y-%m-%d")
            resp = self._client.get(
                self._url("/markets/history"),
                params={
                    "symbol": symbol.upper(),
                    "interval": "daily",
                    "start": start,
                },
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Tradier history {symbol} {tf} -> {resp.status_code}: {resp.text}"
                )
            bars = parse_tradier_history(resp.json())
        else:
            raise ValueError(
                f"Tradier market data has no {timeframe!r} interval "
                "(timesales is 1m/5m/15m; history is daily). "
                "Set settings.data_source: yahoo for other bar sizes."
            )
        bars = drop_incomplete(bars, tf, now=now)
        log.debug("Tradier %s %s: %s closed bars", symbol, tf, len(bars))
        return bars[-limit:]
