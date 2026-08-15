# ContinuityAI — Contract Issues Register

**Created:** 2026-08-14
**Status:** Open — awaiting joint resolution (Person A + Person B)
**Scope:** Cross-document audit of the five Phase-0 specifications
**Rule:** These are Category C decisions. Nothing here is applied until both developers agree.

---

## Purpose

The Phase-0 documents were written separately and frozen separately. They have drifted. This
register lists every discrepancy found by reading all five documents against each other, so the
conflicts can be resolved once, deliberately, before implementation begins.

No existing document in `docs/` has been modified.

### Documents audited

| Short name | File |
|---|---|
| PRD | `ContinuityAI_PRD_v1.0.md` (also present as `.docx`) |
| CONTRACT | `API_CONTRACT.md` |
| DOMAIN | `DOMAIN_MODEL.md` |
| ARCH | `ARCHITECTURE.md` |
| WORKFLOW | `TEAM_WORKFLOW_PERSON_A_B.md` |

### Severity definitions

- **BLOCKING** — code written before this is resolved will have to be rewritten, or a frozen
  acceptance criterion cannot be met. Must be answered before Phase 1 implementation.
- **DEFERRABLE** — real inconsistency, but implementation can proceed with a documented
  assumption. Resolve when the affected area is built.

### Summary

| Severity | Count | IDs |
|---|---|---|
| BLOCKING | 14 | CI-01 … CI-14 |
| DEFERRABLE | 20 | CI-15 … CI-34 |

A one-line decision sheet is at the end of this document.

---

# Part 1 — BLOCKING

---

## CI-01 — The source-of-truth hierarchy lets the PRD override the frozen contract

**Conflict.**

WORKFLOW §5 "Source of Truth Hierarchy":

> ```
> 1. PRD.md
> 2. API_CONTRACT.md
> 3. DOMAIN_MODEL.md
> 4. ARCHITECTURE.md
> ```

ARCH §68 "Contract Change Rule":

> "`API_CONTRACT.md` and `DOMAIN_MODEL.md` are frozen after Phase 0."

CONTRACT §5 header:

> "These enum values are part of the contract and must not be changed independently by either team."

**Why it matters.** Applied literally, the hierarchy resolves every enum conflict in this
register in favour of the PRD — which would replace the 3-value `Freshness` with the PRD's
4-value scale, replace typed snake_case IDs with kebab-case, and reintroduce a platform risk
class the contract explicitly froze out. That is the opposite of what "frozen contract" means.
This issue governs CI-02 through CI-14; resolve it first.

**Recommended resolution.** Split authority by subject matter rather than by document rank:

| Subject | Authoritative document |
|---|---|
| Product scope, user journey, UX requirements, acceptance criteria | PRD |
| Wire format — endpoints, field names, enum spelling, JSON shape | CONTRACT |
| Internal semantics — entity meaning, invariants, rule intent | DOMAIN |
| Module layout, technology, testing, deployment | ARCH |
| Process, ownership, decision categories | WORKFLOW |

Where the PRD demands a product behaviour the contract cannot carry, the contract is amended —
the PRD does not silently win at the wire level. Record this in `DECISIONS.md` and update
WORKFLOW §5.

**Severity:** BLOCKING

---

## CI-02 — `PRACTICED` means two different things

**Conflict.**

DOMAIN §5.3:

> "**PRACTICED** — The engineer has performed substantial hands-on execution, typically in
> controlled or lower-risk contexts, or has repeated meaningful implementation evidence
> **without sufficient independent operational evidence**."

CONTRACT §5.3 table:

> "| `PRACTICED` | Evidence of **independent execution** in a meaningful but not fully validated context. |"

PRD §16.2:

> "| PRACTICED | At least 1 recent/current strong **independent** item + 1 supporting item | Has
> independently performed the capability at least once with current evidence. |"

**Why it matters.** DOMAIN says PRACTICED is explicitly *not* independent execution; CONTRACT
and PRD say it *is* independent execution, just not yet repeated. This is the threshold the
readiness engine keys on, and it directly changes the exposure rules — DOMAIN §19 uses
`practiced_or_validated_backup_count == 0` as the CRITICAL_GAP trigger. It also changes every
readiness tooltip and legend on the frontend. Two developers reading different documents will
build incompatible logic. Affects FR-007, AC-05, AC-06.

**Recommended resolution.** Adopt the CONTRACT/PRD reading (2 of 3 documents, and it is the one
that makes the PRACTICED→VALIDATED ladder coherent: PRACTICED = independent once, VALIDATED =
independent repeatedly across sources). Amend DOMAIN §5.3 to: *"The engineer has independently
performed the capability in a meaningful context, but without the repetition, source diversity,
or recency required for VALIDATED."* Keep DOMAIN §16.4's "insufficient evidence of repeated
independent real-world execution" sentence, which is already consistent with this.

**Severity:** BLOCKING

---

## CI-03 — The seeded hero baseline contradicts itself three ways

**Conflict.** Three different "before simulation" states for Payment Gateway / Incident Recovery:

CONTRACT §6.2, §6.3, §8.1, §8.2, §8.3 (dashboard and system fixtures) — repeated six times:

> `"continuity_risk_index": 93, "exposure": "CRITICAL_GAP", "critical_gap_count": 2`

CONTRACT §8.7 (simulation `before` state):

> ```json
> "before": { "continuity_risk_index": 58, "critical_gap_count": 0, "degraded_capability_count": 0 }
> ```
> and `"capability_impacts": [ { "capability_id": "cap_incident_recovery", … "before": "COVERED" } ]`

DOMAIN §46 "Example Domain Walkthrough":

> ```
> Incident Recovery
> Exposure: DEGRADED
> Risk: 72
> Confidence: HIGH
> ```

**Why it matters.** These cannot all be true simultaneously. If the dashboard shows Payment
Gateway at 93 with 2 critical gaps *before* anything is simulated, then the simulation's
"before: 58, 0 gaps" is wrong and the headline demo beat "risk 58 → 93" (PRD §27, 1:08–1:28) is
incoherent — the risk was already 93. I cannot author fixtures until this is settled, and
Person A cannot seed the database. Affects AC-01, AC-02, AC-06, AC-07, AC-15 and the demo.

**Recommended resolution.** Make the *pre-simulation* baseline 58 / `DEGRADED` / 0 critical gaps
and let 93 / `CRITICAL_GAP` / 2 gaps be exclusively the post-simulation state. Reasoning: the
demo's dramatic arc depends on the simulation *causing* the critical gap; a dashboard that
already reads 93 has nothing left to reveal. This means amending the CONTRACT's dashboard and
system-detail examples (six occurrences) from 93 to 58, `CRITICAL_GAP` to `DEGRADED`,
`critical_gap_count` 2 → 0, `degraded_capability_count` 1 → 1.

