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

OPEN-01 is closed by DEC-10. OPEN-08 is closed by DEC-14. OPEN-06 was closed by the previous build.

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
`watsonx.py`'s reasoning and its code are both untouched, and extraction under `openrouter` is
identical to extraction under `deterministic` — the two providers this decision actually compares —
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
