"""Backup candidate comparison. PRD section 19, API contract section 8.8.

The product will not claim to know the right staffing choice, because workload, leave, career
goals, and team priorities are outside the evidence model entirely. What it can do is say which
engineers have demonstrated adjacent technical work, and show the trade-offs.

Technical overlap is a band, never a percentage. "87% match" implies a precision nothing here
supports; `HIGH` / `MEDIUM` / `LOW` says what the evidence can actually carry (PRD section 19.3).

Scoring, in full — deliberately small enough to explain in a sentence:

    target readiness            VALIDATED 6, PRACTICED 5, ASSISTED 3, EXPOSED 1, NONE 0
    same component, others      +3 if PRACTICED or better, +1 if ASSISTED
    same system, other parts    +2 if PRACTICED or better, +1 if ASSISTED
    operational evidence        +1 if the candidate has incident evidence in this system
    current target evidence     +1 if their evidence on the target capability is FRESH

    HIGH >= 6      MEDIUM 3-5      LOW <= 2

Same-component adjacency is weighted above elsewhere-in-system because it is the stronger signal:
someone who has done provider failover in the same integration layer is closer to gateway
incident recovery than someone who has done retry logic in the transaction processor. Freshness
counts only on the target capability — recency about *this* capability is meaningful, whereas a
recent unrelated change is not.

There is no employee ranking here. Candidates are ordered by evidence overlap for one capability
and the manager chooses; nothing is assigned.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, get_provider
from app.ai.schemas import CandidateNarrativeContext
from app.continuity.facts import CapabilityFacts
from app.core.errors import NotFoundError
from app.evidence.strength import is_adequate, readiness_rank
from app.repositories import (
    CapabilityRepository,
    CoverageRepository,
    EngineerRepository,
    EvidenceRepository,
    SimulationRepository,
)
from app.schemas.capability import CapabilityRef
from app.schemas.enums import (
    EvidenceConfidence,
    EvidenceSourceType,
    Freshness,
    ReadinessLevel,
    TechnicalOverlap,
)
from app.schemas.recommendation import (
    BackupCandidate,
    BackupCandidateRequest,
    BackupCandidateResponse,
)
from app.services.facts import build_capability_facts

TARGET_READINESS_POINTS: dict[ReadinessLevel, int] = {
    ReadinessLevel.VALIDATED: 6,
    ReadinessLevel.PRACTICED: 5,
    ReadinessLevel.ASSISTED: 3,
    ReadinessLevel.EXPOSED: 1,
    ReadinessLevel.NONE: 0,
}

SAME_COMPONENT_ADEQUATE = 3
SAME_COMPONENT_ASSISTED = 1
SAME_SYSTEM_ADEQUATE = 2
SAME_SYSTEM_ASSISTED = 1
OPERATIONAL_EVIDENCE_BONUS = 1
FRESH_TARGET_BONUS = 1

HIGH_THRESHOLD = 6
MEDIUM_THRESHOLD = 3

MAX_STRENGTHS = 4
MAX_GAPS = 3

# Reviewed once here and reused, so the limitation cannot be forgotten on one screen.
DISCLAIMER = (
    "Technical overlap only. Workload, availability, staffing priorities, and career goals are "
    "not evaluated."
)
NO_CANDIDATE_MESSAGE = (
    "No strong internal technical backup candidate was identified from the available evidence."
)


class BackupCandidateService:
    def __init__(self, session: Session, provider: AIProvider | None = None) -> None:
        self.session = session
        self.provider = provider or get_provider()

    def compare(self, request: BackupCandidateRequest) -> BackupCandidateResponse:
        capability = CapabilityRepository(self.session).get(request.capability_id)
        if capability is None:
            raise NotFoundError(
                f"Capability '{request.capability_id}' not found.",
                {"capability_id": request.capability_id},
            )

        target = build_capability_facts(self.session, request.capability_id)
        excluded = self._excluded_engineers(target, request.simulation_id)

        system_coverage = CoverageRepository(self.session).list_by_system(capability.system_id)
        capabilities = {
            c.capability_id: c for c in CapabilityRepository(self.session).list_by_system(capability.system_id)
        }
        engineers = EngineerRepository(self.session).by_id()

        by_engineer: dict[str, dict[str, object]] = {}
        for row in system_coverage:
            by_engineer.setdefault(row.engineer_id, {})[row.capability_id] = row

        scored: list[tuple[int, BackupCandidate, CandidateNarrativeContext]] = []
        for engineer_id, coverage_by_capability in by_engineer.items():
            if engineer_id in excluded or engineer_id not in engineers:
                continue
            if not self._eligible(engineer_id, coverage_by_capability, capability, capabilities):
                continue
            system_evidence = EvidenceRepository(self.session).list_by_engineer_and_system(
                engineer_id, capability.system_id
            )
            score = self._score(
                coverage_by_capability, capability, capabilities, system_evidence
            )
            if score <= 0:
                continue
            candidate, narrative_context = self._candidate(
                engineer_id,
                engineers[engineer_id].name,
                score,
                coverage_by_capability,
                capability,
                capabilities,
                system_evidence,
            )
            scored.append((score, candidate, narrative_context))

        scored.sort(key=lambda item: (-item[0], item[1].engineer_id))

        # Narration happens here, after the slice, rather than inside the scoring loop above. The
        # loop runs once per *eligible engineer* — four of them for cap_retry_logic on the seeded
        # dataset, and bounded by nothing except how many engineers happen to qualify — so a
        # model-backed provider was being paid for narratives on candidates that were then
        # discarded, and enough of them to put AC-14's 12-second budget out of reach. Deferring
        # bounds the provider calls at `limit`, which the contract caps at 3.
        candidates = [
            self._narrate(candidate, narrative_context)
            for _, candidate, narrative_context in scored[: request.limit]
        ]

        # `message` is omitted rather than sent as null when candidates exist: the contract only
        # documents it for the empty case, and an explicit null would show up as a contract diff.
        payload: dict = {
            "capability": CapabilityRef(
                capability_id=capability.capability_id, name=capability.name
            ),
            "candidates": candidates,
            "disclaimer": DISCLAIMER,
        }
        if not candidates:
            payload["message"] = NO_CANDIDATE_MESSAGE
        return BackupCandidateResponse(**payload)

    # -- selection ----------------------------------------------------------------------

    def _excluded_engineers(self, target: CapabilityFacts, simulation_id: str | None) -> set[str]:
        """Whoever currently holds the capability, and whoever was simulated away.

        Offering the person you are trying to build a backup for would be worse than useless.
        """
        excluded: set[str] = set()
        primary = target.primary
        if primary is not None and is_adequate(primary.readiness):
            excluded.add(primary.engineer_id)
        if simulation_id:
            simulation = SimulationRepository(self.session).get(simulation_id)
            if simulation is not None:
                excluded.add(simulation.engineer_id)
        return excluded

    @staticmethod
    def _eligible(
        engineer_id: str,
        coverage_by_capability: dict,
        capability,
        capabilities: dict,
    ) -> bool:
        """Some demonstrable connection to the work, not merely membership of the same team.

        Either the candidate has touched this capability, or they have practised something in the
        same component. Absent both, the "adjacency" claim would rest on nothing.
        """
        target_row = coverage_by_capability.get(capability.capability_id)
        if target_row is not None and readiness_rank(target_row.readiness) >= readiness_rank(
            ReadinessLevel.EXPOSED
        ):
            return True
        return any(
            is_adequate(row.readiness)
            and capabilities[capability_id].component_id == capability.component_id
            for capability_id, row in coverage_by_capability.items()
            if capability_id in capabilities and capability_id != capability.capability_id
        )

    @staticmethod
    def _score(
        coverage_by_capability: dict,
        capability,
        capabilities: dict,
        system_evidence: list,
    ) -> int:
        """The whole score in one place, so ordering and the displayed band cannot disagree."""
        target_row = coverage_by_capability.get(capability.capability_id)
        target_readiness = (
            ReadinessLevel(target_row.readiness) if target_row is not None else ReadinessLevel.NONE
        )
        score = TARGET_READINESS_POINTS[target_readiness]

        for capability_id, row in coverage_by_capability.items():
            if capability_id == capability.capability_id or capability_id not in capabilities:
                continue
            same_component = capabilities[capability_id].component_id == capability.component_id
            readiness = ReadinessLevel(row.readiness)
            if is_adequate(readiness):
                score += SAME_COMPONENT_ADEQUATE if same_component else SAME_SYSTEM_ADEQUATE
            elif readiness is ReadinessLevel.ASSISTED:
                score += SAME_COMPONENT_ASSISTED if same_component else SAME_SYSTEM_ASSISTED

        if target_row is not None and Freshness(target_row.freshness) is Freshness.FRESH:
            score += FRESH_TARGET_BONUS

        # Operational experience is a distinct signal from development experience: having been in a
        # live incident on this system carries context a pull request cannot demonstrate.
        if any(e.source_type == EvidenceSourceType.INCIDENT.value for e in system_evidence):
            score += OPERATIONAL_EVIDENCE_BONUS

        return score

    def _candidate(
        self,
        engineer_id: str,
        engineer_name: str,
        score: int,
        coverage_by_capability: dict,
        capability,
        capabilities: dict,
        system_evidence: list,
    ) -> tuple[BackupCandidate, CandidateNarrativeContext]:
        """The candidate's structured half, plus the facts a provider may narrate.

        The two are returned separately because narration is deferred to `_narrate`, which runs
        only for the candidates that survive the `limit` slice. Everything here is computed for
        every eligible engineer, because the score decides who survives.
        """
        target_row = coverage_by_capability.get(capability.capability_id)
        target_readiness = (
            ReadinessLevel(target_row.readiness) if target_row is not None else ReadinessLevel.NONE
        )

        demonstrated: list[str] = []
        assisted: list[str] = []
        missing: list[str] = []

        if target_readiness is ReadinessLevel.ASSISTED:
            assisted.append(capability.name)
        if not is_adequate(target_readiness):
            missing.append(capability.name)

        for capability_id, row in sorted(coverage_by_capability.items()):
            if capability_id == capability.capability_id or capability_id not in capabilities:
                continue
            other = capabilities[capability_id]
            readiness = ReadinessLevel(row.readiness)
            if is_adequate(readiness):
                demonstrated.append(other.name)
            elif readiness is ReadinessLevel.ASSISTED:
                assisted.append(other.name)
            elif other.component_id == capability.component_id:
                missing.append(other.name)

        narrative_context = CandidateNarrativeContext(
            capability_name=capability.name,
            candidate_name=engineer_name,
            technical_overlap=self._band(score).value,
            demonstrated_capabilities=demonstrated[:MAX_STRENGTHS],
            assisted_capabilities=assisted[:MAX_STRENGTHS],
            missing_capabilities=missing[:MAX_GAPS],
        )

        supporting = [
            e.evidence_id for e in system_evidence if e.capability_id == capability.capability_id
        ]
        if not supporting:
            supporting = [
                e.evidence_id
                for e in system_evidence
                if e.capability_id in capabilities
                and capabilities[e.capability_id].component_id == capability.component_id
            ][:4]

        confidence = (
            EvidenceConfidence(target_row.evidence_confidence)
            if target_row is not None
            else EvidenceConfidence.LOW
        )

        return (
            BackupCandidate(
                engineer_id=engineer_id,
                name=engineer_name,
                technical_overlap=self._band(score),
                # Filled by `_narrate` for the candidates that are actually returned.
                strengths=[],
                gaps=[],
                evidence_confidence=confidence,
                supporting_evidence_ids=supporting,
            ),
            narrative_context,
        )

    def _narrate(
        self, candidate: BackupCandidate, context: CandidateNarrativeContext
    ) -> BackupCandidate:
        """Ask the provider for this candidate's strengths and gaps.

        The one place a provider is called on this path, and it is called once per returned
        candidate. Whatever the provider is, the facts it narrates were decided above by the
        rules; a provider that fails or wanders returns the deterministic template instead, so
        the structured half of the candidate is unaffected either way.
        """
        narrative = self.provider.explain_candidate(context)
        return candidate.model_copy(
            update={
                "strengths": narrative.strengths[:MAX_STRENGTHS],
                "gaps": narrative.gaps[:MAX_GAPS],
            }
        )

    @staticmethod
    def _band(score: int) -> TechnicalOverlap:
        if score >= HIGH_THRESHOLD:
            return TechnicalOverlap.HIGH
        if score >= MEDIUM_THRESHOLD:
            return TechnicalOverlap.MEDIUM
        return TechnicalOverlap.LOW
