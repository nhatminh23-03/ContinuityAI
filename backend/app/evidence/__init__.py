"""Evidence engine: strength, freshness, and aggregation into coverage assessments."""

from .aggregation import EvidenceAggregate, EvidenceItem, aggregate
from .freshness import best_freshness, freshness_for
from .strength import (
    ADEQUATE_READINESS,
    READINESS_RANK,
    best_readiness,
    is_adequate,
    readiness_rank,
    strength_for_role,
)

__all__ = [
    "ADEQUATE_READINESS",
    "READINESS_RANK",
    "EvidenceAggregate",
    "EvidenceItem",
    "aggregate",
    "best_freshness",
    "best_readiness",
    "freshness_for",
    "is_adequate",
    "readiness_rank",
    "strength_for_role",
]
