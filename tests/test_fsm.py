"""Unit tests for regime FSM transitions."""

from __future__ import annotations

import pytest

from regime_logger.config import (
    BalanceThresholds,
    BreakThresholds,
    ConfirmThresholds,
    RegimeLoggerConfig,
    ThresholdsConfig,
    VenueConfig,
)
from regime_logger.fsm import RegimeFSM, RegimeState
from regime_logger.models import MarketObservation


def _base_config(**overrides) -> RegimeLoggerConfig:
    cfg = RegimeLoggerConfig(
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
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


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
    signed_vol: float = 0.0,
    reload_side: str | None = None,
    cvd_align: bool | None = None,
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
        signed_volume_beyond_level=signed_vol,
        reload_side=reload_side,
        cvd_align=cvd_align,
        depth_drop_pct=depth_drop_pct,
        event_window=event_window,
        macro_clear=macro_clear,
        prev_mid=prev_mid,
    )


class TestBalanceDefinition:
    def test_stays_balance_inside_range_and_vwap(self):
        fsm = RegimeFSM(_base_config())
        state = fsm.step(_obs(0, 100_000, print_volume=0.01, print_count=1))
        assert state == RegimeState.BALANCE
        assert not any(t.to_state == RegimeState.BREAK_CANDIDATE for t in fsm.transitions)

    def test_thin_range_blocks_break_candidate_c1(self):
        fsm = RegimeFSM(_base_config())
        # Tiny range: 100000 ± 2 => ~0.4 bps width < R_min=10
        obs = _obs(0, 100_000, session_low=99_998, session_high=100_002, band_lo=99_998, band_hi=100_002)
        obs2 = _obs(5, 100_050, session_low=99_998, session_high=100_002, band_lo=99_998, band_hi=100_002,
                     print_volume=0.5, print_count=5)
        fsm.step(obs)
        state = fsm.step(obs2)
        assert state == RegimeState.BALANCE


class TestBreakCandidate:
    def test_balance_to_break_candidate_on_range_exit_with_prints(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        # Mid must clear session_high + epsilon (~100600.6 at these levels)
        state = fsm.step(
            _obs(5, 100_620, print_volume=0.2, print_count=2, prev_mid=100_000)
        )
        assert state == RegimeState.BREAK_CANDIDATE
        tr = [t for t in fsm.transitions if t.to_state == RegimeState.BREAK_CANDIDATE][0]
        assert tr.which in ("range", "both")
        assert tr.from_state == RegimeState.BALANCE

    def test_quote_walk_does_not_enter_break_candidate(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        # Mid jumps with zero prints
        state = fsm.step(_obs(5, 100_600, print_volume=0, print_count=0, prev_mid=100_000))
        assert state == RegimeState.BALANCE
        veto_logs = [t for t in fsm.transitions if t.quote_walk_veto]
        assert len(veto_logs) >= 1

    def test_break_candidate_to_confirm_window_after_t0(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_620, print_volume=0.2, print_count=2, prev_mid=100_000))
        # t0=5s: at ts=10 sticky time met → CONFIRM_WINDOW
        state = fsm.step(_obs(10, 100_630, print_volume=0.2, print_count=2, prev_mid=100_620))
        assert state == RegimeState.CONFIRM_WINDOW


class TestConfirmWindow:
    def test_first_print_alone_does_not_trend_handoff(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_600, print_volume=0.2, print_count=2, prev_mid=100_000))
        fsm.step(_obs(15, 100_610, print_volume=0.2, print_count=2, prev_mid=100_600))
        # Only 10s hold — less than t_hold=30 (single leg uses 60)
        state = fsm.step(_obs(25, 100_620, print_volume=0.5, print_count=5, reload_side="ask",
                              signed_vol=0.5, prev_mid=100_610))
        assert state == RegimeState.CONFIRM_WINDOW

    def test_confirm_pass_to_trend_handoff(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_600, print_volume=0.2, print_count=2, prev_mid=100_000))
        fsm.step(_obs(15, 100_610, print_volume=0.2, print_count=2, prev_mid=100_600))
        # Advance through confirm window with sufficient hold + prints + reload
        for i, ts in enumerate(range(20, 80, 5), start=1):
            state = fsm.step(
                _obs(
                    ts,
                    100_620 + i,
                    print_volume=0.3,
                    print_count=3,
                    signed_vol=0.3,
                    reload_side="ask",
                    prev_mid=100_620 + i - 1,
                )
            )
        assert state == RegimeState.TREND_HANDOFF
        pass_tr = [t for t in fsm.transitions if t.confirm_result == "PASS"]
        assert len(pass_tr) == 1

    def test_fast_reclaim_fails_confirm(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_620, print_volume=0.2, print_count=2, prev_mid=100_000))
        fsm.step(_obs(15, 100_630, print_volume=0.2, print_count=2, prev_mid=100_620))
        fsm.step(_obs(20, 100_640, print_volume=0.2, print_count=2, prev_mid=100_630))
        state = fsm.step(_obs(25, 100_000, print_volume=0.1, print_count=1, prev_mid=100_640))
        assert state == RegimeState.BALANCE
        fail_tr = [t for t in fsm.transitions if t.confirm_result == "FAIL"]
        assert any(t.reason == "FAST_RECLAIM" for t in fail_tr)


