# ContinuityAI API Contract

**Version:** 1.0.0  
**Status:** Phase 0 Frozen  
**API Base Path:** `/api/v1`  
**Primary Consumers:** Next.js frontend, automated tests, demo fixtures  
**Backend:** FastAPI / Python  
**Frontend:** Next.js / React / TypeScript

---

## 1. Purpose

This document is the implementation contract between the ContinuityAI frontend and backend teams.

It defines:

- the MVP domain objects exposed through the API;
- the exact enums both teams must use;
- the 10 MVP endpoints;
- request and response payloads;
- ownership of derived fields;
- error behavior;
- simulation semantics;
- graph DTO rules;
- backup-candidate recommendation rules;
- mitigation-plan rules; and
- change-control expectations during parallel development.

The goal is to allow the frontend and backend to be developed simultaneously without either team waiting for the other.

> **Contract rule:** The frontend renders and interacts with data. The backend owns intelligence, graph state, readiness, exposure, risk, confidence, simulation outcomes, candidate comparison, and mitigation generation.

---

# 2. Frozen Phase 0 Decisions

The following decisions are frozen for the MVP.

## 2.1 Platform risk

ContinuityAI does **not** calculate a synthetic platform-level risk score.

A platform summary exposes:

- highest system Continuity Risk Index;
- total critical coverage gaps;
- system count; and
- knowledge-drift status.

This avoids creating an arbitrary second aggregation formula.

## 2.2 Simulation model

The MVP supports one simulation semantic only:

`ENGINEER_UNAVAILABLE`

The simulation temporarily removes an engineer's demonstrated capability coverage from the selected scope and recalculates capability/system continuity exposure.

The MVP does **not** implement different mathematical behavior for resignation, vacation, illness, or reassignment.

## 2.3 Backup candidate output

The backend may return up to **3 technical backup candidates**.

Each candidate includes:

- technical-overlap classification;
- strengths;
- capability gaps;
- evidence confidence; and
- supporting evidence references where applicable.

The API does **not** make the staffing decision. The manager selects the candidate.

## 2.4 Graph transport

The backend returns a dedicated graph DTO containing typed `nodes` and `edges`.

The frontend does not reconstruct graph relationships from unrelated domain responses.

---

# 3. Architectural Ownership

## 3.1 Backend owns

The backend is the source of truth for:

- AI semantic artifact extraction;
- system/component/capability normalization;
- knowledge-graph construction;
- evidence strength;
- evidence freshness;
- evidence aggregation;
- engineer-capability readiness;
- evidence confidence;
- capability exposure;
- Continuity Risk Index;
- critical coverage-gap counts;
- knowledge-drift status;
- counterfactual simulation;
- technical backup-candidate comparison;
- AI-generated mitigation plans; and
- mitigation-plan state.

The frontend must not duplicate or recalculate these values.

## 3.2 Frontend owns

The frontend owns:

- rendering;
- navigation;
- interaction state;
- filters;
- sorting;
- graph layout;
- charts and visualizations;
- selected engineer/candidate state before requests are submitted;
- confirmation modals; and
- display formatting.

The frontend may derive purely presentational values such as:

- display labels;
- sorted lists;
- abbreviated text;
- percentages used only for progress bars when the API already supplied the underlying value.

## 3.3 Human owns

The human manager owns:

- confirming business criticality;
- challenging incorrect assessments;
- selecting a backup candidate;
- editing a proposed mitigation plan where allowed; and
- approving a mitigation plan.

ContinuityAI provides evidence-backed decision support, not autonomous staffing decisions.

---

# 4. Naming and Serialization Standards

## 4.1 JSON casing

All JSON keys use `snake_case`.

Example:

```json
{
  "continuity_risk_index": 93,
  "evidence_confidence": "HIGH"
}
```

## 4.2 IDs

Names must never be used as primary identifiers.

IDs are stable strings and should be human-debuggable where practical.

Recommended prefixes:

```text
platform_
system_
component_
cap_
eng_
evidence_
sim_
plan_
task_
```

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
```

Implementation note: UUIDs are allowed internally, but API responses should remain stable for seeded demo fixtures.

## 4.3 Dates

Dates/timestamps must use ISO-8601.

Examples:

```text
2026-05-14
2026-05-14T19:22:11Z
```

## 4.4 Nullability

Use `null` only when the concept exists but the value is unknown.

Prefer an explicit enum state such as `INSUFFICIENT_EVIDENCE` where the state itself is meaningful.

---

# 5. Shared Enums

These enum values are part of the contract and must not be changed independently by either team.

## 5.1 BusinessCriticality

```text
LOW
MEDIUM
HIGH
CRITICAL
```

## 5.2 OperationalCriticality

```text
LOW
MEDIUM
HIGH
CRITICAL
```

## 5.3 ReadinessLevel

```text
NONE
EXPOSED
ASSISTED
PRACTICED
VALIDATED
```

Interpretation:

| Value | Meaning |
|---|---|
| `NONE` | No qualifying evidence of capability interaction. |
| `EXPOSED` | Evidence of review, observation, discussion, or limited interaction. |
| `ASSISTED` | Participated in execution with another engineer or under guidance. |
| `PRACTICED` | Performed the capability hands-on without significant support, but evidence is limited to controlled or lower-risk contexts, or lacks the repetition, source diversity, or recency required for `VALIDATED`. |
| `VALIDATED` | Strong, diverse, current, repeated evidence of independent capability execution. |

## 5.4 CapabilityExposure

```text
COVERED
DEGRADED
CRITICAL_GAP
INSUFFICIENT_EVIDENCE
```

Interpretation:

| Value | Meaning |
|---|---|
| `COVERED` | Sufficient demonstrated coverage remains. |
| `DEGRADED` | Coverage exists but redundancy/readiness has weakened. |
| `CRITICAL_GAP` | Critical capability lacks adequate demonstrated coverage. |
| `INSUFFICIENT_EVIDENCE` | Available evidence is too weak/incomplete for a responsible assessment. |

## 5.5 EvidenceStrength

```text
WEAK
MODERATE
STRONG
```

## 5.6 EvidenceConfidence

```text
LOW
MEDIUM
HIGH
```

This is **not** a probability.

## 5.7 Freshness

```text
FRESH
AGING
STALE
```

Freshness is determined by the backend from evidence age and, where supported, relevant component change since the artifact was created.

## 5.8 KnowledgeDriftStatus

```text
NEW_RISK
RISK_INCREASED
STABLE
RISK_REDUCED
```

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

The MVP may populate only a subset of these.

## 5.10 EvidenceRole

```text
EXPOSURE
CONTRIBUTION
ASSISTED_EXECUTION
INDEPENDENT_EXECUTION
KNOWLEDGE_CAPTURE
```

Typical examples:

| Artifact behavior | Role |
|---|---|
| Reviewed relevant PR | `EXPOSURE` |
| Implemented related feature | `CONTRIBUTION` |
| Assisted P1 recovery | `ASSISTED_EXECUTION` |
| Independently resolved P1 outage | `INDEPENDENT_EXECUTION` |
| Authored recovery runbook | `KNOWLEDGE_CAPTURE` |

## 5.11 GraphNodeType

```text
PLATFORM
SYSTEM
COMPONENT
CAPABILITY
ENGINEER
EVIDENCE
```

## 5.12 GraphEdgeType

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
Platform  --HAS_SYSTEM-->           System
System    --HAS_COMPONENT-->        Component
Component --REQUIRES_CAPABILITY-->  Capability
Engineer  --DEMONSTRATES-->         Capability
Coverage  --SUPPORTED_BY-->         Evidence
Engineer  --DECLARED_OWNER-->       System
```

