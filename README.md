# ContinuityAI

**Engineering Knowledge Resilience**

> ContinuityAI turns fragmented engineering evidence into an evidence-backed knowledge graph so
> engineering managers can see which critical capabilities become exposed when expertise
> disappears — and prepare targeted knowledge-transfer work before the gap becomes an operational
> problem.

*Submission README. The technical sections are drafted; the product narrative, screenshots, and
demo walkthrough are still to come (`TEAM_WORKFLOW_PERSON_A_B.md` section 27 splits the first
drafts, then both developers cross-review).*

---

## Problem

*Draft — product narrative to be expanded.* Engineering organisations eliminate infrastructure
single points of failure while leaving a less visible failure mode untreated: critical technical
knowledge concentrated in one person. A service may be redundant across regions, but the ability to
recover it, deploy it, rotate its credentials, or diagnose its failures may still depend on one
engineer.

Existing tools cannot answer this. `CODEOWNERS` records who *declared* ownership, not who has
demonstrably operated the service. Contribution graphs record activity volume, and two hundred
trivial commits say less than two independent production recoveries. The evidence that would answer
the question is real but scattered across repositories, incident platforms, ticket systems, and
runbooks, and it goes stale as architecture changes.

*To expand: the trigger scenarios — resignation, leave during an incident, reorganisation,
architecture migration.*

## Solution

*Draft — screenshots and user journey to come.* One decision loop for an engineering manager:

```
Dashboard → System Detail → Graph + Evidence ("Why?") → Simulate engineer unavailable
  → Capability loss analysis → Compare technical backup candidates
  → Generate knowledge-transfer plan → Manager approves
```

Four concepts are measured, and keeping them separate is what makes the output legible:

| Concept | Attaches to | Answers |
|---|---|---|
| **Readiness** | one `(engineer, capability)` pair | What has this person demonstrably done? |
| **Exposure** | a capability, rolled up to a system | Does redundant coverage exist across everyone? |
| **Continuity Risk Index / Class** | a capability, a system | How severe, for comparison and sorting? |
| **Evidence Confidence** | coverage, capability, system | How much do we trust the underlying data? |

`Risk: HIGH` with `Confidence: LOW` is a legitimate and meaningful state — the evidence points at
exposure, and the evidence is thin. Collapsing the two would let a data-quality problem read as
safety.

## AI approach and architecture

The governing rule is **AI understands, rules decide**:

```
Engineering artifacts        incidents · pull requests · reviews · tickets · runbooks · CODEOWNERS
        │
        ▼  AI semantic extraction          what does this artifact demonstrate, about whom?
Structured evidence          (engineer, capability, evidence_role, strength, provenance)
        │
        ▼  deterministic aggregation       strength · diversity · repetition · freshness
Readiness                    NONE · EXPOSED · ASSISTED · PRACTICED · VALIDATED
        │
        ▼  deterministic rules             criticality × coverage shape
Exposure + Continuity Risk   COVERED · DEGRADED · CRITICAL_GAP · INSUFFICIENT_EVIDENCE
        │
        ▼  counterfactual                  same rules, one engineer's coverage excluded
Capability loss analysis  →  backup candidates  →  knowledge-transfer plan  →  human approval
```

### Where the boundary sits, and why

AI interprets unstructured text. It never assigns readiness, exposure, continuity risk, employee
value, or a chosen candidate. The `AIProvider` interface (`app/ai/provider.py`) has four methods —
`extract_artifact_semantics`, `summarize_simulation`, `explain_candidate`,
`generate_mitigation_plan` — and deliberately no `assess_readiness` or `score_risk`. **The interface
shape is itself the guardrail:** there is no method through which a model could return a score, so
no amount of prompt drift can produce one.

Everything downstream is deterministic and reproducible, which is what makes a "Why?" drawer
possible at all. A model cannot explain why it output 72; a rule engine can show that a CRITICAL
capability with one adequate engineer anchors at 70, plus one for the sole-expert dependency, plus
one because the best alternative has only assisted.

### Extraction is closed-world and validated

A provider receives the capability taxonomy it is allowed to attribute evidence to, and every
response is validated before anything reaches the database (`app/ai/validation.py`). Four rejection
classes:

