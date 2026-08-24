"""The wall-clock budget on narrative generation. OPEN-11.

These are the tests for the fix rather than for the symptom, so they use a deliberately slow stub
provider instead of a real model. The symptom was measured live: three sequential narrative calls
reached 16.91s against AC-14's 12-second allowance for an AI explanation operation. What has to hold
afterwards is narrow and testable — the calls run together, the deadline is real, and a narrative
that misses it is answered from the deterministic template rather than dropped or errored.

`test_the_candidates_endpoint_stays_inside_the_budget_with_a_slow_provider` is the one that would
have caught OPEN-11. Everything above it pins a piece of the mechanism.
"""

from __future__ import annotations

import time

import pytest

from app.ai.budget import narrate_in_parallel

DEADLINE = 1.0


def test_every_narrative_that_finishes_in_time_is_the_model_answer() -> None:
    results = narrate_in_parallel(
        ["a", "b", "c"],
        narrate=lambda item: f"model:{item}",
        fallback=lambda item: f"template:{item}",
        deadline_seconds=DEADLINE,
        max_workers=3,
    )
    assert results == ["model:a", "model:b", "model:c"]


def test_results_keep_the_order_of_the_items_not_the_order_they_finish() -> None:
    """Candidates are returned ranked, so an order that depends on completion would reorder them.

    The first item is made the slowest so that finishing order is the reverse of input order.
    """

    def narrate(item: str) -> str:
        time.sleep({"a": 0.15, "b": 0.05, "c": 0.0}[item])
        return f"model:{item}"

    results = narrate_in_parallel(
        ["a", "b", "c"],
        narrate=narrate,
        fallback=lambda item: f"template:{item}",
        deadline_seconds=DEADLINE,
        max_workers=3,
    )
    assert results == ["model:a", "model:b", "model:c"]


def test_one_failure_falls_back_without_affecting_the_others() -> None:
    def narrate(item: str) -> str:
        if item == "b":
            raise RuntimeError("gateway said no")
        return f"model:{item}"

    results = narrate_in_parallel(
        ["a", "b", "c"],
        narrate=narrate,
        fallback=lambda item: f"template:{item}",
        deadline_seconds=DEADLINE,
        max_workers=3,
    )
    assert results == ["model:a", "template:b", "model:c"]


def test_a_narrative_that_misses_the_deadline_is_answered_from_the_template() -> None:
    """The whole point. A slow narrative must not become a slow endpoint."""

    def narrate(item: str) -> str:
        if item == "slow":
            time.sleep(5)
        return f"model:{item}"

    started = time.monotonic()
    results = narrate_in_parallel(
        ["quick", "slow"],
        narrate=narrate,
        fallback=lambda item: f"template:{item}",
        deadline_seconds=0.3,
        max_workers=2,
    )
    elapsed = time.monotonic() - started

    assert results == ["model:quick", "template:slow"]
    # Returned on the deadline, not after the sleep. Generous upper bound so a loaded machine does
    # not fail the build, but far below the 5 seconds the slow narrative actually takes.
    assert elapsed < 2.0, f"took {elapsed:.2f}s, so the deadline is not being enforced"


def test_the_calls_run_together_rather_than_one_after_another() -> None:
    """Three 0.3s calls must cost about 0.3s, not 0.9s.

    This is the difference between 16.91s and something inside the budget, so it is asserted
    directly rather than inferred from the deadline test above.
    """

    def narrate(item: str) -> str:
        time.sleep(0.3)
        return f"model:{item}"

    started = time.monotonic()
    results = narrate_in_parallel(
        ["a", "b", "c"],
        narrate=narrate,
        fallback=lambda item: f"template:{item}",
        deadline_seconds=5.0,
        max_workers=3,
    )
    elapsed = time.monotonic() - started

    assert results == ["model:a", "model:b", "model:c"]
    assert elapsed < 0.75, f"took {elapsed:.2f}s, which is closer to sequential than to parallel"


def test_a_zero_deadline_skips_the_model_entirely() -> None:
    """Turning the budget down to nothing must not call the provider at all.

    This is the escape hatch for a demo on a bad connection: templates only, no waiting.
    """
    called: list[str] = []

    def narrate(item: str) -> str:
        called.append(item)
        return f"model:{item}"

    results = narrate_in_parallel(
        ["a", "b"],
        narrate=narrate,
        fallback=lambda item: f"template:{item}",
        deadline_seconds=0,
        max_workers=3,
    )
    assert results == ["template:a", "template:b"]
    assert called == []


def test_no_items_needs_no_provider_call() -> None:
    results = narrate_in_parallel(
        [],
        narrate=lambda item: pytest.fail("should not be called"),
        fallback=lambda item: pytest.fail("should not be called"),
        deadline_seconds=DEADLINE,
        max_workers=3,
    )
    assert results == []


def test_a_single_item_skips_the_thread_pool_but_still_falls_back() -> None:
    """One narrative is the common case for the plan and the simulation sentence.

    It takes the direct path — no thread hop — so the fallback has to be wired on that path too.
    """

    def narrate(item: str) -> str:
        raise RuntimeError("no")

    results = narrate_in_parallel(
        ["only"],
        narrate=narrate,
        fallback=lambda item: f"template:{item}",
        deadline_seconds=DEADLINE,
        max_workers=3,
    )
    assert results == ["template:only"]


# ---------------------------------------------------------------------------------------
# The regression test for OPEN-11 itself, through the endpoint
# ---------------------------------------------------------------------------------------


def test_the_candidates_endpoint_stays_inside_the_budget_with_a_slow_provider(
    client, monkeypatch
) -> None:
    """A provider that takes 4s per narrative must not produce a 12s response.

    Sequentially this would be about 8-12 seconds for the two candidates the seeded dataset
    returns, which is the shape of the breach that was measured. In parallel under the deadline it
    is one call's worth, and anything overdue arrives as the deterministic template.

    The structured half of each candidate — readiness, overlap band, evidence ids — comes from the
    rules and must be present and correct either way, which is what makes the fallback acceptable
    rather than a loss.
    """
    from app.ai.deterministic import DeterministicProvider
    from app.recommendation import service as recommendation_service

    class SlowProvider(DeterministicProvider):
        name = "slow-test-double"

        def explain_candidate(self, context):
            time.sleep(4.0)
            return super().explain_candidate(context)

    monkeypatch.setattr(recommendation_service, "get_provider", lambda name=None: SlowProvider())
    monkeypatch.setattr(recommendation_service.settings, "narrative_deadline_seconds", 1.0)

    started = time.monotonic()
    response = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": "cap_incident_recovery", "limit": 3},
    )
    elapsed = time.monotonic() - started

    assert response.status_code == 200
    body = response.json()
    assert body["candidates"], "the slow provider must not cost us the candidates themselves"
    for candidate in body["candidates"]:
        # Narrated one way or the other; never empty, never absent.
        assert candidate["strengths"]
        assert candidate["technical_overlap"] in {"HIGH", "MEDIUM", "LOW"}

    assert elapsed < 8.0, (
        f"the endpoint took {elapsed:.1f}s with a 1s narrative budget, so the budget is not "
        "bounding the response"
    )
    # Bounded from below as well, otherwise this test would also pass if the monkeypatch silently
    # missed and the fast deterministic provider answered instead — which would make the upper
    # bound meaningless.
    assert elapsed >= 1.0, (
        f"the endpoint answered in {elapsed:.2f}s, faster than the 1s budget and the 4s narratives "
        "allow. The slow provider was probably not installed, so this test proves nothing."
    )
