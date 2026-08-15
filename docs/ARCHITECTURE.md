# ContinuityAI — Architecture Specification

**Version:** 1.0  
**Status:** Phase 0 — Frozen for MVP implementation  
**Project:** IBM Builders Challenge — Wildcard: Intelligent Systems for the Future of Work  
**Companion documents:** `PRD.md`, `API_CONTRACT.md`, `DOMAIN_MODEL.md`

---

# 1. Purpose

This document defines the technical architecture for the ContinuityAI MVP.

It exists so two developers can work in parallel without repeatedly renegotiating:

- system boundaries;
- service ownership;
- frontend/backend responsibilities;
- AI responsibilities;
- deterministic reasoning responsibilities;
- persistence strategy;
- module layout;
- data flow;
- API integration points;
- error handling;
- testing boundaries;
- evaluation architecture;
- deployment assumptions;
- collaboration ownership.

The architecture is intentionally optimized for a hackathon-quality prototype:

> **Small enough to build quickly, structured enough to feel like a real product, and explicit enough that the two developers can work independently behind stable contracts.**

---

# 2. Architectural Goals

The MVP architecture must satisfy six goals.

## 2.1 Parallel development

Frontend and backend developers must be able to make meaningful progress at the same time.

The frontend builds against frozen mock DTOs.

The backend implements the exact same DTOs through FastAPI.

---

## 2.2 Explainable intelligence

AI may interpret unstructured engineering evidence, but it must not directly decide final readiness or continuity risk.

The architecture therefore separates:

```text
AI semantic interpretation
        ↓
Structured evidence
        ↓
Deterministic aggregation
        ↓
Deterministic readiness/risk
```

---

## 2.3 Evidence traceability

Every important user-visible conclusion should be traceable to source evidence.

For example:

```text
Incident Recovery = CRITICAL_GAP
        ↓
Alex = VALIDATED
Maria = ASSISTED
Jordan = EXPOSED
        ↓
INC-184
INC-221
PR-442
DOC-17
```

---

## 2.4 Counterfactual simulation

The system must be able to answer:

> What technical capability coverage changes if this engineer becomes unavailable?

without modifying the persisted baseline state.

---

## 2.5 Responsible decision support

The architecture must support technical continuity decisions without becoming an employee-ranking or surveillance system.

---

## 2.6 Hackathon feasibility

Avoid unnecessary infrastructure.

Do not introduce:

- microservices;
- Kubernetes;
- Kafka;
- a dedicated graph database;
- distributed event systems;
- complex authentication infrastructure;
- multiple persistence technologies;

unless required later.

---