| Rejected | Why it matters |
|---|---|
| Unknown capability | An invented capability is a hallucination entering the graph |
| Cross-system attribution | Gateway work credited to the refund service is a mis-mapping |
| Unknown engineer | An identity that does not exist cannot have demonstrated anything |
| **Claim against a non-participant** | The most damaging output available to this product: an unsupported claim against a named person |

Evidence strength is derived from the evidence role rather than trusted from the model, so a
provider that returns "STRONG" for a code review is corrected, not believed.

### Providers, one interface

| `AI_PROVIDER` | What it does |
|---|---|
| `deterministic` | Offline rule-based extraction, deterministic template narratives. No credential, fully repeatable. **The shipped default.** |
| `watsonx` | IBM watsonx.ai (`ibm/granite-4-h-small`) reads each artifact and returns structured claims. Narratives stay deterministic — see below |
| `cached` | Replays committed watsonx output from `data/extraction/`, so a model-derived graph seeds offline |
| `openrouter` | The mirror image of `watsonx`: extraction stays rule-based, and a model writes the three manager-facing narratives instead — see below |

`app/ingestion/pipeline.py` runs every extraction claim, from every provider including the default,
through `validate_extraction` unconditionally — that gate is not something only the model-backed
providers opt into. What is provider-specific is `openrouter`'s second gate, for the three prose
fields it alone generates: no other provider writes free text that needs that check. Swapping
providers changes extraction quality (`watsonx`, `cached`) or narrative wording (`openrouter`) and
changes no conclusion path either way — readiness, exposure, continuity risk, and simulation are
computed the same way under every provider, which is the property the interface exists to guarantee.

### What runs, precisely

For anyone deciding whether to trust a given response: **extraction is rule-based** under every
provider except `watsonx` and `cached` — `cached` replays committed `watsonx` output
(`app/ai/cache.py`: "The graph is model-derived"), so it inherits `watsonx`'s extraction rather than
running the rule-based matcher. Under `deterministic` and `openrouter`, capability names and aliases
are matched in the artifact text, scoped to its system, and the source system's participant role is
mapped onto an evidence role. **The three
narratives** — the simulation summary, a candidate's strengths and gaps, and a mitigation plan's task
titles, descriptions, and acceptance criteria — are template-written by default and, under
`AI_PROVIDER=openrouter`, model-written and validated before use. **Readiness, exposure, continuity
risk, and simulation are always deterministic rules and are never model-decided**, under any
provider: no `AIProvider` method exists through which a model could return one of those values (see
"Where the boundary sits, and why", above), so this is a property of the interface shape rather than
of provider configuration.

`AI_PROVIDER` still defaults to `deterministic`. Nothing above is switched on by default; it
describes what runs when an operator explicitly configures a model provider and supplies credentials
in `backend/.env`.

### A second provider: rule-based extraction, model-written narratives

`OpenRouterProvider` (`backend/app/ai/openrouter.py`) exists for the opposite reason `watsonx` does.
`watsonx` spends a model call on extraction, where a wrong answer changes the knowledge graph and
every downstream number while still looking plausible — so two of its three narratives stay
deterministic on purpose (`explain_candidate` and `generate_mitigation_plan` in `watsonx.py` each
say why in their own body). The third, `summarize_simulation`, is model-written there as well, and
passes the same `validate_simulation_summary` gate before it is returned or written to
`result_json`. `openrouter` spends its model calls the
other way: extraction delegates to `DeterministicProvider` in one line, and the model writes only the
simulation sentence, a candidate's strengths and gaps, and the mitigation plan's task text — prose
over facts the rules already decided, which changes no conclusion and is the part a manager actually
reads out in a room.

**Every generation passes `app/ai/validation.py` before it can be returned**, the same discipline the
extraction gate applies to claims, but the checks are not identical across the three narratives —
each has its own validator function, and which rule applies depends on what the text is claiming.
No prohibited phrase and no name — person or capability — outside what the generator was actually
given apply everywhere, in all three. Beyond that they diverge: only the simulation summary is
checked for likelihood or percentage language (a simulation reports coverage loss, not an outage
forecast) and only it carries a length cap; only a candidate's **gaps** are checked for wording that
states inability rather than absence of evidence, and only its **strengths** are checked for
overstating a capability the record holds as assisted-only or missing as independently demonstrated
— arguably the gate's strongest responsible-AI property, because it is the one check built to catch
exactly the overstatement this product exists to prevent, and it fires on a fact-buckets comparison
the other checks cannot see. That check is lexical, though, and the limit belongs next to the claim:
it pairs the independence wording with an unproven capability only when the strength contains that
capability's **name**, so "has independently handled that recovery work, unaided" carries the same
overstatement past it. See the fifth blind spot below. The mitigation plan carries a different set
entirely, all structural:
3-5 actions in total, a narrower count band keyed to the candidate's readiness, every task type a
valid enum member, at least one acceptance criterion per task, the opening task citing evidence, and
a recovery drill present or absent to match the readiness band. Anything any check rejects, and any
transport failure, timeout, or malformed reply, falls back to the deterministic template; rejections
log at WARN so a gate that is silently rejecting everything remains visible rather than looking
identical to one that works.

