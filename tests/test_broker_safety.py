import pytest

from dta_bot.broker import (
    LIVE_CONFIRM_ENV,
    LIVE_CONFIRM_VALUE,
    LIVE_ENV_FLAG,
    LIVE_TRADING_URL,
    PAPER_TRADING_URL,
    AlpacaBroker,
    DryRunBroker,
    resolve_trading_url,
)
from dta_bot.models import OrderRequest


def test_default_is_paper(monkeypatch):
    monkeypatch.delenv(LIVE_ENV_FLAG, raising=False)
    monkeypatch.delenv(LIVE_CONFIRM_ENV, raising=False)
    url, mode = resolve_trading_url(allow_live=False)
    assert mode == "paper"
    assert url == PAPER_TRADING_URL


def test_incomplete_live_gates_stay_paper(monkeypatch):
    monkeypatch.setenv(LIVE_ENV_FLAG, "true")
    monkeypatch.delenv(LIVE_CONFIRM_ENV, raising=False)
    url, mode = resolve_trading_url(allow_live=True)
    assert mode == "paper"
    assert url == PAPER_TRADING_URL


def test_all_gates_required_for_live(monkeypatch):
    monkeypatch.setenv(LIVE_ENV_FLAG, "true")
    monkeypatch.setenv(LIVE_CONFIRM_ENV, LIVE_CONFIRM_VALUE)
    url, mode = resolve_trading_url(allow_live=True)
    assert mode == "live"
    assert url == LIVE_TRADING_URL


def test_paper_client_refuses_live_url():
    with pytest.raises(RuntimeError, match="Paper mode refuses"):
        AlpacaBroker(
            api_key="k",
            api_secret="s",
            base_url=LIVE_TRADING_URL,
            mode="paper",
        )


def test_live_client_refuses_paper_url():
    with pytest.raises(RuntimeError, match="paper endpoint"):
        AlpacaBroker(
            api_key="k",
            api_secret="s",
            base_url=PAPER_TRADING_URL,
            mode="live",
        )


def test_dry_run_never_marks_submitted():
    broker = DryRunBroker(equity=50_000)
    result = broker.submit_order(
        OrderRequest(symbol="AAPL", side="buy", qty=1, order_type="market")
    )
    assert result.submitted is False
    assert result.status == "dry_run"
    assert len(broker.submitted) == 1
