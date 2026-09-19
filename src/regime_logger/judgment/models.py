"""Typed judgment-battery answer shapes (Jev-like Choice / Noul / Score)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RegimeChoice(str, Enum):
    """Regime Choice aligned with FSM states (no conflicting labels)."""

    BALANCE = "BALANCE"
    BREAK_CANDIDATE = "BREAK_CANDIDATE"
    TREND_HANDOFF = "TREND_HANDOFF"
    FLAT_WATCH = "FLAT_WATCH"


@dataclass
class ChoiceAnswer:
    """Jev-style Choice answer."""

    question: str
    value: RegimeChoice
    confidence: float  # stub 0–1
    short_circuited: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "choice",
            "question": self.question,
            "value": self.value.value,
            "confidence": self.confidence,
            "short_circuited": self.short_circuited,
        }


@dataclass
class NoulAnswer:
    """Jev-style Noul (0–1 probability) answer."""

    question: str
    value: float
    confidence: float
    short_circuited: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "noul",
            "question": self.question,
            "value": self.value,
            "confidence": self.confidence,
            "short_circuited": self.short_circuited,
        }


@dataclass
class ScoreAnswer:
    """Jev-style Score (0–100) answer."""

    question: str
    value: float
    confidence: float
    short_circuited: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "score",
            "question": self.question,
            "value": self.value,
            "confidence": self.confidence,
            "short_circuited": self.short_circuited,
        }


@dataclass
class BatteryResult:
    """Full parallel judgment battery output for one MarketState snapshot."""

    ts: float
    regime: ChoiceAnswer
    toxic_flow: NoulAnswer
    liquidity_stressed: NoulAnswer
    quote_walk_veto_risk: NoulAnswer
    quote_environment: ScoreAnswer
    inventory_pressure: ScoreAnswer
    hard_gate_short_circuit: bool = False
    short_circuit_reason: str | None = None
    sig_pull: bool = False
    client_name: str = "stub"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "hard_gate_short_circuit": self.hard_gate_short_circuit,
            "short_circuit_reason": self.short_circuit_reason,
            "sig_pull": self.sig_pull,
            "client_name": self.client_name,
            "regime": self.regime.to_dict(),
            "toxic_flow": self.toxic_flow.to_dict(),
            "liquidity_stressed": self.liquidity_stressed.to_dict(),
            "quote_walk_veto_risk": self.quote_walk_veto_risk.to_dict(),
            "quote_environment": self.quote_environment.to_dict(),
            "inventory_pressure": self.inventory_pressure.to_dict(),
            **self.extra,
        }
