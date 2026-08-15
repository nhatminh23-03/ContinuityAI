# Build Log

Development record for ContinuityAI. Each entry states what was built or decided, which files
changed, which specification requirement or contract clause it implements, how it was validated,
and what remains open.

---

## 2026-08-14 — Phase 0 contract audit

**What was done.** All five Phase-0 specifications were read in full and cross-checked against
each other: enum definitions, DTO field lists, endpoint tables, functional requirements,
acceptance criteria, UX requirement tables, and the demo script. 34 discrepancies were recorded,
14 classified BLOCKING and 20 DEFERRABLE.

The audit found four classes of drift: enum definitions differing between documents; endpoints
referenced in the PRD but absent from the frozen contract; UX requirements and acceptance criteria
demanding data that no DTO or graph edge could carry; and two coexisting identifier conventions.

One finding was structural rather than editorial. Under continuity rule R1 as originally written,
a capability could only lose adequate coverage on engineer removal if it already had no
practiced-or-validated backup — which is R1's own trigger condition. The simulation could
therefore never create a new critical gap, and the frozen `before.critical_gap_count: 0` state
was unreachable. The three contradictory seeded baselines across the documents were a symptom of
this, not the cause.

**Files created.** `docs/CONTRACT_ISSUES.md`.

**Implements.** Phase 0 exit condition — both developers accept the frozen contracts
(`TEAM_WORKFLOW_PERSON_A_B.md` §17).

**Validation.** Every quotation was verified against its source file before being recorded. No
existing document was modified during the audit.

**Open questions at time of writing.** Which document wins on enum conflicts; the meaning of
`PRACTICED`; the seeded baseline; whether the challenge workflow is in MVP scope.

---

## 2026-08-14 — Phase 0 resolutions applied

**What was decided.** All 34 issues were resolved jointly. Two standing rules were adopted:
authority over the specifications is split by subject matter rather than by document rank, and any
new UX requirement must name the DTO field that will carry its data before it is accepted.

Substantive contract changes: `ContinuityRiskClass` added as a shared enum with a
`continuity_risk_class` field on system and capability DTOs; `rules_triggered` added to carry
fired rule reason codes; `declared_ownership` and `criticality_source` added to `SystemDetail`;
`DECLARED_OWNER` added to the graph edge enum; plan edits carried on the existing approval request
rather than a new endpoint; fixtures relocated to a shared repository-root directory.

The exposure model now separates *no redundancy* from *no coverage*. A capability whose only
adequate coverage is a single engineer is `DEGRADED` at baseline; `CRITICAL_GAP` means no adequate
coverage would remain. This makes the counterfactual simulation capable of producing a new
critical gap, which the previous rule shape prevented.

The seeded Payment Gateway baseline settled at index 74, class HIGH. The class is authoritative
and the index derived, so where the two conflicted the index moved. 74 is also what the rules
produce: the system contains a HIGH-class capability, and system risk may not average severe gaps
away.

**Files changed.** `docs/API_CONTRACT.md`, `docs/DOMAIN_MODEL.md`, `docs/ARCHITECTURE.md`,
`docs/TEAM_WORKFLOW_PERSON_A_B.md`, and `docs/PRD.md` (renamed from `ContinuityAI_PRD_v1.0.md` so
that filenames match how documents are cross-referenced). The stale `.docx` export moved to
`docs/archive/`. `docs/CONTRACT_ISSUES.md` deliberately left byte-identical as the record of the
pre-resolution state.

**Files created.** `docs/README.md`, `docs/DECISIONS.md`, `docs/ENGINEERING_RULES.md`.

**Implements.** `API_CONTRACT.md` §17 change control; `ARCHITECTURE.md` §68 contract change rule;
`TEAM_WORKFLOW_PERSON_A_B.md` §6 and §32 (Category C decisions require both developers and a
logged rationale).

