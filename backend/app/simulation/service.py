"""Counterfactual simulation. PRD section 18, API contract section 8.7.

The hero capability of the product, and the smallest piece of code in it. That is the point: the
simulation is not a second model, it is the same rules run over the same facts with one engineer's
demonstrated coverage excluded.

    baseline facts ── assess ──> before
         │
         └─ .without(engineer) ── assess ──> after

Two properties this shape guarantees for free:

* **Baseline state cannot be corrupted** (ARCHITECTURE.md quality bar E). `CapabilityFacts` is
  frozen and `.without()` returns a new object; nothing is written, nothing is deleted, and there
  is no snapshot to restore.
* **Before and after cannot disagree by construction.** A separate "simulate" implementation
  could drift from the baseline engine. There isn't one.

What it does *not* do: predict an outage. It identifies which capabilities would have no adequate
demonstrated coverage. The disclaimer wording lives in the frontend (decision CI-32) so it cannot
be forgotten by a backend code path.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, get_provider
from app.ai.schemas import SimulationSummaryContext
from app.continuity.aggregation import SystemAssessmentResult, aggregate_system
from app.continuity.exposure import CapabilityAssessmentResult, assess
from app.continuity.facts import SystemFacts
from app.core.errors import InsufficientEvidenceError, NotFoundError, ValidationError
from app.models import Simulation
from app.repositories import EngineerRepository, SimulationRepository, SystemRepository
from app.schemas.enums import CapabilityExposure, SimulationScopeType
from app.schemas.simulation import (
    CapabilityImpact,
    EngineerRef,
    SimulationRequest,
    SimulationResponse,
    SimulationScope,
    SimulationState,
)
from app.services.facts import build_system_facts


class SimulationService:
    def __init__(self, session: Session, provider: AIProvider | None = None) -> None:
        self.session = session
        self.provider = provider or get_provider()

    def run(self, request: SimulationRequest) -> SimulationResponse:
        engineer = EngineerRepository(self.session).get(request.engineer_id)
        if engineer is None:
            raise NotFoundError(
                f"Engineer '{request.engineer_id}' not found.", {"engineer_id": request.engineer_id}
            )

        if request.scope.type is not SimulationScopeType.SYSTEM:
            # The enum keeps PLATFORM because the contract froze it and it costs nothing
            # (decision CI-22), but multi-system rollup is unimplemented. Saying so is better
            # than quietly treating a platform id as a system id.
            raise ValidationError(
                "Only SYSTEM scope is implemented in the MVP.",
                {"scope_type": request.scope.type.value, "supported": ["SYSTEM"]},
            )

        system = SystemRepository(self.session).get(request.scope.id)
        if system is None:
            raise NotFoundError(
                f"System '{request.scope.id}' not found.", {"system_id": request.scope.id}
            )

        facts = build_system_facts(self.session, system.system_id)
        before_results, before_state = self._evaluate(facts)
        after_results, after_state = self._evaluate(facts.without(engineer.engineer_id))

        if before_state.continuity_risk_index is None:
            raise InsufficientEvidenceError(
                f"'{system.name}' has no assessable capability coverage, so a responsible "
                f"simulation cannot be produced.",
                {"system_id": system.system_id},
            )

        impacts = self._impacts(facts, engineer.engineer_id, before_results, after_results)

        repository = SimulationRepository(self.session)
        simulation_id = repository.next_id()
        response = SimulationResponse(
            simulation_id=simulation_id,
            simulation_type=request.simulation_type,
            engineer=EngineerRef(engineer_id=engineer.engineer_id, name=engineer.name),
            scope=SimulationScope(
                type=SimulationScopeType.SYSTEM, id=system.system_id, name=system.name
            ),
            before=self._state(before_state),
            after=self._state(after_state),
            capability_impacts=impacts,
            summary=self._summary(engineer.name, system.name, impacts, before_state, after_state),
        )

        repository.add(
            Simulation(
                simulation_id=simulation_id,
                simulation_type=request.simulation_type.value,
                engineer_id=engineer.engineer_id,
                scope_type=SimulationScopeType.SYSTEM.value,
                scope_id=system.system_id,
                created_at=datetime.utcnow(),
                result_json=response.model_dump(mode="json", exclude_unset=False),
            )
        )
        self.session.commit()
        return response

    # -- internals ----------------------------------------------------------------------

    @staticmethod
    def _evaluate(
        facts: SystemFacts,
    ) -> tuple[dict[str, CapabilityAssessmentResult], SystemAssessmentResult]:
        results = {c.capability_id: assess(c) for c in facts.capabilities}
        return results, aggregate_system(facts, results)

    @staticmethod
    def _state(aggregate: SystemAssessmentResult) -> SimulationState:
        return SimulationState(
            continuity_risk_index=aggregate.continuity_risk_index or 0,
            continuity_risk_class=aggregate.continuity_risk_class,
            critical_gap_count=aggregate.critical_gap_count,
            degraded_capability_count=aggregate.degraded_capability_count,
            covered_capability_count=aggregate.covered_capability_count,
        )

    @staticmethod
    def _impacts(
        facts: SystemFacts,
        engineer_id: str,
        before: dict[str, CapabilityAssessmentResult],
        after: dict[str, CapabilityAssessmentResult],
    ) -> list[CapabilityImpact]:
        """Report on every capability the engineer touches, plus anything that changed.

        Including unchanged capabilities is the point rather than noise: "Retry Logic stays
        covered" is what makes the result specific instead of "this person is important".
        """
        impacts: list[CapabilityImpact] = []
        for capability in facts.capabilities:
            before_result = before[capability.capability_id]
            after_result = after[capability.capability_id]
            changed = before_result.exposure is not after_result.exposure
            if not capability.covers(engineer_id) and not changed:
                continue
            impacts.append(
                CapabilityImpact(
                    capability_id=capability.capability_id,
                    name=capability.name,
                    operational_criticality=capability.operational_criticality,
                    before=before_result.exposure,
                    after=after_result.exposure,
                    remaining_best_readiness=after_result.best_readiness,
                )
            )
        return impacts

    def _summary(
        self,
        engineer_name: str,
        scope_name: str,
        impacts: list[CapabilityImpact],
        before: SystemAssessmentResult,
        after: SystemAssessmentResult,
    ) -> str | None:
        if not impacts:
            return (
                f"{engineer_name} has no demonstrated capability coverage recorded in "
                f"{scope_name}, so no coverage would be lost."
            )
        context = SimulationSummaryContext(
            engineer_name=engineer_name,
            scope_name=scope_name,
            critical_gap_capabilities=[
                i.name
                for i in impacts
                if i.after is CapabilityExposure.CRITICAL_GAP
                and i.before is not CapabilityExposure.CRITICAL_GAP
            ],
            degraded_capabilities=[
                i.name
                for i in impacts
                if i.after is CapabilityExposure.DEGRADED and i.before is not CapabilityExposure.DEGRADED
            ],
            preserved_capabilities=[
                i.name
                for i in impacts
                if i.after is CapabilityExposure.COVERED and i.before is CapabilityExposure.COVERED
            ],
            risk_class_before=before.continuity_risk_class.value if before.continuity_risk_class else "UNKNOWN",
            risk_class_after=after.continuity_risk_class.value if after.continuity_risk_class else "UNKNOWN",
        )
        return self.provider.summarize_simulation(context)

    def get(self, simulation_id: str) -> dict:
        record = SimulationRepository(self.session).get(simulation_id)
        if record is None:
            raise NotFoundError(
                f"Simulation '{simulation_id}' not found.", {"simulation_id": simulation_id}
            )
        return record.result_json
