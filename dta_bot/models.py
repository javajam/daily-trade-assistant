"""Shared data types for bars, positions, orders, and evaluation results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional


Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]
ActionType = Literal["buy", "sell", "close"]
SizeType = Literal["shares", "percent_equity"]


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def body(self) -> float:
        return abs(self.close - self.open)

    def range(self) -> float:
        return self.high - self.low

    def upper_shadow(self) -> float:
        return self.high - max(self.open, self.close)

    def lower_shadow(self) -> float:
        return min(self.open, self.close) - self.low

    def is_bullish(self) -> bool:
        return self.close > self.open

    def is_bearish(self) -> bool:
        return self.close < self.open

    def body_top(self) -> float:
        return max(self.open, self.close)

    def body_bottom(self) -> float:
        return min(self.open, self.close)

    def mid_body(self) -> float:
        return (self.open + self.close) / 2.0

    def summary(self) -> str:
        ts = self.timestamp.isoformat()
        return (
            f"{ts} O={self.open:.4f} H={self.high:.4f} "
            f"L={self.low:.4f} C={self.close:.4f} V={self.volume:.0f}"
        )


@dataclass(frozen=True)
class Account:
    equity: float
    cash: float
    buying_power: float
    status: str
    account_number: str = ""
    pattern_day_trader: bool = False


@dataclass(frozen=True)
class Position:
    symbol: str
    qty: float
    side: str
    avg_entry_price: float
    market_value: float
    unrealized_pl: float = 0.0


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: Side
    qty: float
    order_type: OrderType = "market"
    time_in_force: str = "day"
    limit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    client_order_id: Optional[str] = None


@dataclass(frozen=True)
class OrderResult:
    id: str
    symbol: str
    side: str
    qty: float
    status: str
    submitted: bool
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionResult:
    matched: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    rule_id: str
    symbol: str
    matched: bool
    reasons: list[str]
    action_type: Optional[ActionType] = None
    signal_bar_ts: Optional[datetime] = None
    skipped: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def explain(self) -> str:
        why = " | ".join(self.reasons) if self.reasons else "(no detail)"
        if self.skipped:
            return f"[SKIP] {self.symbol} / {self.rule_id} — {self.skipped} | {why}"
        if self.matched:
            return f"[FIRE] {self.symbol} / {self.rule_id} — {why}"
        return f"[NO]   {self.symbol} / {self.rule_id} — {why}"
