"""Knowledge-transfer plan generation and approval. PRD section 20, API contract 8.9 and 8.10.

Turns an exposed capability plus a manager-chosen candidate into specific, reviewable work. The
guardrail from docs/ARCHITECTURE.md section 38 is that the plan targets the *missing capability*,
not the whole person: "teach Maria everything Alex knows" is the failure mode, and it is what a
naive prompt produces.

Two properties the contract insists on and this service enforces:

* **A plan changes nothing.** Generating or approving a plan does not touch readiness, coverage,
  or continuity risk. Nobody becomes more capable because work was scheduled. Readiness moves only
  when qualifying evidence appears.
* **Approval is human.** `DRAFT -> APPROVED` happens on an explicit request carrying who approved
  it. There is no autonomous path to `APPROVED`.

Editing rides on the approval request as an optional complete task array (decision CI-12), which
preserves edit-before-approve without an eleventh endpoint or plan-mutation semantics.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, get_provider
from app.ai.schemas import PlanContext
from app.core.errors import MitigationGenerationError, NotFoundError, ValidationError
from app.evidence.strength import is_adequate
from app.models import MitigationPlan, MitigationTask
from app.repositories import (
    CapabilityRepository,
    CoverageRepository,
    EngineerRepository,
    EvidenceRepository,
    MitigationPlanRepository,
    SystemRepository,
)
from app.schemas.capability import CapabilityRef
from app.schemas.enums import (
    EvidenceRole,
    MitigationPlanStatus,
    MitigationTaskType,
    OperationalCriticality,
    ReadinessLevel,
)
from app.schemas.mitigation import (
    ApprovePlanRequest,
    ApprovePlanResponse,
    EngineerRef,
    MitigationPlanRequest,
    MitigationPlanResponse,
)
from app.schemas.mitigation import MitigationTask as MitigationTaskDTO

# AC-10 requires 3 to 5 actions. A generator that returns 2 or 9 has misunderstood the job, and
# silently trimming would hide that.
MIN_TASKS = 3
MAX_TASKS = 5
MAX_REFERENCE_EVIDENCE = 2


class MitigationPlanService:
    def __init__(self, session: Session, provider: AIProvider | None = None) -> None:
        self.session = session
        self.provider = provider or get_provider()

    def create(self, request: MitigationPlanRequest) -> MitigationPlanResponse:
        capabilities = CapabilityRepository(self.session)
        capability = capabilities.get(request.capability_id)
        if capability is None:
            raise NotFoundError(
                f"Capability '{request.capability_id}' not found.",
                {"capability_id": request.capability_id},
            )

        engineers = EngineerRepository(self.session)
        source = engineers.get(request.primary_engineer_id)
        candidate = engineers.get(request.selected_backup_engineer_id)
        for engineer_id, engineer in (
            (request.primary_engineer_id, source),
            (request.selected_backup_engineer_id, candidate),
        ):
            if engineer is None:
                raise NotFoundError(
                    f"Engineer '{engineer_id}' not found.", {"engineer_id": engineer_id}
                )
        if source.engineer_id == candidate.engineer_id:
            raise ValidationError(
                "The source engineer and the selected backup cannot be the same person.",
                {"engineer_id": source.engineer_id},
            )

        system = SystemRepository(self.session).get(capability.system_id)
        component = next(
            (c for c in SystemRepository(self.session).components(capability.system_id)
             if c.component_id == capability.component_id),
            None,
        )

        coverage_repository = CoverageRepository(self.session)
        candidate_coverage = coverage_repository.get(candidate.engineer_id, capability.capability_id)
        candidate_readiness = (
            ReadinessLevel(candidate_coverage.readiness)
            if candidate_coverage is not None
            else ReadinessLevel.NONE
        )

        missing = self._missing_capabilities(candidate.engineer_id, capability, capabilities)
        reference_evidence = self._reference_evidence(source.engineer_id, capability.capability_id)
        target_readiness = self._target_readiness(capability, candidate_readiness)

        draft = self.provider.generate_mitigation_plan(
            PlanContext(
                capability_name=capability.name,
                system_name=system.name if system else capability.system_id,
                component_name=component.name if component else capability.component_id,
                source_engineer_name=source.name,
                candidate_name=candidate.name,
                candidate_readiness=candidate_readiness.value,
                target_readiness=target_readiness.value,
                missing_capabilities=missing,
                reference_evidence=reference_evidence,
            )
        )

        if not MIN_TASKS <= len(draft.tasks) <= MAX_TASKS:
            raise MitigationGenerationError(
                f"Plan generation produced {len(draft.tasks)} actions; between {MIN_TASKS} and "
                f"{MAX_TASKS} are required.",
                {"capability_id": capability.capability_id, "task_count": len(draft.tasks)},
            )

        repository = MitigationPlanRepository(self.session)
        plan_id = repository.next_id()
        plan = MitigationPlan(
            plan_id=plan_id,
            capability_id=capability.capability_id,
            system_id=capability.system_id,
            source_engineer_id=source.engineer_id,
            selected_backup_engineer_id=candidate.engineer_id,
            simulation_id=request.simulation_id,
            status=MitigationPlanStatus.DRAFT.value,
            target_readiness=target_readiness.value,
            created_at=datetime.now(timezone.utc),
        )
        for index, task in enumerate(draft.tasks, start=1):
            # `task.task_type` is a plain str from the provider, not yet validated against the
            # enum. Coercing it here, before the plan is added to the session, is what keeps an
            # invalid value from ever being committed — `_to_response` doing the coercion later
            # was the bug: by then the row was already persisted and permanently unreadable.
            try:
                task_type = MitigationTaskType(task.task_type)
            except ValueError as exc:
                raise MitigationGenerationError(
                    f"Plan generation produced an invalid task type '{task.task_type}'.",
                    {"capability_id": capability.capability_id, "task_type": task.task_type},
                ) from exc
            plan.tasks.append(
                MitigationTask(
                    task_id=f"task_{index:03d}",
                    plan_id=plan_id,
                    title=task.title,
                    description=task.description,
                    type=task_type.value,
                    sequence=index,
                    acceptance_criteria=task.acceptance_criteria,
                    linked_evidence_ids=task.linked_evidence_ids,
                )
            )
        repository.add(plan)
        self.session.commit()

        return self._to_response(plan, capability.name, source.name, candidate.name)

    def approve(self, plan_id: str, request: ApprovePlanRequest) -> ApprovePlanResponse:
        repository = MitigationPlanRepository(self.session)
        plan = repository.get(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan '{plan_id}' not found.", {"plan_id": plan_id})

        if plan.status != MitigationPlanStatus.DRAFT.value:
            raise ValidationError(
                "Only a DRAFT plan can be approved.",
                {"plan_id": plan_id, "status": plan.status},
            )

        if request.tasks is not None:
            # A complete replacement, not a patch (contract section 8.10). Editing is only
            # permitted while the plan is DRAFT, which the status check above already guarantees.
            if not MIN_TASKS <= len(request.tasks) <= MAX_TASKS:
                raise ValidationError(
                    f"An edited plan must contain between {MIN_TASKS} and {MAX_TASKS} actions.",
                    {"plan_id": plan_id, "task_count": len(request.tasks)},
                )
            plan.tasks.clear()
            self.session.flush()
            for index, task in enumerate(request.tasks, start=1):
                plan.tasks.append(
                    MitigationTask(
                        task_id=task.task_id or f"task_{index:03d}",
                        plan_id=plan.plan_id,
                        title=task.title,
                        description=task.description,
                        type=task.type.value,
                        sequence=index,
                        acceptance_criteria=task.acceptance_criteria,
                        linked_evidence_ids=task.linked_evidence_ids,
                    )
                )

        plan.status = MitigationPlanStatus.APPROVED.value
        plan.approved_by = request.approved_by
        plan.approved_at = datetime.now(timezone.utc)
        self.session.commit()

        return ApprovePlanResponse(
            plan_id=plan.plan_id,
            status=MitigationPlanStatus.APPROVED,
            approved_by=plan.approved_by,
            approved_at=plan.approved_at,
        )

    def get(self, plan_id: str) -> MitigationPlanResponse:
        plan = MitigationPlanRepository(self.session).get(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan '{plan_id}' not found.", {"plan_id": plan_id})
        capability = CapabilityRepository(self.session).get(plan.capability_id)
        engineers = EngineerRepository(self.session).by_id()
        return self._to_response(
            plan,
            capability.name if capability else plan.capability_id,
            engineers[plan.source_engineer_id].name,
            engineers[plan.selected_backup_engineer_id].name,
        )

    # -- internals ----------------------------------------------------------------------

    def _missing_capabilities(
        self, candidate_id: str, capability, capabilities: CapabilityRepository
    ) -> list[str]:
        """The gap set: the target, plus anything in the same component they have not practised.

        Scoped to the component on purpose. Widening it to the whole system is how a focused
        transfer plan turns into "learn the entire service".
        """
        coverage = {
            row.capability_id: row
            for row in CoverageRepository(self.session).list_by_engineer(candidate_id)
        }
        missing: list[str] = []
        target_row = coverage.get(capability.capability_id)
        if target_row is None or not is_adequate(target_row.readiness):
            missing.append(capability.name)

        for sibling in capabilities.list_by_component(capability.component_id):
            if sibling.capability_id == capability.capability_id:
                continue
            row = coverage.get(sibling.capability_id)
            if row is None or not is_adequate(row.readiness):
                missing.append(sibling.name)
        return missing

    def _reference_evidence(self, source_engineer_id: str, capability_id: str) -> list[dict]:
        """The source engineer's strongest evidence, for the candidate to study.

        Independent executions first: those are the records that actually show the capability
        being exercised, which is what makes the review task concrete rather than a reading list.
        """
        records = EvidenceRepository(self.session).list_by_capability(
            capability_id, engineer_id=source_engineer_id
        )
        independent = [
            r for r in records if r.evidence_role == EvidenceRole.INDEPENDENT_EXECUTION.value
        ]
        chosen = (independent or records)[:MAX_REFERENCE_EVIDENCE]
        return [
            {"evidence_id": r.evidence_id, "source_reference": r.source_reference}
            for r in chosen
        ]

    @staticmethod
    def _target_readiness(capability, candidate_readiness: ReadinessLevel) -> ReadinessLevel:
        """A target, explicitly not an achievement.

        PRACTICED for someone who has not performed the capability unaided. Aiming a candidate who
        is already PRACTICED at VALIDATED only makes sense where repetition genuinely matters,
        which is on the critical capabilities.
        """
        if (
            candidate_readiness is ReadinessLevel.PRACTICED
            and capability.operational_criticality == OperationalCriticality.CRITICAL.value
        ):
            return ReadinessLevel.VALIDATED
        return ReadinessLevel.PRACTICED

    @staticmethod
    def _to_response(
        plan: MitigationPlan, capability_name: str, source_name: str, candidate_name: str
    ) -> MitigationPlanResponse:
        return MitigationPlanResponse(
            plan_id=plan.plan_id,
            status=MitigationPlanStatus(plan.status),
            capability=CapabilityRef(capability_id=plan.capability_id, name=capability_name),
            source_engineer=EngineerRef(engineer_id=plan.source_engineer_id, name=source_name),
            backup_candidate=EngineerRef(
                engineer_id=plan.selected_backup_engineer_id, name=candidate_name
            ),
            target_readiness=ReadinessLevel(plan.target_readiness),
            tasks=[
                MitigationTaskDTO(
                    task_id=task.task_id,
                    title=task.title,
                    description=task.description,
                    type=MitigationTaskType(task.type),
                    acceptance_criteria=task.acceptance_criteria,
                    linked_evidence_ids=task.linked_evidence_ids,
                )
                for task in sorted(plan.tasks, key=lambda t: t.sequence)
            ],
        )