## 5.13 SimulationType

```text
ENGINEER_UNAVAILABLE
```

## 5.14 SimulationScopeType

```text
SYSTEM
PLATFORM
```

For the hero MVP workflow, `SYSTEM` is the expected scope.

## 5.15 TechnicalOverlap

```text
LOW
MEDIUM
HIGH
```

## 5.16 MitigationPlanStatus

```text
DRAFT
APPROVED
```

## 5.17 MitigationTaskType

```text
KNOWLEDGE_REVIEW
SHADOWING
PRACTICE
RECOVERY_DRILL
DOCUMENTATION
ARCHITECTURE_REVIEW
```

## 5.18 ContinuityRiskClass

```text
LOW
MODERATE
HIGH
CRITICAL
```

The class is the authoritative rule-engine output; `continuity_risk_index` is the derived
comparison number. Bands are `LOW 0–39`, `MODERATE 40–59`, `HIGH 60–79`, `CRITICAL 80–100`, and
the index is clamped to the band of its class so modifiers cannot silently reclassify.

The frontend must not derive the class from the index.

---

# 6. Core DTOs

These DTOs describe the external API contract. Internal persistence models may differ.

---

## 6.1 PlatformSummary

```json
{
  "platform_id": "platform_payments",
  "name": "Payments Platform",
  "description": "Customer payment and transaction services",
  "system_count": 3,
  "critical_gap_count": 1,
  "single_expert_dependency_count": 4,
  "highest_system_risk_index": 74,
  "drift_status": "NEW_RISK"
}
```

Required fields:

- `platform_id: string`
- `name: string`
- `description: string | null`
- `system_count: integer >= 0`
- `critical_gap_count: integer >= 0`
- `single_expert_dependency_count: integer >= 0`
- `highest_system_risk_index: integer 0..100 | null`
- `drift_status: KnowledgeDriftStatus`

`highest_system_risk_index` may be `null` if the platform contains no assessable systems.

`single_expert_dependency_count` is the number of capabilities under the platform whose adequate
coverage is exactly one engineer — the "one person away from a gap" count. Added by DEC-17 to close
GAP-01; the dashboard card had no field carrying this number.

Three things it is not, each of which would produce a different number:

- **Not** `critical_gap_count`. That counts capabilities with *no* adequate engineer.
- **Not** derivable from `degraded_capability_count`. Under DEC-07 a lower-criticality capability
  with zero adequate engineers is `DEGRADED` rather than a critical gap, so the degraded count
  includes both the one-expert and the no-expert cases.
- **Not** a count of engineers. Two capabilities each held solely by Alex count as two.

"Adequate" means readiness `PRACTICED` or `VALIDATED` with evidence that is not `STALE`, which is the
same definition behind the `SOLE_EXPERT_CAPABILITY` and `MULTIPLE_SOLE_EXPERT_CAPABILITIES` reason
codes in section 12.1 — deliberately, so a platform card cannot disagree with the reason codes shown
on the systems beneath it.

---

## 6.2 SystemSummary

```json
{
  "system_id": "system_payment_gateway",
  "platform_id": "platform_payments",
  "name": "Payment Gateway",
  "description": "Processes customer payment transactions",
  "business_criticality": "CRITICAL",
  "continuity_risk_index": 74,
  "continuity_risk_class": "HIGH",
  "exposure": "DEGRADED",
  "evidence_confidence": "HIGH",
  "critical_gap_count": 0,
  "degraded_capability_count": 2,
  "covered_capability_count": 3,
  "insufficient_evidence_count": 0,
  "drift_status": "NEW_RISK"
}
```

The risk index is an **index**, not a probability of failure.

---

## 6.3 SystemDetail

```json
{
  "system_id": "system_payment_gateway",
  "platform_id": "platform_payments",
  "name": "Payment Gateway",
  "description": "Processes customer payment transactions",
  "business_criticality": "CRITICAL",
  "continuity_risk_index": 74,
  "continuity_risk_class": "HIGH",
  "exposure": "DEGRADED",
  "evidence_confidence": "HIGH",
  "critical_gap_count": 0,
  "degraded_capability_count": 2,
  "covered_capability_count": 3,
  "insufficient_evidence_count": 0,
  "drift_status": "NEW_RISK",
  "criticality_source": "HUMAN_CONFIRMED",
  "rules_triggered": [
    "CRITICAL_CAPABILITY_DEGRADED",
    "MULTIPLE_SOLE_EXPERT_CAPABILITIES"
  ],
  "declared_ownership": {
    "engineer_id": "eng_jordan_lee",
    "name": "Jordan Lee",
    "source": "CODEOWNERS",
    "mismatch_detected": true
  },
  "components": [
    {
      "component_id": "component_gateway_integration",
      "name": "Gateway Integration",
      "description": "Handles payment-provider connectivity",
      "capability_ids": [
        "cap_incident_recovery",
        "cap_provider_failover",
        "cap_certificate_management"
      ]
    }
  ]
}
```

