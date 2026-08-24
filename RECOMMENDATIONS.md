# Recommendations and Open Concerns

Running list, maintained as the backend was built. Each item states what is true today, why it
matters, and what the fix would cost. Referenced from code comments by identifier, so a `R-05` in a
docstring points here.

Ordering is by **risk to the submission**, not by size. Nothing here blocks the frontend.

---

## Legend

| Field | Meaning |
|---|---|
| **Impact** | What it costs the product or the submission if left as is |
| **Effort** | Rough size for one developer |
| **Owner** | Who would do it |
| **Decision** | Whether it needs both developers (Category C) or not |

---

# Concerns — things that could hurt the submission

## R-01 — Model-backed extraction is built but blocked on the watsonx token quota

**Status 2026-08-17 — partially resolved, one external blocker.**

`app/ai/watsonx.py` implements the full `AIProvider` interface against IBM watsonx.ai
(`ibm/granite-4-h-small`). Credentials verified, chat endpoint working, versioned runtime prompt in
`app/ai/prompts/extraction_system.txt`, 16 tests covering parsing and the closed-world guards without
touching the network. `AI_PROVIDER=cached` replays committed model output so a model-derived graph can
seed offline with no credential.

**The blocker is the account plan, not the code.** Two limits surfaced:

| Limit | Effect | Handled by |
|---|---|---|
| 2 requests/second per instance | Eight parallel workers made the run *slower* — 429 fails the whole burst | Client-side pacing plus `Retry-After` handling |
| Capped token quota | Run stopped at 313 of 640 artifacts with HTTP 403 `token_quota_reached` | A distinct non-retryable error, and a resumable cache |

Extraction is now resumable: cached artifacts are skipped, so re-running after a quota reset continues
where it stopped. The cache sits at **49% coverage**, and `cached` refuses to run below full coverage
on purpose — a graph half model-derived and half string-matched would be neither.

### What the partial run already measured

`data/extraction/comparison_report.md`, over 313 artifacts:

- **291 / 313 artifacts identical** to the rule-based extractor
- 50 claims agreed, **0 found only by the model**, 5 found only by the rules
- **17 role disagreements, all in one direction:** 14 × `CONTRIBUTION → INDEPENDENT_EXECUTION`,
  3 × `CONTRIBUTION → KNOWLEDGE_CAPTURE`

That is a genuinely useful finding for the submission. The model reads narrative and concludes someone
acted *alone* where the rule saw only that they changed something — the judgement a string match cannot
make, and the one that matters most, because promoting a contribution to an independent execution is
what moves an engineer toward `PRACTICED` and therefore closes or opens a coverage gap.

The 5 claims found only by the rules are worth a look before trusting the model further: the rule-based
matcher is aggressive on alias hits, so some may be rule false-positives rather than model misses.

### What is needed to finish

**One of:** wait for the quota window to reset, raise the watsonx plan limit, or supply a key on an
account with headroom. Then:

```bash
python -m scripts.extract_with_provider --provider watsonx --compare   # resumes from 49%
AI_PROVIDER=cached python -m scripts.seed_demo && python -m scripts.run_evaluation
```

The evaluation then answers the question that actually matters — **does model extraction reconstruct
the hidden ground truth better than the rules?** — and whichever wins becomes the default, with the
measurement quotable either way. Roughly 30 minutes of runtime plus a reseed.

**Risk to note if the model does win:** LLM extraction may shift readiness for some pairs, which can
move the frozen fixture numbers. That is a contract change to coordinate, not a surprise to absorb
quietly. The evaluation harness will show exactly which pairs moved.

**Impact:** high (it is the headline innovation claim) · **Effort:** 30 minutes once quota exists ·
**Owner:** Person A · **Decision:** C if the numbers move

---

## R-01a — Until then, the README wording carries the honesty

The README now states which provider ships, what the model measurably adds, and that the served graph
is rule-derived. Keep it that way. A judge can check the claim in ninety seconds, and "we built the
model path, measured it against the rules, and ran out of quota at 49%" is a stronger story than an
overstatement — it is a real engineering result with a real constraint.

---

## R-02 — The evaluation measures self-consistency, not accuracy

