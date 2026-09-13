"""OHLCV bars from Alpaca market data or a local fixture file."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol

import httpx

from dta_bot.broker import resolve_api_keys
from dta_bot.models import Bar
from dta_bot.timeframes import drop_incomplete, normalize

log = logging.getLogger("dta_bot.data")

DATA_URL = "https://data.alpaca.markets"


def _parse_ts(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def bars_from_rows(rows: list[dict]) -> list[Bar]:
    bars: list[Bar] = []
    for row in rows:
        ts = row.get("t") or row.get("timestamp")
        bars.append(
            Bar(
                timestamp=_parse_ts(ts) if isinstance(ts, str) else ts,
                open=float(row.get("o", row.get("open"))),
                high=float(row.get("h", row.get("high"))),
                low=float(row.get("l", row.get("low"))),
                close=float(row.get("c", row.get("close"))),
                volume=float(row.get("v", row.get("volume", 0))),
            )
        )
    bars.sort(key=lambda b: b.timestamp)
    return bars


class MarketData(Protocol):
    def get_bars(self, symbol: str, timeframe: str, limit: int = 80) -> list[Bar]: ...


class AlpacaMarketData:
    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        feed: str = "iex",
        base_url: str = DATA_URL,
        timeout: float = 15.0,
        client: Optional[httpx.Client] = None,
        now: Optional[datetime] = None,
    ) -> None:
        self.feed = feed
        self._now = now
        self._own = client is None
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": api_secret,
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        if self._own:
            self._client.close()

    def get_bars(self, symbol: str, timeframe: str, limit: int = 80) -> list[Bar]:
        tf = normalize(timeframe)
        resp = self._client.get(
            f"/v2/stocks/{symbol}/bars",
            params={
                "timeframe": tf,
                "limit": str(limit),
                "adjustment": "raw",
                "feed": self.feed,
            },
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Alpaca data {symbol} {tf} -> {resp.status_code}: {resp.text}")
        payload = resp.json()
        rows = payload.get("bars") or []
        bars = drop_incomplete(bars_from_rows(rows), tf, now=self._now)
        log.debug("Fetched %s %s bars for %s (%s closed)", len(bars), tf, symbol, tf)
        return bars


class FixtureMarketData:
    """Local JSON: { "AAPL": { "15Min": [ {t,o,h,l,c,v}, ... ] } }."""

    def __init__(self, path: str | Path, now: Optional[datetime] = None, drop_open: bool = False) -> None:
        self.path = Path(path)
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._data: dict[str, dict[str, list[Bar]]] = {}
        for symbol, tfs in raw.items():
            self._data[symbol.upper()] = {}
            for tf, rows in tfs.items():
                key = normalize(tf)
                self._data[symbol.upper()][key] = bars_from_rows(rows)
        self._now = now
        self._drop_open = drop_open

    def get_bars(self, symbol: str, timeframe: str, limit: int = 80) -> list[Bar]:
        tf = normalize(timeframe)
        series = self._data.get(symbol.upper(), {}).get(tf)
        if series is None:
            raise KeyError(f"Fixture {self.path} has no bars for {symbol} {tf}")
        bars = series[-limit:]
        if self._drop_open:
            bars = drop_incomplete(bars, tf, now=self._now)
        return list(bars)


def build_market_data(*, feed: str, fixture: Optional[str]) -> MarketData:
    if fixture:
        return FixtureMarketData(fixture)
    key, secret = resolve_api_keys()
    if not key or not secret:
        raise RuntimeError(
            "Market data needs ALPACA_API_KEY / ALPACA_API_SECRET, or pass --fixture."
        )
    return AlpacaMarketData(api_key=key, api_secret=secret, feed=feed)