---

## 6.4 EngineerCoverage

```json
{
  "engineer_id": "eng_alex_chen",
  "name": "Alex Chen",
  "readiness": "VALIDATED",
  "freshness": "FRESH",
  "evidence_confidence": "HIGH",
  "last_demonstrated_at": "2026-05-14"
}
```

---

## 6.5 CapabilityDetail

```json
{
  "capability_id": "cap_incident_recovery",
  "component_id": "component_gateway_integration",
  "system_id": "system_payment_gateway",
  "name": "Incident Recovery",
  "description": "Ability to diagnose and restore Payment Gateway operation during production incidents",
  "operational_criticality": "CRITICAL",
  "exposure": "DEGRADED",
  "continuity_risk_index": 72,
  "continuity_risk_class": "HIGH",
  "evidence_confidence": "HIGH",
  "rules_triggered": [
    "CRITICAL_CAPABILITY",
    "SINGLE_VALIDATED_ENGINEER",
    "NO_PRACTICED_OR_VALIDATED_BACKUP"
  ],
  "primary_engineer": {
    "engineer_id": "eng_alex_chen",
    "name": "Alex Chen",
    "readiness": "VALIDATED"
  },
  "best_remaining_coverage": {
    "engineer_id": "eng_maria_gomez",
    "name": "Maria Gomez",
    "readiness": "ASSISTED"
  },
  "engineer_coverage": [
    {
      "engineer_id": "eng_alex_chen",
      "name": "Alex Chen",
      "readiness": "VALIDATED",
      "freshness": "FRESH",
      "evidence_confidence": "HIGH"
    },
    {
      "engineer_id": "eng_maria_gomez",
      "name": "Maria Gomez",
      "readiness": "ASSISTED",
      "freshness": "FRESH",
      "evidence_confidence": "MEDIUM"
    },
    {
      "engineer_id": "eng_jordan_lee",
      "name": "Jordan Lee",
      "readiness": "EXPOSED",
      "freshness": "AGING",
      "evidence_confidence": "MEDIUM"
    }
  ]
}
```

Rules:

- `primary_engineer` may be `null` when evidence is insufficient.
- `best_remaining_coverage` may be `null` when no qualifying alternative coverage exists.
- `continuity_risk_index` may be `null` when exposure is `INSUFFICIENT_EVIDENCE`.

---

## 6.6 EngineerSummary

```json
{
  "engineer_id": "eng_alex_chen",
  "name": "Alex Chen",
  "role": "Senior Payments Engineer",
  "team": "Payments Engineering"
}
```

The MVP must not expose fields such as:

- productivity score;
- employee value score;
- layoff suitability;
- bonus recommendation;
- sentiment score; or
- hours worked.

---

## 6.7 EvidenceRecord

```json
{
  "evidence_id": "evidence_inc_184",
  "source_type": "INCIDENT",
  "source_reference": "INC-184",
  "source_title": "P1 Payment Gateway Provider Failure",
  "artifact_date": "2026-05-14",
  "engineer_id": "eng_alex_chen",
  "system_id": "system_payment_gateway",
  "component_id": "component_gateway_integration",
  "capability_id": "cap_incident_recovery",
  "evidence_role": "INDEPENDENT_EXECUTION",
  "evidence_strength": "STRONG",
  "summary": "Alex diagnosed failed provider routing and restored payment processing.",
  "freshness": "FRESH",
  "provenance": {
    "source": "synthetic_incident_dataset",
    "record_id": "INC-184",
    "source_url": null
  }
}
```

### Evidence contract rule

Every user-visible expertise/readiness claim must be traceable to one or more `EvidenceRecord` objects or explicitly state that evidence is insufficient.

---

## 6.8 GraphNode

```json
{
  "id": "cap_incident_recovery",
  "type": "CAPABILITY",
  "label": "Incident Recovery",
  "status": "DEGRADED",
  "metadata": {
    "operational_criticality": "CRITICAL"
  }
}
```

`status` is optional and context dependent.

The frontend must not depend on arbitrary metadata fields for core functionality; only documented metadata may be used.

---

## 6.9 GraphEdge

```json
{
  "source": "eng_alex_chen",
  "target": "cap_incident_recovery",
  "type": "DEMONSTRATES",
  "metadata": {
    "readiness": "VALIDATED",
    "freshness": "FRESH",
    "evidence_confidence": "HIGH"
  }
}
```

---

## 6.10 GraphResponse

```json
{
  "scope": {
    "type": "SYSTEM",
    "id": "system_payment_gateway",
    "name": "Payment Gateway"
  },
  "nodes": [
    {
      "id": "system_payment_gateway",
      "type": "SYSTEM",
      "label": "Payment Gateway",
      "status": "DEGRADED",
      "metadata": {}
    },
    {
      "id": "component_gateway_integration",
      "type": "COMPONENT",
      "label": "Gateway Integration",
      "metadata": {}
    },
    {
      "id": "cap_incident_recovery",
      "type": "CAPABILITY",
      "label": "Incident Recovery",
      "status": "DEGRADED",
      "metadata": {
        "operational_criticality": "CRITICAL"
      }
    },
    {
      "id": "eng_alex_chen",
      "type": "ENGINEER",
      "label": "Alex Chen",
      "metadata": {}
    }
  ],
  "edges": [
    {
      "source": "system_payment_gateway",
      "target": "component_gateway_integration",
      "type": "HAS_COMPONENT",
      "metadata": {}
    },
    {
      "source": "component_gateway_integration",
      "target": "cap_incident_recovery",
      "type": "REQUIRES_CAPABILITY",
      "metadata": {}
    },
    {
      "source": "eng_alex_chen",
      "target": "cap_incident_recovery",
      "type": "DEMONSTRATES",
      "metadata": {
        "readiness": "VALIDATED"
      }
    }
  ]
}
```

---

# 7. Endpoint Summary

The MVP API contains exactly these 10 endpoints unless both developers explicitly agree to amend the contract.

