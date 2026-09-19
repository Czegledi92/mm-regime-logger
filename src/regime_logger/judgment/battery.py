"""JudgmentBattery orchestrator — hard gates first, then client evaluation."""

from __future__ import annotations

from regime_logger.config import JudgmentBatteryConfig, RegimeLoggerConfig
from regime_logger.fsm import RegimeState
from regime_logger.judgment.client import JudgmentClient, StubJudgmentClient
from regime_logger.judgment.gates import evaluate_hard_gates
from regime_logger.judgment.market_state import build_market_state
from regime_logger.judgment.models import (
    BatteryResult,
    ChoiceAnswer,
    NoulAnswer,
    RegimeChoice,
    ScoreAnswer,
)
from regime_logger.models import MarketObservation


def create_judgment_client(client_name: str) -> JudgmentClient:
    """Factory — swap stub for future TypeSafe client behind same interface."""
    if client_name in ("stub", "StubJudgmentClient"):
        return StubJudgmentClient()
    raise ValueError(
        f"Unknown judgment client '{client_name}'. "
        "Only 'stub' is available (no live Jev / no AgenKit)."
    )


class JudgmentBattery:
    """
    Parallel judgment battery overlay for JOB-20260917-MM-001.

    Hard Lucas gates run in code BEFORE any client evaluation. When
    hard_veto_active, the battery short-circuits with reduced confidence
    and must not be used to promote regime transitions.
    """

    def __init__(
        self,
        config: JudgmentBatteryConfig,
        logger_config: RegimeLoggerConfig,
        client: JudgmentClient | None = None,
    ) -> None:
        self.config = config
        self.logger_config = logger_config
        self.client = client or create_judgment_client(config.client)

    def evaluate(
        self,
        obs: MarketObservation,
        fsm_state: RegimeState,
    ) -> BatteryResult:
        """Evaluate hard gates, build MarketState, then run judgment client."""
        if not self.config.enabled:
            return _disabled_result(obs.ts)

        gate_result = evaluate_hard_gates(obs, self.logger_config)
        state = build_market_state(
            obs,
            fsm_state,
            gate_result,
            venue_proxy=self.logger_config.venue.proxy,
        )

        result = self.client.evaluate(state, self.config)

        # Enforce hard-gate short-circuit on output regardless of client
        if gate_result.hard_veto_active:
            result = _apply_hard_gate_short_circuit(result, gate_result)

        return result

    def evaluate_batch(
        self,
        observations: list[MarketObservation],
        fsm_states: list[RegimeState],
    ) -> list[BatteryResult]:
        if len(observations) != len(fsm_states):
            raise ValueError("observations and fsm_states must have equal length")
        return [
            self.evaluate(obs, state)
            for obs, state in zip(observations, fsm_states, strict=True)
        ]


def _apply_hard_gate_short_circuit(result: BatteryResult, gate_result) -> BatteryResult:
    """Force short-circuit flags when hard gates fired (belt-and-suspenders)."""
    sc_conf = result.regime.confidence if result.regime.short_circuited else 0.5

    regime_value = result.regime.value
    if gate_result.short_circuit_reason == "C3_EVENT_WINDOW":
        regime_value = RegimeChoice.FLAT_WATCH
    elif regime_value == RegimeChoice.TREND_HANDOFF:
        regime_value = RegimeChoice.BALANCE

    # SIG-PULL alone must never show TREND_HANDOFF
    if gate_result.sig_pull and result.regime.value == RegimeChoice.TREND_HANDOFF:
        regime_value = RegimeChoice.BALANCE

    return BatteryResult(
        ts=result.ts,
        regime=ChoiceAnswer(
            question=result.regime.question,
            value=regime_value,
            confidence=sc_conf,
            short_circuited=True,
        ),
        toxic_flow=NoulAnswer(
            question=result.toxic_flow.question,
            value=result.toxic_flow.value,
            confidence=result.toxic_flow.confidence,
            short_circuited=True,
        ),
        liquidity_stressed=NoulAnswer(
            question=result.liquidity_stressed.question,
            value=result.liquidity_stressed.value,
            confidence=result.liquidity_stressed.confidence,
            short_circuited=True,
        ),
        quote_walk_veto_risk=NoulAnswer(
            question=result.quote_walk_veto_risk.question,
            value=result.quote_walk_veto_risk.value,
            confidence=result.quote_walk_veto_risk.confidence,
            short_circuited=True,
        ),
        quote_environment=ScoreAnswer(
            question=result.quote_environment.question,
            value=result.quote_environment.value,
            confidence=result.quote_environment.confidence,
            short_circuited=True,
        ),
        inventory_pressure=ScoreAnswer(
            question=result.inventory_pressure.question,
            value=result.inventory_pressure.value,
            confidence=result.inventory_pressure.confidence,
            short_circuited=True,
        ),
        hard_gate_short_circuit=True,
        short_circuit_reason=gate_result.short_circuit_reason,
        sig_pull=gate_result.sig_pull,
        client_name=result.client_name,
        extra=result.extra,
    )


def _disabled_result(ts: float) -> BatteryResult:
    return BatteryResult(
        ts=ts,
        regime=ChoiceAnswer("regime", RegimeChoice.BALANCE, 0.0, short_circuited=True),
        toxic_flow=NoulAnswer("toxic_flow", 0.0, 0.0, short_circuited=True),
        liquidity_stressed=NoulAnswer("liquidity_stressed", 0.0, 0.0, short_circuited=True),
        quote_walk_veto_risk=NoulAnswer("quote_walk_veto_risk", 0.0, 0.0, short_circuited=True),
        quote_environment=ScoreAnswer("quote_environment", 50.0, 0.0, short_circuited=True),
        inventory_pressure=ScoreAnswer("inventory_pressure", 50.0, 0.0, short_circuited=True),
        hard_gate_short_circuit=True,
        short_circuit_reason="BATTERY_DISABLED",
        client_name="none",
    )
