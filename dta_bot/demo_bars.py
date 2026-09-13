"""Build a synthetic OHLCV fixture that exercises the example rules."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dta_bot.models import Bar


def _rows(bars: list[Bar]) -> list[dict]:
    return [
        {
            "t": b.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "o": round(b.open, 4),
            "h": round(b.high, 4),
            "l": round(b.low, 4),
            "c": round(b.close, 4),
            "v": int(b.volume),
        }
        for b in bars
    ]


def _uptrend(start: datetime, n: int, price: float, step: float, minutes: int) -> list[Bar]:
    bars: list[Bar] = []
    px = price
    for i in range(n):
        o = px
        c = px + step
        h = max(o, c) + abs(step) * 0.3
        l = min(o, c) - abs(step) * 0.2
        bars.append(
            Bar(
                timestamp=start + timedelta(minutes=minutes * i),
                open=o,
                high=h,
                low=l,
                close=c,
                volume=1_000_000 + i * 1000,
            )
        )
        px = c
    return bars


def _choppy(start: datetime, n: int, price: float, minutes: int) -> list[Bar]:
    """Alternating up/down so RSI stays mid-range while price drifts higher."""
    bars: list[Bar] = []
    px = price
    for i in range(n):
        step = 0.35 if i % 2 == 0 else -0.18
        o = px
        c = px + step
        h = max(o, c) + 0.08
        l = min(o, c) - 0.08
        bars.append(
            Bar(
                timestamp=start + timedelta(minutes=minutes * i),
                open=o,
                high=h,
                low=l,
                close=c,
                volume=1_000_000 + i * 1000,
            )
        )
        px = c
    return bars


def aapl_15m_engulfing() -> list[Bar]:
    """Choppy drift so close > SMA20 and RSI < 70, then a dip + bullish engulfing."""
    start = datetime(2026, 9, 11, 13, 30, tzinfo=timezone.utc)
    bars = _choppy(start, 24, 180.0, 15)
    last_ts = bars[-1].timestamp
    last_close = bars[-1].close
    # Small bearish pullback
    pull = Bar(
        timestamp=last_ts + timedelta(minutes=15),
        open=last_close + 0.05,
        high=last_close + 0.15,
        low=last_close - 0.85,
        close=last_close - 0.70,
        volume=1_800_000,
    )
    # Bullish engulfing of the pullback (body covers prior body)
    engulf = Bar(
        timestamp=last_ts + timedelta(minutes=30),
        open=pull.close - 0.05,
        high=pull.open + 1.20,
        low=pull.close - 0.15,
        close=pull.open + 1.00,
        volume=2_400_000,
    )
    return bars + [pull, engulf]


def msft_15m_no_pattern() -> list[Bar]:
    start = datetime(2026, 9, 11, 13, 30, tzinfo=timezone.utc)
    return _uptrend(start, 30, 420.0, 0.10, 15)


def spy_15m_bearish_engulfing() -> list[Bar]:
    start = datetime(2026, 9, 11, 13, 30, tzinfo=timezone.utc)
    bars = _uptrend(start, 26, 560.0, 0.12, 15)
    last_ts = bars[-1].timestamp
    bull = Bar(
        timestamp=last_ts + timedelta(minutes=15),
        open=563.10,
        high=563.80,
        low=563.00,
        close=563.60,
        volume=3_000_000,
    )
    bear = Bar(
        timestamp=last_ts + timedelta(minutes=30),
        open=563.70,
        high=563.90,
        low=562.20,
        close=562.40,
        volume=4_200_000,
    )
    return bars + [bull, bear]


def spy_1h_hammer_oversold() -> list[Bar]:
    """Decline so RSI is low, ending with a hammer."""
    start = datetime(2026, 9, 10, 13, 30, tzinfo=timezone.utc)
    bars = _uptrend(start, 16, 570.0, -0.55, 60)
    last_ts = bars[-1].timestamp
    # Hammer: small body near the high, long lower wick
    hammer = Bar(
        timestamp=last_ts + timedelta(hours=1),
        open=561.20,
        high=561.40,
        low=558.40,
        close=561.10,
        volume=8_000_000,
    )
    return bars + [hammer]


def build_fixture() -> dict:
    return {
        "AAPL": {"15Min": _rows(aapl_15m_engulfing())},
        "MSFT": {"15Min": _rows(msft_15m_no_pattern())},
        "SPY": {
            "15Min": _rows(spy_15m_bearish_engulfing()),
            "1Hour": _rows(spy_1h_hammer_oversold()),
        },
    }


def write_fixture(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture(), indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    dest = Path("config/sample_bars.json")
    write_fixture(dest)
    print(f"Wrote {dest}")
