"""Opening-range (ORB) edge-fade / reversal helpers.

Locked v1 rules
---------------
- Opening range = first ``orb_timeframe`` candle at/after US RTH open
  (default 9:30 America/New_York). Default 15m → 9:30–9:45 ET high/low.
- After that candle is fully formed, evaluate ``signal_timeframe`` bars
  (default 5m).
- Probe (default ``probe_mode: touch_and_band``): the signal bar must
  **touch** the relevant OR extreme **and** **close** inside the edge
  band (``edge_pct`` of OR height, default 5%). Top (potential short):
  ``high >= or_high`` and close in ``[or_high - band, or_high]``.
  Bottom (potential long): ``low <= or_low`` and close in
  ``[or_low, or_low + band]``. ``probe_mode: touch`` keeps the wick-only
  rule (close-in-band not required). ``probe_mode: edge_band`` restores
  the previous close-in-zone rule without requiring a touch.
- Reversal = the **next** signal bar, opposite color:
  top probe + bearish close → short; bottom probe + bullish close → long.
  Default ``reversal_in_range: close`` also requires
  ``or_low <= close <= or_high``. ``body`` is the stricter fully-inside
  mode (high and low within the OR). ``off`` skips the in-range filter.
  A reversal that fails the filter is not an entry; that bar may itself
  be a later probe.
- Entry fills at the **open of the bar after the reversal**.
- Stop (default ``orb_extreme``): long → opening-range low; short → opening-range
  high. ``reversal_candle`` keeps the older stop at the reversal extreme.
- Take profit (default ``one_r``): R is the absolute distance from entry
  to stop (long stop = OR low, short stop = OR high under ``orb_extreme``).
  Long TP = entry + R; short TP = entry − R. ``or_midpoint`` restores the
  previous OR-midpoint target. ``first_profitable_close`` exits at the
  close of the first signal-timeframe bar that is profitable vs entry
  (long: ``close > entry``; short: ``close < entry``). If stop and take
  (1R, midpoint, or first-profit) both trade on the same bar, the stop
  fills first.
- High-vol gate (default ``min_or_height_pct`` 0.01 = 1%): trade only when
  ``(or_high - or_low) / or_open >= min_or_height_pct``. Denominator is the
  OR candle's open; if that print is missing, fall back to the OR midpoint.
  Below the threshold, skip the symbol for that session (no entries).
  Set ``0`` / ``null`` to disable.
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
ProbeMode = Literal["touch_and_band", "touch", "edge_band"]
ReversalInRange = Literal["close", "body", "off"]
TakeProfitMode = Literal["one_r", "or_midpoint", "first_profitable_close"]


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
    open_price: Optional[float] = None

    @property
    def height(self) -> float:
        return self.high - self.low

    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2.0

    @property
    def reference_price(self) -> Optional[float]:
        """Height-% denominator: OR open, else midpoint if open is missing."""
        if self.open_price is not None and self.open_price > 0:
            return self.open_price
        mid = self.midpoint
        return mid if mid > 0 else None

    def height_pct(self) -> Optional[float]:
        ref = self.reference_price
        if ref is None:
            return None
        return self.height / ref

    def meets_min_height(self, min_or_height_pct: Optional[float]) -> bool:
        """True when the OR is tall enough, or the gate is off (None/<=0)."""
        if min_or_height_pct is None or min_or_height_pct <= 0:
            return True
        pct = self.height_pct()
        if pct is None:
            return False
        return pct >= min_or_height_pct

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

    def classify_touch(self, bar: Bar) -> Optional[Zone]:
        """Return the OR edge this bar's wick touched, or None if neither / both."""
        if self.height <= 0:
            return None
        touches_top = bar.high >= self.high
        touches_bottom = bar.low <= self.low
        if touches_top and touches_bottom:
            return None
        if touches_top:
            return "top"
        if touches_bottom:
            return "bottom"
        return None

    def classify_touch_and_band(self, bar: Bar, edge_pct: float) -> Optional[Zone]:
        """Touch the OR extreme AND close inside that same edge band."""
        touch = self.classify_touch(bar)
        close = self.classify_close(bar.close, edge_pct)
        if touch is None or close is None or touch != close:
            return None
        return touch

    def classify_probe(
        self,
        bar: Bar,
        *,
        probe_mode: ProbeMode = "touch_and_band",
        edge_pct: float = 0.05,
    ) -> Optional[Zone]:
        """Classify a signal bar as a top/bottom probe under the configured mode."""
        mode = probe_mode or "touch_and_band"
        if mode == "touch_and_band":
            return self.classify_touch_and_band(bar, edge_pct)
        if mode == "touch":
            return self.classify_touch(bar)
        if mode == "edge_band":
            return self.classify_close(bar.close, edge_pct)
        raise ValueError(f"unknown probe_mode: {probe_mode!r}")


