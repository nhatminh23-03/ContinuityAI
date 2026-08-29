# ContinuityAI — Decision Log

A running log of joint decisions. Append; do not rewrite history.

A decision belongs here when it is **Category C** under `TEAM_WORKFLOW_PERSON_A_B.md` §32 — an
API contract change, an enum change, domain semantics, risk or readiness rule meaning, a UI
interpretation of risk, a responsible-AI boundary, or a major scope change. Category A and B
decisions belong in pull-request descriptions, not here.

Each entry records the date, the decision, why, and which documents changed.

---

## Standing rules adopted

### SR-01 — Authority is split by subject, not by document rank

**Date:** 2026-08-14 · **Agreed by:** Person A and Person B

Replaces the flat source-of-truth ranking in `TEAM_WORKFLOW_PERSON_A_B.md` §5.

| Subject | Authoritative document |
|---|---|
| Product scope, user journey, UX requirements, acceptance criteria | `PRD.md` |
| Wire format — endpoints, field names, enum spelling, JSON shape | `API_CONTRACT.md` |
| Internal semantics — entity meaning, invariants, rule intent | `DOMAIN_MODEL.md` |
| Module layout, technology, testing, deployment | `ARCHITECTURE.md` |
| Process, ownership, decision categories | `TEAM_WORKFLOW_PERSON_A_B.md` |

**Rationale.** A flat ranking put `PRD.md` above `API_CONTRACT.md`, which meant that every enum
conflict resolved in favour of the PRD — replacing frozen enum values, ID formats, and field
names that both developers had already built against. That is incompatible with the concept of a
frozen contract. Where the PRD requires behaviour the contract cannot carry, the contract is
amended through the §6 change process rather than being silently overridden.

**Documents affected:** `TEAM_WORKFLOW_PERSON_A_B.md` §5.

---

### SR-02 — A UX requirement must name the field that will carry its data

**Date:** 2026-08-14 · **Agreed by:** Person A and Person B

Any new or amended UX requirement must name the DTO field, graph edge, or enum that will supply
its data before the requirement is accepted. A requirement with no transport is not accepted.

**Rationale.** Six of the fourteen blocking issues in the Phase 0 audit (CI-03, CI-07, CI-08,
CI-09, CI-10, CI-13) came from the same gap: the PRD specified product behaviour that the API
contract had been frozen without a way to deliver. Each one surfaced only when the frontend
tried to build the screen. This check catches the class of problem rather than the instances.

**Documents affected:** process rule; applies to all specification changes.

---

## Contract resolutions — Phase 0 audit

All 34 issues in `CONTRACT_ISSUES.md` were reviewed and agreed jointly by Person A and Person B
on **2026-08-14**. Issue IDs below refer to that register, which is retained unmodified as the
record of the pre-resolution state.

### Blocking

| ID | Decision | Rationale | Documents affected |
|---|---|---|---|
| CI-01 | Split authority by subject matter | See SR-01 | `TEAM_WORKFLOW_PERSON_A_B.md` |
| CI-02 | `PRACTICED` = hands-on without significant support, but limited to controlled/lower-risk contexts or lacking repetition, diversity, or recency | The ASSISTED→PRACTICED boundary is independence; the PRACTICED→VALIDATED boundary is production context, repetition, and source diversity. The frozen mitigation plan targets `PRACTICED` and reaches it through staged practice, so PRACTICED must admit controlled-context execution. | `DOMAIN_MODEL.md` §5.3, `API_CONTRACT.md` §5.3, `PRD.md` §16.2 |
| CI-03 | Separate *no redundancy* from *no coverage* in the exposure model | See detailed entry below | `API_CONTRACT.md`, `DOMAIN_MODEL.md`, `PRD.md`, `ARCHITECTURE.md`, `TEAM_WORKFLOW_PERSON_A_B.md` |
| CI-04 | `Freshness` keeps three values: `FRESH / AGING / STALE` | Two of three documents already agreed; a 3-value scale needs three badge states, and the PRD's four-value scale was never reflected in any DTO. PRD thresholds carried over, folding CURRENT and RECENT into FRESH. | `PRD.md` §8, §16.3, §16.4, App. B; `DOMAIN_MODEL.md` §18 |
| CI-05 | Six graph edge types: `HAS_SYSTEM`, `HAS_COMPONENT`, `REQUIRES_CAPABILITY`, `DEMONSTRATES`, `SUPPORTED_BY`, `DECLARED_OWNER`. Direction `Engineer → System` for ownership. `ADJACENT_TO` dropped. | The wire enum had no ownership edge, so declared-vs-demonstrated could not be drawn. Engineer-origin direction matches `DEMONSTRATES`. `ADJACENT_TO` was already marked optional and is computed internally by the candidate engine. | `API_CONTRACT.md` §5.12, `DOMAIN_MODEL.md` §37, `PRD.md` §13.2 |
| CI-06 | The five UPPER_SNAKE `EvidenceRole` values are authoritative at every layer including AI extraction | A smaller closed vocabulary is easier to validate and to explain in the provenance drawer. Mapping recorded below. | `PRD.md` §15.3, App. B.1 |
| CI-07 | Add `declared_ownership` to `SystemDetail` | The declared-vs-demonstrated mismatch is the demo's opening hook and belongs on System Detail, one level above the capability evidence view where it was the only place it existed. Selecting "strongest demonstrated coverage" is domain intelligence and cannot be derived client-side. | `API_CONTRACT.md` §6.3, §8.3 |
| CI-08 | Add `rules_triggered: string[]` to `CapabilityDetail` and the capability-evidence `assessment` block | AC-07, FR-013, and FR-024 all require displaying fired rules; the data existed in the backend with no field to travel in. Values are machine-readable reason codes; the frontend owns the display copy so responsible-AI wording stays under joint review. | `API_CONTRACT.md` §6.5, §8.6, §12.1; `DOMAIN_MODEL.md` §9.1 |
| CI-09 | Add `ContinuityRiskClass { LOW, MODERATE, HIGH, CRITICAL }` and `continuity_risk_class` to `SystemSummary`, `SystemDetail`, `CapabilityDetail` | PRD §17.1 makes the class authoritative and the index derived, yet only the index crossed the API. Banding in React is domain logic, and §17.2's clamping rule means band edges are not a pure function of the index. | `API_CONTRACT.md` §5.18, §6, §15, §16; `DOMAIN_MODEL.md` §5.15, §7.1, §9.1 |
| CI-10 | Hold the no-platform-risk freeze; platform rows show highest system risk index | Inventing a second aggregation formula is what the freeze exists to prevent, and the manager's "where do I look first?" job is served by highest system risk plus gap count. | `PRD.md` §11.1, §17.3 |
| CI-11 | Typed snake_case IDs. Engineer IDs use the full-name form: `eng_alex_chen`, `eng_maria_gomez`, `eng_jordan_lee` | Type prefixes make IDs debuggable in logs and graph payloads. Full-name engineer IDs avoid a rename once the dataset holds more than one Alex. | `PRD.md` §13.1, §24, App. B; `API_CONTRACT.md` §4.2 and all examples; `DOMAIN_MODEL.md` §4 |
| CI-12 | Plan edits are submitted with the approval request via an optional `tasks` array; no separate endpoint | Preserves the manager's edit-before-approve step and AC-10 in full without an 11th endpoint or plan-mutation semantics. Permitted only while status is `DRAFT`. | `API_CONTRACT.md` §8.10 |
| CI-13 | **OPEN** — conditional defer, see below | | |
| CI-14 | Fixtures live in repository-root `fixtures/`, jointly owned | Fixtures inside `frontend/` become frontend mocks Person A never reads — the "second unofficial API specification" the workflow document warns against. Shared placement lets backend API tests validate against the same payloads. | `API_CONTRACT.md` §14, `ARCHITECTURE.md` §6, §11 |

### Deferrable

