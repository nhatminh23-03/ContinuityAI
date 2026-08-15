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

---

## 2026-08-15 — Backend implemented end to end (Person A)

**Read this first if you are picking up the frontend.** The backend is no longer returning fixtures.
Every endpoint is served by a real pipeline: artifacts are ingested, interpreted into evidence,
aggregated into readiness, and run through the continuity rules. Set
`NEXT_PUBLIC_USE_MOCKS=false` and the whole golden path works against live data.

### Running it

```bash
# Backend — creates and seeds the database on first boot, no separate setup step
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload          # :8000, interactive docs at /docs

# Frontend
cd frontend && npm install
cp .env.local.example .env.local                            # NEXT_PUBLIC_USE_MOCKS=false
npm run dev                                                 # :3000
```

Useful commands, all from `backend/` with `PYTHONPATH=.`:

| Command | What it does |
|---|---|
| `python -m scripts.seed_demo` | Rebuild the database from scratch. Idempotent |
| `python -m scripts.verify_golden_path` | Walk all ten endpoints and diff each against its fixture |
| `python -m scripts.run_evaluation` | Compare inferred state against the hidden ground truth |
| `python -m scripts.refresh_fixtures --check` | Fail if any fixture is stale |
| `python -m scripts.generate_synthetic_data` | Regenerate the artifact corpus (rarely needed) |
| `python -m pytest -q` | 101 tests, ~2 seconds |

### What now works

Every step of the golden path, from real data:

```
Dashboard → Payments Platform → Payment Gateway → Incident Recovery → Why? / evidence
  → simulate Alex unavailable → compare Maria and Jordan → select → generate plan → approve
```

The seeded organisation is 2 platforms, 5 systems, 12 components, 25 capabilities, 11 engineers,
520 synthetic artifacts, 124 evidence records, 55 coverage relationships.

**The numbers are derived, not seeded.** Readiness is recomputed from evidence on every seed, and
the hidden ground-truth labels are never readable by application code — there is a test enforcing
that. The evaluation reconstructs all 56 readiness labels from artifacts alone, detects both real
critical gaps with no false positives, and reproduces the whole counterfactual. Report at
`data/generated/evaluation_report.md`.

Every frozen number survived: Incident Recovery **72 / HIGH**, Payment Gateway **74 / HIGH** with
0 gaps / 2 degraded / 3 covered, simulating Alex **74 → 93, HIGH → CRITICAL** with 2 / 1 / 2,
Payments highest 74, Identity highest 68, Maria **HIGH** overlap, Jordan **MEDIUM**.

### Things that affect you directly

**1. Nine of ten fixtures were regenerated.** They now contain exactly what the API returns.
`platforms.json` was already correct. Full table in `docs/DECISIONS.md`, but the ones that change
what you render:

- `payments-systems.json` now has **3 systems**, not 1. The dashboard needs to handle a list.
- `payment-gateway.json` now has **3 components** covering all 5 capabilities. Previously one
  component held 2 capability ids while the counts summed to 5, so the page could not reconcile.
- `payment-gateway-graph.json` is the **real graph: 14 nodes, 25 edges**, including a
  `DECLARED_OWNER` edge. This is the shape to design React Flow against. Build for ~15 nodes rather
  than 4.
- `incident-recovery-evidence.json` has **7 evidence records**, not 1. Ordered strongest-role first,
  so the independent production recovery (`evidence_inc_184`) leads and the review sits last. Design
  the drawer as a scrollable list.
- `last_demonstrated_at` is now always present on coverage entries. **This closes OPEN-06.** It is
  optional in `types/api.ts`, so nothing breaks.

I checked every fixture key against `frontend/types/api.ts`: no undeclared fields except graph node
`metadata`, which is typed `Record<string, unknown>` anyway. Run `npm run typecheck` to confirm on
your machine.

**2. The `rules_triggered` vocabulary you were blocked on.** Closed list, owned by
`app/continuity/reason_codes.py`. Render an unrecognised code as its raw value.

Capability-level codes:

| Code | Suggested copy |
|---|---|
| `CRITICAL_CAPABILITY` | Business-critical capability |
| `HIGH_CAPABILITY` | High-importance capability |
| `NO_PRACTICED_OR_VALIDATED_COVERAGE` | No engineer has demonstrated this unaided |
| `SINGLE_VALIDATED_ENGINEER` | One engineer has repeatedly demonstrated this |
| `SINGLE_PRACTICED_ENGINEER` | One engineer has demonstrated this once |
| `NO_PRACTICED_OR_VALIDATED_BACKUP` | No second engineer has demonstrated it |
| `ADEQUATE_BACKUP_PRESENT` | More than one engineer has demonstrated this |
| `INSUFFICIENT_EVIDENCE` | Not enough evidence for a responsible assessment |
| `LOW_EVIDENCE_CONFIDENCE` | Supporting evidence is thin or single-source |
| `CONFLICTING_EVIDENCE` | Sources disagree; human review recommended |
| `STALE_ADEQUATE_COVERAGE` | The only hands-on evidence has gone stale |
| `MISSING_RUNBOOK` / `INCOMPLETE_RUNBOOK` / `CURRENT_RUNBOOK` | Documentation state |