**Validation.** Automated checks over the amended documents confirm that every
`continuity_risk_index` / `continuity_risk_class` pair sits inside its band per `PRD.md` §17.2;
that the simulation example reconciles in both directions against its own before/after counts
(before 0/2/3, after 2/1/2 across five capabilities); that all seven shared enums are identical
between `API_CONTRACT.md` and `ENGINEERING_RULES.md`; and that no superseded edge name, four-value
freshness scale, short-form engineer identifier, or old drift type name remains.

**Open questions.** One item remains open: the cost of a minimal manager-attestation endpoint for
the challenge workflow, to be reviewed at the Phase 7 checkpoint. Tracked as OPEN-01 in
`docs/DECISIONS.md`.

---

## 2026-08-14 — Repository skeleton

**What was built.** Repository structure only — no framework scaffolding and no feature code.
Directories for `docs/`, `fixtures/`, `frontend/`, and `backend/`, with the two application
directories left empty for their respective owners. Root `README.md` stubbed with the sections
the submission requires. `fixtures/README.md` documents the shared-contract rule and the content
constraints for fixture payloads.

**Files created.** `README.md`, `fixtures/README.md`, `BUILD_WITH_BOB.md`, `HANDOFF.md`,
`frontend/.gitkeep`, `backend/.gitkeep`.

**Files changed.** `.gitignore` — the local working-notes entry was moved to `.git/info/exclude`,
since `.gitignore` is itself a committed file and would otherwise publish the name of a file
intended to stay local.

**Implements.** `ARCHITECTURE.md` §6 repository structure, as amended by the fixtures relocation;
`TEAM_WORKFLOW_PERSON_A_B.md` §18 Phase 1 skeletons and §39 file ownership.

**Validation.** `git status` confirms the local working-notes file is untracked and excluded;
`git remote -v` and `git log` verified before and after the initial commit.

**Open questions.** None for this unit.

---

## 2026-08-14 — Frontend and backend skeletons with the contract layer

**What was built.** Both applications now run, and every artefact that the frozen contract fully
determines has been generated from it rather than written by hand.

*Shared.* The 10 fixture payloads in `fixtures/` were extracted programmatically from the JSON
examples in `API_CONTRACT.md`, so they cannot drift from the document they came from.

*Backend.* FastAPI application on Python 3.11 with a health endpoint and all 10 frozen routes
mounted under `/api/v1`, each returning its shared fixture. Pydantic schemas cover all 19 enums
and every DTO group. The error envelope from contract §9 is implemented as domain exceptions
translated at the API boundary, so handlers raise `NotFoundError` rather than assembling response
bodies.

*Frontend.* Next.js 16 with TypeScript, Tailwind, React Flow, TanStack Query, and Zod — the stack
frozen in `ARCHITECTURE.md` §5.1. `types/api.ts` mirrors the contract. A single API adapter in
`lib/api/` is the only place the UI touches data; `NEXT_PUBLIC_USE_MOCKS` switches the whole
application between fixtures and a live backend without a component change. Feature folders were
created per `ARCHITECTURE.md` §8.

Because the fixtures are shared and live at the repository root, the frontend copies them into
`public/` through a sync script wired to `predev`, `prebuild`, and `pretypecheck`. The copy is
generated and ignored; the root directory stays the single source.

**Files created.** `backend/` — `requirements.txt`, `pytest.ini`, `.env.example`, `app/main.py`,
`app/core/{config,errors,fixtures}.py`, `app/schemas/` (10 modules), `app/api/v1/` (7 modules),
`tests/` (2 modules). `frontend/` — `types/api.ts`, `lib/api/{client,endpoints,fixtures.contract}.ts`,
`app/providers.tsx`, `scripts/sync-fixtures.mjs`, `.env.local.example`, feature folders.
`fixtures/` — 10 JSON payloads.

