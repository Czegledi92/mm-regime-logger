"""Paper harness runner — transition log + develop summary."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from regime_logger.config import RegimeLoggerConfig, load_config
from regime_logger.fsm import RegimeFSM
from regime_logger.ingest import load_market_data
from regime_logger.judgment.battery import JudgmentBattery
from regime_logger.splits import chronological_splits


def run_paper_harness(
    data_path: str | Path,
    config_path: str | Path,
    output_dir: str | Path = ".",
) -> dict:
    """
    Run the offline regime logger on stub data.

    Writes transition log (all splits) and summary counts (develop only).
    """
    config = load_config(config_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_market_data(data_path)
    splits = chronological_splits(df, config.splits)

    all_transitions: list[dict] = []
    all_battery_rows: list[dict] = []
    develop_summary: dict | None = None
    battery = JudgmentBattery(config.judgment_battery, config)

    for split_name, observations in [
        ("develop", splits.develop),
        ("validate", splits.validate),
        ("holdout", splits.holdout),
    ]:
        if not observations:
            continue

        fsm = RegimeFSM(config)
        for obs in observations:
            fsm.step(obs)
            if config.judgment_battery.enabled:
                batt = battery.evaluate(obs, fsm.state)
                row = _battery_row(batt)
                row["split"] = split_name
                row["fsm_state"] = fsm.state.value
                all_battery_rows.append(row)

        for tr in fsm.transitions:
            row = tr.to_dict()
            row["split"] = split_name
            all_transitions.append(row)

        if split_name == "develop":
            develop_summary = fsm.summary_counts()
            develop_summary["split"] = "develop"
            develop_summary["n_observations"] = len(observations)
            if config.judgment_battery.enabled:
                develop_summary["battery_short_circuits"] = sum(
                    1 for r in all_battery_rows if r.get("hard_gate_short_circuit")
                )
                develop_summary["battery_client"] = config.judgment_battery.client

    transition_path = output_dir / config.output.transition_log
    pd.DataFrame(all_transitions).to_csv(transition_path, index=False)

    summary_path = output_dir / config.output.summary_json
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(develop_summary or {}, fh, indent=2)

    battery_path = output_dir / config.output.battery_log
    if all_battery_rows:
        pd.DataFrame(all_battery_rows).to_csv(battery_path, index=False)

    return {
        "transition_log": str(transition_path),
        "summary_json": str(summary_path),
        "battery_log": str(battery_path) if all_battery_rows else None,
        "develop_summary": develop_summary,
        "n_transitions": len(all_transitions),
        "n_battery_rows": len(all_battery_rows),
    }


def _battery_row(batt) -> dict:
    """Flatten BatteryResult for CSV logging."""
    d = batt.to_dict()
    flat = {
        "ts": d["ts"],
        "hard_gate_short_circuit": d["hard_gate_short_circuit"],
        "short_circuit_reason": d.get("short_circuit_reason"),
        "sig_pull": d["sig_pull"],
        "client_name": d["client_name"],
        "regime_choice": d["regime"]["value"],
        "regime_confidence": d["regime"]["confidence"],
        "toxic_flow": d["toxic_flow"]["value"],
        "toxic_flow_confidence": d["toxic_flow"]["confidence"],
        "liquidity_stressed": d["liquidity_stressed"]["value"],
        "liquidity_stressed_confidence": d["liquidity_stressed"]["confidence"],
        "quote_walk_veto_risk": d["quote_walk_veto_risk"]["value"],
        "quote_walk_veto_risk_confidence": d["quote_walk_veto_risk"]["confidence"],
        "quote_environment": d["quote_environment"]["value"],
        "quote_environment_confidence": d["quote_environment"]["confidence"],
        "inventory_pressure": d["inventory_pressure"]["value"],
        "inventory_pressure_confidence": d["inventory_pressure"]["confidence"],
    }
    return flat