System-level codes: `CRITICAL_CAPABILITY_GAP`, `HIGH_CAPABILITY_GAP`,
`CRITICAL_CAPABILITY_DEGRADED`, `HIGH_CAPABILITY_DEGRADED`, `SOLE_EXPERT_CAPABILITY`,
`MULTIPLE_SOLE_EXPERT_CAPABILITIES`, `INSUFFICIENT_EVIDENCE_PRESENT`, `LOW_EVIDENCE_CONFIDENCE`.

Keep the copy descriptive, never evaluative — `SINGLE_VALIDATED_ENGINEER` means the evidence shows
one person has done this, not that anyone else is deficient.

**3. `?focus_capability_id=` on the graph endpoint** narrows to one capability's neighbourhood and
adds `EVIDENCE` nodes with `SUPPORTED_BY` edges. Use the unfocused call for the system overview and
the focused one for the Why drawer. Note the edge runs engineer → evidence with `capability_id` in
metadata; the frozen node enum has no `COVERAGE` type to hang it off (DEC-08).

**4. `drift_status` is seeded, not computed.** It is a static value from the org file. Please do not
build a drift history view or trend chart on it — there are no snapshots behind it (R-04).

**5. Two things now behave differently from the old stubs:**
- `message` on the candidate response is **omitted** when candidates exist, rather than sent as
  `null`. Only the empty case carries it.
- `PLATFORM` simulation scope returns `422 VALIDATION_ERROR` naming the supported scopes. Only
  `SYSTEM` is implemented (decision CI-22). Do not offer a platform-scope option in the selector.

**6. Empty and error states you can actually trigger:**

| State | How |
|---|---|
| `INSUFFICIENT_EVIDENCE` capability | `GET /api/v1/capabilities/cap_permission_audit` — null index and class |
| Simulation with no coverage lost | simulate `eng_sofia_ruiz` on `system_payment_gateway` |
| `404` envelope | any unknown id |
| `422` envelope | `PLATFORM` scope, or `limit: 9` on candidates |
| Plan already approved | approve the same plan twice |

### Needs your acknowledgement — four contract-visible decisions

I decided these rather than blocking, with reasoning in `docs/DECISIONS.md` DEC-05 to DEC-09. Please
skim them; it is about fifteen minutes and they are all Category C:

1. **Reason-code spelling** — `API_CONTRACT.md` wins over `ARCHITECTURE.md` section 29. Your display
   copy was already going to be written against the contract spelling.
2. **AI extraction output shape** — per-claim records, not the flat array in `API_CONTRACT.md`
   section 10.2. Internal only, nothing on the wire changes.
3. **Risk class scales with operational criticality** — a HIGH capability with no coverage is HIGH
   risk, not CRITICAL. Exposure values, all counts, and the entire hero scenario are unaffected;
   without it the seeded dashboard ordering is unreachable.
4. **Nine regenerated fixtures** — table above.

### Not built

- **The challenge / correct workflow** (FR-020, AC-11, PRD section 21). Still no "Challenge
  Assessment" action, as agreed. But it is now costed at 2-3 hours because the recompute path
  already exists, and the "Phase 7 checkpoint" it was deferred to arrives after the deadline.
  **This is the main scope decision waiting on us both** — see RECOMMENDATIONS.md R-09.
- **A model-backed AI provider.** The interface, validation, and a versioned prompt specification
  are all in place, and the shipped provider is rule-based. This matters for how we word the README
  and the demo — see R-01, which is the top item on the list.
- No authentication (R-03), no real GitHub ingestion (R-07), no `GET /simulations/{id}` (the
  contract has exactly ten endpoints).

### New reading

`RECOMMENDATIONS.md` at the repository root — every concern and improvement found while building,
ranked by risk to the submission, with effort estimates. R-01, R-02, R-03 and R-09 are the ones
worth ten minutes each.

### Recommended next task

**Person B — B4 and onward: the dashboard, for real.** `api.listPlatforms()` and
`api.listPlatformSystems()` now return live data with three systems under Payments. Everything you
need exists: types, adapter, fixtures, query provider, loading and error states to trigger. Build
for the shape in the regenerated fixtures, not the old ones.

**Person A — decide OPEN-01 (challenge workflow) and OPEN-07 (AI provider) at the next sync**, then
implement whichever wins. Both are small now; both are on the critical path for what we can claim.

Before either: skim `RECOMMENDATIONS.md` R-01 and R-20.