Counter-option worth discussing: keep the dashboard at 93 because PRD §11.1 and the demo script
at 0:18–0:30 both show "Payment Gateway risk 93 / 2 gaps" on the landing dashboard, and instead
change the simulation `before` to 93 → and the `after` to something higher. This preserves the
PRD but destroys the 58→93 transition. **I recommend the first option and amending PRD §11.1
and the demo script to show 58 on the dashboard.** This is a joint decision with demo impact —
please decide explicitly.

**Severity:** BLOCKING

---

## CI-04 — `Freshness` has two different value sets

**Conflict.**

DOMAIN §5.7 and CONTRACT §5.7 — three values:

> ```
> FRESH
> AGING
> STALE
> ```

PRD §8 and §16.3 — four values:

> "| CURRENT | Evidence ≤6 months old, OR ≤12 months with low component change (\<20%). |
> | RECENT | 6-18 months old with moderate component change (\<40%). |
> | AGING | 18-36 months old OR substantial component change (40-70%). |
> | STALE | \>36 months old OR component change \>70% … |"

The PRD is also internally inconsistent: Appendix B.1 uses `"freshness": "current"` (lowercase)
while B.2 uses `"freshness": "CURRENT"` (uppercase).

**Why it matters.** `freshness` is a field on `EngineerCoverage`, `EvidenceRecord`, and the
`DEMONSTRATES` graph edge — it appears in almost every payload I render. A 3-value enum needs
three badge states; a 4-value enum needs four. Affects FR-008 and the provenance drawer (UX 11.4).

**Recommended resolution.** Keep the frozen 3-value `FRESH / AGING / STALE` for the wire format
(CONTRACT and DOMAIN already agree, 2 of 3). Amend PRD §8 and §16.3 to the 3-value scale, folding
CURRENT and RECENT into `FRESH`, and carry over the PRD's threshold table as the implementation
default: `FRESH` ≤ 18 months or ≤ 12 months with low component change, `AGING` 18–36 months,
`STALE` > 36 months or major architecture migration. Fix the lowercase `"current"` in Appendix B.1.

**Severity:** BLOCKING

---

## CI-05 — Graph edge types have three different names, and the ownership edge is missing from the API

**Conflict.**

DOMAIN §37:

> ```
> CONTAINS_SYSTEM
> HAS_COMPONENT
> REQUIRES_CAPABILITY
> DEMONSTRATES
> SUPPORTED_BY
> DECLARED_OWNER
> ```

CONTRACT §5.12 `GraphEdgeType`:

> ```
> HAS_SYSTEM
> HAS_COMPONENT
> REQUIRES_CAPABILITY
> DEMONSTRATES
> SUPPORTED_BY
> ```

PRD §13.2:

> "| CONTAINS | Portfolio → System | | DECLARES_OWNER | System/Component → Engineer |
> | ADJACENT_TO | Capability ↔ Capability | similarity reason / shared skills (optional MVP) |"

Three names for platform→system (`CONTAINS_SYSTEM` / `HAS_SYSTEM` / `CONTAINS`), three states
for the ownership edge (`DECLARED_OWNER` / absent / `DECLARES_OWNER`), and `ADJACENT_TO` exists
only in the PRD. Direction also differs: DOMAIN §37 draws `Engineer --DECLARED_OWNER--> System`;
PRD §13.2 draws `System/Component → Engineer`.

**Why it matters.** The graph DTO is a frozen wire contract; a mismatched edge-type string means
the visualization silently drops edges. `GraphEdgeType` is the enum I switch on to pick edge
styling. More seriously, the CONTRACT enum has **no ownership edge at all**, so the declared-vs-
demonstrated story cannot be drawn on the graph — see CI-07. Affects AC-03, FR-021.

**Recommended resolution.** Freeze the CONTRACT's five names as the wire values and add a sixth:

```
HAS_SYSTEM
HAS_COMPONENT
REQUIRES_CAPABILITY
DEMONSTRATES
SUPPORTED_BY
DECLARED_OWNER
```

Direction: `Engineer --DECLARED_OWNER--> System` (DOMAIN's direction, which matches how
`DEMONSTRATES` already flows engineer→target and keeps all engineer-origin edges consistent).
Amend DOMAIN §37 `CONTAINS_SYSTEM` → `HAS_SYSTEM`, and PRD §13.2 to the same six. Drop
`ADJACENT_TO` from the MVP — the PRD already marks it "(optional MVP)" and the backup-candidate
engine computes adjacency internally without needing to transport it.

**Severity:** BLOCKING

---

## CI-06 — `EvidenceRole` has two incompatible vocabularies

**Conflict.**

DOMAIN §5.10 and CONTRACT §5.10 — five UPPER_SNAKE values:

> ```
> EXPOSURE
> CONTRIBUTION
> ASSISTED_EXECUTION
> INDEPENDENT_EXECUTION
> KNOWLEDGE_CAPTURE
> ```

PRD §15.3, the required AI extraction output schema — seven lowercase values:

> `evidence_role: "observed" | "reviewed" | "assisted" | "implemented" | "independent_resolution" | "authored" | "designed",`

PRD Appendix B.1 uses `"evidence_role": "independent_resolution"`.

**Why it matters.** PRD §15.3 is the contract Person A's AI extraction layer implements against,
and §5.10 is the contract the persisted evidence and my provenance cards use. Two vocabularies
means either a lossy mapping table nobody has written, or seven role badges in a UI designed for
five. Affects FR-004, FR-006, AC-04.

**Recommended resolution.** Frozen five UPPER_SNAKE values win at every layer, including the AI
extraction schema — a smaller closed vocabulary is easier to validate and to explain in the
provenance drawer. Amend PRD §15.3 and Appendix B.1. Record the intended mapping in
`DECISIONS.md` so the PRD's finer distinctions are not lost:

| PRD value | Frozen value |
|---|---|
| `observed`, `reviewed` | `EXPOSURE` |
| `implemented`, `designed` | `CONTRIBUTION` |
| `assisted` | `ASSISTED_EXECUTION` |
| `independent_resolution` | `INDEPENDENT_EXECUTION` |
| `authored` | `KNOWLEDGE_CAPTURE` |

Note `designed` → `CONTRIBUTION` is a judgement call worth confirming with Person A; architecture
design could reasonably map to `KNOWLEDGE_CAPTURE`.

**Severity:** BLOCKING

---

