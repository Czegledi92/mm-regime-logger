"""Tests for chronological splits."""

from pathlib import Path

from regime_logger.config import SplitsConfig, load_config
from regime_logger.ingest import load_market_data
from regime_logger.splits import chronological_splits


def test_chronological_splits():
    cfg = load_config("config/regime_logger.default.yaml")
    df = load_market_data("data/stubs/sample_ticks.csv")
    splits = chronological_splits(df, cfg.splits)

    total = len(splits.develop) + len(splits.validate) + len(splits.holdout)
    assert total == len(df)
    if splits.develop and splits.validate:
        assert splits.develop[-1].ts <= splits.validate[0].ts
