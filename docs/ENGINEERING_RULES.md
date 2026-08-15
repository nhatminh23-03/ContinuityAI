# ContinuityAI — Engineering Rules

Working reference. Load this instead of re-reading the full specifications. If this file and an
authoritative document disagree, the document wins and this file gets fixed.

## The one-line architecture

> **AI understands. Rules decide. Graph connects. Simulation asks "what if?" Managers decide.**

AI extracts semantic evidence from artifacts. It never emits readiness, risk, employee value, or
a chosen candidate. Deterministic rules own those. The frontend renders them.

## Ownership

| Layer | Owns |
|---|---|
| **Backend** (Person A) | AI extraction, graph construction, evidence strength/freshness/aggregation, readiness, evidence confidence, exposure, Continuity Risk Index and class, gap counts, drift status, simulation, candidate comparison, mitigation generation and state |
| **Frontend** (Person B) | Rendering, navigation, interaction state, filters, sorting, graph layout, charts, pre-request selection state, modals, display formatting |
| **Human** (the manager) | Confirming business criticality, challenging assessments, selecting a backup candidate, editing a plan, approving a plan |

The frontend may derive display labels, sorted lists, abbreviated text, and progress-bar
percentages from values the API already supplied. It may **not** compute risk, readiness,
evidence confidence, exposure, technical overlap, or risk class. Banding an index into a class is
domain logic, not formatting.

## Conventions

- **JSON:** `snake_case` keys, everywhere, both directions.
- **Dates:** ISO-8601 — `2026-05-14` or `2026-05-14T19:22:11Z`.
- **IDs:** typed, lowercase snake_case, stable. Names are never identifiers.
  `platform_payments`, `system_payment_gateway`, `component_gateway_integration`,
  `cap_incident_recovery`, `eng_alex_chen`, `evidence_inc_184`, `sim_001`, `plan_001`, `task_001`.
  Engineer IDs use the full name: `eng_alex_chen`, not `eng_alex`.
- **Null:** only when the concept exists but the value is unknown. Prefer an explicit enum state
  such as `INSUFFICIENT_EVIDENCE` where the state itself is meaningful.
- **Errors:** one envelope, `{"error": {"code", "message", "details"}}`. Switch on `error.code`,
  never on message text. Codes: `NOT_FOUND` (404), `VALIDATION_ERROR` (422),
  `INSUFFICIENT_EVIDENCE` (409), `AI_EXTRACTION_FAILED` (502/500), `GRAPH_INCONSISTENCY` (500),
  `SIMULATION_FAILED` (500), `MITIGATION_GENERATION_FAILED` (500), `INTERNAL_ERROR` (500).

## Enums

Exact spelling and casing. Changing any value is a Category C decision.

| Enum | Values |
|---|---|
| `BusinessCriticality` | `LOW` `MEDIUM` `HIGH` `CRITICAL` |
| `OperationalCriticality` | `LOW` `MEDIUM` `HIGH` `CRITICAL` |
| `ReadinessLevel` | `NONE` `EXPOSED` `ASSISTED` `PRACTICED` `VALIDATED` |
| `CapabilityExposure` | `COVERED` `DEGRADED` `CRITICAL_GAP` `INSUFFICIENT_EVIDENCE` |
| `ContinuityRiskClass` | `LOW` `MODERATE` `HIGH` `CRITICAL` |
| `EvidenceStrength` | `WEAK` `MODERATE` `STRONG` |
| `EvidenceConfidence` | `LOW` `MEDIUM` `HIGH` |
| `Freshness` | `FRESH` `AGING` `STALE` |
| `KnowledgeDriftStatus` | `NEW_RISK` `RISK_INCREASED` `STABLE` `RISK_REDUCED` |
| `EvidenceSourceType` | `COMMIT` `PULL_REQUEST` `CODE_REVIEW` `ISSUE` `TICKET` `INCIDENT` `DOCUMENT` `TECHNICAL_DISCUSSION` `MANAGER_ATTESTATION` |
| `EvidenceRole` | `EXPOSURE` `CONTRIBUTION` `ASSISTED_EXECUTION` `INDEPENDENT_EXECUTION` `KNOWLEDGE_CAPTURE` |
| `GraphNodeType` | `PLATFORM` `SYSTEM` `COMPONENT` `CAPABILITY` `ENGINEER` `EVIDENCE` |
| `GraphEdgeType` | `HAS_SYSTEM` `HAS_COMPONENT` `REQUIRES_CAPABILITY` `DEMONSTRATES` `SUPPORTED_BY` `DECLARED_OWNER` |
| `SimulationType` | `ENGINEER_UNAVAILABLE` |
| `SimulationScopeType` | `SYSTEM` `PLATFORM` — only `SYSTEM` implemented in MVP |
| `TechnicalOverlap` | `LOW` `MEDIUM` `HIGH` |
| `MitigationPlanStatus` | `DRAFT` `APPROVED` |
| `MitigationTaskType` | `KNOWLEDGE_REVIEW` `SHADOWING` `PRACTICE` `RECOVERY_DRILL` `DOCUMENTATION` `ARCHITECTURE_REVIEW` |

