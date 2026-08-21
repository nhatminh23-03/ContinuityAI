"""Regression test for the post-commit enum bug in mitigation-plan generation.

`MitigationPlanService.create` used to write `task.task_type` (a plain `str` from the provider)
straight into the ORM row and commit, coercing it into `MitigationTaskType` only in `_to_response`
afterwards. `DeterministicProvider` never emits an invalid value, so the bug was latent — but a
language-model provider can, and when it does the row was persisted, then every subsequent read
(including the same POST's own response) raised a bare `ValueError`: an unhandled 500 with no
error envelope, and a plan permanently unreadable. Task 1 of
.superpowers/sdd/superpowers-brainstorming-continuityai-merry-heron/task-1-brief.md.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.ai.schemas import PlanContext, PlanDraft, PlanTaskDraft
from app.core.errors import MitigationGenerationError
from app.mitigation import MitigationPlanService
from app.models import MitigationPlan
from app.schemas.mitigation import MitigationPlanRequest

CAPABILITY = "cap_incident_recovery"
ALEX = "eng_alex_chen"
MARIA = "eng_maria_gomez"


class _InvalidTaskTypeProvider:
    """Stands in for a language-model provider that emits a task type outside the enum."""

    name = "stub-invalid-task-type"

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft:
        return PlanDraft(
            target_readiness=context.target_readiness,
            tasks=[
                PlanTaskDraft(
                    title=f"Review the recovery runbook {i}",
                    description="Walk through the incident recovery runbook end to end.",
                    task_type="URGENT_REPLACEMENT",  # not a MitigationTaskType member
                    acceptance_criteria=["Can narrate each step unaided."],
                )
                for i in range(3)
            ],
        )


def _plan_count(session) -> int:
    return int(session.scalar(select(func.count(MitigationPlan.plan_id))) or 0)


def test_an_invalid_provider_task_type_raises_cleanly_and_persists_nothing(session) -> None:
    before = _plan_count(session)

    service = MitigationPlanService(session, provider=_InvalidTaskTypeProvider())
    request = MitigationPlanRequest(
        capability_id=CAPABILITY,
        primary_engineer_id=ALEX,
        selected_backup_engineer_id=MARIA,
    )

    with pytest.raises(MitigationGenerationError):
        service.create(request)

    assert _plan_count(session) == before, "a failed generation must not leave an orphan row"