| # | Method | Endpoint | Purpose |
|---|---|---|---|
| 1 | GET | `/api/v1/platforms` | Portfolio dashboard platform summaries |
| 2 | GET | `/api/v1/platforms/{platform_id}/systems` | Systems within a platform |
| 3 | GET | `/api/v1/systems/{system_id}` | System detail |
| 4 | GET | `/api/v1/systems/{system_id}/graph` | Contextual typed graph |
| 5 | GET | `/api/v1/capabilities/{capability_id}` | Capability detail/readiness |
| 6 | GET | `/api/v1/capabilities/{capability_id}/evidence` | Provenance/evidence |
| 7 | POST | `/api/v1/simulations` | Engineer-unavailable simulation |
| 8 | POST | `/api/v1/recommendations/backup-candidates` | Compare technical backup candidates |
| 9 | POST | `/api/v1/mitigation-plans` | Generate candidate-specific mitigation plan |
| 10 | POST | `/api/v1/mitigation-plans/{plan_id}/approve` | Human approval of draft plan |

---

# 8. Endpoint Contracts

---

## 8.1 GET `/api/v1/platforms`

### Purpose

Populate the portfolio dashboard.

### Request

No body.

Optional query parameters for MVP: none.

### Success response

`200 OK`

```json
{
  "platforms": [
    {
      "platform_id": "platform_payments",
      "name": "Payments Platform",
      "description": "Customer payment and transaction services",
      "system_count": 3,
      "critical_gap_count": 1,
      "single_expert_dependency_count": 4,
      "highest_system_risk_index": 74,
      "drift_status": "NEW_RISK"
    },
    {
      "platform_id": "platform_identity",
      "name": "Identity Platform",
      "description": "Authentication and authorization services",
      "system_count": 2,
      "critical_gap_count": 1,
      "single_expert_dependency_count": 2,
      "highest_system_risk_index": 68,
      "drift_status": "STABLE"
    }
  ]
}
```

### Frontend use

- platform cards/rows;
- system count;
- critical-gap count;
- knowledge-drift indicator;
- highest risk indicator.

---

## 8.2 GET `/api/v1/platforms/{platform_id}/systems`

### Purpose

Populate system rows under the selected portfolio/platform.

### Success response

`200 OK`

```json
{
  "platform": {
    "platform_id": "platform_payments",
    "name": "Payments Platform"
  },
  "systems": [
    {
      "system_id": "system_payment_gateway",
      "platform_id": "platform_payments",
      "name": "Payment Gateway",
      "description": "Processes customer payment transactions",
      "business_criticality": "CRITICAL",
      "continuity_risk_index": 74,
      "continuity_risk_class": "HIGH",
      "exposure": "DEGRADED",
      "evidence_confidence": "HIGH",
      "critical_gap_count": 0,
      "degraded_capability_count": 2,
      "covered_capability_count": 3,
      "insufficient_evidence_count": 0,
      "drift_status": "NEW_RISK"
    }
  ]
}
```

### Errors

- `404 NOT_FOUND` for unknown platform.

---

## 8.3 GET `/api/v1/systems/{system_id}`

### Purpose

Populate the system-detail page.

### Success response

`200 OK`

Returns a `SystemDetail` object.

Example:

```json
{
  "system_id": "system_payment_gateway",
  "platform_id": "platform_payments",
  "name": "Payment Gateway",
  "description": "Processes customer payment transactions",
  "business_criticality": "CRITICAL",
  "continuity_risk_index": 74,
  "continuity_risk_class": "HIGH",
  "exposure": "DEGRADED",
  "evidence_confidence": "HIGH",
  "critical_gap_count": 0,
  "degraded_capability_count": 2,
  "covered_capability_count": 3,
  "insufficient_evidence_count": 0,
  "drift_status": "NEW_RISK",
  "criticality_source": "HUMAN_CONFIRMED",
  "rules_triggered": [
    "CRITICAL_CAPABILITY_DEGRADED",
    "MULTIPLE_SOLE_EXPERT_CAPABILITIES"
  ],
  "declared_ownership": {
    "engineer_id": "eng_jordan_lee",
    "name": "Jordan Lee",
    "source": "CODEOWNERS",
    "mismatch_detected": true
  },
  "components": [
    {
      "component_id": "component_gateway_integration",
      "name": "Gateway Integration",
      "description": "Handles payment-provider connectivity",
      "capability_ids": [
        "cap_incident_recovery",
        "cap_provider_failover"
      ]
    }
  ]
}
```

### Errors

- `404 NOT_FOUND`.

---

## 8.4 GET `/api/v1/systems/{system_id}/graph`

### Purpose

Provide a contextual graph DTO for system visualization.

### Query parameters

Optional:

```text
focus_capability_id=<capability_id>
```

If supplied, the backend may limit the graph to the local neighborhood required for the focused capability.

### Success response

`200 OK`

Returns `GraphResponse`.

### Contract rule

The frontend may choose the graph layout but must not invent or infer additional relationships.

### Errors

- `404 NOT_FOUND`.
- `500 GRAPH_INCONSISTENCY` if required graph relationships are invalid.

---

## 8.5 GET `/api/v1/capabilities/{capability_id}`

### Purpose

Populate capability-level continuity/readiness detail.

### Success response

`200 OK`

Returns `CapabilityDetail`.

### Errors

- `404 NOT_FOUND`.

---

## 8.6 GET `/api/v1/capabilities/{capability_id}/evidence`

### Purpose

Populate the provenance-first `Why?` view.

### Query parameters

Optional:

```text
engineer_id=<engineer_id>
```

If supplied, filter evidence to one engineer.

### Success response

`200 OK`

```json
{
  "capability": {
    "capability_id": "cap_incident_recovery",
    "name": "Incident Recovery"
  },
  "assessment": {
    "exposure": "DEGRADED",
    "evidence_confidence": "HIGH",
    "rules_triggered": [
      "CRITICAL_CAPABILITY",
      "SINGLE_VALIDATED_ENGINEER",
      "NO_PRACTICED_OR_VALIDATED_BACKUP"
    ]
  },
  "evidence": [
    {
      "evidence_id": "evidence_inc_184",
      "source_type": "INCIDENT",
      "source_reference": "INC-184",
      "source_title": "P1 Payment Gateway Provider Failure",
      "artifact_date": "2026-05-14",
      "engineer_id": "eng_alex_chen",
      "system_id": "system_payment_gateway",
      "component_id": "component_gateway_integration",
      "capability_id": "cap_incident_recovery",
      "evidence_role": "INDEPENDENT_EXECUTION",
      "evidence_strength": "STRONG",
      "summary": "Alex diagnosed failed provider routing and restored payment processing.",
      "freshness": "FRESH",
      "provenance": {
        "source": "synthetic_incident_dataset",
        "record_id": "INC-184",
        "source_url": null
      }
    }
  ],
  "missing_evidence": [
    {
      "engineer_id": "eng_jordan_lee",
      "engineer_name": "Jordan Lee",
      "description": "No qualifying independent production recovery evidence found."
    }
  ],
  "conflicting_evidence": [],
  "declared_vs_demonstrated": {
    "declared_owner": {
      "engineer_id": "eng_jordan_lee",
      "name": "Jordan Lee",
      "source": "CODEOWNERS"
    },
    "strongest_demonstrated_coverage": {
      "engineer_id": "eng_alex_chen",
      "name": "Alex Chen"
    },
    "mismatch_detected": true
  }
}
```

