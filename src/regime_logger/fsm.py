"""Regime state machine: BALANCE → BREAK_CANDIDATE → CONFIRM_WINDOW → TREND_HANDOFF."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from regime_logger.config import RegimeLoggerConfig
from regime_logger.models import MarketObservation
from regime_logger.signals import (
    BreakWhich,
    evaluate_balance,
    evaluate_break_exit,
    evaluate_confirm,
    evaluate_sig_pull,
    classify_break_which,
)
from regime_logger.veto import check_quote_walk_veto


class RegimeState(str, Enum):
    BALANCE = "BALANCE"
    BREAK_CANDIDATE = "BREAK_CANDIDATE"
    CONFIRM_WINDOW = "CONFIRM_WINDOW"
    TREND_HANDOFF = "TREND_HANDOFF"
    FLAT_WATCH = "FLAT_WATCH"


@dataclass
class TransitionEvent:
    ts: float
    from_state: RegimeState
    to_state: RegimeState
    reason: str
    which: str = "none"
    sig_pull: bool = False
    quote_walk_veto: bool = False
    confirm_result: str | None = None
    venue: str = "BN_AGG"
    proxy: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "reason": self.reason,
            "which": self.which,
            "sig_pull": self.sig_pull,
            "quote_walk_veto": self.quote_walk_veto,
            "confirm_result": self.confirm_result,
            "venue": self.venue,
            "proxy": self.proxy,
            **self.extra,
        }


@dataclass
class _BreakTracker:
    which: BreakWhich = BreakWhich.NONE
    outside_since_ts: float | None = None
    first_print_seen: bool = False


@dataclass
class _ConfirmTracker:
    window_start_ts: float | None = None
    hold_start_ts: float | None = None
    n_prints: int = 0
    signed_vol: float = 0.0
    which: BreakWhich = BreakWhich.NONE


class RegimeFSM:
    """
    Offline regime logger FSM per JOB-20260917-MM-001 architecture v0.1.

    SIG-PULL is logged as a separate boolean and never promotes TREND_HANDOFF alone.
    """

    def __init__(self, config: RegimeLoggerConfig) -> None:
        self.config = config
        self.state = RegimeState.BALANCE
        self.transitions: list[TransitionEvent] = []
        self._break = _BreakTracker()
        self._confirm = _ConfirmTracker()
        self._last_ts: float | None = None
        self._quote_walk_vetos: int = 0
        self._sig_pull_fires: int = 0

    def reset(self) -> None:
        self.state = RegimeState.BALANCE
        self.transitions.clear()
        self._break = _BreakTracker()
        self._confirm = _ConfirmTracker()
        self._last_ts = None
        self._quote_walk_vetos = 0
        self._sig_pull_fires = 0

    def step(self, obs: MarketObservation) -> RegimeState:
        """Process one observation and return the new state."""
        cfg = self.config
        t = cfg.thresholds

        # --- VETO: quote-walk ---
        qw = check_quote_walk_veto(obs, t.quote_walk)
        if qw.vetoed:
            self._quote_walk_vetos += 1
            self._log_veto(obs, qw.reason or "QUOTE_WALK")

        # --- SIG-PULL (orthogonal; never alone → TREND_HANDOFF) ---
        pull = evaluate_sig_pull(obs, t.sig_pull)
        if pull.fired:
            self._sig_pull_fires += 1

        balance = evaluate_balance(obs, t.balance)
        outside_range, outside_vwap = evaluate_break_exit(obs, t.break_thresholds, t.balance)
        which = classify_break_which(outside_range, outside_vwap)
        has_prints = obs.print_volume > 0 or obs.print_count > 0
        dt = self._delta_t(obs.ts)

        prev_state = self.state

        if self.state == RegimeState.BALANCE:
            self._step_balance(obs, balance, which, outside_range, outside_vwap, has_prints, qw, pull)

        elif self.state == RegimeState.BREAK_CANDIDATE:
            self._step_break_candidate(obs, balance, which, outside_range, outside_vwap, has_prints, qw, pull, dt)

        elif self.state == RegimeState.CONFIRM_WINDOW:
            self._step_confirm_window(obs, balance, which, outside_range, outside_vwap, has_prints, qw, pull, dt)

        elif self.state == RegimeState.TREND_HANDOFF:
            self._step_trend_handoff(obs, balance, pull)

        elif self.state == RegimeState.FLAT_WATCH:
            self._step_flat_watch(obs, balance)

        self._last_ts = obs.ts

        if self.state != prev_state:
            pass  # transitions recorded in sub-steps

        return self.state

    def run(self, observations: list[MarketObservation]) -> list[TransitionEvent]:
        """Process all observations chronologically."""
        for obs in observations:
            self.step(obs)
        return self.transitions

    def summary_counts(self) -> dict[str, Any]:
        """Aggregate transition counts for develop-split reporting."""
        counts: dict[str, int] = {}
        for tr in self.transitions:
            key = f"{tr.from_state.value}->{tr.to_state.value}"
            counts[key] = counts.get(key, 0) + 1

        return {
            "job_id": self.config.job_id,
            "final_state": self.state.value,
            "transition_counts": counts,
            "quote_walk_vetos": self._quote_walk_vetos,
            "sig_pull_fires": self._sig_pull_fires,
            "total_transitions": len(self.transitions),
        }

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _step_balance(
        self,
        obs: MarketObservation,
        balance,
        which: BreakWhich,
        outside_range: bool,
        outside_vwap: bool,
        has_prints: bool,
        qw,
        pull,
    ) -> None:
        t = self.config.thresholds

        if balance.thin_range_blocked:
            return  # C1: stay BALANCE (or could FLAT_WATCH — stay BALANCE per spec)

        if obs.event_window and not balance.in_balance:
            # Toxic event without balance — optional FLAT_WATCH
            pass

        if which == BreakWhich.NONE:
            return

        # Quote-walk alone must NOT enter BREAK_CANDIDATE
        if qw.vetoed and not has_prints:
            return

        # C1: hard gate range width before BREAK_CANDIDATE
        if balance.thin_range_blocked or obs.range_width_bps < t.balance.range_min_bps:
            return

        # Need sticky t0 outside boundary with print evidence
        if not has_prints:
            return

        self._break = _BreakTracker(which=which, outside_since_ts=obs.ts, first_print_seen=True)
        self._transition(
            obs,
            RegimeState.BALANCE,
            RegimeState.BREAK_CANDIDATE,
            reason="RANGE_OR_VWAP_EXIT",
            which=which.value,
            sig_pull=pull.fired,
            quote_walk_veto=qw.vetoed,
        )

    def _step_break_candidate(
        self,
        obs: MarketObservation,
        balance,
        which: BreakWhich,
        outside_range: bool,
        outside_vwap: bool,
        has_prints: bool,
        qw,
        pull,
        dt: float,
    ) -> None:
        t = self.config.thresholds

        # Reclaim inside both range AND vwap band → back to BALANCE
        if balance.in_balance:
            self._transition(
                obs,
                RegimeState.BREAK_CANDIDATE,
                RegimeState.BALANCE,
                reason="RECLAIM_INSIDE_BALANCE",
                which=self._break.which.value,
                sig_pull=pull.fired,
            )
            self._break = _BreakTracker()
            return

        # Quote-walk without prints — invalidate candidate
        if qw.vetoed and not has_prints:
            self._transition(
                obs,
                RegimeState.BREAK_CANDIDATE,
                RegimeState.BALANCE,
                reason="QUOTE_WALK_INVALIDATE",
                which=self._break.which.value,
                quote_walk_veto=True,
                sig_pull=pull.fired,
            )
            self._break = _BreakTracker()
            return

        if has_prints:
            self._break.first_print_seen = True

        # Accumulate sticky time outside
        if self._break.outside_since_ts is None:
            self._break.outside_since_ts = obs.ts

        sticky_s = obs.ts - self._break.outside_since_ts
        if sticky_s >= t.break_thresholds.t0_seconds and self._break.first_print_seen:
            self._confirm = _ConfirmTracker(
                window_start_ts=obs.ts,
                hold_start_ts=obs.ts,
                which=self._break.which,
            )
            self._transition(
                obs,
                RegimeState.BREAK_CANDIDATE,
                RegimeState.CONFIRM_WINDOW,
                reason="T0_MET_ENTER_CONFIRM",
                which=self._break.which.value,
                sig_pull=pull.fired,
                extra={"sticky_s": sticky_s},
            )

    def _step_confirm_window(
        self,
        obs: MarketObservation,
        balance,
        which: BreakWhich,
        outside_range: bool,
        outside_vwap: bool,
        has_prints: bool,
        qw,
        pull,
        dt: float,
    ) -> None:
        t = self.config.thresholds
        confirm_t = t.confirm

        if self._confirm.window_start_ts is None:
            self._confirm.window_start_ts = obs.ts

        # Timeout
        window_elapsed = obs.ts - self._confirm.window_start_ts
        if window_elapsed > confirm_t.confirm_timeout_seconds:
            self._finish_confirm(
                obs,
                passed=False,
                reason="CONFIRM_TIMEOUT",
                next_state=RegimeState.BALANCE,
                pull=pull,
                qw=qw,
            )
            return

        # Fast reclaim → FAIL
        if balance.in_balance:
            self._finish_confirm(
                obs,
                passed=False,
                reason="FAST_RECLAIM",
                next_state=RegimeState.BALANCE,
                pull=pull,
                qw=qw,
            )
            return

        if has_prints:
            self._confirm.n_prints += obs.print_count or 1
            self._confirm.signed_vol += obs.signed_volume_beyond_level or obs.print_volume

        t_hold_actual = obs.ts - (self._confirm.hold_start_ts or obs.ts)

        # C3: SIG-PULL in event_window must not co-promote weak single-leg breaks
        weak_single_leg = (
            obs.event_window
            and self._confirm.which in (BreakWhich.RANGE, BreakWhich.VWAP)
            and pull.fired
        )
        if weak_single_leg and not obs.macro_clear:
            self._finish_confirm(
                obs,
                passed=False,
                reason="EVENT_PULL_WEAK_SINGLE_LEG",
                next_state=RegimeState.FLAT_WATCH,
                pull=pull,
                qw=qw,
            )
            return

        result = evaluate_confirm(
            obs=obs,
            which=self._confirm.which,
            t_hold_actual=t_hold_actual,
            n_prints_accum=self._confirm.n_prints,
            signed_vol_accum=self._confirm.signed_vol,
            confirm_thresholds=confirm_t,
            event_window=obs.event_window,
            macro_clear=obs.macro_clear,
            first_print_seen=self._break.first_print_seen,
            quote_walk_vetoed=qw.vetoed and not has_prints,
            venue=obs.venue,
            venue_proxy=self.config.venue.proxy,
        )

        immediate_fail_reasons = {
            "EVENT_WINDOW_DEFAULT_FLAT_WATCH",
            "QUOTE_WALK_VETO",
            "EVENT_PULL_WEAK_SINGLE_LEG",
        }

        if result.passed:
            # SIG-PULL alone must NOT have caused this — we only PASS on full confirm recipe
            next_state = RegimeState.TREND_HANDOFF
            self._finish_confirm(
                obs,
                passed=True,
                reason=result.reason,
                next_state=next_state,
                pull=pull,
                qw=qw,
                confirm_result="PASS",
                extra={
                    "t_hold_s": t_hold_actual,
                    "n_prints": self._confirm.n_prints,
                    "venue": obs.venue,
                    "proxy": self.config.venue.proxy and obs.venue == "BN_AGG",
                },
            )
        elif result.failed and (
            t_hold_actual >= result.t_hold_required or result.reason in immediate_fail_reasons
        ):
            next_state = RegimeState[result.next_state] if result.next_state in RegimeState.__members__ else RegimeState.BALANCE
            self._finish_confirm(
                obs,
                passed=False,
                reason=result.reason,
                next_state=next_state,
                pull=pull,
                qw=qw,
                confirm_result="FAIL",
            )

    def _step_trend_handoff(self, obs: MarketObservation, balance, pull) -> None:
        if balance.in_balance:
            self._transition(
                obs,
                RegimeState.TREND_HANDOFF,
                RegimeState.BALANCE,
                reason="REBALANCE_AFTER_TREND",
                sig_pull=pull.fired,
            )
            self._break = _BreakTracker()
            self._confirm = _ConfirmTracker()

    def _step_flat_watch(self, obs: MarketObservation, balance) -> None:
        if balance.in_balance and not obs.event_window:
            self._transition(
                obs,
                RegimeState.FLAT_WATCH,
                RegimeState.BALANCE,
                reason="EVENT_CLEARED_REBALANCE",
            )

    def _finish_confirm(
        self,
        obs: MarketObservation,
        passed: bool,
        reason: str,
        next_state: RegimeState,
        pull,
        qw,
        confirm_result: str | None = None,
        extra: dict | None = None,
    ) -> None:
        self._transition(
            obs,
            RegimeState.CONFIRM_WINDOW,
            next_state,
            reason=reason,
            which=self._confirm.which.value,
            sig_pull=pull.fired,
            quote_walk_veto=qw.vetoed,
            confirm_result=confirm_result or ("PASS" if passed else "FAIL"),
            extra=extra or {},
        )
        self._break = _BreakTracker()
        self._confirm = _ConfirmTracker()

    def _transition(
        self,
        obs: MarketObservation,
        from_state: RegimeState,
        to_state: RegimeState,
        reason: str,
        which: str = "none",
        sig_pull: bool = False,
        quote_walk_veto: bool = False,
        confirm_result: str | None = None,
        extra: dict | None = None,
    ) -> None:
        self.state = to_state
        self.transitions.append(
            TransitionEvent(
                ts=obs.ts,
                from_state=from_state,
                to_state=to_state,
                reason=reason,
                which=which,
                sig_pull=sig_pull,
                quote_walk_veto=quote_walk_veto,
                confirm_result=confirm_result,
                venue=obs.venue,
                proxy=self.config.venue.proxy and obs.venue == "BN_AGG",
                extra=extra or {},
            )
        )

    def _log_veto(self, obs: MarketObservation, reason: str) -> None:
        """Log quote-walk VETO as a pseudo-transition for audit trail."""
        self.transitions.append(
            TransitionEvent(
                ts=obs.ts,
                from_state=self.state,
                to_state=self.state,
                reason=reason,
                quote_walk_veto=True,
                venue=obs.venue,
                proxy=self.config.venue.proxy and obs.venue == "BN_AGG",
                extra={"mid_move_bps": obs.mid_move_bps, "print_volume": obs.print_volume},
            )
        )

    def _delta_t(self, ts: float) -> float:
        if self._last_ts is None:
            return 0.0
        return ts - self._last_ts