**Grounding is prompt-enforced, not gate-enforced, and that is worth stating without hedging.** The
gate's name check (`find_unattested_names` in `app/ai/language_policy.py`) is a documented heuristic
with four real blind spots: a single-word invention such as "ask Priya to confirm" passes it, because
one capitalised word is structurally identical to any capitalised ordinary noun; an invented
capability written in lower case passes it; a bare, fully capitalised line passes only the narrower
recombination check, because on a title-cased line capitalisation carries no signal at all; and a
two-word qualifier attached to an attested name — "Refund Processing In Europe" where "Refund
Processing" is attested — passes, because the title-tail exemption is bounded to exactly two words.
A fifth belongs to a different check: the independence rule above is lexical, so an oblique
reference to an assisted-only capability — "has independently handled that recovery work, unaided",
where the capability is never named — passes, and closing it needs a lexicon the module does not
have. These are not oversights — the four name-check blind spots are stated plainly in
`app/ai/language_policy.py`'s module docstring (`find_unattested_names`'s own docstring only
points there), the fifth is stated in `validate_candidate_narrative`'s own docstring, and
`backend/tests/test_narrative_validation.py` pins them, though no single test covers them all:
`test_known_blind_spots_of_the_name_check`
parametrizes two of the name check's four, and `test_known_blind_spot_of_the_independence_check`
covers the fifth. Nobody should mistake the gate for closed-world grounding it does not
have. What actually keeps a narrative grounded is the prompt: each of the three prompt files under
`app/ai/prompts/` states explicitly which names, capabilities, and evidence ids may appear, and the
gate is the net under that instruction, not a replacement for it.

**Timing is sized against AC-14's 12-second budget for an AI plan or explanation operation — for two
of the three narratives.** `explain_candidate` is called once per *returned* candidate rather than
once per eligible engineer — narration runs after the response is sliced to `limit`, which the
contract caps at 3 — so three sequential calls at the 3.5-second default timeout come to 10.5
seconds, inside the budget. That total is bought by narrowing each phase's own headroom: splitting
the 3.5-second default across `TIMEOUT_PHASE_SHARES` leaves connect 0.875s and read 2.275s, each
down from the full 3.5s an unsplit `httpx.Timeout` would have given it, so on a slow network this
provider now falls back to the deterministic template more often than the wider, unbounded-total
budget used to — safe, and WARN-logged, but a real trade against the old headroom. A plan is one
call per request and gets twice the per-call ceiling. The
third narrative does not fit that budget at all: `summarize_simulation` runs inside
`POST /simulations` (`app/simulation/service.py`), and AC-14's figure for that endpoint is not the
12-second "AI plan/explanation" one but the 2-second "deterministic simulation" one (`PRD.md`,
AC-14) — a target set before this narrative call existed. A single call at the 3.5-second default
timeout can, on its own, take longer than the endpoint's entire stated budget, and nothing in this
build reconciles the two.

**That measurement has since been taken, and both budgets are breached.** On a live pass against a
real key on 2026-08-21: `POST /simulations` 2.85s against the 2-second deterministic-simulation
budget, and `POST /recommendations/backup-candidates` 11.93s typically and 16.91s at worst against
the 12-second AI-operation budget. Reads are unaffected at 16–23ms. The arithmetic above assumes a
call completes near its 3.5-second nominal timeout; in practice each took roughly 6 seconds, because
httpx's read timeout bounds the gap between successive socket reads rather than the time to generate
a whole response. Four responses are open — cap `max_tokens`, use a faster model, run the candidate
calls concurrently, or accept and document the breach — and none is implemented here (`OPEN-11`,
`docs/DECISIONS.md`). `AI_PROVIDER=deterministic` is unaffected and remains the default, so the
shipped configuration meets AC-14.

