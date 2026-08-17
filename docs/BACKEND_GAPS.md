# Backend Gap Register — Phase 3

**Date:** 2026-08-17 · **Author:** Person B · **Status:** for review with Person A

Three-way comparison of (a) what `PRD.md` requires — FR-001…FR-025, AC-01…AC-16, UX sections 11.1–11.7,
20, 21, 27 — against (b) what `API_CONTRACT.md` and `DOMAIN_MODEL.md` specify as amended, against
(c) what the backend actually implements and returns, observed live and captured in
`docs/api-samples/` (21 payloads, 2026-08-17, freshly seeded database).

Ruling context, agreed at the Phase 1 checkpoint: **DEC-01 values are canonical** (Payment Gateway
74/HIGH, simulation 74 → 93 HIGH → CRITICAL, Identity highest 68, five Payment Gateway
capabilities, Maria Gomez), and **DEC-10 is acknowledged** — the challenge endpoint stays and the
frontend will build a challenge action after the golden-path screens.

Headline: the backend is in materially better shape than a gap register usually implies. Ten of
ten frozen endpoints match their fixtures byte-for-byte (one pinned timestamp aside), every
canonical demo value is reproduced live, and the enum audit found zero drift. **One gap is
BLOCKING** and it is a missing contract field, not a defect.

---

## 1. Blocking

### GAP-01 — `single_expert_dependency_count` has no transport anywhere

| | |
|---|---|
| **Expected** | The corrected dashboard places a single-expert-dependency count on each platform card (brief §C.1; stale brief values "3" for Payments, "1" for Identity). |
| **Exists** | Nothing. The field is absent from `API_CONTRACT.md` §6.1, from `PlatformSummary` in code, from every fixture, and from `frontend/types/api.ts`. It was never added to the contract. |
| **Affected requirement** | Dashboard corrections §C.1; FR-002-adjacent dashboard content; SR-02 (a UX requirement must name the field that carries its data). |
| **Blocks** | The platform cards as corrected. Nothing else — the demo script's own dashboard beat (§27, 0:18–0:30) uses "0 critical gaps, 2 capabilities without resilient backup", which is the *system-level* `degraded_capability_count` and exists. |
| **Owner** | Joint Category C contract amendment; Person A implements. |
| **Recommended resolution** | Add `single_expert_dependency_count: integer >= 0` to `PlatformSummary` (and optionally `SystemSummary`), defined as the count of capabilities whose adequate coverage is exactly one engineer. The backend already computes per-capability adequate-engineer counts, so this is aggregation, not new analysis. **The frontend must not approximate it by summing `degraded_capability_count`**: under DEC-07 a MEDIUM/LOW-criticality capability is DEGRADED with *zero* adequate engineers, so degraded ≠ sole-expert, and deriving it client-side would also breach the no-domain-computation rule. |
| **Severity** | **BLOCKING** for §C.1 as written. Fallback if declined: platform cards show `critical_gap_count` + drift only, and the count moves to the system level where `degraded_capability_count` is an honest proxy label ("capabilities without resilient backup"). |

---

## 2. Deferrable — contract and behavior

### GAP-02 — Approved plans cannot be read back

**Expected:** post-approval plan state (approved chip, timestamp, approver, final task list — brief
§C.7; AC-10 "can be edited/approved"). **Exists:** `ApprovePlanResponse` carries `plan_id, status,
approved_by, approved_at` only — it does not echo the (possibly edited) task list — and the frozen
contract has no `GET /mitigation-plans/{id}`. Edits submitted with the approval are persisted
server-side but are unreadable afterwards. **Blocks:** nothing at MVP — the frontend holds the plan
and the edits it just submitted and renders the approved state from client state. A page reload
loses it. **Owner:** frontend for MVP; a `GET /mitigation-plans/{plan_id}` would be a Category C
twelfth-endpoint decision (same class as R-18). **Recommendation:** client-state MVP; log the GET
as a post-MVP contract item. DEFERRABLE.

### GAP-03 — The challenge endpoint has no fixture

**Expected:** mock mode (`NEXT_PUBLIC_USE_MOCKS=true`) covers every screen the frontend builds,
and the challenge UI is now in scope. **Exists:** `fixtures/` holds the ten frozen payloads only;
`scripts/refresh_fixtures.py` does not emit a challenge fixture. A live capture exists at
`docs/api-samples/challenge-attest-jordan.json`. **Owner:** joint — fixtures are jointly owned
(CI-14). **Recommendation:** Person A adds a challenge fixture to the refresh script (the
attest-Jordan case, which is also the demo beat); until then the frontend seeds its mock from the
captured sample. DEFERRABLE.

### GAP-04 — Candidate `evidence_confidence` uses the narrow definition (R-14)

