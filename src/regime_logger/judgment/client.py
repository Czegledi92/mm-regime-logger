"""Judgment client interface and deterministic stub implementation."""

from __future__ import annotations

from typing import Protocol

from regime_logger.config import JudgmentBatteryConfig
from regime_logger.judgment.market_state import MarketState
from regime_logger.judgment.models import (
    BatteryResult,
    ChoiceAnswer,
    NoulAnswer,
    RegimeChoice,
    ScoreAnswer,
)


class JudgmentClient(Protocol):
    """Interface for judgment providers (stub today; TypeSafe Jev later)."""

    @property
    def name(self) -> str: ...

    def evaluate(self, state: MarketState, config: JudgmentBatteryConfig) -> BatteryResult: ...


class StubJudgmentClient:
    """
    Deterministic stub battery — no external Jev / TypeSafe API.

    Returns Jev-like Choice / Noul / Score answers from MarketState heuristics.
    SIG-PULL alone never yields TREND_HANDOFF regime choice.
    """

    @property
    def name(self) -> str:
        return "stub"

    def evaluate(self, state: MarketState, config: JudgmentBatteryConfig) -> BatteryResult:
        t = config.thresholds
        hg = state.hard_gates

        toxic = _clamp01(
            _base_toxic(state)
            + (t.toxic_flow_event_window_boost if state.event_window else 0.0)
            + (t.toxic_flow_sig_pull_boost if hg.sig_pull else 0.0)
            + (t.toxic_flow_quote_walk_boost if hg.quote_walk_veto else 0.0)
        )

        liq_stressed = _clamp01(
            _depth_stress(state.depth_drop_pct, t.liquidity_stressed_depth_drop_min)
            + (t.liquidity_stressed_sig_pull_boost if hg.sig_pull else 0.0)
        )

        qw_risk = _clamp01(
            state.mid_move_bps / max(t.quote_walk_veto_risk_mid_move_bps, 1.0)
            if state.print_volume <= 0 and state.print_count <= 0
            else 0.0
        )

        quote_env = _clamp_score(
            t.quote_environment_base
            - toxic * t.quote_environment_toxic_penalty
            - liq_stressed * t.quote_environment_liquidity_penalty
        )

        inv_pressure = _clamp_score(_inventory_pressure_score(state))

        regime = _infer_regime_choice(state, config)

        conf_base = t.confidence_base
        return BatteryResult(
            ts=state.ts,
            regime=ChoiceAnswer(
                question="regime",
                value=regime,
                confidence=conf_base if not hg.hard_veto_active else t.confidence_short_circuit,
                short_circuited=hg.hard_veto_active,
            ),
            toxic_flow=NoulAnswer(
                question="toxic_flow",
                value=toxic,
                confidence=conf_base,
                short_circuited=hg.hard_veto_active,
            ),
            liquidity_stressed=NoulAnswer(
                question="liquidity_stressed",
                value=liq_stressed,
                confidence=conf_base,
                short_circuited=hg.hard_veto_active,
            ),
            quote_walk_veto_risk=NoulAnswer(
                question="quote_walk_veto_risk",
                value=qw_risk,
                confidence=conf_base,
                short_circuited=hg.hard_veto_active,
            ),
            quote_environment=ScoreAnswer(
                question="quote_environment",
                value=quote_env,
                confidence=conf_base,
                short_circuited=hg.hard_veto_active,
            ),
            inventory_pressure=ScoreAnswer(
                question="inventory_pressure",
                value=inv_pressure,
                confidence=conf_base,
                short_circuited=hg.hard_veto_active,
            ),
            hard_gate_short_circuit=hg.hard_veto_active,
            short_circuit_reason=hg.short_circuit_reason,
            sig_pull=hg.sig_pull,
            client_name=self.name,
        )


def _infer_regime_choice(state: MarketState, config: JudgmentBatteryConfig) -> RegimeChoice:
    """
    Map FSM-aligned regime choice from market snapshot.

    SIG-PULL alone must NOT yield TREND_HANDOFF — only sig_pull with no break
    evidence stays BALANCE (or FLAT_WATCH in event_window).
    """
    hg = state.hard_gates
    t = config.thresholds

    # Hard short-circuit paths — never promote on battery alone
    if hg.hard_veto_active:
        if hg.short_circuit_reason == "C3_EVENT_WINDOW":
            return RegimeChoice.FLAT_WATCH
        return RegimeChoice.BALANCE

    # SIG-PULL alone: never TREND_HANDOFF (locked)
    only_sig_pull = (
        hg.sig_pull
        and state.break_which == "none"
        and state.fsm_state in ("BALANCE", "FLAT_WATCH")
    )
    if only_sig_pull:
        return RegimeChoice.FLAT_WATCH if state.event_window else RegimeChoice.BALANCE

    # Mirror FSM state when available (authoritative path is still code FSM)
    fsm_map = {
        "BALANCE": RegimeChoice.BALANCE,
        "BREAK_CANDIDATE": RegimeChoice.BREAK_CANDIDATE,
        "CONFIRM_WINDOW": RegimeChoice.BREAK_CANDIDATE,
        "TREND_HANDOFF": RegimeChoice.TREND_HANDOFF,
        "FLAT_WATCH": RegimeChoice.FLAT_WATCH,
    }
    if state.fsm_state in fsm_map:
        choice = fsm_map[state.fsm_state]
        # Extra guard: never TREND from stub when only sig_pull fired this tick
        if choice == RegimeChoice.TREND_HANDOFF and hg.sig_pull and state.break_which == "none":
            return RegimeChoice.BALANCE
        return choice

    # Heuristic fallback from market geometry
    if state.in_balance:
        return RegimeChoice.BALANCE
    if state.break_which != "none" and state.print_volume >= t.regime_break_min_print_volume:
        return RegimeChoice.BREAK_CANDIDATE
    if state.event_window and not state.macro_clear:
        return RegimeChoice.FLAT_WATCH
    return RegimeChoice.BALANCE


def _base_toxic(state: MarketState) -> float:
    if state.outside_range and state.outside_vwap:
        return 0.35
    if state.outside_range or state.outside_vwap:
        return 0.2
    return 0.05


def _depth_stress(depth_drop_pct: float | None, threshold: float) -> float:
    if depth_drop_pct is None:
        return 0.0
    if depth_drop_pct < threshold:
        return depth_drop_pct / max(threshold, 1e-9) * 0.5
    return min(1.0, 0.5 + (depth_drop_pct - threshold) / max(1.0 - threshold, 1e-9) * 0.5)


def _inventory_pressure_score(state: MarketState) -> float:
    """Stub: distance from range midpoint as pseudo inventory pressure."""
    if state.session_high <= state.session_low:
        return 50.0
    mid_range = (state.session_high + state.session_low) / 2.0
    half_width = (state.session_high - state.session_low) / 2.0
    if half_width <= 0:
        return 50.0
    offset = abs(state.mid - mid_range) / half_width
    return offset * 100.0


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _clamp_score(x: float) -> float:
    return max(0.0, min(100.0, x))
