"""Simulation DTOs. docs/API_CONTRACT.md sections 8.7.

The simulation identifies coverage loss. It does not predict an outage.
All impact fields are deterministic backend output; only `summary` may be AI-generated.
"""

from pydantic import BaseModel, Field

from .enums import (
    CapabilityExposure,
    ContinuityRiskClass,
    OperationalCriticality,
    ReadinessLevel,
    SimulationScopeType,
    SimulationType,
)


class SimulationScopeRequest(BaseModel):
    type: SimulationScopeType
    id: str


class SimulationRequest(BaseModel):
    simulation_type: SimulationType
    engineer_id: str
    scope: SimulationScopeRequest


class SimulationScope(SimulationScopeRequest):
    name: str


class EngineerRef(BaseModel):
    engineer_id: str
    name: str


class SimulationState(BaseModel):
    continuity_risk_index: int = Field(ge=0, le=100)
    continuity_risk_class: ContinuityRiskClass
    critical_gap_count: int = Field(ge=0)
    degraded_capability_count: int = Field(ge=0)
    covered_capability_count: int = Field(ge=0)


class CapabilityImpact(BaseModel):
    capability_id: str
    name: str
    operational_criticality: OperationalCriticality
    before: CapabilityExposure
    after: CapabilityExposure
    remaining_best_readiness: ReadinessLevel


class SimulationResponse(BaseModel):
    simulation_id: str
    simulation_type: SimulationType
    engineer: EngineerRef
    scope: SimulationScope
    before: SimulationState
    after: SimulationState
    capability_impacts: list[CapabilityImpact]
    summary: str | None = None
