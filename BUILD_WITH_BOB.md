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
