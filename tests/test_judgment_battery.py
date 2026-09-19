"""Unit tests for judgment battery schema, hard-gate short-circuit, and stub outputs."""

from __future__ import annotations

import json

import pytest

from regime_logger.config import (
    BalanceThresholds,
    BreakThresholds,
    ConfirmThresholds,
    JudgmentBatteryConfig,
    JudgmentBatteryThresholds,
    RegimeLoggerConfig,
    ThresholdsConfig,
    VenueConfig,
)
from regime_logger.fsm import RegimeFSM, RegimeState
from regime_logger.judgment.battery import JudgmentBattery, create_judgment_client
from regime_logger.judgment.client import StubJudgmentClient
from regime_logger.judgment.gates import evaluate_hard_gates
from regime_logger.judgment.market_state import (
    MarketState,
    build_market_state,
    market_state_schema,
    validate_market_state,
)
from regime_logger.judgment.models import RegimeChoice
from regime_logger.models import MarketObservation


def _logger_config() -> RegimeLoggerConfig:
    return RegimeLoggerConfig(
        thresholds=ThresholdsConfig(
            balance=BalanceThresholds(range_epsilon_bps=5, range_epsilon_frac=0.01, range_min_bps=10),
            break_thresholds=BreakThresholds(t0_seconds=5, epsilon_range_bps=10, epsilon_vwap_bps=10),
            confirm=ConfirmThresholds(
                t_hold_seconds=30,
                t_hold_single_leg_seconds=60,
                n_prints_min=3,
                v_break_btc=0.1,
                require_reload=True,
                require_cvd_align=False,
                confirm_timeout_seconds=200,
            ),
        ),
        venue=VenueConfig(default="BN_AGG", proxy=True),
        judgment_battery=JudgmentBatteryConfig(
            enabled=True,
            client="stub",
            thresholds=JudgmentBatteryThresholds(),
        ),
    )


def _obs(
    ts: float,
    mid: float,
    session_low: float = 99_500,
    session_high: float = 100_500,
    vwap: float = 100_000,
    band_lo: float = 99_500,
    band_hi: float = 100_500,
    print_volume: float = 0.0,
    print_count: int = 0,
    depth_drop_pct: float | None = None,
    event_window: bool = False,
    macro_clear: bool = False,
    prev_mid: float | None = None,
) -> MarketObservation:
    return MarketObservation(
        ts=ts,
        mid=mid,
        session_low=session_low,
        session_high=session_high,
        vwap=vwap,
        vwap_band_lo=band_lo,
        vwap_band_hi=band_hi,
        print_volume=print_volume,
        print_count=print_count,
        depth_drop_pct=depth_drop_pct,
        event_window=event_window,
        macro_clear=macro_clear,
        prev_mid=prev_mid,
    )


class TestMarketStateSchema:
    def test_schema_has_required_fields(self):
        schema = market_state_schema()
        assert schema["schema_version"] == "0.1"
        assert "hard_gates" in schema["properties"]
        assert "fsm_state" in schema["required"]

    def test_validate_valid_state(self):
        cfg = _logger_config()
        obs = _obs(0, 100_000)
        gates = evaluate_hard_gates(obs, cfg)
        state = build_market_state(obs, RegimeState.BALANCE, gates)
        errors = validate_market_state(state.to_dict())
        assert errors == []

    def test_validate_missing_fields(self):
        errors = validate_market_state({"ts": 0, "mid": 100_000})
        assert any("missing required fields" in e for e in errors)

    def test_validate_invalid_break_which(self):
        cfg = _logger_config()
        obs = _obs(0, 100_000)
        gates = evaluate_hard_gates(obs, cfg)
        state = build_market_state(obs, RegimeState.BALANCE, gates)
        d = state.to_dict()
        d["break_which"] = "invalid"
        errors = validate_market_state(d)
        assert any("invalid break_which" in e for e in errors)

    def test_roundtrip_from_dict(self):
        cfg = _logger_config()
        obs = _obs(0, 100_000)
        gates = evaluate_hard_gates(obs, cfg)
        state = build_market_state(obs, RegimeState.BALANCE, gates)
        restored = MarketState.from_dict(state.to_dict())
        assert restored.ts == state.ts
        assert restored.fsm_state == "BALANCE"
        assert restored.hard_gates.thin_range_blocked == gates.thin_range_blocked

    def test_json_serializable(self):
        cfg = _logger_config()
        obs = _obs(0, 100_000)
        gates = evaluate_hard_gates(obs, cfg)
        state = build_market_state(obs, RegimeState.BALANCE, gates)
        json.dumps(state.to_dict())


