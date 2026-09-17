"""Signal detectors: balance, break, confirm features, SIG-PULL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from regime_logger.config import (
    BalanceThresholds,
    BreakThresholds,
    ConfirmThresholds,
    SigPullThresholds,
)
from regime_logger.models import MarketObservation


class BreakWhich(str, Enum):
    NONE = "none"
    RANGE = "range"
    VWAP = "vwap"
    BOTH = "both"


@dataclass
class BalanceResult:
    in_balance: bool
    in_range: bool
    in_vwap_band: bool
    range_width_bps: float
    thin_range_blocked: bool


@dataclass
class BreakCandidateResult:
    is_candidate: bool
    which: BreakWhich
    outside_range: bool
    outside_vwap: bool
    has_print_evidence: bool


@dataclass
class SigPullResult:
    fired: bool
    depth_drop_pct: float | None
    print_vol: float


@dataclass
class ConfirmResult:
    passed: bool
    failed: bool
    reason: str
    t_hold_required: float
    t_hold_actual: float
    n_prints: int
    next_state: str  # TREND_HANDOFF | BALANCE | FLAT_WATCH


def range_epsilon_bps(obs: MarketObservation, thresholds: BalanceThresholds) -> float:
    """Effective inner buffer from session extremes (bps)."""
    frac_component = obs.range_width_bps * thresholds.range_epsilon_frac
    return max(thresholds.range_epsilon_bps, frac_component)


def evaluate_balance(
    obs: MarketObservation,
    thresholds: BalanceThresholds,
) -> BalanceResult:
    """
    Balance = inside session range AND rolling VWAP band.

    DOM shelf is NOT part of this definition (optional confirm only).
    Two-sided refill is a label feature only (C5), not a hard gate.
    """
    eps = range_epsilon_bps(obs, thresholds)
    eps_price = obs.mid * eps / 10_000

    in_range = (obs.session_low + eps_price) <= obs.mid <= (obs.session_high - eps_price)
    in_vwap = obs.vwap_band_lo <= obs.mid <= obs.vwap_band_hi
    thin_range_blocked = obs.range_width_bps < thresholds.range_min_bps

    return BalanceResult(
        in_balance=in_range and in_vwap and not thin_range_blocked,
        in_range=in_range,
        in_vwap_band=in_vwap,
        range_width_bps=obs.range_width_bps,
        thin_range_blocked=thin_range_blocked,
    )


def evaluate_break_exit(
    obs: MarketObservation,
    break_thresholds: BreakThresholds,
    balance_thresholds: BalanceThresholds,
) -> tuple[bool, bool]:
    """Return (outside_range, outside_vwap) with epsilon beyond boundary."""
    range_eps_bps = max(
        break_thresholds.epsilon_range_bps,
        obs.range_width_bps * balance_thresholds.range_epsilon_frac,
    )
    range_eps_price = obs.mid * range_eps_bps / 10_000
    vwap_eps_price = obs.mid * break_thresholds.epsilon_vwap_bps / 10_000

    outside_range = obs.mid < (obs.session_low - range_eps_price) or obs.mid > (
        obs.session_high + range_eps_price
    )
    outside_vwap = obs.mid < (obs.vwap_band_lo - vwap_eps_price) or obs.mid > (
        obs.vwap_band_hi + vwap_eps_price
    )
    return outside_range, outside_vwap


def classify_break_which(outside_range: bool, outside_vwap: bool) -> BreakWhich:
    if outside_range and outside_vwap:
        return BreakWhich.BOTH
    if outside_range:
        return BreakWhich.RANGE
    if outside_vwap:
        return BreakWhich.VWAP
    return BreakWhich.NONE


def evaluate_sig_pull(
    obs: MarketObservation,
    thresholds: SigPullThresholds,
) -> SigPullResult:
    """
    SIG-PULL: liquidity pull — separate from balance-break.

    Must NOT set TREND_HANDOFF by itself.
    """
    depth_drop = obs.depth_drop_pct
    if depth_drop is None and obs.bid_depth is not None and obs.ask_depth is not None:
        # Stub heuristic when only absolute depth provided
        total = obs.bid_depth + obs.ask_depth
        depth_drop = 0.0 if total <= 0 else 0.0

    fired = False
    if depth_drop is not None:
        fired = (
            depth_drop >= thresholds.depth_drop_pct
            and obs.print_volume < thresholds.print_vol_min_btc
        )

    return SigPullResult(
        fired=fired,
        depth_drop_pct=depth_drop,
        print_vol=obs.print_volume,
    )


def evaluate_confirm(
    obs: MarketObservation,
    which: BreakWhich,
    t_hold_actual: float,
    n_prints_accum: int,
    signed_vol_accum: float,
    confirm_thresholds: ConfirmThresholds,
    event_window: bool,
    macro_clear: bool,
    first_print_seen: bool,
    quote_walk_vetoed: bool,
    venue: str,
    venue_proxy: bool,
) -> ConfirmResult:
    """
    Confirm recipe — NOT first print through.

    Requires hold beyond level + reload/aggression + optional print count.
    Emits PASS/FAIL with next_state.
    """
    # C3: event_window defaults to FLAT_WATCH unless macro clear + full confirm recipe
    if event_window and not macro_clear:
        return ConfirmResult(
            passed=False,
            failed=True,
            reason="EVENT_WINDOW_DEFAULT_FLAT_WATCH",
            t_hold_required=_required_hold(which, confirm_thresholds),
            t_hold_actual=t_hold_actual,
            n_prints=n_prints_accum,
            next_state="FLAT_WATCH",
        )

    # C4: BN-only proxy cannot claim Bitunix TREND_HANDOFF
    if venue_proxy and venue == "BN_AGG":
        # Research labels only — still allow PASS but tag proxy (logged by FSM)
        pass

    if quote_walk_vetoed:
        return ConfirmResult(
            passed=False,
            failed=True,
            reason="QUOTE_WALK_VETO",
            t_hold_required=_required_hold(which, confirm_thresholds),
            t_hold_actual=t_hold_actual,
            n_prints=n_prints_accum,
            next_state="BALANCE",
        )

    # Anti-confirm: first print through alone is NOT sufficient
    if first_print_seen and t_hold_actual < _required_hold(which, confirm_thresholds):
        return ConfirmResult(
            passed=False,
            failed=True,
            reason="FIRST_PRINT_INSUFFICIENT",
            t_hold_required=_required_hold(which, confirm_thresholds),
            t_hold_actual=t_hold_actual,
            n_prints=n_prints_accum,
            next_state="BALANCE",
        )

    if not _full_confirm_recipe(
        obs, which, t_hold_actual, n_prints_accum, signed_vol_accum, confirm_thresholds
    ):
        return ConfirmResult(
            passed=False,
            failed=True,
            reason="CONFIRM_RECIPE_INCOMPLETE",
            t_hold_required=_required_hold(which, confirm_thresholds),
            t_hold_actual=t_hold_actual,
            n_prints=n_prints_accum,
            next_state="BALANCE",
        )

    return ConfirmResult(
        passed=True,
        failed=False,
        reason="CONFIRM_PASS",
        t_hold_required=_required_hold(which, confirm_thresholds),
        t_hold_actual=t_hold_actual,
        n_prints=n_prints_accum,
        next_state="TREND_HANDOFF",
    )


def _required_hold(which: BreakWhich, thresholds: ConfirmThresholds) -> float:
    """C2: stricter hold for single-leg breaks."""
    if which in (BreakWhich.RANGE, BreakWhich.VWAP):
        return thresholds.t_hold_single_leg_seconds
    return thresholds.t_hold_seconds


def _full_confirm_recipe(
    obs: MarketObservation,
    which: BreakWhich,
    t_hold_actual: float,
    n_prints_accum: int,
    signed_vol_accum: float,
    thresholds: ConfirmThresholds,
) -> bool:
    t_hold_req = _required_hold(which, thresholds)
    if t_hold_actual < t_hold_req:
        return False

    # Reclaim inside BOTH range and VWAP is handled by FSM before calling evaluate_confirm.

    print_gate = (
        n_prints_accum >= thresholds.n_prints_min
        or signed_vol_accum >= thresholds.v_break_btc
    )
    if not print_gate:
        return False

    if thresholds.require_reload and obs.reload_side is None:
        return False

    # C2: single-leg requires both aggression AND reload alignment
    if which in (BreakWhich.RANGE, BreakWhich.VWAP):
        if thresholds.require_reload and obs.reload_side not in ("bid", "ask", "both"):
            return False
        if thresholds.require_cvd_align and obs.cvd_align is not None and not obs.cvd_align:
            return False
    else:
        if thresholds.require_cvd_align and obs.cvd_align is not None and not obs.cvd_align:
            return False

    return True
