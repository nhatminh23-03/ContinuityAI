"""Continuity engine: readiness, exposure, risk, and aggregation. All deterministic."""

from .aggregation import (
    EXPOSURE_SEVERITY,
    PlatformAssessmentResult,
    SystemAssessmentResult,
    aggregate_platform,
    aggregate_system,
)
from .exposure import CLASS_BANDS, CapabilityAssessmentResult, assess, band_for
from .facts import CapabilityFacts, CoverageFact, SystemFacts
from .readiness import ReadinessResult, classify
from .reason_codes import (
    MODIFIER_DELTAS,
    CapabilityReason,
    IndexModifier,
    ReadinessReason,
    SystemReason,
)

__all__ = [
    "CLASS_BANDS",
    "EXPOSURE_SEVERITY",
    "MODIFIER_DELTAS",
    "CapabilityAssessmentResult",
    "CapabilityFacts",
    "CapabilityReason",
    "CoverageFact",
    "IndexModifier",
    "PlatformAssessmentResult",
    "ReadinessReason",
    "ReadinessResult",
    "SystemAssessmentResult",
    "SystemFacts",
    "SystemReason",
    "aggregate_platform",
    "aggregate_system",
    "assess",
    "band_for",
    "classify",
]