**Nothing above changes a number.** `OpenRouterProvider.extract_artifact_semantics` delegates
straight to `DeterministicProvider`, so the seeded baseline is untouched under this provider exactly
as it is under `deterministic`: Payment Gateway 74 / HIGH, Incident Recovery 72 / HIGH, the
simulation 74 → 93, Identity Systems 68, Maria HIGH overlap, Jordan MEDIUM. What can move is
narrower than the DTO shape but wider than wording alone: the simulation summary and a candidate's
strengths and gaps are wording-level changes over fixed facts, but the mitigation plan can also
legitimately vary in task count (within the readiness-appropriate band `_task_count_band` computes),
per-task type (any valid `MitigationTaskType`, not the deterministic template's specific sequence),
and linked evidence (a filtered subset of what was offered, not a fixed list) — all still bounded by
the gate above, none of it a sign the gate is failing.

**The rule-based provider is the default, and its ceiling is worth stating plainly.** It finds what
the text *names*: it resolves capabilities by matching capability names and aliases, scoped to the
artifact's system, then maps the participant role the source system recorded onto an evidence role. It
cannot read "restarted the workers and traffic recovered" and infer incident recovery without the
phrase present.

### What the model measurably adds

The watsonx provider was run over the corpus and diffed against the rule-based one
(`data/extraction/comparison_report.md`). Over the 313 artifacts extracted before the account's token
quota was spent:

| Measure | Count |
|---|---|
| Artifacts where both produced identical output | 291 / 313 |
| Claims both agree on | 50 |
| Claims found only by the model | 0 |
| Claims found only by the rules | 5 |
| Same `(capability, engineer)` pair, different evidence role | 17 |

The disagreements are the interesting part, and they are all in one direction: 14 cases of
`CONTRIBUTION → INDEPENDENT_EXECUTION` and 3 of `CONTRIBUTION → KNOWLEDGE_CAPTURE`. The model read
the narrative and concluded the person acted alone, or authored operational guidance, where the rule
saw only that they changed something. That is precisely the judgement a string match cannot make —
and precisely the judgement that most needs checking, because promoting a contribution to an
independent execution is what moves an engineer toward `PRACTICED` and therefore what closes or opens
a coverage gap.

**Which is more accurate is an open question, and the harness can answer it.** Seed and evaluate under
each provider and compare reconstruction against the hidden ground truth. That comparison is not yet
run because the watsonx account's token quota was exhausted at 49% coverage, and `cached` deliberately
refuses to run on a partial cache: a graph half derived by a model and half by string matching would be
neither, and no number in it could be explained by reference to a single method.

So the honest position today: the model-backed path is implemented, credential-verified, rate-limit
aware, resumable, and measured against the rules on half the corpus — and the graph the API serves is
still rule-derived. [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) R-01 tracks finishing it.

### Module layout

```
backend/app/
  ingestion/     source adapters → normalised artifacts
  ai/            provider interface, deterministic provider, validation, versioned prompt spec
  evidence/      strength, freshness, aggregation, evidence confidence
  continuity/    readiness rules, exposure rules, risk index and class, reason codes, aggregation
  graph/         typed nodes and edges assembled from relational tables
  simulation/    the counterfactual
  recommendation/ backup candidate comparison
  mitigation/    knowledge-transfer plan generation and approval
  challenge/     manager attestation, evidence linking, mapping correction
  services/      facts loader, read services, recompute
  evaluation/    hidden-ground-truth comparison (the only package that may read the answer key)
```

A modular monolith on FastAPI with SQLite behind a typed graph abstraction. No graph database: the
graph semantics live in Python so traversal and simulation do not depend on a storage product.

## Evidence model

Readiness is computed from evidence and never written directly. There is no code path anywhere —
including the manager challenge workflow — that accepts a readiness value.

| Level | Requires |
|---|---|
| `VALIDATED` | 2+ independent executions, across 2+ artifact types among the strong evidence, at least one still fresh, no conflicts |
| `PRACTICED` | 1+ independent execution that has not gone stale, plus a supporting item |
| `ASSISTED` | 2+ items including assisted execution, a contribution, or authored documentation |
| `EXPOSED` | Any qualifying evidence, none of it execution |
| `NONE` | No qualifying evidence |

The `EXPOSED → ASSISTED → PRACTICED` progression turns on **independence, never volume** — the rules
read `independent_execution_count`, not a total. Twenty code reviews stay `EXPOSED`. That is the
"artifact, not activity" principle expressed as code. `PRACTICED → VALIDATED` additionally requires
repetition *and* source diversity: two incidents from the same pager rotation are one kind of proof;
an incident plus an authored runbook are two.

Uncertainty is a first-class answer. Fewer than two evidence records returns
`INSUFFICIENT_EVIDENCE` with a null index and null class rather than a manufactured classification,
and conflicting evidence — an attempt that was reverted — is retained, shown separately, and drops
confidence to `LOW` while leaving the other evidence's conclusions intact.

## Continuity risk engine

The risk **class** is the authoritative rule output. The **index** is a derived comparison number,
anchored on the class and clamped to its band so a modifier can never silently reclassify anything.
It is not a probability of outage, of departure, or of anything else.

Adequate coverage means `PRACTICED` or better, on evidence that has not gone stale.

| Adequate engineers | CRITICAL capability | HIGH capability | MEDIUM / LOW |
|---|---|---|---|
| 0 | `CRITICAL_GAP` / CRITICAL | `CRITICAL_GAP` / HIGH | `DEGRADED` / MODERATE |
| 1 | `DEGRADED` / HIGH | `DEGRADED` / MODERATE | `COVERED` / MODERATE |
| 2+ | `COVERED` / LOW with a VALIDATED engineer, else MODERATE | same | same |

Separating `DEGRADED` (coverage exists, resilience does not) from `CRITICAL_GAP` (no adequate
coverage remains) is what makes the counterfactual able to *create* a gap. Under the original rule
shape a sole-expert capability was already a critical gap, so removing the expert could not change
anything — the defect that the Phase 0 contract audit found and fixed.

Bands are LOW 0–39, MODERATE 40–59, HIGH 60–79, CRITICAL 80–100, anchored at 20 / 50 / 70 / 90.
Worked example, Incident Recovery: CRITICAL capability, one adequate engineer, best alternative only
assisted → class HIGH, anchor 70, +1 sole adequate engineer, +1 best alternative assisted = **72**.
Every fired rule is returned as a machine-readable reason code, and the modifier arithmetic is
returned alongside it, so the number is inspectable rather than merely reproducible.

System risk is the **maximum** across a system's capabilities, never an average: nine healthy
capabilities must not dilute one critical gap. Platforms get no index of their own — a platform row
shows its highest system index, total critical gaps, and drift.

## Counterfactual simulation

The hero capability, and the smallest piece of code in the system:

```python
before = assess(facts)
after  = assess(facts.without(engineer_id))
```

`CapabilityFacts` is a frozen dataclass and `.without()` returns a new instance, so two properties
hold structurally rather than by discipline. Baseline state **cannot** be corrupted — nothing is
written and there is no snapshot to restore. And before and after **cannot** disagree, because there
is only one assessment implementation rather than a separate "simulate" path that could drift.

The result is specific rather than vague. Simulating the sole expert on the seeded Payment Gateway:

```
Incident Recovery        DEGRADED → CRITICAL_GAP   (best remaining: ASSISTED)
Provider Failover        COVERED  → DEGRADED       (best remaining: PRACTICED)
Certificate Management   DEGRADED → CRITICAL_GAP   (best remaining: EXPOSED)
Retry Logic              COVERED  → COVERED        (best remaining: VALIDATED)
Monitoring               COVERED  → COVERED        (best remaining: VALIDATED)

system  74 HIGH → 93 CRITICAL
```

Reporting the unchanged capabilities is the point, not noise: "Retry Logic stays covered" is what
makes this an analysis rather than the observation that a person is important. The simulation
identifies coverage loss and does not predict an outage.

## Human correction

An assessment can be disputed, and a manager never edits a score. They change the **evidence** —
link an artifact extraction missed, attest to something no artifact captured, or correct a
mis-mapped record — and readiness, exposure, and risk are recomputed from it through the same code
path the seed uses. Previous and new assessments are both persisted, because a correctable
assessment that cannot be audited is worse than one that cannot be corrected.

Manager attestation is capped at moderate strength and always visibly labelled as an attestation, so
no quantity of assertions can manufacture a `VALIDATED` expert.

## Evaluation

Because real employee and incident data is sensitive and unavailable, the prototype is validated
against a synthetic organisation with **hidden ground truth**. A generator reads the true readiness
distribution and emits artifacts from it; the application receives only the artifacts and must
re-derive everything.

The isolation is enforced, not asserted. Application configuration exposes no path to the answer
key, only `app/evaluation/` resolves one, and a test parses every module under `app/` and fails if
any of them names the directory, imports the evaluation package, or reaches it through settings.
Without that test the product's central claim would be unfalsifiable.

Results on the seeded dataset — 640 artifacts, 126 evidence records, 56 coverage relationships:

| Check | Result |
|---|---|
| Knowledge reconstruction (engineer-capability readiness) | 56 / 56 |
| Capability exposure classification | 25 / 25 |
| Critical gap detection (no misses, no false positives) | 2 / 2 |
| Declared-versus-demonstrated ownership mismatch | 1 / 1 |
| Counterfactual simulation | 25 / 25 |
| Backup candidate recommendation | 2 / 2 |
| Evidence grounding (every coverage claim cites a source) | 56 / 56 |

**These are not accuracy figures and must not be quoted as such.** The generator emits evidence
patterns chosen to be classifiable, so what they measure is that the pipeline is self-consistent end
to end — ingestion, extraction, aggregation, readiness, exposure, risk, simulation, candidates — and
that no stage drops or invents information. They say nothing about whether the readiness heuristics
match real human expertise; those are prototype thresholds for transparent demo logic, not
calibrated competency standards. The caveat is printed inside the generated report.

### What real public data showed

The corpus is hybrid, as the data strategy requires: 520 synthetic private enterprise records
(incidents, tickets, runbooks) plus 120 real merged pull requests and reviews from a public
repository, ingested through the same pipeline.

Exactly one of those 120 real artifacts produced capability evidence. That is a finding rather than a
failure. A public SDK repository's vocabulary is library maintenance — support, error handling,
tests, packaging — while the capabilities this product assesses are demonstrated in *private
operational* records: incidents, runbooks, on-call history. It is direct evidence for why the hybrid
data strategy is necessary, and a concrete measurement of the rule-based extractor's ceiling.

Contributor identities in that public data are pseudonymised onto the synthetic organisation and the
real logins are never written to disk, including `@mentions` scrubbed from pull request bodies. This
product infers capability readiness about named people; doing that to real engineers who never
consented would breach its own responsible-AI boundary. Artifacts stay traceable through their real
URLs — the attribution is what is synthetic, and the manifest says so.

## Challenge theme

*Draft — judging-criteria mapping to be expanded jointly.* Wildcard Challenge — Build Intelligent
Systems for the Future of Work.

The product addresses the four capabilities the brief names: it **plans** targeted
knowledge-transfer work for specific capability gaps, **coordinates** by identifying primary and
backup coverage and preparing work for approval, supports **decision-making** through the
counterfactual simulator, and prepares **execution** as structured tasks a human approves. It is
decision support for an engineering manager, not workflow automation — every staffing decision
stays human.

## Development tooling

*Draft.* See [`BUILD_WITH_BOB.md`](BUILD_WITH_BOB.md) for the development log: what was built, which
requirement each unit implements, how it was validated, and what remains open. It records the three
specification defects the build surfaced, including a rule that made the frozen demo state
unreachable.

## Setup

Prerequisites: Node 20+ and Python 3.10+ (the DTOs use `int | None`, so 3.9 will not work).

**Backend** — http://localhost:8000, interactive docs at `/docs`:

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload
```

The database is created and seeded on first boot, so there is no separate setup step. Set
`AUTO_SEED=false` to manage it yourself.

**Frontend** — http://localhost:3000:

```bash
cd frontend && npm install
cp .env.local.example .env.local     # NEXT_PUBLIC_USE_MOCKS=false points at the live backend
npm run dev
```

### Commands

All from `backend/`, with `PYTHONPATH=.`:

| Command | Purpose |
|---|---|
| `python -m scripts.seed_demo` | Rebuild the demo database from scratch. Deterministic and idempotent |
| `python -m scripts.run_evaluation` | Compare inferred state against the hidden ground truth; writes `data/generated/evaluation_report.md` |
| `python -m scripts.verify_golden_path` | Walk every endpoint, diff each response against its fixture, and report latency against AC-14 |
| `python -m scripts.refresh_fixtures --check` | Fail if any fixture has drifted from live output |
| `python -m scripts.generate_synthetic_data` | Regenerate the synthetic corpus from the hidden model |
| `python -m scripts.fetch_public_github` | Refetch and re-anonymise the real public GitHub corpus (needs `gh`) |

Neither regeneration command is needed for normal work: both corpora are committed.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///backend/continuity.db` | Demo database |
| `AUTO_SEED` | `true` | Seed automatically when the database is empty |
| `AI_PROVIDER` | `deterministic` | `deterministic`, `watsonx`, `cached`, or `openrouter`. The offline provider ships as the default; the model-backed providers are implemented and credential-gated, and shipping with `deterministic` means nothing is switched on until an operator opts in |
| `API_TOKEN` | *(empty)* | When set, `/api/v1` requires `Authorization: Bearer <token>`. Empty leaves the API open, which is the local default |
| `REFERENCE_DATE` | `2026-08-15` | The clock freshness is judged against, so a seeded demo cannot age into different classifications |

### Checks

```bash
cd backend && .venv/bin/python -m pytest -q                 # 269 tests, ~3 seconds
cd ../frontend && npm run typecheck && npm run build
```

### Clean-clone walkthrough

```bash
git clone <repo> && cd ContinuityAI
cd backend && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python -m scripts.seed_demo          # 640 artifacts -> 126 evidence records
PYTHONPATH=. .venv/bin/python -m scripts.run_evaluation     # every check should pass
.venv/bin/python -m uvicorn app.main:app --reload
```

The interpreter is named explicitly because on macOS a bare `python3` is often the system 3.9, which
cannot run this application — the version floor is 3.10. Substitute whatever 3.10+ interpreter is on
the machine.

The seeded organisation, the hidden ground truth, and both artifact corpora are committed, so the
demo reproduces byte for byte from a fresh clone with no network access.

## Demo

*TODO.* Public demo video (≤ 3 minutes): link to be added.

Hero scenario — NovaPay Payment Gateway. Jordan is the declared CODEOWNERS owner; the engineering
evidence shows Alex has the strongest demonstrated Incident Recovery coverage. Simulating Alex as
unavailable turns Incident Recovery and Certificate Management into critical coverage gaps while
Retry Logic stays covered, moving the system from HIGH to CRITICAL. Maria returns as the strongest
technical backup candidate; the manager selects her and approves a targeted transfer plan.

---

## Responsible use

ContinuityAI scores **systems and capabilities**, never people. It produces no employee
productivity, value, ranking, promotion, bonus, or layoff output, and ingests no private messages,
working hours, location, or sentiment data. The Continuity Risk Index is a severity index for
comparison — not a probability of failure. Absence of evidence is reported as absence of evidence,
never as inability. Staffing decisions remain human decisions.

## Repository layout

| Path | Contents |
|---|---|
| [`docs/`](docs/) | Specifications. Start at [`docs/README.md`](docs/README.md); load [`docs/ENGINEERING_RULES.md`](docs/ENGINEERING_RULES.md) before any task. |
| [`fixtures/`](fixtures/) | Shared contract payloads both sides validate against. Regenerated from live output by `scripts/refresh_fixtures.py`. |
| `data/org/` | The NovaPay organisation structure: platforms, systems, components, capabilities, engineers. |
| `data/synthetic/` | Generated private enterprise corpus — 520 incidents, pull requests, reviews, issues, tickets, runbooks. Committed for reproducibility. |
| [`data/public/`](data/public/) | 120 real merged pull requests and reviews from a public repository, contributor identities pseudonymised. |
| [`data/ground_truth/`](data/ground_truth/) | Hidden readiness labels. Readable by the generator and the evaluator only, never by application runtime. |
| `frontend/` | Next.js / React / TypeScript application. |
| `backend/` | FastAPI / Python application. Engines under `app/{evidence,continuity,simulation,recommendation,mitigation,challenge}/`. |
| [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) | Open concerns and improvements, ranked by risk. |
| [`BUILD_WITH_BOB.md`](BUILD_WITH_BOB.md) | Development log. |
| [`HANDOFF.md`](HANDOFF.md) | Session handoff notes. |
