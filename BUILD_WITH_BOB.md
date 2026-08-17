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

---

## 2026-08-17 — Closing the remaining backend scope

**What was built.** The five backend items that were still open, plus the technical half of the
submission README. `FR-020` and `AC-11` move from unbuilt to passing, and the PRD's hybrid data
strategy is satisfied for the first time.

**Implements.** `FR-020`, `AC-11`, `PRD.md` section 21 (challenge workflow); `PRD.md` section 14.1
(real public GitHub evidence); `ARCHITECTURE.md` section 50 (security posture) and section 54
(challenge architecture); `TEAM_WORKFLOW_PERSON_A_B.md` section 27 (Person A's README draft).

### The refactor that made the challenge workflow cheap

`CI-13` deferred the challenge workflow on the grounds that it "re-runs extraction, aggregation,
readiness, and risk on demand — the most expensive unbuilt feature in the register". That was true
when it was written and false by the time it was revisited, because the seed already did all of it.

Extracting `app/services/recompute.py` from the seed turned the feature into a thin layer over tested
machinery, and gave something more valuable than reuse: **one implementation.** A recomputed
capability and a freshly seeded baseline now cannot disagree, because there is no second code path
for them to disagree through. Three callers share it — the seed, the challenge workflow, and the
evaluator reading what they wrote.

### Designing a correction workflow that cannot become a back door

The obvious way to let a manager fix a wrong assessment is to let them set the right value. That
would have quietly destroyed the product: every number would become an opinion, the evidence graph
would be decorative, and "risk is derived from evidence" would be false.

So the request object has no field for a readiness level, an exposure state, a confidence, or a risk
index, and a test asserts their absence. A manager supplies *evidence* — an artifact extraction
missed, a statement no artifact captured, or a correction to a mis-mapping — and the rules recompute.
The abuse case still had to be closed: a manager who can attest to anything can attest their way to a
`VALIDATED` expert. Attested evidence is therefore capped at moderate strength, which means it never
counts toward the strong-source diversity `VALIDATED` requires. It can establish `ASSISTED` or
contribute to `PRACTICED` — a manager who watched someone do the work can say so — but it cannot
manufacture an expert.

The result is a satisfying demo beat. Attesting that Jordan once recovered the gateway alone moves him
`EXPOSED → PRACTICED`, Incident Recovery `DEGRADED → COVERED`, and its index 72 → 15. The *system*
index stays at 74, because Certificate Management is now the binding constraint. The engine is
reasoning about which capability drives the system rather than moving one number, which is difficult
to fake and easy to show.

### Real public GitHub data, and what it actually taught us

The PRD commits to "real public GitHub + synthetic private enterprise data". Only the second half had
been built, so 120 merged pull requests and reviews were fetched from a public repository, normalised,
committed, and ingested through the same pipeline.

Two problems surfaced immediately, both worth recording.

**The privacy problem.** This product infers capability readiness about named people. Doing that to
real engineers who never consented, from a repository they do not work on, mapped onto an invented
company, is exactly the behaviour the responsible-AI boundary exists to prevent — and the PRD had
anticipated it, asking for public evidence to be "normalized/anonymized". Contributor identities are
now mapped deterministically onto synthetic engineers and the real logins are never written to disk.
A second pass was needed after the first: pull request *bodies* routinely name other contributors
through `@mentions` and profile links, so pseudonymising the participant field alone still leaked
identities into text that later gets summarised on screen. Artifacts stay traceable through their real
URLs; the attribution is what is synthetic, and the manifest says so rather than leaving it to be
discovered.

**The more interesting problem.** Exactly one of the 120 real artifacts produced capability evidence.

That is not an extraction failure. A public SDK repository's vocabulary is library maintenance —
support, error handling, tests, packaging — while the capabilities this product assesses are
demonstrated in private operational records: incidents, runbooks, on-call history. The finding is
direct evidence for *why* the hybrid data strategy is necessary rather than merely convenient, and it
is the most concrete available measurement of the rule-based extractor's ceiling.

The temptation was to loosen the matcher until the number looked better. Resisted, and a test now
asserts the match rate stays low: a high rate here would mean the matcher had become credulous, not
that the corpus had improved. The single match is itself instructive — it surfaces as `EXPOSED / STALE
/ LOW`, which is the correct reading of a years-old third-party pull request.

### Security, without pretending

`ARCHITECTURE.md` descopes enterprise IAM, correctly. But "the manager approves the plan" rested on a
caller-supplied string, so shipping with no option at all left a responsible-AI claim resting on
nothing. A single shared bearer token was added, **off by default** so the frontend developer never
has to coordinate a secret, with constant-time comparison and `/health` never gated.

Worth being precise about what it does not do, and this is now stated in the README: it controls
*access*, not *attribution*. `approved_by` and `submitted_by` remain caller-supplied. Real identity is
post-MVP, and claiming otherwise would be the same category of overstatement the AI section is careful
to avoid.

### Validation

- **131 tests, under three seconds.** New coverage: the challenge workflow including the attestation
  abuse case and the non-participant rejection, optional auth, and public-data privacy scrubbing
  asserted against the committed corpus.
- **All seven hidden-ground-truth checks still at 100%** after adding 120 real artifacts — which was
  the point of keeping public data off the four engineers whose coverage the ground truth labels.
- **Every frozen number unchanged.** Three fixtures regenerated, all additive.
- **AC-14 measured** rather than assumed: reads 2.5–26 ms against an 800 ms budget, simulation 6 ms
  against 2 s.

One class of failure was caused entirely by test infrastructure rather than behaviour: the challenge
tests reseed to undo their mutations, and the session-scoped database fixture kept referring to tables
that reseeding had dropped. Thirty-one failures and eighteen errors in modules that had nothing to do
with the change — a good reminder that a fixture's lifetime is part of its contract.

### Open questions

`RECOMMENDATIONS.md` R-01 is now the only item that materially affects what the submission can claim:
the shipped extraction provider is rule-based, and the README says so plainly. Wiring a model needs a
provider choice and a credential, and changes no conclusion path. R-20 lists the ten decisions awaiting
Person B's acknowledgement, of which DEC-10 — the eleventh endpoint — is the only one needing a yes or
no.

---

## 2026-08-17 — Backend verification and API sample capture (Person B)

**What was done.** A read-only verification of the merged backend against the amended
`API_CONTRACT.md`, ahead of frontend work. All eleven route modules, every DTO schema module, the
enum module, the error envelope, and the provider factory were read and compared against the
contract and `ENGINEERING_RULES.md`. The database was reseeded, both verification scripts were run,
and 21 live payloads — the ten frozen endpoints plus `/health`, the challenge endpoint, both
designed empty states, and four error cases — were captured verbatim into `docs/api-samples/`.

Two decisions from the session preceding this work, recorded here because they change scope:
`DECISIONS.md` DEC-01's values (Payment Gateway 74/HIGH, simulation 74 → 93 HIGH → CRITICAL,
Identity 68, five capabilities, Maria Gomez) are confirmed as the canonical demo values, and DEC-10
is acknowledged — the eleventh endpoint stays, and the frontend will build a challenge action in
the provenance drawer after the golden-path screens.