Edge direction: `Platform→System`, `System→Component`, `Component→Capability`,
`Engineer→Capability` (`DEMONSTRATES`), `Coverage→Evidence` (`SUPPORTED_BY`),
`Engineer→System` (`DECLARED_OWNER`).

## The four scored concepts

They are orthogonal. Do not collapse them.

| Concept | Attaches to | Answers |
|---|---|---|
| **Readiness** | the `(engineer, capability)` edge | What has this one person demonstrably done? |
| **Exposure** | Capability, rolled up to System | Does redundant coverage exist across everyone? |
| **Continuity Risk Index / Class** | Capability, System | How severe, for comparison and sorting? |
| **Evidence Confidence** | coverage, capability, system | How much do we trust the underlying data? |

`Risk: HIGH` with `Confidence: LOW` is legitimate and meaningful. The index is **not** a
probability of anything. Risk attaches to Capability, System, and Platform — **never** to an
Engineer.

`DEGRADED` means coverage exists but resilience does not (typically one adequate engineer).
`CRITICAL_GAP` means no adequate coverage remains. A sole-expert capability is `DEGRADED` at
baseline and reaches `CRITICAL_GAP` when that engineer is simulated unavailable.

## Endpoints — all 10, all under `/api/v1`

| # | Method | Path | Purpose |
|---|---|---|---|
| 1 | GET | `/platforms` | Dashboard platform summaries |
| 2 | GET | `/platforms/{platform_id}/systems` | Systems in a platform |
| 3 | GET | `/systems/{system_id}` | System detail + components |
| 4 | GET | `/systems/{system_id}/graph` | Contextual graph (`?focus_capability_id`) |
| 5 | GET | `/capabilities/{capability_id}` | Capability detail + engineer coverage |
| 6 | GET | `/capabilities/{capability_id}/evidence` | Provenance / "Why?" (`?engineer_id`) |
| 7 | POST | `/simulations` | `ENGINEER_UNAVAILABLE` counterfactual |
| 8 | POST | `/recommendations/backup-candidates` | Up to 3 technical candidates |
| 9 | POST | `/mitigation-plans` | Generate plan → `201`, status `DRAFT` |
| 10 | POST | `/mitigation-plans/{plan_id}/approve` | Approve; optional `tasks` array applies edits |

Adding an 11th endpoint is a Category C decision. The evidence drawer gets per-engineer evidence
from endpoint 6 with `?engineer_id=` — the coverage DTO deliberately carries no evidence IDs.

## Source of truth

| Subject | Document |
|---|---|
| Scope, journey, UX, acceptance criteria | `PRD.md` |
| Wire format — endpoints, fields, enums, JSON | `API_CONTRACT.md` |
| Internal semantics, invariants, rule intent | `DOMAIN_MODEL.md` |
| Module layout, technology, testing, deployment | `ARCHITECTURE.md` |
| Process, ownership, decision categories | `TEAM_WORKFLOW_PERSON_A_B.md` |
| Settled Category C decisions | `DECISIONS.md` |

