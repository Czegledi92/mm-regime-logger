"""Data models for tick/bar observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MarketObservation:
    """One chronological market snapshot for the regime logger."""

    ts: float
    mid: float
    session_low: float
    session_high: float
    vwap: float
    vwap_band_lo: float
    vwap_band_hi: float

    # Print / tape evidence
    print_volume: float = 0.0
    print_count: int = 0
    signed_volume_beyond_level: float = 0.0

    # Optional depth / CVD columns
    bid_depth: Optional[float] = None
    ask_depth: Optional[float] = None
    depth_drop_pct: Optional[float] = None
    cvd_align: Optional[bool] = None
    reload_side: Optional[str] = None  # "bid" | "ask" | "both" | None

    # Optional confirm feature (NOT part of balance definition)
    shelf_confirm: Optional[bool] = None

    # Event / venue overlays
    event_window: bool = False
    macro_clear: bool = False
    venue: str = "BN_AGG"
    vwap_source: str = "MMT_DEV"

    # Prior mid for quote-walk detection (filled by ingest if absent)
    prev_mid: Optional[float] = None

    @property
    def range_width_bps(self) -> float:
        if self.session_high <= 0:
            return 0.0
        width = self.session_high - self.session_low
        return (width / self.mid) * 10_000 if self.mid > 0 else 0.0

    @property
    def mid_move_bps(self) -> float:
        if self.prev_mid is None or self.prev_mid <= 0:
            return 0.0
        return abs(self.mid - self.prev_mid) / self.prev_mid * 10_000