**Expected (stale brief):** Maria HIGH. **Exists:** MEDIUM — the field reports confidence in the
candidate's coverage of the *target* capability only, not of the overlap claim (Person A's R-14,
flagged by them as a Category C judgement call). **Blocks:** nothing; the value is defensible.
**Recommendation:** render as-is with copy that says what it means ("confidence in demonstrated
coverage of this capability"); decide the wider definition jointly post-MVP. DEFERRABLE.

### GAP-05 — Specification text superseded by logged decisions

Three places where a document still carries pre-decision wording; no behavior differs:

| Where | Stale text | Superseded by |
|---|---|---|
| `PRD.md` §17.1 R1/R1b class column | any CRITICAL-or-HIGH gap → class CRITICAL | DEC-07 (class scales with criticality; implemented table is in `ENGINEERING_RULES.md`) |
| `ARCHITECTURE.md` §29 | old reason-code spellings | DEC-05 (`API_CONTRACT.md` §12.1 wins) |
| `API_CONTRACT.md` §10.2 | flat extraction array | DEC-06 (per-claim records; internal only) |

**Owner:** both, next contract touch (already tracked as OPEN-09 plus the R1 note). DEFERRABLE.

### GAP-06 — PRD features deliberately not implemented, PRD not yet annotated

| Item | State | Recommendation |
|---|---|---|
| `HIGH_OPERATIONAL_DEPENDENCY` +3 modifier (§17.2) | Not implemented — double-counts the sole-expert signal (R-08) | Amend the PRD table or annotate "not implemented" |
| Freshness component-change half (FR-008, §16.3) | Age half only; no schema signal for component change (R-05) | Note the limitation in the README; seeded `change_ratio` is the only honest post-MVP path |
| Taxonomy discovery / low-confidence concept flagging (FR-005, §15.5) | Extraction is closed-world against the seeded taxonomy by design; nothing proposes new concepts | Annotate as post-MVP; the closed world is what makes the validation gate strong |
| Operational-criticality rationale (FR-011) | `operational_criticality` crosses the wire; no rationale field | Drop from UI, or SR-02 a field if we decide we want it |

All DEFERRABLE, owner both (they are PRD amendments, not code changes).

### GAP-07 — Small DTO absences the corrected UI works around

| Corrected-UI need | Missing from DTO | Workaround (no contract change) |
|---|---|---|
| Simulation default scenario (§11.5 "AI-suggested high-impact") | No suggestions endpoint | Default the selector to `primary_engineer` from `CapabilityDetail` — a received value, not a computation |
| Candidate freshness (§11.6) | No freshness on `BackupCandidate` | Resolve `supporting_evidence_ids` against the evidence endpoint, or omit |
| Plan: backup's *current* readiness (§20.2) | Not on `MitigationPlanResponse` | Read from `CapabilityDetail.engineer_coverage` for the selected engineer |
| Plan: per-action owner suggestion (§20.2) | No owner field on tasks | Drop the column; mentor = `source_engineer` exists |
| Task duration ("Est. 2 weeks", brief §C.6) | No duration field | Remove from the design (recommended) rather than amend the contract |
| Platform "critical systems" count (§11.1) | No field | Count `business_criticality == CRITICAL` rows from endpoint 2 client-side (display counting of received values), or drop per §C.1 |

All DEFERRABLE, owner frontend.

### GAP-08 — Cosmetic contract-envelope inconsistency

Framework-level 422s (e.g. candidate `limit: 9`) return `details.errors` as a *stringified* list,
while domain-raised errors return structured `details`. Both use the correct envelope and `code`.
The frontend already switches on `error.code` only, so nothing breaks. Worth one line to Person A;
no action required. Also noted: the `INSUFFICIENT_EVIDENCE` 409 error code is defined but no read
path raises it — the state is correctly served as a 200 with null index/class, which is what the
designed UI state wants. DEFERRABLE.

### GAP-09 — PRD §11.1 example numbers drifted from live output

The PRD example table shows Refund Engine 72 and Billing Integration 51; the live engine produces
**71 / HIGH** and **52 / MODERATE** (`docs/api-samples/payments-systems.json`). DEC-07's own
rationale quotes 71, so the example predates it. Doc-example refresh, owner both. DEFERRABLE.

---

## 3. Design constraints — data paths that exist but shape the frontend

Not gaps; recorded so screens are designed against reality.

1. **System Detail capability panel** composes two calls: `SystemDetail` (components + counts) and
   the unfocused graph, whose CAPABILITY nodes carry `label`, `status` (exposure), and
   `operational_criticality` in metadata. There is no bulk capabilities-of-system list endpoint.
2. **Evidence nodes appear only under `?focus_capability_id=`** (DEC-08), and `SUPPORTED_BY` edges
   run engineer → evidence with `capability_id` in edge metadata. The Why-drawer graph focus uses
   the focused call; the system overview uses the unfocused one.
3. **Person drawer (FR-022)** has no engineer endpoint; it composes the graph's DEMONSTRATES edges
   (readiness, freshness, confidence in edge metadata) plus the per-capability evidence endpoint.
4. **Simulation dimming (§11.3)** is client visual state derived from `capability_impacts`; the
   graph endpoint has no simulation mode.
5. **`message` on the candidate response is omitted** when candidates exist; only the empty case
   carries it. `limit` is capped at 3 (422 above).
6. **`PLATFORM` simulation scope returns 422** naming supported scopes (CI-22) — the selector
   never offers it.
7. **`drift_status` is seeded, not computed** (R-04), and crosses the wire as
   `NEW_RISK / RISK_INCREASED / STABLE / RISK_REDUCED` — the "Drift: increasing / stable" copy
   needs a four-value display mapping, and nothing may build trends on it.
8. **AC-09 verified live:** a plan generates for a non-top candidate (Jordan → 5 tasks, DRAFT,
   target PRACTICED). The database was reseeded after the check.

---

## 4. Stale-brief deltas — recorded per the Phase 1 ruling, not backend gaps

The working brief's Section B predated DEC-01 and the seeded reality. Canonical values, all
observed live:

| Brief said | Canonical (DEC-01 + live) |
|---|---|
| Payment Gateway 58 / MODERATE | **74 / HIGH** (58 is unreachable: §17.2 clamps the index to the class band) |
| Simulation 58 → 93 | **74 → 93, HIGH → CRITICAL**, gaps 0 → 2 (2 / 1 / 2 after) |
| Payments Platform highest 58 · 0 critical gaps | highest **74** · **1** critical gap (Refund Engine) |
| Identity Platform 34 · 0 critical gaps | highest **68** · **1** critical gap (Authentication) |
| Four capabilities | **Five** — Monitoring stays COVERED alongside Retry Logic |
| "Maria Santos" | **Maria Gomez** (`eng_maria_gomez`) |
| Drift "increasing" / "stable" | Wire values `NEW_RISK` (Payments) / `STABLE` (Identity) |
| Payment Gateway evidence confidence HIGH | HIGH ✓ (unchanged) |
| Readiness triple, ownership mismatch, Maria HIGH / Jordan MEDIUM, plan target PRACTICED / DRAFT | All ✓ (unchanged) |

---

## 5. Acceptance-criteria data paths — AC-01 … AC-16

| AC | Data path | Status |
|---|---|---|
| AC-01 | Endpoints 1+2: 2 platforms, 5 systems, highest index + gap count on platform cards | ✓ live |
| AC-02 | Endpoint 3 + graph node statuses (constraint 1 above) | ✓ live |
| AC-03 | Endpoint 4; evidence layer via `?focus_capability_id` | ✓ live |
| AC-04 | Endpoint 6: role, strength, freshness, source, date on every record | ✓ live |
| AC-05 | Alex VALIDATED · Maria ASSISTED · Jordan EXPOSED | ✓ live |
| AC-06 | Incident Recovery → CRITICAL_GAP; Retry Logic and Monitoring preserved | ✓ live |
| AC-07 | Deterministic re-runs identical; `rules_triggered` + `index_modifiers` | ✓ live |
| AC-08 | 2 candidates, strengths/gaps/evidence ids + not-considered disclaimer | ✓ live |
| AC-09 | Any engineer accepted as backup; verified with Jordan | ✓ live |
| AC-10 | 4–5 tasks, acceptance criteria, linked evidence, edit-on-approve (CI-12) | ✓ live; read-back caveat is GAP-02 |
| AC-11 | Challenge endpoint, all three actions, recompute verified (72/HIGH → 15/LOW) | ✓ live; **frontend action now in scope** |
| AC-12 | `cap_permission_audit`: INSUFFICIENT_EVIDENCE, null index/class | ✓ live |
| AC-13 | No such field anywhere; `test_responsible_ai.py` enforces | ✓ |
| AC-14 | Reads 2.0–12.2 ms, simulation 4.6 ms | ✓ measured |
| AC-15 | Auto-seed on first boot from committed data; mock mode must stay working for offline reproduction | ✓ backend; frontend obligation open |
| AC-16 | README technical half drafted (Person A); product narrative, screenshots, video pending | Person B, post-build |

## 6. Enum and identifier audit

No drift. `app/schemas/enums.py` is identical to `ENGINEERING_RULES.md` and `API_CONTRACT.md` §5
across all 19 frozen enums. Three additive extensions, each logged: `CriticalitySource` (CI-19),
`ChallengeType` (DEC-10), `ErrorCode.UNAUTHORIZED` (DEC-13). Every observed identifier is typed
snake_case with full-name engineer ids; challenge-created evidence follows the pattern
(`evidence_attest_jordan_lee_incident_recovery`).

---

## Summary for the sync with Person A

1. **Decide GAP-01** — add `single_expert_dependency_count` to `PlatformSummary` (Category C), or
   the corrected dashboard drops the number. This is the only blocking item.
2. Acknowledge receipt of the DEC-10 acceptance: endpoint stays, challenge UI will be built; a
   challenge fixture would help (GAP-03).
3. Doc amendments at next contract touch: GAP-05, GAP-06, GAP-09.
4. Everything else is frontend-absorbable and listed so it is absorbed deliberately.