Implementation is never authoritative. Fixtures are never a second specification — where a
fixture and `API_CONTRACT.md` disagree, the fixture is wrong.

## Decision categories

- **A — decide alone.** Function names, local component structure, test helpers, private
  technique, behaviour-preserving refactors.
- **B — tell your teammate before merging.** Adding a library, restructuring an internal module,
  changing mock infrastructure, changing the database implementation.
- **C — decide together, and log it in `DECISIONS.md`.** API contract change, enum change, domain
  semantics, risk or readiness rule meaning, UI interpretation of risk, responsible-AI boundary,
  major scope change.

Any new UX requirement must name the DTO field that will carry its data before it is accepted.

## Prohibited language and outputs

Never produce these, in the UI, the API, a prompt, a log, or a variable name.

| Never | Instead |
|---|---|
| "Alex is a 93 risk" | "Payment Gateway has a 93/100 Continuity Risk Index" |
| "Jordan cannot recover Payments" | "No qualifying independent recovery evidence was found for Jordan" |
| "Maria is the best employee" | "Maria has the strongest technical overlap among evaluated candidates" |
| "92% chance of failure" | "Continuity Risk Index 92/100; not a failure probability" |
| "Maria = 87% match" | "Technical overlap: HIGH" |
| "critical employee", "irreplaceable person" | "single point of knowledge concentration" |
| "weak engineer", "low-value engineer" | name the capability and its evidence instead |
| Simulation predicts an outage | "Coverage simulation; not an outage prediction." |

No field, score, or ranking for employee productivity, value, importance, layoff, promotion,
bonus, salary, engagement, personality, sentiment, loyalty, working hours, or performance review.
No autonomous staffing. Absence of evidence is never phrased as inability. `INSUFFICIENT_EVIDENCE`
is a valid, preferred answer over a manufactured classification.

Never ingest private messages, personal email, keystrokes, mouse activity, screen monitoring,
working hours, location, presence, sentiment, or non-technical behaviour. Hidden ground truth
under `data/ground_truth/` is readable by evaluation scripts only, never at application runtime.

## Standing constraints

- `main` stays runnable. Short-lived feature branches, small frequent merges.
- The golden path is the highest-priority feature. If it breaks, stop and repair it.
- Never modify `backend/` if you are Person B, or `frontend/` if you are Person A, without saying so.
- Prefer the smallest change that satisfies the requirement. No unrequested libraries or abstractions.
- Log meaningful work in `BUILD_WITH_BOB.md`; end each session with `HANDOFF.md`.

## Hero scenario

NovaPay → Payments Platform → Payment Gateway → Gateway Integration → Incident Recovery.
Engineers `eng_alex_chen`, `eng_maria_gomez`, `eng_jordan_lee`. Jordan is the declared CODEOWNERS
owner; Alex has the strongest demonstrated coverage. Alex unavailable → Incident Recovery
`DEGRADED → CRITICAL_GAP`, Provider Failover `COVERED → DEGRADED`, Retry Logic stays `COVERED`,
system risk 74 → 93 (HIGH → CRITICAL). Maria returns HIGH overlap, Jordan MEDIUM. Manager selects Maria, plan
generates `DRAFT`, manager approves. Use this scenario in tests, fixtures, screenshots, and demo.

## The rules, as implemented

Previously this file omitted the readiness thresholds and the risk rules, so the document everyone
is told to load instead of the specifications did not contain the rules the backend is built on.
They are below. Authoritative source remains `PRD.md` sections 16.2, 17.1 and 17.2; where this
summary and the code disagree, `backend/tests/test_continuity_engine.py` is the tie-breaker because
it pins the frozen numbers.

### Readiness — `app/continuity/readiness.py`

Computed per `(engineer, capability)` from that pair's evidence. Never written directly, never set by
the AI layer.

