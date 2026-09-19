"""Configuration loading and schema validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class VenueConfig:
    default: str = "BN_AGG"
    proxy: bool = True


@dataclass
class SessionConfig:
    anchor: str = "UTC_DAY"


@dataclass
class SplitsConfig:
    develop_frac: float = 0.6
    validate_frac: float = 0.2
    holdout_frac: float = 0.2


@dataclass
class BalanceThresholds:
    range_epsilon_bps: float = 10.0
    range_epsilon_frac: float = 0.05
    range_min_bps: float = 15.0


@dataclass
class BreakThresholds:
    t0_seconds: float = 10.0
    epsilon_range_bps: float = 15.0
    epsilon_vwap_bps: float = 12.0


@dataclass
class ConfirmThresholds:
    t_hold_seconds: float = 45.0
    t_hold_single_leg_seconds: float = 75.0
    n_prints_min: int = 5
    v_break_btc: float = 0.5
    require_reload: bool = True
    require_cvd_align: bool = True
    confirm_timeout_seconds: float = 120.0


@dataclass
class SigPullThresholds:
    depth_drop_pct: float = 0.30
    window_seconds: float = 5.0
    print_vol_min_btc: float = 0.1


@dataclass
class QuoteWalkThresholds:
    mid_move_bps_min: float = 3.0


@dataclass
class VwapThresholds:
    band_mode: str = "bps"
    band_bps: float = 50.0
    band_k_sigma: float = 2.0


@dataclass
class ThresholdsConfig:
    balance: BalanceThresholds = field(default_factory=BalanceThresholds)
    break_thresholds: BreakThresholds = field(default_factory=BreakThresholds)
    confirm: ConfirmThresholds = field(default_factory=ConfirmThresholds)
    sig_pull: SigPullThresholds = field(default_factory=SigPullThresholds)
    quote_walk: QuoteWalkThresholds = field(default_factory=QuoteWalkThresholds)
    vwap: VwapThresholds = field(default_factory=VwapThresholds)


@dataclass
class OutputConfig:
    transition_log: str = "regime_transitions.csv"
    summary_json: str = "regime_summary_develop.json"
    battery_log: str = "judgment_battery.csv"


@dataclass
class JudgmentBatteryThresholds:
    """DRAFT thresholds for stub judgment battery (calibrate on develop only)."""

    confidence_base: float = 0.75
    confidence_short_circuit: float = 0.35
    toxic_flow_event_window_boost: float = 0.25
    toxic_flow_sig_pull_boost: float = 0.20
    toxic_flow_quote_walk_boost: float = 0.30
    liquidity_stressed_depth_drop_min: float = 0.25
    liquidity_stressed_sig_pull_boost: float = 0.35
    quote_walk_veto_risk_mid_move_bps: float = 3.0
    quote_environment_base: float = 70.0
    quote_environment_toxic_penalty: float = 40.0
    quote_environment_liquidity_penalty: float = 30.0
    regime_break_min_print_volume: float = 0.01
    toxic_flow_high_threshold: float = 0.65
    liquidity_stressed_high_threshold: float = 0.55
    quote_walk_veto_risk_high_threshold: float = 0.50


@dataclass
class JudgmentBatteryConfig:
    """Judgment battery overlay config — stub client only (no live Jev)."""

    enabled: bool = True
    client: str = "stub"  # swap for future TypeSafe client behind JudgmentClient interface
    thresholds: JudgmentBatteryThresholds = field(default_factory=JudgmentBatteryThresholds)


@dataclass
class RegimeLoggerConfig:
    job_id: str = "JOB-20260917-MM-001"
    research_only: bool = True
    venue: VenueConfig = field(default_factory=VenueConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    splits: SplitsConfig = field(default_factory=SplitsConfig)
    thresholds: ThresholdsConfig = field(default_factory=ThresholdsConfig)
    judgment_battery: JudgmentBatteryConfig = field(default_factory=JudgmentBatteryConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def _merge_dataclass(cls: type, data: dict[str, Any] | None) -> Any:
    if not data:
        return cls()
    field_names = {f.name for f in cls.__dataclass_fields__.values()}
    kwargs = {k: v for k, v in data.items() if k in field_names}
    return cls(**kwargs)


def load_config(path: str | Path) -> RegimeLoggerConfig:
    """Load YAML config into typed dataclasses."""
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    thresholds_raw = raw.get("thresholds", {})
    thresholds = ThresholdsConfig(
        balance=_merge_dataclass(BalanceThresholds, thresholds_raw.get("balance")),
        break_thresholds=_merge_dataclass(BreakThresholds, thresholds_raw.get("break")),
        confirm=_merge_dataclass(ConfirmThresholds, thresholds_raw.get("confirm")),
        sig_pull=_merge_dataclass(SigPullThresholds, thresholds_raw.get("sig_pull")),
        quote_walk=_merge_dataclass(QuoteWalkThresholds, thresholds_raw.get("quote_walk")),
        vwap=_merge_dataclass(VwapThresholds, thresholds_raw.get("vwap")),
    )

    battery_raw = raw.get("judgment_battery", {})
    battery_thresholds_raw = battery_raw.get("thresholds", {})

    return RegimeLoggerConfig(
        job_id=raw.get("job_id", "JOB-20260917-MM-001"),
        research_only=raw.get("research_only", True),
        venue=_merge_dataclass(VenueConfig, raw.get("venue")),
        session=_merge_dataclass(SessionConfig, raw.get("session")),
        splits=_merge_dataclass(SplitsConfig, raw.get("splits")),
        thresholds=thresholds,
        judgment_battery=JudgmentBatteryConfig(
            enabled=battery_raw.get("enabled", True),
            client=battery_raw.get("client", "stub"),
            thresholds=_merge_dataclass(
                JudgmentBatteryThresholds, battery_thresholds_raw
            ),
        ),
        output=_merge_dataclass(OutputConfig, raw.get("output")),
    )


def config_schema_description() -> dict[str, Any]:
    """Return a JSON-serializable description of the config schema."""
    return {
        "job_id": "string — JOB identifier",
        "research_only": "bool — must remain true; no live trading",
        "venue": {
            "default": "string — e.g. BN_AGG",
            "proxy": "bool (DRAFT) — C4 BN proxy flag",
        },
        "session": {"anchor": "UTC_DAY (locked)"},
        "splits": {
            "develop_frac": "float (DRAFT)",
            "validate_frac": "float (DRAFT)",
            "holdout_frac": "float (DRAFT)",
        },
        "thresholds": {
            "balance": "range_epsilon_bps, range_epsilon_frac, range_min_bps (all DRAFT)",
            "break": "t0_seconds, epsilon_range_bps, epsilon_vwap_bps (all DRAFT)",
            "confirm": "t_hold_seconds, t_hold_single_leg_seconds, n_prints_min, v_break_btc, "
            "require_reload, require_cvd_align, confirm_timeout_seconds (all DRAFT)",
            "sig_pull": "depth_drop_pct, window_seconds, print_vol_min_btc (all DRAFT)",
            "quote_walk": "mid_move_bps_min (DRAFT)",
            "vwap": "band_mode, band_bps, band_k_sigma (all DRAFT)",
        },
        "judgment_battery": {
            "enabled": "bool — run stub battery overlay (no live Jev)",
            "client": "string — 'stub' only (future: typesafe behind interface)",
            "thresholds": "JudgmentBatteryThresholds fields (all DRAFT)",
        },
        "output": {
            "transition_log": "path for CSV transition log",
            "summary_json": "path for develop-split summary JSON",
            "battery_log": "path for judgment battery CSV log",
        },
    }
