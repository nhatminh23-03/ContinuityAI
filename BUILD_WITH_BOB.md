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

---

## 2026-08-17 — Phase 6 begins: branch, shared primitives, dashboard (Person B)

**What was built.** Work moved to `feature/frontend-screens` with the accumulated Phase 2–5 output
committed as three logical commits. Then the first two units of the screen plan:

1. *Shared primitives.* `components/status.tsx` (ExposurePill with the dashed
   INSUFFICIENT_EVIDENCE variant, liquid-glass RiskClassChip on the semantic gradient tints,
   RiskIndex tabular numeral, DriftLabel, ConfidenceLabel), `components/people.tsx` (the
   monochrome five-step ReadinessLadder with text label and aria-label, EngineerBadge initials
   avatar), and `lib/copy.ts` — the frontend-owned display copy for all rule codes, index
   modifiers, drift values, class anchors, and the two static simulation strings. A unit test
   locks the maps, asserts unmapped codes render raw, and rejects prohibited vocabulary by regex.
2. *Dashboard.* Platform cards (highest system risk, critical-gap count, drift text; no exposure
   class per CI-10, no single-expert count pending GAP-01) and the merged systems table across
   both platforms, sorted by `sortSystemsByRisk` (unit-tested pure display sort, nulls last),
   with exposure pills, confidence, drift, tabular right-aligned indices, class chips, row
   navigation, and a per-row Simulate entry point.

**Implements.** §C.1 dashboard corrections in full; AC-01's visible-without-drill-down values;
FR-002 as amended by CI-20.

**Validation.** 18 unit tests + contract lock green; typecheck clean; verified in the browser at
1280px against fixtures — Payments 74 / 1 gap / new-risk drift, Identity 68 / 1 / stable, systems
ordered 74 · 71 · 68 · 54 · 52 with correct pills and chips.

**Open questions.** None new. Next unit: System Detail.

---

## 2026-08-17 — System Detail (Person B)

**What was built.** `/systems/{system_id}`: breadcrumb with the platform name, header with the
primary "Simulate unavailability" action (disabled until the sandbox unit), the four-cell metric
strip (Continuity Risk Index 74 + HIGH glass chip + "Why this risk?" placeholder · capabilities
without resilient backup 2 · critical gaps 0 · evidence confidence HIGH), the declared-ownership
card (Jordan Lee, CODEOWNERS, ochre "Differs from demonstrated coverage" note), the five-row
capability panel (exposure pill + coverage summary per row, no ladders, no activity chips), and
the coverage card for the URL-selected capability (engineer rows with monochrome readiness
ladders, freshness, last-demonstrated date, confidence). The graph area is a placeholder pane
until its own unit. Pure helpers `capabilitiesFromGraph`, `coverageSummary`, and
`defaultCapabilityId` project the graph payload without deriving any domain value and are
unit-tested against the shared graph fixture.

**Files created.** `frontend/app/systems/[systemId]/page.tsx`,
`frontend/features/systems/{SystemDetailView,MetricStrip,OwnershipCard,CapabilityPanel,CoverageCard}.tsx`,
`frontend/features/systems/capabilities.ts`, `frontend/tests/capabilities.test.ts`.

**Implements.** §C.2 corrections in full (valid class, relabels, no edit action, no activity
proxies, ladder off capabilities, coverage card, ownership correction); AC-02.

**Validation.** 22 unit tests + contract lock green; typecheck clean; page text verified in the
browser against fixtures — every canonical value present, including the public-data EXPOSED edge
appearing in Retry Logic's coverage summary.

**Open questions.** None new. Next unit: the evidence drawer.

---

## 2026-08-17 — Evidence drawer (Person B)

**What was built.** The provenance drawer, opened from capability rows (capability-wide) and
coverage rows (engineer-filtered) via URL state. Assessment card: exposure pill, confidence,
fired-rule display copy, declared-versus-demonstrated with the mismatch note. Seven typed
evidence cards in server order — `evidence_inc_184` leads — each carrying role, strength, and
freshness badges beside the source-type icon, reference, date, title, excerpt, and provenance
line with `source_url` when present. Missing-evidence entries (Jordan, Maria) render in the
dashed insufficient treatment; a conflicting-evidence section appears when the array is
non-empty. Footer: Close plus a disabled "Challenge assessment" primary awaiting the challenge
unit. Escape and scrim-click close with focus return.

**Files created.** `frontend/features/evidence/{EvidenceDrawer,EvidenceCard,AssessmentCard}.tsx`.
**Files changed.** `frontend/features/systems/{SystemDetailView,CapabilityPanel,CoverageCard}.tsx`,
`frontend/app/systems/[systemId]/page.tsx`.

**Implements.** §C.4 corrections (assessment card populated, typed model visible, no Acknowledge
Pattern); AC-04; the §11.4 drawer sections.

**Validation.** 22 tests + contract lock green; typecheck clean; full drawer text verified in the
browser against the fixture — all seven records with correct badges, both missing-evidence
entries, the mismatch comparison. Known mock-mode limit recorded: the fixture ignores the
`engineer_id` filter (mocks are verbatim payloads); live filtering was verified in the Phase 2
captures and re-checks in the Phase 7 live pass.

**Open questions.** None new. Next unit: the contextual graph (timeboxed).

---

## 2026-08-17 — Contextual graph (Person B)

**What was built.** The graph pane on System Detail, well inside its timebox because the layout
is deterministic rather than automatic: `toFlow` (pure, unit-tested against the shared fixture)
places nodes on fixed concentric bands — system centre, component ring, capability ring,
engineer outer ring, evidence leaves — and maps edges by type: solid DEMONSTRATES with stroke
width scaled from the received readiness label (VALIDATED 4 → NONE 1), the one dashed
DECLARED_OWNER edge labelled "declared owner" (Jordan Lee → Payment Gateway), dotted
SUPPORTED_BY, hairline structural edges. Focusing a capability — by clicking its node or via
`?focus=` — dims everything outside its neighbourhood to 18% opacity and fetches the focused
graph (`?focus_capability_id=`), which adds evidence nodes against the live backend. Tests cover
position determinism, the dashed labelled ownership edge, width ordering, and dim behaviour.

**Files created.** `frontend/features/graph/{layout.ts,SystemGraph.tsx}`,
`frontend/tests/graph-layout.test.ts`.
**Files changed.** `frontend/features/systems/SystemDetailView.tsx`,
`frontend/app/systems/[systemId]/page.tsx`.

**Implements.** §C.2's graph requirements (the solid-vs-dashed contrast, focus dimming); AC-03;
§11.3.

**Validation.** 26 tests + contract lock green; typecheck clean; verified in the browser — edge
thickness visibly varies, the dashed ownership edge reads against the solid coverage edges, and
focusing Incident Recovery keeps only Alex, Maria, Jordan, Gateway Integration, and the system at
full opacity. Mock-mode note: the focused fixture is the unfocused payload, so evidence nodes
appear only against the live backend (Phase 7 pass).

