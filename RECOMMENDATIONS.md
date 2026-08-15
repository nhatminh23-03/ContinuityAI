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

## R-01 — The shipped "AI" layer is rule-based extraction, not a language model

**Status today.** `app/ai/deterministic.py` implements the full `AIProvider` interface, but it
resolves capabilities by matching capability names and aliases in artifact text, scoped to the
artifact's system, and maps `(source_type, participant_role)` onto an evidence role. It finds what
the text *names* and nothing more. It cannot read "restarted the workers and traffic recovered" and
infer incident recovery without the phrase being present.

**Why it matters.** Two reasons, and the second is the sharper one:

1. Judging criteria include Technical Execution and Innovation. "AI-generated evidence-backed
   knowledge graph" is the stated primary innovation (PRD section 1). A keyword matcher is a
   defensible engineering choice, but it is not what the phrase implies.
2. **The README and the demo script must not overstate it.** Saying "AI interprets engineering
   artifacts" while shipping string matching is the kind of claim a judge can check in ninety
   seconds. That is a credibility risk far larger than the technical gap.

**What is already right.** The seam is real, not cosmetic. Extraction output is validated against a
closed taxonomy (`app/ai/validation.py`), claims against non-participants are rejected, and every
downstream conclusion — readiness, exposure, risk, simulation, candidates — is deterministic and
unchanged by which provider runs. A model can be dropped in without touching a single conclusion
path, and `app/ai/prompts/extraction.md` already specifies what it must satisfy.

**Recommendation.** Implement one model-backed provider behind the same interface, run it over the
520-artifact corpus once, cache the extracted evidence into the seed, and keep the deterministic
provider as the offline fallback. `ARCHITECTURE.md` sections 85-86 already sanction precomputing
extraction so the live demo cannot fail on provider latency. If time runs out instead, say plainly
in the README that extraction is currently rule-based with a model-ready interface — that reads as
engineering judgement, whereas an overstated claim reads as something else.

**Impact:** high (judging + credibility) · **Effort:** ~half a day · **Owner:** Person A ·
**Decision:** B — tell Person B before merging

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

## R-03 — The API has no authentication at all

**Status today.** Every endpoint is open. CORS allows `http://localhost:3000`. There is no
identity: `approved_by` is a string the caller supplies, so anyone can approve a plan as anyone.

**Why it matters.** `ARCHITECTURE.md` section 50 explicitly descopes enterprise IAM for the MVP,
and that is the right call for a hackathon. But the product handles per-person capability
assessments — precisely the data that should not be world-readable — and "the manager approves"
is a core responsible-AI claim that currently rests on an unauthenticated string field.

**Recommendation.** Do not build SSO or RBAC. Do add two cheap things before any deployment beyond
localhost: a single shared demo token checked by a FastAPI dependency, and a note in the README
stating that authentication is deliberately out of MVP scope. If it stays localhost-only for the
demo, the note alone is enough.

**Impact:** high if deployed, low if localhost-only · **Effort:** 1 hour · **Owner:** Person A ·
**Decision:** C — it touches the responsible-AI story

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

## R-07 — No real public GitHub data is ingested

**Status today.** `app/ingestion/adapters.py` provides `load_normalised_github_export`, which reads
a public GitHub export already flattened to the internal artifact shape. Nothing calls it; the
seeded corpus is entirely synthetic.

**Why it matters.** `PRD.md` section 14.1 and the scope-freeze checklist both commit to "real
public GitHub + synthetic private enterprise data". Shipping only synthetic data narrows the
"realistic activity patterns and source ingestion credibility" claim.

**Recommendation.** Cheap version: export pull requests and reviews from one public repository,
normalise them offline into `data/public/`, map them onto one seeded system, and ingest through the
existing adapter. No live API call, so the demo cannot fail on a rate limit. If that is cut,
amend the PRD rather than leaving a commitment unmet — this is a Category C scope change.

**Impact:** medium (a frozen scope commitment) · **Effort:** 2-3 hours · **Owner:** Person A ·
**Decision:** C

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

## R-09 — The challenge / correct workflow is still unbuilt

**Status today.** `FR-020`, `AC-11`, and `PRD.md` section 21 remain in the specifications.
`OPEN-01` in `DECISIONS.md` defers the costing to "the Phase 7 checkpoint". Nothing is implemented,
and the provenance drawer deliberately has no "Challenge Assessment" action.

**Why it matters.** Two things. It is a named acceptance criterion, so leaving it silently unbuilt
means AC-11 fails. And the Phase 7 checkpoint it is deferred to arrives after the deadline at the
current pace, so the deferral is decaying into an omission by default.

