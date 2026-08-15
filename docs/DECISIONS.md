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

OPEN-02, OPEN-03, OPEN-04, and OPEN-05 were resolved on 2026-08-14 — see DEC-01, DEC-02, the
CI-06 detailed entry, and DEC-03 respectively.

OPEN-01 stays open by design: it turns on Person A's implementation cost, which cannot be
estimated from the specifications alone. The frontend commitment is already firm — no "Challenge
Assessment" action is built, and the provenance drawer is laid out so the action can be added
later without rework.