## CI-07 — Declared ownership cannot be shown on System Detail

**Conflict.**

PRD §11.2 "System Detail" requires:

> "Show declared owner(s) and highlighted mismatch if demonstrated operational expertise differs."

PRD FR-021:

> "System shall flag when declared ownership materially differs from demonstrated operational coverage."

PRD §27, demo beat 0:08–0:18:

> "Declared owner Jordan vs demonstrated recovery evidence Alex … 'Jordan officially owns the
> service. But the team's work history tells a different story.'"

But `declared_owner` appears in exactly one place in the frozen contract — inside the
`declared_vs_demonstrated` block of `GET /capabilities/{capability_id}/evidence` (CONTRACT §8.6).
The `SystemDetail` DTO (CONTRACT §6.3) has no ownership field, and `GraphEdgeType` has no
ownership edge (CI-05).

**Why it matters.** The mismatch is the emotional hook of the demo and it is supposed to be
visible on the System Detail page and the graph — one level *above* where the contract can
deliver it. Today I can only surface it after the user drills into a specific capability's
evidence view. I cannot derive it client-side: picking "strongest demonstrated coverage" is
domain intelligence and is prohibited. Affects FR-021, AC-02, and the 0:08–0:18 demo beat.

**Recommended resolution.** Add to `SystemDetail` (only — not `SystemSummary`, which is used in
list views):

```json
"declared_ownership": {
  "engineer_id": "eng_jordan",
  "name": "Jordan Lee",
  "source": "CODEOWNERS",
  "mismatch_detected": true
}
```

Nullable when no declared owner exists. `mismatch_detected` is backend-computed. Combined with
the `DECLARED_OWNER` edge from CI-05, this makes the story renderable on both System Detail and
the graph. DOMAIN §35 already specifies the internal `DeclaredOwnership { system_id, engineer_id,
source_reference }` model, so this is a transport gap, not a modelling gap.

**Severity:** BLOCKING

---

## CI-08 — "Why this risk?" has no field to carry the fired rules

**Conflict.**

PRD AC-07:

> "Before/after risk is deterministically reproducible from rules and 'Why?' shows rule triggers."

PRD FR-013:

> "System shall map rule outcome to a transparent 0-100 Continuity Risk Index and **display
> contributing rule factors**."

PRD FR-024:

> "All user-visible risk/readiness/recommendation claims shall be traceable to rule output and source evidence."

DOMAIN §20:

> "The UI must provide a `Why this risk?` explanation based on fired rules."

CONTRACT §12.1 makes it optional and future:

> "This field **may be included later** in `CapabilityDetail` if required by the UI, but adding it
> should be a documented contract change."

**Why it matters.** AC-07 and FR-013 are not optional, and ARCH §75 makes "User can understand
why Incident Recovery is risky" the Phase 4 exit condition. The data exists in the backend —
CONTRACT §12.1 and ARCH §29 both show reason codes like `CRITICAL_CAPABILITY`,
`SINGLE_VALIDATED_ENGINEER`, `NO_PRACTICED_OR_VALIDATED_BACKUP` — it simply has no field to travel
in. I cannot reconstruct fired rules client-side without reimplementing the risk engine, which is
explicitly prohibited. This is the documented contract change CONTRACT §12.1 anticipates.

**Recommended resolution.** Add to `CapabilityDetail` (CONTRACT §6.5) and to the `assessment`
block of the capability-evidence response:

```json
"rules_triggered": ["CRITICAL_CAPABILITY", "SINGLE_VALIDATED_ENGINEER", "NO_PRACTICED_OR_VALIDATED_BACKUP"]
```

Machine-readable reason codes, not prose — I own the human-readable copy, which keeps the
responsible-AI wording under joint review rather than backend-generated. Ask Person A for the
closed list of reason codes so I can write a display-string map. Also add the same array to
`SystemDetail` if the "Why?" link on the system page (PRD §11.2) is in scope for MVP; if not,
scope "Why?" to capability level only and note it in `DECISIONS.md`.

**Severity:** BLOCKING

---

## CI-09 — Risk *class* is required by the UI but is not in any DTO

**Conflict.**

PRD §11.1 dashboard requirements:

> "| Portfolio rows | Portfolio name, aggregated **risk class**/index, critical systems, critical gaps, drift indicator. |"
> "| Sort/filter | Default sort by risk descending; filter by portfolio and **risk class**. |"

PRD §11.2:

> "Show Continuity Risk Index, **risk class**, Evidence Confidence, and 'Why?' link."

PRD AC-02 requires System Detail to show "risk index/**class**". PRD §17.1 makes the class
authoritative:

> "The risk class is determined by explicit resilience rules. A numeric index is derived for
> comparison/UI but never interpreted as failure probability."

PRD §17.2 defines the bands `LOW 0-39 / MODERATE 40-59 / HIGH 60-79 / CRITICAL 80-100`. No DTO in
CONTRACT §6 carries a risk class field, and no enum in CONTRACT §5 defines one.

**Why it matters.** PRD §17.1 says the class is the source of truth and the number is derived —
yet only the derived number crosses the API. Bucketing 93 into "CRITICAL" in React is arithmetic
on a domain value, and PRD §17.2's clamping rule ("Clamp to the band corresponding to the
authoritative risk class so modifiers cannot silently change the classification") means the band
edges are not always a pure function of the index. Affects AC-02, FR-002, FR-012, and the
dashboard filter.

**Recommended resolution.** Add enum `ContinuityRiskClass { LOW, MODERATE, HIGH, CRITICAL }` to
CONTRACT §5, and a `continuity_risk_class` field alongside `continuity_risk_index` on
`SystemSummary`, `SystemDetail`, and `CapabilityDetail`. Nullable under the same conditions as
the index. This is the smallest change that satisfies FR-012 and keeps classification in the rule
engine where PRD §17.1 puts it.

**Severity:** BLOCKING

---

## CI-10 — Platform-level risk is simultaneously forbidden and required

**Conflict.**

CONTRACT §2.1, a frozen Phase-0 decision:

> "ContinuityAI does **not** calculate a synthetic platform-level risk score."

DOMAIN §21.3 agrees:

> "MVP does not calculate an independent Platform Risk Index."

PRD §11.1 dashboard table shows a platform-level risk value:

> "| Payments Platform | \- | **HIGH** | 3 | +1 new risk |"
> "| Identity Platform | \- | **MODERATE** | 1 | Stable |"

PRD §17.3:

> "Portfolio risk is driven by highest-risk critical system plus number of critical systems/gaps."

