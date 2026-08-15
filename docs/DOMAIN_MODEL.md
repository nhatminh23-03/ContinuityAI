# ContinuityAI — Domain Model Specification

**Version:** 1.0  
**Status:** Phase 0 — Frozen for MVP implementation  
**Companion documents:** `PRD.md`, `API_CONTRACT.md`, `ARCHITECTURE.md`

---

## 1. Purpose

This document defines the internal domain model for the ContinuityAI MVP.

It is the shared reference for both backend and frontend developers and establishes:

- core domain entities;
- typed identifiers;
- entity relationships;
- graph node and edge semantics;
- enumerations;
- invariants;
- ownership of derived fields;
- evidence-to-readiness rules;
- continuity-risk semantics;
- simulation semantics;
- candidate-comparison semantics;
- mitigation-plan semantics;
- responsible-AI boundaries.

The API contract defines **what crosses the frontend/backend boundary**.

This document defines **what the product means internally**.

---

# 2. Core Product Principle

ContinuityAI models organizational knowledge resilience around technical systems.

The primary hierarchy is:

```text
Platform
  └── System
       └── Component
            └── Capability
                 └── Engineer
                      └── Evidence
```

A more precise graph interpretation is:

```text
Platform
   │
   └── contains → System
                    │
                    └── contains → Component
                                      │
                                      └── requires → Capability
                                                        │
                                                        ├── demonstrated_by → Engineer
                                                        │                       │
                                                        │                       └── supported_by → Evidence
                                                        │
                                                        └── supported_by → Evidence
```

Continuity risk originates primarily at the **Capability** level and rolls upward.

ContinuityAI does **not** model employee value, employee productivity, or employee worth.

---

# 3. Domain Boundaries

## 3.1 Backend-owned domain truth

The backend owns all authoritative calculations for:

- capability readiness;
- evidence strength;
- evidence diversity;
- evidence freshness;
- evidence confidence;
- capability exposure;
- Continuity Risk Index;
- critical-gap detection;
- counterfactual simulation;
- technical backup-candidate comparison;
- mitigation-plan generation.

The frontend may:

- render;
- sort;
- filter;
- search;
- navigate;
- select;
- visualize.

The frontend must **not** recompute domain intelligence.

---

# 4. Typed Identifier Convention

All persistent domain entities use typed string identifiers.

Examples:

```text
platform_payments
system_payment_gateway
component_gateway_integration
cap_incident_recovery
eng_alex_chen
evidence_inc_184
sim_001
plan_001
task_001
```

## 4.1 Rules

1. IDs are stable.
2. Names are not identifiers.
3. UI labels may change without changing IDs.
4. IDs should be lowercase snake case where human-readable.
5. Generated workflow objects may use UUIDs in production, but human-readable IDs are acceptable for MVP seed data.

---

# 5. Enumerations

## 5.1 BusinessCriticality

Human-confirmed top-level business importance.

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Used primarily on `System`.

AI may recommend criticality, but the human-confirmed value is authoritative.

---

## 5.2 OperationalCriticality

Technical importance of a capability to successful system operation.

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Used primarily on `Capability`.

---

## 5.3 ReadinessLevel

Represents demonstrated technical readiness for an engineer-capability relationship.

```text
NONE
EXPOSED
ASSISTED
PRACTICED
VALIDATED
```

Meaning:

### NONE
No qualifying evidence exists.

### EXPOSED
The engineer has observed, reviewed, discussed, or lightly interacted with the capability, but there is not enough evidence of execution.

### ASSISTED
The engineer has participated in execution with meaningful support from another engineer.

### PRACTICED
The engineer has performed the capability hands-on without significant support, but the evidence is limited to controlled or lower-risk contexts, or lacks the repetition, source diversity, or recency required for `VALIDATED`.

### VALIDATED
Available evidence demonstrates repeated or sufficiently strong independent execution of the capability.

Important:

`VALIDATED` means **demonstrated readiness based on available evidence**.

It does not mean absolute certainty about what a person knows.

---

## 5.4 CapabilityExposure

Represents continuity coverage for a capability.

```text
COVERED
DEGRADED
CRITICAL_GAP
INSUFFICIENT_EVIDENCE
```

### COVERED
Sufficient demonstrated backup coverage exists.