### Important wording rule

The API should use language such as:

`No qualifying evidence found`

not:

`Jordan cannot perform this capability`.

Absence of evidence is not proof of inability.

---

## 8.7 POST `/api/v1/simulations`

### Purpose

Run the counterfactual engineer-unavailability simulation.

### Request

```json
{
  "simulation_type": "ENGINEER_UNAVAILABLE",
  "engineer_id": "eng_alex_chen",
  "scope": {
    "type": "SYSTEM",
    "id": "system_payment_gateway"
  }
}
```

### Backend behavior

The backend must:

1. resolve the selected engineer and scope;
2. copy/overlay graph state without mutating baseline state;
3. temporarily remove the engineer's capability-coverage relationships within scope;
4. determine remaining readiness per capability;
5. rerun capability exposure rules;
6. aggregate results to system state;
7. calculate before/after Continuity Risk Index;
8. return deterministic impact details;
9. optionally generate a grounded natural-language summary.

### Success response

`200 OK`

```json
{
  "simulation_id": "sim_001",
  "simulation_type": "ENGINEER_UNAVAILABLE",
  "engineer": {
    "engineer_id": "eng_alex_chen",
    "name": "Alex Chen"
  },
  "scope": {
    "type": "SYSTEM",
    "id": "system_payment_gateway",
    "name": "Payment Gateway"
  },
  "before": {
    "continuity_risk_index": 74,
    "continuity_risk_class": "HIGH",
    "critical_gap_count": 0,
    "degraded_capability_count": 2,
    "covered_capability_count": 3
  },
  "after": {
    "continuity_risk_index": 93,
    "continuity_risk_class": "CRITICAL",
    "critical_gap_count": 2,
    "degraded_capability_count": 1,
    "covered_capability_count": 2
  },
  "capability_impacts": [
    {
      "capability_id": "cap_incident_recovery",
      "name": "Incident Recovery",
      "operational_criticality": "CRITICAL",
      "before": "DEGRADED",
      "after": "CRITICAL_GAP",
      "remaining_best_readiness": "ASSISTED"
    },
    {
      "capability_id": "cap_provider_failover",
      "name": "Provider Failover",
      "operational_criticality": "HIGH",
      "before": "COVERED",
      "after": "DEGRADED",
      "remaining_best_readiness": "PRACTICED"
    },
    {
      "capability_id": "cap_certificate_management",
      "name": "Certificate Management",
      "operational_criticality": "CRITICAL",
      "before": "DEGRADED",
      "after": "CRITICAL_GAP",
      "remaining_best_readiness": "EXPOSED"
    },
    {
      "capability_id": "cap_retry_logic",
      "name": "Retry Logic",
      "operational_criticality": "HIGH",
      "before": "COVERED",
      "after": "COVERED",
      "remaining_best_readiness": "VALIDATED"
    },
    {
      "capability_id": "cap_monitoring",
      "name": "Monitoring",
      "operational_criticality": "MEDIUM",
      "before": "COVERED",
      "after": "COVERED",
      "remaining_best_readiness": "VALIDATED"
    }
  ],
  "summary": "Alex's unavailability creates two critical capability gaps in Payment Gateway while Retry Logic remains covered."
}
```

### Contract rule

`summary` may be AI-generated. All impact fields are backend deterministic outputs.

### Errors

- `404 NOT_FOUND`
- `422 VALIDATION_ERROR`
- `409 INSUFFICIENT_EVIDENCE` where the baseline graph cannot support a responsible simulation
- `500 SIMULATION_FAILED`

---

## 8.8 POST `/api/v1/recommendations/backup-candidates`

### Purpose

Compare up to 3 technical backup candidates for one exposed capability.

### Request

```json
{
  "simulation_id": "sim_001",
  "capability_id": "cap_incident_recovery",
  "limit": 3
}
```

`limit` defaults to 3 and must not exceed 3 in MVP.

### Backend behavior

Candidate comparison may consider:

- demonstrated adjacent capabilities;
- current readiness for the target capability;
- evidence freshness;
- evidence strength/diversity;
- technical overlap with the missing capability; and
- relevant system/component familiarity.

Candidate comparison must **not** consider unless added in a future version:

- employee workload;
- compensation;
- performance-review rating;
- career goals;
- personal availability;
- protected characteristics;
- productivity scores;
- sentiment/personality; or
- layoff suitability.

### Success response

`200 OK`

```json
{
  "capability": {
    "capability_id": "cap_incident_recovery",
    "name": "Incident Recovery"
  },
  "candidates": [
    {
      "engineer_id": "eng_maria_gomez",
      "name": "Maria Gomez",
      "technical_overlap": "HIGH",
      "strengths": [
        "Production deployment",
        "Infrastructure recovery",
        "Assisted Payment Gateway recovery"
      ],
      "gaps": [
        "Independent Payment Gateway recovery",
        "Provider failover execution"
      ],
      "evidence_confidence": "HIGH",
      "supporting_evidence_ids": [
        "evidence_inc_230",
        "evidence_pr_402"
      ]
    },
    {
      "engineer_id": "eng_jordan_lee",
      "name": "Jordan Lee",
      "technical_overlap": "MEDIUM",
      "strengths": [
        "Payment Gateway development",
        "Retry architecture"
      ],
      "gaps": [
        "Independent production recovery",
        "Provider failover execution"
      ],
      "evidence_confidence": "MEDIUM",
      "supporting_evidence_ids": [
        "evidence_pr_391"
      ]
    }
  ],
  "disclaimer": "Technical overlap only. Workload, availability, staffing priorities, and career goals are not evaluated."
}
```

