"""How often the recommendation service asks a provider to write prose.

The candidate DTO is assembled for every *eligible* engineer, because the score decides who
survives, but the narrative is prose over facts the rules already decided and is only ever read
for the candidates that come back. Generating it inside the scoring loop meant a model-backed
provider was paid for candidates that were then discarded — and, worse, made the call count a
function of how many engineers happened to qualify, which is bounded by nothing. AC-14 gives an
AI explanation operation 12 seconds, and a per-call timeout can only be sized against a bound
that exists.

These tests hold that bound in place, and hold the payload steady against the shared contract
fixture so the deferral cannot change what a candidate says.
"""

from __future__ import annotations

from app.ai.deterministic import DeterministicProvider
from app.ai.schemas import CandidateNarrative, CandidateNarrativeContext
from app.recommendation.service import BackupCandidateService
from app.repositories import CapabilityRepository
from app.schemas.recommendation import BackupCandidateRequest

from .conftest import load_fixture

MAX_LIMIT = next(
    c.le for c in BackupCandidateRequest.model_fields["limit"].metadata if hasattr(c, "le")
)


class CountingProvider:
    """The deterministic provider, counting narrative calls.

    A wrapper rather than a mock: every answer is the real deterministic one, so a test that
    compares output against the contract fixture is comparing the shipped behaviour.
    """

    name = "counting"

    def __init__(self) -> None:
        self._rules = DeterministicProvider()
        self.calls: list[str] = []

    def extract_artifact_semantics(self, artifact, context):
        return self._rules.extract_artifact_semantics(artifact, context)

    def summarize_simulation(self, context):
        return self._rules.summarize_simulation(context)

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative:
        self.calls.append(context.candidate_name)
        return self._rules.explain_candidate(context)

    def generate_mitigation_plan(self, context):
        return self._rules.generate_mitigation_plan(context)


def test_a_narrative_is_written_only_for_the_candidates_that_are_returned(session) -> None:
    """Measured across every capability in the seeded dataset, not just the demo one.

    `cap_retry_logic` is the case that used to exceed the budget: four engineers are eligible,
    three are returned, and the fourth was being narrated and then thrown away.
    """
    provider = CountingProvider()
    service = BackupCandidateService(session, provider=provider)

    worst = 0
    for capability in CapabilityRepository(session).list_all():
        before = len(provider.calls)
        response = service.compare(
            BackupCandidateRequest(capability_id=capability.capability_id, limit=MAX_LIMIT)
        )
        calls = len(provider.calls) - before

        assert calls == len(response.candidates), (
            f"{capability.capability_id}: {calls} narratives written for "
            f"{len(response.candidates)} candidates returned"
        )
        assert [c.name for c in response.candidates] == provider.calls[before:]
        worst = max(worst, calls)

    assert worst <= MAX_LIMIT, f"{worst} sequential provider calls; the contract caps them at {MAX_LIMIT}"


def test_a_smaller_limit_buys_fewer_calls(session) -> None:
    """The bound is the requested limit, not a constant, so a manager asking for one candidate
    pays for one narrative."""
    provider = CountingProvider()
    service = BackupCandidateService(session, provider=provider)

    response = service.compare(
        BackupCandidateRequest(capability_id="cap_incident_recovery", limit=1)
    )
    assert len(response.candidates) == 1
    assert len(provider.calls) == 1


def test_the_returned_candidates_still_match_the_contract_fixture(client) -> None:
    """Deferring narration must change nothing a caller can see. Jointly owned fixture, CI-14."""
    expected = load_fixture("backup-candidates")
    body = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": expected["capability"]["capability_id"], "limit": MAX_LIMIT},
    ).json()

    assert body["capability"] == expected["capability"]
    assert body["disclaimer"] == expected["disclaimer"]
    assert body["candidates"] == expected["candidates"]


# ---------------------------------------------------------------------------------------
# The primary is never offered as its own backup
# ---------------------------------------------------------------------------------------


def test_no_capability_offers_its_own_primary_engineer_as_a_backup(client, session) -> None:
    """Found in the browser, on the plan screen, as `VALIDATION_ERROR`.

    `CapabilityDetail.primary_engineer` is `facts.primary`, documented as the strongest coverage
    "adequate or not", and it is what the frontend sends as the plan's knowledge source. The
    exclusion here was guarded by `is_adequate`, so on any capability whose strongest holder was
    below PRACTICED that person came back as a candidate to back up themselves — and
    `MitigationPlanService` rejects a plan whose source and backup are the same person.

    The guard failed exactly where it mattered: no adequate holder means a critical gap, which is
    when a manager actually goes looking for a backup. `cap_refund_reversal` was the live case,
    with Priya Nair at ASSISTED.

    Swept across every capability rather than pinned to that one, because the bug was a general
    rule with a specific symptom, and the next dataset will put a different capability in that state.
    """
    capability_ids = [c.capability_id for c in CapabilityRepository(session).list_all()]
    assert capability_ids, "no capabilities seeded, so this test proves nothing"

    offenders = []
    for capability_id in capability_ids:
        detail = client.get(f"/api/v1/capabilities/{capability_id}").json()
        primary = (detail.get("primary_engineer") or {}).get("engineer_id")
        if not primary:
            continue
        candidates = client.post(
            "/api/v1/recommendations/backup-candidates",
            json={"capability_id": capability_id, "limit": 3},
        ).json()
        offered = [c["engineer_id"] for c in candidates.get("candidates", [])]
        if primary in offered:
            offenders.append((capability_id, primary))

    assert not offenders, f"primary offered as its own backup: {offenders}"


def test_every_candidate_the_api_offers_can_actually_produce_a_plan(client, session) -> None:
    """The invariant behind the bug above, stated as the user experiences it.

    A candidate that cannot be turned into a plan is a dead end the interface has no way to predict,
    so it renders a button and the button fails. Walking the two calls in the order the UI walks them
    is the only way this class of mismatch shows up — each endpoint is individually correct.
    """
    capability_ids = [c.capability_id for c in CapabilityRepository(session).list_all()]
    failures = []
    for capability_id in capability_ids:
        detail = client.get(f"/api/v1/capabilities/{capability_id}").json()
        primary = (detail.get("primary_engineer") or {}).get("engineer_id")
        if not primary:
            continue
        candidates = client.post(
            "/api/v1/recommendations/backup-candidates",
            json={"capability_id": capability_id, "limit": 3},
        ).json()
        for candidate in candidates.get("candidates", []):
            response = client.post(
                "/api/v1/mitigation-plans",
                json={
                    "capability_id": capability_id,
                    "primary_engineer_id": primary,
                    "selected_backup_engineer_id": candidate["engineer_id"],
                },
            )
            if response.status_code not in (200, 201):
                failures.append(
                    (
                        capability_id,
                        candidate["engineer_id"],
                        response.status_code,
                        response.json().get("error", {}).get("code"),
                    )
                )

    assert not failures, f"candidates the API offers but refuses to plan for: {failures}"