### DEGRADED
Coverage exists, but redundancy or readiness is weaker than desired.

### CRITICAL_GAP
A critical capability lacks sufficient demonstrated independent backup coverage.

### INSUFFICIENT_EVIDENCE
The system cannot responsibly determine continuity coverage from available artifacts.

---

## 5.5 EvidenceStrength

```text
WEAK
MODERATE
STRONG
```

Strength measures how strongly a single artifact demonstrates execution or knowledge.

---

## 5.6 EvidenceConfidence

```text
LOW
MEDIUM
HIGH
```

Confidence is separate from risk.

A system may have:

```text
Risk: HIGH
Evidence Confidence: LOW
```

This means the evidence suggests exposure, but the underlying data is weak.

It must never be interpreted as a probability.

---

## 5.7 Freshness

```text
FRESH
AGING
STALE
```

Freshness reflects whether evidence is recent enough to remain relevant to the current technical state.

---

## 5.8 KnowledgeDriftStatus

```text
NEW_RISK
RISK_INCREASED
STABLE
RISK_REDUCED
```

Used for dashboard knowledge-drift communication.

---

## 5.9 EvidenceSourceType

```text
COMMIT
PULL_REQUEST
CODE_REVIEW
ISSUE
TICKET
INCIDENT
DOCUMENT
TECHNICAL_DISCUSSION
MANAGER_ATTESTATION
```

MVP does not need to populate every source type.

---

## 5.10 EvidenceRole

The semantic role of evidence after AI extraction.

```text
EXPOSURE
CONTRIBUTION
ASSISTED_EXECUTION
INDEPENDENT_EXECUTION
KNOWLEDGE_CAPTURE
```

### EXPOSURE
Reviewing, observing, discussing, or lightly interacting with work.

### CONTRIBUTION
Meaningful implementation or operational contribution without evidence of independent execution.

### ASSISTED_EXECUTION
Hands-on execution performed with another person providing significant support.

### INDEPENDENT_EXECUTION
Evidence indicates the engineer independently performed the capability.

### KNOWLEDGE_CAPTURE
The engineer created or substantially updated technical documentation, runbooks, architecture guidance, or operational knowledge.

---

## 5.11 SimulationType

For MVP:

```text
ENGINEER_UNAVAILABLE
```

No separate departure, vacation, termination, or reassignment semantics exist in MVP.

---

## 5.12 TechnicalOverlap

```text
LOW
MEDIUM
HIGH
```

Used for backup candidate comparison.

This is not a staffing recommendation score.

---

## 5.13 MitigationPlanStatus

```text
DRAFT
APPROVED
```

MVP does not need execution tracking.

---

## 5.14 MitigationTaskType

```text
KNOWLEDGE_REVIEW
SHADOWING
PRACTICE
RECOVERY_DRILL
DOCUMENTATION
ARCHITECTURE_REVIEW
```

---

## 5.15 ContinuityRiskClass

```text
LOW
MODERATE
HIGH
CRITICAL
```

The class is the authoritative rule-engine output. The Continuity Risk Index is the derived
comparison number, clamped to the band of its class (`LOW 0–39`, `MODERATE 40–59`,
`HIGH 60–79`, `CRITICAL 80–100`) so that modifiers cannot silently reclassify a capability.

---

# 6. Entity: Platform

A Platform is the top-level portfolio grouping shown on the dashboard.

Examples:

```text
Payments Platform
Identity Platform
Risk Platform
```

## 6.1 Fields

```text
platform_id: string
name: string
description: string | null
system_ids: list[string]
```

Derived dashboard fields:

```text
system_count: integer
critical_gap_count: integer
highest_system_risk_index: integer
drift_status: KnowledgeDriftStatus
```

## 6.2 Invariants

- A Platform contains one or more Systems.
- Platform does not receive an independent risk score in MVP.
- Platform risk communication uses:
  - highest system risk;
  - total critical gaps;
  - knowledge drift.

---

# 7. Entity: System

A System is a technical service or application that must remain operable.

Examples:

```text
Payment Gateway
Refund Engine
Billing Integration
Authentication
Authorization
```

## 7.1 Fields

```text
system_id: string
platform_id: string
name: string
description: string
business_criticality: BusinessCriticality
component_ids: list[string]
```

Derived:

```text
continuity_risk_index: integer 0..100
continuity_risk_class: ContinuityRiskClass
exposure: CapabilityExposure
evidence_confidence: EvidenceConfidence
critical_gap_count: integer
degraded_capability_count: integer
covered_capability_count: integer
insufficient_evidence_count: integer
drift_status: KnowledgeDriftStatus
```

## 7.2 Invariants

- Each System belongs to exactly one Platform in MVP.
- Each System contains one or more Components.
- Business criticality is human-confirmed.
- Risk is derived from underlying capability conditions.
- System risk is not a probability of outage.

---

# 8. Entity: Component

A Component is a meaningful technical subsystem inside a System.

Examples for Payment Gateway:

```text
Gateway Integration
Retry Engine
Payment Routing
Observability
```

## 8.1 Fields

```text
component_id: string
system_id: string
name: string
description: string | null
capability_ids: list[string]
```

## 8.2 Invariants

- A Component belongs to one System.
- A Component requires one or more Capabilities.
- Component-level risk may be derived internally but does not require a dedicated public score in MVP.

---

# 9. Entity: Capability

Capability is the central continuity unit.

A Capability describes a technical ability required to operate, recover, maintain, or safely change a System.

Examples:

```text
Incident Recovery
Provider Failover
Retry Logic
Certificate Rotation
Schema Migration
Deployment Rollback
Fraud Rule Recovery
```

## 9.1 Fields

```text
capability_id: string
system_id: string
component_id: string
name: string
description: string
operational_criticality: OperationalCriticality
```

Derived:

```text
exposure: CapabilityExposure
continuity_risk_index: integer 0..100
continuity_risk_class: ContinuityRiskClass
evidence_confidence: EvidenceConfidence
rules_triggered: list[string]
engineer_coverage: list[EngineerCapabilityCoverage]
primary_engineer_id: string | null
best_remaining_coverage_engineer_id: string | null
```

## 9.2 Invariants

- Every Capability belongs to one Component.
- Every Capability belongs indirectly to one System.
- Continuity analysis occurs primarily at this level.
- Capability risk must remain explainable through explicit rules.
- A capability may legitimately return `INSUFFICIENT_EVIDENCE`.

---

# 10. Entity: Engineer

An Engineer represents a technical contributor visible in organizational engineering evidence.

## 10.1 Fields

```text
engineer_id: string
name: string
role: string | null
team: string | null
```

Derived:

```text
demonstrated_capabilities: list[EngineerCapabilityCoverage]
```

## 10.2 Explicitly prohibited fields

The following must not exist:

```text
employee_value_score
productivity_score
importance_score
layoff_score
promotion_score
bonus_score
engagement_score
personality_score
```

The Engineer entity exists only to represent technical coverage relationships.

---

# 11. Relationship: EngineerCapabilityCoverage

This is one of the most important domain relationships.

It represents:

```text
Engineer → demonstrates → Capability
```

## 11.1 Fields

```text
engineer_id: string
capability_id: string
readiness: ReadinessLevel
freshness: Freshness
evidence_confidence: EvidenceConfidence
supporting_evidence_ids: list[string]
last_demonstrated_at: datetime | null
```

Optional internal aggregates:

```text
strong_evidence_count: integer
moderate_evidence_count: integer
weak_evidence_count: integer
source_type_count: integer
independent_execution_count: integer
assisted_execution_count: integer
knowledge_capture_count: integer
```

## 11.2 Invariants

- Readiness is calculated by deterministic backend logic.
- AI does not directly assign readiness.
- Every non-`NONE` readiness classification must be explainable through evidence.
- If evidence is contradictory or too sparse, readiness may remain low or the capability may be marked insufficient evidence.

---

# 12. Entity: Evidence

Evidence is the traceable source supporting a technical-capability claim.

## 12.1 Fields

```text
evidence_id: string

source_type: EvidenceSourceType
source_reference: string
source_title: string | null
artifact_date: datetime

engineer_id: string
system_id: string
component_id: string | null
capability_id: string

evidence_role: EvidenceRole
evidence_strength: EvidenceStrength
freshness: Freshness

summary: string

provenance: {
  source: string
  record_id: string
  source_url: string | null
}
```

Optional:

```text
raw_artifact_id: string | null
ai_extraction_confidence: EvidenceConfidence | null
```

## 12.2 Invariants