# 3. High-Level Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                      ContinuityAI Web App                     │
│                       Next.js / React                        │
│                                                              │
│ Dashboard │ System │ Graph │ Evidence │ Simulation │ Plans  │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                │ HTTPS / JSON
                                │ /api/v1/*
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                         │
│                                                              │
│  API Layer                                                   │
│      │                                                       │
│      ├── Platform/System Queries                             │
│      ├── Capability/Evidence Queries                         │
│      ├── Simulation Commands                                 │
│      ├── Candidate Comparison                                │
│      └── Mitigation Plans                                    │
│                                                              │
│  Application / Domain Services                               │
│      │                                                       │
│      ├── Ingestion                                           │
│      ├── AI Semantic Extraction                              │
│      ├── Evidence Aggregation                                │
│      ├── Typed Knowledge Graph                               │
│      ├── Readiness Engine                                    │
│      ├── Continuity Risk Engine                              │
│      ├── Counterfactual Simulator                            │
│      ├── Backup Candidate Engine                             │
│      ├── Mitigation Generator                                │
│      └── Evaluation                                          │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                         SQLite                               │
│                                                              │
│ Platforms │ Systems │ Components │ Capabilities │ Engineers │
│ Evidence │ Coverage │ Ownership │ Simulations │ Plans       │
└──────────────────────────────────────────────────────────────┘

External / development-time inputs:

┌──────────────────┐   ┌─────────────────────┐
│ Public GitHub    │   │ Synthetic Enterprise│
│ artifacts        │   │ incidents/docs/etc. │
└─────────┬────────┘   └──────────┬──────────┘
          └──────────────┬────────┘
                         ▼
                  Ingestion Pipeline
                         │
                         ▼
                  AI Extraction Adapter
```

---

# 4. Architectural Style

ContinuityAI will use a:

> **Modular monolith**

That means:

- one frontend application;
- one backend application;
- one database;
- clear internal modules.

This is preferred over microservices because:

1. the team has two developers;
2. the product is an MVP;
3. the challenge values working technical execution more than infrastructure complexity;
4. most modules require tight access to shared domain entities;
5. deployment and debugging remain simple.

---

# 5. Technology Stack

## 5.1 Frontend

```text
Next.js
React
TypeScript
```

Recommended supporting libraries:

```text
React Flow       knowledge graph visualization
TanStack Query   API request/query state
Zod              optional frontend runtime validation
Tailwind CSS     UI styling
```

Use only what is needed.

Do not over-build a design system.

---

## 5.2 Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy or SQLModel
```

Recommended:

```text
FastAPI          HTTP/API layer
Pydantic         request/response/domain validation
SQLAlchemy       persistence
Alembic          migrations if needed
pytest           automated tests
```

For a very short build, migration tooling can be introduced after the schema stabilizes.

---

## 5.3 Persistence

```text
SQLite
```

SQLite is sufficient for the MVP because:

- the demo dataset is small;
- the app is primarily read/analysis heavy;
- no large-scale concurrency is required;
- the graph is a logical abstraction, not necessarily a graph database;
- local development is easy.

---

## 5.4 AI Provider

AI access must sit behind an application abstraction.

Example:

```text
AIProvider
  ├── extract_artifact_semantics(...)
  ├── summarize_simulation(...)
  ├── explain_candidate(...)
  └── generate_mitigation_plan(...)
```

Do not call a model directly from random controllers or React components.

This allows the team to change the underlying provider without rewriting domain logic.

---

# 6. Repository Structure

Recommended monorepo:

```text
continuity-ai/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   ├── types/
│   └── public/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── ai/
│   │   ├── ingestion/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── graph/
│   │   ├── evidence/
│   │   ├── continuity/
│   │   ├── simulation/
│   │   ├── recommendation/
│   │   ├── mitigation/
│   │   ├── evaluation/
│   │   └── core/
│   │
│   ├── tests/
│   └── scripts/
│
├── fixtures/
│
├── data/
│   ├── public/
│   ├── synthetic/
│   ├── ground_truth/
│   └── generated/
│
├── docs/
│   ├── PRD.md
│   ├── API_CONTRACT.md
│   ├── DOMAIN_MODEL.md
│   └── ARCHITECTURE.md
│
├── README.md
├── BUILD_WITH_BOB.md
└── .gitignore
```

---

# 7. Frontend Architecture

The frontend is responsible for presentation and interaction.

It does not own domain intelligence.

---

# 8. Frontend Feature Areas

Recommended:

```text
features/
├── dashboard/
├── systems/
├── graph/
├── evidence/
├── simulations/
├── recommendations/
└── mitigation/
```

Each feature may include:

```text
components/
hooks/
api/
types/
```

Avoid a giant global components folder for every piece of product behavior.

---

# 9. Frontend Pages

The meaningful MVP routes should be limited.

Suggested:

```text
/
  Portfolio Dashboard

/systems/[systemId]
  System Detail

/systems/[systemId]/graph
  Contextual Knowledge Graph / Evidence

/simulations/[simulationId]
  Simulation Result

/plans/[planId]
  Mitigation Plan
```

Candidate comparison may be embedded inside the simulation result.

A dedicated People application is not required.

Engineer information can appear in:

- drawers;
- profile cards;
- graph nodes;
- capability coverage panels.

---

# 10. Frontend State Model

Separate state into three categories.

## 10.1 Server state

Data fetched from FastAPI.

Examples:

```text
platforms
systems
capabilities
evidence
simulation results
recommendations
mitigation plans
```

Use query-state tooling rather than duplicating this globally.

---

## 10.2 UI state

Examples:

```text
selected platform
open evidence drawer
selected engineer
expanded capability
graph zoom
filters
```

This remains frontend-owned.

---

## 10.3 Domain-derived state

Do not calculate this in React:

```text
risk index
readiness
confidence
critical-gap status
technical overlap
```

Receive it from backend.

---

# 11. Frontend Mock Strategy

During parallel development:

```text
fixtures/
├── platforms.json
├── payment-gateway.json
├── payment-gateway-graph.json
├── incident-recovery-evidence.json
├── alex-simulation.json
├── backup-candidates.json
└── mitigation-plan.json
```

Mock payloads live in the repository-root `fixtures/` directory, are jointly owned by both
developers, and must conform exactly to `API_CONTRACT.md`.

The frontend API wrapper should make switching environments simple.

Example:

```text
NEXT_PUBLIC_USE_MOCKS=true
```

When mock mode is disabled:

```text
fetch("/api/v1/...")
```

The UI components should not care where the data came from.

---

# 12. Backend Layering

Recommended dependency direction:

```text
API Routes
    ↓
Application Services
    ↓
Domain Logic
    ↓
Repositories / AI Provider
    ↓
SQLite / External Model
```

Routes should not contain business logic.

---

# 13. Backend API Layer

Responsibilities:

- parse requests;
- validate DTOs;
- call application services;
- translate known exceptions into API errors;
- return contract-compliant responses.

Routes should remain thin.

Example:

```text
POST /api/v1/simulations

Route
  ↓
SimulationService.simulate_engineer_unavailable(...)
  ↓
SimulationResponse
```

---

# 14. Backend Schemas

`schemas/` contains Pydantic request/response DTOs.

Examples:

```text
platform.py
system.py
capability.py
evidence.py
graph.py
simulation.py
recommendation.py
mitigation.py
error.py
```

These should closely mirror `API_CONTRACT.md`.

---

# 15. Persistence Models

`models/` represents database tables.

Do not force database models to equal API DTOs.

Example:

```text
CapabilityModel
```

may have persistence-specific fields that do not appear in:

```text
CapabilityResponse
```

This separation prevents UI needs from dictating storage structure.

---

# 16. Repository Layer

Repositories encapsulate persistence access.

Suggested:

```text
PlatformRepository
SystemRepository
CapabilityRepository
EngineerRepository
EvidenceRepository
CoverageRepository
SimulationRepository
MitigationPlanRepository
```

Application services should not contain raw SQL.

---

# 17. Ingestion Module

Purpose:

> Convert external engineering artifacts into normalized RawArtifact objects.

Inputs may include:

```text
GitHub commits
GitHub pull requests
GitHub issues
CODEOWNERS
synthetic incident records
synthetic tickets
synthetic runbooks
synthetic architecture documents
```

Output:

```text
RawArtifact
```

This is not yet Evidence.

---

# 18. Ingestion Pipeline

```text
Source Artifact
      ↓
Source Adapter
      ↓
RawArtifact
      ↓
Normalization
      ↓
AI Semantic Extraction
      ↓
Evidence Candidate
      ↓
Validation
      ↓
Evidence Record
```

---

# 19. AI Module

The AI module owns semantic interpretation of unstructured text.

It should not own final continuity decisions.

Suggested interface:

```python
class AIProvider:
    async def extract_artifact_semantics(self, artifact):
        ...

    async def summarize_simulation(self, simulation):
        ...

    async def explain_candidate(self, candidate_context):
        ...

    async def generate_mitigation_plan(self, context):
        ...
```

---

# 20. AI Extraction Input

Example:

```text
Artifact type: INCIDENT
Reference: INC-184
Title: Payment Gateway P1 Provider Failure
Participants: Alex Chen, Maria Gomez

Body:
...
```

---

# 21. AI Extraction Output

Structured only.

Example conceptual output:

```json
{
  "system": "Payment Gateway",
  "component": "Gateway Integration",
  "capabilities": [
    {
      "capability": "Incident Recovery",
      "engineer": "Alex Chen",
      "evidence_role": "INDEPENDENT_EXECUTION",
      "evidence_strength": "STRONG"
    },
    {
      "capability": "Incident Recovery",
      "engineer": "Maria Gomez",
      "evidence_role": "ASSISTED_EXECUTION",
      "evidence_strength": "MODERATE"
    }
  ]
}
```

AI does not emit:

```text
Alex readiness = VALIDATED
risk = 93
```

---

# 22. AI Extraction Validation

Every AI response should be validated before persistence.

Recommended sequence:

```text
LLM JSON
  ↓
Pydantic schema validation
  ↓
entity-resolution validation
  ↓
capability/system mapping validation
  ↓
persist evidence
```

If invalid:

```text
AI_EXTRACTION_FAILED
```

or send to a review state.

Do not silently accept malformed free text.

---

# 23. AI Provider Boundary

Use:

```text
app/ai/provider.py
```

and:

```text
app/ai/prompts/
```

Avoid:

```text
openai/bedrock/model calls scattered across
routes
services
React components
```

The exact AI provider can change without affecting the continuity engine.

---

# 24. Typed Knowledge Graph Module

The graph is a domain abstraction.

It represents:

```text
Platform → System → Component → Capability
Engineer → Capability
Capability/coverage → Evidence
```

The graph module should expose operations such as:

```text
get_system_neighborhood(system_id)
get_capability_coverage(capability_id)
get_engineer_capabilities(engineer_id)
get_system_capabilities(system_id)
get_candidate_neighbors(capability_id)
```

---

# 25. Graph Persistence Strategy

Do not introduce Neo4j for MVP.

Use relational tables and construct graph DTOs in Python.

For example:

```text
systems
components
capabilities
engineers
engineer_capability_coverage
evidence
```

The graph service converts these into:

```text
nodes[]
edges[]
```

for the frontend.

---

# 26. Evidence Engine

The evidence engine converts individual Evidence records into an aggregate technical assessment.

Input:

```text
Evidence[] for (Engineer, Capability)
```

Output:

```text
EngineerCapabilityCoverage
```

Responsibilities:

- count evidence by strength;
- count evidence-role types;
- assess diversity;
- assess freshness;
- detect independent execution;
- detect assisted execution;
- produce evidence confidence;
- send aggregate into readiness rules.

---

# 27. Readiness Engine

The readiness engine is deterministic.

Suggested service:

```text
ReadinessService
```

Input:

```text
EvidenceAggregate
```

Output:

```text
NONE
EXPOSED
ASSISTED
PRACTICED
VALIDATED
```

Every result should include internal explanation/reason codes.

Example:

```text
READINESS_VALIDATED_BECAUSE:
- 2 STRONG INDEPENDENT_EXECUTION records
- evidence is FRESH
- 3 source types
```

These reason codes help the `Why?` UI.

---

# 28. Continuity Engine

The continuity engine evaluates capability coverage and risk.

Suggested services:

```text
ExposureService
RiskService
```

Responsibilities:

```text
Capability coverage
    ↓
Capability exposure
    ↓
Capability risk
    ↓
System aggregation
```

---

# 29. Rule-First Risk Architecture

Risk classification should be explainable through fired rules.

Example:

```text
RULE: CRITICAL_SINGLE_VALIDATED_NO_BACKUP

IF:
  capability.operational_criticality == CRITICAL
  AND practiced_or_validated_count == 1
  AND practiced_or_validated_backup_count == 0

THEN:
  exposure = DEGRADED
  add risk weight
```

```text
RULE: CRITICAL_NO_ADEQUATE_COVERAGE

IF:
  capability.operational_criticality == CRITICAL
  AND practiced_or_validated_count == 0

THEN:
  exposure = CRITICAL_GAP
  add risk weight
```

Result for the sole-expert case:

```text
Continuity Risk Index = 72 (HIGH)

Reason codes:
- CRITICAL_CAPABILITY
- SINGLE_VALIDATED_EXPERT
- NO_READY_BACKUP
- AGING_DOCUMENTATION
```

The number communicates severity and comparison.

It is not probability.

---

# 30. Counterfactual Simulation Module

Simulation is implemented as a temporary alternate graph state.

It must not mutate baseline coverage.

Suggested service:

```text
SimulationService
```

---

# 31. Simulation Flow

```text
POST /simulations
       ↓
Load system baseline
       ↓
Calculate BEFORE state
       ↓
Create in-memory coverage snapshot
       ↓
Remove target engineer coverage edges
       ↓
Recalculate affected capabilities
       ↓
Recalculate system continuity
       ↓
Create AFTER state
       ↓
Compare
       ↓
Persist simulation result
       ↓
Return DTO
```

---

# 32. Simulation Optimization

The simulator does not need to recompute the entire organization.

If scope is:

```text
Payment Gateway
```

only recompute:

```text
capabilities within Payment Gateway
```

This keeps logic simple.

---

# 33. Simulation Semantics

Only:

```text
ENGINEER_UNAVAILABLE
```

For MVP this means:

> Remove the selected engineer's demonstrated capability coverage from the selected System scope.

Do not model:

- whether the engineer quit;
- why they are unavailable;
- probability of departure;
- time horizon;
- replacement hiring.

---

# 34. Recommendation Module

The recommendation module identifies technically adjacent backup candidates.

Suggested service:

```text
BackupCandidateService
```

Input:

```text
capability gap
current graph
available engineers
evidence coverage
```

Output:

```text
up to 3 BackupCandidate objects
```

---

# 35. Recommendation Pipeline

```text
Critical capability gap
      ↓
Find engineers with relevant neighboring capabilities
      ↓
Calculate transparent technical overlap
      ↓
Collect supporting evidence
      ↓
Generate strengths
      ↓
Generate missing capability gaps
      ↓
Return top candidates
```

Deterministic code should perform candidate filtering/ranking where practical.

AI may help convert structured evidence into concise explanations.

---

# 36. Candidate Selection Factors

Potential deterministic inputs:

```text
same-system familiarity
same-component familiarity
adjacent capability readiness
incident-response experience
deployment experience
operational experience
evidence freshness
evidence confidence
```

Excluded:

```text
workload
availability
career goals
salary
manager preference
performance rating
```

The UI must remind users of this limitation.

---

# 37. Mitigation Module

Suggested service:

```text
MitigationPlanService
```

Flow:

```text
Manager selects backup candidate
        ↓
Backend gathers:
  missing capabilities
  existing strengths
  supporting evidence
        ↓
AI generates specific transfer tasks
        ↓
Pydantic validates structured plan
        ↓
Store DRAFT
        ↓
Manager approves
        ↓
APPROVED
```

No automatic Jira creation in MVP.

---

# 38. Mitigation Plan Guardrail

The generated plan must target missing capability coverage.

Bad:

```text
Teach Maria everything Alex knows.
```

Good:

```text
Incident Recovery
- review recovery architecture
- study INC-184 / INC-221
- perform provider failover in staging
- complete independent recovery drill
- update runbook
```

---

# 39. Evaluation Module

The evaluation module is separated from production domain logic.

Suggested:

```text
evaluation/
├── ground_truth.py
├── evaluator.py
├── metrics.py
└── reports.py
```

It reads:

```text
data/ground_truth/
```

The normal application must not.

---

# 40. Hidden Ground Truth Isolation

Critical architectural rule:

```text
Application runtime
    X
    │ cannot read
    X
data/ground_truth/
```

Only evaluation scripts can access hidden labels.

This ensures the system cannot simply look up the answer.

---

# 41. Synthetic Data Generator

Recommended structure:

```text
backend/scripts/generate_synthetic_data.py
```

or:

```text
data/generator/
```

Inputs:

```text
hidden organization model
```

Outputs:

```text
incidents.json
tickets.json
documents.json
employees.json
systems.json
```

The generator may deliberately create:

- declared-owner mismatches;
- incomplete evidence;
- varying evidence strength;
- stale artifacts;
- noisy activity.

But MVP evaluation does not need a large benchmark suite.

---

# 42. Example Data Flow: Incident

```text
INC-184 synthetic incident
        ↓
Ingestion adapter
        ↓
RawArtifact
        ↓
AI extraction
        ↓
Evidence:
Alex
Incident Recovery
INDEPENDENT_EXECUTION
STRONG
        ↓
Evidence engine
        ↓
Aggregate with INC-221, PR-442, DOC-17
        ↓
Readiness engine
        ↓
Alex → Incident Recovery → VALIDATED
        ↓
Continuity engine
        ↓
Capability coverage
```

---

# 43. Example Data Flow: Frontend

```text
Dashboard loads
        ↓
GET /api/v1/platforms
        ↓
Payments Platform
Highest System Risk 74
Critical Gaps 1
        ↓
User expands
        ↓
GET /api/v1/platforms/platform_payments/systems
        ↓
Payment Gateway 74
Refund Engine 72
Billing Integration 51
```

Frontend performs no risk calculation.

---

# 44. Example Data Flow: Simulation

```text
User selects:
Alex unavailable
Payment Gateway

        ↓

POST /api/v1/simulations

        ↓

Simulation engine:
remove Alex coverage
recalculate capability exposure

        ↓

Incident Recovery:
DEGRADED → CRITICAL_GAP

Provider Failover:
COVERED → DEGRADED

Retry Logic:
COVERED → COVERED

        ↓

Risk:
74 → 93

        ↓

Frontend renders before/after
```

---

# 45. Example Data Flow: Recommendation

```text
User clicks:
Find backup candidates
for Incident Recovery

        ↓

POST /recommendations/backup-candidates

        ↓

Candidate engine
        ↓
Maria HIGH
Jordan MEDIUM
Kevin LOW

        ↓

AI explanation layer
        ↓

strengths / gaps text

        ↓

Frontend comparison cards
```

---

# 46. API Boundary

The only supported frontend/backend communication is through the frozen `/api/v1` contract.

Frontend must not:

- connect directly to SQLite;
- import Python domain models;
- invoke the AI provider;
- calculate graph truth from raw source data.

---

# 47. Error Architecture

Backend application errors should become a consistent envelope.

Example:

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

Known domain exceptions:

```text
NotFoundError
ValidationError
InsufficientEvidenceError
SimulationError
AIExtractionError
GraphConsistencyError
```

Convert these at the API boundary.

---

# 48. Logging

MVP logging should be simple but useful.

Backend log events:

```text
artifact_ingested
ai_extraction_started
ai_extraction_completed
ai_extraction_failed
evidence_persisted
readiness_recalculated
risk_recalculated
simulation_completed
recommendation_generated
mitigation_plan_created
```

Do not log private raw artifacts unnecessarily.

---

# 49. Configuration

Recommended backend configuration:

```text
DATABASE_URL
AI_PROVIDER
AI_MODEL
AI_API_KEY
APP_ENV
LOG_LEVEL
SEED_DATA_PATH
```

Frontend:

```text
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_USE_MOCKS
```

No secrets in source control.

---

# 50. Security Scope

The hackathon MVP is not intended to implement enterprise-grade IAM.

Reasonable MVP:

```text
single demo user
or
simple local/demo authentication
```

Do not spend substantial time on:

- SSO;
- RBAC matrix;
- SCIM;
- enterprise provisioning.

Document these as future requirements.

---

# 51. Data Access Boundary

In a production system, access to engineering artifacts would require strict organizational authorization.

For MVP:

- public GitHub data is safe to ingest;
- private-style enterprise data is synthetic;
- no real private messages or employee monitoring data is used.

This sharply reduces prototype privacy risk.

---

# 52. Responsible AI Architecture

Responsible-AI boundaries are architectural, not merely wording.

## AI is allowed to:

```text
extract technical capability signals
summarize evidence
identify missing technical coverage
explain candidate strengths/gaps
generate knowledge-transfer tasks
```

## AI is not allowed to:

```text
rank employee worth
recommend layoffs
recommend promotion/bonus
infer personality
infer sentiment
monitor productivity
make final staffing decisions
```

---

# 53. Human-in-the-Loop Architecture

Human control points:

```text
Confirm business criticality
        ↓
Review evidence
        ↓
Challenge assessment
        ↓
Review technical candidates
        ↓
Select candidate
        ↓
Review mitigation plan
        ↓
Approve plan
```

No automated staffing assignment occurs.

---

# 54. Challenge Workflow Architecture

Future/MVP-light workflow:

```text
User challenges assessment
        ↓
ChallengeService
        ↓
Attach missing evidence
or
correct mapping
or
manager attestation
        ↓
Evidence engine reruns
        ↓
Readiness reruns
        ↓
Risk reruns
```

The manager never directly types:

```text
Risk = 30
```

---

# 55. Performance Expectations

MVP dataset is intentionally small.

Target:

```text
2–3 Platforms
5–7 Systems
~20–40 Components
~30–60 Capabilities
~8–15 Engineers
hundreds of Evidence records
```

This is enough to make the product feel reusable while remaining easy to reason about.

---

# 56. Expected Latency

Non-AI endpoints:

```text
< 800 ms local p95 (PRD AC-14)
```

PRD AC-14 holds the authoritative performance targets: reads < 800 ms local p95, deterministic
simulation < 2 s on the seeded dataset, AI plan/explanation operations < 12 s.

AI operations may take several seconds.

For UI:

- show meaningful loading state;
- do not freeze the page;
- cache where appropriate.

Mitigation generation and initial artifact extraction can tolerate slower latency.

---

# 57. Caching

Do not build distributed caching.

Frontend query caching is enough.

Backend may memoize expensive demo calculations if needed.

---

# 58. Testing Strategy

Testing is divided by architectural layer.

---

# 59. Backend Unit Tests

High-priority deterministic tests:

```text
evidence aggregation
readiness classification
freshness
capability exposure
risk rules
simulation
candidate filtering
```

Example:

```text
Given:
Alex VALIDATED
Maria ASSISTED
Jordan EXPOSED

When:
Alex unavailable

Then:
Incident Recovery = CRITICAL_GAP
```

---

# 60. AI Contract Tests

Do not test whether the LLM returns identical prose.

Test:

```text
response parses
required fields exist
enum values valid
known artifact maps to expected capability family
unsupported output rejected
```

---

# 61. Repository Tests

Test:

```text
create evidence
query evidence
load system graph
load capability coverage
persist simulation
persist mitigation plan
```

---

# 62. API Tests

Test the frozen contract.

Examples:

```text
GET /platforms returns expected DTO
POST /simulations validates engineer
POST /recommendations rejects unknown simulation
POST /mitigation-plans returns DRAFT
approve changes DRAFT → APPROVED
```

---

# 63. Frontend Tests

Focus on the golden path rather than exhaustive UI testing.

Test:

```text
dashboard renders platform/system data
critical gap is visible
evidence drawer renders provenance
simulation before/after renders
candidate comparison renders
plan approval updates state
```

---

# 64. Evaluation Tests

Separate from unit tests.

Evaluation compares inferred results to hidden ground truth.

Example report:

```text
Engineer-Capability Reconstruction
Expected: VALIDATED
Actual: VALIDATED

Critical Gap
Expected: yes
Actual: yes

Simulation
Expected Incident Recovery gap after Alex unavailable
Actual: gap

Candidate
Expected strongest technical candidate: Maria
Actual: Maria
```

---

# 65. Golden Path Test

Both developers should protect this path:

```text
Dashboard
  ↓
Payments Platform
  ↓
Payment Gateway
  ↓
Incident Recovery
  ↓
Why?
  ↓
Evidence
  ↓
Simulate Alex unavailable
  ↓
Critical gap
  ↓
Compare candidates
  ↓
Select Maria
  ↓
Generate plan
  ↓
Approve
```

If this path breaks, feature development pauses until it is restored.

---

# 66. CI Strategy

Keep CI simple.

On pull request:

```text
Backend:
- format/lint
- unit tests
- API tests

Frontend:
- lint
- TypeScript build
- selected component tests
```

Do not let tooling setup consume the hackathon.

---

# 67. Git Strategy

Primary branch:

```text
main
```

`main` should stay runnable.

Use short-lived branches:

```text
feature/backend-schemas
feature/dashboard
feature/evidence-engine
feature/graph-ui
feature/simulation-engine
feature/simulation-ui
feature/recommendations
feature/mitigation
```

Avoid long-running branches by developer name.

---

# 68. Contract Change Rule

`API_CONTRACT.md` and `DOMAIN_MODEL.md` are frozen after Phase 0.

If a contract must change:

```text
1. Developer identifies requirement.
2. Both developers discuss impact.
3. Update documentation first.
4. Update mock payload.
5. Update backend schema.
6. Update frontend type.
7. Merge as one coordinated change.
```

No silent breaking changes.

---

# 69. Two-Person Ownership Model

For clarity, define:

## Developer A — Intelligence / Backend Lead

Primary ownership:

```text
FastAPI
SQLite
Pydantic
ingestion
AI provider adapter
semantic extraction
typed graph
evidence engine
readiness
risk
simulation
candidate engine
evaluation
```

---

## Developer B — Product / Frontend Lead

Primary ownership:

```text
Next.js
React
dashboard
system detail
graph visualization
evidence UX
simulation UX
candidate comparison
mitigation UX
responsive design
demo polish
```

---

## Shared

```text
contracts
architecture
integration
testing
README
BUILD_WITH_BOB.md
demo script
submission
```

---

# 70. Ownership Matrix

| Area | Developer A | Developer B |
|---|---|---|
| API contract | Shared | Shared |
| Domain model | Shared | Shared |
| Architecture | Shared | Shared |
| FastAPI | Lead | Review |
| Database | Lead | Review |
| Synthetic data | Lead | Review |
| AI extraction | Lead | Review |
| Evidence engine | Lead | Review |
| Readiness engine | Lead | Review |
| Risk engine | Lead | Review |
| Graph query service | Lead | Review |
| Graph visualization | Data support | Lead |
| Dashboard | API support | Lead |
| Evidence UX | API support | Lead |
| Simulator | Engine | UX |
| Candidate comparison | Engine | UX |
| Mitigation plan | API/AI | UX |
| Evaluation | Lead | Cross-test |
| Product polish | Review | Lead |
| README | Shared | Shared |
| Demo | Shared | Shared |

---

# 71. Parallel Development Model

The development rhythm should be:

```text
Contract
   ↓
Mock
   ↓
Frontend implementation
   │
   │ parallel
   │
Backend implementation
   ↓
Integration
   ↓
Golden-path test
```

Do not wait for the backend to be complete before starting UI.

---

# 72. Phase 1 — Skeleton

Developer A:

```text
FastAPI project
Pydantic DTOs
SQLite connection
10 API routes
hardcoded/mock backend responses
basic tests
```

Developer B:

```text
Next.js project
navigation shell
dashboard
system detail shell
mock API layer
core visual components
```

Exit condition:

> Both applications run independently and agree on the frozen DTOs.

---

# 73. Phase 2 — Data Foundation

Developer A:

```text
NovaPay domain seed
synthetic generator
ground truth
artifact normalization
initial database seed
```

Developer B:

```text
portfolio dashboard
system cards
risk display
critical gaps
drift UI
loading/error states
```

Exit condition:

> Dashboard works from backend seeded system data.

---

# 74. Phase 3 — Knowledge Intelligence

Developer A:

```text
AI extraction adapter
evidence records
evidence aggregation
readiness rules
graph query service
```

Developer B:

```text
system capability table
graph visualization
evidence panel
Why? workflow
declared vs demonstrated view
```

Exit condition:

> Payment Gateway capability assessments are evidence-backed and visible.

---

# 75. Phase 4 — Continuity Engine

Developer A:

```text
exposure rules
risk engine
reason codes
system aggregation
```

Developer B:

```text
risk explanation
coverage visualization
critical-gap presentation
```

Exit condition:

> User can understand why Incident Recovery is risky.

---

# 76. Phase 5 — Simulation

Developer A:

```text
ENGINEER_UNAVAILABLE simulation
before/after state
impact calculations
simulation API
```

Developer B:

```text
engineer selection
simulation launch
before/after UX
capability impact cards
risk transition
```

Exit condition:

> Alex unavailable scenario works end-to-end.

---

# 77. Phase 6 — Decision Support

Developer A:

```text
candidate search
technical-overlap logic
strength/gap generation
recommendation API
```

Developer B:

```text
candidate comparison
trade-off presentation
human-selection interaction
```

Exit condition:

> Maria and Jordan comparison works from real backend data.

---

# 78. Phase 7 — Mitigation

Developer A:

```text
AI plan generation
structured validation
persist DRAFT
approve endpoint
```

Developer B:

```text
plan view
task list
approval interaction
success state
```

Exit condition:

> Manager can approve a personalized Maria transfer plan.

---

# 79. Phase 8 — Evaluation

Developer A:

```text
hidden-ground-truth evaluator
reconstruction checks
gap checks
simulation checks
candidate checks
```

Developer B:

```text
cross-test results
identify confusing UX
validate claims against actual evidence
```

Exit condition:

> Team has defensible prototype evaluation results.

---

# 80. Phase 9 — Demo Hardening

Both developers:

```text
fix bugs
remove dead UI
seed deterministic demo data
improve loading states
polish copy
verify responsible-AI language
lock demo script
record backup video
```

No major features should be added here.

---

# 81. Integration Checkpoints

Do not postpone integration.

Recommended checkpoints:

## Checkpoint 1
Dashboard frontend → real `/platforms`.

## Checkpoint 2
System detail → real capabilities.

## Checkpoint 3
Knowledge graph → real graph DTO.

## Checkpoint 4
Evidence → real provenance.

## Checkpoint 5
Simulation → real engine.

## Checkpoint 6
Recommendation → real candidates.

## Checkpoint 7
Mitigation → real structured plan.

---

# 82. Daily Collaboration Rhythm

## Start of day

15-minute sync:

```text
What finished?
What is today's deliverable?
What contract dependency exists?
What is blocked?
```

---

## During day

Develop independently behind the contract.

Merge small PRs.

---

## End of day

Run golden path together.

Even if some steps are mocked, it should remain navigable.

---

# 83. Definition of Done for a Feature

A feature is done only when:

```text
backend contract implemented
frontend integrated
happy path works
error/loading state exists
key deterministic logic tested
demo data supports it
documentation updated if contract changed
```

Not merely:

```text
backend code exists
```

or:

```text
UI screenshot looks good
```

---

# 84. Deployment Architecture

For hackathon deployment, keep frontend and backend simple.

Possible deployment model:

```text
Frontend:
Vercel or equivalent

Backend:
small Python hosting service/container

Database:
SQLite persisted with backend
or seeded in-memory/demo database
```

If SQLite persistence is awkward on chosen hosting, a lightweight Postgres service can replace SQLite without changing domain architecture.

Do not make this change unless deployment requires it.

---

# 85. Demo Reliability Mode

The live demo should not depend on unpredictable external ingestion.

Before recording/submitting:

- seed the required NovaPay dataset;
- persist extracted evidence;
- precompute expensive ingestion if necessary;
- allow deterministic system startup.

Runtime AI can still generate mitigation text if reliable.

If model latency or provider instability threatens the demo, cache the structured expected demo response while preserving the real implementation path.

The goal is to demonstrate the product, not gamble on network latency.

---

# 86. Runtime vs Preprocessing

Not every AI operation needs to happen live.

Recommended:

## Preprocessed

```text
artifact ingestion
semantic extraction
graph construction
readiness calculation
baseline risk
```

## Interactive runtime

```text
simulation
candidate comparison
mitigation generation
```

This makes the product feel responsive.

---

# 87. Observability for Development

Useful debug endpoint or internal tooling may expose:

```text
current graph counts
evidence count
capability coverage
rule reasons
```

Do not expose raw developer debugging on polished screens.

---

# 88. Seed Command

Create one deterministic setup command.

Example:

```text
python -m app.scripts.seed_demo
```

It should:

```text
create database
load NovaPay systems
load engineers
load synthetic artifacts
load/precompute evidence
calculate readiness
calculate risk
```

This drastically improves collaboration and judging setup.

---

# 89. Frontend Development Command

Example:

```text
npm run dev
```

Backend:

```text
uvicorn app.main:app --reload
```

Document these in README immediately.

---

# 90. Recommended Backend Interfaces

Conceptual service interfaces:

```text
ArtifactIngestionService
EvidenceExtractionService
EvidenceAggregationService
ReadinessService
GraphService
ExposureService
RiskService
SimulationService
BackupCandidateService
MitigationPlanService
EvaluationService
```

Avoid premature abstraction beyond these boundaries.

---

# 91. Recommended Frontend Components

Potential components:

```text
PlatformSection
SystemRiskCard
RiskIndex
ExposureBadge
DriftBadge
CapabilityCoverageTable
EngineerReadinessBadge
EvidenceCard
EvidenceDrawer
KnowledgeGraph
SimulationSelector
SimulationImpactCard
RiskTransition
CandidateComparisonCard
MitigationTaskList
ApprovalPanel
```

---

# 92. Architecture Decision Records

If major architectural choices change, create:

```text
docs/decisions/
```

Example:

```text
ADR-001-modular-monolith.md
ADR-002-sqlite-not-neo4j.md
ADR-003-ai-extraction-deterministic-risk.md
```

For the hackathon this is optional, but useful if major decisions emerge.

---

# 93. Decisions Explicitly Frozen

The following are frozen for MVP:

```text
Next.js / React frontend
Python / FastAPI backend
modular monolith
one primary database
typed graph abstraction
no dedicated graph database
AI semantic extraction
deterministic readiness
deterministic risk
ENGINEER_UNAVAILABLE simulation
up to 3 backup candidates
human staffing decision
structured mitigation plan
no live Jira write
hidden ground truth evaluation
```

---

# 94. Decisions Deliberately Deferred

Do not solve these during MVP unless necessary:

```text
enterprise SSO
role-based authorization
real Slack integration
live Jira integration
live Confluence integration
continuous scheduled ingestion
graph database migration
enterprise multi-tenancy
billing
real HRIS integration
employee performance review
workload scheduling
automatic task assignment
advanced event-driven architecture
```

---

# 95. Architecture Quality Bar

The architecture should make these statements true:

### A
The frontend developer can work for several days without waiting for backend intelligence.

### B
The backend developer can replace mock logic with real logic without requiring a UI rewrite.

### C
Every major continuity conclusion can be traced to evidence.

### D
AI failures cannot silently become final risk classifications.

### E
The simulator cannot corrupt baseline organization state.

### F
A user cannot interpret candidate ranking as an autonomous staffing decision without ignoring explicit product wording.

### G
The entire application can be reset into a known demo state easily.

---

# 96. Primary Golden Architecture Story

When explaining the architecture to judges:

> ContinuityAI uses AI where AI is strongest: interpreting fragmented, unstructured engineering evidence. It converts incidents, pull requests, tickets, and documentation into structured capability evidence. A deterministic evidence and continuity engine then calculates readiness, redundancy, and continuity risk using transparent rules. That evidence-backed graph powers counterfactual simulations such as “What happens if Alex is unavailable?” and helps managers compare technical backup candidates and generate targeted knowledge-transfer plans. Human managers remain responsible for staffing decisions.

That is the architectural story.

---

# 97. Why This Architecture Fits the Product

Traditional engineering tooling provides activity and ownership data.

ContinuityAI adds a semantic and reasoning layer:

```text
Engineering artifacts
        ↓
Technical meaning
        ↓
Capability evidence
        ↓
Knowledge graph
        ↓
Continuity reasoning
        ↓
Counterfactual decisions
        ↓
Mitigation
```

The architecture mirrors the product thesis.

---

# 98. Phase 0 Technical Freeze Checklist

Both developers should explicitly approve:

- [ ] Next.js / React frontend
- [ ] Python / FastAPI backend
- [ ] modular monolith
- [ ] SQLite for MVP
- [ ] stable `/api/v1` boundary
- [ ] frontend mock-first development
- [ ] backend owns all domain intelligence
- [ ] AI provider abstraction
- [ ] AI outputs structured semantic evidence only
- [ ] deterministic evidence aggregation
- [ ] deterministic readiness engine
- [ ] deterministic continuity/risk engine
- [ ] relational storage + typed graph abstraction
- [ ] no Neo4j required
- [ ] simulation uses temporary graph state
- [ ] simulation type is ENGINEER_UNAVAILABLE only
- [ ] recommendation returns up to 3 technical candidates
- [ ] manager chooses candidate
- [ ] mitigation is generated after human selection
- [ ] hidden ground truth isolated from app runtime
- [ ] golden path protected throughout development
- [ ] API contract changes require coordination

---

# 99. Phase 1 Starting Tasks

Once this document is accepted, create the following parallel work.

## Developer A — first tasks

```text
A1. Initialize FastAPI project.
A2. Create Pydantic enums from DOMAIN_MODEL.md.
A3. Create API DTO schemas from API_CONTRACT.md.
A4. Add the 10 `/api/v1` routes with mock responses.
A5. Initialize SQLite.
A6. Add baseline repository structure.
A7. Add pytest health/API tests.
```

Stop after the contract-level backend skeleton is working.

---

## Developer B — first tasks

```text
B1. Initialize Next.js + TypeScript project.
B2. Create TypeScript enums/types from API_CONTRACT.md.
B3. Create mock JSON payloads.
B4. Build application shell/navigation.
B5. Build Payments Platform dashboard.
B6. Build initial Payment Gateway system page.
B7. Add mock API adapter.
```

Stop after the frontend shell works against the frozen mocks.

---

# 100. Phase 1 Integration Gate

Before moving into AI or real graph logic, both developers must prove:

```text
GET /api/v1/platforms
```

returns the same shape the dashboard already renders from mock JSON.

Then switch the dashboard from:

```text
mock
```

to:

```text
FastAPI
```

without changing the visual component contract.

If this succeeds, Phase 0 architecture has done its job.

---

# 101. Final Architecture Principle

The simplest way to remember the whole system is:

```text
AI understands.
Rules decide.
Graph connects.
Simulation asks "what if?"
Managers decide.
```

That principle should remain intact throughout implementation.
