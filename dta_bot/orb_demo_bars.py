"""Synthetic ORB fixture: top fade, bottom fade, and a no-trade tape."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dta_bot.models import Bar


# Friday 2026-09-11. US Eastern is EDT (UTC-4), so 09:30 ET = 13:30 UTC.
SESSION = datetime(2026, 9, 11, 13, 30, tzinfo=timezone.utc)


def _row(bar: Bar) -> dict:
    return {
        "t": bar.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "o": round(bar.open, 4),
        "h": round(bar.high, 4),
        "l": round(bar.low, 4),
        "c": round(bar.close, 4),
        "v": int(bar.volume),
    }


def _bar(minutes: int, o: float, h: float, l: float, c: float, v: float = 1_000_000) -> Bar:
    return Bar(SESSION + timedelta(minutes=minutes), o, h, l, c, v)


def _ema_warmup(price: float, n: int = 9, start_minutes: int = -45) -> list[Bar]:
    """Premarket/early 5m closes so EMA(9) exists before the first post-OR probe.

    These prints sit before OR completion, so they never become probes.
    """
    return [
        _bar(start_minutes + 5 * i, price, price + 0.10, price - 0.10, price)
        for i in range(n)
    ]


def aapl_top_fade_short() -> dict[str, list[Bar]]:
    """15m OR 96–104 (mid 100). Touch of OR high + close in 5% band → bearish reversal → short."""
    # 09:15 ET dummy so the OR picker must skip it.
    premkt = _bar(-15, 99.0, 99.4, 98.8, 99.1)
    orb = _bar(0, 100.0, 104.0, 96.0, 101.0, 4_000_000)
    # Warmup closes ~103.80 keep EMA9 above the 102.60 reversal close (short filter).
    # 09:45 mid-range, 09:50 top touch, 09:55 bearish reversal (close inside OR),
    # 10:00 entry. Entry-bar close 102.45 is already profitable vs 102.55.
    signal = [
        *_ema_warmup(103.80),
        _bar(15, 101.0, 101.4, 100.6, 100.8),
        _bar(20, 103.20, 104.00, 103.10, 103.80),
        _bar(25, 103.70, 103.90, 102.50, 102.60),
        _bar(30, 102.55, 102.70, 102.40, 102.45),
        _bar(35, 102.40, 102.50, 99.80, 100.10),
        # 10:10: close back above EMA9 so the default ema_cross short can take.
        _bar(40, 100.20, 103.20, 100.10, 103.00),
    ]
    return {"15Min": [premkt, orb], "5Min": signal}


def msft_bottom_fade_long() -> dict[str, list[Bar]]:
    """15m OR 200–210 (mid 205). Touch of OR low + close in 5% band → bullish reversal → long."""
    orb = _bar(0, 204.0, 210.0, 200.0, 205.0, 3_500_000)
    # Warmup closes ~200.20 keep EMA9 below the 201.40 reversal close (long filter).
    signal = [
        *_ema_warmup(200.20),
        _bar(15, 205.0, 205.4, 204.6, 205.1),
        _bar(20, 200.80, 200.90, 200.00, 200.30),
        _bar(25, 200.40, 201.50, 200.20, 201.40),
        _bar(30, 201.50, 201.80, 201.30, 201.60),
        _bar(35, 201.60, 205.20, 201.40, 204.80),
        # 10:10: close back below EMA9 so the default ema_cross long can take.
        _bar(40, 204.50, 204.70, 201.00, 201.20),
    ]
    return {"15Min": [orb], "5Min": signal}


def spy_no_trade() -> dict[str, list[Bar]]:
    """Closes stay mid-range, then a top-edge touch with a same-color follow-through."""
    orb = _bar(0, 494.0, 500.0, 490.0, 496.0, 8_000_000)
    signal = [
        *_ema_warmup(496.00),
        _bar(15, 496.0, 496.8, 495.5, 496.2),
        _bar(20, 496.2, 498.4, 496.0, 498.0),  # no touch of 500 / 490
        _bar(25, 498.0, 498.6, 497.2, 497.4),
        _bar(30, 499.60, 500.00, 499.40, 499.80),  # touches OR high and closes in band
        _bar(35, 499.70, 500.10, 499.50, 499.95),  # still bullish — not a reversal
    ]
    return {"15Min": [orb], "5Min": signal}


def build_fixture() -> dict:
    aapl = aapl_top_fade_short()
    msft = msft_bottom_fade_long()
    spy = spy_no_trade()
    return {
        "AAPL": {tf: [_row(b) for b in bars] for tf, bars in aapl.items()},
        "MSFT": {tf: [_row(b) for b in bars] for tf, bars in msft.items()},
        "SPY": {tf: [_row(b) for b in bars] for tf, bars in spy.items()},
    }


def write_fixture(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture(), indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    dest = Path("config/orb_sample_bars.json")
    write_fixture(dest)
    print(f"Wrote {dest}")
