"""Ingest market data from CSV or Parquet stubs."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from regime_logger.models import MarketObservation

REQUIRED_COLUMNS = {
    "ts",
    "mid",
    "session_low",
    "session_high",
    "vwap",
    "vwap_band_lo",
    "vwap_band_hi",
}

OPTIONAL_COLUMNS = {
    "print_volume",
    "print_count",
    "signed_volume_beyond_level",
    "bid_depth",
    "ask_depth",
    "depth_drop_pct",
    "cvd_align",
    "reload_side",
    "shelf_confirm",
    "event_window",
    "macro_clear",
    "venue",
    "vwap_source",
}


def load_market_data(path: str | Path) -> pd.DataFrame:
    """Load stub data from CSV or Parquet."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    elif path.suffix.lower() in {".csv", ".tsv"}:
        sep = "\t" if path.suffix.lower() == ".tsv" else ","
        df = pd.read_csv(path, sep=sep)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.sort_values("ts").reset_index(drop=True)
    return df


def observations_from_dataframe(df: pd.DataFrame) -> list[MarketObservation]:
    """Convert a DataFrame into chronological MarketObservation rows."""
    observations: list[MarketObservation] = []
    prev_mid: float | None = None

    for _, row in df.iterrows():
        obs = MarketObservation(
            ts=float(row["ts"]),
            mid=float(row["mid"]),
            session_low=float(row["session_low"]),
            session_high=float(row["session_high"]),
            vwap=float(row["vwap"]),
            vwap_band_lo=float(row["vwap_band_lo"]),
            vwap_band_hi=float(row["vwap_band_hi"]),
            print_volume=float(row.get("print_volume", 0.0) or 0.0),
            print_count=int(row.get("print_count", 0) or 0),
            signed_volume_beyond_level=float(row.get("signed_volume_beyond_level", 0.0) or 0.0),
            bid_depth=_optional_float(row, "bid_depth"),
            ask_depth=_optional_float(row, "ask_depth"),
            depth_drop_pct=_optional_float(row, "depth_drop_pct"),
            cvd_align=_optional_bool(row, "cvd_align"),
            reload_side=_optional_str(row, "reload_side"),
            shelf_confirm=_optional_bool(row, "shelf_confirm"),
            event_window=bool(row.get("event_window", False)),
            macro_clear=bool(row.get("macro_clear", False)),
            venue=str(row.get("venue", "BN_AGG")),
            vwap_source=str(row.get("vwap_source", "MMT_DEV")),
            prev_mid=prev_mid,
        )
        observations.append(obs)
        prev_mid = obs.mid

    return observations


def _optional_float(row: pd.Series, col: str) -> float | None:
    if col not in row or pd.isna(row[col]):
        return None
    return float(row[col])


def _optional_bool(row: pd.Series, col: str) -> bool | None:
    if col not in row or pd.isna(row[col]):
        return None
    return bool(row[col])


def _optional_str(row: pd.Series, col: str) -> str | None:
    if col not in row or pd.isna(row[col]):
        return None
    return str(row[col])


def iter_observations(path: str | Path) -> Iterable[MarketObservation]:
    """Load file and yield observations."""
    df = load_market_data(path)
    return observations_from_dataframe(df)
