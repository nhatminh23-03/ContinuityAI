"""Read services behind the six GET endpoints.

Routes stay thin (docs/ARCHITECTURE.md section 13): parse, delegate, return. Everything these
services return was computed by the continuity engine at seed time and persisted, so a dashboard
load is a few indexed reads rather than a recomputation — which is what keeps reads inside the
AC-14 target.

Nothing here derives a domain value. If a field is not in the database, it does not get invented
at the boundary; that is the same rule the frontend follows, one layer up.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.evidence.strength import readiness_rank, role_priority
from app.repositories import (
    CapabilityRepository,
    CoverageRepository,
    EngineerRepository,
    EvidenceRepository,
    PlatformRepository,
    SystemRepository,
)
from app.schemas.capability import (
    CapabilityDetail,
    CapabilityRef,
    EngineerCoverage,
    EngineerRef,
    IndexModifier,
)
from app.schemas.enums import ReadinessLevel
from app.schemas.evidence import (
    CapabilityAssessment as CapabilityAssessmentDTO,
)
from app.schemas.evidence import (
    DeclaredOwnerRef,
    DeclaredVsDemonstrated,
    EngineerNameRef,
    EvidenceRecord,
    EvidenceResponse,
    MissingEvidence,
    Provenance,
)
from app.schemas.platform import PlatformListResponse, PlatformRef, PlatformSummary
from app.schemas.system import (
    ComponentSummary,
    DeclaredOwnership,
    SystemDetail,
    SystemListResponse,
    SystemSummary,
)

# Anyone below PRACTICED has not demonstrated the capability unaided, and saying so is what the
# provenance drawer is for. Previously this was set at ASSISTED, which meant Maria — the leading
# backup candidate — showed no note at all, even though "has assisted but has no independent
# recovery evidence" is exactly what a manager choosing a backup needs to read. Widened per
# RECOMMENDATIONS.md R-13.
MISSING_EVIDENCE_BELOW = readiness_rank(ReadinessLevel.PRACTICED)


class PlatformService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_platforms(self) -> PlatformListResponse:
        platforms = PlatformRepository(self.session)
        systems = SystemRepository(self.session)
        capabilities = CapabilityRepository(self.session)
        summaries: list[PlatformSummary] = []

        for platform in platforms.list_all():
            assessments = systems.assessments_for_platform(platform.platform_id)
            indexes = [a.continuity_risk_index for a in assessments if a.continuity_risk_index is not None]
            summaries.append(
                PlatformSummary(
                    platform_id=platform.platform_id,
                    name=platform.name,
                    description=platform.description,
                    system_count=len(systems.list_by_platform(platform.platform_id)),
                    critical_gap_count=sum(a.critical_gap_count for a in assessments),
                    # Counted in the database from the persisted per-capability adequate-engineer
                    # count, not derived here and not derivable by the client: summing
                    # `degraded_capability_count` would conflate "one expert" with "no expert"
                    # under DEC-07. See the repository method for why the `== 1` test is shared
                    # with the sole-expert reason codes.
                    single_expert_dependency_count=capabilities.sole_expert_count_for_platform(
                        platform.platform_id
                    ),
                    # No synthesised platform score (contract decision CI-10). The highest system
                    # answers "where do I look first?" without a second aggregation formula.
                    highest_system_risk_index=max(indexes) if indexes else None,
                    drift_status=platform.drift_status,
                )
            )
        return PlatformListResponse(platforms=summaries)


class SystemService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_platform(self, platform_id: str) -> SystemListResponse:
        platform = PlatformRepository(self.session).get(platform_id)
        if platform is None:
            raise NotFoundError(
                f"Platform '{platform_id}' not found.", {"platform_id": platform_id}
            )
        systems = SystemRepository(self.session)
        return SystemListResponse(
            platform=PlatformRef(platform_id=platform.platform_id, name=platform.name),
            systems=[
                self._summary(system, systems)
                for system in systems.list_by_platform(platform_id)
            ],
        )

    def detail(self, system_id: str) -> SystemDetail:
        systems = SystemRepository(self.session)
        system = systems.get(system_id)
        if system is None:
            raise NotFoundError(f"System '{system_id}' not found.", {"system_id": system_id})

        assessment = systems.assessment(system_id)
        summary = self._summary(system, systems)
        capabilities = CapabilityRepository(self.session).list_by_system(system_id)
        by_component: dict[str, list[str]] = {}
        for capability in capabilities:
            by_component.setdefault(capability.component_id, []).append(capability.capability_id)

        declared = systems.declared_owner(system_id)
        declared_ownership = None
        if declared is not None:
            owner, source_reference = declared
            declared_ownership = DeclaredOwnership(
                engineer_id=owner.engineer_id,
                name=owner.name,
                source=source_reference,
                # Declared ownership is never replaced by demonstrated coverage; the difference is
                # surfaced instead. DOMAIN_MODEL.md section 35.
                mismatch_detected=bool(assessment.declared_owner_mismatch) if assessment else False,
            )

        return SystemDetail(
            **summary.model_dump(),
            criticality_source=system.criticality_source,
            rules_triggered=list(assessment.rules_triggered) if assessment else [],
            declared_ownership=declared_ownership,
            components=[
                ComponentSummary(
                    component_id=component.component_id,
                    name=component.name,
                    description=component.description,
                    capability_ids=by_component.get(component.component_id, []),
                )
                for component in systems.components(system_id)
            ],
        )

    def _summary(self, system, systems: SystemRepository) -> SystemSummary:
        assessment = systems.assessment(system.system_id)
        if assessment is None:
            raise NotFoundError(
                f"System '{system.system_id}' has not been assessed. Run the seed command.",
                {"system_id": system.system_id},
            )
        return SystemSummary(
            system_id=system.system_id,
            platform_id=system.platform_id,
            name=system.name,
            description=system.description,
            business_criticality=system.business_criticality,
            continuity_risk_index=assessment.continuity_risk_index,
            continuity_risk_class=assessment.continuity_risk_class,
            exposure=assessment.exposure,
            evidence_confidence=assessment.evidence_confidence,
            critical_gap_count=assessment.critical_gap_count,
            degraded_capability_count=assessment.degraded_capability_count,
            covered_capability_count=assessment.covered_capability_count,
            insufficient_evidence_count=assessment.insufficient_evidence_count,
            drift_status=system.drift_status,
        )


class CapabilityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def detail(self, capability_id: str) -> CapabilityDetail:
        capabilities = CapabilityRepository(self.session)
        capability = capabilities.get(capability_id)
        if capability is None:
            raise NotFoundError(
                f"Capability '{capability_id}' not found.", {"capability_id": capability_id}
            )
        assessment = capabilities.assessment(capability_id)
        if assessment is None:
            raise NotFoundError(
                f"Capability '{capability_id}' has not been assessed. Run the seed command.",
                {"capability_id": capability_id},
            )

        engineers = EngineerRepository(self.session).by_id()
        coverages = CoverageRepository(self.session).list_by_capability(capability_id)
        ordered = sorted(
            coverages,
            key=lambda c: (-readiness_rank(c.readiness), c.engineer_id),
        )

        return CapabilityDetail(
            capability_id=capability.capability_id,
            component_id=capability.component_id,
            system_id=capability.system_id,
            name=capability.name,
            description=capability.description,
            operational_criticality=capability.operational_criticality,
            exposure=assessment.exposure,
            continuity_risk_index=assessment.continuity_risk_index,
            continuity_risk_class=assessment.continuity_risk_class,
            evidence_confidence=assessment.evidence_confidence,
            rules_triggered=list(assessment.rules_triggered),
            # The arithmetic behind the index, so it is inspectable rather than merely
            # reproducible. Optional and additive (DEC-11).
            index_modifiers=[
                IndexModifier(code=m["code"], delta=m["delta"])
                for m in (assessment.index_modifiers or [])
            ],
            primary_engineer=self._engineer_ref(assessment.primary_engineer_id, ordered, engineers),
            best_remaining_coverage=self._engineer_ref(
                assessment.best_remaining_engineer_id, ordered, engineers
            ),
            engineer_coverage=[
                EngineerCoverage(
                    engineer_id=row.engineer_id,
                    name=engineers[row.engineer_id].name,
                    readiness=row.readiness,
                    freshness=row.freshness,
                    evidence_confidence=row.evidence_confidence,
                    last_demonstrated_at=row.last_demonstrated_at,
                )
                for row in ordered
                if row.engineer_id in engineers
            ],
        )

    @staticmethod
    def _engineer_ref(engineer_id: str | None, coverages: list, engineers: dict) -> EngineerRef | None:
        if engineer_id is None or engineer_id not in engineers:
            return None
        row = next((c for c in coverages if c.engineer_id == engineer_id), None)
        if row is None:
            return None
        return EngineerRef(
            engineer_id=engineer_id, name=engineers[engineer_id].name, readiness=row.readiness
        )


class EvidenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def for_capability(self, capability_id: str, engineer_id: str | None = None) -> EvidenceResponse:
        capabilities = CapabilityRepository(self.session)
        capability = capabilities.get(capability_id)
        if capability is None:
            raise NotFoundError(
                f"Capability '{capability_id}' not found.", {"capability_id": capability_id}
            )
        assessment = capabilities.assessment(capability_id)
        if assessment is None:
            raise NotFoundError(
                f"Capability '{capability_id}' has not been assessed. Run the seed command.",
                {"capability_id": capability_id},
            )

        engineers = EngineerRepository(self.session).by_id()
        # Strongest evidence first, most recent within a role. A manager opening "Why?" wants the
        # independent production recovery at the top, not whatever happened to be written last.
        records = sorted(
            EvidenceRepository(self.session).list_by_capability(capability_id, engineer_id),
            key=lambda r: (role_priority(r.evidence_role), -r.artifact_date.toordinal()),
        )
        coverages = CoverageRepository(self.session).list_by_capability(capability_id)
        if engineer_id is not None:
            coverages = [c for c in coverages if c.engineer_id == engineer_id]

        systems = SystemRepository(self.session)
        declared = systems.declared_owner(capability.system_id)
        strongest_id = assessment.primary_engineer_id

        declared_vs_demonstrated = None
        if declared is not None or strongest_id is not None:
            owner_ref = None
            if declared is not None:
                owner, source_reference = declared
                owner_ref = DeclaredOwnerRef(
                    engineer_id=owner.engineer_id, name=owner.name, source=source_reference
                )
            strongest_ref = None
            if strongest_id is not None and strongest_id in engineers:
                strongest_ref = EngineerNameRef(
                    engineer_id=strongest_id, name=engineers[strongest_id].name
                )
            declared_vs_demonstrated = DeclaredVsDemonstrated(
                declared_owner=owner_ref,
                strongest_demonstrated_coverage=strongest_ref,
                mismatch_detected=bool(
                    owner_ref and strongest_ref and owner_ref.engineer_id != strongest_ref.engineer_id
                ),
            )

        return EvidenceResponse(
            capability=CapabilityRef(
                capability_id=capability.capability_id, name=capability.name
            ),
            assessment=CapabilityAssessmentDTO(
                exposure=assessment.exposure,
                evidence_confidence=assessment.evidence_confidence,
                rules_triggered=list(assessment.rules_triggered),
            ),
            evidence=[self._record(r) for r in records if not r.is_conflicting],
            missing_evidence=[
                MissingEvidence(
                    engineer_id=row.engineer_id,
                    engineer_name=engineers[row.engineer_id].name,
                    # Absence of evidence, never inability. PRD section 22.3.
                    description=(
                        f"No qualifying independent {capability.name.lower()} evidence found."
                    ),
                )
                for row in sorted(coverages, key=lambda c: c.engineer_id)
                if row.engineer_id in engineers
                and readiness_rank(row.readiness) < MISSING_EVIDENCE_BELOW
            ],
            conflicting_evidence=[self._record(r) for r in records if r.is_conflicting],
            declared_vs_demonstrated=declared_vs_demonstrated,
        )

    @staticmethod
    def _record(row) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=row.evidence_id,
            source_type=row.source_type,
            source_reference=row.source_reference,
            source_title=row.source_title,
            artifact_date=row.artifact_date,
            engineer_id=row.engineer_id,
            system_id=row.system_id,
            component_id=row.component_id,
            capability_id=row.capability_id,
            evidence_role=row.evidence_role,
            evidence_strength=row.evidence_strength,
            summary=row.summary,
            freshness=row.freshness,
            provenance=Provenance(
                source=row.provenance_source,
                record_id=row.provenance_record_id,
                source_url=row.provenance_url,
            ),
        )
