"""Persistence access. docs/ARCHITECTURE.md section 16.

Application services never write SQL; they go through these. Each repository takes a
Session so a simulation can read a consistent snapshot without owning transaction
lifetime.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Capability,
    CapabilityAssessment,
    Component,
    Coverage,
    DeclaredOwnership,
    Engineer,
    Evidence,
    MitigationPlan,
    Platform,
    Simulation,
    System,
    SystemAssessment,
)


class _Repo:
    def __init__(self, session: Session) -> None:
        self.session = session


class PlatformRepository(_Repo):
    def list_all(self) -> list[Platform]:
        return list(self.session.scalars(select(Platform).order_by(Platform.position)))

    def get(self, platform_id: str) -> Platform | None:
        return self.session.get(Platform, platform_id)


class SystemRepository(_Repo):
    def list_all(self) -> list[System]:
        return list(self.session.scalars(select(System).order_by(System.position)))

    def list_by_platform(self, platform_id: str) -> list[System]:
        stmt = select(System).where(System.platform_id == platform_id).order_by(System.position)
        return list(self.session.scalars(stmt))

    def get(self, system_id: str) -> System | None:
        return self.session.get(System, system_id)

    def components(self, system_id: str) -> list[Component]:
        stmt = select(Component).where(Component.system_id == system_id).order_by(Component.position)
        return list(self.session.scalars(stmt))

    def assessment(self, system_id: str) -> SystemAssessment | None:
        return self.session.get(SystemAssessment, system_id)

    def assessments_for_platform(self, platform_id: str) -> list[SystemAssessment]:
        stmt = (
            select(SystemAssessment)
            .join(System, System.system_id == SystemAssessment.system_id)
            .where(System.platform_id == platform_id)
        )
        return list(self.session.scalars(stmt))

    def declared_owner(self, system_id: str) -> tuple[Engineer, str] | None:
        stmt = (
            select(Engineer, DeclaredOwnership.source_reference)
            .join(DeclaredOwnership, DeclaredOwnership.engineer_id == Engineer.engineer_id)
            .where(DeclaredOwnership.system_id == system_id)
        )
        row = self.session.execute(stmt).first()
        return (row[0], row[1]) if row else None


class CapabilityRepository(_Repo):
    def get(self, capability_id: str) -> Capability | None:
        return self.session.get(Capability, capability_id)

    def list_by_system(self, system_id: str) -> list[Capability]:
        stmt = (
            select(Capability)
            .join(Component, Component.component_id == Capability.component_id)
            .where(Capability.system_id == system_id)
            .order_by(Component.position, Capability.position)
        )
        return list(self.session.scalars(stmt))

    def list_by_component(self, component_id: str) -> list[Capability]:
        stmt = (
            select(Capability)
            .where(Capability.component_id == component_id)
            .order_by(Capability.position)
        )
        return list(self.session.scalars(stmt))

    def list_all(self) -> list[Capability]:
        return list(self.session.scalars(select(Capability).order_by(Capability.capability_id)))

    def assessment(self, capability_id: str) -> CapabilityAssessment | None:
        return self.session.get(CapabilityAssessment, capability_id)

    def assessments_for_system(self, system_id: str) -> dict[str, CapabilityAssessment]:
        stmt = (
            select(CapabilityAssessment)
            .join(Capability, Capability.capability_id == CapabilityAssessment.capability_id)
            .where(Capability.system_id == system_id)
        )
        return {a.capability_id: a for a in self.session.scalars(stmt)}


class EngineerRepository(_Repo):
    def get(self, engineer_id: str) -> Engineer | None:
        return self.session.get(Engineer, engineer_id)

    def list_all(self) -> list[Engineer]:
        return list(self.session.scalars(select(Engineer).order_by(Engineer.engineer_id)))

    def by_id(self) -> dict[str, Engineer]:
        return {e.engineer_id: e for e in self.list_all()}


class CoverageRepository(_Repo):
    def list_by_capability(self, capability_id: str) -> list[Coverage]:
        stmt = select(Coverage).where(Coverage.capability_id == capability_id)
        return list(self.session.scalars(stmt))

    def list_by_system(self, system_id: str) -> list[Coverage]:
        stmt = (
            select(Coverage)
            .join(Capability, Capability.capability_id == Coverage.capability_id)
            .where(Capability.system_id == system_id)
        )
        return list(self.session.scalars(stmt))

    def list_by_engineer(self, engineer_id: str) -> list[Coverage]:
        stmt = select(Coverage).where(Coverage.engineer_id == engineer_id)
        return list(self.session.scalars(stmt))

    def get(self, engineer_id: str, capability_id: str) -> Coverage | None:
        return self.session.get(Coverage, {"engineer_id": engineer_id, "capability_id": capability_id})


class EvidenceRepository(_Repo):
    def list_by_capability(self, capability_id: str, engineer_id: str | None = None) -> list[Evidence]:
        stmt = select(Evidence).where(Evidence.capability_id == capability_id)
        if engineer_id is not None:
            stmt = stmt.where(Evidence.engineer_id == engineer_id)
        return list(self.session.scalars(stmt.order_by(Evidence.artifact_date.desc())))

    def list_by_ids(self, evidence_ids: list[str]) -> list[Evidence]:
        if not evidence_ids:
            return []
        stmt = select(Evidence).where(Evidence.evidence_id.in_(evidence_ids))
        return list(self.session.scalars(stmt))

    def list_by_engineer_and_system(self, engineer_id: str, system_id: str) -> list[Evidence]:
        stmt = select(Evidence).where(
            Evidence.engineer_id == engineer_id, Evidence.system_id == system_id
        )
        return list(self.session.scalars(stmt.order_by(Evidence.artifact_date.desc())))

    def list_all(self) -> list[Evidence]:
        return list(self.session.scalars(select(Evidence)))

    def count(self) -> int:
        return int(self.session.scalar(select(func.count(Evidence.evidence_id))) or 0)

    def counts_by_capability(self, system_id: str | None = None) -> dict[str, tuple[int, int]]:
        """`capability_id -> (qualifying_count, conflicting_count)`.

        The qualifying count is what decides `INSUFFICIENT_EVIDENCE`, so it must exclude
        conflicting records: a capability whose only evidence contradicts itself has not been
        assessed, it has been argued about.
        """
        stmt = select(
            Evidence.capability_id,
            func.sum(func.iif(Evidence.is_conflicting, 0, 1)),
            func.sum(func.iif(Evidence.is_conflicting, 1, 0)),
        ).group_by(Evidence.capability_id)
        if system_id is not None:
            stmt = stmt.where(Evidence.system_id == system_id)
        return {row[0]: (int(row[1] or 0), int(row[2] or 0)) for row in self.session.execute(stmt)}

    def list_by_system(self, system_id: str) -> list[Evidence]:
        stmt = select(Evidence).where(Evidence.system_id == system_id)
        return list(self.session.scalars(stmt.order_by(Evidence.artifact_date.desc())))


class SimulationRepository(_Repo):
    def get(self, simulation_id: str) -> Simulation | None:
        return self.session.get(Simulation, simulation_id)

    def next_id(self) -> str:
        used = int(self.session.scalar(select(func.count(Simulation.simulation_id))) or 0)
        return f"sim_{used + 1:03d}"

    def add(self, simulation: Simulation) -> Simulation:
        self.session.add(simulation)
        self.session.flush()
        return simulation


class MitigationPlanRepository(_Repo):
    def get(self, plan_id: str) -> MitigationPlan | None:
        return self.session.get(MitigationPlan, plan_id)

    def next_id(self) -> str:
        used = int(self.session.scalar(select(func.count(MitigationPlan.plan_id))) or 0)
        return f"plan_{used + 1:03d}"

    def add(self, plan: MitigationPlan) -> MitigationPlan:
        self.session.add(plan)
        self.session.flush()
        return plan