**Files created.** `docs/api-samples/` — 21 payload files, `manifest.json`, `README.md`.

**Implements.** The `API_CONTRACT.md` §19 integration check; AC-14 verification; the pre-frontend
reality check preceding the gap register.

**Validation.**

- `scripts.verify_golden_path`: 10/10 endpoints matched the shared fixtures; the only difference is
  the pinned `approved_at` fixture timestamp. Latency 2.0–12.2 ms against the 800 ms read budget.
- `scripts.refresh_fixtures --check`: no stale fixture.
- Enum values in `app/schemas/enums.py` are identical to the `ENGINEERING_RULES.md` tables, with
  three additive extensions traceable to logged decisions: `CriticalitySource` (CI-19),
  `ChallengeType` (DEC-10), `ErrorCode.UNAUTHORIZED` (DEC-13).
- All identifiers observed on the wire follow typed snake_case, engineers in full-name form.
- The challenge endpoint was exercised live (attest Jordan, `INDEPENDENT_EXECUTION`): Jordan
  `EXPOSED → PRACTICED`, Incident Recovery `DEGRADED → COVERED` at 72/HIGH → 15/LOW, system held at
  74/HIGH with degraded 2 → 1 — matching the HANDOFF account. The database was reseeded afterwards.

**Open questions.**

1. `single_expert_dependency_count` appears nowhere — not in the contract, the fixtures, the
   backend, or the frontend types. The corrected dashboard design requires it on platform cards, so
   it is a UX requirement with no transport (the SR-02 class of problem) and goes to the gap
   register as the main contract question.
2. The approve response does not echo the task list and no GET-plan endpoint exists, so a
   post-approval plan view must render from client-held state. Worth an explicit note rather than
   an accidental discovery.
3. `drift_status` crosses the wire as `NEW_RISK / RISK_INCREASED / STABLE / RISK_REDUCED`; the
   dashboard copy ("Drift: increasing / stable") needs a display mapping for all four values.
4. The PRD §17.1 R1 table still assigns class CRITICAL to any CRITICAL-or-HIGH gap, which DEC-07
   superseded (class scales with criticality). `ENGINEERING_RULES.md` carries the implemented
   table; the PRD table is stale wording to amend at the next contract touch.