| ID | Decision | Rationale | Documents affected |
|---|---|---|---|
| CI-15 | `MitigationTaskType` includes `ARCHITECTURE_REVIEW` (6 values) | Both the PRD demo plan and the domain walkthrough open with an architecture review. | `API_CONTRACT.md` §5.17 |
| CI-16 | Enum type is named `KnowledgeDriftStatus` | Matches the product term "Knowledge Drift"; field name `drift_status` unchanged. | `DOMAIN_MODEL.md` §5.8 |
| CI-17 | `MitigationPlanStatus` keeps two values; no `REJECTED` | A rejected plan in MVP is one the manager never approves — no state to persist, nothing in the demo exercises it. | `PRD.md` §20.2, FR-019 |
| CI-18 | Add optional `conflicting_evidence[]` to the capability-evidence response; no new exposure enum value | A fifth exposure state complicates every badge and rule for a case absent from the seed data. Conflicting evidence already drives `LOW` evidence confidence. | `API_CONTRACT.md` §8.6 |
| CI-19 | Add `criticality_source` to `SystemDetail` | Showing that a human confirmed criticality is part of the human-in-the-loop story. | `API_CONTRACT.md` §6.3, §8.3 |
| CI-20 | Reduce the dashboard summary strip to critical gaps + drift | Three of its four numbers had no source. FR-023 is satisfied by per-row drift status; AC-01 only tests highest-risk system and gap count. | `PRD.md` §11.1 |
| CI-21 | `API_CONTRACT.md` simulation shape is authoritative; `covered_capability_count` added to before/after states | Per SR-01. The covered count was already a System-derived field, so its absence read as an oversight. | `DOMAIN_MODEL.md` §23, §24; `API_CONTRACT.md` §8.7 |
| CI-22 | `SimulationScopeType` keeps `SYSTEM \| PLATFORM`; only `SYSTEM` is implemented in MVP | The enum costs nothing and leaves the door open; multi-system rollup is real work with no demo beat. | `DOMAIN_MODEL.md` §22.1, `PRD.md` §18.2, §18.3 |
| CI-23 | `acceptance_criteria` and `linked_evidence_ids` added to the domain `MitigationTask`; `sequence` and `plan_id` marked persistence-only | Acceptance criteria are required by AC-10 and were missing from the domain model. Wire ordering uses array order; `sequence` keeps ordering stable across a database round-trip. | `DOMAIN_MODEL.md` §30 |
| CI-24 | Add optional `linked_evidence_ids` to plan tasks | Lets the plan screen link back into the evidence drawer that justified it. | `API_CONTRACT.md` §8.9 |
| CI-25 | Provenance is nested; `source_url` added inside it | FR-006 calls for a source URI where available. | `DOMAIN_MODEL.md` §12.1, `API_CONTRACT.md` §6.7, §8.6 |
| CI-26 | `insufficient_evidence_count` added to the domain System derived fields | Present in six contract examples and both code sketches; its absence would have caused a missing required response field. | `DOMAIN_MODEL.md` §7.1 |
| CI-27 | **Platform** is the single domain term. "Portfolio Dashboard" may remain as a screen title. | Platform is the wire format, the enum value, and the ID prefix. Domain model rule 4.1.3 already permits UI labels to differ from identifiers. | `PRD.md` throughout |
| CI-28 | `evidence_inc_184` — lowercase | Typo in the ID convention section, the one place developers look the format up. | `API_CONTRACT.md` §4.2 |
| CI-29 | Handoff notes live at repository-root `HANDOFF.md` | Sits alongside `BUILD_WITH_BOB.md`; more discoverable than a path inside `docs/`. | `TEAM_WORKFLOW_PERSON_A_B.md` §29 |
| CI-30 | `ContinuityAI_PRD_v1.0.md` renamed to `PRD.md`; the `.docx` moved to `docs/archive/` | Every cross-reference in every document pointed at `PRD.md`, which did not exist. Two copies of the top specification is a guaranteed drift source. | filesystem |
| CI-31 | PRD AC-14 holds the authoritative performance targets | AC-14 is testable and specific; the architecture figure was informal and stricter. | `ARCHITECTURE.md` §56 |
| CI-32 | The simulation disclaimer is static frontend copy, not an API field: *"Coverage simulation; not an outage prediction."* | Reviewed once here, reused everywhere; cannot be forgotten by a backend code path. Recorded in `ENGINEERING_RULES.md`. | `ENGINEERING_RULES.md` |
| CI-33 | Seed-data constraint: `cap_incident_recovery` must yield at least two backup candidates | AC-08 requires two; the API permits zero. This is a data requirement, not a contract change. The empty-state UI is still built and tested. | seed data (Person A) |
| CI-34 | No contract change; the evidence drawer fetches from `GET /capabilities/{id}/evidence?engineer_id=`. `last_demonstrated_at` added to `EngineerCoverage`. | The filtered evidence endpoint already answers this; the coverage DTO deliberately carries no evidence IDs. The freshness row in the Why drawer needs the timestamp. | `API_CONTRACT.md` §6.4, `ENGINEERING_RULES.md` |

---

## Detailed entries

### CI-03 — Exposure separates *no redundancy* from *no coverage*

**Date:** 2026-08-14 · **Agreed by:** Person A and Person B

**Root cause.** This was not documentation drift. Under rule R1 as originally written, a
capability could only lose adequate coverage on engineer removal if it *already* had no
PRACTICED-or-VALIDATED backup — which is R1's own trigger condition. The simulation could
therefore never create a new critical gap, and the frozen `"before": {"critical_gap_count": 0}`
state was unreachable. The three contradictory baselines across the documents were a symptom.

**Decision.** Separate the two conditions in the exposure model:

- A capability whose only adequate coverage is a single engineer is `DEGRADED` at baseline —
  coverage exists, resilience does not.
- `CRITICAL_GAP` means no adequate coverage would remain.

**Resulting seeded baseline — Payment Gateway:**

| Capability | Baseline | After Alex unavailable |
|---|---|---|
| Incident Recovery | `DEGRADED` | `CRITICAL_GAP` |
| Certificate Management | `DEGRADED` | `CRITICAL_GAP` |
| Provider Failover | `COVERED` | `DEGRADED` |
| Retry Logic | `COVERED` | `COVERED` |
| Monitoring | `COVERED` | `COVERED` |

Baseline: 0 critical gaps, 2 degraded, 3 covered, index 74, class HIGH. After: 2 critical gaps,
1 degraded, 2 covered, index 93, class CRITICAL. See DEC-01 for how the baseline index was
settled at 74 rather than the 58 in the original amendment text.

**Documents affected:** `API_CONTRACT.md` §6.1, §6.2, §6.3, §6.5, §6.8, §6.10, §8.1, §8.2, §8.3,
§8.6, §8.7; `DOMAIN_MODEL.md` §19, §20; `PRD.md` §9 (S1), §11.1, §17.1, §18.3, §27;
`ARCHITECTURE.md` §29, §43, §44; `TEAM_WORKFLOW_PERSON_A_B.md` §22.

