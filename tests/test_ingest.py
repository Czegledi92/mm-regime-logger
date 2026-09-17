"""Tests for data ingestion."""

from pathlib import Path

import pytest

from regime_logger.ingest import load_market_data, observations_from_dataframe


def test_load_sample_csv():
    path = Path("data/stubs/sample_ticks.csv")
    df = load_market_data(path)
    assert len(df) > 0
    assert "mid" in df.columns

    obs = observations_from_dataframe(df)
    assert obs[0].prev_mid is None
    assert obs[1].prev_mid == obs[0].mid


def test_missing_columns_raises():
    import pandas as pd
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        f.write("ts,mid\n1,100\n")
        f.flush()
        with pytest.raises(ValueError, match="Missing required"):
            load_market_data(f.name)