**Why it matters.** The PRD's dashboard mockup — the first screen of the product and the 0:18
demo beat — shows a platform risk class the contract forbids the backend from producing. I cannot
compute it client-side. Either the dashboard drops that column or the freeze is amended.

**Recommended resolution.** Hold the freeze and change the presentation: the platform row shows
`highest_system_risk_index` (already in `PlatformSummary`) labelled explicitly as *"Highest system
risk: 93"* rather than an aggregate platform score, plus `critical_gap_count` and `drift_status`.
This satisfies the manager's "where do I look first?" job without inventing a second aggregation
formula, which is the stated reason for the freeze. Amend PRD §11.1's table and §17.3's portfolio
sentence to match.

If instead the team wants a genuine platform class, that is a contract amendment adding
`continuity_risk_class` to `PlatformSummary` and a defined aggregation rule owned by Person A —
larger, and it reopens a decision that was deliberately closed. I do not recommend it.

**Severity:** BLOCKING

---

## CI-11 — Identifier format: typed snake_case vs kebab-case

**Conflict.**

DOMAIN §4 and CONTRACT §4.2:

> ```
> platform_payments
> system_payment_gateway
> component_gateway_integration
> cap_incident_recovery
> eng_alex
> evidence_inc_184
> ```

PRD §13.1, §24.1, Appendix B — kebab-case, untyped:

> `"engineer_id": "alex-chen"`, `"system_id": "payment-gateway"`,
> `"capability_id": "incident-recovery"`, `"evidence_id": "ev-inc-184-alex-recovery"`

**Why it matters.** Every fixture file, every URL path parameter, every test assertion, and every
seeded database row uses one of these. Person A and I picking differently means the golden path
404s on first integration — precisely the failure WORKFLOW §54 warns about.

**Recommended resolution.** Typed snake_case (`cap_incident_recovery`), per CONTRACT §4.2 and
DOMAIN §4 — 2 of 3 documents, it is the wire format, and the type prefix makes IDs debuggable in
logs and graph payloads. Amend the PRD's examples (§13.1 table, §24.1, Appendix B.1–B.3). Note
the PRD's engineer IDs also carry surnames (`alex-chen`); the contract uses `eng_alex`. Confirm
`eng_alex` is acceptable given a real dataset would need `eng_alex_chen` for uniqueness — I
recommend `eng_alex_chen` style now to avoid a rename later, but `eng_alex` is already written
into eight CONTRACT examples, so this is Person A's call on seed-data cost.

**Severity:** BLOCKING

---

## CI-12 — Plan editing is required by an acceptance criterion but has no endpoint

**Conflict.**

PRD AC-10:

> "Generated plan contains 3-5 actions, acceptance criteria, linked evidence/material, and **can be
> edited**/approved."

PRD FR-019:

> "Manager shall be able to **edit** and approve/reject generated mitigation plan."

PRD §11.7:

> "Manager can edit the plan before approval."

PRD §24 lists `PATCH /api/plans/{id}` — "Edit plan". The frozen 10 endpoints (CONTRACT §7)
contain no edit route; `POST /mitigation-plans/{plan_id}/approve` accepts only
`{"approved_by": "..."}`.