class TestSigPull:
    def test_sig_pull_logged_but_no_trend_alone(self):
        cfg = _base_config()
        fsm = RegimeFSM(cfg)
        # Only SIG-PULL events — stay in balance, never TREND_HANDOFF
        for ts in range(0, 30, 5):
            fsm.step(
                _obs(
                    ts,
                    100_000,
                    depth_drop_pct=0.5,
                    print_volume=0.0,
                    print_count=0,
                    prev_mid=100_000 if ts == 0 else 100_000,
                )
            )
        assert fsm.state == RegimeState.BALANCE
        assert fsm._sig_pull_fires >= 1
        assert not any(t.to_state == RegimeState.TREND_HANDOFF for t in fsm.transitions)

    def test_sig_pull_during_confirm_does_not_auto_promote(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_600, print_volume=0.2, print_count=2, prev_mid=100_000))
        fsm.step(_obs(15, 100_610, print_volume=0.2, print_count=2, prev_mid=100_600))
        # Pull fires but insufficient confirm
        state = fsm.step(
            _obs(20, 100_615, depth_drop_pct=0.5, print_volume=0.01, print_count=1,
                 event_window=True, macro_clear=False, prev_mid=100_610)
        )
        assert state in (RegimeState.CONFIRM_WINDOW, RegimeState.FLAT_WATCH, RegimeState.BALANCE)
        if state == RegimeState.FLAT_WATCH:
            tr = [t for t in fsm.transitions if t.to_state == RegimeState.FLAT_WATCH]
            assert any(t.reason == "EVENT_PULL_WEAK_SINGLE_LEG" for t in tr)


class TestTrendHandoff:
    def test_trend_handoff_returns_to_balance_on_reclaim(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_600, print_volume=0.2, print_count=2, prev_mid=100_000))
        fsm.step(_obs(15, 100_610, print_volume=0.2, print_count=2, prev_mid=100_600))
        for i, ts in enumerate(range(20, 80, 5), start=1):
            fsm.step(
                _obs(ts, 100_620 + i, print_volume=0.3, print_count=3, signed_vol=0.3,
                     reload_side="ask", prev_mid=100_620 + i - 1)
            )
        assert fsm.state == RegimeState.TREND_HANDOFF
        state = fsm.step(_obs(85, 100_000, print_volume=0.1, print_count=1, prev_mid=100_650))
        assert state == RegimeState.BALANCE


class TestEventWindow:
    def test_event_window_defaults_flat_watch_without_macro_clear(self):
        cfg = _base_config()
        fsm = RegimeFSM(cfg)
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_620, print_volume=0.2, print_count=2, prev_mid=100_000))
        fsm.step(_obs(15, 100_630, print_volume=0.2, print_count=2, prev_mid=100_620, event_window=True))
        fsm.step(_obs(20, 100_640, print_volume=0.2, print_count=2, prev_mid=100_630, event_window=True))
        for i, ts in enumerate(range(20, 80, 5), start=1):
            fsm.step(
                _obs(
                    ts,
                    100_620 + i,
                    print_volume=0.3,
                    print_count=3,
                    signed_vol=0.3,
                    reload_side="ask",
                    event_window=True,
                    macro_clear=False,
                    prev_mid=100_620 + i - 1,
                )
            )
        flat_tr = [t for t in fsm.transitions if t.to_state == RegimeState.FLAT_WATCH]
        assert len(flat_tr) >= 1


class TestVenueProxy:
    def test_bn_proxy_tagged_on_transitions(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_620, print_volume=0.2, print_count=2, prev_mid=100_000))
        tr = [t for t in fsm.transitions if t.to_state == RegimeState.BREAK_CANDIDATE][0]
        assert tr.venue == "BN_AGG"
        assert tr.proxy is True


class TestSummary:
    def test_summary_counts(self):
        fsm = RegimeFSM(_base_config())
        fsm.step(_obs(0, 100_000))
        fsm.step(_obs(5, 100_600, print_volume=0.2, print_count=2, prev_mid=100_000))
        summary = fsm.summary_counts()
        assert summary["job_id"] == "JOB-20260917-MM-001"
        assert "transition_counts" in summary