- Evidence must be traceable to a source artifact.
- Evidence summaries must not invent facts unsupported by the source.
- Evidence is about demonstrated technical activity.
- Absence of evidence must not be phrased as inability.

Preferred wording:

```text
No qualifying evidence found.
```

Not:

```text
Jordan cannot recover Payment Gateway.
```

---

# 13. Raw Artifact Model

Before evidence exists, the ingestion layer processes Raw Artifacts.

Raw Artifact is an internal ingestion concept.

## 13.1 Fields

```text
artifact_id: string
source_type: EvidenceSourceType
source_reference: string
title: string | null
body: string
author_ids: list[string]
created_at: datetime
updated_at: datetime | null
metadata: object
```

Examples:

- GitHub pull request
- production incident record
- engineering ticket
- runbook
- architecture document
- CODEOWNERS metadata

---

# 14. AI Semantic Extraction Contract

AI converts Raw Artifacts into structured evidence candidates.

The AI may extract:

```text
source
system
component
capability
engineer
evidence_role
evidence_strength
artifact_date
summary
```

The AI must **not** directly output:

```text
readiness = VALIDATED
continuity_risk = 93
employee_is_critical = true
best_employee = Maria
```

The deterministic engine performs those decisions.

---

# 15. Evidence Aggregation Model

Multiple pieces of evidence are aggregated for each:

```text
(engineer_id, capability_id)
```

The aggregation considers:

1. evidence strength;
2. evidence diversity;
3. freshness;
4. repetition;
5. independent execution;
6. assisted execution;
7. documentation/knowledge capture;
8. conflicting evidence.

---

# 16. Readiness Classification Model

The exact numeric thresholds may be tuned during implementation, but the semantic contract is fixed.

## 16.1 NONE

Typical condition:

```text
No qualifying evidence.
```

---

## 16.2 EXPOSED

Typical evidence:

```text
reviewed PR
commented on incident
observed recovery
discussed architecture
minor related contribution
```

No meaningful execution evidence.

---

## 16.3 ASSISTED

Typical evidence:

```text
participated in incident recovery with senior engineer
performed part of failover under guidance
assisted implementation
```

---

## 16.4 PRACTICED

Typical evidence:

```text
performed staging recovery
executed operational procedure
repeated implementation evidence
performed significant hands-on work
```

But insufficient evidence of repeated independent real-world execution.

---

## 16.5 VALIDATED

Typical evidence pattern:

```text
independent execution
+ strong evidence
+ sufficiently recent
+ repeated or corroborated
+ preferably more than one evidence source
```

Example:

```text
INC-184   independent recovery
INC-221   independent recovery
PR-442    recovery implementation
DOC-17    runbook authorship
```

---

# 17. Evidence Confidence Model

Evidence confidence answers:

> How confident are we in the assessment given the available evidence?

It does **not** answer:

> What is the probability the engineer is competent?

Suggested model:

## LOW

```text
few artifacts
single source type
old evidence
ambiguous extraction
```

## MEDIUM

```text
multiple relevant artifacts
some source diversity
reasonable freshness
```

## HIGH

```text
multiple strong artifacts
source diversity
recent evidence
consistent signals
repeated demonstration
```

---

# 18. Freshness Model

Freshness may be implemented initially with simple date thresholds.

Example starting point:

```text
FRESH  = evidence within 18 months, or within 12 months where component change is low
AGING  = 18–36 months, or substantial component change
STALE  = older than 36 months, or component change is high, or a known architecture migration
```

These are implementation defaults, not permanent product truths.

A more advanced future model can also account for system-change velocity.

---

# 19. Capability Exposure Model

Exposure is derived from:

- capability criticality;
- engineer readiness distribution;
- independent backup coverage;
- evidence quality;
- documentation;
- freshness.

The model separates **no redundancy** from **no coverage**. A capability carried by a single
adequate engineer has coverage but no resilience; a capability with no adequate engineer at all
has neither. These are different states and must not collapse into one.

```text
IF capability criticality in (CRITICAL, HIGH)
AND practiced_or_validated_engineer_count == 0
THEN exposure = CRITICAL_GAP
```

```text
IF capability criticality in (CRITICAL, HIGH)
AND practiced_or_validated_engineer_count == 1
AND practiced_or_validated_backup_count == 0
THEN exposure = DEGRADED
```

