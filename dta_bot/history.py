"""Download historical OHLCV into the same Bar objects the live engine uses."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from dta_bot.broker import resolve_api_keys
from dta_bot.market_data import DATA_URL, bars_from_rows
from dta_bot.models import Bar
from dta_bot.timeframes import duration, normalize

log = logging.getLogger("dta_bot.history")

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Yahoo retention caps (requesting more returns HTTP 422).
_YAHOO_INTERVAL = {
    "1Min": ("1m", "7d"),
    "5Min": ("5m", "60d"),
    "15Min": ("15m", "60d"),
    "30Min": ("30m", "60d"),
    "1Hour": ("60m", "2y"),
    "4Hour": ("60m", "2y"),
    "1Day": ("1d", "max"),
    "1Week": ("1wk", "max"),
}


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def bars_to_rows(bars: list[Bar]) -> list[dict]:
    rows = []
    for b in bars:
        rows.append(
            {
                "t": _aware(b.timestamp).isoformat().replace("+00:00", "Z"),
                "o": b.open,
                "h": b.high,
                "l": b.low,
                "c": b.close,
                "v": b.volume,
            }
        )
    return rows


def save_fixture(path: str | Path, data: dict[str, dict[str, list[Bar]]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, dict[str, list[dict]]] = {}
    for symbol, tfs in data.items():
        payload[symbol] = {tf: bars_to_rows(series) for tf, series in tfs.items()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_fixture(path: str | Path) -> dict[str, dict[str, list[Bar]]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[str, dict[str, list[Bar]]] = {}
    for symbol, tfs in raw.items():
        out[symbol.upper()] = {}
        for tf, rows in tfs.items():
            out[symbol.upper()][normalize(tf)] = bars_from_rows(rows)
    return out


def parse_yahoo_chart(payload: dict) -> list[Bar]:
    """Turn a Yahoo v8 chart JSON object into oldest-first Bar rows."""
    chart = payload.get("chart") or {}
    error = chart.get("error")
    if error:
        raise RuntimeError(f"Yahoo chart error: {error}")
    results = chart.get("result") or []
    if not results:
        return []
    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = (result.get("indicators") or {}).get("quote") or [{}]
    quote = indicators[0] if indicators else {}
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    bars: list[Bar] = []
    n = len(timestamps)
    for i in range(n):
        o, h, l, c = (
            opens[i] if i < len(opens) else None,
            highs[i] if i < len(highs) else None,
            lows[i] if i < len(lows) else None,
            closes[i] if i < len(closes) else None,
        )
        if o is None or h is None or l is None or c is None:
            continue
        vol = float(volumes[i] or 0) if i < len(volumes) else 0.0
        bars.append(
            Bar(
                timestamp=datetime.fromtimestamp(int(timestamps[i]), tz=timezone.utc),
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=vol,
            )
        )
    bars.sort(key=lambda b: b.timestamp)
    return bars


def fetch_yahoo_bars(
    symbol: str,
    timeframe: str,
    *,
    client: Optional[httpx.Client] = None,
    range_hint: Optional[str] = None,
) -> list[Bar]:
    tf = normalize(timeframe)
    if tf not in _YAHOO_INTERVAL:
        raise ValueError(f"No Yahoo mapping for timeframe {timeframe!r}")
    interval, default_range = _YAHOO_INTERVAL[tf]
    # 4h is not a Yahoo interval; caller should request 1h instead.
    if tf == "4Hour":
        log.warning("Yahoo has no 4h bars; fetching 60m for %s", symbol)
    url = YAHOO_CHART.format(symbol=symbol.upper())
    params = {
        "interval": interval,
        "range": range_hint or default_range,
        "includePrePost": "false",
        "events": "div,split",
    }
    own = client is None
    client = client or httpx.Client(timeout=30.0, headers={"User-Agent": YAHOO_UA})
    try:
        resp = client.get(url, params=params, follow_redirects=True)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Yahoo {symbol} {tf} -> {resp.status_code}: {resp.text[:300]}"
            )
        bars = parse_yahoo_chart(resp.json())
    finally:
        if own:
            client.close()
    log.info("Yahoo %s %s: %s bars", symbol, tf, len(bars))
    return bars


def fetch_alpaca_bars(
    symbol: str,
    timeframe: str,
    *,
    api_key: str,
    api_secret: str,
    feed: str = "iex",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    client: Optional[httpx.Client] = None,
) -> list[Bar]:
    """Page through Alpaca v2 historical bars (used when keys are present)."""
    tf = normalize(timeframe)
    own = client is None
    client = client or httpx.Client(
        base_url=DATA_URL.rstrip("/"),
        headers={
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
            "Accept": "application/json",
        },
        timeout=30.0,
    )
    params: dict[str, str] = {
        "timeframe": tf,
        "limit": "10000",
        "adjustment": "raw",
        "feed": feed,
    }
    if start:
        params["start"] = _aware(start).isoformat().replace("+00:00", "Z")
    if end:
        params["end"] = _aware(end).isoformat().replace("+00:00", "Z")
    rows: list[dict] = []
    try:
        page_token: Optional[str] = None
        while True:
            if page_token:
                params["page_token"] = page_token
            resp = client.get(f"/v2/stocks/{symbol}/bars", params=params)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Alpaca data {symbol} {tf} -> {resp.status_code}: {resp.text[:300]}"
                )
            payload = resp.json()
            rows.extend(payload.get("bars") or [])
            page_token = payload.get("next_page_token")
            if not page_token:
                break
    finally:
        if own:
            client.close()
    bars = bars_from_rows(rows)
    log.info("Alpaca %s %s: %s bars", symbol, tf, len(bars))
    return bars


def fetch_bars(
    symbol: str,
    timeframe: str,
    *,
    source: str = "auto",
    feed: str = "iex",
) -> tuple[list[Bar], str]:
    """Return (bars, source_label). auto = Alpaca when keys exist, else Yahoo."""
    source = (source or "auto").lower()
    key, secret = resolve_api_keys()
    if source == "auto":
        source = "alpaca" if key and secret else "yahoo"
    if source == "alpaca":
        if not key or not secret:
            raise RuntimeError("Alpaca source requested but ALPACA_API_KEY/SECRET are unset")
        return fetch_alpaca_bars(symbol, timeframe, api_key=key, api_secret=secret, feed=feed), "alpaca"
    if source == "yahoo":
        return fetch_yahoo_bars(symbol, timeframe), "yahoo"
    raise ValueError(f"Unknown history source {source!r}")


def download_pairs(
    pairs: set[tuple[str, str]],
    *,
    source: str = "auto",
    feed: str = "iex",
    cache_dir: Optional[str | Path] = None,
) -> tuple[dict[tuple[str, str], list[Bar]], dict[str, str]]:
    """Download every (symbol, timeframe) pair. Returns bars map + per-pair source."""
    bars: dict[tuple[str, str], list[Bar]] = {}
    sources: dict[str, str] = {}
    cache_root = Path(cache_dir) if cache_dir else None
    if cache_root:
        cache_root.mkdir(parents=True, exist_ok=True)
    for symbol, tf in sorted(pairs):
        tf_n = normalize(tf)
        cache_path = cache_root / f"{symbol}_{tf_n}.json" if cache_root else None
        if cache_path and cache_path.exists() and cache_path.stat().st_size > 2:
            loaded = load_fixture(cache_path)
            series = loaded.get(symbol, {}).get(tf_n) or []
            if series:
                bars[(symbol, tf_n)] = series
                sources[f"{symbol}:{tf_n}"] = f"cache:{cache_path}"
                log.info("Cache hit %s %s (%s bars)", symbol, tf_n, len(series))
                continue
        series, label = fetch_bars(symbol, tf_n, source=source, feed=feed)
        bars[(symbol, tf_n)] = series
        sources[f"{symbol}:{tf_n}"] = label
        if cache_path:
            save_fixture(cache_path, {symbol: {tf_n: series}})
    return bars, sources


def series_span(bars: list[Bar]) -> tuple[Optional[datetime], Optional[datetime]]:
    if not bars:
        return None, None
    return bars[0].timestamp, bars[-1].timestamp


def drop_still_forming(
    bars: list[Bar],
    timeframe: str,
    now: Optional[datetime] = None,
) -> list[Bar]:
    now = _aware(now or datetime.now(timezone.utc))
    tf = normalize(timeframe)
    out: list[Bar] = []
    dur = duration(tf)
    for b in bars:
        ts = _aware(b.timestamp)
        if ts + dur <= now:
            out.append(b)
    return out