**Status today.** All seven checks pass at 100% (`data/generated/evaluation_report.md`): readiness
reconstruction 56/56, exposure 25/25, critical gaps 2/2 with no false positives, simulation 25/25,
candidates 2/2, evidence grounding 55/55.

**Why it matters.** Those numbers are real but narrow. The generator emits evidence patterns
*chosen to be classifiable by the readiness rules*, so what the evaluation demonstrates is that the
whole pipeline is self-consistent end to end — ingestion, extraction, aggregation, readiness,
exposure, risk, simulation — and that no stage silently drops or invents information. It is not
evidence that the readiness heuristics match real human expertise, and 100% is a number that
invites exactly that misreading.

**Recommendation.** The caveat is already printed inside the report and repeated in
`app/evaluation/report.py` and `data/ground_truth/README.md`. Keep it in the README too, and quote
the checks by name rather than as a headline percentage. Consider adding deliberately *misleading*
artifacts — a reviewer who comments extensively without ever executing, an engineer named in an
incident they did not resolve — so the evaluation can show the rules declining to be fooled. That
is a much stronger claim than 100%.

**Impact:** medium (honesty, and a stronger story available) · **Effort:** 2-3 hours ·
**Owner:** Person A · **Decision:** A

---

## R-03 — Optional bearer authentication added — **RESOLVED 2026-08-17**

`API_TOKEN` is unset by default, leaving every endpoint open exactly as before, so the frontend and
local development are unaffected and nobody has to coordinate a secret to run the demo. Set it and
`/api/v1` requires `Authorization: Bearer <token>`; `/health` is never gated so a container can still
report ready. Comparison is constant-time.

Deliberately not attempted: SSO, roles, sessions, or token rotation. A shared token is honest about
being a demo control rather than pretending to be authorisation. Enterprise IAM stays descoped per
`ARCHITECTURE.md` section 50, and the README now says so explicitly instead of leaving it unstated.
Logged as DEC-13.

**Still true and worth stating in the submission:** identity is not modelled. `approved_by` remains a
caller-supplied string, so the token controls *access*, not *attribution*. Real per-user identity is
a post-MVP item.

---

## R-04 — `drift_status` is seeded, not computed

**Status today.** Every platform and system returns a `drift_status`, read from
`data/org/novapay.json`. Nothing computes it.

**Why it matters.** It is honest for the MVP — `PRD.md` section 10.3 lists Knowledge Drift as
"seeded indicators" and defers continuous monitoring — but it is a field the dashboard displays as
though it were derived. **Person B should know it is static** so nobody builds a drift history view
or a trend chart on top of it.

**Recommendation.** Leave it seeded for the MVP and say so on screen if the design allows (a
tooltip is enough). Computing it properly needs assessment snapshots over time, which is Phase 3 on
the post-MVP roadmap.

**Impact:** low, provided nobody builds on it · **Effort:** 1 day to do properly ·
**Owner:** Person A · **Decision:** B

---

## R-05 — Freshness ignores component change

**Status today.** `app/evidence/freshness.py` implements the age half of the PRD rule (FRESH up to
18 months, AGING to 36, STALE beyond). The other half — "or substantial component change since the
artifact date" — is **not implemented**.

**Why it matters.** It is the more interesting half. Evidence about code that has since been
rewritten is worth less regardless of age, and Knowledge Drift after an architecture migration
(PRD section 4.3) is one of the named failure modes the product claims to address.

**Why it was left out.** Nothing in the schema expresses component change. There is no field, no
table, and no metric, and deriving one from commit counts would produce a number nobody could
defend in a "Why?" drawer. An unexplainable input to an explainable engine is worse than a missing
one.

**Recommendation.** Either add a seeded `change_ratio` per component with an honest label, or leave
it out and note the limitation. Do not infer it.

**Impact:** medium (a named product capability is partly unimplemented) · **Effort:** half a day
with seeded data · **Owner:** Person A · **Decision:** C — it changes rule intent

---

## R-06 — `runbook_state` is seeded per capability, not derived

**Status today.** Documentation modifiers (`RUNBOOK_MISSING +5`, `INCOMPLETE +3`, `CURRENT -3`) are
implemented and unit-tested, but the state itself comes from `data/org/novapay.json`. Only
`cap_session_recovery` is seeded `CURRENT`; every Payment Gateway capability is `NOT_ASSESSED` and
contributes nothing.

