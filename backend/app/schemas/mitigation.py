"""Mitigation-plan DTOs. docs/API_CONTRACT.md sections 8.9 and 8.10.

Generating a plan does not change readiness or continuity risk.
"""

from datetime import datetime

from pydantic import BaseModel

from .capability import CapabilityRef
from .enums import MitigationPlanStatus, MitigationTaskType, ReadinessLevel


class EngineerRef(BaseModel):
    engineer_id: str
    name: str


class MitigationPlanRequest(BaseModel):
    capability_id: str
    primary_engineer_id: str
    selected_backup_engineer_id: str
    simulation_id: str | None = None


class MitigationTask(BaseModel):
    task_id: str
    title: str
    description: str
    type: MitigationTaskType
    acceptance_criteria: list[str] = []
    linked_evidence_ids: list[str] = []


class MitigationPlanResponse(BaseModel):
    plan_id: str
    status: MitigationPlanStatus
    capability: CapabilityRef
    source_engineer: EngineerRef
    backup_candidate: EngineerRef
    target_readiness: ReadinessLevel
    tasks: list[MitigationTask]


class ApprovePlanRequest(BaseModel):
    """`tasks` carries manager edits made before approval. Contract decision CI-12.

    Omitted means approve as generated. Permitted only while status is DRAFT.
    """

    approved_by: str
    tasks: list[MitigationTask] | None = None


class ApprovePlanResponse(BaseModel):
    plan_id: str
    status: MitigationPlanStatus
    approved_by: str
    approved_at: datetime