**Consequence not in the original amendment list.** The Payments Platform aggregate is forced
to `highest_system_risk_index: 74` and `critical_gap_count: 1` (Refund Engine's single gap).
Payment Gateway remains the highest-risk system, ahead of Refund Engine at 72.

---

### CI-06 — EvidenceRole mapping

**Date:** 2026-08-14 · **Agreed by:** Person A and Person B

The PRD's seven extraction values map onto the five frozen roles as follows. Recorded so the
finer distinctions are not lost if extraction quality later needs tuning.

| PRD extraction value | Frozen `EvidenceRole` |
|---|---|
| `observed`, `reviewed` | `EXPOSURE` |
| `implemented` | `CONTRIBUTION` |
| `assisted` | `ASSISTED_EXECUTION` |
| `independent_resolution` | `INDEPENDENT_EXECUTION` |
| `authored`, `designed` | `KNOWLEDGE_CAPTURE` |

`designed` maps to `KNOWLEDGE_CAPTURE`, resolved 2026-08-14 — `DOMAIN_MODEL.md` §5.10 names
"architecture guidance" explicitly in that role's definition, and design work reaches the
evidence layer as a design or architecture document. Implementation-level design that produces
only code maps to `CONTRIBUTION` via `implemented`.

---

### CI-13 — Challenge workflow: conditional defer

**Date:** 2026-08-14 · **Status:** **OPEN** · **Review at:** Phase 7 checkpoint

Not a flat deferral. Person A will cost a minimal version: one endpoint that records a
`MANAGER_ATTESTATION` evidence record against a single `(engineer, capability)` pair and
recomputes that capability only.

Until the Phase 7 decision:

- `FR-020`, `AC-11`, and `PRD.md` §21 stay in the specifications. They are not removed.
- The "Challenge Assessment" action is **not** built in the provenance drawer.

**Rationale for not deciding now.** The full workflow re-runs extraction, aggregation, readiness,
and risk on demand — the most expensive unbuilt feature in the register — and appears in no demo
beat. The minimal version may be affordable, and that is worth measuring before cutting an MVP
goal, a functional requirement, an acceptance criterion, a user scenario, a domain entity, and a
named service.

---

## Follow-up decisions

### DEC-01 — Payment Gateway baseline is 74 / HIGH

**Date:** 2026-08-14 · **Closes:** OPEN-02

The CI-03 decision text specified "index 58, class HIGH", but 58 falls in the `MODERATE` band
(40–59) and `PRD.md` §17.2 clamps the index to the band of its class. The two could not both hold.

**Decision.** The baseline index moves to **74**; the class is **HIGH**.

**Rationale.** The class is authoritative and the index is derived, so the index moves rather than
the class. HIGH is also the value the rules actually produce: Incident Recovery is a CRITICAL
capability under rule R1b at 72 / HIGH, and §17.3 requires that system risk be driven by its
highest-severity capabilities and forbids averaging severe gaps away — a system containing a HIGH
capability cannot read MODERATE. Keeping 58 would have reproduced the exact defect CI-03 exists to
fix: a seeded number the rule engine cannot generate. 74 also places Payment Gateway above Refund
Engine (72), so it remains the top dashboard row and the demo's opening beat still lands.

The demo transition becomes **74 → 93, HIGH → CRITICAL**. Leading with the class change is the
better line anyway: the class is the authoritative output and the index is explicitly not a
probability.

**Documents affected:** `API_CONTRACT.md` §6.1, §6.2, §6.3, §8.1, §8.2, §8.3, §8.7; `PRD.md`
§11.1, §18.3, §24.2, §27; `ARCHITECTURE.md` §43, §44; `ENGINEERING_RULES.md`.

---

### DEC-02 — `rules_triggered` is added to `SystemDetail`

**Date:** 2026-08-14 · **Closes:** OPEN-03

`PRD.md` §11.2 puts a "Why?" link on the system page. Without a system-level field the link would
either be dead or would have to jump to an arbitrarily chosen capability.

System-level codes describe the aggregation (`CRITICAL_CAPABILITY_DEGRADED`,
`MULTIPLE_SOLE_EXPERT_CAPABILITIES`); capability-level codes stay on `CapabilityDetail`. One
field, no navigation workaround, and the backend aggregation already knows which rules fired.

**Documents affected:** `API_CONTRACT.md` §6.3, §8.3.

---

### DEC-03 — The simulation example lists all five capabilities

**Date:** 2026-08-14 · **Closes:** OPEN-05

`API_CONTRACT.md` §8.7 reported `after.critical_gap_count: 2` while listing only one capability
reaching `CRITICAL_GAP`. Certificate Management and Monitoring were added to `capability_impacts`
so the example reconciles exactly against its own before/after counts: before 0 critical /
2 degraded / 3 covered, after 2 / 1 / 2.

An example payload that does not reconcile becomes a fixture that does not reconcile.

**Documents affected:** `API_CONTRACT.md` §8.7.

---

## Open items

| ID | Item | Owner | Resolve by |
|---|---|---|---|
| OPEN-01 | CI-13 challenge workflow — cost the minimal `MANAGER_ATTESTATION` endpoint | Person A | Phase 7 checkpoint |
| OPEN-06 | `last_demonstrated_at` is on `EngineerCoverage` in §6.4 but absent from the nested coverage entries in the §6.5 example | Both | Next contract touch |

OPEN-02, OPEN-03, OPEN-04, and OPEN-05 were resolved on 2026-08-14 — see DEC-01, DEC-02, the
CI-06 detailed entry, and DEC-03 respectively.

OPEN-01 stays open by design: it turns on Person A's implementation cost, which cannot be
estimated from the specifications alone. The frontend commitment is already firm — no "Challenge
Assessment" action is built, and the provenance drawer is laid out so the action can be added
later without rework.

---

### DEC-04 — Backend scaffolded without Person A present

**Date:** 2026-08-14 · **Category:** B (tell your teammate before merging) · **Decided by:** Person B

`backend/` is Person A's ownership and the Phase 1 plan left it empty. Person B chose to scaffold
it so the API could be run locally and the Phase 1 integration gate proved before Person A starts.
Everything below is replaceable — this is a starting point, not a claim on Person A's design.

**Libraries added** (`backend/requirements.txt`), all named in `ARCHITECTURE.md` §5.2:

| Package | Version | Why |
|---|---|---|
| fastapi | 0.115.6 | HTTP/API layer |
| uvicorn[standard] | 0.34.0 | ASGI server |
| pydantic | 2.10.4 | DTO validation |
| pydantic-settings | 2.7.1 | Env configuration (`ARCHITECTURE.md` §49) |
| SQLAlchemy | 2.0.36 | Persistence, not yet wired |
| pytest | 8.3.4 | Tests |
| httpx | 0.28.1 | Required by fastapi's TestClient |

Alembic is listed in `ARCHITECTURE.md` §5.2 as optional and was **not** added — §5.2 says
migration tooling can wait until the schema stabilises.

**Module layout** follows `ARCHITECTURE.md` §6 and §14: `app/api/v1/` one module per resource,
`app/schemas/` one module per DTO group, `app/core/` for config and the error envelope,
`tests/`. No repository or service layer yet — those arrive with real persistence.

**Python version.** The venv is built on Python 3.11. The machine default `python3` is 3.9.6
(Xcode's), which is end-of-life and cannot parse the `int | None` syntax the contract's Pydantic
sketch uses.

**One behavioural choice worth reviewing.** All 10 routes set
`response_model_exclude_unset=True`. Without it FastAPI serialises unset optional fields as
`null` or `[]`, and four live responses stopped matching their fixtures — `status` on component
and engineer graph nodes, `message` on the candidate response, `linked_evidence_ids` on tasks
that have none, and `last_demonstrated_at` on coverage entries. The contract examples omit those
fields, so the responses should too. **Person A should note this when real engines replace the
stubs:** an optional field that is meant to be sent must be explicitly set, not left to a default.

**Contract note.** `API_CONTRACT.md` §6.4 defines `last_demonstrated_at` on `EngineerCoverage`,
but the §6.5 `CapabilityDetail` example omits it from its nested coverage entries. The field is
modelled as optional on both sides so the two are compatible, but the contract should be made
self-consistent. Tracked as OPEN-06.

---

## Implementation decisions — backend build

Made while implementing the backend on **2026-08-15**. Person A decided each one under time
pressure with the reasoning recorded here rather than deferring; the four marked **needs
acknowledgement** are contract-visible and should be walked through at the next sync
(RECOMMENDATIONS.md R-20).

### DEC-05 — `API_CONTRACT.md` reason-code spelling is authoritative

**Date:** 2026-08-15 · **Category:** C · **Needs acknowledgement**

Two spellings existed for the same three concepts:

| `API_CONTRACT.md` section 12.1 | `ARCHITECTURE.md` section 29 |
|---|---|
| `SINGLE_VALIDATED_ENGINEER` | `SINGLE_VALIDATED_EXPERT` |
| `NO_PRACTICED_OR_VALIDATED_BACKUP` | `NO_READY_BACKUP` |
| `INCOMPLETE_DOCUMENTATION` | `AGING_DOCUMENTATION` |

**Decision.** The contract spelling wins, and the closed list now lives in
`app/continuity/reason_codes.py` — which is what `API_CONTRACT.md` section 12.1 assigned to Person A
("Person A owns the closed list of codes").

**Rationale.** The frozen fixtures already used the contract spelling, so the frontend will have
written display copy against it. Per SR-01 the contract owns the wire format, and these values cross
the wire.

**Also decided:** index modifiers are **not** reason codes. `rules_triggered` answers "which rules
decided the classification"; a modifier only nudges the comparison number inside a band it cannot
leave. Modifiers are persisted separately on the assessment row. Without this split, Incident
Recovery would return five codes instead of the three in the fixture.

**Documents affected:** `ARCHITECTURE.md` section 29 should be amended to match.

---

### DEC-06 — AI extraction returns per-claim records, not a flat capability array

**Date:** 2026-08-15 · **Category:** C · **Needs acknowledgement**

`ARCHITECTURE.md` section 21 shows extraction returning a list of records, each with its own
engineer and evidence role. `API_CONTRACT.md` section 10.2 shows a flat array of capability strings
with a single `engineer_id` and a single `evidence_role` for the whole artifact. They are not
compatible.

**Decision.** The section 21 shape is implemented (`ArtifactExtraction` in `app/ai/schemas.py`).

**Rationale.** The section 10.2 shape cannot express the hero artifact. INC-230 shows Maria
assisting while INC-184 shows Alex resolving independently; an artifact with both participants —
which is the realistic case and the one the demo depends on — would have to discard one role. A
shape that cannot represent the hero scenario is not a candidate.

**Blast radius: none on the wire.** Extraction output is internal and never crosses the API
boundary. `API_CONTRACT.md` section 10.2 should be amended to match so the two documents agree.

---

### DEC-07 — Continuity risk class scales with operational criticality

**Date:** 2026-08-15 · **Category:** C · **Needs acknowledgement**

`PRD.md` rule R1 assigns `CRITICAL` class to any CRITICAL-**or-HIGH** capability with no adequate
coverage. R1b assigns `HIGH` to either with exactly one.

**Decision.** Exposure is unchanged, but the class scales:

| Coverage | CRITICAL capability | HIGH capability |
|---|---|---|
| no adequate engineer | `CRITICAL_GAP` / class CRITICAL | `CRITICAL_GAP` / class HIGH |
| exactly one adequate | `DEGRADED` / class HIGH | `DEGRADED` / class MODERATE |

**Rationale.** Implemented literally, every uncovered capability in the portfolio reads CRITICAL, the
criticality dimension collapses, and a HIGH capability with a gap becomes indistinguishable from a
CRITICAL one. It also makes the seeded dashboard unreachable: Refund Engine has one gap on a HIGH
capability and must read 71 / HIGH for Payment Gateway to remain the top row at 74, which a CRITICAL
class (band 80-100) forbids.

**Verified unaffected:** exposure values, all gap and degraded counts, and the entire hero scenario —
both Payment Gateway gaps are on CRITICAL capabilities and still read CRITICAL.

---

### DEC-08 — `SUPPORTED_BY` edges originate at the engineer

**Date:** 2026-08-15 · **Category:** C

The contract's canonical direction is `Coverage --SUPPORTED_BY--> Evidence`, but `GraphNodeType` has
no `COVERAGE` value, so a coverage relationship has no id to serve as an edge endpoint.

**Decision.** Emit `Engineer --SUPPORTED_BY--> Evidence` with `capability_id` in the edge metadata,
preserving the full `(engineer, capability, evidence)` triple without adding a node type.

**Rationale.** The alternative is a seventh node type, which is a larger contract change for the same
information. Evidence nodes are included only when `?focus_capability_id=` is supplied — a whole
system's evidence would put hundreds of leaves on the canvas.

---

### DEC-09 — Mitigation task ids are scoped to their plan

**Date:** 2026-08-15 · **Category:** A

`mitigation_tasks` now has a composite primary key `(plan_id, task_id)`.

**Rationale.** The contract's task ids are `task_001`, `task_002`, ... within a plan (section 8.9). A
globally unique key would either force `plan_001_task_001` onto the wire or make the second plan
collide with the first — which it did, until a test caught it.

---

### Fixture amendments — nine payloads regenerated from live engine output

**Date:** 2026-08-15 · **Category:** C · **Needs acknowledgement**

`scripts/refresh_fixtures.py` now regenerates `fixtures/` from a freshly seeded database, and
`--check` fails if any fixture is stale. Nine of the ten changed. `platforms.json` was already
correct.

| Fixture | Change | Why |
|---|---|---|
| `payments-systems.json` | 1 → 3 systems | Payments Platform has three systems; the fixture listed one, so `system_count: 3` did not reconcile |
| `payment-gateway.json` | 1 → 3 components | The single component carried 2 capability ids while the counts summed to 5. All five now belong to a component |
| `payment-gateway-graph.json` | 4 → 14 nodes, 3 → 25 edges | Was illustrative. Now the real contextual graph, including the `DECLARED_OWNER` edge |
| `incident-recovery.json` | `last_demonstrated_at` added | **Closes OPEN-06** — the field was declared in section 6.4 but omitted from the section 6.5 example |
| `incident-recovery-evidence.json` | 1 → 7 evidence records | Was a single illustrative card. Ordered strongest-role first, so `evidence_inc_184` still leads |
| `alex-simulation.json` | `summary` rewritten | Generated from the deterministic result; names both gaps and both preserved capabilities |
| `backup-candidates.json` | strengths, gaps, confidence, evidence ids | Now derived from evidence rather than hand-written. Maria's confidence is MEDIUM, not HIGH — see R-14 |
| `mitigation-plan.json` | task titles, descriptions, criteria | Generated from the capability gap |
| `mitigation-plan-approved.json` | `approved_at` pinned | A real timestamp would churn the fixture every run |

**Every frozen number survived unchanged:** Incident Recovery 72 / HIGH, Payment Gateway 74 / HIGH
with 0 critical gaps / 2 degraded / 3 covered, after simulating Alex 93 / CRITICAL with 2 / 1 / 2,
Payments highest 74, Identity highest 68, Maria HIGH overlap, Jordan MEDIUM. The rule engine
reproduces all of them from evidence rather than having them asserted — see DEC-01, which required
exactly that.

---

### OPEN-06 — closed

`last_demonstrated_at` is now always populated on `EngineerCoverage` and present in the fixture. The
field is optional in both the Pydantic and the TypeScript types, so nothing breaks either way.

### Open items after this build

| ID | Item | Owner | Resolve by |
|---|---|---|---|
| OPEN-01 | Challenge / attestation workflow (CI-13, FR-020, AC-11). **Now costed at 2-3 hours** — the recompute path exists and is already used by the seed. See RECOMMENDATIONS.md R-09 | Person A | Decide at the next sync, not at "Phase 7" |
| OPEN-07 | Runtime AI provider is rule-based. Interface, validation, and prompt specification are model-ready. See R-01 | Person A | Before the README is written |
| OPEN-08 | No real public GitHub data ingested, against the section 14.1 commitment. Adapter exists. See R-07 | Person A | Before submission, or amend the PRD |

---

## Implementation decisions — closing the remaining backend scope

Made on **2026-08-17**. Four are contract-visible and need Person B's acknowledgement; the fifth is
a data-strategy decision with a privacy dimension worth reading.

### DEC-10 — An eleventh endpoint, for the challenge workflow

**Date:** 2026-08-17 · **Category:** C · **Needs acknowledgement** · **Closes OPEN-01 / CI-13**

`POST /api/v1/capabilities/{capability_id}/challenge` is added. The contract froze ten endpoints and
`API_CONTRACT.md` section 7 says an eleventh requires both developers, so this is logged rather than
assumed.

**Why build it now.** `FR-020`, `AC-11`, user scenario S5, the `AssessmentChallenge` domain entity,
and `PRD.md` section 21 all depend on it, and there is no way to satisfy them without a write path.
CI-13 deferred the costing to "the Phase 7 checkpoint" — which, at the current pace, arrives after
the deadline, so the deferral was quietly turning into an omission rather than a decision.

**Why it is now cheap.** When it was deferred, the objection was that the full workflow "re-runs
extraction, aggregation, readiness, and risk on demand — the most expensive unbuilt feature in the
register". That is no longer true: `app/services/recompute.py` already does exactly that, and the
seed already exercises it on every run. The endpoint is a thin layer over tested machinery.

**Three actions**, matching PRD section 21:

| Action | Behaviour |
|---|---|
| `LINK_EVIDENCE` | Attach an artifact extraction missed. The manager references an existing artifact; they cannot invent one, and the engineer must be a recorded participant of it |
| `MANAGER_ATTESTATION` | Record something no artifact captured, as evidence with `source_type=MANAGER_ATTESTATION`, capped at MODERATE strength |
| `CORRECT_CAPABILITY_MAPPING` | Move an evidence record to the capability it belongs to. Both capabilities are recomputed |

**The rule the design enforces.** A manager changes *evidence*, never a score. `ChallengeRequest`
has no field for readiness, exposure, confidence, or a risk index, and a test asserts their absence.
Previous and new assessments are both persisted: a correctable assessment that cannot be audited is
worse than one that cannot be corrected, because nobody can later ask why it moved.

**Attestation is capped at MODERATE** whatever role is claimed. A MODERATE record never contributes
to the strong-source diversity `VALIDATED` requires, so no quantity of assertions can manufacture a
validated expert — the abuse case that would make the whole evidence model decorative. It can
establish `ASSISTED` or contribute to `PRACTICED`, which is the point: a manager who watched someone
do the work can say so. Implements DOMAIN_MODEL.md section 34's "lower evidentiary weight" as a
mechanism rather than a sentence.

**Additive.** Nothing that previously worked changes. The frontend can adopt it whenever the
provenance drawer is ready for a "Challenge Assessment" action; until then the endpoint is simply
unused.

---

### DEC-11 — `index_modifiers` on `CapabilityDetail`

**Date:** 2026-08-17 · **Category:** C · **Needs acknowledgement**

An optional array of `{code, delta}` is added, exposing the arithmetic behind the Continuity Risk
Index. Incident Recovery returns:

```json
"index_modifiers": [
  { "code": "SOLE_ADEQUATE_ENGINEER", "delta": 1 },
  { "code": "BEST_ALTERNATIVE_ASSISTED", "delta": 1 }
]
```

Read with the class anchor of 70, that is the whole derivation of 72.

**Rationale.** `rules_triggered` already answers "which rules fired", but the number itself was
reproducible without being inspectable. PRD section 30 lists "risk score appears arbitrary" as a high
severity risk, and showing the arithmetic is the strongest available answer to it. The data was
already computed and persisted; only the transport was missing.

Optional and additive, so it costs the frontend nothing until it is rendered.

---

### DEC-12 — `missing_evidence` widened to everyone below PRACTICED

**Date:** 2026-08-17 · **Category:** C · **Needs acknowledgement**

Previously a "no qualifying evidence found" note was emitted only for engineers below `ASSISTED`,
which in the hero scenario meant Jordan alone.

**Decision.** Emit for anyone below `PRACTICED`.

**Rationale.** Maria is `ASSISTED` and is the leading backup candidate, and "has assisted but has no
independent recovery evidence" is precisely what a manager choosing a backup needs to read. Omitting
it made the Why drawer least informative about the person the decision is actually about.

`fixtures/incident-recovery-evidence.json` gains one entry. The wording remains descriptive —
"No qualifying independent incident recovery evidence found" — never evaluative.

---

### DEC-13 — Optional bearer authentication, off by default

**Date:** 2026-08-17 · **Category:** C · **Closes part of R-03**

`API_TOKEN` is unset by default, and with it unset every endpoint is open exactly as before. When
set, `/api/v1` requires `Authorization: Bearer <token>`; `/health` is never gated so a container can
report ready.

**Rationale.** `ARCHITECTURE.md` section 50 descopes enterprise IAM, correctly. But the product
serves per-person capability assessments and "the manager approves the plan" rested on a
caller-supplied `approved_by` string, so shipping with no option at all left a responsible-AI claim
resting on nothing. A single shared token is honest about being a demo control rather than
pretending to be authorisation, and defaulting it off means the frontend developer never has to
coordinate a secret to run the demo.

Deliberately not attempted: per-user identity, roles, sessions, token rotation.

---

### DEC-14 — Real public GitHub evidence is ingested with pseudonymised identities

**Date:** 2026-08-17 · **Category:** C · **Closes R-07**

120 merged pull requests and reviews from a public repository are fetched, normalised, committed
under `data/public/`, and ingested through the same pipeline as the synthetic corpus. This satisfies
the second half of the PRD section 14.1 hybrid data strategy.

**Contributor identities are pseudonymised** onto the synthetic organisation, and the real logins are
never written to disk — including `@mentions` scrubbed out of pull request bodies, because bodies
routinely name other contributors.

**Rationale, and it is substantive rather than procedural.** This product infers capability readiness
about named people. Doing that to real engineers who never consented, from a repository they do not
work on, mapped onto an invented company, is precisely the behaviour the responsible-AI boundary in
PRD section 22 exists to prevent. PRD section 14.1 anticipated this and asked for public evidence to
be "normalized/anonymized".

Artifacts stay fully traceable — `source_url` points at the real pull request, so any conclusion can
be checked against its source. What is synthetic is the attribution, and the manifest states so
rather than leaving it to be discovered. Bots are excluded: automated codegen authors a large share
of real pull requests, and counting it as demonstrated human capability would be a measurement error.

**Pseudonyms deliberately exclude Alex, Maria, Jordan and Omar.** Those four carry the seeded hero
coverage that the frozen fixtures and the hidden ground truth both depend on, and mixing unlabelled
real activity into a labelled pair would corrupt the evaluation rather than add to it.

**The finding worth carrying into the README.** Exactly one of the 120 real artifacts produced
capability evidence. A public SDK repository's vocabulary is library maintenance — support, error
handling, tests, packaging — while the capabilities this product assesses are demonstrated in private
operational records: incidents, runbooks, on-call history. That is evidence *for* the hybrid data
strategy, and a concrete measurement of the rule-based extractor's ceiling (R-01).

---

### Fixture amendments — three payloads

`incident-recovery.json` gains `index_modifiers` (DEC-11). `incident-recovery-evidence.json` gains a
`missing_evidence` entry for Maria (DEC-12). `payment-gateway-graph.json` gains one `DEMONSTRATES`
edge — Lena Novak on Retry Logic at `EXPOSED / STALE / LOW`, derived from the real public pull
request, which is a nice illustration that old third-party activity reads as stale low-confidence
exposure rather than as capability.

All three changes are additive. **Every frozen number is unchanged**: Incident Recovery 72 / HIGH,
Payment Gateway 74 / HIGH with 0 critical gaps / 2 degraded / 3 covered, the simulation 74 → 93 and
HIGH → CRITICAL with 2 / 1 / 2, Payments highest 74, Identity highest 68, Maria HIGH overlap, Jordan
MEDIUM.

### Open items after this build

| ID | Item | Owner | Resolve by |
|---|---|---|---|
| OPEN-07 | Runtime AI provider is rule-based. Interface, validation, and prompt specification are model-ready; a provider and credential are needed. See R-01 | Both | Before the demo is recorded |
| OPEN-09 | `ARCHITECTURE.md` section 29 and `API_CONTRACT.md` section 10.2 still carry the superseded reason-code spelling and extraction shape (DEC-05, DEC-06). Amend for self-consistency | Both | Next contract touch |

OPEN-01 is closed by DEC-10. OPEN-08 is closed by DEC-14. OPEN-06 was closed by the previous
build. **OPEN-07 is closed by DEC-15**: a fourth provider was implemented and run against a
real credential, so the runtime AI provider is no longer rule-based in every configuration.

---

## Implementation decision — the OpenRouter narrative provider

Made on **2026-08-21**. One decision, and it needs **Person A's** acknowledgement rather than
Person B's, because it reopens reasoning Person A recorded and decided against, in code Person A
owns.

### DEC-15 — A second narrative path is added behind a validation gate, reopening `watsonx.py`'s deterministic-narrative decision

**Date:** 2026-08-21 · **Category:** C · **Needs Person A's acknowledgement**

`backend/app/ai/openrouter.py` adds `OpenRouterProvider`, a second model-backed `AIProvider`
implementation, selected by `AI_PROVIDER=openrouter`. It is the mirror image of `WatsonxProvider`:
extraction delegates to `DeterministicProvider` in one line and stays rule-based, while a model
writes the three manager-facing narratives — the simulation summary, a candidate's strengths and
gaps, and the mitigation plan's task titles, descriptions, and acceptance criteria.

**This overrides a decision Person A already made and documented, not an open question.**
`watsonx.py:360-362`, on `explain_candidate`:

> The structured content — which capabilities are demonstrated, assisted, or missing — is decided
> by the rules. A model here would only rephrase it, and a rephrasing that drifts is worse than a
> plain one, so the deterministic phrasing stands.

and `watsonx.py:366-371`, on `generate_mitigation_plan`:

> The deterministic plan is already gap-targeted and validated for 3-5 actions. A model could write
> warmer prose, but the plan is the artifact a manager approves and then someone executes — invented
> steps or an invented tool would be a real cost, and the structure is what carries the value. Left
> deterministic on purpose.

Both are reasoned engineering positions recorded at the time the code was written, not defaults left
unconsidered, and this decision does not treat them as wrong. It argues that the objection they
raise is answerable rather than fatal to letting a model write these three fields.

**The counter-argument, stated honestly.** The risk both passages name is real: a model that
rephrases can drift, and an invented step or an invented tool in a plan a manager approves and
someone then executes is a real cost. What is different under `openrouter` is that nothing a model
writes reaches a manager unchecked. Every narrative is drafted by the model and then validated by
`app/ai/validation.py` before it can be returned — the same discipline `validate_extraction` already
applies to claims, extended to prose: no prohibited phrase, no likelihood or percentage language, no
wording that states a person's inability rather than an absence of evidence, and no capability or
person named outside what the generator was actually given. Anything the gate rejects, and anything
that fails in transport, parsing, or shape, falls back to the deterministic template in
`app/ai/deterministic.py`. That is the exact text `watsonx.py` returns for the candidate narrative
and for the plan; its third narrative, `summarize_simulation`, is model-written there too, so the
same template is what it falls back to when `validate_simulation_summary` — the identical gate —
rejects a sentence. The model never gets the last word — the rules do, on every
single generation — so
the two passages' worry (a rephrasing that drifts, an invented step) is precisely the failure the
gate exists to catch before the output is returned to a caller.

**The gate's limits, so this is not one-sided.** `find_unattested_names`
(`app/ai/language_policy.py`) is a documented heuristic, not closed-world grounding, and its module
docstring together with the test suite in `backend/tests/test_narrative_validation.py` — no single
test covers all four, `test_known_blind_spots_of_the_name_check` alone parametrizes only two — name
what it cannot catch: a single-word invention ("ask Priya to confirm" — one capitalised word is
structurally identical to any capitalised ordinary noun), an invented capability written in lower
case, an invention on a line where every word is capitalised, where capitalisation carries no
signal to check names against, and a two-word qualifier attached to an attested name ("Refund
Processing In Europe" where "Refund Processing" is attested), because the title-tail exemption is
bounded to exactly two words. Closing the second and third needs the capability taxonomy passed
into the validator, the way `validate_extraction` already receives it — not built here.

A fifth blind spot belongs to the independence check in `validate_candidate_narrative` rather than
to the name check, and is recorded here for the same reason: that check pairs independence wording
with an unproven capability only where the strength lexically contains the capability's name, so
"has independently handled that recovery work, unaided" — the assisted-presented-as-demonstrated
failure, with the capability never named — is accepted. Resolving an oblique reference to a
capability needs a lexicon the module does not have; HARD RULE 2 of
`app/ai/prompts/candidate_narrative_system.txt` addresses it, and
`test_known_blind_spot_of_the_independence_check` pins it. Until then,
grounding is carried by the three prompt files under `app/ai/prompts/`, which state explicitly
which names, capabilities, and evidence ids may appear; the gate is the net under that instruction,
not a substitute for it. A manager reading a narrative generated under `openrouter` is protected by
validated output with documented gaps, not by output that has been proven safe.

**Nothing about the deterministic path changes.** `AI_PROVIDER` still defaults to `deterministic`,
`watsonx.py`'s `explain_candidate` and `generate_mitigation_plan` still delegate to the
deterministic templates for the reasons stated in their own bodies, its `summarize_simulation` is
model-written and now passes the same `validate_simulation_summary` gate described above, and
extraction under `openrouter` is identical to extraction under `deterministic` — the two providers
this decision actually compares —
because `OpenRouterProvider.extract_artifact_semantics` delegates straight to
`DeterministicProvider`. This is narrower than "every provider": `watsonx` and `cached` do change
extraction (the README's own comparison table records 17 role disagreements against the rule-based
result over 313 artifacts), which is exactly why `watsonx.py` treats extraction as high-stakes and
narratives as safe to leave deterministic. Under `openrouter`, as under `deterministic`, the seeded
baseline (Payment Gateway 74 / HIGH, Incident Recovery 72 / HIGH, the simulation 74 → 93, Identity
Systems 68, Maria HIGH / Jordan MEDIUM) is byte-identical.

**Recorded here, rather than assumed settled, because it reopens Person A's own reasoning about a
package Person A owns.** `openrouter` is implemented, credential-gated, and off by default; it
should not be treated as anything more than available until Person A has seen this entry.

**Documents affected:** none of the frozen specifications — the change is additive and sits behind
a default that stays off. `README.md` (AI-provider section), `fixtures/README.md` (fixture
capture policy), `backend/.env.example` (three new operator-facing variables, no values).

### Open items after this build

| ID | Item | Owner | Resolve by |
|---|---|---|---|
| OPEN-10 | DEC-15 (OpenRouter narrative provider) needs Person A's acknowledgement | Person A | Next sync |

---

## Implementation decision — frontend presentation of received values

### DEC-16 — Headline risk indices are revealed, never counted up

**Date:** 2026-08-22 · **Category:** B · **Owner:** Person B · **No contract change**

A motion layer was added across the frontend. The conventional treatment for a large headline
number is a count-up from zero, and it was rejected for the continuity risk index, the degraded
capability count, and the critical gap count.

The frontend's standing constraint is that risk, readiness, exposure, evidence confidence, and
technical overlap are received from the API and rendered, never computed here. A count-up paints
43, then 61, then 74 for a system whose index is 74. Those intermediate figures are produced by the
browser, are not values the engine ever returned, and are indistinguishable on screen from ones
that were. Under demonstration a paused frame or a screenshot shows a continuity risk index that
does not exist — against a product whose entire argument is that its numbers are traceable to
evidence.

The headline figures instead arrive with the same fade-and-rise entrance as the rest of the
interface, so the only value ever painted is the one the API returned. `RiskIndex`
(`frontend/components/status.tsx`) therefore renders its value directly and holds no animation
state; the entrance belongs to the container.

**Recorded rather than left as a styling preference** because the reasoning is not visible from the
code. A later contributor adding a count-up would see only an unanimated number and a tempting
improvement, and would be reversing a decision about the compute boundary without knowing it.

**Documents affected:** none. No endpoint, field, enum, or domain semantic is involved.

### Open items after this build

| ID | Item | Owner | Resolve by |
|---|---|---|---|
| OPEN-11 | AC-14 latency is breached under `AI_PROVIDER=openrouter`, measured live on 2026-08-21: `POST /simulations` 2.85s against the 2s deterministic-simulation budget, and `POST /recommendations/backup-candidates` 11.93s typical and 16.91s worst against the 12s AI-operation budget. Reads are unaffected at 16–23ms. The cause is roughly 6s per model call against a 3.5s nominal timeout, because httpx's read timeout bounds the gap between socket reads rather than total generation. Four responses are open: cap `max_tokens`, use a faster model, run the candidate calls concurrently, or accept and document the breach. `AI_PROVIDER=deterministic` is unaffected and remains the default | Both | Before the demo is recorded under `openrouter` |

---

## Contract amendment and latency — closing Person B's gap register

### DEC-17 — `single_expert_dependency_count` is added to `PlatformSummary`

**Date:** 2026-08-24 · **Category:** C · **Owner:** Person A implements, jointly agreed ·
**Contract change: additive, one new required field**

`docs/BACKEND_GAPS.md` GAP-01 was the only blocking item in Person B's three-way review: the
corrected dashboard puts a single-expert-dependency count on each platform card, and no field
anywhere carried it — not in `API_CONTRACT.md` §6.1, not in `PlatformSummary`, not in any fixture,
not in `frontend/types/api.ts`. It had simply never been added.

`single_expert_dependency_count: integer >= 0` now sits on `PlatformSummary`, defined as the number
of capabilities under the platform whose adequate coverage is exactly one engineer.

**Why it could not be left to the frontend.** GAP-01 anticipated the shortcut and it is worth
recording why the shortcut is wrong, because it is the kind that looks right on the seeded data.
Summing `degraded_capability_count` across the platform's systems does not give this number: under
DEC-07 a lower-criticality capability with *zero* adequate engineers is `DEGRADED` rather than a
critical gap, so the degraded count spans both the one-expert and the no-expert cases. On the seeded
dataset the two figures differ, and `test_single_expert_dependency_count_is_not_the_degraded_count`
asserts that they differ — a test that exists purely so a future contributor cannot conclude the
client-side derivation is equivalent. Deriving it client-side would also breach the standing rule
that the frontend renders received values and computes no domain quantity.

**Why no new engine work was needed.** `capability_assessments.adequate_engineer_count` is already
persisted by every recompute path and is already staleness-aware — `CoverageFact.is_adequate`
excludes `STALE` evidence per PRD rule R6. The field is therefore a read-path aggregate, counted in
SQL and joined up to the platform through `Capability.system_id`. No column, no migration, no rule.

**The `== 1` test is shared, not re-invented.** It is the same condition
`app/continuity/aggregation.py` already uses to raise `SOLE_EXPERT_CAPABILITY` and
`MULTIPLE_SOLE_EXPERT_CAPABILITIES`. Writing a second definition here would have let a platform card
disagree with the reason codes displayed on the systems beneath it, which is the sort of
inconsistency nobody notices until it is on a screen in front of judges.

**Seeded values: Payments 4, Identity 2.** The working brief said 3 and 1. Those were stale-brief
figures, as GAP-01 itself noted, and the derived numbers are what ship. Payment Gateway contributes
two of Payments' four (Incident Recovery, Certificate Management) and Refund Engine and Billing
Integration one each.

**Documents affected:** `docs/API_CONTRACT.md` §6.1 and the §8.1 example, `fixtures/platforms.json`,
`frontend/types/api.ts`, `frontend/lib/api/schemas.ts`. `PlatformCard.tsx` renders it; the copy is
descriptive ("N single-expert capabilities") and Person B should restyle freely.

### DEC-18 — The narrative latency budget is enforced by a deadline, not by a transport timeout

**Date:** 2026-08-24 · **Category:** B · **Owner:** Person A · **No contract change** ·
**Closes OPEN-11**

OPEN-11 recorded two AC-14 breaches under `AI_PROVIDER=openrouter`. They turned out to be different
kinds of problem and only one of them was real.

**The simulation was not a breach.** AC-14 reads: "Deterministic simulation returns in \<2 seconds on
seeded dataset; normal read APIs target \<800ms local p95; AI plan/explanation operations target
\<12 seconds." Under `openrouter` the simulation summary is written by a model, so the operation is
not a deterministic simulation and the 2-second clause is not the one that applies to it — it is an
AI explanation operation, and 2.85s is comfortably inside 12. The deterministic simulation, which is
what that clause governs, measures 7.3ms. OPEN-11 applied the stricter clause to a configuration it
does not cover. Recorded rather than quietly dropped, because "we fixed it" would have been a
misdescription of a requirement we had simply read wrong.

**The candidates endpoint was a real breach**, at 16.91s worst against 12. Two causes, both now
addressed:

*The configured timeout bounded nothing.* `openrouter_timeout_seconds` is applied through
`httpx.Timeout`, and httpx has no total-request setting: its `read` timeout bounds the gap *between*
socket reads. The gateway keeps the socket warm while the model generates, so the clock kept
resetting and calls nominally budgeted at 3.5s ran to about 6. `_call_budget` had already flagged
this in its own docstring as a "pathological slow trickle" that could defeat the budget; the
measurement showed it is not pathological, it is the normal case. **A timeout the transport does not
honour is not a budget.**

*Three independent calls ran in sequence.* The three candidate narratives describe three different
people and share nothing, so sequencing them multiplied one call's latency by `limit`.

The fix is `app/ai/budget.py`. `narrate_in_parallel` runs the narratives concurrently under one
shared wall-clock deadline (`narrative_deadline_seconds`, default 8s against AC-14's 12), preserves
the input order so ranked candidates are not reordered by completion order, and answers anything that
raises or misses the deadline from the deterministic template. Setting the deadline to 0 skips model
narration entirely, which is the escape hatch for demonstrating on a bad connection.

**What was rejected.** Capping `max_tokens` harder was rejected as the primary fix: truncated output
fails JSON parsing and falls back to the template *silently*, so it would have bought latency by
quietly turning the model off and would have looked like success. A faster model was rejected as a
fix rather than a preference — it would move the number without removing the unbounded wait, and the
next slow response would breach again. Accepting and documenting the breach was rejected because the
endpoint is on the demo path.

**A limit worth being honest about.** Missing the deadline does not cancel the HTTP call. A thread
already inside a blocking `post` cannot be interrupted, so it finishes and its answer is discarded.
Those threads are bounded by the phase timeouts, which is what those timeouts are still good for.
Real cancellation would need an async transport throughout, which is a larger change than the problem
justifies. The work is wasted, not leaked, and it is documented at the top of `budget.py`.

Also fixed while here: the `httpx.Client` was constructed per provider, and a provider is constructed
per request, so every request paid a TCP connect and TLS handshake *inside* its own budget — which is
why `connect` had been given a quarter of it. The pool is now shared for the life of the process.

**Documents affected:** none of the frozen specifications. `backend/.env.example` gains two
operator-facing variables with defaults.

### DEC-15 acknowledged — the OpenRouter narrative provider stands

**Date:** 2026-08-24 · **Owner:** Person A · **Closes OPEN-10**

DEC-15 overrode a decision recorded in `watsonx.py`: that a model should not write the candidate
narrative or the mitigation plan, because a rephrasing that drifts is worse than a plain one and an
invented step in a plan a manager approves is a real cost. Person A acknowledges DEC-15 and the
provider stands.

The objection those passages raised was about *unchecked* model output, and that is no longer the
shape of the thing. Every generation now passes `app/ai/validation.py` before it can be returned, and
anything rejected falls back to the same deterministic text those passages were defending. The plan
returned to a caller is `outcome.draft` — the gate's filtered version, with unresolvable citations
removed — not the model's. That is a materially different proposition from letting a model's prose
through, and the original reasoning does not argue against it.

Two things keep this acknowledgement narrow. The gate's `find_unattested_names` is a documented
heuristic rather than closed-world grounding, and DEC-15 says so plainly, including which inventions
it cannot catch; the prompts are the primary defence and the gate is the net. And extraction remains
rule-based under this provider, so no model output reaches the graph that the risk numbers are
computed from. The split DEC-15 draws — model on the prose, rules on the numbers — is the same split
`watsonx.py` was reaching for from the other direction.

`AI_PROVIDER` stays `deterministic` by default. Both model-backed providers remain opt-in and
credential-gated, which is what makes a clean clone reproduce the demo offline (AC-15).

### Fixture capture policy — closing GAP-03

GAP-03 asked for a challenge fixture. The underlying problem was worse than a missing file:
`scripts/refresh_fixtures.py` captured ten of the twelve files in `fixtures/`, so
`refresh_fixtures --check` printed "all fixtures match live engine output" without having looked at
`identity-systems.json` or `challenge-attest-jordan.json` at all. **An uncaptured fixture is worse
than a missing one, because the check that exists to catch drift reports success over it.**

Both are captured now. The challenge is captured last and the database reseeded afterwards, because
it is the only call in the golden path that changes an assessment — anything captured after it would
show the corrected graph instead of the demo baseline. Its `submitted_at` is pinned to an
illustrative instant for the same reason `approved_at` is: a live timestamp would churn the fixture
on every run.

To stop this recurring, `refresh_fixtures.py` declares `CAPTURED_FIXTURES`, `main()` verifies the
declaration against what the run actually captured, and
`test_every_shared_fixture_is_captured_by_the_refresh_script` asserts set equality with the directory.
A fixture added on either side now fails a test instead of drifting quietly.

Every value Person B captured by hand was already correct; the only difference the regeneration
produced was the pinned timestamp.

### Open items after this build

| ID | Item | Owner | Resolve by |
|---|---|---|---|
| OPEN-12 | The AC-14 figures under `openrouter` are now predicted rather than measured: the fix is verified against a stub provider that sleeps, not against the live gateway. Re-measure `POST /recommendations/backup-candidates` and `POST /mitigation-plans` with a real key before claiming the numbers | Both | Before the demo is recorded under `openrouter` |
| OPEN-13 | `docs/BACKEND_GAPS.md` GAP-02 (approved plans cannot be read back), GAP-04 (candidate `evidence_confidence` definition, R-14), and the doc-refresh items GAP-05, GAP-06, GAP-09 are all still open and all still deferrable | Both | Post-MVP |

---

## The AI layer, finished and then measured

### DEC-19 — `AI_PROVIDER=chain`, and two different failure policies inside it

**Date:** 2026-08-24 · **Category:** B · **Owner:** Person A · **No contract change**

Two model providers were configured and neither was reliable alone: watsonx has a capped token quota
that can be spent mid-run, and any hosted gateway can rate-limit or time out. `AI_PROVIDER=watsonx`
therefore meant "work until the quota runs out, then stop", and `openrouter` meant "never use the IBM
model this challenge is about". `chain` tries every configured model in preference order — watsonx
first, `openrouter` second — with per-call failover.

**A defect found on the way is worth recording, because the plan would have silently failed without
it.** `OpenRouterProvider.extract_artifact_semantics` delegated to the deterministic provider. Chaining
watsonx to OpenRouter would therefore have produced rule-based extraction under a model's name — the
exact misdescription `CacheBuildRefusedError` was written to prevent, reached from the other direction.
OpenRouter now extracts with the model, and the ~70 lines of prompt building and closed-world checking
moved into `app/ai/extraction.py` so both providers share one definition. Two definitions would have
turned the provider comparison into a measurement of two hand-written parsers rather than two models.

**The failure policies are deliberately not uniform**, and the split matters more than the chaining.
Extraction hands over between models and then **raises**, never reaching the templates: extraction
decides the graph every risk number is computed from, so a quiet fallback would mean an outage produced
a different graph while every number still looked plausible and nothing announced it. Narratives hand
over and then **use the template**, because a live request must not fail over a sentence. Never fake the
graph, never break the screen.

A provider that fails permanently is retired for the rest of the run. Measured: watsonx's spent quota
was reported 640 times, once per artifact, roughly doubling wall-clock time. Retrying a permanent failure
is not resilience. Quota and auth failures retire; timeouts, 429s and 503s do not. The last provider is
never retired, because "everything is retired" is a worse error than whatever actually went wrong.

`deterministic` remains the default, so a clean clone with no credentials still reproduces the demo
offline (AC-15).

### DEC-20 — FR-005 proposals are a different kind of object, not a weaker kind of claim

**Date:** 2026-08-24 · **Category:** B · **Owner:** Person A · **No contract change**

FR-005 asks the model to propose components and capabilities and flag low-confidence concepts for
review. It was the one deliberate non-implementation left (GAP-06) because it appears to contradict the
closed world: the model may only choose from the capability list it is given, and FR-005 asks it to name
things that are not on it.

The contradiction dissolves once a proposal stops being a weaker claim. A `TaxonomyProposal` cannot carry
evidence, cannot be attributed to an engineer, has no readiness and no strength, and lives in its own
table that nothing under `app/continuity/`, `app/evidence/`, `app/simulation/` or `app/graph/` reads — a
test asserts that rather than leaving it to review. So a hallucinated capability here costs a manager ten
seconds of reading; in the graph it would silently move a risk index.

**Low-confidence proposals are kept, not filtered.** Filtering them would satisfy the closed world and
defeat the requirement, which asks for them to be *flagged for review*. A half-recognised concept is
frequently the interesting one. What is filtered is anything already in the taxonomy by name or alias —
"using existing metadata first"; a rewording is not a discovery, and the near-miss is recorded as
ambiguity — and anything unnamed or unjustified, on the same rule every claim obeys.

### DEC-21 — FR-010 suggests criticality and is never allowed to win

**Date:** 2026-08-24 · **Category:** B · **Owner:** Person A · **No contract change**

"AI **may** suggest system criticality; a human-confirmed value is **authoritative**." Both halves are
implemented in `app/ai/criticality.py`, and the second is the one worth being strict about: a suggestion
that can overwrite a human's answer is not a suggestion. A human-confirmed value wins outright *even when
the model disagrees*, and the disagreement is surfaced as a question rather than acted on. Only an
unconfirmed system takes the model's value, and it is labelled `AI_SUGGESTED`.

The model is given the system's purpose, components and capabilities, and deliberately **no engineer, no
headcount and no activity volume**. Those inputs would turn "how important is this system" into "how busy
is this team", which is the inference this product exists to argue against. A test asserts their absence,
because adding them would look helpful.

Measured against the five human-confirmed values: the model agrees with three, and all three
disagreements are `HIGH → CRITICAL`. It is systematically more alarmist than the humans — worth knowing
before anyone describes its judgement as equivalent to theirs.

### DEC-22 — Rule-based extraction stays on the demo path, because it measurably wins

**Date:** 2026-08-24 · **Category:** A — this one changes what we claim · **Owner:** Person A ·
**No contract change, because the losing option was not adopted**

The open question since the build began: is a model better than string matching at reading these
artifacts? The full corpus was extracted by `anthropic/claude-sonnet-5` (640/640, cached and committed),
and the evaluation run under both with everything downstream identical.

| Check | Rules | Model |
|---|---|---|
| Knowledge reconstruction | **56/56** | 54/56 |
| Exposure classification | **25/25** | 24/25 |
| Critical gap detection | 2/2 | 2/2 |
| Ownership mismatch | 1/1 | 1/1 |
| Counterfactual simulation | **25/25** | **15/25** |
| Backup candidates | **2/2** | 1/2 |
| Evidence grounding | 56/56 | 62/62 |

The model extracted more — 144 claims against 126 — which reads as better recall until it is checked
against the labels. It made two readiness errors, both on the hero capability, both **too high**: Jordan
`EXPOSED` read as `PRACTICED`, Maria `ASSISTED` read as `PRACTICED`. Jordan's record on gateway recovery
is two years of review comments; Maria assisted with support.

Those two promotions give Incident Recovery two extra adequate engineers, so it flips `DEGRADED →
COVERED` and *"Alex is the only person who can recover the payment gateway"* — the product's opening
claim — becomes false. The simulation becomes 74 → 91 with one critical gap instead of 74 → 93 with two.
The 60% simulation score is that single error propagating.

**The direction disqualifies it.** A continuity tool that overestimates readiness tells a manager they
are covered when they are not, and nobody goes looking for a problem the tool says does not exist. Being
wrong in the reassuring direction is worse than being wrong at all.

**What was rejected.** Shipping the model's extraction because it makes a better sentence in the
submission — it would have cost the hero scenario, moved every frozen fixture, and made the product worse
on the only benchmark we have. Also rejected: quietly dropping the model work. It earns its place on the
narratives, the taxonomy proposals and the criticality suggestions, and the losing experiment is itself
the strongest evidence for the PRD's "AI extracts; deterministic logic scores" split — which was an
assumption when written and is now a result, with the qualification that the safe division is *narrower*
than the PRD assumed.

Thirteen claims were found only by the model, so its extra recall is real. A hybrid taking that recall but
requiring corroboration before any promotion above `ASSISTED` is the obvious next experiment, and is
logged as OPEN-14.

**Documents affected:** `README.md` — the "open question" section is replaced by the result, and the
provider table now describes which providers extract with a model.

### Open items after this build

| ID | Item | Owner | Resolve by |
|---|---|---|---|
| OPEN-14 | Hybrid extraction: take the model's recall, require corroboration before any promotion above `ASSISTED`. The measured failure is one-directional over-promotion, which is exactly the shape a corroboration rule addresses | Person A | Post-MVP |
| OPEN-15 | OpenRouter returns `HTTP 402 "would exceed your available credits given your current in-flight requests"` under concurrency — six workers failed 127 of 640 artifacts, one worker completed all 127. The provider treats it as a plain failure; it should back off and serialise instead | Person A | Post-MVP |

---

## Implementation decision — the interface's vocabulary

### DEC-23 — User-facing wording is named for what a reader needs to know, not for the field it renders

**Date:** 2026-08-27 · **Category:** B · **Owner:** Person B · **No contract change**

Every screen rendered its DTO faithfully, and the result was an interface that spoke the data
model's language rather than the manager's. Reviewed against the running application, not the
specification: a reader who had studied the PRD still could not tell what the product wanted them
to do.

**The word `exposure` names three unrelated things in this contract.** `CapabilityExposure` is the
organisation's exposure to losing a capability. `ReadinessLevel.EXPOSED` is an engineer who has
only *observed* the work — the lowest rung but one. `EvidenceRole.EXPOSURE` is one artifact showing
presence. The first is a risk state, the second is close to its opposite, and the system detail
screen showed all three at once — "1 exposed" in a capability's coverage tally sat inches from a
capability marked as an exposure risk. No reader can be expected to disambiguate that, and the
enum values are frozen. Display copy is frontend-owned, so each of the three is now named for what
it describes and the word itself is retired from the interface.

Two labels were also **wrong**, not merely opaque. `DEGRADED` was shown as "Degraded" and, in a
first pass at this change, as "Weak backup"; `DOMAIN_MODEL.md` §5.4 and the rules at its lines
950-975 define it as `practiced_or_validated_engineer_count == 1` with no backup — the sole-expert
state. "Weak backup" asserts a backup exists. `CRITICAL_GAP` is `count == 0`: nobody has
demonstrated the capability independently at all, so calling it a missing *backup* understated it.
They now read "Backup at risk" and "No proven coverage".

The full map lives in `frontend/lib/copy.ts`, which is now the single home for user-facing wording;
labels that had been inlined in components were consolidated there as they were touched. Each
string was checked against PRD §22.3 — a gap states the absence of evidence, never a person's
inability — which is why readiness reads "No evidence" rather than "None", and "Has observed"
rather than "Exposed".

**Two decisions inside this one are worth their own line.** The candidate card briefly said "Shared
capability" instead of "Technical overlap"; it was reverted, because the API's own disclaimer
renders verbatim at the foot of that same screen and calls it technical overlap. One concept with
two names on one page is the problem this change exists to remove, so the jargon stays and an
explanation is attached to it instead. And the sidebar drops from four entries to three: a
simulation is always run against a system already on screen, so the Simulations entry offered a
second, context-free way to start one. `/simulations` still resolves. This supersedes the
four-entry decision in `docs/UI_REVIEW.md`, annotated there.

**Recorded rather than treated as styling** because the labels now deliberately diverge from the
specification's own terms. A later contributor comparing the interface to the PRD will find
"Backup at risk" where the contract says `DEGRADED`, and the correct reading is that the contract
governs the wire and this file governs the words.

**Documents affected:** `docs/UI_REVIEW.md` (sidebar entry annotated as superseded). No endpoint,
field, enum value, or domain semantic changes; the frozen figures are untouched.

---

## Implementation decision — the three surfaces the first legibility pass did not restructure

### DEC-24 — Challenge becomes a pane, the plan becomes a sequence, and the hierarchy is stated

**Date:** 2026-08-29 · **Category:** B · **Owner:** Person B · **No contract change**

The first legibility pass (DEC-23) changed wording everywhere and layout on two screens. It left
three things, all of which turned out to be hiding defects rather than merely being untidy.

**Challenge was two dialogs deep, and that is why nobody had audited it.** It opened as a second
`aria-modal` drawer stacked pixel-for-pixel on the first, at a `z-[60]` that did nothing because
the parent's `z-50` already established the stacking context. Both drawers registered an Escape
handler on `window`, so a single press closed both — and since the recompute result lives only in
the mutation, backing out of the form threw away the answer it had just produced. The form is now
a second *pane* of the same drawer, toggled with the `hidden` attribute so a half-typed challenge
survives a step back to check a date, and Escape retreats one level. Two leaks that the earlier
"no raw enums remain" audit missed were found inside it once it was reachable to inspect: the
engineer dropdown rendered `eng_alex_chen` because `EvidenceResponse` carries no engineer names
and the id was used as its own label, and the role dropdown rendered `EXPOSURE` — the exact word
DEC-23 claimed to have retired. Names now come from the capability's `engineer_coverage`, which
does carry them and is usually already in cache.

**The plan rendered an ordered sequence as a two-column grid.** CI-23 makes array position
load-bearing, and the generated content depends on it: task 3 requires performing the recovery
unaided, which only means anything after the shadowing in task 2. It is now a single-column `<ol>`
with a step count. This reverses `docs/UI_REVIEW.md`'s "usable as-is" endorsement of the 2×2 grid,
annotated there — that endorsement judged a static mockup's composition, before the real generated
tasks existed to read.

**The hierarchy is now stated where it is used** rather than left to be inferred: platform cards
carry their system count and a note that platforms hold no score of their own (the large `74 / 100`
on a platform card is one of its systems' numbers, and the identical 74 appears twelve rows below
as that system's); the capability list is grouped by the component that requires each capability,
so the panel and the graph beside it stop describing differently shaped data; and the capability
detail route carries the only breadcrumb in the product that shows all four levels at once.

**That route had no inbound link and never had.** It was built, specified and reviewed, and
nothing anywhere in the frontend navigated to it. `CoverageCard` now links to it. It had also
never received the DEC-23 wording pass, for the same reason its other defects went unnoticed: a
screen nobody can reach is a screen nobody audits.

**Four defects fixed alongside, all in the surfaces above.** The acceptance-criteria editor
normalised its own value on every keystroke, so a trailing space was deleted before the next
character arrived and a newline was filtered away — no multi-word criterion could be typed, while
the helper text told the reader to press Enter. `savePlan` wrote `{ plan }` unconditionally over
`{ plan, approval }`, so revisiting an approved plan redisplayed it as a draft with a live Approve
button that then failed; with GAP-02 leaving that store as the only record, it was silent data
loss, and it now has a regression test. The plan-creating POST ran through `useQuery` with retry
enabled, which could create a second plan for one request. Rendering tasks out of an effect painted
one frame of an empty grid on every load.

**Corrections this change forced on DEC-23's own wording.** An adversarial review of the diff
found that three labels introduced by the previous pass were inaccurate rather than merely terse,
and all three are corrected here.

`CRITICAL_GAP` rendered as "No proven coverage" is true of a capability and false of a system.
`ENGINEERING_RULES.md` line 250 defines a system's exposure as the worst of its capabilities', so
Refund Engine reports `CRITICAL_GAP` while four of its five capabilities are covered — and the
dashboard was stating, without qualification, that a system with proven coverage has none. The old
label "Critical gap" survived this because a state name asserts nothing; a sentence does.
`ExposurePill` now takes a `scope`, and system rows read "Worst: no proven coverage".

`DEGRADED` rendered as "Backup at risk" asserts that a backup exists. `exposure.py` reaches that
state by two routes — one proven engineer on an important capability, or *no* proven engineer on a
medium or low one — so the assertion is false on the second. It now reads "No resilient backup",
which holds on both. The hint beside it claimed the rule was "more than one engineer has
demonstrated this"; importance is part of the rule, and the hint now says so.

`EXPOSED` and the `EXPOSURE` evidence role rendered as "Has observed" and "Was present for it".
`DOMAIN_MODEL.md` 5.3 and 5.10 define both as observing, **reviewing, discussing** or lightly
interacting, and the records behind them here are a code review and an issue comment — the
server's own summary says "reviewed or discussed". The copy kept only the narrowest member of the
list, and now matches the server's phrasing.

The graph caption was also wrong again, in the state the previous fix did not check: focusing a
capability adds an outermost ring of evidence records and a second kind of dashed line
(`SUPPORTED_BY`, evidence to engineer) alongside `DECLARED_OWNER`. Verified against
`features/graph/layout.ts` and a live focused payload.

**Two regressions the same review caught in this change.** Putting an `InfoHint` inside
`ConfidenceLabel` placed a `<button>` inside the dashboard row's `<a>` — invalid, and clicking the
hint navigated to the system instead of explaining the term; the hint is now opt-in and off inside
links. And `InfoHint`'s own Escape handler closed the tooltip while the drawer beneath closed too,
the same layering fault this decision fixes for the challenge pane; it now listens in the capture
phase and stops the event.

**Documents affected:** `docs/UI_REVIEW.md` — the mitigation-plan "usable as-is" grid endorsement
is annotated as superseded. No endpoint, field, enum value, or domain semantic changes; frozen
figures unaffected.