**Why it matters.** `KNOWLEDGE_CAPTURE` evidence proves a document was *written*, not that it
covers the failure path. Deriving "complete" from "exists" would be a fabrication, and it would
also silently move the hero numbers.

**Consequence worth knowing.** Because Payment Gateway is seeded `NOT_ASSESSED`, its risk indices
are driven purely by coverage evidence. That is why 72 / 74 / 93 are reproducible from coverage
alone, which makes them easy to explain on stage.

**Recommendation.** Leave as is. If a runbook-completeness signal is wanted later, it needs a real
input — a checklist, a template conformance check — not an inference.

**Impact:** low · **Effort:** n/a · **Owner:** Person A · **Decision:** A

---

## R-07 — Real public GitHub evidence ingested — **RESOLVED 2026-08-17**

`scripts/fetch_public_github.py` fetches merged pull requests and reviews through the `gh` CLI,
normalises them, and commits them to `data/public/`. The seed ingests them alongside the synthetic
corpus through the same pipeline: **640 artifacts total — 520 synthetic private records, 120 real
public ones.** Seeding itself stays offline, so the demo cannot fail on a rate limit.

Identities are pseudonymised onto the synthetic organisation and real logins are never written to
disk, including `@mentions` scrubbed from pull request bodies. That is a substantive requirement
rather than a formality: this product infers capability readiness about named people, and doing that
to real engineers who never consented would breach its own responsible-AI boundary. Artifacts stay
traceable through their real URLs. Bots are excluded. Logged as DEC-14.

### The finding, which is more useful than the feature

**Exactly one of the 120 real artifacts produced capability evidence.**

That is not a defect. A public SDK repository's vocabulary is library maintenance — support, error
handling, tests, packaging — while the capabilities this product assesses are demonstrated in
*private operational* records: incidents, runbooks, on-call history. It is direct evidence for why
the hybrid data strategy in PRD section 14.1 is necessary rather than merely convenient, and it is a
concrete measurement of the ceiling described in R-01.

Two things follow. In the submission, say what real public data actually contributes — realistic,
messy text that extraction must mostly *decline* — rather than implying it drives the assessments.
And resist raising the match rate by loosening the matcher: a high match rate here would mean the
matcher had become credulous, not that the corpus had improved. A test asserts the rate stays low for
that reason.

---

## R-08 — One PRD index modifier is deliberately not implemented