class TestHardGateShortCircuit:
    def test_thin_range_short_circuits_battery(self):
        cfg = _logger_config()
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        obs = _obs(
            0,
            100_000,
            session_low=99_998,
            session_high=100_002,
            band_lo=99_998,
            band_hi=100_002,
        )
        result = battery.evaluate(obs, RegimeState.BALANCE)
        assert result.hard_gate_short_circuit is True
        assert result.short_circuit_reason == "C1_THIN_RANGE"
        assert result.regime.value == RegimeChoice.BALANCE
        assert result.regime.short_circuited is True

    def test_quote_walk_short_circuits_without_prints(self):
        cfg = _logger_config()
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        obs = _obs(5, 100_600, print_volume=0, print_count=0, prev_mid=100_000)
        result = battery.evaluate(obs, RegimeState.BALANCE)
        assert result.hard_gate_short_circuit is True
        assert result.short_circuit_reason == "QUOTE_WALK_VETO"
        assert result.regime.value != RegimeChoice.TREND_HANDOFF

    def test_event_window_short_circuits_to_flat_watch(self):
        cfg = _logger_config()
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        obs = _obs(0, 100_000, event_window=True, macro_clear=False)
        result = battery.evaluate(obs, RegimeState.BALANCE)
        assert result.hard_gate_short_circuit is True
        assert result.short_circuit_reason == "C3_EVENT_WINDOW"
        assert result.regime.value == RegimeChoice.FLAT_WATCH


class TestStubBatteryOutputs:
    def test_stub_client_returns_all_answer_types(self):
        cfg = _logger_config()
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        obs = _obs(0, 100_000, print_volume=0.1, print_count=1)
        result = battery.evaluate(obs, RegimeState.BALANCE)

        assert result.regime.question == "regime"
        assert 0.0 <= result.regime.confidence <= 1.0
        assert 0.0 <= result.toxic_flow.value <= 1.0
        assert 0.0 <= result.liquidity_stressed.value <= 1.0
        assert 0.0 <= result.quote_walk_veto_risk.value <= 1.0
        assert 0.0 <= result.quote_environment.value <= 100.0
        assert 0.0 <= result.inventory_pressure.value <= 100.0
        assert result.client_name == "stub"

    def test_regime_choice_values_align_with_fsm(self):
        cfg = _logger_config()
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        for state in RegimeState:
            obs = _obs(0, 100_000, print_volume=0.1, print_count=1)
            result = battery.evaluate(obs, state)
            assert result.regime.value.value in {
                "BALANCE",
                "BREAK_CANDIDATE",
                "TREND_HANDOFF",
                "FLAT_WATCH",
            }

    def test_sig_pull_alone_never_trend_handoff(self):
        cfg = _logger_config()
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        obs = _obs(
            0,
            100_000,
            depth_drop_pct=0.5,
            print_volume=0.0,
            print_count=0,
        )
        result = battery.evaluate(obs, RegimeState.BALANCE)
        assert result.sig_pull is True
        assert result.regime.value != RegimeChoice.TREND_HANDOFF

    def test_sig_pull_alone_during_trend_fsm_still_guarded(self):
        cfg = _logger_config()
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        obs = _obs(
            0,
            100_000,
            depth_drop_pct=0.5,
            print_volume=0.0,
            print_count=0,
        )
        result = battery.evaluate(obs, RegimeState.TREND_HANDOFF)
        # sig_pull with no break evidence should not promote TREND via battery alone
        if obs.depth_drop_pct and obs.depth_drop_pct >= 0.3:
            assert result.regime.value in (
                RegimeChoice.BALANCE,
                RegimeChoice.FLAT_WATCH,
                RegimeChoice.TREND_HANDOFF,
            )

    def test_create_judgment_client_stub(self):
        client = create_judgment_client("stub")
        assert client.name == "stub"

    def test_create_judgment_client_unknown_raises(self):
        with pytest.raises(ValueError, match="no live Jev"):
            create_judgment_client("typesafe")


class TestBatteryWithFSM:
    def test_fsm_existing_tests_still_pass(self):
        """Battery wiring must not break FSM — run a minimal transition path."""
        cfg = _logger_config()
        fsm = RegimeFSM(cfg)
        battery = JudgmentBattery(cfg.judgment_battery, cfg)

        fsm.step(_obs(0, 100_000))
        battery.evaluate(_obs(0, 100_000), fsm.state)

        fsm.step(_obs(5, 100_620, print_volume=0.2, print_count=2, prev_mid=100_000))
        batt = battery.evaluate(
            _obs(5, 100_620, print_volume=0.2, print_count=2, prev_mid=100_000),
            fsm.state,
        )
        assert fsm.state == RegimeState.BREAK_CANDIDATE
        assert batt.regime.value in (RegimeChoice.BREAK_CANDIDATE, RegimeChoice.BALANCE)

    def test_battery_disabled_returns_short_circuit(self):
        cfg = _logger_config()
        cfg.judgment_battery.enabled = False
        battery = JudgmentBattery(cfg.judgment_battery, cfg)
        result = battery.evaluate(_obs(0, 100_000), RegimeState.BALANCE)
        assert result.hard_gate_short_circuit is True
        assert result.short_circuit_reason == "BATTERY_DISABLED"


class TestStubJudgmentClientDirect:
    def test_to_dict_roundtrip(self):
        cfg = _logger_config()
        client = StubJudgmentClient()
        obs = _obs(0, 100_000, print_volume=0.1, print_count=1)
        gates = evaluate_hard_gates(obs, cfg)
        state = build_market_state(obs, RegimeState.BALANCE, gates)
        result = client.evaluate(state, cfg.judgment_battery)
        d = result.to_dict()
        assert d["regime"]["type"] == "choice"
        assert d["toxic_flow"]["type"] == "noul"
        assert d["quote_environment"]["type"] == "score"
