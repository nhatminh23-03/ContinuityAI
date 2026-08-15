"""Platform DTOs. docs/API_CONTRACT.md sections 6.1 and 8.1.

The MVP deliberately exposes no platform-level risk score (contract section 2.1).
"""

from pydantic import BaseModel, Field

from .enums import KnowledgeDriftStatus


class PlatformSummary(BaseModel):
    platform_id: str
    name: str
    description: str | None = None
    system_count: int = Field(ge=0)
    critical_gap_count: int = Field(ge=0)
    highest_system_risk_index: int | None = Field(default=None, ge=0, le=100)
    drift_status: KnowledgeDriftStatus


class PlatformListResponse(BaseModel):
    platforms: list[PlatformSummary]


class PlatformRef(BaseModel):
    platform_id: str
    name: str