Another:

```text
IF primary coverage == VALIDATED
AND strongest backup == PRACTICED
THEN exposure = DEGRADED
```

Possible:

```text
IF primary coverage >= VALIDATED
AND at least one backup >= VALIDATED
THEN exposure = COVERED
```

Possible:

```text
IF evidence confidence == LOW
AND readiness cannot be responsibly inferred
THEN exposure = INSUFFICIENT_EVIDENCE
```

---

# 20. Continuity Risk Index

The Continuity Risk Index is a transparent comparison index from:

```text
0..100
```

It is not:

- outage probability;
- employee departure probability;
- failure probability;
- loss estimate.

It combines deterministic continuity conditions.

Potential factors:

```text
knowledge concentration
backup readiness
business criticality
operational criticality
documentation gap
evidence freshness
evidence confidence
```

The UI must provide a `Why this risk?` explanation based on fired rules.

Example:

```text
Continuity Risk Index: 72 (HIGH)

Why:
- Capability is CRITICAL.
- Only one VALIDATED engineer exists.
- No PRACTICED or VALIDATED backup exists.
- Backup evidence is limited.
- Recovery documentation is aging.
```

This is a sole-expert capability: exposure is `DEGRADED`, because coverage exists today but no
resilient backup does. Should that single engineer become unavailable, the same capability
reaches `CRITICAL_GAP`.

---

# 21. Risk Aggregation

## 21.1 Capability → Component

Component exposure derives from the severity of its required capabilities.

MVP may use maximum-severity logic.

---

## 21.2 Component → System

System risk derives from capability-level conditions.

MVP may use a weighted aggregation emphasizing:

- CRITICAL capability gaps;
- HIGH capability gaps;
- number of single-expert dependencies.

---

## 21.3 System → Platform

MVP does not calculate an independent Platform Risk Index.

Platform shows:

```text
highest_system_risk_index
critical_gap_count
drift_status
```

---

# 22. Entity: Simulation

Simulation models a counterfactual state where one engineer's demonstrated capability coverage is removed.

## 22.1 Fields

```text
simulation_id: string
simulation_type: ENGINEER_UNAVAILABLE

engineer_id: string

scope_type: SimulationScopeType   # SYSTEM only in MVP
scope_id: string

created_at: datetime

before_state: SimulationState
after_state: SimulationState

capability_impacts: list[CapabilityImpact]

summary: string | null
```

---

# 23. SimulationState

```text
continuity_risk_index: integer
continuity_risk_class: ContinuityRiskClass
critical_gap_count: integer
degraded_capability_count: integer
covered_capability_count: integer
```

---

# 24. CapabilityImpact

```text
capability_id: string
name: string

operational_criticality: OperationalCriticality

before: CapabilityExposure
after: CapabilityExposure

remaining_best_readiness: ReadinessLevel
```

---

# 25. Simulation Algorithm

For MVP:

```text
1. Load current system graph.
2. Capture baseline state.
3. Remove target engineer's EngineerCapabilityCoverage edges within scope.
4. Recompute remaining readiness distribution.
5. Re-run capability exposure rules.
6. Re-run system risk aggregation.
7. Compare before vs after.
8. Return capability impacts.
```

Important:

The simulation does not predict whether the System will fail.

It answers:

> Which technical capabilities become exposed if this demonstrated expertise is unavailable?

---

# 26. Backup Candidate Domain Model

Candidate comparison occurs only after a continuity gap is identified.

## 26.1 Entity: BackupCandidate

```text
engineer_id: string
capability_id: string

technical_overlap: TechnicalOverlap
strengths: list[string]
gaps: list[string]

evidence_confidence: EvidenceConfidence

supporting_capability_ids: list[string]
supporting_evidence_ids: list[string]
```

---

# 27. Backup Candidate Rules

The system may consider:

```text
adjacent demonstrated capabilities
system familiarity
component familiarity
operational experience
recovery experience
deployment experience
relevant documentation
evidence freshness
```

The system must not consider unless explicitly integrated in the future:

```text
workload
availability
salary
performance rating
promotion readiness
career goals
personality
working hours
manager preference
```

The output is:

> strongest technical candidate based on available engineering evidence.

Not:

> best employee to assign.

---

# 28. Candidate Ranking

MVP returns up to three candidates.