**Why it matters.** AC-10 is a Definition-of-Done item (PRD §26.1: "All AC-01 through AC-16 pass
or any exception is explicitly documented"). Without an edit route the plan screen is read-only,
and the human-in-the-loop story weakens from "review, adjust, approve" to "approve".

**Recommended resolution.** Defer the endpoint, narrow the criterion, document the exception.
Reasoning: the demo beat (PRD §27, 2:15–2:30) is *approval*, not editing; an 11th endpoint plus
plan-mutation semantics is real backend cost for a beat nobody watches. Amend AC-10 to
"…linked material, and can be reviewed and approved", and log the deferral in `DECISIONS.md`
against FR-019 as post-MVP.

If editing is judged essential to the responsible-AI story, the minimum change is
`PATCH /api/v1/mitigation-plans/{plan_id}` accepting a full `tasks` array while `status` is
`DRAFT`. Person A's call on cost — but this must be decided now, because it determines whether
I build editable task cards or static ones.

**Severity:** BLOCKING

---

## CI-13 — The challenge/correct workflow has no endpoint

**Conflict.**

PRD AC-11:

> "Manager can link missed evidence or correct mapping and see readiness/risk recomputed."

PRD FR-020:

> "Manager shall be able to link evidence, add manager attestation, or correct capability mapping
> and trigger recomputation."

PRD §5.1 lists it as an MVP goal; §21 specifies the full workflow; §11.4 puts "Challenge
Assessment" in the provenance drawer as an action; scenario S5 is built on it; DOMAIN §33 models
`AssessmentChallenge`; ARCH §54 specifies `ChallengeService`. PRD §24 lists
`POST /api/assessments/{id}/challenge`.

The frozen 10 endpoints contain nothing for this. CONTRACT §20 "Non-Goals" does not list it as
excluded either — it is simply absent.

**Why it matters.** This is the largest scope question in the register: an entire MVP goal, a
functional requirement, an acceptance criterion, a user scenario, a domain entity, and a service
exist for a feature with no API surface. It also affects my provenance drawer design — PRD §11.4
lists "Challenge Assessment" as the drawer's action row.

**Recommended resolution.** Defer to post-MVP and document the exception explicitly. Reasoning:
the challenge loop requires re-running extraction, aggregation, readiness, and risk on demand —
by far the most expensive unbuilt feature here — and it appears nowhere in the three-minute demo
script. WORKFLOW §34's scope-control test ("Does this materially improve the golden path or
judging story?") answers no. Amend PRD to move FR-020, AC-11, and §21 to the post-MVP roadmap
(§31), and drop the "Challenge Assessment" action from the §11.4 drawer spec so I do not build a
dead button.

Retain DOMAIN §33's `AssessmentChallenge` model as a documented future design — it costs nothing
and shows judges the correction path was designed, not overlooked.

**Severity:** BLOCKING

---

## CI-14 — Fixture location conflicts with the shared-contract model

**Conflict.**

CONTRACT §14:

> "Create these fixtures under a path such as: `frontend/mocks/`"

ARCH §11 shows the same `frontend/mocks/` tree. WORKFLOW §41 "Mock Data Ownership":

> "Person B may create initial mock payloads based on `API_CONTRACT.md`. … Mock data must not
> become a second unofficial API specification."

The Phase 4 bootstrap brief for this session specifies a **root-level `fixtures/`** directory
that "frontend and backend both read".

**Why it matters.** Location determines ownership. Fixtures inside `frontend/` are mine by
WORKFLOW §39's file-ownership rule, which makes them frontend mocks that Person A has no reason
to read — exactly the "second unofficial API specification" WORKFLOW §41 warns against. A shared
root directory makes them jointly owned contract fixtures that Person A's API tests can validate
against, which is materially better for integration.

**Recommended resolution.** Adopt root `fixtures/`, and amend CONTRACT §14 and ARCH §11 to point
there. State in `fixtures/README.md` that these are jointly owned and that CONTRACT remains
authoritative when a fixture and the contract disagree (preserving WORKFLOW §41's rule).
**Person A must be told before their Phase 1 work starts** — their API tests should read from
`fixtures/`, not from a frontend path.

**Severity:** BLOCKING — this is a Category B change (mock infrastructure) that Person A depends on.

---

# Part 2 — DEFERRABLE

---

## CI-15 — `MitigationTaskType` has 5 values in one document and 6 in another

**Conflict.** DOMAIN §5.14 lists six: `KNOWLEDGE_REVIEW, SHADOWING, PRACTICE, RECOVERY_DRILL,
DOCUMENTATION, ARCHITECTURE_REVIEW`. CONTRACT §5.17 lists five — no `ARCHITECTURE_REVIEW`.

**Why it matters.** A backend emitting `ARCHITECTURE_REVIEW` breaks my task-type icon map and
fails frontend enum validation. Affects FR-018, AC-10. Low urgency — mitigation is Phase 7.

**Recommended resolution.** Include `ARCHITECTURE_REVIEW` (6 values). PRD §20.3's demo plan opens
with "Review Payment Gateway recovery architecture", which is an architecture review, and DOMAIN
§46's generated plan step 1 is "Review recovery architecture". Amend CONTRACT §5.17.

**Severity:** DEFERRABLE

---

## CI-16 — The drift enum has two type names

**Conflict.** DOMAIN §5.8 names the type `DriftStatus`; CONTRACT §5.8 names it
`KnowledgeDriftStatus`. Values are identical (`NEW_RISK, RISK_INCREASED, STABLE, RISK_REDUCED`)
and the field is `drift_status` in both.

**Why it matters.** No wire impact — cosmetic drift between the Pydantic class name and the
TypeScript type name. Worth fixing so generated types match across languages.

**Recommended resolution.** Use `KnowledgeDriftStatus` (CONTRACT wins on type naming; it also
matches the product term "Knowledge Drift" in PRD §8). Amend DOMAIN §5.8.

**Severity:** DEFERRABLE

---

## CI-17 — `REJECTED` plan status does not exist

**Conflict.** DOMAIN §5.13 and CONTRACT §5.16 both freeze `MitigationPlanStatus { DRAFT, APPROVED }`.
PRD §20.2: "| Status | Draft → Approved / **Rejected** (MVP only). |" and FR-019: "approve/**reject**".

**Why it matters.** No reject enum value and no reject endpoint. Affects FR-019; related to CI-12.

**Recommended resolution.** Keep two values and amend the PRD. A rejected plan in the MVP is
simply a plan the manager never approves — there is no state to persist and nothing in the demo
exercises it. Note the deferral in `DECISIONS.md` alongside CI-12.

**Severity:** DEFERRABLE

---

## CI-18 — `CONFLICTING_EVIDENCE` is a required state with no representation

**Conflict.** PRD FR-025: "System shall support Insufficient Evidence and **Conflicting Evidence**
states instead of forcing a classification." PRD §16.5 defines `CONFLICTING EVIDENCE - different
sources materially disagree; human review recommended`. PRD §11.4 requires a
"Counter/conflicting evidence" section in the Why drawer. PRD §17.1 rule R5 keys on it.

`CapabilityExposure` has `INSUFFICIENT_EVIDENCE` but no conflicting state, and the
capability-evidence response (CONTRACT §8.6) has `evidence` and `missing_evidence` arrays but no
conflicting array.

**Why it matters.** The Why drawer is specified with a section I cannot populate. Affects FR-025,
AC-12 (which only tests insufficient evidence, so AC-12 itself is safe).

**Recommended resolution.** Do not add an enum value — a fifth exposure state complicates every
badge and every rule for one demo-absent case. Instead add an optional
`conflicting_evidence: EvidenceRecord[]` array to the capability-evidence response, defaulting to
empty, and treat materially-conflicting evidence as a driver of `LOW` evidence confidence (which
DOMAIN §17 and PRD §16.4 already specify: "Sparse, stale, single-source, or materially conflicting
evidence"). Drop the conflicting-evidence section from PRD §11.4 if the array stays empty in the
seed data.

**Severity:** DEFERRABLE

---

## CI-19 — `criticality_source` is required by the UI but absent from the DTOs

**Conflict.** PRD §11.2: "Show business criticality and **whether it was human-confirmed or
AI-suggested**." PRD §13.1 System node properties: `id, name, business_criticality,
criticality_source`. PRD FR-010: "AI may suggest system criticality; a human-confirmed value is
authoritative." DOMAIN §5.1 repeats the rule.

`SystemSummary` and `SystemDetail` carry `business_criticality` but no source field.

**Why it matters.** A small but genuine responsible-AI signal — showing that a human confirmed
the criticality is part of the human-in-the-loop story. Affects FR-010, AC-02.

**Recommended resolution.** Add `criticality_source: "HUMAN_CONFIRMED" | "AI_SUGGESTED"` to
`SystemDetail` only. Seed everything as `HUMAN_CONFIRMED` except one system left `AI_SUGGESTED` to
demonstrate the distinction.

**Severity:** DEFERRABLE

---

## CI-20 — Dashboard top-summary counts have no source

**Conflict.** PRD §11.1: "| Top summary | Critical coverage gaps, **new risks, resolved risks,
stale capabilities**. No single 'employee health' score. |"

`PlatformSummary` (CONTRACT §6.1) provides `critical_gap_count` and a single `drift_status` enum —
no counts of new, resolved, or stale.

**Why it matters.** The top-of-dashboard summary strip is the first thing the manager sees (PRD
§11.1: "within 10 seconds"). Three of its four numbers have no source. Affects FR-023, AC-01.

**Recommended resolution.** Either add `new_risk_count`, `resolved_risk_count`,
`stale_capability_count` to `PlatformSummary`, or reduce the summary strip to what the contract
provides: total critical gaps + a drift indicator per platform. **I recommend reducing the strip**
— FR-023 only requires the dashboard to "show seeded/new/resolved/stale continuity changes for
demo data", which `drift_status` already conveys per row, and AC-01 only tests that the
highest-risk system and critical-gap count are visible. Amend PRD §11.1.

**Severity:** DEFERRABLE

---

## CI-21 — Simulation DTO field drift between DOMAIN and CONTRACT

**Conflict.**

DOMAIN §23 `SimulationState` has four fields:

> `continuity_risk_index, critical_gap_count, degraded_capability_count, covered_capability_count`

CONTRACT §8.7 `before`/`after` have three — no `covered_capability_count`.

DOMAIN §24 `CapabilityImpact`:

> `capability_id, capability_name, before_exposure, after_exposure, remaining_best_readiness, risk_before, risk_after`

CONTRACT §8.7 `capability_impacts[]`:

> `capability_id, name, operational_criticality, before, after, remaining_best_readiness`

Four differences: `capability_name` vs `name`; `before_exposure`/`after_exposure` vs
`before`/`after`; per-capability `risk_before`/`risk_after` present in DOMAIN, absent in CONTRACT;
`operational_criticality` present in CONTRACT, absent in DOMAIN.

**Why it matters.** Person A implements from one document, I type from the other, and the
simulation screen — the hero feature — fails on first integration. Affects AC-06, FR-015.

**Recommended resolution.** CONTRACT's shape wins (it is the wire format per CI-01). Amend DOMAIN
§23–24 to match, and add `covered_capability_count` to CONTRACT's `before`/`after` — PRD §18.3
requires reporting "Preserved" capabilities, and DOMAIN §7.1 already lists
`covered_capability_count` as a System-derived field, so its absence from the simulation state
looks like an oversight rather than a decision.

**Severity:** DEFERRABLE

---

## CI-22 — Simulation scope: three different answers

**Conflict.** DOMAIN §22.1 fixes `scope_type: SYSTEM` — a single literal, no alternatives.
CONTRACT §5.14 defines `SimulationScopeType { SYSTEM, PLATFORM }` with "For the hero MVP workflow,
`SYSTEM` is the expected scope." PRD §18.2 step 1: "Select engineer E and simulation scope
(**portfolio/system**)." PRD §18.3's required output lists "Systems affected: Payment Gateway,
Refund Engine" — plural, implying cross-system rollup the frozen single-scope response cannot
express.

**Why it matters.** Determines whether my simulation launcher offers a scope selector, and whether
the result view must aggregate across systems. Affects FR-014, AC-06.

**Recommended resolution.** Keep `SYSTEM | PLATFORM` in the enum but implement `SYSTEM` only for
MVP, and amend PRD §18.3's example to a single system. Reasoning: the enum costs nothing to keep
and leaves the door open; the multi-system rollup is real work with no demo beat. My selector
hardcodes `SYSTEM`. Amend DOMAIN §22.1 to reference `SimulationScopeType` rather than a literal.

**Severity:** DEFERRABLE

---

## CI-23 — `MitigationTask` field drift

**Conflict.** DOMAIN §30 `MitigationTask`: `task_id, plan_id, title, description, type, sequence`.
CONTRACT §8.9 task objects: `task_id, title, description, type, acceptance_criteria[]`.

`sequence` and `plan_id` exist only in DOMAIN; `acceptance_criteria` exists only in CONTRACT — yet
acceptance criteria are required by PRD §20.2 and AC-10, so the DOMAIN model is missing the more
important field.

**Why it matters.** Ordering matters — PRD §11.7 requires actions to "progress from Understand →
Observe/Assist → Practice → Recovery Exercise → Documentation Update". Without `sequence` I rely
on array order, which is fine for JSON but undefined once tasks are persisted and re-read.

**Recommended resolution.** Add `acceptance_criteria: string[]` to DOMAIN §30. Rely on array order
for the wire format (do not add `sequence` to the DTO); keep `sequence` as an internal persistence
column so ordering survives the database round-trip. Amend DOMAIN §30 to mark `sequence` and
`plan_id` as persistence-only, which ARCH §15 already permits ("Do not force database models to
equal API DTOs").

**Severity:** DEFERRABLE

---

## CI-24 — Plan tasks cannot link to source material

**Conflict.** PRD §20.2: "| Linked material | Relevant incidents, PRs, runbooks, architecture
docs. |" PRD AC-10 requires "linked evidence/material". PRD §11.7: "acceptance criteria, and
linked source material."

CONTRACT §8.9 tasks reference sources only in prose — `"Review the recovery architecture, current
runbook, and historical incidents INC-184 and INC-221."` No structured field.

**Why it matters.** Prose references are not clickable, so the plan screen cannot link back to the
evidence that justified it — a missed opportunity for the provenance story. Strictly read, AC-10
is unmet.

**Recommended resolution.** Add optional `linked_evidence_ids: string[]` to each task. Small
backend cost, and it lets the plan screen link straight into the evidence drawer I am already
building. If Person A judges even this too costly, prose references satisfy the demo and the
deviation should be logged against AC-10.

**Severity:** DEFERRABLE

---

## CI-25 — Evidence provenance shape: flat vs nested

**Conflict.** DOMAIN §12.1 uses flat fields:

> `provenance_source: string` / `provenance_record_id: string`

CONTRACT §6.7 nests them:

> `"provenance": { "source": "synthetic_incident_dataset", "record_id": "INC-184" }`

DOMAIN also lists optional `source_url`, `raw_artifact_id`, `ai_extraction_confidence` that
CONTRACT omits entirely.

**Why it matters.** Provenance cards are the backbone of AC-04 and FR-006. `source_url` in
particular is called for by FR-006 ("source URI/reference if available").

**Recommended resolution.** Keep CONTRACT's nested shape and add optional `source_url: string |
null` inside the `provenance` object. Amend DOMAIN §12.1 to the nested form. Leave
`raw_artifact_id` and `ai_extraction_confidence` internal — they are debugging aids, not user-
visible, and DOMAIN already marks them optional.

**Severity:** DEFERRABLE

---

## CI-26 — `insufficient_evidence_count` exists in the API but not the domain model

**Conflict.** CONTRACT ships `insufficient_evidence_count` on `SystemSummary` and `SystemDetail`
(six occurrences, plus both the TypeScript and Pydantic sketches). DOMAIN §7.1's System derived
fields list `critical_gap_count`, `degraded_capability_count`, `covered_capability_count` — no
insufficient-evidence count.

**Why it matters.** Minor, but Person A implementing from DOMAIN would omit a required response
field, failing frontend validation.

**Recommended resolution.** Add `insufficient_evidence_count: integer` to DOMAIN §7.1.

**Severity:** DEFERRABLE

---

## CI-27 — "Portfolio" and "Platform" are used for the same concept

**Conflict.** PRD uses Portfolio throughout: FR-001 "System shall represent **Portfolio** → System
→ Component → Capability"; §13.1 node type `Portfolio`; §13.2 `CONTAINS | Portfolio → System`;
§17.3 "Portfolio risk"; §24 `GET /api/portfolios`. CONTRACT and DOMAIN use Platform exclusively:
`PlatformSummary`, `platform_id`, `GET /api/v1/platforms`, node type `PLATFORM`.

PRD §8 treats them as one term — "**Portfolio / Platform** | Top-level grouping of systems" — but
then uses Portfolio everywhere else.

**Why it matters.** WORKFLOW §2 lists "domain terminology" as jointly owned, and mixed vocabulary
in the UI ("Portfolio Dashboard" showing `platform_id`) reads as sloppiness to judges. Affects
FR-001 and every screen label.

**Recommended resolution.** **Platform** everywhere — it is the wire format, the enum value, and
the ID prefix. Amend the PRD's prose and tables. The one exception worth keeping is the screen
title "Portfolio Dashboard" if the team prefers it as a UX label, since DOMAIN §4.1 rule 3 allows
UI labels to differ from identifiers — but state that explicitly rather than leaving it ambiguous.

**Severity:** DEFERRABLE

---

## CI-28 — Evidence ID casing typo in the contract's own example list

**Conflict.** CONTRACT §4.2's ID example block reads `Evidence_inc_184` (capital E) while §6.7 and
§8.6 both use `evidence_inc_184`. DOMAIN §4 uses `evidence_inc_184`. DOMAIN §4.1 rule 4: "IDs
should be lowercase snake case where human-readable."

**Why it matters.** Trivially small, but it is in the ID convention section — the one place a
developer looks up the format — so it will be copied.

**Recommended resolution.** Fix to `evidence_inc_184` in CONTRACT §4.2.

**Severity:** DEFERRABLE

---

## CI-29 — Handoff notes: `docs/HANDOFF.md` vs root `HANDOFF.md`

**Conflict.** WORKFLOW §29 "Agent Handoff Rule" suggests `docs/HANDOFF.md`. The Phase 4 bootstrap
brief for this session specifies a root-level `HANDOFF.md`.

**Why it matters.** Two handoff files, or one that Person A cannot find. WORKFLOW §29 is explicit
that the point is "keeping the human teammate from having to reverse-engineer what the agent
changed" — which fails if it is in the wrong place.

**Recommended resolution.** Root `HANDOFF.md` per the current instruction, and amend WORKFLOW §29
to point at it. Root placement is more discoverable and sits next to `BUILD_WITH_BOB.md`, which
WORKFLOW §39 already places at root.

**Severity:** DEFERRABLE

---

## CI-30 — The PRD exists twice

**Conflict.** `docs/` contains both `ContinuityAI_PRD_v1.0.md` (1,471 lines) and
`ContinuityAI_PRD_v1.0.docx` (76 KB). All four other documents cross-reference a file named
`PRD.md`, which does not exist. ARCH §6's repository structure lists `docs/PRD.md`.

**Why it matters.** Every cross-reference in every document is currently broken, and two copies of
the top-of-hierarchy specification is a guaranteed drift source — an edit to one silently diverges
from the other.

**Recommended resolution.** Rename `ContinuityAI_PRD_v1.0.md` → `PRD.md` (Phase 3 of the current
work). Keep the `.docx` only if a non-technical stakeholder needs it; if kept, add a line at the
top of `docs/README.md` stating the Markdown file is authoritative and the `.docx` is a
non-authoritative export. Best option: move the `.docx` out of `docs/` entirely so there is one
specification tree.

**Severity:** DEFERRABLE

---

## CI-31 — Latency targets differ between PRD and ARCHITECTURE

**Conflict.** ARCH §56: non-AI endpoints "`< 500 ms locally where practical`". PRD AC-14:
"Deterministic simulation returns in \<2 seconds on seeded dataset; normal read APIs target
\<800ms local p95; AI plan/explanation operations target \<12 seconds."

**Why it matters.** AC-14 is a testable acceptance criterion; ARCH's number is stricter and
informal. No functional impact, but it determines what Person A's tests assert.

**Recommended resolution.** AC-14's numbers are authoritative (PRD owns acceptance criteria per
CI-01). Amend ARCH §56 to reference AC-14 rather than restating a different figure.

**Severity:** DEFERRABLE

---

## CI-32 — The simulation response has no disclaimer field

**Conflict.** PRD §11.5: "Explicit disclaimer: simulation identifies coverage loss; it does not
predict an outage." PRD §18.3 lists `Disclaimer | Coverage simulation; not an outage prediction.`
as required output, and §24.2's example response includes a `"disclaimer"` key.

CONTRACT §8.7's simulation response has `summary` but no `disclaimer`. The backup-candidates
response (§8.8) *does* carry a `disclaimer` field, so the omission is inconsistent within the
contract itself.

**Why it matters.** Responsible-AI wording is jointly owned (WORKFLOW §2, §32 Category C). If I
hardcode the disclaimer as frontend copy it never passes through joint review, and it can drift
from the backend's language.

**Recommended resolution.** Either add `disclaimer: string` to the simulation response for
symmetry with §8.8, or agree the exact static string here and record it in
`ENGINEERING_RULES.md`'s prohibited-language table so it is reviewed once and reused. **I
recommend the static string** — it cannot be forgotten by a backend code path, and it keeps one
fewer field on a hot response. Proposed wording, taken verbatim from PRD §18.3: *"Coverage
simulation; not an outage prediction."*

**Severity:** DEFERRABLE

---

## CI-33 — Candidate count: "at least two" vs "up to three" vs zero

**Conflict.** CONTRACT §2.3: "The backend may return **up to 3** technical backup candidates" and
§8.8 permits a valid `200` response with `"candidates": []`. PRD §11.6: "Show **up to 3**
technical candidates." PRD §19.3: "Top **2-3** candidate comparison." PRD AC-08: "**At least
two** candidates display strengths, gaps, evidence, and non-considered staffing factors."

**Why it matters.** AC-08 requires ≥2, the API allows 0. Not a contract conflict so much as a
fixture constraint — but if the seed data yields one candidate, AC-08 fails and I have no
comparison view to build.

**Recommended resolution.** No contract change. Record the constraint explicitly: the seeded
NovaPay dataset must produce **at least two** candidates for `cap_incident_recovery` (Maria HIGH,
Jordan MEDIUM, per WORKFLOW §23 and the CONTRACT §8.8 example). I still build and test the
empty-state UI, since CONTRACT §8.8 makes zero candidates a valid response. Note in
`DECISIONS.md` as a seed-data requirement for Person A.

**Severity:** DEFERRABLE

---

## CI-34 — `EngineerCoverage` carries no evidence linkage

**Conflict.** DOMAIN §11.1 `EngineerCapabilityCoverage` includes `supporting_evidence_ids:
list[string]` and `last_demonstrated_at: datetime | null`. CONTRACT §6.4 `EngineerCoverage` has
only `engineer_id, name, readiness, freshness, evidence_confidence`.

**Why it matters.** PRD §11.3 requires the engineer-capability edge to show confidence and
freshness (satisfied), and AC-04 requires every displayed readiness claim to open its evidence.
With no evidence IDs on the coverage object, clicking Alex's `VALIDATED` badge has nothing to
open. WORKFLOW §30 raises this exact question as its example of good communication:

> "The graph DTO gives Engineer → Capability edges, but the evidence drawer needs evidence IDs for
> the selected coverage relationship. Should we query the existing evidence endpoint rather than
> expand the graph contract?"

**Why this is likely already resolved by design.** `GET /capabilities/{capability_id}/evidence`
accepts `?engineer_id=<engineer_id>` (CONTRACT §8.6), which returns exactly that engineer's
evidence for that capability. The workflow document's own example question answers itself.

**Recommended resolution.** No contract change. Confirm the intent and document it in
`ENGINEERING_RULES.md`: *the evidence drawer fetches from the filtered evidence endpoint; the
coverage DTO deliberately carries no evidence IDs.* Optionally add `last_demonstrated_at` to
`EngineerCoverage`, which PRD §11.4's "Freshness | Latest qualifying evidence and freshness state"
row would use — that one is a genuine small gap.

**Severity:** DEFERRABLE

---

# Decision sheet

Reply with a resolution per ID. `ACCEPT` = adopt the recommendation as written.

| ID | Issue | Recommendation | Severity | Decision |
|---|---|---|---|---|
| CI-01 | Source-of-truth hierarchy overrides frozen contract | Split authority by subject matter | BLOCKING | |
| CI-02 | `PRACTICED` semantics conflict | Adopt CONTRACT/PRD reading; amend DOMAIN | BLOCKING | |
| CI-03 | Hero baseline 58 vs 93 vs 72 | Baseline 58/DEGRADED; 93 is post-simulation | BLOCKING | |
| CI-04 | `Freshness` 3 vs 4 values | Keep 3; amend PRD, carry over thresholds | BLOCKING | |
| CI-05 | Graph edge names ×3; no ownership edge | Six values, `HAS_SYSTEM` + `DECLARED_OWNER` | BLOCKING | |
| CI-06 | `EvidenceRole` 5 UPPER vs 7 lowercase | Frozen five win; record mapping table | BLOCKING | |
| CI-07 | Declared owner missing from `SystemDetail` | Add `declared_ownership` block | BLOCKING | |
| CI-08 | "Why this risk?" has no transport | Add `rules_triggered: string[]` | BLOCKING | |
| CI-09 | Risk class has no DTO field | Add `ContinuityRiskClass` + field | BLOCKING | |
| CI-10 | Platform risk forbidden vs required | Hold freeze; show highest system risk | BLOCKING | |
| CI-11 | snake_case vs kebab-case IDs | Typed snake_case; amend PRD | BLOCKING | |
| CI-12 | Plan edit endpoint missing | Defer endpoint; narrow AC-10 | BLOCKING | |
| CI-13 | Challenge workflow has no endpoint | Defer FR-020/AC-11 to post-MVP | BLOCKING | |
| CI-14 | `frontend/mocks/` vs root `fixtures/` | Root `fixtures/`; amend CONTRACT §14, ARCH §11 | BLOCKING | |
| CI-15 | `MitigationTaskType` 5 vs 6 | Include `ARCHITECTURE_REVIEW` | DEFERRABLE | |
| CI-16 | `DriftStatus` vs `KnowledgeDriftStatus` | Use `KnowledgeDriftStatus` | DEFERRABLE | |
| CI-17 | `REJECTED` status missing | Keep two values; amend PRD | DEFERRABLE | |
| CI-18 | Conflicting evidence unrepresented | Optional array, not a new enum value | DEFERRABLE | |
| CI-19 | `criticality_source` missing | Add to `SystemDetail` | DEFERRABLE | |
| CI-20 | Dashboard new/resolved/stale counts | Reduce the summary strip; amend PRD §11.1 | DEFERRABLE | |
| CI-21 | Simulation DTO field drift | CONTRACT shape wins; add covered count | DEFERRABLE | |
| CI-22 | Simulation scope ×3 | Keep enum, implement `SYSTEM` only | DEFERRABLE | |
| CI-23 | `MitigationTask` field drift | Add `acceptance_criteria` to DOMAIN; `sequence` internal | DEFERRABLE | |
| CI-24 | Plan tasks cannot link source material | Add optional `linked_evidence_ids` | DEFERRABLE | |
| CI-25 | Provenance flat vs nested | Nested; add optional `source_url` | DEFERRABLE | |
| CI-26 | `insufficient_evidence_count` missing from DOMAIN | Add to DOMAIN §7.1 | DEFERRABLE | |
| CI-27 | Portfolio vs Platform | Platform everywhere | DEFERRABLE | |
| CI-28 | `Evidence_inc_184` casing typo | Fix to lowercase | DEFERRABLE | |
| CI-29 | `docs/HANDOFF.md` vs root | Root; amend WORKFLOW §29 | DEFERRABLE | |
| CI-30 | PRD exists twice | Rename to `PRD.md`; move `.docx` out | DEFERRABLE | |
| CI-31 | Latency targets differ | AC-14 authoritative; amend ARCH §56 | DEFERRABLE | |
| CI-32 | Simulation disclaimer field absent | Static frontend string, wording agreed here | DEFERRABLE | |
| CI-33 | Candidate count ≥2 vs 0 allowed | Seed-data constraint, no contract change | DEFERRABLE | |
| CI-34 | `EngineerCoverage` has no evidence IDs | No change; document the filtered-endpoint pattern | DEFERRABLE | |

---

## Notes on method

Every quotation was verified against the source file before being recorded here. Issues were
identified by reading all five documents in full and cross-checking enum definitions, DTO field
lists, endpoint tables, functional requirements, acceptance criteria, UX requirement tables, and
the demo script against each other.

Six of these (CI-03, CI-07, CI-08, CI-09, CI-10, CI-13) originate from the same root cause: the
PRD specifies product behaviour that the API contract was frozen without a way to carry. That is
worth naming explicitly in `DECISIONS.md` — the fix is not just the fourteen individual
amendments but a standing check that new UX requirements name the DTO field that will feed them.