**Status today.** `HIGH_OPERATIONAL_DEPENDENCY` (+3, "majority of recent P1 recovery evidence
concentrated in one engineer") from `PRD.md` section 17.2 is absent from
`app/continuity/reason_codes.py`.

**Why.** It is true of nearly every sole-expert capability in the seed, so it would add a constant
to exactly the capabilities `SOLE_ADEQUATE_ENGINEER` already penalises — double-counting one signal
under two names, and making the index harder to explain rather than more accurate.

**Recommendation.** Keep it out, or redefine it to capture something the sole-expert modifier does
not (for instance, concentration across a *component* rather than a capability). Either way it
should be removed from the PRD table or annotated as not implemented, so the specification and the
code agree.

**Impact:** low · **Effort:** 30 minutes to amend the PRD · **Owner:** both · **Decision:** C

---

## R-09 — Challenge / correct / learn workflow built — **RESOLVED 2026-08-17**

`POST /api/v1/capabilities/{id}/challenge` closes `FR-020`, `AC-11`, user scenario S5, the
`AssessmentChallenge` domain entity, and `PRD.md` section 21. It is an eleventh endpoint on a
ten-endpoint frozen contract, so it is logged as DEC-10 and **needs Person B's acknowledgement**.

Three actions: link an artifact extraction missed, attest to something no artifact captured, or
correct a mis-mapped record. All three change *evidence*; readiness, exposure, and risk are then
recomputed through the same `app/services/recompute.py` the seed uses. `ChallengeRequest` has no
field for a readiness level, exposure, confidence, or a risk index, and a test asserts their
absence — which is how "scores change because evidence changes" became a property of the design
rather than a sentence in a document.

Attestation is capped at MODERATE strength, so no quantity of assertions can manufacture a
`VALIDATED` expert. That was the abuse case that would have made the evidence model decorative.

**Verified live**, and it makes a good demo beat:

```
attest Jordan, INDEPENDENT_EXECUTION
  Jordan             EXPOSED  → PRACTICED
  Incident Recovery  DEGRADED → COVERED,  72/HIGH → 15/LOW
  system             74 HIGH  → 74 HIGH,  degraded 2 → 1, covered 3 → 4
  rules  [CRITICAL_CAPABILITY, SINGLE_VALIDATED_ENGINEER, NO_PRACTICED_OR_VALIDATED_BACKUP]
      →  [CRITICAL_CAPABILITY, ADEQUATE_BACKUP_PRESENT]
```

Worth noticing that the system index stays at 74: Certificate Management is now the binding
constraint. The engine is reasoning about which capability drives the system rather than moving a
single number — a detail worth pointing at if the challenge beat makes the demo cut.

**Frontend note:** additive. Nothing that previously worked changes, and the provenance drawer can
gain a "Challenge Assessment" action whenever Person B is ready.

---

## R-10 — Performance measured against AC-14 — **RESOLVED 2026-08-17**

`scripts/verify_golden_path.py` now records per-endpoint latency and flags anything over budget.
Measured on the seeded dataset:

| Endpoint group | Measured | AC-14 budget |
|---|---|---|
| Reads (six GET endpoints) | 2.5 - 26 ms | < 800 ms local p95 |
| `POST /simulations` | 6.1 ms | < 2 s |
| Candidate comparison, plan generation, approval | 3 - 6 ms | < 12 s (AI operations) |

Two orders of magnitude of headroom, because assessments are precomputed at seed time and reads are
indexed lookups. The 26 ms on the first call is import and connection warm-up, not query cost.

---

## R-11 — Conflicting evidence now exercised by the seed — **RESOLVED 2026-08-17**

`INC-259` was added to the corpus: a Policy Rollback attempt that was itself rolled back and handed
off unresolved. It produces a record the extractor marks conflicting, which means:

- the record is retained and shown separately in `conflicting_evidence`, never in `evidence`
- `cap_policy_rollback` reports `CONFLICTING_EVIDENCE` and `LOW_EVIDENCE_CONFIDENCE`
- confidence drops to `LOW` while exposure stays `DEGRADED` at index 54

That last line is the point: **`Risk: MODERATE` with `Confidence: LOW` is now reachable in the
seeded data**, which is the clearest demonstration available that the two are orthogonal (PRD
section 5.6). Daniel keeps `PRACTICED` because his two qualifying records are untouched — the
conflict changes how much the assessment can be trusted, not what the other evidence shows.

Placed on Authorization deliberately so it exercises the path without moving any number the frozen
fixtures pin. Verified: Payment Gateway still 74 / HIGH with HIGH confidence, Identity Platform
still reports a highest system index of 68.

---

# Improvements — worth doing if time allows

## R-12 — Index modifiers exposed on the wire — **RESOLVED 2026-08-17**

`CapabilityDetail` now carries an optional `index_modifiers` array. Incident Recovery returns:

```json
"index_modifiers": [
  { "code": "SOLE_ADEQUATE_ENGINEER", "delta": 1 },
  { "code": "BEST_ALTERNATIVE_ASSISTED", "delta": 1 }
]
```

With the HIGH class anchor of 70, that is the entire derivation of 72. The index is now inspectable
rather than merely reproducible, which is the strongest available answer to "the risk score appears
arbitrary" (PRD section 30, listed there as a high-severity risk). Additive and optional, so it costs
the frontend nothing until rendered. Logged as DEC-11.

---

## R-13 — `missing_evidence` widened to everyone below PRACTICED — **RESOLVED 2026-08-17**

Previously emitted only below `ASSISTED`, which meant Jordan alone. Maria is `ASSISTED` and is the
leading backup candidate, so the drawer was least informative about the person the decision is
actually about. It now reads:

```
Jordan Lee   No qualifying independent incident recovery evidence found.
Maria Gomez  No qualifying independent incident recovery evidence found.
```

Descriptive, never evaluative — absence of evidence, not inability. Logged as DEC-12.

---

## R-14 — Candidate `evidence_confidence` uses a narrow definition

It reports the confidence of the candidate's coverage of the *target* capability only. For Maria
that is `MEDIUM` (two evidence records), even though the overlap judgement also leans on her
`HIGH`-confidence Provider Failover and Monitoring coverage.

Reporting confidence in the *overlap claim* — the strongest coverage the score actually used — would
be more informative. It is a judgement call worth making explicitly rather than by accident.

**Effort:** 1 hour · **Decision:** C, it changes a displayed meaning.

---

## R-15 — No database migrations

Alembic is listed as optional in `ARCHITECTURE.md` section 5.2 and was not added. `scripts/seed_demo`
drops and recreates every table, which is correct for a demo and fine while the dataset is
generated. It does mean any schema change requires a reseed and discards simulations and plans.

Acceptable for the MVP. Worth a README line so nobody is surprised.

**Effort:** n/a to leave; half a day to add Alembic.

---

## R-16 — `datetime.utcnow()` replaced — **RESOLVED 2026-08-17**

`app/simulation/service.py` and `app/mitigation/service.py` now use `datetime.now(timezone.utc)`.
Timestamps are timezone-aware, so `approved_at` serialises with an explicit offset rather than a
naive local-looking value — which also makes the API contract's ISO-8601 requirement true rather
than approximately true.

---

## R-17 — Platform-scope simulation is unimplemented

`SimulationScopeType` keeps `PLATFORM` because the contract froze it (decision CI-22), but the
service rejects it with a `422` naming the supported scopes. That is better than silently treating a
platform id as a system id, and multi-system rollup has no demo beat. Leave it; the error message is
the documentation.

---

## R-18 — There is no `GET /simulations/{id}`

Simulation results are persisted in full (`simulations.result_json`), but the frozen contract has
exactly ten endpoints and `PRD.md` section 24's outline predates it. If Person B wants a shareable
simulation URL, the storage is already there and it is a one-endpoint Category C decision.

---

# Process items

## R-19 — Housekeeping found while building

| Item | Status |
|---|---|
| `docs/ContinuityAI_PRD_v1.0.md` — untracked stale pre-audit PRD | User removed it |
| `frontend/.env.local.example` referenced by the README but absent, and `frontend/.gitignore` `.env*` would have excluded it | Created, with a `!` negation added |
| Working on branch `yaza_work`, which `TEAM_WORKFLOW_PERSON_A_B.md` section 7 forbids | Still outstanding — move to short-lived `feature/*` branches |
| `README.md` claimed Python 3.9 will not work and 3.11 is required | Corrected; 3.10 is verified working |
| `data/generated/` (evaluation output) | Gitignored |

## R-20 — Ten decisions need Person B's acknowledgement

All are logged in `docs/DECISIONS.md` as DEC-05 through DEC-14 with reasoning. None was made
silently, but seven are contract-visible and one adds an endpoint, so they need a joint read rather
than a merge:

| Decision | What changed | Blast radius for the frontend |
|---|---|---|
| DEC-05 | Reason-code spelling follows `API_CONTRACT.md` over `ARCHITECTURE.md` section 29 | None — display copy was already going to use this spelling |
| DEC-06 | AI extraction uses the per-claim shape from `ARCHITECTURE.md` section 21 | None — internal only |
| DEC-07 | Risk class scales with operational criticality | None — exposures, counts, and the hero scenario unchanged |
| DEC-08 | `SUPPORTED_BY` edges originate at the engineer, since no `COVERAGE` node type exists | Read `capability_id` from edge metadata |
| DEC-09 | Mitigation task ids scoped to their plan | None |
| **DEC-10** | **An eleventh endpoint for the challenge workflow** | **Additive. Adopt when the drawer is ready** |
| DEC-11 | `index_modifiers` on capability detail | Additive optional field |
| DEC-12 | `missing_evidence` widened to below PRACTICED | One more entry in an existing array |
| DEC-13 | Optional bearer auth, off by default | None while `API_TOKEN` is unset |
| DEC-14 | Real public GitHub ingested, identities pseudonymised | One extra graph edge |
| — | Twelve fixtures regenerated across the two builds | Build against the current fixtures |

**Recommendation.** Walk the table at the next sync — fifteen minutes, and DEC-10 is the only one
that genuinely needs a yes or no. It is the difference between "we decided" and "Person A changed
things".

---

## R-21 — Identity is still not modelled

`API_TOKEN` (DEC-13) controls *access*. It does not establish *attribution*: `approved_by` on a plan
approval and `submitted_by` on a challenge are both caller-supplied strings, so the audit trail
records what the caller claimed rather than who they were.

For a single-user demo this is fine and is the documented MVP posture. It is worth one sentence in
the submission rather than left implicit, because "the manager approves" and "the manager attested
this" are both responsible-AI claims that a reader might reasonably assume are authenticated.

**Effort:** real identity is a post-MVP item. Saying so costs a sentence.

---

## R-22 — Attestation evidence is dated the day it was made

A manager attesting to something that happened eighteen months ago produces evidence dated today, so
it reads as `FRESH`. That is convenient for the demo and slightly wrong in principle: the freshness of
a claim should follow the work, not the paperwork.

Adding an optional `occurred_on` to the challenge request would fix it, and would let a manager
attest to genuinely old work without it appearing current. Small, and it makes the freshness model
coherent across both evidence sources.

**Effort:** 30 minutes · **Decision:** C, it touches the challenge contract.

---

## R-23 — Live credentials were sitting in an untracked, un-ignored file

**Found 2026-08-17. Contained, but it needs one decision from you.**

`keys.md` at the repository root held live watsonx, Tavily, and Gemini credentials in plaintext. It
was **untracked and in no commit**, so nothing reached GitHub — but it was not gitignored either, so a
single `git add .` would have published all three. That is roughly one keystroke away from a real
incident, and secrets in git history cannot be removed by deleting the file afterwards; the only fix
at that point is rotation.

**Done:**

- `.gitignore` now excludes `keys.md`, `keys.txt`, `secrets.md`, `*credentials*.json`, `*.pem`, `*.key`
- The watsonx values were copied into `backend/.env`, which was already ignored, and which is where
  the application reads them from
- `backend/.env.example` documents every variable with no real values

**Two things for you:**

1. **Delete `keys.md`,** or accept that credentials now exist in two local places. I left it alone
   because it is your file — but one copy is better than two.
2. **Consider rotating the three keys.** They were pasted into a chat transcript, so treat them as
   disclosed even though they never reached the repository. Rotation is cheap; assuming disclosure did
   not matter is the expensive assumption. The Tavily and Gemini keys are not used by this project at
   all, so those two are pure exposure with no upside.

**Worth noting for the submission:** `docs/DOMAIN_MODEL.md` and the PRD both commit to strong data
boundaries, and a judge who finds credentials in the repository will weigh that against the
responsible-data claims regardless of what the code does. Keeping this clean is part of the story.

---

# Items from Person B's gap register — 2026-08-24

## R-24 — `single_expert_dependency_count` had no transport — **RESOLVED 2026-08-24**

`docs/BACKEND_GAPS.md` GAP-01, and the only blocking item in Person B's three-way review of the PRD,
the contract, and the implementation. The corrected dashboard puts a single-expert-dependency count on
each platform card, and no field carried it anywhere — not in the contract, not in `PlatformSummary`,
not in a fixture, not in `frontend/types/api.ts`. It had never been added.

Added as a required field on `PlatformSummary` and logged as DEC-17. It counts capabilities under the
platform whose adequate coverage is exactly one engineer, aggregated in SQL from the already-persisted
`capability_assessments.adequate_engineer_count`, so no rule or column changed. Seeded values are
Payments 4 and Identity 2; the brief's 3 and 1 were stale-brief figures.

**The part worth remembering** is why the frontend could not have derived it. Summing
`degraded_capability_count` looks equivalent and is not: under DEC-07 a lower-criticality capability
with *zero* adequate engineers is `DEGRADED` rather than a critical gap, so the degraded count spans
both the one-expert and no-expert cases. There is now a test that asserts the two numbers differ on
the seeded data, purely so nobody later concludes the shortcut was fine.

---

## R-25 — A configured timeout that the transport does not honour is not a budget — **RESOLVED 2026-08-24**

`OPEN-11` recorded `POST /recommendations/backup-candidates` at 16.91s against AC-14's 12 seconds under
`AI_PROVIDER=openrouter`. Two causes, and the first is the interesting one.

`openrouter_timeout_seconds` was applied through `httpx.Timeout`, and httpx has no total-request
setting — its `read` timeout bounds the gap *between* socket reads. The gateway keeps the socket warm
while the model generates, so the clock kept resetting and a call nominally budgeted at 3.5s ran to
about 6. The code had already flagged this in a docstring as a "pathological slow trickle" that could
defeat the budget. It is not pathological; it is the normal case. **Every latency number that budget
implied was fiction, and nothing failed to make that visible** — the calls simply took as long as they
took.

Fixed in `app/ai/budget.py`: the three independent candidate narratives now run concurrently under one
real wall-clock deadline, and anything that misses it is answered from the deterministic template.
Logged as DEC-18. Also fixed the `httpx.Client` being rebuilt per request, which was paying a TLS
handshake inside the very budget it was spending.

The second finding was that the simulation half of OPEN-11 was **not a breach at all**: AC-14's
2-second clause governs *deterministic* simulation, and under `openrouter` the summary is model-written,
which makes it a 12-second AI explanation operation. 2.85s was always inside it.

**Residual concern, tracked as OPEN-12.** The fix is verified against a stub provider that sleeps, not
against the live gateway. The mechanism is proven — the endpoint returns on the deadline and falls back
to templates — but the *numbers* under a real key are now predicted rather than measured. Re-measure
before quoting them.

**Effort to close OPEN-12:** one run with a live key, about ten minutes.

---

## R-26 — The fixture check was reporting success over files it never read — **RESOLVED 2026-08-24**

Raised as GAP-03, which asked only for a challenge fixture. The underlying problem was worse.
`scripts/refresh_fixtures.py` captured ten of the twelve files in `fixtures/`, so
`refresh_fixtures --check` printed "all fixtures match live engine output" while
`identity-systems.json` and `challenge-attest-jordan.json` were never compared to anything.

**An uncaptured fixture is worse than a missing one**, because the mechanism that exists to catch drift
actively reports success over it. Both fixtures happened to be accurate — the only difference
regeneration produced was a live timestamp that needed pinning — so this had cost nothing yet. It would
have, silently, on the first divergence.

Both are captured now, the challenge last because it is the only golden-path call that mutates an
assessment, with a reseed afterwards. `CAPTURED_FIXTURES` is declared, verified against what the run
actually captured, and asserted against the directory by a test, so the next fixture added on either
side fails a test instead of drifting.

**Generalisable lesson worth carrying into the submission:** every check in this repository should be
asked what it would *fail* to notice. This one had a blind spot exactly where it mattered, and it read
as green.

---

## R-27 — A clean clone cannot run `npm run typecheck` before a build

Minor, but it touches AC-15 (fresh clone plus documented setup reproduces the demo), so it is worth
writing down rather than each of us rediscovering it.

Two friction points on a fresh frontend setup:

1. **`npm install` can fail on a root-owned npm cache** with `errno -13`, unrelated to this project.
   The fix that needs no `sudo` is `npm install --cache /tmp/continuityai-npm-cache`, which sidesteps
   the bad cache entirely. The `sudo chown -R 501:20 ~/.npm` that npm suggests also works but asks for
   a password.
2. **`npm run typecheck` fails on a clean clone** with `app/layout.tsx: TS2304 Cannot find name
   'LayoutProps'`. Not a real error: `LayoutProps` is a global that Next 16 generates into
   `.next/types` during a build, so `tsc --noEmit` has nothing to resolve until `npm run build` has run
   once. `npm run build` passes, and its own TypeScript pass is clean.

**Recommendation:** one line in the README setup section — run `npm run build` once before
`npm run typecheck` — and, if it seems worth it, a `prebuild`-style step so the ordering is not
folklore.

**Effort:** 10 minutes · **Owner:** Person B, since it is the frontend setup path.

---

# The AI layer, finished and measured — 2026-08-24

## R-01 — **RESOLVED 2026-08-24, and the answer was not the expected one**

R-01 was the top item on this list for the whole build: "model-backed extraction is built but blocked".
It is no longer blocked, and the resolution is a measurement rather than a delivery.

The full corpus was extracted by `anthropic/claude-sonnet-5` and evaluated against the hidden ground
truth alongside the rule-based extractor. **The rules won**: reconstruction 56/56 against 54/56,
simulation 25/25 against 15/25, candidates 2/2 against 1/2. The model made two readiness errors, both on
the hero capability and both too generous, which flipped Incident Recovery from `DEGRADED` to `COVERED`
and broke the demo's opening claim.

So the honest resolution of R-01 is: **the model-backed path is complete, exercised over the whole corpus,
and deliberately not used for extraction, because it is worse.** It is used for the narratives, the
taxonomy proposals and the criticality suggestions.

That is a better outcome than the one this item was written expecting. R-01 was framed as a submission
risk — "a judge can check the claim in ninety seconds". The claim we can now make is stronger than the one
we were worried about not being able to make: not "we use AI here" but "we tested whether AI belongs here,
and here is the run that says where it does and does not".

**Effort remaining:** none. The follow-up is OPEN-14, the hybrid.

---

## R-28 — Over-promotion is one-directional, which makes it fixable

The most useful detail in the losing run is that the model did not fail randomly. Every error was in the
same direction: it read review comments and assisted work as independent execution, never the reverse. It
was generous about people, consistently.

That is a tractable failure. A hybrid that takes the model's recall — **13 claims it found and the rules
missed** — while requiring corroboration before any promotion above `ASSISTED` would keep the extra reach
and discard the specific mistake. One independent-execution claim from one artifact stays `ASSISTED` until
a second artifact agrees.

Worth doing because the ceiling on rule-based extraction is real and documented (R-01's original framing,
and the 1-in-120 public-PR match rate). The rules are more accurate here, not more capable.

**Effort:** half a day, plus a re-run of the evaluation to confirm it beats both. **Decision:** B — it
changes extraction quality, not the contract. **Tracked as** OPEN-14.

---

## R-29 — A continuity tool must be biased toward alarm, and we should say so

Not a defect. A design principle the measurement surfaced, which is currently implicit in the code and
ought to be explicit in the submission.

Both model experiments erred the same way. Extraction over-promoted readiness; criticality suggestions came
back higher than the humans in three of five cases. In one case that is bad and in the other it is
harmless, and the difference is instructive:

- **Over-stating readiness is dangerous.** It says a capability is covered when it is not, and nobody
  investigates a problem the tool denies. This is the failure that broke the hero scenario.
- **Over-stating criticality is survivable.** It draws attention to a system that may not need it, and a
  human corrects it. FR-010 already makes that correction authoritative.

So the asymmetry is not "the model is unreliable" but "errors that reassure are worse than errors that
alarm". Everything in the evidence model already leans this way — `STALE` evidence does not count toward
adequate coverage, attestations cap at `MODERATE`, `INSUFFICIENT_EVIDENCE` is a valid output rather than a
guess. It is a coherent stance and it is never stated in one place.

**Recommendation:** one paragraph in the README's responsible-AI section. It reframes several existing
decisions as one principle, and it is a good answer to "what happens when your model is wrong?" — we know
which direction it is wrong in, and we chose the direction that fails safely.

**Effort:** 20 minutes · **Owner:** joint, since it touches the submission narrative.

---

## R-30 — `AI_PROVIDER=chain` must not be the day-to-day setting

Operational trap worth writing down, because the natural instinct is to set the most capable provider and
leave it.

Seeding makes one model call per artifact. Under `chain` that is 640 live calls per seed — and the test
suite seeds, so a single `pytest` run would make 640 calls. Slow, and not free.

The right runtime once a cache exists is `AI_PROVIDER=cached` with
`EXTRACTION_CACHE_FILE=chain_cache.json`: extraction replayed instantly from the committed cache, with
live model prose over the top. `deterministic` stays the default so a clean clone works with no key.

Documented in `backend/.env.example`. Recorded here because a config comment is easy to miss and the
symptom — a slow, expensive test run — would take a while to attribute.

**Effort:** none, already documented · **Owner:** whoever configures a machine.