The frontend should show trade-offs.

Example:

```text
Maria
Technical overlap: HIGH

Strengths
- infrastructure recovery
- production deployment
- assisted payment recovery

Gaps
- independent gateway recovery
- provider failover execution
```

No fake numeric precision such as:

```text
Maria = 87.4%
```

unless the team later creates a well-defined, transparent score.

---

# 29. Entity: MitigationPlan

A MitigationPlan is generated after the manager selects a backup candidate.

## 29.1 Fields

```text
plan_id: string

capability_id: string
system_id: string

source_engineer_id: string
selected_backup_engineer_id: string

status: MitigationPlanStatus

tasks: list[MitigationTask]

created_at: datetime
approved_at: datetime | null
```

---

# 30. Entity: MitigationTask

```text
task_id: string

title: string
description: string
type: MitigationTaskType

acceptance_criteria: list[string]
linked_evidence_ids: list[string]

# persistence-only, not part of the API DTO:
plan_id: string
sequence: integer
```

MVP does not need:

```text
due_date
jira_ticket
completion_state
calendar_event
automatic assignment
```

---

# 31. Mitigation-Plan Principles

The generated plan should target the **specific missing capability**, not clone the entire source engineer.

Example:

Alex may demonstrate 20 Payments capabilities.

If Maria already covers 18, the plan should focus only on:

```text
Incident Recovery
Provider Failover
```

This is one of the product's key conceptual advantages.

---

# 32. Entity: KnowledgeDriftEvent

Optional MVP internal domain object.

```text
drift_event_id: string
entity_type: SYSTEM | CAPABILITY
entity_id: string

previous_exposure: CapabilityExposure | null
current_exposure: CapabilityExposure

drift_status: KnowledgeDriftStatus
detected_at: datetime

reason_codes: list[string]
```

Possible reasons:

```text
ENGINEER_REMOVED
EVIDENCE_BECAME_STALE
NEW_CRITICAL_CAPABILITY
BACKUP_VALIDATED
NEW_INDEPENDENT_EVIDENCE
CAPABILITY_RECLASSIFIED
```

If implementation time is tight, dashboard drift may be derived without persisting this entity.

---

# 33. Manager Challenge / Correction Model

The MVP should preserve the ability to challenge an assessment.

Possible internal entity:

## AssessmentChallenge

```text
challenge_id: string
capability_id: string
engineer_id: string | null

challenge_type:
  MISSING_EVIDENCE
  INCORRECT_CAPABILITY_MAPPING
  INCORRECT_ENGINEER_MAPPING
  MANAGER_ATTESTATION

comment: string
linked_evidence_ids: list[string]

created_at: datetime
```

The intended flow is:

```text
AI proposes extraction
↓
deterministic engine calculates assessment
↓
manager challenges
↓
new/corrected evidence enters model
↓
assessment is recomputed
```

Managers do not directly overwrite risk scores.

---

# 34. Manager Attestation

Manager attestation is a distinct evidence source.

Example:

```text
source_type = MANAGER_ATTESTATION
evidence_role = CONTRIBUTION or INDEPENDENT_EXECUTION
```

It should remain visibly distinguishable from artifact-derived evidence.

It may carry lower confidence than direct operational evidence.

---

# 35. Declared Ownership vs Demonstrated Coverage

Declared ownership and demonstrated capability are separate concepts.

Example:

```text
CODEOWNERS:
Payment Gateway → Jordan

Evidence:
Incident Recovery → Alex VALIDATED
```

ContinuityAI must preserve both.

Suggested internal model:

```text
DeclaredOwnership {
  system_id
  engineer_id
  source_reference
}
```

The UI may show:

```text
Declared owner: Jordan
Strongest demonstrated recovery coverage: Alex
```

The application must not silently replace declared ownership with inferred expertise.

---

# 36. Graph Model

## 36.1 Node Types

```text
PLATFORM
SYSTEM
COMPONENT
CAPABILITY
ENGINEER
EVIDENCE
```

Optional future:

```text
DOCUMENT
INCIDENT
REPOSITORY
TEAM
```

For MVP, source artifacts remain represented through Evidence nodes.

---

# 37. Graph Edge Types

```text
HAS_SYSTEM
HAS_COMPONENT
REQUIRES_CAPABILITY
DEMONSTRATES
SUPPORTED_BY
DECLARED_OWNER
```

