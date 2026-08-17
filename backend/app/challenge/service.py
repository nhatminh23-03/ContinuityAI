"""Human challenge / correct / learn workflow. PRD section 21, ARCHITECTURE.md section 54.

Closes FR-020 and AC-11, and resolves OPEN-01 / CI-13, which had been deferred to a "Phase 7
checkpoint". Deferring it made sense when the recompute path did not exist; now that
`app/services/recompute.py` is the same code the seed uses, the whole feature is a thin layer over
machinery that is already tested.

    manager disputes an assessment
        → evidence is added, linked, or re-mapped
            → readiness recomputed for the affected coverage
                → capability reassessed, system reaggregated
                    → before/after returned, both snapshots persisted

The rule that shapes every method here: **a manager changes evidence, never a score.** There is no
code path in this module — or anywhere else — that accepts a readiness level, an exposure state, or
a risk index. That is what makes "scores change because evidence changes" a property of the design
rather than a promise in a document.

Three actions, from PRD section 21:

* `LINK_EVIDENCE` — an artifact the extraction step missed or mis-mapped. The manager points at an
  existing artifact by reference; they cannot invent one, and the engineer must be a recorded
  participant of it. Same invariant the AI validation layer enforces, for the same reason.
* `MANAGER_ATTESTATION` — the manager states something no artifact captured. Recorded as evidence
  with `source_type=MANAGER_ATTESTATION` so it is always visibly distinguishable from
  artifact-derived proof, and **capped at MODERATE strength** whatever role is claimed.
* `CORRECT_CAPABILITY_MAPPING` — move one evidence record to the capability it actually belongs to.
  Both capabilities are recomputed, since one loses evidence as the other gains it.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.evidence.freshness import freshness_for
from app.evidence.strength import strength_for_role
from app.models import (
    Artifact,
    AssessmentChallenge,
    Capability,
    CapabilityAssessment,
    Coverage,
    Engineer,
    Evidence,
    SystemAssessment,
)
from app.repositories import CapabilityRepository, EngineerRepository
from app.schemas.challenge import (
    AssessmentSnapshot,
    ChallengeRequest,
    ChallengeResponse,
    SystemSnapshot,
)
from app.schemas.enums import (
    CapabilityExposure,
    ChallengeType,
    ContinuityRiskClass,
    EvidenceConfidence,
    EvidenceRole,
    EvidenceSourceType,
    EvidenceStrength,
    ReadinessLevel,
)
from app.services.recompute import recompute_capability

# DOMAIN_MODEL.md section 34: attestation "may carry lower confidence than direct operational
# evidence". Capping strength is how that is enforced rather than merely stated — a MODERATE record
# never counts toward the strong-source diversity that `VALIDATED` requires, so no number of
# attestations can manufacture a validated expert. They can establish ASSISTED or contribute to
# PRACTICED, which is the point: a manager who watched someone do the work can say so.
ATTESTATION_MAX_STRENGTH = EvidenceStrength.MODERATE


class ChallengeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def submit(self, capability_id: str, request: ChallengeRequest) -> ChallengeResponse:
        capability = CapabilityRepository(self.session).get(capability_id)
        if capability is None:
            raise NotFoundError(
                f"Capability '{capability_id}' not found.", {"capability_id": capability_id}
            )

        engineer = self._resolve_engineer(request)
        capability_before, system_before = self._snapshot(capability, request.engineer_id)

        created_id: str | None = None
        moved_id: str | None = None
        moved_from: str | None = None

        if request.challenge_type is ChallengeType.LINK_EVIDENCE:
            created_id = self._link_evidence(capability, engineer, request)
        elif request.challenge_type is ChallengeType.MANAGER_ATTESTATION:
            created_id = self._attest(capability, engineer, request)
        else:
            moved_id, moved_from = self._correct_mapping(capability, request)

        # Recompute from evidence. Both capabilities when a record moved between them.
        recompute_capability(self.session, capability.capability_id)
        if moved_from:
            recompute_capability(self.session, moved_from)

        capability_after, system_after = self._snapshot(capability, request.engineer_id)

        challenge = AssessmentChallenge(
            challenge_id=self._next_id(),
            capability_id=capability.capability_id,
            engineer_id=request.engineer_id,
            challenge_type=request.challenge_type.value,
            comment=request.comment.strip(),
            submitted_by=request.submitted_by,
            submitted_at=datetime.now(timezone.utc),
            evidence_created_id=created_id,
            evidence_moved_id=moved_id,
            moved_from_capability_id=moved_from,
            previous_assessment=capability_before.model_dump(mode="json"),
            new_assessment=capability_after.model_dump(mode="json"),
        )
        self.session.add(challenge)
        self.session.commit()

        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            challenge_type=request.challenge_type,
            capability_id=capability.capability_id,
            engineer_id=request.engineer_id,
            submitted_by=request.submitted_by,
            submitted_at=challenge.submitted_at,
            evidence_created=created_id,
            evidence_moved=moved_id,
            capability_before=capability_before,
            capability_after=capability_after,
            system_before=system_before,
            system_after=system_after,
            recomputed=capability_before != capability_after or system_before != system_after,
        )

    # -- actions ------------------------------------------------------------------------

    def _link_evidence(
        self, capability: Capability, engineer: Engineer, request: ChallengeRequest
    ) -> str:
        """Attach an artifact the extraction step missed, or mapped to the wrong capability."""
        if not request.source_reference:
            raise ValidationError(
                "LINK_EVIDENCE requires the source_reference of the artifact to link.",
                {"challenge_type": request.challenge_type.value},
            )

        artifact = self.session.scalar(
            select(Artifact).where(Artifact.source_reference == request.source_reference)
        )
        if artifact is None:
            raise NotFoundError(
                f"No ingested artifact with reference '{request.source_reference}'. A manager may "
                f"point at existing evidence, not create it.",
                {"source_reference": request.source_reference},
            )

        participants = {p["engineer_id"]: p["participant_role"] for p in artifact.participants}
        if engineer.engineer_id not in participants:
            # The same invariant the AI validation layer enforces. A claim against someone who does
            # not appear in the artifact is unsupported however it arrives.
            raise ValidationError(
                f"{engineer.name} is not a recorded participant of "
                f"{artifact.source_reference}, so it cannot evidence their work.",
                {
                    "source_reference": artifact.source_reference,
                    "participants": sorted(participants),
                },
            )

        existing = self.session.scalar(
            select(Evidence).where(
                Evidence.artifact_id == artifact.artifact_id,
                Evidence.engineer_id == engineer.engineer_id,
                Evidence.capability_id == capability.capability_id,
            )
        )
        if existing is not None:
            raise ValidationError(
                f"{artifact.source_reference} already evidences {engineer.name} for "
                f"{capability.name}.",
                {"evidence_id": existing.evidence_id},
            )

        role = request.evidence_role or self._role_for_participant(
            EvidenceSourceType(artifact.source_type), participants[engineer.engineer_id]
        )
        return self._create_evidence(
            capability=capability,
            engineer=engineer,
            artifact=artifact,
            source_type=EvidenceSourceType(artifact.source_type),
            source_reference=artifact.source_reference,
            source_title=artifact.title,
            artifact_date=artifact.artifact_date,
            role=role,
            strength=strength_for_role(role),
            summary=(
                f"{engineer.name}: {capability.name} evidenced by {artifact.source_reference}, "
                f"linked by {request.submitted_by} during review."
            ),
            provenance_source=artifact.provenance_source,
            provenance_record_id=artifact.source_reference,
            rationale=f"Manager-linked artifact. Reason: {request.comment.strip()}",
            suffix="linked",
        )

    def _attest(
        self, capability: Capability, engineer: Engineer, request: ChallengeRequest
    ) -> str:
        """Record what the manager states, distinguishably and at capped weight."""
        role = request.evidence_role or EvidenceRole.ASSISTED_EXECUTION
        strength = strength_for_role(role)
        if strength is EvidenceStrength.STRONG:
            strength = ATTESTATION_MAX_STRENGTH

        today = datetime.now(timezone.utc).date()
        return self._create_evidence(
            capability=capability,
            engineer=engineer,
            artifact=None,
            source_type=EvidenceSourceType.MANAGER_ATTESTATION,
            source_reference=f"ATTEST-{engineer.engineer_id}-{capability.capability_id}",
            source_title=f"Manager attestation by {request.submitted_by}",
            artifact_date=today,
            role=role,
            strength=strength,
            summary=(
                f"{request.submitted_by} attests that {engineer.name} has demonstrated "
                f"{capability.name}: {request.comment.strip()}"
            ),
            provenance_source="manager_attestation",
            provenance_record_id=request.submitted_by,
            rationale=(
                f"Manager attestation, not artifact-derived. Strength capped at "
                f"{strength.value} (DOMAIN_MODEL.md section 34)."
            ),
            suffix="attest",
        )

    def _correct_mapping(
        self, capability: Capability, request: ChallengeRequest
    ) -> tuple[str, str]:
        """Move one evidence record to the capability it belongs to."""
        if not request.evidence_id:
            raise ValidationError(
                "CORRECT_CAPABILITY_MAPPING requires the evidence_id to move.",
                {"challenge_type": request.challenge_type.value},
            )

        record = self.session.get(Evidence, request.evidence_id)
        if record is None:
            raise NotFoundError(
                f"Evidence '{request.evidence_id}' not found.", {"evidence_id": request.evidence_id}
            )
        if record.capability_id == capability.capability_id:
            raise ValidationError(
                f"Evidence '{record.evidence_id}' is already mapped to {capability.name}.",
                {"evidence_id": record.evidence_id},
            )
        if record.system_id != capability.system_id:
            raise ValidationError(
                "Evidence cannot be moved between systems; that would be a re-ingestion, not a "
                "mapping correction.",
                {"from_system": record.system_id, "to_system": capability.system_id},
            )

        moved_from = record.capability_id
        record.capability_id = capability.capability_id
        record.component_id = capability.component_id
        record.extraction_rationale = (
            f"{record.extraction_rationale} | Re-mapped from {moved_from} by "
            f"{request.submitted_by}: {request.comment.strip()}"
        )
        self.session.add(record)
        self.session.flush()
        return record.evidence_id, moved_from

    # -- helpers ------------------------------------------------------------------------

    def _create_evidence(
        self,
        *,
        capability: Capability,
        engineer: Engineer,
        artifact: Artifact | None,
        source_type: EvidenceSourceType,
        source_reference: str,
        source_title: str | None,
        artifact_date,
        role: EvidenceRole,
        strength: EvidenceStrength,
        summary: str,
        provenance_source: str,
        provenance_record_id: str,
        rationale: str,
        suffix: str,
    ) -> str:
        evidence_id = self._unique_evidence_id(
            f"evidence_{suffix}_{engineer.engineer_id.removeprefix('eng_')}_"
            f"{capability.capability_id.removeprefix('cap_')}"
        )
        self.session.add(
            Evidence(
                evidence_id=evidence_id,
                artifact_id=artifact.artifact_id if artifact else self._attestation_artifact(
                    source_reference, source_title, artifact_date, engineer, summary
                ),
                source_type=source_type.value,
                source_reference=source_reference,
                source_title=source_title,
                artifact_date=artifact_date,
                engineer_id=engineer.engineer_id,
                system_id=capability.system_id,
                component_id=capability.component_id,
                capability_id=capability.capability_id,
                evidence_role=role.value,
                evidence_strength=strength.value,
                summary=summary,
                freshness=freshness_for(artifact_date).value,
                provenance_source=provenance_source,
                provenance_record_id=provenance_record_id,
                provenance_url=artifact.source_url if artifact else None,
                # A human statement is not a high-confidence extraction. Labelling it MEDIUM keeps
                # the provenance drawer honest about where the claim came from.
                extraction_confidence=EvidenceConfidence.MEDIUM.value,
                is_conflicting=False,
                extraction_rationale=rationale,
            )
        )
        self.session.flush()
        return evidence_id

    def _attestation_artifact(
        self, source_reference: str, title: str | None, artifact_date, engineer: Engineer, body: str
    ) -> str:
        """Every evidence record must trace to an artifact (DOMAIN_MODEL.md section 12.2).

        An attestation has no external source, so the statement itself becomes the artifact. That
        keeps the invariant true rather than carving out an exception for human input.
        """
        artifact_id = f"artifact_{source_reference.lower().replace('-', '_')}"
        if self.session.get(Artifact, artifact_id) is None:
            self.session.add(
                Artifact(
                    artifact_id=artifact_id,
                    source_type=EvidenceSourceType.MANAGER_ATTESTATION.value,
                    source_reference=source_reference,
                    title=title,
                    body=body,
                    artifact_date=artifact_date,
                    participants=[
                        {
                            "engineer_id": engineer.engineer_id,
                            "participant_role": "ATTESTING_MANAGER",
                        }
                    ],
                    system_hint=None,
                    file_paths=[],
                    provenance_source="manager_attestation",
                    source_url=None,
                    extra={},
                )
            )
            self.session.flush()
        return artifact_id

    def _unique_evidence_id(self, base: str) -> str:
        candidate, index = base, 1
        while self.session.get(Evidence, candidate) is not None:
            index += 1
            candidate = f"{base}_{index}"
        return candidate

    def _resolve_engineer(self, request: ChallengeRequest) -> Engineer | None:
        if request.challenge_type is ChallengeType.CORRECT_CAPABILITY_MAPPING:
            return None
        if not request.engineer_id:
            raise ValidationError(
                f"{request.challenge_type.value} requires an engineer_id.",
                {"challenge_type": request.challenge_type.value},
            )
        engineer = EngineerRepository(self.session).get(request.engineer_id)
        if engineer is None:
            raise NotFoundError(
                f"Engineer '{request.engineer_id}' not found.",
                {"engineer_id": request.engineer_id},
            )
        return engineer

    @staticmethod
    def _role_for_participant(source_type: EvidenceSourceType, participant_role: str) -> EvidenceRole:
        """Fall back to the role the source system recorded, as extraction would have done."""
        from app.ai.deterministic import _ROLE_MAP
        from app.models.enums import ParticipantRole

        try:
            role = _ROLE_MAP.get((source_type, ParticipantRole(participant_role)))
        except ValueError:
            role = None
        return role or EvidenceRole.CONTRIBUTION

    def _snapshot(
        self, capability: Capability, engineer_id: str | None
    ) -> tuple[AssessmentSnapshot, SystemSnapshot]:
        assessment = self.session.get(CapabilityAssessment, capability.capability_id)
        system = self.session.get(SystemAssessment, capability.system_id)

        readiness = None
        if engineer_id:
            coverage = self.session.get(
                Coverage, {"engineer_id": engineer_id, "capability_id": capability.capability_id}
            )
            readiness = ReadinessLevel(coverage.readiness) if coverage else ReadinessLevel.NONE

        capability_snapshot = AssessmentSnapshot(
            exposure=CapabilityExposure(assessment.exposure)
            if assessment
            else CapabilityExposure.INSUFFICIENT_EVIDENCE,
            continuity_risk_index=assessment.continuity_risk_index if assessment else None,
            continuity_risk_class=(
                ContinuityRiskClass(assessment.continuity_risk_class)
                if assessment and assessment.continuity_risk_class
                else None
            ),
            evidence_confidence=EvidenceConfidence(assessment.evidence_confidence)
            if assessment
            else EvidenceConfidence.LOW,
            readiness=readiness,
            rules_triggered=list(assessment.rules_triggered) if assessment else [],
        )
        system_snapshot = SystemSnapshot(
            continuity_risk_index=system.continuity_risk_index if system else None,
            continuity_risk_class=(
                ContinuityRiskClass(system.continuity_risk_class)
                if system and system.continuity_risk_class
                else None
            ),
            exposure=CapabilityExposure(system.exposure)
            if system
            else CapabilityExposure.INSUFFICIENT_EVIDENCE,
            critical_gap_count=system.critical_gap_count if system else 0,
            degraded_capability_count=system.degraded_capability_count if system else 0,
            covered_capability_count=system.covered_capability_count if system else 0,
        )
        return capability_snapshot, system_snapshot

    def _next_id(self) -> str:
        used = int(
            self.session.scalar(select(func.count(AssessmentChallenge.challenge_id))) or 0
        )
        return f"challenge_{used + 1:03d}"