**Open questions.** None new. Next unit: the Why-this-risk panel.

---

## 2026-08-17 — "Why this risk?" panel (Person B)

**What was built.** The metric strip's "Why this risk?" link now opens a glass modal carrying the
system-level fired rules ("A business-critical capability lacks a resilient backup", "Multiple
capabilities depend on a single expert"), the selected capability's rules, and the index
arithmetic: HIGH anchor 70, +1 only-one-engineer, +1 next-strongest-only-assisted, = 72/100 —
every number the server's own (anchor from the received class, deltas from `index_modifiers`,
total from the index field; nothing recomputed). The block is omitted when modifiers are absent,
and the footnote reads "The index is a comparison number, not a probability." Escape/scrim close
with focus return; URL-driven (`?why=1`).

**Files created.** `frontend/features/systems/WhyPanel.tsx`.
**Files changed.** `frontend/features/systems/{SystemDetailView,MetricStrip}.tsx` (link enabled),
`frontend/app/systems/[systemId]/page.tsx`.

**Implements.** AC-07's "Why?" surface; FR-013's contributing-factor display; DEC-11 rendered;
missing-screen 2 from the UI review.

**Validation.** 26 tests + contract lock green; typecheck clean; verified in the browser —
70 + 1 + 1 = 72 renders with descriptive copy per line.

**Open questions.** None new. Next unit: the simulation sandbox.

---

## 2026-08-17 — Simulation sandbox and launcher (Person B)

**What was built.** The counterfactual overlay (URL-driven from System Detail's primary action and
the dashboard row action) and the `/simulations` launcher. The overlay corrects every §C.0/§C.3
defect: 74 → 93 in the right direction under the "Continuity Risk Index" label with the
HIGH → CRITICAL class transition beside the numbers, "Nothing has changed in your real data." in
the header, the grounded API summary in place of departure/urgency copy, all five capability
impact rows — the two survivors marked "unchanged" — each with a best-remaining readiness ladder,
counts 0/2/3 → 2/1/2, and the static disclaimer "This models coverage loss. It does not predict
an outage." The engineer selector defaults to the strongest demonstrated engineer
(`primary_engineer`, a received value) and shows name + role from graph metadata. The primary
action carries `simulation_id` and the worst-hit capability into the candidates route. No
prohibited panel: the person-level "silo" framing from the mockup does not exist here.

**Files created.** `frontend/features/simulations/{SimulationOverlay,ImpactRow}.tsx`,
`frontend/app/simulations/page.tsx`.
**Files changed.** `frontend/features/systems/SystemDetailView.tsx` (simulate wiring, button
enabled), `frontend/app/systems/[systemId]/page.tsx`.

**Implements.** §C.0 and §C.3 in full; FR-014, FR-015; AC-06; §11.5; CI-32's static disclaimer.

**Validation.** 26 tests + contract lock green; typecheck clean; verified in the browser — the
canonical transition, five rows, banner, and disclaimer all render; the launcher lists all five
systems. Mock-mode note: the fixture returns the Alex scenario for any engineer selection; the
Sofia no-loss case is exercised in the Phase 7 live pass.

**Open questions.** None new. Next unit: backup candidates.

---

## 2026-08-17 — Backup candidates (Person B)

**What was built.** `/systems/{id}/candidates?capability=&simulation=`: Maria Gomez (HIGH
overlap) and Jordan Lee (MEDIUM) as frosted cards with monochrome initials and roles from graph
metadata — no photographs — demonstrated strengths as chips, per-candidate gap statements from
the API, "Confidence in demonstrated coverage of this capability: MEDIUM" (the honest GAP-04
wording), an evidence link opening the provenance drawer filtered by engineer, and **Generate
transfer plan** as each card's primary action. A quiet free-choice select covers AC-09 (any other
system engineer can be picked). The Not-considered panel lists all seven excluded factors —
including career goals and performance history per the correction list — with the API disclaimer
verbatim and the line "The manager chooses. Nothing here assigns anyone to anything." The plan
route receives capability, backup, simulation id, and the primary engineer.

**Files created.**
`frontend/features/recommendations/{CandidatesView,CandidateCard,NotConsideredPanel}.tsx`,
`frontend/app/systems/[systemId]/candidates/page.tsx`.

**Implements.** §C.5 in full; AC-08, AC-09; FR-016/FR-017's display side; §11.6.

**Validation.** 26 tests + contract lock green; typecheck clean; page text verified in the
browser — both candidates with correct overlaps, gaps, confidence, and the complete
not-considered list.

**Open questions.** None new. Next unit: the mitigation plan.

---

## 2026-08-17 — Mitigation plan (Person B)

**What was built.** `/plans/new` (generate → edit → approve) and `/plans` (the session's plan or
a designed empty state). The mockup's inverted roles are corrected structurally: the header reads
"Developing: Maria Gomez · Knowledge source: Alex Chen", and the task copy comes from the API,
which already has the direction right. DRAFT status chip, target readiness PRACTICED labelled
"(target, not achieved)", task-type labels, acceptance criteria, and linked-evidence chips per
card. Cards are editable while DRAFT; edited tasks are submitted with the approve call (CI-12) and
omitted when untouched. The approved state — APPROVED chip, approver, timestamp, final task list —
renders from a unit-tested sessionStorage store because the approve response echoes no tasks and
no read-back endpoint exists (GAP-02); it survives navigation and reload within the session.
"Est." durations and mode chips do not exist here. Double-approval renders the VALIDATION_ERROR
copy.

**Files created.** `frontend/features/mitigation/{planStore.ts,TaskCard.tsx,PlanView.tsx}`,
`frontend/app/plans/{new/page.tsx,page.tsx}`, `frontend/tests/planStore.test.ts`.

**Implements.** §C.6 in full; AC-09, AC-10; FR-018/FR-019; §20.2's structure minus the fields the
DTO does not carry.

**Validation.** 29 tests + contract lock green; typecheck clean; the full flow exercised in the
browser — task title edited, plan approved, APPROVED chip and approval line rendered, and the
edited title verified inside the session store and on `/plans` after navigation.

**Open questions.** None new. Next unit: capability detail, the final Phase 6 screen.

---

## 2026-08-17 — Capability detail, closing the screen phase (Person B)