def reversal_in_opening_range(
    bar: Bar,
    opening_range: OpeningRange,
    mode: ReversalInRange = "close",
) -> bool:
    """Whether the reversal candle satisfies ``reversal_in_range``.

    - ``close`` (default): ``or_low <= close <= or_high``
    - ``body``: high and low both inside the OR (stricter fully-inside mode)
    - ``off``: no in-range filter
    """
    mode = mode or "close"
    if mode == "off":
        return True
    if opening_range.height <= 0:
        return False
    if mode == "close":
        return opening_range.low <= bar.close <= opening_range.high
    if mode == "body":
        return opening_range.low <= bar.low and bar.high <= opening_range.high
    raise ValueError(f"unknown reversal_in_range: {mode!r}")


def first_profitable_close(
    *,
    side: Side,
    entry_price: float,
    close: float,
) -> bool:
    """True when a signal-bar close is strictly profitable vs entry."""
    if side == "buy":
        return close > entry_price
    return close < entry_price


def one_r_take(
    *,
    side: Side,
    entry_price: float,
    stop: float,
) -> Optional[float]:
    """1R target from entry: long entry+R, short entry−R, R = |entry − stop|."""
    risk = abs(entry_price - stop)
    if risk <= 0:
        return None
    if side == "buy":
        return entry_price + risk
    return entry_price - risk


