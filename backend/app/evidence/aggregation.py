"""Aggregate individual evidence records into one assessment per coverage relationship.

docs/ARCHITECTURE.md section 26, docs/DOMAIN_MODEL.md section 15.

Input:  every Evidence record for one `(engineer, capability)` pair
Output: counts, diversity, freshness, and Evidence Confidence

This is where the product's "artifact, not activity" principle becomes arithmetic. Twenty weak
reviews aggregate to twenty weak reviews; they never accumulate into demonstrated execution,
because the readiness rules downstream read `independent_execution_count`, not `total`.

Evidence Confidence is computed here and is deliberately **orthogonal to risk**. A capability
can be HIGH risk with LOW confidence: the evidence points at exposure, and the evidence is
thin. Collapsing the two would let a data-quality problem read as safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.evidence.freshness import best_freshness
from app.schemas.enums import (
    EvidenceConfidence,
    EvidenceRole,
    EvidenceSourceType,
    EvidenceStrength,
    Freshness,
)


@dataclass(frozen=True)
class EvidenceItem:
    """A storage-agnostic view of one evidence record.

    Both the seed (building records in memory) and the simulator (reading rows back) aggregate
    through this, so there is exactly one aggregation implementation rather than two that can
    drift.
    """

    evidence_id: str
    source_type: EvidenceSourceType
    evidence_role: EvidenceRole
    evidence_strength: EvidenceStrength
    freshness: Freshness
    artifact_date: date
    is_conflicting: bool = False

    @classmethod
    def from_row(cls, row) -> EvidenceItem:
        return cls(
            evidence_id=row.evidence_id,
            source_type=EvidenceSourceType(row.source_type),
            evidence_role=EvidenceRole(row.evidence_role),
            evidence_strength=EvidenceStrength(row.evidence_strength),
            freshness=Freshness(row.freshness),
            artifact_date=row.artifact_date,
            is_conflicting=bool(row.is_conflicting),
        )


@dataclass
class EvidenceAggregate:
    engineer_id: str
    capability_id: str
    items: list[EvidenceItem] = field(default_factory=list)

    # -- volume and quality -------------------------------------------------------------
    @property
    def total(self) -> int:
        return len(self.qualifying)

    @property
    def qualifying(self) -> list[EvidenceItem]:
        """Conflicting records still count as evidence but never support a claim.

        They are surfaced separately in the provenance drawer and they depress confidence.
        """
        return [i for i in self.items if not i.is_conflicting]

    @property
    def conflicting(self) -> list[EvidenceItem]:
        return [i for i in self.items if i.is_conflicting]

    def _count_strength(self, strength: EvidenceStrength) -> int:
        return sum(1 for i in self.qualifying if i.evidence_strength is strength)

    def _count_role(self, role: EvidenceRole) -> int:
        return sum(1 for i in self.qualifying if i.evidence_role is role)

    @property
    def strong_count(self) -> int:
        return self._count_strength(EvidenceStrength.STRONG)

    @property
    def moderate_count(self) -> int:
        return self._count_strength(EvidenceStrength.MODERATE)

    @property
    def weak_count(self) -> int:
        return self._count_strength(EvidenceStrength.WEAK)

    @property
    def independent_execution_count(self) -> int:
        return self._count_role(EvidenceRole.INDEPENDENT_EXECUTION)

    @property
    def assisted_execution_count(self) -> int:
        return self._count_role(EvidenceRole.ASSISTED_EXECUTION)

    @property
    def contribution_count(self) -> int:
        return self._count_role(EvidenceRole.CONTRIBUTION)

    @property
    def knowledge_capture_count(self) -> int:
        return self._count_role(EvidenceRole.KNOWLEDGE_CAPTURE)

    @property
    def exposure_count(self) -> int:
        return self._count_role(EvidenceRole.EXPOSURE)

    # -- diversity ----------------------------------------------------------------------
    @property
    def source_types(self) -> set[EvidenceSourceType]:
        return {i.source_type for i in self.qualifying}

    @property
    def source_type_count(self) -> int:
        return len(self.source_types)

    @property
    def strong_source_type_count(self) -> int:
        """Diversity among *strong* records only.

        `VALIDATED` requires repeated independent execution across more than one kind of
        artifact. Two incidents from the same pager rotation are one kind of proof; an incident
        plus an authored runbook are two.
        """
        return len({i.source_type for i in self.qualifying if i.evidence_strength is EvidenceStrength.STRONG})

    # -- recency ------------------------------------------------------------------------
    @property
    def freshness(self) -> Freshness:
        return best_freshness([i.freshness for i in self.qualifying])

    @property
    def has_fresh_strong(self) -> bool:
        return any(
            i.evidence_strength is EvidenceStrength.STRONG and i.freshness is Freshness.FRESH
            for i in self.qualifying
        )

    @property
    def has_current_independent(self) -> bool:
        """An independent execution that has not gone stale."""
        return any(
            i.evidence_role is EvidenceRole.INDEPENDENT_EXECUTION and i.freshness is not Freshness.STALE
            for i in self.qualifying
        )

    @property
    def last_demonstrated_at(self) -> date | None:
        dates = [i.artifact_date for i in self.qualifying]
        return max(dates) if dates else None

    @property
    def supporting_evidence_ids(self) -> list[str]:
        return [i.evidence_id for i in sorted(self.qualifying, key=lambda i: (-i.artifact_date.toordinal(), i.evidence_id))]

    # -- confidence ---------------------------------------------------------------------
    @property
    def evidence_confidence(self) -> EvidenceConfidence:
        """PRD section 16.4. Not a probability, and not a statement about the person."""
        if self.conflicting:
            return EvidenceConfidence.LOW
        if self.total >= 3 and self.source_type_count >= 2 and self.has_fresh_strong:
            return EvidenceConfidence.HIGH
        if self.total >= 2 or self.strong_count >= 1:
            return EvidenceConfidence.MEDIUM
        return EvidenceConfidence.LOW

    def as_dict(self) -> dict:
        """Persisted alongside the coverage row so an assessment stays explainable."""
        return {
            "total": self.total,
            "strong_count": self.strong_count,
            "moderate_count": self.moderate_count,
            "weak_count": self.weak_count,
            "source_type_count": self.source_type_count,
            "strong_source_type_count": self.strong_source_type_count,
            "independent_execution_count": self.independent_execution_count,
            "assisted_execution_count": self.assisted_execution_count,
            "contribution_count": self.contribution_count,
            "knowledge_capture_count": self.knowledge_capture_count,
            "exposure_count": self.exposure_count,
            "conflicting_count": len(self.conflicting),
            "has_fresh_strong": self.has_fresh_strong,
        }


def aggregate(engineer_id: str, capability_id: str, items: list[EvidenceItem]) -> EvidenceAggregate:
    return EvidenceAggregate(engineer_id=engineer_id, capability_id=capability_id, items=list(items))


def group_by_coverage(items: list[EvidenceItem], keys: list[tuple[str, str]]) -> dict[tuple[str, str], EvidenceAggregate]:
    """Bucket evidence items into `(engineer_id, capability_id)` aggregates."""
    buckets: dict[tuple[str, str], list[EvidenceItem]] = {key: [] for key in keys}
    return {key: aggregate(key[0], key[1], buckets[key]) for key in buckets}