### No-candidate response

Still return `200 OK` when analysis succeeds but no suitable candidate exists:

```json
{
  "capability": {
    "capability_id": "cap_incident_recovery",
    "name": "Incident Recovery"
  },
  "candidates": [],
  "message": "No strong internal technical backup candidate was identified from the available evidence.",
  "disclaimer": "Technical overlap only. Workload, availability, staffing priorities, and career goals are not evaluated."
}
```

---

## 8.9 POST `/api/v1/mitigation-plans`

### Purpose

Generate a personalized knowledge-transfer plan after the manager selects a technical candidate.

### Request

```json
{
  "capability_id": "cap_incident_recovery",
  "primary_engineer_id": "eng_alex_chen",
  "selected_backup_engineer_id": "eng_maria_gomez",
  "simulation_id": "sim_001"
}
```

### Backend behavior

The plan generator may use AI, but the prompt/context must be grounded in:

- target capability;
- existing evidence;
- selected candidate strengths;
- selected candidate gaps;
- relevant historical incidents/documents; and
- stated readiness target.

The plan should not invent unavailable systems, tools, incidents, or expertise.

### Success response

`201 Created`

```json
{
  "plan_id": "plan_001",
  "status": "DRAFT",
  "capability": {
    "capability_id": "cap_incident_recovery",
    "name": "Incident Recovery"
  },
  "source_engineer": {
    "engineer_id": "eng_alex_chen",
    "name": "Alex Chen"
  },
  "backup_candidate": {
    "engineer_id": "eng_maria_gomez",
    "name": "Maria Gomez"
  },
  "target_readiness": "PRACTICED",
  "tasks": [
    {
      "task_id": "task_001",
      "title": "Review Payment Gateway recovery architecture",
      "description": "Review the recovery architecture, current runbook, and historical incidents INC-184 and INC-221.",
      "type": "KNOWLEDGE_REVIEW",
      "acceptance_criteria": [
        "Review current recovery architecture",
        "Review two historical P1 recovery incidents",
        "Document unresolved questions"
      ],
      "linked_evidence_ids": [
        "evidence_inc_184",
        "evidence_inc_221"
      ]
    },
    {
      "task_id": "task_002",
      "title": "Shadow a Payment Gateway recovery exercise",
      "description": "Observe the recovery workflow and identify decision points used during restoration.",
      "type": "SHADOWING",
      "acceptance_criteria": [
        "Attend guided recovery exercise",
        "Identify major recovery decision points"
      ]
    },
    {
      "task_id": "task_003",
      "title": "Run provider failover in staging",
      "description": "Perform a controlled provider failover and restore normal routing.",
      "type": "PRACTICE",
      "acceptance_criteria": [
        "Execute failover in staging",
        "Verify restored transaction flow",
        "Document any undocumented steps"
      ]
    },
    {
      "task_id": "task_004",
      "title": "Update the recovery runbook",
      "description": "Capture missing recovery knowledge discovered during the exercise.",
      "type": "DOCUMENTATION",
      "acceptance_criteria": [
        "Add missing recovery steps",
        "Add rollback guidance",
        "Submit runbook for review"
      ]
    }
  ]
}
```

### Contract rule

Creating a mitigation plan does **not** change engineer readiness or continuity risk in the MVP.

The MVP does not claim that training has been completed simply because a plan was generated.

---

## 8.10 POST `/api/v1/mitigation-plans/{plan_id}/approve`

### Purpose

Record explicit human approval of a draft plan.

### Request

```json
{
  "approved_by": "eng_manager_sarah",
  "tasks": [ ]
}
```

For the hackathon, authentication/identity may be simplified; this field may be a seeded manager identifier.

`tasks` is optional. When omitted, the plan is approved exactly as generated. When supplied, it
must be the complete edited task array and it replaces the stored tasks before the status
transition. Editing is permitted only while the plan is in `DRAFT`; a request carrying `tasks`
for an already-`APPROVED` plan is a `422 VALIDATION_ERROR`.

This is how the manager's edit-before-approve step (FR-019, AC-10) is satisfied without a
separate mutation endpoint.

### Success response

`200 OK`

```json
{
  "plan_id": "plan_001",
  "status": "APPROVED",
  "approved_by": "eng_manager_sarah",
  "approved_at": "2026-08-11T22:30:00Z"
}
```

### Contract rule

Approval remains inside ContinuityAI.

No Jira, email, Slack, calendar, or autonomous assignment side effect is required for MVP.

---

# 9. Error Contract

All API errors must use the same envelope.

```json
{
  "error": {
    "code": "INSUFFICIENT_EVIDENCE",
    "message": "Not enough qualifying evidence exists to assess Incident Recovery.",
    "details": {
      "capability_id": "cap_incident_recovery"
    }
  }
}
```

## 9.1 Error codes

```text
NOT_FOUND
VALIDATION_ERROR
INSUFFICIENT_EVIDENCE
AI_EXTRACTION_FAILED
GRAPH_INCONSISTENCY
SIMULATION_FAILED
MITIGATION_GENERATION_FAILED
INTERNAL_ERROR
```

## 9.2 Recommended HTTP mapping

| Error code | HTTP |
|---|---:|
| `NOT_FOUND` | 404 |
| `VALIDATION_ERROR` | 422 |
| `INSUFFICIENT_EVIDENCE` | 409 |
| `AI_EXTRACTION_FAILED` | 502 or 500 |
| `GRAPH_INCONSISTENCY` | 500 |
| `SIMULATION_FAILED` | 500 |
| `MITIGATION_GENERATION_FAILED` | 500 |
| `INTERNAL_ERROR` | 500 |

The frontend should switch on `error.code`, not parse human-readable messages.

---

# 10. AI Extraction Contract

The backend AI layer may semantically interpret artifacts, but it must not directly decide engineer readiness or continuity risk.

## 10.1 Input example

```json
{
  "source_type": "INCIDENT",
  "source_reference": "INC-184",
  "artifact_date": "2026-05-14",
  "title": "P1 Payment Gateway Provider Failure",
  "content": "Alex investigated failed transactions, identified that provider failover had not activated after the primary gateway became unavailable, corrected the failover configuration, and restored transaction processing.",
  "participants": ["eng_alex_chen"]
}
```