---

## 2026-08-17 — Gap register (Person B)

**What was done.** `docs/BACKEND_GAPS.md` created: a three-way comparison of the PRD requirements
(FR-001…025, AC-01…016, UX sections 11 and 20–21, the section 27 demo script) against the amended
contract and against observed live behavior from the captured samples. Two additional live checks
were run to make the register factual rather than inferred: AC-09 (a mitigation plan generates for
the non-top candidate — Jordan, five tasks, DRAFT, target PRACTICED) and the capability-panel data
path (graph CAPABILITY nodes carry `label`, `status`, and `operational_criticality`, which is the
transport for the System Detail capability list). The database was reseeded afterwards.

**Findings.** One BLOCKING gap: `single_expert_dependency_count` was never added to the contract
and exists nowhere — a Category C amendment to `PlatformSummary` is proposed, with an explicit
warning that summing `degraded_capability_count` is not a valid client-side substitute under
DEC-07. Eight deferrable items (approved-plan read-back, missing challenge fixture, R-14 candidate
confidence definition, three superseded-spec-text items, deliberately unimplemented PRD features
not yet annotated, small DTO absences with client-side workarounds, a cosmetic envelope
inconsistency, stale PRD example numbers). Eight design constraints recorded so screens are built
against real data paths. All sixteen acceptance criteria have a data path; AC-16's product half
remains Person B's post-build work. Enum and identifier audit: zero drift.

**Files created.** `docs/BACKEND_GAPS.md`.

**Implements.** The pre-build gap analysis the phase plan requires before frontend foundation work;
SR-02 enforcement for the corrected dashboard.

**Validation.** Every register claim cites either a live capture in `docs/api-samples/` or a
specific document section; the two new live checks were observed directly rather than assumed.

**Open questions.** GAP-01 needs a joint yes/no with Person A; GAP-03 (challenge fixture) and the
GAP-05/06/09 document amendments ride on the same sync.

---

## 2026-08-17 — UI design review (Person B)

**What was done.** All six mockups in `UI Design/` were reviewed against the binding design system
and correction list, re-based onto the canonical DEC-01 values, and mapped to the endpoints that
feed them. `docs/UI_REVIEW.md` created: per-mockup verdicts (usable as-is vs must change), the
cross-cutting design-system restorations, a 20-item shared component inventory, and the list of
seven screens that have no mockup and must be designed in the same visual language — including the
challenge-assessment drawer, newly in scope.

**Findings worth recording.** The six `DESIGN.md` files are byte-identical — one shared token
sheet (Inter ramp, warm near-white neutrals) adopted as the starting tokens where it does not
conflict with the design-system rules. The three product-inverting mockup defects were confirmed
in the images: the simulation shows 93 → 58 with a "System Resilience Score" label (must be
74 → 93 Continuity Risk Index), a "Critical Silo Detected" panel assigns a numeric knowledge level
and risk color to a named person (deleted, replaced by a capability statement), and System Detail
declares Maria Santos as owner via a registry sync (must be Jordan Lee via CODEOWNERS with the
mismatch note). The mitigation-plan mockup additionally inverts the mentor/backup roles, and every
mockup lost the mesh-gradient background layer.

**Files created.** `docs/UI_REVIEW.md`.

**Implements.** The pre-build design review phase; §C of the working brief as re-based; the §A
design system as the binding reference for Phase 5 tokens.

**Validation.** Every correction cites either a live payload in `docs/api-samples/` or a specific
brief/spec clause; endpoint mappings cross-checked against `docs/BACKEND_GAPS.md` design
constraints.

**Open questions.** Three design decisions await approval before Phase 5: the risk-class chip
color mapping, the sidebar navigation scope (Simulations/Plans destinations have no list
endpoints), and whether engineer role labels from graph metadata appear on candidate cards.
All three were resolved the same day and recorded in `docs/UI_REVIEW.md`: liquid-glass gradient
chips on the semantic scale, the four-entry sidebar reinterpreted, and name + role on engineer
rows.

---

## 2026-08-17 — App shell: ambient background and liquid-glass sidebar (Person B)