| Level | Condition |
|---|---|
| `VALIDATED` | 2+ independent executions, across 2+ artifact types among the strong evidence, at least one still fresh, no conflicts |
| `PRACTICED` | 1+ independent execution that has not gone stale, plus at least one supporting item |
| `ASSISTED` | 2+ items including assisted execution, a contribution, or authored documentation. Also where a stale independent execution lands |
| `EXPOSED` | Any qualifying evidence, none of it execution |
| `NONE` | No qualifying evidence |

The `EXPOSED → ASSISTED → PRACTICED` progression is about **independence**, never volume: the rules
read `independent_execution_count`, not `total`. Twenty reviews stay `EXPOSED`.
`PRACTICED → VALIDATED` is repetition **and** source diversity — two incidents from the same pager
rotation are one kind of proof.

### Exposure and risk class — `app/continuity/exposure.py`

Adequate coverage means readiness of `PRACTICED` or better **and** evidence that is not stale.

| Adequate engineers | CRITICAL capability | HIGH capability | MEDIUM / LOW |
|---|---|---|---|
| 0 | `CRITICAL_GAP` / CRITICAL | `CRITICAL_GAP` / HIGH | `DEGRADED` / MODERATE |
| 1 | `DEGRADED` / HIGH | `DEGRADED` / MODERATE | `COVERED` / MODERATE |
| 2+ | `COVERED` / LOW if any is VALIDATED, else MODERATE | same | same |

Fewer than two evidence records, or no adequate coverage with every coverage at LOW confidence,
returns `INSUFFICIENT_EVIDENCE` with a null index and null class.

`DEGRADED` means coverage exists but resilience does not. `CRITICAL_GAP` means no adequate coverage
remains. Keeping them separate is what lets the simulation *create* a gap (decision CI-03). Risk
class scales with criticality (DEC-07).

### Continuity Risk Index — `app/continuity/exposure.py`

Class anchor, plus modifiers, clamped to the class band. The class is authoritative; the index is a
derived comparison number and never a probability.

| Class | Band | Anchor |
|---|---|---|
| LOW | 0-39 | 20 |
| MODERATE | 40-59 | 50 |
| HIGH | 60-79 | 70 |
| CRITICAL | 80-100 | 90 |

| Modifier | Delta |
|---|---|
| `SOLE_ADEQUATE_ENGINEER` | +1 |
| `BEST_ALTERNATIVE_ASSISTED` | +1 |
| `BEST_ALTERNATIVE_EXPOSED_OR_NONE` | +3 |
| `SECOND_PRACTICED_ENGINEER` | -5 |
| `SECOND_VALIDATED_ENGINEER` | -8 |
| `RUNBOOK_MISSING` / `RUNBOOK_INCOMPLETE` / `RUNBOOK_CURRENT` | +5 / +3 / -3 |

Coverage modifiers are mutually exclusive: with two or more adequate engineers the second one *is*
the backup, so `SECOND_*` applies and `BEST_ALTERNATIVE_*` does not. `HIGH_OPERATIONAL_DEPENDENCY`
from the PRD table is not implemented (RECOMMENDATIONS.md R-08).

Worked example — Incident Recovery: CRITICAL capability, one adequate engineer (Alex VALIDATED),
best alternative ASSISTED (Maria), runbook not assessed. Class HIGH, anchor 70, +1 sole adequate,
+1 best alternative assisted = **72**.

### Aggregation — `app/continuity/aggregation.py`

System index is the **maximum** across its capabilities, and the class is that capability's class.
Severe gaps are never averaged away (PRD section 17.3); breadth is communicated through the counts
and the fired rules. System exposure is the worst capability exposure, ordering
`CRITICAL_GAP > DEGRADED > INSUFFICIENT_EVIDENCE > COVERED`. System evidence confidence is the
minimum across capabilities that are degraded or worse. Platforms get no index of their own
(decision CI-10) — only the highest system index, total critical gaps, and drift.

### Where the numbers come from

Nothing in `fixtures/` is asserted. `python -m scripts.seed_demo` derives every readiness value from
the committed artifact corpus, and `python -m scripts.refresh_fixtures --check` fails if a fixture
has drifted from what the engine produces.