**Implements.** Workflow tasks A1–A3 and B1–B3 (`TEAM_WORKFLOW_PERSON_A_B.md` §53); the 10 frozen
endpoints (`API_CONTRACT.md` §7); the error envelope (§9); the shared enums (§5); the mock-first
frontend strategy (§14); the module layout in `ARCHITECTURE.md` §6, §8 and §14.

**Validation.** Both sides now check the same fixtures independently, from opposite directions.

- 13 backend tests pass. Beyond shape checks, one asserts that the simulation payload's before and
  after states reconcile against its own capability impact list — 0 critical / 2 degraded /
  3 covered before, 2 / 1 / 2 after — and another asserts the error envelope returns
  `NOT_FOUND` for an unknown identifier.
- `npm run typecheck` compiles the fixtures against the TypeScript contract types, so a fixture
  that drifts from a type fails the build.
- The full golden path was run against the live server: all 10 responses are byte-identical to
  the fixtures the frontend renders. This is the Phase 1 integration gate in `ARCHITECTURE.md`
  §100, reached before either side has written a feature.
- `npm run build` compiles clean.

The integration check initially failed on 4 of 10 endpoints. The cause was uniform: unset optional
fields were being serialised as `null` or empty arrays where the contract omits them. Responses now
exclude unset fields, which brought all 10 into agreement.

**Open questions.** `API_CONTRACT.md` §6.4 declares `last_demonstrated_at` on `EngineerCoverage`
while the §6.5 example omits it from nested coverage entries; both sides model it as optional so
they interoperate, but the document should be made self-consistent.

---

## 2026-08-15 — Backend implementation: evidence pipeline through to mitigation

**What was built.** The whole backend, replacing the fixture-returning stubs with a working pipeline.
Fourteen packages under `backend/app/`, three data directories, five scripts, and 101 tests.

```
data/org/            structure                      data/ground_truth/   hidden labels
      │                                                   │
      │                                    generate_synthetic_data.py (reads labels)
      │                                                   ▼
      │                                            data/synthetic/  520 artifacts
      ▼                                                   ▼
   ingestion ──> AI extraction ──> validation ──> Evidence ──> aggregation ──> Coverage
                                                                                   │
                        readiness rules ──> exposure rules ──> risk index ──> assessments
                                                                                   │
                    graph · simulation · candidates · mitigation ──> the 10 frozen endpoints
```

**Implements.** Workflow tasks A4 onward and phases 2 through 8 of
`TEAM_WORKFLOW_PERSON_A_B.md`; milestones M2 through M13 of `PRD.md` section 29; the module layout in
`ARCHITECTURE.md` sections 6 and 14; `FR-001` through `FR-019` and `FR-021` through `FR-025`.

### The decision that shaped the build

The frozen fixtures already contained specific numbers — Incident Recovery 72, Payment Gateway 74,
93 after the simulation, Identity 68 — chosen during the Phase 0 audit before any rule engine
existed. Two ways to proceed: write rules and let the numbers land wherever they land, or reverse
out a rule set that reproduces them.