@dataclass(frozen=True)
class OrbSetup:
    symbol: str
    opening_range: OpeningRange
    zone: Zone
    side: Side
    probe: Bar
    reversal: Bar
    stop: float
    take: Optional[float] = None
    entry_bar: Optional[Bar] = None
    stop_mode: StopMode = "orb_extreme"
    probe_mode: ProbeMode = "touch_and_band"
    reversal_in_range: ReversalInRange = "close"
    take_profit_mode: TakeProfitMode = "one_r"

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
        if self.take_profit_mode == "first_profitable_close":
            take_txt = "take=first profitable signal-bar close"
        elif self.take_profit_mode == "one_r":
            if self.take is not None:
                take_txt = f"take={self.take:.4f} (1R)"
            else:
                take_txt = "take=1R (entry ± |entry−stop|)"
        elif self.take is not None:
            take_txt = f"take={self.take:.4f} (OR midpoint)"
        else:
            take_txt = "take=(none)"
        return (
            f"ORB {self.zone}-zone probe + "
            f"{'bearish' if self.side == 'sell' else 'bullish'} reversal → {direction}; "
            f"OR {self.opening_range.low:.4f}–{self.opening_range.high:.4f} "
            f"mid={self.opening_range.midpoint:.4f}; "
            f"probe H={self.probe.high:.4f} L={self.probe.low:.4f} "
            f"C={self.probe.close:.4f}; reversal {self.reversal.summary()}; "
            f"{entry}; stop={self.stop:.4f} ({stop_why}) "
            f"{take_txt}"
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
        open_price=or_bar.open,
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
    first = min(window, key=lambda b: _aware(b.timestamp))
    return OpeningRange(
        session_date=session_date,
        start=open_dt,
        end=end_dt,
        high=max(b.high for b in window),
        low=min(b.low for b in window),
        source="aggregated",
        open_price=first.open,
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
    probe: Bar,
    reversal: Bar,
    entry_bar: Optional[Bar],
    stop_mode: StopMode = "orb_extreme",
    probe_mode: ProbeMode = "touch_and_band",
    edge_pct: float = 0.05,
    reversal_in_range: ReversalInRange = "close",
    take_profit_mode: TakeProfitMode = "one_r",
) -> Optional[OrbSetup]:
    zone = opening_range.classify_probe(probe, probe_mode=probe_mode, edge_pct=edge_pct)
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
    if not reversal_in_opening_range(reversal, opening_range, reversal_in_range):
        return None
    stop = stop_price(
        zone=zone,
        opening_range=opening_range,
        reversal=reversal,
        stop_mode=stop_mode,
    )
    take: Optional[float]
    if take_profit_mode == "or_midpoint":
        take = opening_range.midpoint
    elif take_profit_mode == "one_r" and entry_bar is not None:
        take = one_r_take(side=side, entry_price=entry_bar.open, stop=stop)
    else:
        take = None
    return OrbSetup(
        symbol=symbol,
        opening_range=opening_range,
        zone=zone,
        side=side,
        probe=probe,
        reversal=reversal,
        stop=stop,
        take=take,
        entry_bar=entry_bar,
        stop_mode=stop_mode,
        probe_mode=probe_mode,
        reversal_in_range=reversal_in_range,
        take_profit_mode=take_profit_mode,
    )


def find_setups(
    symbol: str,
    signal_bars: list[Bar],
    opening_range: OpeningRange,
    *,
    edge_pct: float = 0.05,
    probe_mode: ProbeMode = "touch_and_band",
    session_timezone: str = "America/New_York",
    session_close: Optional[str] = "16:00",
    stop_mode: StopMode = "orb_extreme",
    reversal_in_range: ReversalInRange = "close",
    take_profit_mode: TakeProfitMode = "one_r",
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
        zone = opening_range.classify_probe(probe, probe_mode=probe_mode, edge_pct=edge_pct)
        if zone is None:
            i += 1
            continue
        reversal = series[i + 1]
        entry = series[i + 2] if i + 2 < len(series) else None
        setup = _setup_from_pair(
            symbol=symbol,
            opening_range=opening_range,
            probe=probe,
            reversal=reversal,
            entry_bar=entry,
            stop_mode=stop_mode,
            probe_mode=probe_mode,
            edge_pct=edge_pct,
            reversal_in_range=reversal_in_range,
            take_profit_mode=take_profit_mode,
        )
        if setup is None:
            # Same-color / doji / reversal outside OR — no trade. That bar may itself be a probe.
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
    probe_mode: ProbeMode = "touch_and_band",
    stop_mode: StopMode = "orb_extreme",
    reversal_in_range: ReversalInRange = "close",
    take_profit_mode: TakeProfitMode = "one_r",
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
        probe_mode=probe_mode,
        session_timezone=session_timezone,
        session_close=session_close,
        stop_mode=stop_mode,
        reversal_in_range=reversal_in_range,
        take_profit_mode=take_profit_mode,
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
    probe_mode: ProbeMode = "touch_and_band",
    stop_mode: StopMode = "orb_extreme",
    reversal_in_range: ReversalInRange = "close",
    take_profit_mode: TakeProfitMode = "one_r",
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
            probe_mode=probe_mode,
            stop_mode=stop_mode,
            reversal_in_range=reversal_in_range,
            take_profit_mode=take_profit_mode,
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
    probe_mode: ProbeMode = "touch_and_band",
    reversal_in_range: ReversalInRange = "close",
    min_or_height_pct: Optional[float] = 0.01,
) -> str:
    if opening_range is None:
        return "opening range not formed (need first orb_timeframe bar at/after session open)"
    if opening_range.height <= 0:
        return f"opening range has zero height ({opening_range.low:.4f})"
    if not opening_range.meets_min_height(min_or_height_pct):
        pct = opening_range.height_pct()
        ref = opening_range.reference_price
        denom = "OR open" if opening_range.open_price and opening_range.open_price > 0 else "OR midpoint"
        pct_txt = f"{pct:.2%}" if pct is not None else "n/a"
        ref_txt = f"{ref:.4f}" if ref is not None else "n/a"
        need = f"{min_or_height_pct:.2%}" if min_or_height_pct is not None else "n/a"
        return (
            f"opening-range height {pct_txt} of {denom} {ref_txt} is below "
            f"min_or_height_pct {need}; no entries this session"
        )
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
    last = series[-1]
    zone = opening_range.classify_probe(last, probe_mode=probe_mode, edge_pct=edge_pct)

    def _missed(bar: Bar) -> str:
        if probe_mode == "touch":
            return (
                f"bar H={bar.high:.4f} L={bar.low:.4f} did not touch OR high "
                f"{opening_range.high:.4f} or low {opening_range.low:.4f}"
            )
        top = opening_range.top_zone(edge_pct)
        bot = opening_range.bottom_zone(edge_pct)
        if probe_mode == "touch_and_band":
            return (
                f"bar H={bar.high:.4f} L={bar.low:.4f} C={bar.close:.4f} did not both "
                f"touch OR high {opening_range.high:.4f} / low {opening_range.low:.4f} "
                f"and close inside the {edge_pct:.0%} edge band "
                f"[{top[0]:.4f}–{top[1]:.4f}] / [{bot[0]:.4f}–{bot[1]:.4f}]"
            )
        return (
            f"close {bar.close:.4f} outside edge zones "
            f"[{top[0]:.4f}–{top[1]:.4f}] / [{bot[0]:.4f}–{bot[1]:.4f}]"
        )

    def _probe_waiting(bar: Bar, z: Zone) -> str:
        if probe_mode == "touch":
            return (
                f"probe touched OR {z} (H={bar.high:.4f} L={bar.low:.4f}); "
                "waiting for opposite-color reversal"
            )
        if probe_mode == "touch_and_band":
            return (
                f"probe touched OR {z} and closed in the edge band "
                f"(H={bar.high:.4f} L={bar.low:.4f} C={bar.close:.4f}); "
                "waiting for opposite-color reversal"
            )
        return f"probe in {z} zone (C={bar.close:.4f}); waiting for opposite-color reversal"

    if len(series) == 1:
        if zone:
            return _probe_waiting(last, zone)
        return _missed(last)
    prev = series[-2]
    prev_zone = opening_range.classify_probe(prev, probe_mode=probe_mode, edge_pct=edge_pct)
    if prev_zone:
        color = "bullish" if last.is_bullish() else ("bearish" if last.is_bearish() else "doji")
        needed = "bearish" if prev_zone == "top" else "bullish"
        opposite = (prev_zone == "top" and last.is_bearish()) or (
            prev_zone == "bottom" and last.is_bullish()
        )
        if opposite and not reversal_in_opening_range(last, opening_range, reversal_in_range):
            return (
                f"opposite-color reversal closed outside the OR "
                f"({opening_range.low:.4f}–{opening_range.high:.4f}); "
                f"C={last.close:.4f} H={last.high:.4f} L={last.low:.4f} "
                f"(reversal_in_range={reversal_in_range})"
            )
        if zone is None:
            return (
                f"probe in {prev_zone} zone but next bar is {color} "
                f"(need {needed} reversal for a fade)"
            )
    if zone:
        return _probe_waiting(last, zone)
    return _missed(last)


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
    min_or_height_pct: Optional[float] = 0.01,
) -> list[tuple[OrbSetup, Optional[str]]]:
    """Tag each setup with a skip reason, or None if the entry window allows it.

    Default product rule: at most ``max_trades_before_cutoff`` entries per symbol
    per session whose entry time is strictly before ``entry_cutoff`` (10:30 ET),
    and no entries at/after that cutoff. Counts reset each session date.
    Sessions whose OR height/open is below ``min_or_height_pct`` are skipped
    entirely (no entries that day for that symbol).
    """
    before_count: dict[date, int] = {}
    out: list[tuple[OrbSetup, Optional[str]]] = []
    for setup in setups:
        if not setup.opening_range.meets_min_height(min_or_height_pct):
            out.append((setup, "min_or_height"))
            continue
        if not entry_cutoff:
            out.append((setup, None))
            continue
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
