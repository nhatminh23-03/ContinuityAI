"""Compare what the application inferred against the hidden ground truth. PRD section 25.

Six checks, matching the metric table in PRD section 25.2:

    1. knowledge reconstruction    did readiness come back to the true label?
    2. exposure classification     did the continuity rules reach the expected state?
    3. critical gap detection      found the real single-expert dependencies, and no false ones?
    4. counterfactual simulation   did removing the engineer produce the expected coverage change?
    5. backup candidates           did the expected engineers surface, at the expected overlap?
    6. evidence grounding          does every coverage claim have a source behind it?

Read the reporting policy in PRD section 25.3 before quoting any of these numbers. This is a
controlled prototype validation against a synthetic organisation, and the generator emits evidence
patterns chosen to be classifiable. What it measures is whether the pipeline is self-consistent end
to end — ingestion, extraction, aggregation, readiness, exposure, risk. It is **not** evidence that
the readiness heuristics match real human expertise, and it must never be quoted as accuracy.
RECOMMENDATIONS.md R-02.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.evaluation.ground_truth import GroundTruth
from app.evidence.strength import readiness_rank
from app.models import Coverage
from app.repositories import CapabilityRepository, SystemRepository
from app.schemas.enums import ReadinessLevel, SimulationScopeType, SimulationType
from app.schemas.recommendation import BackupCandidateRequest
from app.schemas.simulation import SimulationRequest, SimulationScopeRequest


@dataclass
class CheckResult:
    name: str
    passed: int = 0
    total: int = 0
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def rate(self) -> float:
        return (self.passed / self.total) if self.total else 0.0

    @property
    def ok(self) -> bool:
        return self.total > 0 and self.passed == self.total


@dataclass
class EvaluationReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(check.ok for check in self.checks)


def evaluate(session: Session, truth: GroundTruth) -> EvaluationReport:
    return EvaluationReport(
        checks=[
            _reconstruction(session, truth),
            _exposure(session, truth),
            _critical_gaps(session, truth),
            _declared_owner_mismatch(session, truth),
            _simulation(session, truth),
            _candidates(session, truth),
            _grounding(session),
            _adversarial(session, truth),
        ]
    )


def _reconstruction(session: Session, truth: GroundTruth) -> CheckResult:
    """Exact readiness match, with near-misses reported separately.

    A one-bucket miss (PRACTICED read as VALIDATED) and a three-bucket miss (EXPOSED read as
    VALIDATED) are different failures: the first is threshold calibration, the second means the
    evidence was misinterpreted. Collapsing them into one percentage would hide that.
    """
    result = CheckResult("Knowledge reconstruction (engineer-capability readiness)")
    inferred = {
        (row.engineer_id, row.capability_id): row.readiness
        for row in session.query(Coverage).all()
    }
    adjacent = 0

    for (engineer_id, capability_id), expected in sorted(truth.by_pair.items()):
        result.total += 1
        actual = inferred.get((engineer_id, capability_id), ReadinessLevel.NONE.value)
        if actual == expected:
            result.passed += 1
            continue
        distance = abs(readiness_rank(actual) - readiness_rank(expected))
        if distance == 1:
            adjacent += 1
        result.failures.append(
            f"{engineer_id} / {capability_id}: expected {expected}, inferred {actual} "
            f"({distance} bucket{'s' if distance != 1 else ''} out)"
        )

    if adjacent:
        result.notes.append(f"{adjacent} of {len(result.failures)} miss(es) are within one bucket")
    return result


def _exposure(session: Session, truth: GroundTruth) -> CheckResult:
    result = CheckResult("Capability exposure classification")
    capabilities = CapabilityRepository(session)
    for capability_id, expected in sorted(truth.expected_capability_exposure.items()):
        result.total += 1
        assessment = capabilities.assessment(capability_id)
        actual = assessment.exposure if assessment else "MISSING"
        if actual == expected:
            result.passed += 1
        else:
            result.failures.append(f"{capability_id}: expected {expected}, got {actual}")
    return result


def _critical_gaps(session: Session, truth: GroundTruth) -> CheckResult:
    """Both directions matter. Missing a real gap is dangerous; inventing one destroys trust."""
    result = CheckResult("Critical gap detection (no misses, no false positives)")
    capabilities = CapabilityRepository(session)
    detected = {
        capability.capability_id
        for capability in capabilities.list_all()
        if (assessment := capabilities.assessment(capability.capability_id))
        and assessment.exposure == "CRITICAL_GAP"
    }
    expected = truth.expected_critical_gaps

    result.total = len(expected | detected)
    result.passed = len(expected & detected)
    for capability_id in sorted(expected - detected):
        result.failures.append(f"{capability_id}: real gap not detected")
    for capability_id in sorted(detected - expected):
        result.failures.append(f"{capability_id}: gap reported but not expected")
    if not result.total:
        result.total = 1
        result.passed = 1
        result.notes.append("no critical gaps expected or detected")
    return result


def _declared_owner_mismatch(session: Session, truth: GroundTruth) -> CheckResult:
    result = CheckResult("Declared-versus-demonstrated ownership mismatch")
    systems = SystemRepository(session)
    detected = {
        system.system_id
        for system in systems.list_all()
        if (assessment := systems.assessment(system.system_id)) and assessment.declared_owner_mismatch
    }
    expected = set(truth.expected_declared_owner_mismatch)

    result.total = len(expected | detected) or 1
    result.passed = len(expected & detected) or (1 if not (expected | detected) else 0)
    for system_id in sorted(expected - detected):
        result.failures.append(f"{system_id}: expected a mismatch, none reported")
    for system_id in sorted(detected - expected):
        result.failures.append(f"{system_id}: mismatch reported but not expected")
    return result


def _simulation(session: Session, truth: GroundTruth) -> CheckResult:
    result = CheckResult("Counterfactual simulation")
    expectation = truth.expected_simulation
    if not expectation:
        result.notes.append("no simulation expectation defined")
        result.total = result.passed = 1
        return result

    from app.simulation import SimulationService

    response = SimulationService(session).run(
        SimulationRequest(
            simulation_type=SimulationType(expectation["simulation_type"]),
            engineer_id=expectation["engineer_id"],
            scope=SimulationScopeRequest(
                type=SimulationScopeType(expectation["scope_type"]), id=expectation["scope_id"]
            ),
        )
    )

    for side in ("before", "after"):
        expected_state = expectation.get(side, {})
        actual_state = getattr(response, side)
        for key, expected_value in expected_state.items():
            result.total += 1
            actual_value = getattr(actual_state, key)
            actual_value = getattr(actual_value, "value", actual_value)
            if actual_value == expected_value:
                result.passed += 1
            else:
                result.failures.append(
                    f"{side}.{key}: expected {expected_value}, got {actual_value}"
                )

    impacts = {impact.capability_id: impact for impact in response.capability_impacts}
    for capability_id, expected_impact in sorted(expectation.get("impacts", {}).items()):
        for key, expected_value in expected_impact.items():
            result.total += 1
            impact = impacts.get(capability_id)
            if impact is None:
                result.failures.append(f"{capability_id}: not reported in capability_impacts")
                continue
            actual_value = getattr(getattr(impact, key), "value", getattr(impact, key))
            if actual_value == expected_value:
                result.passed += 1
            else:
                result.failures.append(
                    f"{capability_id}.{key}: expected {expected_value}, got {actual_value}"
                )
    return result


def _candidates(session: Session, truth: GroundTruth) -> CheckResult:
    result = CheckResult("Backup candidate recommendation")
    from app.recommendation import BackupCandidateService

    service = BackupCandidateService(session)
    for capability_id, expected_list in sorted(truth.expected_backup_candidates.items()):
        response = service.compare(
            BackupCandidateRequest(capability_id=capability_id, limit=3)
        )
        actual = {c.engineer_id: c.technical_overlap.value for c in response.candidates}
        for expected in expected_list:
            result.total += 1
            engineer_id = expected["engineer_id"]
            if engineer_id not in actual:
                result.failures.append(f"{capability_id}: {engineer_id} was not returned")
                continue
            if actual[engineer_id] != expected["technical_overlap"]:
                result.failures.append(
                    f"{capability_id}/{engineer_id}: expected overlap "
                    f"{expected['technical_overlap']}, got {actual[engineer_id]}"
                )
                continue
            result.passed += 1

        expected_ids = {e["engineer_id"] for e in expected_list}
        unexpected = set(actual) - expected_ids
        if unexpected:
            result.notes.append(
                f"{capability_id}: additional candidates returned: {sorted(unexpected)}"
            )
    return result


def _grounding(session: Session) -> CheckResult:
    """FR-024 and AC-04: no coverage claim without a source behind it.

    This is the check the product cannot afford to fail. A single ungrounded readiness value would
    put an unsupported claim about a named person on screen.
    """
    result = CheckResult("Evidence grounding (every coverage claim cites a source)")
    for row in session.query(Coverage).all():
        result.total += 1
        if row.supporting_evidence_ids:
            result.passed += 1
        else:
            result.failures.append(
                f"{row.engineer_id} / {row.capability_id}: readiness {row.readiness} with no "
                f"supporting evidence"
            )
    if not result.total:
        result.total = 1
        result.notes.append("no coverage rows found")
    return result


def _adversarial(session: Session, truth: GroundTruth) -> CheckResult:
    """Did the rules decline the artifacts written to fool them? RECOMMENDATIONS.md R-02.

    The other seven checks measure whether the pipeline reconstructs labels from evidence designed to
    be classifiable. The fair objection is that a perfect score there might only show the pipeline
    agreeing with its own generator. This check exists to answer that objection with a different kind
    of evidence: a corpus that contains deliberate traps, and a requirement that each one is refused.

    **Declining a trap is a stronger claim than reconstructing a label**, because each trap is a
    specific way a plausible implementation gets this wrong — counting activity as capability, reading
    attribution out of prose instead of the participant record, treating a claim of seniority as a
    record of execution. A system can score 100% on cooperative data and still fail every one.

    Two constraint shapes, both expressed in the hidden ground truth so the traps in
    `data/synthetic/` do not carry their own answers:

    * `ceiling` — this pair must not read *above* the stated readiness. Stated as a ceiling rather
      than an equality because the trap can only do damage by promoting; a level below the ceiling
      would be a different bug and is caught by the reconstruction check.
    * `no_coverage` — this pair must have no coverage row at all. Used where being fooled would
      invent a capability for someone with no relationship to it.

    A trap whose artifact is missing from the corpus fails rather than passes. Otherwise the check
    would quietly go green the moment someone regenerated the corpus without the traps in it, which
    is exactly the blind spot R-26 was about.
    """
    result = CheckResult("Adversarial artifacts declined (traps the rules must refuse)")
    if not truth.adversarial_artifacts:
        result.total = result.passed = 1
        result.notes.append("no adversarial artifacts defined")
        return result

    from app.models import Artifact

    references = {row.source_reference for row in session.query(Artifact).all()}
    coverage = {
        (row.engineer_id, row.capability_id): row.readiness
        for row in session.query(Coverage).all()
    }
    declined_traps: set[str] = set()

    for entry in truth.adversarial_artifacts:
        reference = entry["reference"]
        trap = entry.get("trap", "unspecified")

        result.total += 1
        if reference not in references:
            result.failures.append(
                f"{reference}: the trap is not in the corpus, so nothing was tested. Regenerate "
                f"with backend/scripts/generate_synthetic_data.py."
            )
            continue

        breaches: list[str] = []

        ceiling = entry.get("ceiling")
        if ceiling:
            pair = (ceiling["engineer_id"], ceiling["capability_id"])
            actual = coverage.get(pair, ReadinessLevel.NONE.value)
            if readiness_rank(actual) > readiness_rank(ceiling["readiness"]):
                breaches.append(
                    f"{pair[0]} / {pair[1]} rose to {actual}, above the {ceiling['readiness']} "
                    f"ceiling — the trap worked"
                )

        no_coverage = entry.get("no_coverage")
        if no_coverage:
            pair = (no_coverage["engineer_id"], no_coverage["capability_id"])
            if pair in coverage:
                breaches.append(
                    f"{pair[0]} gained {coverage[pair]} on {pair[1]} from prose alone — attribution "
                    f"followed the narrative instead of the participant record"
                )

        if breaches:
            result.failures.extend(f"{reference} ({trap}): {b}" for b in breaches)
        else:
            result.passed += 1
            declined_traps.add(trap)

    if declined_traps:
        result.notes.append(f"traps declined: {', '.join(sorted(declined_traps))}")
    return result
