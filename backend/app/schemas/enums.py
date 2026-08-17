"""Shared enums. Frozen by docs/API_CONTRACT.md section 5.

Values are part of the contract. Changing one is a Category C decision requiring
both developers and an entry in docs/DECISIONS.md.
"""

from enum import Enum


class StrEnum(str, Enum):
    """String enum so values serialise as their literal text."""


class BusinessCriticality(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OperationalCriticality(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReadinessLevel(StrEnum):
    NONE = "NONE"
    EXPOSED = "EXPOSED"
    ASSISTED = "ASSISTED"
    PRACTICED = "PRACTICED"
    VALIDATED = "VALIDATED"


class CapabilityExposure(StrEnum):
    COVERED = "COVERED"
    DEGRADED = "DEGRADED"
    CRITICAL_GAP = "CRITICAL_GAP"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ContinuityRiskClass(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceStrength(StrEnum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class EvidenceConfidence(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Freshness(StrEnum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"


class KnowledgeDriftStatus(StrEnum):
    NEW_RISK = "NEW_RISK"
    RISK_INCREASED = "RISK_INCREASED"
    STABLE = "STABLE"
    RISK_REDUCED = "RISK_REDUCED"


class EvidenceSourceType(StrEnum):
    COMMIT = "COMMIT"
    PULL_REQUEST = "PULL_REQUEST"
    CODE_REVIEW = "CODE_REVIEW"
    ISSUE = "ISSUE"
    TICKET = "TICKET"
    INCIDENT = "INCIDENT"
    DOCUMENT = "DOCUMENT"
    TECHNICAL_DISCUSSION = "TECHNICAL_DISCUSSION"
    MANAGER_ATTESTATION = "MANAGER_ATTESTATION"


class EvidenceRole(StrEnum):
    EXPOSURE = "EXPOSURE"
    CONTRIBUTION = "CONTRIBUTION"
    ASSISTED_EXECUTION = "ASSISTED_EXECUTION"
    INDEPENDENT_EXECUTION = "INDEPENDENT_EXECUTION"
    KNOWLEDGE_CAPTURE = "KNOWLEDGE_CAPTURE"


class GraphNodeType(StrEnum):
    PLATFORM = "PLATFORM"
    SYSTEM = "SYSTEM"
    COMPONENT = "COMPONENT"
    CAPABILITY = "CAPABILITY"
    ENGINEER = "ENGINEER"
    EVIDENCE = "EVIDENCE"


class GraphEdgeType(StrEnum):
    HAS_SYSTEM = "HAS_SYSTEM"
    HAS_COMPONENT = "HAS_COMPONENT"
    REQUIRES_CAPABILITY = "REQUIRES_CAPABILITY"
    DEMONSTRATES = "DEMONSTRATES"
    SUPPORTED_BY = "SUPPORTED_BY"
    DECLARED_OWNER = "DECLARED_OWNER"


class SimulationType(StrEnum):
    ENGINEER_UNAVAILABLE = "ENGINEER_UNAVAILABLE"


class SimulationScopeType(StrEnum):
    SYSTEM = "SYSTEM"
    PLATFORM = "PLATFORM"


class TechnicalOverlap(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MitigationPlanStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"


class MitigationTaskType(StrEnum):
    KNOWLEDGE_REVIEW = "KNOWLEDGE_REVIEW"
    SHADOWING = "SHADOWING"
    PRACTICE = "PRACTICE"
    RECOVERY_DRILL = "RECOVERY_DRILL"
    DOCUMENTATION = "DOCUMENTATION"
    ARCHITECTURE_REVIEW = "ARCHITECTURE_REVIEW"


class CriticalitySource(StrEnum):
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"
    AI_SUGGESTED = "AI_SUGGESTED"


class ChallengeType(StrEnum):
    """How a manager disputes an assessment. PRD section 21, contract decision CI-13.

    A manager never edits a readiness value or a risk score. They change the *evidence*, and the
    assessment is recomputed from it — which is why every value in this enum names an evidence
    operation rather than an outcome.
    """

    LINK_EVIDENCE = "LINK_EVIDENCE"
    MANAGER_ATTESTATION = "MANAGER_ATTESTATION"
    CORRECT_CAPABILITY_MAPPING = "CORRECT_CAPABILITY_MAPPING"


class ErrorCode(StrEnum):
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    # Only reachable when API_TOKEN is configured; the API is open by default. RECOMMENDATIONS R-03.
    UNAUTHORIZED = "UNAUTHORIZED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    AI_EXTRACTION_FAILED = "AI_EXTRACTION_FAILED"
    GRAPH_INCONSISTENCY = "GRAPH_INCONSISTENCY"
    SIMULATION_FAILED = "SIMULATION_FAILED"
    MITIGATION_GENERATION_FAILED = "MITIGATION_GENERATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