**What was built.** `/capabilities/{capability_id}`: breadcrumb into the owning system, header
with the index (72), class chip (HIGH), exposure pill, confidence, criticality, and the reused
Why panel; `primary_engineer` and `best_remaining_coverage` rendered as quiet labels ("strongest
demonstrated coverage", "best remaining") rather than ranks; the engineer-by-engineer coverage
list with monochrome ladders, freshness, dates, and per-engineer evidence entry; a
capability-wide evidence view; and a Simulate unavailability action linking into the sandbox.
INSUFFICIENT_EVIDENCE is a designed state — dashed container, em-dash index, and copy naming
evidence-gathering as the next step.

**Files created.** `frontend/features/systems/CapabilityDetailView.tsx`,
`frontend/app/capabilities/[capabilityId]/page.tsx`.

**Implements.** Endpoint 5's screen (UI-review missing-screen 1); FR-022's evidence-backed
person rows within capability context; the INSUFFICIENT_EVIDENCE design (missing-screen 4).

**Validation.** 29 tests + contract lock green; typecheck clean; `npm run build` clean with all
eight routes; page text verified in the browser. The INSUFFICIENT_EVIDENCE visual can only be
exercised against the live backend (`cap_permission_audit`) since mock mode serves the
incident-recovery fixture for every capability id — scheduled for the Phase 7 live pass; the
render logic is null-driven either way.

**Phase status.** All nine screens of the screen phase are built, each behind its own approval:
dashboard, system detail, evidence drawer, contextual graph, why panel, simulation sandbox,
backup candidates, mitigation plan, capability detail. The golden path is clickable end to end on
fixtures. Remaining for the final phase: the challenge drawer, the full state suite, the live
integration pass, responsive polish, and the demo-script walkthrough.

---

## 2026-08-18 — Final phase: challenge drawer, state suite, live integration pass (Person B)

**What was built.** The challenge drawer (closing FR-020 and AC-11 front-to-end): three evidence
operations with a required audit comment and structurally no score inputs; the result view
renders the recomputation from the response snapshots and success invalidates every query so all
screens refetch. State-suite fills across four components (partial-failure notice on the systems
table, error codes on the coverage card, a why-panel error line, launcher loading state); every
screen now has loading, empty, and error treatments switching on `error.code`.

**Live integration pass** (`NEXT_PUBLIC_USE_MOCKS=false`, backend on :8000). Results:

- **One divergence found and resolved without patching the frontend:** the backend pins CORS to
  `http://localhost:3000`, and the dev server was running on :3002 (a leftover instance), so
  every live call failed as a network error. Resolution: the stale server was stopped and the
  frontend now runs on :3000 as the backend expects. Worth remembering: the frontend must run on
  :3000 against the live backend.
- Dashboard, system detail, graph values: identical to fixtures (as the fixture regeneration
  guarantees). No payload divergences anywhere.
- INSUFFICIENT_EVIDENCE verified live (`cap_permission_audit`): dashed treatment, em-dash index,
  LOW confidence, Grace Liu's single EXPOSED row.
- Engineer-filtered evidence verified live: Alex's view returns exactly INC-184, INC-221, DOC-17.
- Focused graph verified live: seven EVIDENCE nodes with SUPPORTED_BY edges arrive server-side.
- Full golden path executed live with real mutations: simulation `sim_002` (74 → 93,
  HIGH → CRITICAL, five rows), candidates (Maria HIGH / Jordan MEDIUM), plan generated, task
  edited, approved with the edit riding the call (CI-12) and a real timestamp.
- Challenge verified live: attesting Jordan moved him EXPOSED → PRACTICED, Incident Recovery
  DEGRADED 72/HIGH → COVERED 15/LOW, the system held at 74/HIGH with degraded 2 → 1 — matching
  the backend handoff's account exactly — and the metric strip refetched to show the new counts.
- The database was reseeded afterwards; the demo state is pristine.

**Responsive.** All screens verified at 1280×860 throughout; no horizontal overflow.

**Demo script (PRD section 27) walkthrough.** Every product beat lands: 0:18 dashboard (74, gap
count), 0:30 system detail and graph, 0:50 Why + provenance cards, 1:08 simulation with Retry
Logic preserved, 1:28 candidates, 1:50 plan with four actions and criteria, 2:15 approve. The
0:00–0:18 opening (outage card, declared-owner intro) and the 2:30 architecture graphic are video
assets, not product screens — the ownership card covers the declared-vs-demonstrated visual if
wanted on screen. The optional challenge beat (Jordan attestation, system holding at 74) is
strong and now demonstrable live.

**Files created.** `frontend/features/challenge/ChallengeDrawer.tsx`.
**Files changed.** `frontend/features/evidence/EvidenceDrawer.tsx`,
`frontend/features/dashboard/SystemsTable.tsx`, `frontend/features/systems/{CoverageCard,WhyPanel}.tsx`,
`frontend/app/simulations/page.tsx`; `frontend/.env.local` created locally (gitignored) pointing
at the live backend.

**Implements.** FR-020, AC-11 (challenge UI); AC-15's state suite; the live-integration and
demo-walkthrough requirements of the final phase.

**Validation.** 29 unit tests + contract lock green; typecheck and build clean; every live check
above observed directly in the browser.

**Open questions.** The four Person A sync items stand (GAP-01, fixture wiring, doc amendments,
key rotation). Demo video, screenshots, and the README product narrative remain Person B's
submission work.

---

## 2026-08-21 — Mitigation-plan generation: fix the post-commit enum bug

**What was built/decided.** `MitigationPlanService.create` wrote `task.task_type` (an
unvalidated `str` from the `AIProvider`) directly into the `MitigationTask` ORM row and
committed; `MitigationTaskType` coercion happened only later, in `_to_response`, which every
subsequent `get` also runs. `DeterministicProvider` never emits an out-of-enum value, so this
was latent, but it becomes reachable once a language-model provider is generating task text.
An invalid value used to persist successfully and then raise a bare `ValueError` on every read
back (a 500 with no error envelope, since `app/core/errors.py` handles only `DomainError` and
`RequestValidationError`), leaving the row permanently unreadable. Fixed by coercing
`task.task_type` into `MitigationTaskType` inside the task-building loop, before
`repository.add(plan)` is called, raising `MitigationGenerationError` (an existing
`DomainError` subclass) on failure — matching the style of the task-count guard already in the
same method. Nothing is added to the session before the raise, so a failing generation persists
no row. The manager-edit path (`ApprovePlanRequest.tasks`) was left untouched; it is already
validated at the request boundary by Pydantic.

**Files changed.** `backend/app/mitigation/service.py` (the coercion, inside `create`).
**Files created.** `backend/tests/test_mitigation_service.py`.

**Implements.** Groundwork for the upcoming LLM-generated mitigation-plan text: task 1 of
`.superpowers/sdd/superpowers-brainstorming-continuityai-merry-heron/task-1-brief.md`.

**Validation.** Test-first: `test_an_invalid_provider_task_type_raises_cleanly_and_persists_nothing`
was confirmed failing against the unfixed code (bare `ValueError` from `_to_response`, not
`MitigationGenerationError`), then passing after the fix. Full backend suite:
`cd backend && PYTHONPATH=. .venv/bin/python -m pytest` → 148 passed, including the existing
golden-path mitigation create/approve/edit coverage (deterministic-provider output unchanged).

**Open questions.** None for this task.

---

## 2026-08-21 — The language policy and the narrative validation gate

**What was built/decided.** The safety gate that model-written manager-facing prose has to pass.
Nothing calls it yet; it exists so that the next step — letting a language model write the
simulation sentence, the candidate strengths and gaps, and the mitigation plan — is defensible
rather than hopeful. Every check reports; none of them raises, so a caller that gets a rejection
falls back to the deterministic template and the request still succeeds.

`app/ai/language_policy.py` holds the wording rules: the canonical prohibited-phrase list, the
probability markers (`%`, "probability", "chance of", "will fail") that would turn a coverage
statement into an outage forecast, the inability markers that would turn absence of evidence into
a claim about a person (PRD 22.3), and an unattested-name check. The phrase list previously
existed only in `tests/test_responsible_ai.py`, where it was applied to source-code string
literals and never to runtime output; it is now enforceable at runtime with contents unchanged, so
the test can import it in a later task without altering behaviour.

Two decisions worth recording:

* The phrase list lives in `app/ai/prohibited_phrases.txt` rather than as literals in the module.
  `test_responsible_ai.py::test_no_prohibited_phrase_appears_in_generated_text` scans string
  constants under `app/ai` for exactly these phrases, so a module that spelled them out would be
  flagged by the rule it exists to enforce — the same reason that test already excludes
  `app/ai/prompts/`. Holding them as data avoids needing an exception in a check that is most
  useful when it is blunt.
* The unattested-name check is a heuristic and is biased on purpose. It reads multi-word
  capitalised runs as proper names, skips a run's first word where it opens a sentence or line
  (it may be capitalised by position — "Shadow Incident Recovery" is a task title), and requires
  every remaining word to come from the facts the generator was given or to be a closed-class
  function word. It over-reports rather than under-reports: a false positive costs the generated
  wording, a false negative puts an invented capability or an invented colleague in front of a
  manager.

`app/ai/validation.py` gains the three validators beside `validate_extraction`, sharing its shape:
`validate_simulation_summary`, `validate_candidate_narrative`, `validate_plan_draft`. Unknown
`linked_evidence_ids` are dropped with a correction logged rather than rejecting the plan,
mirroring how `validate_extraction` corrects an evidence strength instead of discarding the claim.
The task-count rule (AC-10, 3-5 actions) is checked here as well as in `MitigationPlanService`
because the service raises `MitigationGenerationError` — right for a broken generator, wrong for a
model that simply wrote six actions, which should quietly fall back mid-demo.

AC-09 (the plan is specific to the chosen candidate) was previously an implicit property of the
template in `deterministic.py`: a candidate at `NONE`/`EXPOSED` gets an extra `RECOVERY_DRILL`
task, one who has already assisted does not, and `test_golden_path.py:208-218` asserts the
comparison between two generated plans. A validator only ever sees one plan, so the rule is
encoded as readiness bands whose ranges do not overlap: the `NONE`/`EXPOSED` band takes exactly
five actions and must include a `RECOVERY_DRILL`; `ASSISTED` and above take three or four and must
not. Any two plans that pass therefore satisfy the comparison. `requires_recovery_drill` is the
single definition of the readiness half of that rule and `DeterministicProvider` now branches on
it, so the template and the gate cannot drift apart silently.

**Files created.** `backend/app/ai/language_policy.py`,
`backend/app/ai/prohibited_phrases.txt`, `backend/tests/test_narrative_validation.py`.
**Files changed.** `backend/app/ai/validation.py` (the three validators, the outcome types, the
shared AC-09 predicate), `backend/app/ai/deterministic.py` (the drill branch now calls
`requires_recovery_drill`).

**Implements.** Task 2 of
`.superpowers/sdd/superpowers-brainstorming-continuityai-merry-heron/task-2-brief.md`: PRD 22.3
wording rules, FR-017 evidence-backed narrative content, AC-09 and AC-10 on the plan.

**Validation.** Test-first, one test per rejection path with its accepting case beside it:
`cd backend && PYTHONPATH=. .venv/bin/python -m pytest tests/test_narrative_validation.py` → 50
passed. Two of those tests run the deterministic provider's own summary, narrative, and plan
(across all five readiness levels) back through the gate, which is what fails first if the
template and the validator ever disagree. Full backend suite → 198 passed, including
`test_responsible_ai.py` and the golden-path AC-09/AC-10 assertions, unchanged.

**Open questions.** The unattested-name heuristic accepts a recombination of given words
("Payment Recovery" from "Payment Gateway" and "Incident Recovery"). Tightening that needs the
capability taxonomy passed into the validator, which the brief's signatures do not carry; worth
revisiting if the prompt work shows the model actually doing it.

### 2026-08-21 — Review fixes on the narrative gate

Three findings from review of the entry above, all fixed.

**The name check rejected ordinary title-cased output.** The word-level rule ("every word of a
capitalised run must be an attested word or a function word") rejected `Review Incident Recovery
Architecture`, `Execute Incident Recovery In Staging` and every other title-cased task title,
because `Architecture`, `Staging`, `In` and `The` are not names and not function words. Sentence
case passed and title case failed — a formatting coin-flip, and one that would have templated
almost every well-formed plan while looking exactly like a gate that works. Rebuilt on a different
basis: strip every attested name from the line first, then judge what survives. Two rules now
apply — a surviving fragment of an attested *person's* name next to another capitalised word is a
recombination (`Sarah Chen` where the record holds `Alex Chen`) and is caught in any casing; an
unattested capitalised run is caught only where capitalisation carries information, meaning a line
that is otherwise lower-case and a run that does not capitalise a function word. `people` was
added as a third parameter of `find_unattested_names` so the person rule knows which attested
names are individuals.

**The check had bypasses.** The recombination rule closes the sharpest one — an invented forename
on a real surname, which the previous "skip the first word of a line-initial run" step made
invisible in every plan field. Three remain and are now stated in the module docstring, in a test
(`test_known_blind_spots_of_the_name_check`) and in the task report rather than left for someone
to discover: a single-word invention (`ask Priya`, `with Stripe`), a lower-case invented
capability, and an invented capability on a fully capitalised line. Closing the last two needs the
capability taxonomy passed into the validator the way `validate_extraction` receives it; until
then the prompt carries that weight and the gate is a net under it, not a substitute.

**The `ASSISTED`+ drill rejection had no effective test.** Deleting it still left the suite green:
the only test covering it used five tasks, which the readiness band (3-4) already rejects. Added
`test_a_drill_at_assisted_is_rejected_at_a_legal_action_count` — four tasks, one of them a
`RECOVERY_DRILL`, which is the exact shape that would break `test_golden_path.py:213`. Both that
rule and the recombination rule were mutation-checked: removing either now fails a test.

**Rejections are logged.** `_report` logs every rejection at WARN with its reasons and every
correction at INFO, from all three validators including their early returns. A rejected generation
is silent by construction — the caller falls back to the template and the response looks normal —
so without this a gate rejecting everything is indistinguishable from a gate working.

**Files changed.** `backend/app/ai/language_policy.py`, `backend/app/ai/validation.py`,
`backend/tests/test_narrative_validation.py`.

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest tests/test_narrative_validation.py
tests/test_golden_path.py tests/test_responsible_ai.py` → 89 passed. Full suite → 210 passed. The
four title-cased titles from the review and the four bypasses were re-measured directly against
the rebuilt check; all sixteen cases now behave as intended.

### 2026-08-21 — Bound the title exemption to two-word runs

Re-review found that the `quoted_title` exemption added in the previous entry was over-broad and
reopened the bypass class it was meant to sit beside: any capitalised run containing one
capitalised closed-class word was exempt at any length, so `Loop in Sarah Kim And Priya Raman
before the drill.` — two entirely invented colleagues in ordinary prose — passed on the strength
of one capitalised `And`. The stated rationale ("nobody capitalises 'In' mid-sentence") holds for
a stray `In` at the tail of a stripped title; it does not hold for `And`, `From` or `The` binding
several capitalised words together.

Bounded the exemption to runs of exactly two words. Every run surviving the attested-name strip in
a real title is two words long (`In Staging`, `Update The`), while an invented name needs more
room. All four title-cased titles from the first review stay accepted and all five strings from
the re-review are now caught, measured directly against the built module.

`test_known_blind_spots_of_the_name_check` lost `Review The Settlement Batching Runbook`: the
narrowing closes it inside a plan, because a task carries a prose description alongside its title
and the description is checked. The stale assertion was inverted into
`test_a_capitalised_function_word_does_not_buy_a_run_an_exemption`, which pins all six strings as
rejected so the exemption cannot widen again unnoticed. The blind-spot list in the module
docstring was rewritten to match: a bare fully capitalised line, and a two-word qualifier attached
to an attested name (`Refund Processing In Europe` where `Refund Processing` is attested), are
what remain.

**Files changed.** `backend/app/ai/language_policy.py`,
`backend/tests/test_narrative_validation.py`.

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest tests/test_narrative_validation.py
tests/test_golden_path.py tests/test_responsible_ai.py` → 94 passed. Full suite → 215 passed.

### 2026-08-21 — Add the OpenRouter provider: model-written narratives behind the gate

The mirror image of `WatsonxProvider`. That one lets a model do extraction and keeps the narratives
deterministic; `OpenRouterProvider` does the opposite — extraction delegates to
`DeterministicProvider` in one line, and a model writes only the three manager-facing narratives.
The split follows from where the damage is. Every risk number in the product is computed from the
extracted graph, so a model reading an artifact differently changes readiness, exposure and
continuity risk while every number still looks plausible. The narratives change no conclusion and
are the part a manager reads out in a room, so that is where the model calls are spent.

**Every generation passes the gate before it is returned.** Each narrative method builds a context
message, calls the model, parses, validates through `app/ai/validation.py`, and returns the result
only if the outcome is accepted. Any failure at all — transport, timeout, output that is not JSON,
a field the model omitted, a rejection by the gate — logs at WARN and returns
`self._fallback.<same method>(context)`. `generate_mitigation_plan` returns `outcome.draft`, the
filtered draft, never the one that was passed in: the gate drops citations that do not resolve, and
an unresolvable evidence id in front of a manager is a citation to nothing. `target_readiness` is
copied from the context and never taken from the model.

**Grounding is prompt-enforced, and that is a deliberate division of labour.** The gate's
`find_unattested_names` is a documented heuristic with known blind spots — a single-word invention
and a lower-case invented capability both pass it, which
`test_known_blind_spots_of_the_name_check` pins on purpose. So the three prompt files carry the
grounding rule explicitly: use only the capability names, engineer names and evidence ids in the
message, name no colleague who is not listed, invent nothing. The prompts live in
`app/ai/prompts/*.txt` rather than in code, which also lets them name prohibited wording *in order
to forbid it* without tripping the `.py` literal scan in `tests/test_responsible_ai.py` — the same
workaround `watsonx.py:333-335` documents. The plan prompt takes its action count from
`validation._task_count_band` rather than restating it, so a prompt cannot ask for a count the gate
would reject; a mismatch there would fall back on every call, silently.

**Timeouts are sized to AC-14.** `openrouter_timeout_seconds` defaults to 3.5 so that three
sequential calls come to 10.5s, inside the 12-second budget for an AI plan or explanation
operation. *Corrected the same day: the "three sequential calls" premise was false when this was
written — `explain_candidate` ran once per eligible engineer, four of them on the seeded data. See
the entry below, which moved narration after the `limit` slice and made the bound real.* Deliberately not batched: batching would change the `AIProvider`
protocol for one provider's convenience. `openrouter_max_retries` defaults to 0 for the same
reason — a second call spends the rest of the budget to buy a wording that the template already
provides — and the retry/backoff loop honours a higher value where latency is not budgeted, with
`Retry-After` capped at 2s. A plan is one call per request rather than one of three, so it gets
twice the per-call ceiling.

**The cache guard is a refusal, not a note.** `scripts/extract_with_provider.py` names its output
after the provider, so `--provider openrouter` would write an `openrouter_cache.json` full of
string-matched output, and a later provider comparison would compare the deterministic provider
against itself without knowing it. The provider raises `CacheBuildRefusedError` from its
constructor when the entry script is the cache builder, which stops the run before the first
artifact instead of printing 640 identical per-artifact failures and still writing the file.
Verified by running the script: it aborts at `get_provider`, and `data/extraction/` is untouched.

**Files changed.** `backend/app/ai/openrouter.py` (new), `backend/app/ai/prompts/`
`simulation_summary_system.txt`, `candidate_narrative_system.txt`, `mitigation_plan_system.txt`
(new), `backend/app/ai/provider.py` (registration), `backend/app/core/config.py`
(`openrouter_api_key`, `openrouter_base_url`, `openrouter_model`, `openrouter_timeout_seconds`,
`openrouter_max_retries`), `backend/tests/test_openrouter_provider.py` (new).

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest tests/test_openrouter_provider.py`
→ 31 passed. Full suite → 246 passed, up from 215 with none lost. No test touches the network:
`_chat` is stubbed the way `tests/test_watsonx_provider.py` stubs it, and the four transport tests
replace the httpx client instead. Each of the three narratives is covered four ways — a good reply
accepted, a reply the gate rejects, a malformed or fenced reply, and a transport failure — each
asserting the deterministic template is what comes back.

**Open questions.** Nothing here has been run against the live API yet; the timeout figures are
budget arithmetic, not measurements, and a real pass may show 3.5s is tight for a candidate
explanation. Whether narrative generation should be enabled for the demo at all is a separate call:
`AI_PROVIDER` still defaults to `deterministic`, so this changes nothing until it is set.

### 2026-08-21 — Review fixes: bound the narrative calls, catch the overstatement, fail loudly

Four fixes from the review of the OpenRouter provider. The core property held under attack — eight
mutations produced no route by which model output reaches a caller unvalidated — so these are about
the budget the provider sits inside and about three ways it could degrade silently.

**The AC-14 budget was unenforceable, and the timeout was sized against a false premise.**
`explain_candidate` was called from `_candidate(...)` inside the scoring loop, which runs once per
*eligible engineer*, not once per returned candidate: the `scored[: request.limit]` slice happens
afterwards. Measured across all 25 capabilities on the seeded dataset, the worst case was
`cap_retry_logic` at 4 calls for 3 returned candidates — 14s against a 12-second budget, bounded by
nothing except how many engineers happen to qualify.

Fixed at the source rather than by shrinking the timeout. `_candidate` now returns the structured
candidate together with the `CandidateNarrativeContext`, and `_narrate` runs over the sliced list,
so the provider is called once per candidate that is actually returned and the bound is `limit`,
which the contract caps at 3. That stops paying for prose on candidates about to be discarded,
which is worth doing whatever the provider is. Measured again after the change: 3 calls for 3
returned, worst case across every capability.

The DTO is unchanged for the candidates that are returned. `tests/test_recommendation_service.py`
pins all three properties — narratives written equals candidates returned, in the returned order,
across every capability; a `limit` of 1 buys one call; and the endpoint payload still equals
`fixtures/backup-candidates.json` field for field. Mutation-checked by stashing the service change
and re-running: two of the three fail against the old code.

`test_the_call_stays_inside_the_operation_budget` asserted `timeout * 3 <= 12` with a hardcoded 3,
so it asserted an assumption about the caller rather than the caller's bound and could never have
caught this. It now reads the `le` constraint off `BackupCandidateRequest.limit`.

**The product's stated core failure mode was passing the gate.** `validate_candidate_narrative`
flattens the demonstrated, assisted and missing lists into one `attested` list before handing them
to `find_unattested_names`, which loses the bucket — so with Incident Recovery assisted-only in the
context, `Demonstrated Incident Recovery independently` was accepted and returned to a manager. The
name check cannot see this by construction: the capability *is* attested.

Added the bucket-aware rule to `validate_candidate_narrative`, which is the only place that still
has the lists apart, in the report-don't-raise style of the module. A strength naming a capability
the record holds as assisted-only or missing, alongside wording that claims independent execution,
is rejected. The marker vocabulary went to `language_policy.py` as `find_independence_language`,
beside `find_inability_language` and `find_probability_language`, because that module owns what
words mean here while validation owns which facts they may be applied to. Six tests: five rejected
phrasings, the same wording accepted for a demonstrated capability, and assisted participation
still stateable as assisted. The deterministic gap line — "No qualifying independent evidence for
X" — is unaffected: the rule reads strengths only, and `test_the_deterministic_narrative_passes_its
_own_gate` covers it.

**Two silent-degradation holes closed.** `_clean` coerced anything to `str`, so a strengths entry
returned as an object became the literal text `{'capability': 'Provider Failover', 'note': ...}` in
front of a manager and passed the gate as one unremarkable line; it now keeps text entries only,
which empties the list and routes to the template. `_plan_task` had the same shape via
`str(entry["title"])` and now takes the fields as they came. And the constructor validated only the
API key, so an empty `OPENROUTER_BASE_URL` or `OPENROUTER_MODEL` in `.env` — which silently beats
the default — constructed fine and then degraded to templates forever behind one WARN line. All
three are now checked, naming each missing value, matching `watsonx.py:86-95`.

**Files changed.** `backend/app/recommendation/service.py`, `backend/app/ai/validation.py`,
`backend/app/ai/language_policy.py`, `backend/app/ai/openrouter.py`, `backend/app/core/config.py`,
`backend/tests/test_recommendation_service.py` (new), `backend/tests/test_narrative_validation.py`,
`backend/tests/test_openrouter_provider.py`.

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest` → 261 passed, from 246,
with no test removed and one rewritten. `tests/test_golden_path.py tests/test_api_contract.py` →
33 passed, run explicitly because the recommendation service changed. No network, no seeding, no
live API call.

**Open questions.** Unchanged from the previous entry: none of this has run against the live API,
and the per-call ceiling is still arithmetic rather than measurement. The 12-second budget now has
a real bound behind it, which is what makes measuring it meaningful.

### 2026-08-21 — Make the responsible-AI phrase check real at runtime

Backfilled entry — written after the fact, from `git show dfb8dae`, because this commit landed
without one at the time. The commit is two test files only, fully inspectable, so writing the
entry retroactively carries no real risk of misattributing a decision; noted here rather than
silently left missing, which is what the previous version of this log did.

`test_no_prohibited_phrase_appears_in_generated_text` (`backend/tests/test_responsible_ai.py`)
AST-scans `.py` string literals under `app/` for `FORBIDDEN_PHRASES`, which is exactly why it
could not have caught anything a configured model provider writes at request time: prose a model
returns exists nowhere as a source-code literal. With `OpenRouterProvider` landed two commits
earlier, that blind spot stopped being theoretical.

Two changes close it. First, `FORBIDDEN_PHRASES` in `test_responsible_ai.py` — previously eight
strings duplicated by hand — is now imported from `app.ai.language_policy`, the module the
narrative gate itself reads from, so the static scan and the gate can no longer drift onto two
different lists; `test_golden_path.py`'s separate `test_simulation_summary_never_predicts_an_outage`
had its own local outage-language tuple and was moved onto `find_probability_language` and
`find_forbidden_phrases` from the same module for the same reason, keeping `"outage will"` as an
explicit extra check since it is not itself a canonical marker but the test previously asserted
against it. Second, and the actual fix: a new
`test_no_prohibited_phrase_appears_in_narrative_endpoint_responses` POSTs the three endpoints that
return model-generated prose — `/simulations`, `/recommendations/backup-candidates`,
`/mitigation-plans` — and scans every narrative field in the live response (`summary`; each
candidate's `strengths` and `gaps`; each task's `title`, `description`, and
`acceptance_criteria`) against `find_forbidden_phrases`. Tests run under the default
`deterministic` provider, so today this asserts the template output is clean — that is the point:
the same assertions cover whatever a configured model provider writes without the test needing to
change when one is.

**Files changed.** `backend/tests/test_responsible_ai.py`, `backend/tests/test_golden_path.py`.

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest -q` → 262 passed at the time
of this backfill (re-run for this entry; the commit's own contemporaneous count was not recorded).

**Open questions.** None beyond what the OpenRouter provider entries already carry. This entry
exists to close the log gap identified in review of the following documentation task, not because
new work was done here.

### 2026-08-21 — Documentation for the OpenRouter narrative provider: fixture policy, README, decision log, environment template

Four pieces, no application code. `fixtures/README.md` gets a fixture-capture policy section:
fixtures are always captured under `AI_PROVIDER=deterministic`, on the strength that
`OpenRouterProvider.extract_artifact_semantics` delegates to `DeterministicProvider` so every
non-narrative field is unaffected by which of the two produced the fixture, while its three
narrative fields are not byte-reproducible even at temperature 0. Neither `refresh_fixtures.py` nor
`verify_golden_path.py` needed a code change: both already read `AI_PROVIDER` from the environment
and default to `deterministic`, so `--check` keeps passing exactly as before, and the section states
plainly that narrative-field differences reported by `verify_golden_path` under
`AI_PROVIDER=openrouter` are expected — its exit code is 0 by design regardless — and not something
to chase as drift.

`README.md`'s AI-provider section gets a fourth provider row, a "What runs, precisely" paragraph
stating the split in one place (rule-based extraction; the three narratives template-written by
default and model-written-and-validated under `openrouter`; readiness, exposure, risk, and
simulation always deterministic, guaranteed by the `AIProvider` interface shape rather than by
configuration), and a full subsection on `OpenRouterProvider` — what it does, that the validation
gate stands between every generation and the caller, and an explicit statement that grounding is
prompt-enforced rather than gate-enforced, naming the gate's documented blind spots (a single-word
invention, a lower-case invented capability, a fully capitalised line) so the claim is not
overstated. The existing watsonx measured-comparison material is untouched.

`docs/DECISIONS.md` gets DEC-15, the Category C entry the addition requires. It records that the
provider reopens two decisions `watsonx.py` documents and quotes them directly — lines 360-362 on
`explain_candidate` ("a rephrasing that drifts is worse than a plain one") and 366-371 on
`generate_mitigation_plan` ("invented steps or an invented tool would be a real cost... Left
deterministic on purpose") — states the counter-argument (the validation gate is what the model
drafts against before anything reaches a caller) without hiding the gate's own limits, and marks
itself as needing Person A's acknowledgement rather than Person B's, since it reopens Person A's
reasoning in a file Person A owns.

`backend/.env.example` gets the three operator-facing OpenRouter variables — `OPENROUTER_API_KEY`,
`OPENROUTER_BASE_URL`, `OPENROUTER_MODEL` — with no real values, matching the pattern the watsonx
block already sets and restoring the completeness `RECOMMENDATIONS.md` R-23 recorded as remediated.
`openrouter_timeout_seconds` and `openrouter_max_retries` are left out of the file, the same way
`watsonx_timeout_seconds` and `watsonx_max_retries` are: both have working defaults and neither
carries an operator-facing caveat the way `WATSONX_REQUESTS_PER_SECOND`'s plan-limit note does.

**Files changed.** `fixtures/README.md`, `README.md`, `docs/DECISIONS.md`, `backend/.env.example`.
No file under `backend/app/` or `frontend/` touched.

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest -q` → 262 passed, unchanged
from before this entry, since nothing here touches application code. No seed or fixture-refresh
script run; no network call made; `backend/.env` never read.

**Open questions.** DEC-15 needs Person A's walkthrough before `AI_PROVIDER=openrouter` is treated
as more than implemented-and-available; tracked as OPEN-10. Two pre-existing items noticed but left
alone as out of scope for this pass: the commit that made the responsible-AI phrase check run at
runtime has no `BUILD_WITH_BOB.md` entry of its own, and the Checks section of `README.md` still
reads "131 tests" against a suite that is now 262.

### 2026-08-21 — Review fixes on the OpenRouter documentation: seven accuracy corrections

A review of the previous entry's four documentation files found five factual errors, both declined
cleanup items reconsidered and required, and four cheap accuracy minors — all fixed, no application
code touched.

**`cached` was miscategorised as rule-based extraction.** `README.md` said extraction is rule-based
"under every provider except `watsonx`," which is false for `cached`: `app/ai/cache.py`'s own
docstring states "the graph is model-derived," and it replays committed `watsonx` output rather
than running the rule-based matcher. Fixed to "except `watsonx` and `cached`," with the reasoning
spelled out rather than just the exception list.

**DEC-15 claimed a stronger invariant than the code delivers.** "Unaffected by this provider or
any other" and "byte-identical under every provider" is true of `openrouter` against
`deterministic` — the comparison DEC-15 is actually making — but not of `watsonx` or `cached`,
which do change extraction; the README's own comparison table records 17 role disagreements over
313 artifacts. Narrowed to the claim the evidence supports.

**"Only the wording... can move" understated the mitigation plan's legitimate variance**, in
sections written specifically so a maintainer would not chase the difference as a bug. A plan can
also vary in task count (within the readiness-band `_task_count_band` permits — Maria is
`ASSISTED`, which allows 3 or 4, and the fixture has 4, so a 3-task generation re-indexes every
task diff below it), task type (a model choice, only enum-checked), and linked evidence (a filtered
subset, not a fixed list). `README.md` and `fixtures/README.md` both now say so.

**The "four checks" description of the validation gate was wrong in both directions.**
`find_probability_language` runs only inside `validate_simulation_summary`; `find_inability_language`
runs only over a candidate narrative's gaps — so, as written, the description implied a plan
claiming "80% chance" would be caught by a rule that never runs over plan text. It also omitted the
independence-overstatement check (`validation.py:334-343`, arguably the gate's strongest
responsible-AI property, since it is the one built to catch exactly the assisted-read-as-independent
failure this product exists to avoid) and every plan-specific structural check (task count, the
readiness-keyed band, task-type validity, per-task acceptance criteria, the opening citation, the
drill rule). Rewritten to describe which check runs over which narrative, rather than one list of
four applied uniformly.

**The timing section never mentioned `summarize_simulation`'s actual endpoint budget.**
`POST /simulations` is where the simulation narrative call happens, and AC-14's figure for that
endpoint is the 2-second "deterministic simulation" target, not the 12-second "AI plan/explanation"
one the section discussed — a 3.5-second default timeout can alone exceed it. Added, along with a
matching caveat to `fixtures/README.md`'s live-pass invitation: `verify_golden_path.py` applies an
800ms budget to every endpoint whose label does not contain `"simulations"`, so a live `openrouter`
run will print `AC-14 breaches` for `POST /mitigation-plans` and
`POST /recommendations/backup-candidates` by design, not as a regression.

**Two declined cleanup items were reconsidered and fixed.** `README.md`'s Checks block read "131
tests, ~3 seconds" against a suite now measuring 262 passed, ~2 seconds — corrected, since leaving
a known-false number in a file being edited specifically for accuracy does not fit "smallest
change." And the missing `BUILD_WITH_BOB.md` entry for `dfb8dae` (the runtime responsible-AI scan)
is backfilled above — the commit is two test files, fully inspectable, so the misattribution risk
originally cited did not hold up.

**Four minors.** `README.md` no longer credits one narrow test with covering blind spots the
module docstring documents more broadly (only two of the docstring's four are in that test's own
parametrize list) — both `README.md` and DEC-15 now cite "the module docstring together with the
test suite" and list all four blind spots, including the two-word-qualifier-on-an-attested-name
case that was previously dropped from both. `README.md`'s claim that "every non-default provider"
passes validation is corrected: `app/ingestion/pipeline.py` calls `validate_extraction`
unconditionally, for every provider including the default. `fixtures/README.md`'s "never with
`watsonx` or `openrouter` set" now also names `cached`.

**Files changed.** `README.md`, `docs/DECISIONS.md`, `fixtures/README.md`, `BUILD_WITH_BOB.md`
(the backfilled entry above and this one). No file under `backend/app/` or `frontend/` touched.

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest -q` → 262 passed. No seed or
fixture-refresh script run; no network call made; `backend/.env` never read.

**Open questions.** None outstanding from this review round. DEC-15 (OPEN-10) still needs Person
A's acknowledgement; that has not changed.

### 2026-08-21 — Whole-branch review fixes: the narrative gate becomes system-wide

Six items from the final whole-branch review of the OpenRouter narrative work, applied in one pass.
The verdict was merge with no critical findings; these are the items worth closing before it lands.

**The gate now covers every model-written narrative, not only this branch's.** `watsonx.py`'s
`summarize_simulation` is the one narrative that provider has a model write, and it returned the
sentence verbatim: `strip()`, `strip('"')`, return. That value is the response body of
`POST /simulations` and is also written into `result_json` (`app/simulation/service.py`), so an
ungated sentence outlived the request that produced it. The file is untouched by this branch and the
hole predates it, but the branch built the gate that closes it and the README now claims the gate
protects narrative output — so the claim had to become true rather than be softened.
`validate_simulation_summary` is applied exactly as `openrouter.py` applies it, with the
deterministic template on rejection. An empty reply is now a rejection by the gate rather than a
separate branch, since the gate already treats it as one.

**Two documentation claims about watsonx were inaccurate and are corrected.** `README.md` said its
"narratives stay deterministic on purpose" and cited a line range that excluded the model-written
one; it now says two of the three are deterministic, names those two methods instead of citing line
numbers that shift, and states that the third is model-written *and* gated. `docs/DECISIONS.md`
(DEC-15) said the fallback is "the exact deterministic text `watsonx.py` always returns", which was
never true of the simulation summary; it now points at the template in `app/ai/deterministic.py`
and distinguishes the two narratives watsonx returns deterministically from the one it falls back
to.

**A fifth blind spot is disclosed rather than patched.** The independence check in
`validate_candidate_narrative` — the check both `README.md` and DEC-15 call arguably the gate's
strongest responsible-AI property — pairs independence wording with an unproven capability only
where the strength *lexically contains that capability's name*. Verified with Incident Recovery
assisted-only: "has independently demonstrated Incident Recovery" is rejected, and "has
independently handled that recovery work end to end, unaided" is accepted. That second sentence is
the assisted-presented-as-demonstrated failure the product exists to prevent. Resolving an oblique
reference to a capability needs a lexicon the module does not have, and HARD RULE 2 of
`prompts/candidate_narrative_system.txt` already addresses it, so the fix is honesty rather than
heuristics: one paragraph in the `validate_candidate_narrative` docstring, a sentence next to the
claim in `README.md` and a fifth entry in its blind-spot list, a paragraph in DEC-15's "the gate's
limits" section, and `test_known_blind_spot_of_the_independence_check` pinning both wordings so it
is discoverable next to the four name-check ones rather than buried.

**The demo output no longer states the wrong extraction provenance.** `scripts/seed_demo.py`
printed `provider openrouter` while the graph had been built by string matching — the exact
misdescription `CacheBuildRefusedError` refuses to write to disk, printed instead. `provider.py`
gains `extraction_provenance()`, `OpenRouterProvider` gains an `extraction_provider_name` class
attribute naming the deterministic provider, and the script prints `extraction <name>`. The
attribute is optional: a provider that does its own extraction needs none, because its `name` is
already the honest answer.

**AC-10's 3-5 band has one definition again.** `MIN_TASKS`/`MAX_TASKS` in
`app/mitigation/service.py` and `MIN_PLAN_TASKS`/`MAX_PLAN_TASKS` in `app/ai/validation.py` were
independent literals, and changing one would make the gate reject every plan forever — silently,
because a rejection falls back to the template and looks like success. A comment was the fallback
option; an import was available and is stronger. `app/ai` must not depend on `app/mitigation`, and
`app/mitigation/service.py` already imports from `app.ai`, so the definition stays in the gate and
the service imports it under its existing local names. No call site changed.

**AC-14's timeout arithmetic is now true rather than nominal.** `httpx.Client(timeout=3.5)` sets
connect, read, write and pool to 3.5 seconds *each*, so a call that spends 3.4 connecting and 3.4
reading was inside every configured limit and outside the 3 x 3.5 = 10.5 the 12-second budget was
sized against. httpx has no total-request setting, so `_call_budget()` splits one budget across the
four phases, which run in sequence. Connect gets the second-largest share because a provider is
constructed per request and every call therefore pays a TLS handshake inside its own budget; read
gets the largest because that is where the model generates. The default stays 3.5 seconds and the
plan's 2x multiplier now multiplies a real ceiling.

**Requirements.** AC-10 (the task band), AC-14 (the timing budget), AC-09 via the unchanged
readiness bands, PRD section 22 and DOMAIN_MODEL.md section 10.2 (the narrative gate),
ARCHITECTURE.md section 22 (validate before persist — the reason I-1 mattered at all, since the
summary is persisted).

**Files changed.** `backend/app/ai/watsonx.py`, `backend/app/ai/openrouter.py`,
`backend/app/ai/provider.py`, `backend/app/ai/validation.py`, `backend/app/mitigation/service.py`,
`backend/scripts/seed_demo.py`, `backend/tests/test_watsonx_provider.py`,
`backend/tests/test_openrouter_provider.py`, `backend/tests/test_narrative_validation.py`,
`README.md`, `docs/DECISIONS.md`, `BUILD_WITH_BOB.md`. Nothing under `frontend/`.

**Validation.** `cd backend && PYTHONPATH=. .venv/bin/python -m pytest -q` → 269 passed, up from
262. Both behaviour changes were written test-first and confirmed non-vacuous: the poisoned-summary
test and the two timeout tests each failed against the unmodified source before the fix. The
poisoned summary is paired with a grounded one that must still be returned verbatim, so a validator
that rejected everything could not pass the pair. Frozen demo numbers re-read from
`backend/continuity.db` read-only, without reseeding: Payment Gateway 74/HIGH, Incident Recovery
72/HIGH, Identity's highest system 68; the 74 → 93 simulation and Maria HIGH / Jordan MEDIUM stay
pinned by `test_continuity_engine.py` and `test_golden_path.py`. `AI_PROVIDER` still defaults to
`deterministic`. No seed or fixture-refresh script run, no network call made, `backend/.env` never
read.

**Open questions.** Two carried forward, neither introduced here. The `POST /simulations` timing
conflict stands — AC-14 gives that endpoint 2 seconds as a deterministic simulation, and a single
narrative call at the 3.5-second default can exceed it on its own; making the per-call bound real
sharpens that number without resolving the conflict. And closing the lower-case and title-cased
name-check blind spots still needs the capability taxonomy passed into the validator the way
`validate_extraction` receives it. DEC-15 (OPEN-10) still awaits Person A's acknowledgement.
