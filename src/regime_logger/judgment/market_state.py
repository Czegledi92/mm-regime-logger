"""Deterministic MarketState snapshot schema for judgment battery input."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from regime_logger.fsm import RegimeState
from regime_logger.judgment.gates import HardGateResult
from regime_logger.models import MarketObservation
from regime_logger.signals import BreakWhich, evaluate_balance, evaluate_break_exit


@dataclass
class HardGateStatus:
    """Lucas / deterministic gate flags embedded in MarketState."""

    thin_range_blocked: bool = False
    quote_walk_veto: bool = False
    event_window: bool = False
    macro_clear: bool = False
    sig_pull: bool = False
    hard_veto_active: bool = False
    short_circuit_reason: str | None = None


@dataclass
class MarketState:
    """
    JSON-serializable market snapshot for judgment battery.

    Built deterministically from observation + FSM context + hard-gate results.
    """

    ts: float
    mid: float
    session_low: float
    session_high: float
    vwap: float
    vwap_band_lo: float
    vwap_band_hi: float
    range_width_bps: float
    mid_move_bps: float
    in_balance: bool
    in_range: bool
    in_vwap_band: bool
    outside_range: bool
    outside_vwap: bool
    break_which: str
    fsm_state: str
    print_volume: float
    print_count: int
    depth_drop_pct: float | None
    event_window: bool
    macro_clear: bool
    venue: str
    venue_proxy: bool
    vwap_source: str
    hard_gates: HardGateStatus
    schema_version: str = "0.1"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["hard_gates"] = asdict(self.hard_gates)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketState:
        hg = data.get("hard_gates", {})
        hard_gates = HardGateStatus(
            thin_range_blocked=bool(hg.get("thin_range_blocked", False)),
            quote_walk_veto=bool(hg.get("quote_walk_veto", False)),
            event_window=bool(hg.get("event_window", False)),
            macro_clear=bool(hg.get("macro_clear", False)),
            sig_pull=bool(hg.get("sig_pull", False)),
            hard_veto_active=bool(hg.get("hard_veto_active", False)),
            short_circuit_reason=hg.get("short_circuit_reason"),
        )
        return cls(
            ts=float(data["ts"]),
            mid=float(data["mid"]),
            session_low=float(data["session_low"]),
            session_high=float(data["session_high"]),
            vwap=float(data["vwap"]),
            vwap_band_lo=float(data["vwap_band_lo"]),
            vwap_band_hi=float(data["vwap_band_hi"]),
            range_width_bps=float(data["range_width_bps"]),
            mid_move_bps=float(data.get("mid_move_bps", 0.0)),
            in_balance=bool(data["in_balance"]),
            in_range=bool(data["in_range"]),
            in_vwap_band=bool(data["in_vwap_band"]),
            outside_range=bool(data["outside_range"]),
            outside_vwap=bool(data["outside_vwap"]),
            break_which=str(data["break_which"]),
            fsm_state=str(data["fsm_state"]),
            print_volume=float(data.get("print_volume", 0.0)),
            print_count=int(data.get("print_count", 0)),
            depth_drop_pct=data.get("depth_drop_pct"),
            event_window=bool(data.get("event_window", False)),
            macro_clear=bool(data.get("macro_clear", False)),
            venue=str(data.get("venue", "BN_AGG")),
            venue_proxy=bool(data.get("venue_proxy", True)),
            vwap_source=str(data.get("vwap_source", "MMT_DEV")),
            hard_gates=hard_gates,
            schema_version=str(data.get("schema_version", "0.1")),
            extra=dict(data.get("extra", {})),
        )


REQUIRED_MARKET_STATE_FIELDS = frozenset(
    {
        "ts",
        "mid",
        "session_low",
        "session_high",
        "vwap",
        "vwap_band_lo",
        "vwap_band_hi",
        "range_width_bps",
        "in_balance",
        "in_range",
        "in_vwap_band",
        "outside_range",
        "outside_vwap",
        "break_which",
        "fsm_state",
        "hard_gates",
        "schema_version",
    }
)

VALID_BREAK_WHICH = frozenset({"none", "range", "vwap", "both"})
VALID_FSM_STATES = frozenset(s.value for s in RegimeState)
VALID_REGIME_CHOICES = frozenset({"BALANCE", "BREAK_CANDIDATE", "TREND_HANDOFF", "FLAT_WATCH"})


def market_state_schema() -> dict[str, Any]:
    """Return JSON-schema-like description of MarketState (for docs / CLI)."""
    return {
        "schema_version": "0.1",
        "type": "object",
        "required": sorted(REQUIRED_MARKET_STATE_FIELDS),
        "properties": {
            "ts": "float — epoch seconds",
            "mid": "float — mid price",
            "session_low": "float",
            "session_high": "float",
            "vwap": "float",
            "vwap_band_lo": "float",
            "vwap_band_hi": "float",
            "range_width_bps": "float",
            "mid_move_bps": "float",
            "in_balance": "bool — range ∩ VWAP band (locked definition)",
            "in_range": "bool",
            "in_vwap_band": "bool",
            "outside_range": "bool",
            "outside_vwap": "bool",
            "break_which": f"enum {sorted(VALID_BREAK_WHICH)}",
            "fsm_state": f"enum {sorted(VALID_FSM_STATES)}",
            "print_volume": "float",
            "print_count": "int",
            "depth_drop_pct": "float | null",
            "event_window": "bool",
            "macro_clear": "bool",
            "venue": "string",
            "venue_proxy": "bool",
            "vwap_source": "string",
            "hard_gates": {
                "thin_range_blocked": "bool — C1 R_min gate",
                "quote_walk_veto": "bool",
                "event_window": "bool",
                "macro_clear": "bool",
                "sig_pull": "bool — orthogonal; never alone → TREND",
                "hard_veto_active": "bool",
                "short_circuit_reason": "string | null",
            },
        },
    }


def validate_market_state(data: dict[str, Any]) -> list[str]:
    """Validate a MarketState dict; return list of error messages (empty = valid)."""
    errors: list[str] = []

    missing = REQUIRED_MARKET_STATE_FIELDS - set(data.keys())
    if missing:
        errors.append(f"missing required fields: {sorted(missing)}")

    if data.get("schema_version") not in ("0.1", None):
        errors.append(f"unsupported schema_version: {data.get('schema_version')}")

    if data.get("break_which") not in VALID_BREAK_WHICH:
        errors.append(f"invalid break_which: {data.get('break_which')}")

    if data.get("fsm_state") not in VALID_FSM_STATES:
        errors.append(f"invalid fsm_state: {data.get('fsm_state')}")

    hg = data.get("hard_gates")
    if hg is not None and not isinstance(hg, dict):
        errors.append("hard_gates must be an object")

    for field_name in ("ts", "mid", "session_low", "session_high", "vwap"):
        if field_name in data:
            try:
                float(data[field_name])
            except (TypeError, ValueError):
                errors.append(f"{field_name} must be numeric")

    return errors


def build_market_state(
    obs: MarketObservation,
    fsm_state: RegimeState,
    gate_result: HardGateResult,
    venue_proxy: bool = True,
) -> MarketState:
    """Build MarketState from observation, FSM state, and evaluated hard gates."""
    from regime_logger.config import BalanceThresholds, BreakThresholds

    # Use minimal threshold defaults for snapshot fields; caller passes real config via gates.
    balance = evaluate_balance(obs, BalanceThresholds())
    outside_range, outside_vwap = evaluate_break_exit(
        obs, BreakThresholds(), BalanceThresholds()
    )
    which = BreakWhich.NONE
    if outside_range and outside_vwap:
        which = BreakWhich.BOTH
    elif outside_range:
        which = BreakWhich.RANGE
    elif outside_vwap:
        which = BreakWhich.VWAP

    hard_gates = HardGateStatus(
        thin_range_blocked=gate_result.thin_range_blocked,
        quote_walk_veto=gate_result.quote_walk_veto,
        event_window=gate_result.event_window,
        macro_clear=gate_result.macro_clear,
        sig_pull=gate_result.sig_pull,
        hard_veto_active=gate_result.hard_veto_active,
        short_circuit_reason=gate_result.short_circuit_reason,
    )

    return MarketState(
        ts=obs.ts,
        mid=obs.mid,
        session_low=obs.session_low,
        session_high=obs.session_high,
        vwap=obs.vwap,
        vwap_band_lo=obs.vwap_band_lo,
        vwap_band_hi=obs.vwap_band_hi,
        range_width_bps=obs.range_width_bps,
        mid_move_bps=obs.mid_move_bps,
        in_balance=balance.in_balance,
        in_range=balance.in_range,
        in_vwap_band=balance.in_vwap_band,
        outside_range=outside_range,
        outside_vwap=outside_vwap,
        break_which=which.value,
        fsm_state=fsm_state.value,
        print_volume=obs.print_volume,
        print_count=obs.print_count,
        depth_drop_pct=obs.depth_drop_pct,
        event_window=obs.event_window,
        macro_clear=obs.macro_clear,
        venue=obs.venue,
        venue_proxy=venue_proxy and obs.venue == "BN_AGG",
        vwap_source=obs.vwap_source,
        hard_gates=hard_gates,
    )
