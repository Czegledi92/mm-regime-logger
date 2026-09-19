"""Deterministic Lucas / hard gates — evaluated BEFORE judgment battery."""

from __future__ import annotations

from dataclasses import dataclass

from regime_logger.config import RegimeLoggerConfig
from regime_logger.models import MarketObservation
from regime_logger.signals import evaluate_balance, evaluate_sig_pull
from regime_logger.veto import check_quote_walk_veto


@dataclass
class HardGateResult:
    """Outcome of deterministic hard gates (code-owned, never delegated to model)."""

    thin_range_blocked: bool = False
    quote_walk_veto: bool = False
    event_window: bool = False
    macro_clear: bool = False
    sig_pull: bool = False
    hard_veto_active: bool = False
    short_circuit_reason: str | None = None
    has_print_evidence: bool = False


def evaluate_hard_gates(obs: MarketObservation, config: RegimeLoggerConfig) -> HardGateResult:
    """
    Evaluate Lucas C1–C4 hard gates and shared VETOs in code.

    When hard_veto_active is True, the judgment battery must short-circuit and
    must NOT be trusted for regime promotion.
    """
    t = config.thresholds
    balance = evaluate_balance(obs, t.balance)
    qw = check_quote_walk_veto(obs, t.quote_walk)
    pull = evaluate_sig_pull(obs, t.sig_pull)
    has_prints = obs.print_volume > 0 or obs.print_count > 0

    result = HardGateResult(
        thin_range_blocked=balance.thin_range_blocked
        or obs.range_width_bps < t.balance.range_min_bps,
        quote_walk_veto=qw.vetoed,
        event_window=obs.event_window,
        macro_clear=obs.macro_clear,
        sig_pull=pull.fired,
        has_print_evidence=has_prints,
    )

    # C1: thin range blocks break / promotion
    if result.thin_range_blocked:
        result.hard_veto_active = True
        result.short_circuit_reason = "C1_THIN_RANGE"
        return result

    # Quote-walk without prints — hard VETO for break / aggression
    if result.quote_walk_veto and not has_prints:
        result.hard_veto_active = True
        result.short_circuit_reason = "QUOTE_WALK_VETO"
        return result

    # C3: event_window without macro clear — default defensive posture
    if result.event_window and not result.macro_clear:
        result.hard_veto_active = True
        result.short_circuit_reason = "C3_EVENT_WINDOW"
        return result

    return result