## 10.2 Allowed AI extraction output

```json
{
  "system": "Payment Gateway",
  "component": "Gateway Integration",
  "capabilities": [
    "Incident Recovery",
    "Provider Failover"
  ],
  "engineer_id": "eng_alex_chen",
  "evidence_role": "INDEPENDENT_EXECUTION",
  "evidence_strength": "STRONG",
  "summary": "Alex independently restored Payment Gateway operation after provider failover failed."
}
```

## 10.3 AI must not output as source of truth

The extraction model must not directly assign:

```text
readiness = VALIDATED
continuity_risk_index = 93
employee_value = HIGH
best_backup = Maria
```

Those are downstream decisions produced by deterministic aggregation or grounded recommendation services.

## 10.4 Grounding rule

Every extracted claim must reference the input artifact that produced it.

Unsupported invented entities must be rejected or flagged for review.

---

# 11. Readiness Contract

Readiness is computed by deterministic backend logic from evidence.

Inputs may include:

- evidence strength;
- evidence role;
- evidence diversity;
- evidence freshness;
- repetition; and
- independent execution.

The API does not expose the internal formula as a client responsibility.

## 11.1 Required behavior

The engine must be capable of distinguishing at least:

```text
many weak interactions != validated readiness
one or more independent executions > passive exposure
stale evidence < fresh evidence
multiple evidence types > repeated same-type weak evidence
```

## 11.2 Uncertainty

If evidence is too weak or contradictory, the backend may return:

```text
exposure = INSUFFICIENT_EVIDENCE
```

or low evidence confidence.

The system must not manufacture a readiness classification solely to fill the UI.

---

# 12. Continuity Risk Contract

The Continuity Risk Index is an interpretable severity index from `0` to `100`.

It is **not**:

- probability of outage;
- probability an employee leaves;
- employee value;
- performance rating; or
- predicted financial loss.

The source of truth is the capability-level rule engine.

The index is used to:

- compare system states;
- visualize severity;
- show before/after simulation changes; and
- sort systems in the dashboard.

## 12.1 Explainability

The backend should retain rule reasons such that the UI can eventually display `Why this risk?`.

Example internal/result rationale:

```json
{
  "rules_triggered": [
    "CRITICAL_CAPABILITY",
    "SINGLE_VALIDATED_ENGINEER",
    "NO_PRACTICED_OR_VALIDATED_BACKUP",
    "INCOMPLETE_DOCUMENTATION"
  ]
}
```

`rules_triggered` is part of the contract as of decision CI-08 (2026-08-14). It is present on
`CapabilityDetail` and on the `assessment` block of the capability-evidence response.

The values are machine-readable reason codes, never prose. The frontend owns the human-readable
copy for each code, which keeps responsible-AI wording under joint review rather than generating
it in the backend. Person A owns the closed list of codes; the frontend renders an unrecognised
code as its raw value rather than hiding it.

---

# 13. Responsible AI Contract

The API must preserve the product's system-first design.

## 13.1 Prohibited outputs

The backend must not expose or generate:

- employee productivity ranking;
- employee value ranking;
- promotion recommendation;
- bonus recommendation;
- layoff recommendation;
- personality assessment;
- sentiment score;
- working-hours score;
- loyalty score;
- private-message monitoring output.

## 13.2 Backup recommendations

The API must phrase recommendations as technical evidence only.

Preferred:

> Maria has the strongest demonstrated technical overlap among the available candidates.

Avoid:

> Maria is the best employee to assign.

## 13.3 Evidence absence

Preferred:

> No qualifying evidence of independent recovery was found.

Avoid:

> Jordan cannot recover the system.

---

# 14. Mock-First Frontend Development

The frontend may begin before backend intelligence is implemented.

Create these fixtures in the repository-root shared directory:

```text
fixtures/
```

These payloads are jointly owned. Both the frontend and the backend validate against them, so
they must not live inside `frontend/`. Where a fixture and this contract disagree, this contract
is correct and the fixture is fixed.

Recommended files:

```text
platforms.json
payments-systems.json
payment-gateway.json
payment-gateway-graph.json
incident-recovery.json
incident-recovery-evidence.json
alex-simulation.json
backup-candidates.json
mitigation-plan.json
```

The fixture JSON must exactly match this contract.

When FastAPI endpoints become available, frontend components should replace mock loaders with HTTP calls without rewriting component data models.

---

# 15. TypeScript Contract Sketch

The frontend should define shared types equivalent to the API contract.

Example:

```ts
export type BusinessCriticality =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL';

export type ReadinessLevel =
  | 'NONE'
  | 'EXPOSED'
  | 'ASSISTED'
  | 'PRACTICED'
  | 'VALIDATED';

export type CapabilityExposure =
  | 'COVERED'
  | 'DEGRADED'
  | 'CRITICAL_GAP'
  | 'INSUFFICIENT_EVIDENCE';

export type EvidenceConfidence = 'LOW' | 'MEDIUM' | 'HIGH';
export type Freshness = 'FRESH' | 'AGING' | 'STALE';

export type ContinuityRiskClass =
  | 'LOW'
  | 'MODERATE'
  | 'HIGH'
  | 'CRITICAL';

export interface SystemSummary {
  system_id: string;
  platform_id: string;
  name: string;
  description: string | null;
  business_criticality: BusinessCriticality;
  continuity_risk_index: number | null;
  continuity_risk_class: ContinuityRiskClass | null;
  exposure: CapabilityExposure;
  evidence_confidence: EvidenceConfidence;
  critical_gap_count: number;
  degraded_capability_count: number;
  covered_capability_count: number;
  insufficient_evidence_count: number;
  drift_status: 'NEW_RISK' | 'RISK_INCREASED' | 'STABLE' | 'RISK_REDUCED';
}
```

Recommendation: generate TypeScript types from the OpenAPI schema later if convenient, but the contract remains the source of truth.

---

# 16. Pydantic Contract Sketch

The backend should model public DTOs with Pydantic.

Example:

```python
from enum import Enum
from pydantic import BaseModel, Field


class BusinessCriticality(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceConfidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CapabilityExposure(str, Enum):
    COVERED = "COVERED"
    DEGRADED = "DEGRADED"
    CRITICAL_GAP = "CRITICAL_GAP"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ContinuityRiskClass(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SystemSummary(BaseModel):
    system_id: str
    platform_id: str
    name: str
    description: str | None = None
    business_criticality: BusinessCriticality
    continuity_risk_index: int | None = Field(default=None, ge=0, le=100)
    continuity_risk_class: ContinuityRiskClass | None = None
    exposure: CapabilityExposure
    evidence_confidence: EvidenceConfidence
    critical_gap_count: int = Field(ge=0)
    degraded_capability_count: int = Field(ge=0)
    covered_capability_count: int = Field(ge=0)
    insufficient_evidence_count: int = Field(ge=0)
    drift_status: str
```

The exact internal file organization is implementation-specific.

---

# 17. API Change Control

Once Phase 0 is frozen:

1. No developer changes a shared enum, field name, endpoint path, or response shape silently.
2. Proposed changes are discussed by both developers.
3. `API_CONTRACT.md` is updated first.
4. Mock fixtures are updated.
5. Backend models and frontend types are updated in the same change window.
6. Breaking changes should be avoided until after the hackathon unless they are required to unblock the core workflow.

Recommended pull-request label:

```text
contract-change
```

---

# 18. API Acceptance Checklist

Phase 0 is considered implemented when all of the following are true.

## Contract

- [ ] All shared enums exist in backend and frontend.
- [ ] All 10 endpoints are represented in FastAPI, even if some initially return fixtures.
- [ ] All 10 endpoints use `/api/v1`.
- [ ] Error responses use the shared error envelope.
- [ ] Mock JSON validates against expected shapes.

## Dashboard

- [ ] Frontend can load platform summaries.
- [ ] Frontend can load systems under a platform.
- [ ] No platform-level artificial risk score is calculated.

## System analysis

- [ ] System detail includes risk/exposure/confidence counts.
- [ ] Contextual graph loads from the graph endpoint.
- [ ] Capability detail includes engineer readiness coverage.

## Evidence

- [ ] Evidence records contain source references and provenance.
- [ ] The UI can show why a readiness claim exists.
- [ ] Missing evidence is phrased as insufficient evidence rather than inability.

## Simulation

- [ ] `ENGINEER_UNAVAILABLE` is the only MVP simulation type.
- [ ] Simulation does not mutate baseline graph state.
- [ ] Simulation returns deterministic before/after capability impacts.
- [ ] Simulation returns before/after system Continuity Risk Index.

## Recommendation

- [ ] Up to 3 candidates may be returned.
- [ ] Candidates contain strengths and gaps.
- [ ] Candidate response includes the technical-only disclaimer.
- [ ] No employee-value score is exposed.

## Mitigation

- [ ] Manager-selected candidate is required.
- [ ] Generated plan starts in `DRAFT`.
- [ ] Human approval transitions to `APPROVED`.
- [ ] Plan generation does not automatically change readiness/risk.
- [ ] No external task system integration is required.

---

# 19. Golden-Path Contract Test

Both developers should use this exact flow as the daily integration smoke test:

```text
GET /platforms
        ↓
GET /platforms/platform_payments/systems
        ↓
GET /systems/system_payment_gateway
        ↓
GET /systems/system_payment_gateway/graph
        ↓
GET /capabilities/cap_incident_recovery
        ↓
GET /capabilities/cap_incident_recovery/evidence
        ↓
POST /simulations
  engineer = eng_alex_chen
  scope = system_payment_gateway
        ↓
POST /recommendations/backup-candidates
  capability = cap_incident_recovery
        ↓
Manager selects eng_maria_gomez
        ↓
POST /mitigation-plans
        ↓
POST /mitigation-plans/plan_001/approve
```

Expected demo truth for the seeded NovaPay hero scenario:

```text
Declared Payment Gateway owner: Jordan
Strongest demonstrated Incident Recovery coverage: Alex
Alex unavailable: Incident Recovery becomes CRITICAL_GAP
Retry Logic remains COVERED
Maria is returned as a HIGH technical-overlap backup candidate
Mitigation plan is generated in DRAFT state
Manager approval changes plan to APPROVED
```

The exact numeric Continuity Risk Index values may evolve while the rule engine is implemented, but the seeded fixture should be stable once the risk rules are frozen.

---

# 20. Non-Goals for This Contract

This API version does not include:

- authentication/authorization beyond minimal demo identity;
- live Jira integration;
- live Confluence integration;
- Slack/Teams ingestion;
- employee performance reviews;
- employee ranking;
- compensation recommendations;
- autonomous staffing decisions;
- workload optimization;
- long-term mitigation progress tracking;
- automatic readiness upgrades after plan approval;
- calendar scheduling;
- email notifications;
- continuous background monitoring;
- ML probability-of-failure prediction;
- graph-wide arbitrary query language; or
- production multi-tenant SaaS concerns.

These are roadmap items only if the core MVP proves valuable.

---

# 21. Definition of Phase 0 Complete

Phase 0 is complete when both developers can independently answer **yes** to all of the following:

1. Do we agree on the domain vocabulary?
2. Do we agree on every enum spelling and casing?
3. Do we agree that backend owns readiness/risk/simulation decisions?
4. Can the frontend build every MVP screen from the mock payloads in this contract?
5. Can the backend implement endpoints without needing frontend-specific hidden assumptions?
6. Can we run the same golden path using mocks today and real endpoints later?
7. Do we agree that any future breaking contract change requires both developers to approve it?

If yes, development proceeds to Phase 1.

---

# 22. Recommended Next Development Step

After freezing this document:

**Backend lead**

1. Create FastAPI project.
2. Implement shared Pydantic enums/DTOs.
3. Add the 10 endpoint routes.
4. Return seeded fixture payloads first.
5. Add OpenAPI validation/tests.

**Frontend lead**

1. Create Next.js project.
2. Add equivalent TypeScript enums/interfaces.
3. Add `/mocks` fixtures matching this document.
4. Build the dashboard and golden-path screens against fixtures.
5. Centralize API access behind a small client layer so fixtures can later be replaced by HTTP calls.

**Shared checkpoint**

Before implementing AI or the graph engine, confirm that the frontend can complete the entire golden-path flow using the frozen mock payloads and that FastAPI can return the same shapes.

---

**End of Phase 0 API Contract v1.0.0**
