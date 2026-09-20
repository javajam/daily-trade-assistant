"""Tradier sandbox broker + URL gates. No live HTTP — mocked clients only."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dta_bot.broker import DryRunBroker, build_broker
from dta_bot.cli import main
from dta_bot.market_data import YahooMarketData, build_market_data
from dta_bot.models import Bar, OrderRequest
from dta_bot.tradier import (
    LIVE_CONFIRM_ENV,
    LIVE_CONFIRM_VALUE,
    LIVE_ENV_FLAG,
    PRODUCTION_TRADING_URL,
    SANDBOX_TRADING_URL,
    TradierBroker,
    parse_tradier_history,
    parse_tradier_timesales,
    resolve_tradier_creds,
    resolve_tradier_url,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status_code = status
        self._payload = payload
        self.text = "" if payload is None else str(payload)
        self.content = b"{}" if payload else b""

    def json(self):
        return self._payload


class ScriptedClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append({"method": method.upper(), "path": path, "kwargs": kwargs})
        if not self._responses:
            return FakeResponse({"error": "unexpected extra request"}, status=500)
        item = self._responses.pop(0)
        if isinstance(item, FakeResponse):
            return item
        if isinstance(item, tuple):
            return FakeResponse(item[1], status=item[0])
        return FakeResponse(item)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)


def test_default_is_sandbox(monkeypatch):
    monkeypatch.delenv(LIVE_ENV_FLAG, raising=False)
    monkeypatch.delenv(LIVE_CONFIRM_ENV, raising=False)
    url, mode = resolve_tradier_url(allow_live=False)
    assert mode == "sandbox"
    assert url == SANDBOX_TRADING_URL


def test_incomplete_live_gates_stay_sandbox(monkeypatch):
    monkeypatch.setenv(LIVE_ENV_FLAG, "true")
    monkeypatch.delenv(LIVE_CONFIRM_ENV, raising=False)
    url, mode = resolve_tradier_url(allow_live=True, endpoint="production")
    assert mode == "sandbox"
    assert url == SANDBOX_TRADING_URL


def test_production_url_without_gates_stays_sandbox(monkeypatch):
    monkeypatch.delenv(LIVE_ENV_FLAG, raising=False)
    monkeypatch.delenv(LIVE_CONFIRM_ENV, raising=False)
    url, mode = resolve_tradier_url(
        allow_live=False,
        base_url=PRODUCTION_TRADING_URL,
    )
    assert mode == "sandbox"
    assert url == SANDBOX_TRADING_URL


def test_all_gates_required_for_live(monkeypatch):
    monkeypatch.setenv(LIVE_ENV_FLAG, "true")
    monkeypatch.setenv(LIVE_CONFIRM_ENV, LIVE_CONFIRM_VALUE)
    url, mode = resolve_tradier_url(allow_live=True, endpoint="production")
    assert mode == "live"
    assert url == PRODUCTION_TRADING_URL


def test_sandbox_client_refuses_production_url():
    with pytest.raises(RuntimeError, match="refuses non-sandbox"):
        TradierBroker(
            access_token="t",
            account_id="VA000",
            base_url=PRODUCTION_TRADING_URL,
            mode="sandbox",
        )


def test_live_client_refuses_sandbox_url():
    with pytest.raises(RuntimeError, match="sandbox endpoint"):
        TradierBroker(
            access_token="t",
            account_id="VA000",
            base_url=SANDBOX_TRADING_URL,
            mode="live",
        )


def test_resolve_creds(monkeypatch):
    monkeypatch.delenv("TRADIER_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TRADIER_TOKEN", raising=False)
    monkeypatch.delenv("TRADIER_API_TOKEN", raising=False)
    monkeypatch.delenv("TRADIER_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("TRADIER_ACCOUNT", raising=False)
    assert resolve_tradier_creds() == (None, None)
    monkeypatch.setenv("TRADIER_ACCESS_TOKEN", " tok ")
    monkeypatch.setenv("TRADIER_ACCOUNT_ID", " VA123 ")
    assert resolve_tradier_creds() == ("tok", "VA123")


def test_build_broker_tradier_requires_creds(monkeypatch):
    monkeypatch.delenv("TRADIER_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TRADIER_ACCOUNT_ID", raising=False)
    with pytest.raises(RuntimeError, match="TRADIER_ACCESS_TOKEN"):
        build_broker(allow_live=False, dry_run=False, name="tradier")


def test_build_broker_tradier_dry_run_without_creds(monkeypatch):
    monkeypatch.delenv("TRADIER_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TRADIER_ACCOUNT_ID", raising=False)
    broker = build_broker(allow_live=False, dry_run=True, name="tradier")
    assert isinstance(broker, DryRunBroker)
    assert broker.inner is None
    result = broker.submit_order(OrderRequest(symbol="AAPL", side="buy", qty=10))
    assert result.submitted is False


def _broker(client, preview=True) -> TradierBroker:
    return TradierBroker(
        access_token="t",
        account_id="VA000",
        base_url=SANDBOX_TRADING_URL,
        mode="sandbox",
        preview=preview,
        client=client,
    )


def test_get_account_and_positions_parse_single_and_list():
    client = ScriptedClient(
        [
            {
                "balances": {
                    "total_equity": "100000",
                    "total_cash": "80000",
                    "stock_buying_power": "160000",
                    "account_number": "VA000",
                    "account_type": "margin",
                    "pdt": {"day_trades": 0},
                }
            },
            {"positions": {"position": {"symbol": "AAPL", "quantity": "10", "cost_basis": "1800", "close_price": "190", "gain_loss": "100"}}},
        ]
    )
    broker = _broker(client)
    acct = broker.get_account()
    assert acct.equity == 100000
    assert acct.cash == 80000
    assert acct.buying_power == 160000
    assert acct.account_number == "VA000"
    positions = broker.get_positions()
    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"
    assert positions[0].qty == 10
    assert positions[0].avg_entry_price == 180
    assert positions[0].side == "long"
    assert client.calls[0]["path"] == f"{SANDBOX_TRADING_URL}/accounts/VA000/balances"
    assert client.calls[1]["path"] == f"{SANDBOX_TRADING_URL}/accounts/VA000/positions"


def test_list_orders_empty_and_cancel_all():
    client = ScriptedClient(
        [
            {"orders": "null"},
            {
                "orders": {
                    "order": [
                        {"id": 1, "symbol": "AAPL", "status": "open", "side": "sell", "type": "stop", "quantity": 10},
                        {"id": 2, "symbol": "MSFT", "status": "filled", "side": "buy", "type": "market", "quantity": 10},
                    ]
                }
            },
            {},
        ]
    )
    broker = _broker(client)
    assert broker.list_orders() == []
    broker.cancel_all_orders()
    methods = [c["method"] for c in client.calls]
    assert methods == ["GET", "GET", "DELETE"]
    assert client.calls[2]["path"] == f"{SANDBOX_TRADING_URL}/accounts/VA000/orders/1"


def test_submit_order_previews_then_places_entry_and_stop():
    client = ScriptedClient(
        [
            {"order": {"status": "ok"}},
            {"order": {"id": 11, "symbol": "AAPL", "side": "buy", "quantity": 10, "status": "ok"}},
            {"order": {"status": "ok"}},
            {"order": {"id": 12, "symbol": "AAPL", "side": "sell", "type": "stop", "status": "ok"}},
        ]
    )
    broker = _broker(client, preview=True)
    result = broker.submit_order(
        OrderRequest(
            symbol="AAPL",
            side="buy",
            qty=10,
            order_type="market",
            stop_loss_price=189.12,
            client_order_id="dta-test",
        )
    )
    assert result.submitted is True
    assert result.id == "11"
    assert result.symbol == "AAPL"
    paths = [c["path"] for c in client.calls]
    assert paths == [
        f"{SANDBOX_TRADING_URL}/accounts/VA000/orders/preview",
        f"{SANDBOX_TRADING_URL}/accounts/VA000/orders",
        f"{SANDBOX_TRADING_URL}/accounts/VA000/orders/preview",
        f"{SANDBOX_TRADING_URL}/accounts/VA000/orders",
    ]
    entry_form = client.calls[1]["kwargs"]["data"]
    assert entry_form["class"] == "equity"
    assert entry_form["side"] == "buy"
    assert entry_form["type"] == "market"
    assert entry_form["quantity"] == "10"
    assert entry_form["tag"] == "dta-test"
    stop_form = client.calls[3]["kwargs"]["data"]
    assert stop_form["side"] == "sell"
    assert stop_form["type"] == "stop"
    assert stop_form["stop"] == "189.12"


def test_close_position_cancels_then_markets_out():
    client = ScriptedClient(
        [
            {
                "orders": {
                    "order": {
                        "id": 99,
                        "symbol": "AAPL",
                        "status": "pending",
                        "type": "stop",
                    }
                }
            },
            {},
            {"positions": {"position": {"symbol": "AAPL", "quantity": "10", "cost_basis": "1800"}}},
            {"order": {"id": 100, "symbol": "AAPL", "side": "sell", "quantity": 10, "status": "ok"}},
        ]
    )
    broker = _broker(client, preview=False)
    out = broker.close_position("AAPL")
    assert out["closed"] is True
    methods = [c["method"] for c in client.calls]
    assert methods == ["GET", "DELETE", "GET", "POST"]
    flatten = client.calls[3]["kwargs"]["data"]
    assert flatten["side"] == "sell"
    assert flatten["type"] == "market"
    assert flatten["quantity"] == "10"


def test_parse_tradier_timesales_and_history():
    bars = parse_tradier_timesales(
        {
            "series": {
                "data": {
                    "time": "2026-09-18T13:30:00",
                    "timestamp": 1726666200,
                    "open": 1,
                    "high": 2,
                    "low": 0.5,
                    "close": 1.5,
                    "volume": 10,
                }
            }
        }
    )
    assert len(bars) == 1
    assert bars[0].open == 1
    assert bars[0].close == 1.5
    days = parse_tradier_history(
        {
            "history": {
                "day": [
                    {"date": "2026-09-17", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1},
                    {"date": "2026-09-18", "open": 10.5, "high": 12, "low": 10, "close": 11, "volume": 2},
                ]
            }
        }
    )
    assert [d.close for d in days] == [10.5, 11]


def test_yahoo_market_data_uses_fetch_and_trims(monkeypatch):
    now = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    series = [
        Bar(datetime(2026, 9, 18, 18, 30, tzinfo=timezone.utc), 1, 2, 1, 1.5, 10),
        Bar(datetime(2026, 9, 18, 18, 45, tzinfo=timezone.utc), 1.5, 2, 1, 1.6, 10),
        Bar(datetime(2026, 9, 18, 19, 45, tzinfo=timezone.utc), 1.6, 2, 1, 1.7, 10),
    ]

    def fake_fetch(symbol, timeframe, client=None, range_hint=None):
        assert symbol == "AAPL"
        return list(series)

    monkeypatch.setattr("dta_bot.history.fetch_yahoo_bars", fake_fetch)
    data = YahooMarketData(now=now)
    got = data.get_bars("AAPL", "15m", limit=2)
    assert len(got) == 2
    assert got[-1].close == 1.7


def test_build_market_data_yahoo_needs_no_alpaca(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    data = build_market_data(feed="iex", fixture=None, source="yahoo")
    assert isinstance(data, YahooMarketData)


def test_build_market_data_tradier_needs_token(monkeypatch):
    monkeypatch.delenv("TRADIER_ACCESS_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="TRADIER_ACCESS_TOKEN"):
        build_market_data(feed="iex", fixture=None, source="tradier")


def test_cli_status_tradier_sandbox_no_secrets(capsys, monkeypatch):
    monkeypatch.delenv("TRADIER_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TRADIER_ACCOUNT_ID", raising=False)
    monkeypatch.delenv(LIVE_ENV_FLAG, raising=False)
    monkeypatch.delenv(LIVE_CONFIRM_ENV, raising=False)
    rc = main(["status", "--config", "config/ema9_trend_tradier_sandbox.example.yaml"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "broker:          tradier" in out
    assert "data_source:     yahoo" in out
    assert "sandbox.tradier.com" in out
    assert "tradier token:   missing" in out
    assert "tradier account: missing" in out
    assert "I_UNDERSTAND" not in out
    assert "paper-api.alpaca" not in out


def test_cli_validate_tradier_example(capsys):
    rc = main(["validate", "--config", "config/ema9_trend_tradier_sandbox.example.yaml"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "broker=tradier" in out
    assert "data_source=yahoo" in out
    assert "tradier_endpoint=sandbox" in out
    assert "exit=range_expansion" in out
    assert "stop_mode=entry_pct" in out
