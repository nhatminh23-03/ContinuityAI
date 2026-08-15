# Handoff Notes

Append at the end of every session. Assume the next session starts with no memory of this one.

---

## 2026-08-14 — Phase 0 close-out and repository bootstrap

### Completed

- **Contract audit.** All five specifications read in full and cross-checked. 34 discrepancies
  recorded in `docs/CONTRACT_ISSUES.md` — 14 BLOCKING, 20 DEFERRABLE — each with quoted evidence,
  affected requirement, recommended resolution, and severity.
- **Resolutions applied.** All 34 resolved jointly and applied surgically to the specifications.
- **Documents reorganised.** `ContinuityAI_PRD_v1.0.md` renamed to `PRD.md` so filenames match
  their cross-references; the stale `.docx` moved to `docs/archive/`.
- **New reference documents.** `docs/README.md` (index and authority levels), `docs/DECISIONS.md`
  (joint decision log), `docs/ENGINEERING_RULES.md` (~170-line working reference).
- **Repository skeleton.** `docs/`, `fixtures/`, `frontend/`, `backend/`, `.gitignore`,
  `README.md`, `BUILD_WITH_BOB.md`, `HANDOFF.md`. Git initialised on `main`, one commit.

### Files changed

| File | Change |
|---|---|
| `docs/API_CONTRACT.md` | Amended — new enum, six DTO field additions, baseline values, fixtures path |
| `docs/PRD.md` | Renamed from `ContinuityAI_PRD_v1.0.md`; amended for enums, terminology, baseline |
| `docs/DOMAIN_MODEL.md` | Amended — enum alignment, exposure rules, DTO shapes |
| `docs/ARCHITECTURE.md` | Amended — rule example, data-flow figures, fixtures path, latency |
| `docs/TEAM_WORKFLOW_PERSON_A_B.md` | Amended — source-of-truth model, handoff location |
| `docs/CONTRACT_ISSUES.md` | Created; deliberately left byte-identical afterwards |
| `docs/README.md`, `docs/DECISIONS.md`, `docs/ENGINEERING_RULES.md` | Created |
| `README.md`, `fixtures/README.md`, `BUILD_WITH_BOB.md`, `HANDOFF.md` | Created |
| `.gitignore` | Local working-notes entry moved to `.git/info/exclude` |

### Decisions made

Full detail in `docs/DECISIONS.md`. The ones that change how code gets written:

- **Authority is split by subject**, not by document rank. `PRD.md` owns scope and acceptance
  criteria; `API_CONTRACT.md` owns the wire format; `DOMAIN_MODEL.md` owns internal semantics.
- **`PRACTICED`** means hands-on without significant support, but limited to controlled contexts
  or lacking the repetition, diversity, or recency required for `VALIDATED`.
- **Exposure separates no-redundancy from no-coverage.** A sole-expert capability is `DEGRADED`
  at baseline and reaches `CRITICAL_GAP` only when no adequate coverage remains. This is what
  makes the simulation able to create a new critical gap at all.
- **Seeded baseline:** Payment Gateway 74 / HIGH, 0 critical gaps, 2 degraded, 3 covered. After
  simulating Alex unavailable: 93 / CRITICAL, 2 critical gaps, 1 degraded, 2 covered.
- **New contract fields:** `continuity_risk_class`, `rules_triggered`, `declared_ownership`,
  `criticality_source`, `linked_evidence_ids`, `conflicting_evidence`, `last_demonstrated_at`,
  `source_url`, and `covered_capability_count` on simulation states.
- **Identifiers:** typed snake_case; engineers use the full-name form `eng_alex_chen`.
- **Plan edits** ride on the existing approve request via an optional `tasks` array — still 10
  endpoints.
- **Fixtures** live at repository-root `fixtures/`, jointly owned. Person A's API tests should
  read from there, not from a frontend path.

### In progress

Nothing. Phase 0 is closed and the skeleton is committed.

### Blocked

Nothing is blocked. One item is open by design:

- **OPEN-01** — the challenge/correct workflow (`FR-020`, `AC-11`, `PRD.md` §21) is a conditional
  defer. Person A will cost a minimal endpoint that records a `MANAGER_ATTESTATION` evidence
  record against one `(engineer, capability)` pair and recomputes that capability only. Decision
  at the Phase 7 checkpoint. Until then those requirements stay in the specifications and the
  "Challenge Assessment" action is **not** built in the provenance drawer.

