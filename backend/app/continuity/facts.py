"""Plain value objects the continuity rules operate on.

The rules are pure functions over these, with no database access. That is what lets the
counterfactual simulator answer "what if this engineer were unavailable?" by rebuilding facts
with one engineer filtered out and running the identical code path — rather than a second,
parallel implementation that could disagree with the baseline.

`docs/ARCHITECTURE.md` section 30 requires the simulator not to mutate baseline state.
`CapabilityFacts` being frozen makes that structural instead of a matter of discipline.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from app.evidence.strength import is_adequate, readiness_rank
from app.models.enums import RunbookState
from app.schemas.enums import (
    EvidenceConfidence,
    Freshness,
    OperationalCriticality,
    ReadinessLevel,
)


@dataclass(frozen=True)
class CoverageFact:
    """One engineer's demonstrated coverage of one capability."""

    engineer_id: str
    engineer_name: str
    readiness: ReadinessLevel
    freshness: Freshness
    evidence_confidence: EvidenceConfidence
    evidence_count: int = 0
    last_demonstrated_at: date | None = None

    @property
    def is_adequate(self) -> bool:
        """Adequate coverage means demonstrated hands-on execution: PRACTICED or VALIDATED.

        Stale evidence does not count. Someone who last did this three years ago, on a component
        that has moved on, is not current coverage — PRD rule R6.
        """
        return is_adequate(self.readiness) and self.freshness is not Freshness.STALE

    @property
    def rank(self) -> int:
        return readiness_rank(self.readiness)


@dataclass(frozen=True)
class CapabilityFacts:
    capability_id: str
    name: str
    component_id: str
    system_id: str
    operational_criticality: OperationalCriticality
    runbook_state: RunbookState
    coverages: tuple[CoverageFact, ...] = ()
    total_evidence_count: int = 0
    conflicting_evidence_count: int = 0

    # -- coverage views -----------------------------------------------------------------

    @property
    def ranked(self) -> list[CoverageFact]:
        """Coverages best first. Ties broken by evidence count, then id, so results are stable."""
        return sorted(
            self.coverages,
            key=lambda c: (-c.rank, -c.evidence_count, c.engineer_id),
        )

    @property
    def adequate(self) -> list[CoverageFact]:
        return [c for c in self.ranked if c.is_adequate]

    @property
    def adequate_count(self) -> int:
        return len(self.adequate)

    @property
    def primary(self) -> CoverageFact | None:
        """Strongest demonstrated coverage, adequate or not.

        Not "the owner" and not "the best engineer" — the person the available evidence most
        supports for this one capability.
        """
        ranked = self.ranked
        return ranked[0] if ranked else None

    @property
    def best_alternative(self) -> CoverageFact | None:
        """Strongest coverage excluding the primary. The backup, if there is one."""
        ranked = self.ranked
        return ranked[1] if len(ranked) > 1 else None

    @property
    def has_stale_adequate(self) -> bool:
        return any(
            is_adequate(c.readiness) and c.freshness is Freshness.STALE for c in self.coverages
        )

    # -- counterfactual -----------------------------------------------------------------

    def without(self, engineer_id: str) -> CapabilityFacts:
        """The same capability with one engineer's coverage excluded.

        This is the whole of the simulation's data model. Nothing is deleted, nothing is
        written; the baseline object is untouched and a new one is returned.
        """
        return replace(
            self,
            coverages=tuple(c for c in self.coverages if c.engineer_id != engineer_id),
        )

    def covers(self, engineer_id: str) -> bool:
        return any(c.engineer_id == engineer_id for c in self.coverages)


@dataclass(frozen=True)
class SystemFacts:
    system_id: str
    name: str
    platform_id: str
    business_criticality: str
    capabilities: tuple[CapabilityFacts, ...] = ()

    def without(self, engineer_id: str) -> SystemFacts:
        return replace(
            self,
            capabilities=tuple(c.without(engineer_id) for c in self.capabilities),
        )

    def touched_by(self, engineer_id: str) -> list[CapabilityFacts]:
        """Capabilities where this engineer has any demonstrated coverage at all.

        The simulation reports on these plus anything whose exposure changed. Reporting only on
        capabilities that changed would hide the useful negative result — that a capability the
        engineer contributes to stays covered anyway.
        """
        return [c for c in self.capabilities if c.covers(engineer_id)]
