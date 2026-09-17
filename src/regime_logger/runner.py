"""Paper harness runner — transition log + develop summary."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from regime_logger.config import RegimeLoggerConfig, load_config
from regime_logger.fsm import RegimeFSM
from regime_logger.ingest import load_market_data
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
    develop_summary: dict | None = None

    for split_name, observations in [
        ("develop", splits.develop),
        ("validate", splits.validate),
        ("holdout", splits.holdout),
    ]:
        if not observations:
            continue

        fsm = RegimeFSM(config)
        fsm.run(observations)

        for tr in fsm.transitions:
            row = tr.to_dict()
            row["split"] = split_name
            all_transitions.append(row)

        if split_name == "develop":
            develop_summary = fsm.summary_counts()
            develop_summary["split"] = "develop"
            develop_summary["n_observations"] = len(observations)

    transition_path = output_dir / config.output.transition_log
    pd.DataFrame(all_transitions).to_csv(transition_path, index=False)

    summary_path = output_dir / config.output.summary_json
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(develop_summary or {}, fh, indent=2)

    return {
        "transition_log": str(transition_path),
        "summary_json": str(summary_path),
        "develop_summary": develop_summary,
        "n_transitions": len(all_transitions),
    }