### Needs Person A's attention

1. **Fixtures moved** to repository-root `fixtures/` — a change from what the specifications said
   when Person A last read them.
2. **Seed data must produce at least two backup candidates** for `cap_incident_recovery`
   (AC-08 requires two; the API permits zero).
3. **Reason-code vocabulary** — the frontend needs the closed list of `rules_triggered` values to
   write display strings for them.
4. **`API_CONTRACT.md` §8.7** now lists all five capabilities so the example reconciles with its
   own counts; the seeded simulation should match.

### Recommended next task

Person B: **B1 — bootstrap the Next.js + TypeScript application** in `frontend/`
(`TEAM_WORKFLOW_PERSON_A_B.md` §53). Stop when the application runs. Then B2, TypeScript types
generated from the amended `API_CONTRACT.md` — the new fields above are the ones most likely to
be missed.

Person A: **A1 — bootstrap FastAPI**, stop when the health endpoint and its test pass.

Before either: read `docs/ENGINEERING_RULES.md`. It replaces re-reading the five specifications.

---

## 2026-08-14 — Application skeletons and contract layer

### Completed

Workflow tasks **A1–A3** and **B1–B3**. Both applications run; everything the frozen contract
fully determines is generated from it.

- **`fixtures/`** — 10 payloads extracted programmatically from the `API_CONTRACT.md` JSON
  examples, so they cannot have drifted from the document.
- **Backend** — FastAPI on Python 3.11, health endpoint, all 10 frozen routes under `/api/v1`
  returning the shared fixtures, all 19 enums and every DTO group in Pydantic, the §9 error
  envelope as domain exceptions translated at the API boundary. 13 tests pass.
- **Frontend** — Next.js 16, TypeScript, Tailwind, React Flow, TanStack Query, Zod.
  `types/api.ts` mirrors the contract. One API adapter in `lib/api/`; `NEXT_PUBLIC_USE_MOCKS`
  flips the whole app between fixtures and the live backend with no component change.

### Validation

**The Phase 1 integration gate is already green.** The full golden path was run against the live
server and all 10 responses are byte-identical to the fixtures the frontend renders — reached
before either side has written a feature. Both sides check the same fixtures from opposite
directions: pytest on the backend, `npm run typecheck` compiling fixtures against the TypeScript
types on the frontend. `npm run build` is clean.

### Decisions made

- **`backend/` was scaffolded without Person A present.** Logged as DEC-04 in `docs/DECISIONS.md`
  with every library, version, and layout choice listed. It is a starting point, not a claim on
  Person A's design — replace freely.
- **All 10 routes set `response_model_exclude_unset=True`.** Without it, 4 of 10 live responses
  stopped matching their fixtures because unset optional fields serialise as `null` or `[]` where
  the contract omits them. **Person A: when real engines replace the stubs, an optional field you
  intend to send must be explicitly set, not left to a default.**
- **Fixtures are synced into `frontend/public/fixtures/`** by `scripts/sync-fixtures.mjs`, wired
  to `predev`, `prebuild`, and `pretypecheck`. That copy is generated and gitignored — edit
  `fixtures/` at the root, never the copy.
- **Alembic was not added.** `ARCHITECTURE.md` §5.2 marks it optional until the schema stabilises.

### In progress

Nothing.

### Blocked

Nothing. Open items are OPEN-01 (challenge endpoint, Person A, Phase 7) and OPEN-06
(`last_demonstrated_at` inconsistent between contract §6.4 and the §6.5 example).

### Recommended next task

**Person B — B4: the dashboard shell.** Render Payments Platform and Payment Gateway from
`api.listPlatforms()` and `api.listPlatformSystems()`. Everything needed exists: types, adapter,
fixtures, query provider. Stop when both render with loading and error states. Remember the
frontend renders `continuity_risk_class` — it never derives it from the index.

**Person A — A4: SQLite and the repository layer.** `app/core/config.py` already carries
`database_url`. Stop when a platform/system seed can be read through a repository.

Before either: read `docs/ENGINEERING_RULES.md`.

### Running it

```bash
cd backend && .venv/bin/python -m uvicorn app.main:app --reload   # :8000, docs at /docs
cd frontend && npm run dev                                         # :3000
```
