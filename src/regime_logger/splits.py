"""Chronological develop / validate / holdout splits."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from regime_logger.config import SplitsConfig
from regime_logger.models import MarketObservation
from regime_logger.ingest import observations_from_dataframe


@dataclass
class DataSplits:
    develop: list[MarketObservation]
    validate: list[MarketObservation]
    holdout: list[MarketObservation]
    develop_end_ts: float
    validate_end_ts: float


def chronological_splits(
    df: pd.DataFrame,
    config: SplitsConfig,
) -> DataSplits:
    """
    Split data chronologically by timestamp fractions.

    Holdout is frozen until promote — only develop gets summary counts by default.
    """
    total = config.develop_frac + config.validate_frac + config.holdout_frac
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Split fractions must sum to 1.0, got {total}")

    df = df.sort_values("ts").reset_index(drop=True)
    n = len(df)
    if n == 0:
        return DataSplits([], [], [], 0.0, 0.0)

    dev_end = int(n * config.develop_frac)
    val_end = dev_end + int(n * config.validate_frac)

    dev_df = df.iloc[:dev_end]
    val_df = df.iloc[dev_end:val_end]
    hold_df = df.iloc[val_end:]

    develop_end_ts = float(dev_df["ts"].iloc[-1]) if len(dev_df) else 0.0
    validate_end_ts = float(val_df["ts"].iloc[-1]) if len(val_df) else develop_end_ts

    return DataSplits(
        develop=observations_from_dataframe(dev_df),
        validate=observations_from_dataframe(val_df),
        holdout=observations_from_dataframe(hold_df),
        develop_end_ts=develop_end_ts,
        validate_end_ts=validate_end_ts,
    )