The second is what `TEAM_WORKFLOW_PERSON_A_B.md` section 25 warns against ("do not manipulate rules
just to make the demo answer look correct"). But the first would have broken every fixture the
frontend was built against, on a day when the frontend had not started.

The route taken was neither: derive the rule set from the PRD's own definitions — bands and anchors
from section 17.2, coverage conditions from 17.1, readiness heuristics from 16.2 — then check what
those rules produce, and treat any disagreement as a finding rather than a number to be forced.

Three findings came out of it, and all three were specification defects rather than arithmetic:

1. **The index arithmetic did not close.** Reaching 72 from the HIGH anchor of 70 needs exactly +2,
   and no combination of the PRD's modifier table sums to +2. Adding `SOLE_ADEQUATE_ENGINEER` at +1 —
   the sole-expert condition being the central signal of the whole product, and conspicuously absent
   from a table that penalises weak backups — makes 72, 74, 91 and 93 all fall out of coverage
   evidence alone.
2. **Rule R1 flattens criticality.** As written, any CRITICAL-or-HIGH capability with no adequate
   coverage is CRITICAL risk. That makes Refund Engine's single gap read 80+, which puts it above
   Payment Gateway and breaks the seeded dashboard ordering the demo depends on. Scaling the class
   with operational criticality fixes it and leaves every exposure value untouched (DEC-07).
3. **Retry Logic could not stay covered.** Under a literal reading of R1b, removing Alex leaves
   Jordan as the sole adequate engineer and Retry Logic degrades — losing the contrast beat that
   makes the simulation specific rather than vague. Resolved as a *data* decision rather than a rule
   change: the seed gives Retry Logic three adequate holders, which is also more realistic. Retry
   logic is ordinary application code many people touch; incident recovery is the scarce skill. That
   asymmetry is the product's whole point.

Every frozen number is now reproduced by the rules from evidence, and none of them is asserted
anywhere.

### Notable implementation choices

**The counterfactual is not a second engine.** `CapabilityFacts` is a frozen dataclass with a
`.without(engineer_id)` method returning a new instance. The simulation calls the same `assess()` and
`aggregate_system()` the baseline does. Baseline state cannot be corrupted because nothing is
written, and before and after cannot disagree because there is only one implementation.

**Extraction is closed-world.** A provider receives the capability taxonomy it may attribute to and
is validated against it. Four rejection classes: unknown capability, cross-system attribution,
unknown engineer, and — the one that matters most — a claim against someone who is not a recorded
participant of the artifact. That last would put an unsupported claim against a named person, which
is the single output this product cannot afford.

**Ground-truth isolation is enforced, not asserted.** `ARCHITECTURE.md` section 40 states that
application runtime cannot read the hidden labels. Three mechanisms now make it true: application
configuration exposes no path to them, only `app/evaluation/` resolves one, and
`tests/test_ground_truth_isolation.py` parses every module under `app/` and fails if any of them
names the directory, imports the evaluation package, or reaches it through settings. Without that
test the product's central claim would be unfalsifiable.

**The AI provider is a real implementation of the interface, and it is rule-based.** It performs the
same closed-world capability resolution and role interpretation a model would be prompted for, using
explicit rules, so the demo cannot fail on provider latency and the evaluation is repeatable. Being
precise about this in the README is the top item in `RECOMMENDATIONS.md` (R-01) — the seam is
genuine, but the claim must match what ships.

### Validation

- **101 tests pass in under two seconds**, against a database seeded by the same script a developer
  runs. Unit tests pin every readiness boundary and every exposure rule; behaviour tests walk the
  golden path; `test_responsible_ai.py` asserts the `engineers` table columns against an allowlist
  and greps generated text for prohibited phrasing; `test_ground_truth_isolation.py` enforces the
  evaluation boundary.
- **Hidden-ground-truth evaluation passes every check**: readiness reconstruction 56/56, exposure
  25/25, critical gap detection 2/2 with no false positives, declared-ownership mismatch 1/1,
  counterfactual simulation 25/25, backup candidates 2/2, evidence grounding 55/55. Report at
  `data/generated/evaluation_report.md`, with the caveat printed inside it — the generator emits
  classifiable patterns, so this measures pipeline self-consistency and not real-world accuracy
  (R-02).
- **All ten endpoints verified against the shared fixtures** by `scripts/verify_golden_path.py`.
  Nine fixtures were regenerated from live output; every frozen number survived.

Two bugs were found by tests rather than by inspection: mitigation task ids collided across plans
because the primary key was global rather than scoped to the plan (DEC-09), and the candidate scoring
was split across two methods such that the ordering and the displayed band could be computed from
different numbers.

### Open questions

`RECOMMENDATIONS.md` carries twenty items. The four worth deciding before the README is written:
R-01 (the AI claim), R-02 (how the 100% figures are quoted), R-03 (no authentication), and R-09 (the
challenge workflow, now costed at 2-3 hours and the main outstanding scope call).