**Cost, now that the engine exists.** Much lower than when it was deferred. Recording a
`MANAGER_ATTESTATION` evidence record and recomputing one capability is roughly: one endpoint, one
evidence row with `source_type=MANAGER_ATTESTATION`, and a call to the existing
`assess()` + `aggregate_system()` path. The recompute machinery is already written and already used
by the seed. Estimate 2-3 hours including a test.

**Recommendation.** Decide today rather than at a checkpoint. Either build the minimal version — it
is now cheap and it closes AC-11, FR-020, a user scenario, and a domain entity in one go — or
formally cut it and mark those requirements as descoped. The one thing not to do is leave it open.

**Impact:** high (a failing acceptance criterion) · **Effort:** 2-3 hours · **Owner:** Person A ·
**Decision:** C

---

## R-10 — Performance has not been measured against AC-14

**Status today.** Reads are served from precomputed assessment rows and the full test suite runs in
under two seconds, so the targets are almost certainly met. But "almost certainly" is not a
measurement, and AC-14 names specific numbers: reads under 800 ms local p95, deterministic
simulation under 2 s.

**Recommendation.** Add a small timing check to `scripts/verify_golden_path.py` that prints
per-endpoint latency. Ten lines, and it turns an assumption into a number that can be quoted.

**Impact:** low · **Effort:** 30 minutes · **Owner:** Person A · **Decision:** A

---

## R-11 — Conflicting evidence is implemented but never exercised by the seed

**Status today.** Conflict detection works (`_CONFLICT_MARKERS` in the provider, `is_conflicting` on
evidence, confidence dropping to LOW, `conflicting_evidence` in the response). No seeded artifact
triggers it, so the array is always empty and the UI path is untested against real data.

**Recommendation.** Add one incident whose recovery was later reverted. It exercises the
`CONFLICTING_EVIDENCE` reason code, gives Person B something to render, and demonstrates the
uncertainty story better than an empty array does.

**Impact:** low-medium (an untested UI path) · **Effort:** 1 hour · **Owner:** Person A ·
**Decision:** A

---

# Improvements — worth doing if time allows

## R-12 — Index modifiers are computed and stored but never exposed

`capability_assessments.index_modifiers` holds the full arithmetic behind every index
(`[{"code": "SOLE_ADEQUATE_ENGINEER", "delta": 1}, ...]`). No DTO carries it, so the "Why this
risk?" drawer can name the fired rules but cannot show how 72 was reached.

Adding it would make the index genuinely inspectable rather than merely reproducible, which is the
strongest available answer to "the risk score looks arbitrary" (PRD section 30). It is an additive
optional field, so it costs the frontend nothing until used. Category C, because it is a contract
change.

**Effort:** 1 hour backend, and Person B decides whether to render it.

---

## R-13 — `missing_evidence` only covers engineers below ASSISTED

Currently a "no qualifying evidence found" note is emitted only for engineers whose readiness is
below `ASSISTED`, which in the hero scenario means Jordan alone. Maria is `ASSISTED` and therefore
absent — yet "Maria has assisted but has no independent recovery evidence" is exactly what a manager
choosing a backup needs to read.

Widening it to anyone below `PRACTICED` would improve the Why drawer. It changes fixture content, so
coordinate with Person B.

**Effort:** 30 minutes.

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

## R-16 — `datetime.utcnow()` is deprecated in Python 3.12+

`app/simulation/service.py` and `app/mitigation/service.py` use `datetime.utcnow()`, which is
deprecated from 3.12. The venv runs 3.10 so nothing warns today, but the fix is
`datetime.now(timezone.utc)` and takes a minute.

**Effort:** 5 minutes.

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

## R-20 — The specification and the implementation now disagree in eight places

All eight are logged in `docs/DECISIONS.md` as DEC-05 through DEC-09 plus the fixture amendments,
with the reasoning for each. None was decided silently, but **all of them need Person B's
acknowledgement** because four are contract-visible:

- reason-code spelling (`API_CONTRACT.md` wins over `ARCHITECTURE.md` section 29)
- AI extraction output shape (per-claim, not the flat form in `API_CONTRACT.md` section 10.2)
- risk class scaling with operational criticality
- `SUPPORTED_BY` edge origin, since the frozen node enum has no `COVERAGE` type
- nine regenerated fixtures

**Recommendation.** Walk these five bullets at the next sync. It is fifteen minutes and it is the
difference between "we decided" and "Person A changed things".