**What was built.** The Phase 5 app shell, per Person B's direction. A full-viewport animated
gradient background (the "Grainient" WebGL component from the React Bits registry, vendored as
source into `frontend/components/Grainient/` with its stylesheet) renders behind every surface
including the sidebar, with the exact parameter set chosen by Person B (#e98138 / #ffffff /
#3B82F6, contrast 1.5, zoom 0.9, animated). The left navigation is a floating liquid-glass panel —
translucent gradient fill, 24px backdrop blur with saturation, hairline light border, inset
highlight — carrying the four entries resolved in the UI review (Dashboard, Systems, Simulations,
Plans) with inline SVG icons and an active state. The layout moved from the create-next-app
boilerplate to Inter (self-hosted via `next/font`), and `globals.css` now carries the first design
tokens: warm near-white neutrals from the shared mockup token sheet, the four status colours, and
three reusable surface treatments (`glass-panel`, `frosted-card`, `glass-chip`). The dashboard
route holds a placeholder pair of frosted platform cards until Phase 6.

**Library added (Category B):** `ogl` ^1.0.11 — the WebGL micro-library the vendored Grainient
component requires. No other dependency changed.

**Files created.** `frontend/components/Grainient/Grainient.tsx`, `.../Grainient.css` (vendored),
`frontend/components/AppBackground.tsx`, `frontend/components/AppShell.tsx`,
`frontend/components/SidebarNav.tsx`, `.claude/launch.json` (dev-server launch config).
**Files changed.** `frontend/app/layout.tsx`, `frontend/app/globals.css`,
`frontend/app/page.tsx`, `frontend/package.json` / `package-lock.json`.

**Implements.** Phase 5 items 5–6 of the working plan (design tokens, app shell) as re-directed by
Person B; the background respects `prefers-reduced-motion` by freezing the animation.

**Validation.** `npm run typecheck` clean; rendered live in the browser against the running dev
server — gradient underlays the full viewport, sidebar glass shows the background through the
blur, nav active state and placeholder cards render as designed.

**Open questions.** The contract layer (Phase 5 items 2–4: types reconciliation, Zod contract
lock over `fixtures/`, adapter) is the next unit and still precedes any data-bound screen. The
background palette is noticeably more saturated than the §A lilac/blush wash; the component's
props make tuning trivial if it competes with the status colours once real screens land.

---

## 2026-08-17 — Contract layer: types reconciled, Zod contract lock, adapter completed (Person B)

**What was built.** Phase 5 items 2–4.

- `frontend/types/api.ts` reconciled with the amended contract as verified in the backend reality
  check: `IndexModifier` + optional `index_modifiers` on `CapabilityDetail` (DEC-11), the full
  challenge DTO group — `ChallengeType`, `ChallengeRequest`, `AssessmentSnapshot`,
  `SystemSnapshot`, `ChallengeResponse` (DEC-10) — and `UNAUTHORIZED` in `ErrorCode` (DEC-13).
- `frontend/lib/api/schemas.ts` — a Zod mirror of every DTO and all 19 enums plus the three logged
  extensions. Objects are strict: an undeclared field fails validation rather than passing
  silently, which is the point of a lock.
- `frontend/tests/contract-lock.test.ts` — validates **every** `.json` in repository-root
  `fixtures/` against its schema and asserts the coverage map matches the directory exactly in
  both directions, so a fixture added or removed on either side breaks the test, not a screen.
  **13 tests pass** (12 fixtures + the coverage assertion).
- `frontend/lib/api/endpoints.ts` gains the eleventh adapter function `challengeAssessment`
  (POST `/capabilities/{id}/challenge`), and `listPlatformSystems` now routes the Identity
  platform to its own fixture in mock mode instead of returning Payments data.
- Two fixtures added to the jointly owned root `fixtures/`, both captured verbatim from live
  engine output on a freshly seeded database: `identity-systems.json` (the dashboard renders both
  platforms' systems in mock mode) and `challenge-attest-jordan.json` (the challenge drawer works
  in mock mode). `fixtures.contract.ts` compile-checks both against the TypeScript types.

**Library added (Category B):** `vitest` (dev-only) — the project had no test runner and the
contract lock requires one.

**Files created.** `frontend/lib/api/schemas.ts`, `frontend/tests/contract-lock.test.ts`,
`fixtures/identity-systems.json`, `fixtures/challenge-attest-jordan.json`.
**Files changed.** `frontend/types/api.ts`, `frontend/lib/api/client.ts`,
`frontend/lib/api/endpoints.ts`, `frontend/lib/api/fixtures.contract.ts`,
`frontend/package.json` / lock file.

**Implements.** Phase 5 items 2–4; the contract-lock gate that must pass before UI work; adapter
coverage for FR-020/AC-11 (challenge) ahead of its Phase 6/7 screen.

**Validation.** `npm test` — 13/13 pass. `npm run typecheck` clean (fixtures compile against the
TypeScript types, including the two new ones). `npm run build` clean.

**Open questions / for Person A at the next sync.** The two new fixtures are engine-captured but
are **not yet wired into `scripts/refresh_fixtures.py`**, so `--check` does not guard them against
drift; asking Person A to add both (GAP-03 already requested the challenge one). `fixtures/README.md`
enumeration also needs the two new rows — jointly owned, so left for the sync.
