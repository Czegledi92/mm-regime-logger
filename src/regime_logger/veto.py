"""VETO layer — quote-walk and shared toxicity gates."""

from __future__ import annotations

from dataclasses import dataclass

from regime_logger.config import QuoteWalkThresholds
from regime_logger.models import MarketObservation


@dataclass
class VetoResult:
    vetoed: bool
    reason: str | None = None


def check_quote_walk_veto(
    obs: MarketObservation,
    thresholds: QuoteWalkThresholds,
) -> VetoResult:
    """
    Quote-walk VETO: mid moves without prints at new prices.

    Per architecture v0.1 §3: do not treat mid/BBO moves without prints as aggression.
    """
    if obs.print_volume > 0 or obs.print_count > 0:
        return VetoResult(vetoed=False)

    if obs.mid_move_bps >= thresholds.mid_move_bps_min:
        return VetoResult(
            vetoed=True,
            reason="QUOTE_WALK",
        )

    return VetoResult(vetoed=False)
