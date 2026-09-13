"""Opening-range (ORB) edge-fade / reversal helpers.

Locked v1 rules
---------------
- Opening range = first ``orb_timeframe`` candle at/after US RTH open
  (default 9:30 America/New_York). Default 15m → 9:30–9:45 ET high/low.
- After that candle is fully formed, evaluate ``signal_timeframe`` bars
  (default 5m).
- Edge band = ``edge_pct * (or_high - or_low)`` (default 5%).
  Top zone: ``[or_high - band, or_high]``. Bottom: ``[or_low, or_low + band]``.
- Probe = signal bar whose **close** is inside a zone.
- Reversal = the **next** signal bar, opposite color:
  top probe + bearish close → short; bottom probe + bullish close → long.
- Entry fills at the **open of the bar after the reversal**.
- Stop (default ``orb_extreme``): long → opening-range low; short → opening-range
  high. ``reversal_candle`` keeps the older stop at the reversal extreme.
- Take profit (v1): OR midpoint ``(or_high + or_low) / 2``.
  Exit strategy will be A/B tested later.
- Frequency (default): at most one entry per symbol per session, and only if
  that entry is before 10:30 America/New_York. No new entries at/after 10:30.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Literal, Optional
from zoneinfo import ZoneInfo

from dta_bot.models import Bar
from dta_bot.timeframes import duration

Zone = Literal["top", "bottom"]
Side = Literal["buy", "sell"]
StopMode = Literal["orb_extreme", "reversal_candle"]


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_hhmm(value: str) -> time:
    raw = (value or "").strip()
    parts = raw.split(":")
    if len(parts) < 2:
        raise ValueError(f"Time must be HH:MM, got {value!r}")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Time out of range: {value!r}")
    return time(hour, minute)


def session_dt(session_date: date, hhmm: str, tz_name: str) -> datetime:
    zone = ZoneInfo(tz_name)
    return datetime.combine(session_date, parse_hhmm(hhmm), tzinfo=zone)


def bar_session_date(bar: Bar, tz_name: str) -> date:
    return _aware(bar.timestamp).astimezone(ZoneInfo(tz_name)).date()


def session_dates(bars: list[Bar], tz_name: str) -> list[date]:
    return sorted({bar_session_date(b, tz_name) for b in bars})


def bars_on_session(bars: list[Bar], session_date: date, tz_name: str) -> list[Bar]:
    return [b for b in bars if bar_session_date(b, tz_name) == session_date]


def bars_in_window(
    bars: list[Bar],
    start: datetime,
    end: datetime,
    *,
    include_end: bool = False,
) -> list[Bar]:
    start = _aware(start)
    end = _aware(end)
    out: list[Bar] = []
    for bar in bars:
        ts = _aware(bar.timestamp)
        if ts < start:
            continue
        if include_end:
            if ts > end:
                continue
        elif ts >= end:
            continue
        out.append(bar)
    return out


@dataclass(frozen=True)
class OpeningRange:
    session_date: date
    start: datetime
    end: datetime
    high: float
    low: float
    source: str = "orb_bar"

    @property
    def height(self) -> float:
        return self.high - self.low

    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2.0

    def band(self, edge_pct: float) -> float:
        return edge_pct * self.height

    def top_zone(self, edge_pct: float) -> tuple[float, float]:
        width = self.band(edge_pct)
        return (self.high - width, self.high)

    def bottom_zone(self, edge_pct: float) -> tuple[float, float]:
        width = self.band(edge_pct)
        return (self.low, self.low + width)

    def classify_close(self, close: float, edge_pct: float) -> Optional[Zone]:
        """Return the edge zone containing ``close``, or None if outside / ambiguous."""
        if self.height <= 0:
            return None
        top_lo, top_hi = self.top_zone(edge_pct)
        bot_lo, bot_hi = self.bottom_zone(edge_pct)
        in_top = top_lo <= close <= top_hi
        in_bottom = bot_lo <= close <= bot_hi
        if in_top and in_bottom:
            return None
        if in_top:
            return "top"
        if in_bottom:
            return "bottom"
        return None


@dataclass(frozen=True)
class OrbSetup:
    symbol: str
    opening_range: OpeningRange
    zone: Zone
    side: Side
    probe: Bar
    reversal: Bar
    stop: float
    take: float
    entry_bar: Optional[Bar] = None
    stop_mode: StopMode = "orb_extreme"

    @property
    def session_date(self) -> date:
        return self.opening_range.session_date

    def explain(self) -> str:
        direction = "short" if self.side == "sell" else "long"
        entry = (
            f"entry_open={self.entry_bar.open:.4f} @{self.entry_bar.timestamp.isoformat()}"
            if self.entry_bar is not None
            else "entry_open=(next signal bar)"
        )
        if self.stop_mode == "reversal_candle":
            stop_why = "reversal candle extreme"
        else:
            stop_why = "OR low" if self.side == "buy" else "OR high"
        return (
            f"ORB {self.zone}-zone probe + "
            f"{'bearish' if self.side == 'sell' else 'bullish'} reversal → {direction}; "
            f"OR {self.opening_range.low:.4f}–{self.opening_range.high:.4f} "
            f"mid={self.opening_range.midpoint:.4f}; "
            f"probe C={self.probe.close:.4f}; reversal {self.reversal.summary()}; "
            f"{entry}; stop={self.stop:.4f} ({stop_why}) "
            f"take={self.take:.4f} (OR midpoint, v1)"
        )


def build_opening_range(
    orb_bars: list[Bar],
    session_date: date,
    *,
    session_open: str = "09:30",
    session_timezone: str = "America/New_York",
    orb_timeframe: str = "15m",
) -> Optional[OpeningRange]:
    """First fully-formed orb_timeframe candle at or after the session open."""
    open_dt = session_dt(session_date, session_open, session_timezone)
    day = bars_on_session(orb_bars, session_date, session_timezone)
    candidates = [b for b in day if _aware(b.timestamp) >= open_dt]
    if not candidates:
        return None
    or_bar = min(candidates, key=lambda b: _aware(b.timestamp))
    start = _aware(or_bar.timestamp)
    end = start + duration(orb_timeframe)
    return OpeningRange(
        session_date=session_date,
        start=start,
        end=end,
        high=or_bar.high,
        low=or_bar.low,
        source="orb_bar",
    )


def aggregate_opening_range(
    signal_bars: list[Bar],
    session_date: date,
    *,
    session_open: str = "09:30",
    session_timezone: str = "America/New_York",
    orb_timeframe: str = "15m",
    signal_timeframe: str = "5m",
) -> Optional[OpeningRange]:
    """Build the OR from signal-timeframe bars covering [open, open + orb_tf)."""
    open_dt = session_dt(session_date, session_open, session_timezone)
    end_dt = open_dt + duration(orb_timeframe)
    day = bars_on_session(signal_bars, session_date, session_timezone)
    window = bars_in_window(day, open_dt, end_dt)
    if not window:
        return None
    last_slice = end_dt - duration(signal_timeframe)
    if not any(_aware(b.timestamp) >= last_slice for b in window):
        return None
    return OpeningRange(
        session_date=session_date,
        start=open_dt,
        end=end_dt,
        high=max(b.high for b in window),
        low=min(b.low for b in window),
        source="aggregated",
    )


def resolve_opening_range(
    *,
    orb_bars: list[Bar],
    signal_bars: list[Bar],
    session_date: date,
    session_open: str,
    session_timezone: str,
    orb_timeframe: str,
    signal_timeframe: str,
) -> Optional[OpeningRange]:
    rng = build_opening_range(
        orb_bars,
        session_date,
        session_open=session_open,
        session_timezone=session_timezone,
        orb_timeframe=orb_timeframe,
    )
    if rng is not None:
        return rng
    return aggregate_opening_range(
        signal_bars,
        session_date,
        session_open=session_open,
        session_timezone=session_timezone,
        orb_timeframe=orb_timeframe,
        signal_timeframe=signal_timeframe,
    )


def signal_bars_after_or(
    signal_bars: list[Bar],
    opening_range: OpeningRange,
    *,
    session_timezone: str,
    session_close: Optional[str] = "16:00",
) -> list[Bar]:
    """Closed signal bars at/after OR completion, same session, before RTH close."""
    start = opening_range.end
    if session_close:
        end = session_dt(opening_range.session_date, session_close, session_timezone)
        return bars_in_window(signal_bars, start, end)
    day = bars_on_session(signal_bars, opening_range.session_date, session_timezone)
    return [b for b in day if _aware(b.timestamp) >= start]


def stop_price(
    *,
    zone: Zone,
    opening_range: OpeningRange,
    reversal: Bar,
    stop_mode: StopMode = "orb_extreme",
) -> float:
    """Long → OR low (or reversal low); short → OR high (or reversal high)."""
    mode = stop_mode or "orb_extreme"
    if mode == "reversal_candle":
        return reversal.low if zone == "bottom" else reversal.high
    return opening_range.low if zone == "bottom" else opening_range.high


def _setup_from_pair(
    *,
    symbol: str,
    opening_range: OpeningRange,
    edge_pct: float,
    probe: Bar,
    reversal: Bar,
    entry_bar: Optional[Bar],
    stop_mode: StopMode = "orb_extreme",
) -> Optional[OrbSetup]:
    zone = opening_range.classify_close(probe.close, edge_pct)
    if zone is None:
        return None
    if zone == "top":
        if not reversal.is_bearish():
            return None
        side: Side = "sell"
    else:
        if not reversal.is_bullish():
            return None
        side = "buy"
    return OrbSetup(
        symbol=symbol,
        opening_range=opening_range,
        zone=zone,
        side=side,
        probe=probe,
        reversal=reversal,
        stop=stop_price(
            zone=zone,
            opening_range=opening_range,
            reversal=reversal,
            stop_mode=stop_mode,
        ),
        take=opening_range.midpoint,
        entry_bar=entry_bar,
        stop_mode=stop_mode,
    )


def find_setups(
    symbol: str,
    signal_bars: list[Bar],
    opening_range: OpeningRange,
    *,
    edge_pct: float = 0.05,
    session_timezone: str = "America/New_York",
    session_close: Optional[str] = "16:00",
    stop_mode: StopMode = "orb_extreme",
) -> list[OrbSetup]:
    """Walk probe → next-bar reversal on post-OR signal bars. Multiple setups allowed.

    Time/frequency gating is applied separately by ``gate_setups`` so this
    function stays a pure probe/reversal detector.
    """
    series = signal_bars_after_or(
        signal_bars,
        opening_range,
        session_timezone=session_timezone,
        session_close=session_close,
    )
    setups: list[OrbSetup] = []
    i = 0
    while i < len(series) - 1:
        probe = series[i]
        zone = opening_range.classify_close(probe.close, edge_pct)
        if zone is None:
            i += 1
            continue
        reversal = series[i + 1]
        entry = series[i + 2] if i + 2 < len(series) else None
        setup = _setup_from_pair(
            symbol=symbol,
            opening_range=opening_range,
            edge_pct=edge_pct,
            probe=probe,
            reversal=reversal,
            entry_bar=entry,
            stop_mode=stop_mode,
        )
        if setup is None:
            # Same-color (or doji) "reversal" — no trade. That bar may itself be a probe.
            i += 1
            continue
        setups.append(setup)
        i += 2
    return setups


def find_session_setups(
    symbol: str,
    *,
    orb_bars: list[Bar],
    signal_bars: list[Bar],
    session_date: date,
    session_open: str = "09:30",
    session_timezone: str = "America/New_York",
    session_close: Optional[str] = "16:00",
    orb_timeframe: str = "15m",
    signal_timeframe: str = "5m",
    edge_pct: float = 0.05,
    stop_mode: StopMode = "orb_extreme",
) -> tuple[Optional[OpeningRange], list[OrbSetup]]:
    rng = resolve_opening_range(
        orb_bars=orb_bars,
        signal_bars=signal_bars,
        session_date=session_date,
        session_open=session_open,
        session_timezone=session_timezone,
        orb_timeframe=orb_timeframe,
        signal_timeframe=signal_timeframe,
    )
    if rng is None or rng.height <= 0:
        return rng, []
    return rng, find_setups(
        symbol,
        signal_bars,
        rng,
        edge_pct=edge_pct,
        session_timezone=session_timezone,
        session_close=session_close,
        stop_mode=stop_mode,
    )


def find_all_setups(
    symbol: str,
    *,
    orb_bars: list[Bar],
    signal_bars: list[Bar],
    session_open: str = "09:30",
    session_timezone: str = "America/New_York",
    session_close: Optional[str] = "16:00",
    orb_timeframe: str = "15m",
    signal_timeframe: str = "5m",
    edge_pct: float = 0.05,
    stop_mode: StopMode = "orb_extreme",
) -> list[OrbSetup]:
    dates = session_dates(orb_bars or signal_bars, session_timezone)
    found: list[OrbSetup] = []
    for session_date in dates:
        _rng, setups = find_session_setups(
            symbol,
            orb_bars=orb_bars,
            signal_bars=signal_bars,
            session_date=session_date,
            session_open=session_open,
            session_timezone=session_timezone,
            session_close=session_close,
            orb_timeframe=orb_timeframe,
            signal_timeframe=signal_timeframe,
            edge_pct=edge_pct,
            stop_mode=stop_mode,
        )
        found.extend(setups)
    return found


def live_setup(
    setups: list[OrbSetup],
    signal_bars: list[Bar],
) -> Optional[OrbSetup]:
    """A live fire only when the latest closed signal bar *is* the reversal."""
    if not setups or not signal_bars:
        return None
    last = max(signal_bars, key=lambda b: _aware(b.timestamp))
    last_ts = _aware(last.timestamp)
    for setup in reversed(setups):
        if _aware(setup.reversal.timestamp) == last_ts:
            return setup
    return None


def no_setup_reason(
    *,
    opening_range: Optional[OpeningRange],
    signal_bars: list[Bar],
    edge_pct: float,
    session_timezone: str,
    session_close: Optional[str],
) -> str:
    if opening_range is None:
        return "opening range not formed (need first orb_timeframe bar at/after session open)"
    if opening_range.height <= 0:
        return f"opening range has zero height ({opening_range.low:.4f})"
    series = signal_bars_after_or(
        signal_bars,
        opening_range,
        session_timezone=session_timezone,
        session_close=session_close,
    )
    if not series:
        return (
            f"OR {opening_range.low:.4f}–{opening_range.high:.4f} ready; "
            "no closed signal bars after the OR candle yet"
        )
    top = opening_range.top_zone(edge_pct)
    bot = opening_range.bottom_zone(edge_pct)
    last = series[-1]
    zone = opening_range.classify_close(last.close, edge_pct)
    if len(series) == 1:
        if zone:
            return (
                f"probe in {zone} zone (C={last.close:.4f}); waiting for opposite-color reversal"
            )
        return (
            f"close {last.close:.4f} outside edge zones "
            f"[{top[0]:.4f}–{top[1]:.4f}] / [{bot[0]:.4f}–{bot[1]:.4f}]"
        )
    prev = series[-2]
    prev_zone = opening_range.classify_close(prev.close, edge_pct)
    if prev_zone and zone is None:
        color = "bullish" if last.is_bullish() else ("bearish" if last.is_bearish() else "doji")
        needed = "bearish" if prev_zone == "top" else "bullish"
        return (
            f"probe in {prev_zone} zone but next bar is {color} "
            f"(need {needed} reversal for a fade)"
        )
    if zone:
        return f"latest close {last.close:.4f} is a {zone} probe; waiting for opposite-color reversal"
    return (
        f"close {last.close:.4f} outside edge zones "
        f"[{top[0]:.4f}–{top[1]:.4f}] / [{bot[0]:.4f}–{bot[1]:.4f}]"
    )


def next_signal_bar(series: list[Bar], after: datetime) -> Optional[Bar]:
    after = _aware(after)
    later = [b for b in series if _aware(b.timestamp) > after]
    if not later:
        return None
    return min(later, key=lambda b: _aware(b.timestamp))


def setup_entry_time(setup: OrbSetup, signal_timeframe: str = "5m") -> datetime:
    """Fill time: next signal-bar open, or reversal close + one signal bar if unknown."""
    if setup.entry_bar is not None:
        return _aware(setup.entry_bar.timestamp)
    return _aware(setup.reversal.timestamp) + duration(signal_timeframe)


def gate_setups(
    setups: list[OrbSetup],
    *,
    entry_cutoff: Optional[str] = "10:30",
    max_trades_before_cutoff: int = 1,
    allow_entries_after_cutoff: bool = False,
    session_timezone: str = "America/New_York",
    signal_timeframe: str = "5m",
) -> list[tuple[OrbSetup, Optional[str]]]:
    """Tag each setup with a skip reason, or None if the entry window allows it.

    Default product rule: at most ``max_trades_before_cutoff`` entries per symbol
    per session whose entry time is strictly before ``entry_cutoff`` (10:30 ET),
    and no entries at/after that cutoff. Counts reset each session date.
    """
    if not entry_cutoff:
        return [(setup, None) for setup in setups]
    before_count: dict[date, int] = {}
    out: list[tuple[OrbSetup, Optional[str]]] = []
    for setup in setups:
        entry_ts = setup_entry_time(setup, signal_timeframe)
        cutoff_dt = session_dt(setup.session_date, entry_cutoff, session_timezone)
        if entry_ts >= cutoff_dt:
            if allow_entries_after_cutoff:
                out.append((setup, None))
            else:
                out.append((setup, "entry_cutoff"))
            continue
        used = before_count.get(setup.session_date, 0)
        if used >= max_trades_before_cutoff:
            out.append((setup, "max_trades_before_cutoff"))
            continue
        before_count[setup.session_date] = used + 1
        out.append((setup, None))
    return out