Canonical direction:

```text
Platform  --HAS_SYSTEM-->        System
System    --HAS_COMPONENT-->     Component
Component --REQUIRES_CAPABILITY--> Capability
Engineer  --DEMONSTRATES-->      Capability
Capability/EngineerCoverage --SUPPORTED_BY--> Evidence
Engineer  --DECLARED_OWNER-->    System
```

---

# 38. Graph Storage

MVP should use a typed graph abstraction over lightweight persistence.

Recommended persistence:

```text
SQLite
```

Possible tables:

```text
platforms
systems
components
capabilities
engineers
evidence
engineer_capability_coverage
declared_ownership
simulations
mitigation_plans
mitigation_tasks
```

A dedicated graph database is not required for MVP.

---

# 39. Suggested Relational Schema

## platforms

```text
platform_id PK
name
description
```

## systems

```text
system_id PK
platform_id FK
name
description
business_criticality
```

## components

```text
component_id PK
system_id FK
name
description
```

## capabilities

```text
capability_id PK
component_id FK
name
description
operational_criticality
```

## engineers

```text
engineer_id PK
name
role
team
```

## evidence

```text
evidence_id PK
source_type
source_reference
source_title
artifact_date
engineer_id FK
system_id FK
component_id FK nullable
capability_id FK
evidence_role
evidence_strength
freshness
summary
provenance_source
provenance_record_id
```

## engineer_capability_coverage

```text
engineer_id FK
capability_id FK
readiness
freshness
evidence_confidence
last_demonstrated_at

PRIMARY KEY(engineer_id, capability_id)
```

## declared_ownership

```text
system_id FK
engineer_id FK
source_reference
```

## simulations

```text
simulation_id PK
simulation_type
engineer_id FK
scope_type
scope_id
created_at
result_json
```

## mitigation_plans

```text
plan_id PK
capability_id FK
source_engineer_id FK
selected_backup_engineer_id FK
status
created_at
approved_at
```

## mitigation_tasks

```text
task_id PK
plan_id FK
title
description
type
sequence
```

---

# 40. Public GitHub + Synthetic Enterprise Evidence

The MVP data model supports two broad classes of evidence.

## Public / real

Potential sources:

```text
GitHub commits
pull requests
issues
reviews
repository structure
CODEOWNERS
```

## Synthetic private enterprise

Potential sources:

```text
incidents
Jira-style tickets
runbooks
architecture docs
system criticality
team metadata
```

The same Evidence model should normalize both.

---

# 41. Hidden Ground Truth Model

The synthetic generator has a separate hidden model unavailable to the application.

Example:

```text
GroundTruthEngineerCapability {
  engineer_id
  capability_id
  true_readiness
}
```

Example:

```text
Alex    Incident Recovery    VALIDATED
Maria   Incident Recovery    ASSISTED
Jordan  Incident Recovery    EXPOSED
```

The generator uses this hidden model to create artifacts.

ContinuityAI receives artifacts only.

The hidden model exists only for evaluation.

---

# 42. Evaluation Domain

Suggested evaluation outputs:

```text
Knowledge reconstruction accuracy
Critical-gap detection correctness
Counterfactual simulation correctness
Backup-candidate consistency
Evidence grounding rate
Insufficient-evidence correctness
```

Do not claim real-world enterprise accuracy from synthetic evaluation.

---

# 43. Responsible-AI Boundary

ContinuityAI may analyze approved technical work artifacts.

Permitted MVP evidence:

```text
code contributions
pull requests
reviews
engineering tickets
production incidents
runbooks
technical documentation
approved technical collaboration artifacts
```

Prohibited:

```text
private direct messages
personal email
keyboard activity
mouse activity
screen monitoring
working hours
location
online presence
sentiment
personality
non-technical employee behavior
```

---

# 44. Employment-Decision Boundary

ContinuityAI must not produce:

```text
hire recommendation
termination recommendation
layoff recommendation
promotion recommendation
bonus recommendation
salary recommendation
employee value ranking
performance-review score
```

Permitted:

```text
technical capability evidence
technical coverage gaps
technical backup candidate comparison
knowledge-transfer plan
```

Final staffing decisions remain human decisions.

---

# 45. Language Rules

Preferred phrases:

```text
demonstrated capability
available evidence
technical coverage
evidence-backed assessment
no qualifying evidence found
strongest technical candidate
continuity gap
knowledge concentration
```

Avoid:

```text
critical employee
irreplaceable person
low-value engineer
weak engineer
cannot perform
best employee
employee risk score
```

---

# 46. Example Domain Walkthrough

Consider:

```text
Payments Platform
  → Payment Gateway
    → Gateway Integration
      → Incident Recovery
```

Coverage:

```text
Alex    VALIDATED
Maria   ASSISTED
Jordan  EXPOSED
```

Evidence:

```text
Alex
- INC-184 independent recovery
- INC-221 independent recovery
- PR-442 recovery implementation
- DOC-17 runbook

Maria
- INC-221 assisted recovery
- deployment work

Jordan
- PR review
- feature implementation
```

Current state may be:

```text
Incident Recovery
Exposure: DEGRADED
Risk: 72
Confidence: HIGH
```

Simulation:

```text
ENGINEER_UNAVAILABLE: Alex
```

Remaining:

```text
Maria ASSISTED
Jordan EXPOSED
```

Recomputed:

```text
Exposure: CRITICAL_GAP
Risk: 93
```

Candidate comparison:

```text
Maria
Technical overlap: HIGH

Jordan
Technical overlap: MEDIUM
```

Manager selects Maria.

Generated plan:

```text
1. Review recovery architecture.
2. Review historical P1 incidents.
3. Practice provider failover in staging.
4. Run independent recovery drill.
5. Update runbook.
```

Manager approves.

That is the primary end-to-end domain path of the MVP.

---

# 47. Domain Invariants Summary

The following are non-negotiable for MVP.

1. Capability is the primary unit of continuity risk.
2. Evidence supports engineer-capability relationships.
3. AI extracts semantic evidence but does not directly assign readiness or risk.
4. Readiness is deterministic and explainable.
5. Risk is deterministic and explainable.
6. Risk is not probability.
7. Evidence confidence is separate from risk.
8. Absence of evidence is not proof of inability.
9. Simulation removes capability coverage, not people from organizational records.
10. Backup comparison evaluates technical evidence only.
11. Managers make staffing decisions.
12. Mitigation plans target missing capabilities.
13. Platform does not receive an independent numeric risk score in MVP.
14. Frontend does not calculate domain intelligence.
15. Every important assessment must be traceable to evidence.
16. The application may return `INSUFFICIENT_EVIDENCE`.
17. Employee-worth scoring is prohibited.
18. Private-surveillance data is prohibited.

---

# 48. Phase 0 Freeze Checklist

Before Phase 1 starts, both developers should confirm:

- [ ] Core hierarchy is accepted.
- [ ] Enums are accepted.
- [ ] Typed IDs are accepted.
- [ ] Capability is accepted as primary continuity unit.
- [ ] EngineerCapabilityCoverage semantics are accepted.
- [ ] Evidence fields are accepted.
- [ ] AI extraction boundary is accepted.
- [ ] Readiness semantics are accepted.
- [ ] CapabilityExposure semantics are accepted.
- [ ] Continuity Risk Index semantics are accepted.
- [ ] Simulation semantics are accepted.
- [ ] Candidate-comparison semantics are accepted.
- [ ] Mitigation-plan semantics are accepted.
- [ ] Graph node/edge types are accepted.
- [ ] Responsible-AI restrictions are accepted.
- [ ] Employment-decision restrictions are accepted.

Once both developers approve these items, changes should follow the Phase 0 change-control process rather than being made silently during implementation.

---

# 49. Next Implementation Step

After Phase 0 is frozen, Phase 1 should create:

```text
backend/
  app/
    api/
    models/
    schemas/
    services/
    graph/
    evidence/
    continuity/
    simulation/
    recommendation/

frontend/
  app/
  components/
  lib/
  mocks/
  types/
```

The first technical objective is not to build the AI model.

It is to prove that both developers can independently implement against the same contract:

```text
Frontend mock JSON
        │
        │ same DTO
        ▼
API_CONTRACT.md
        ▲
        │
        │ same DTO
Backend Pydantic model
```

Once that boundary works, the mock backend logic can progressively be replaced with real evidence, graph, readiness, and simulation behavior without forcing a frontend rewrite.
