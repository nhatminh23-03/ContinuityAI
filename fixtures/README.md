# Fixtures — shared contract payloads

These JSON files are the **shared contract truth** for ContinuityAI. They are jointly owned by
both developers and live at the repository root — not inside `frontend/` — precisely so that both
sides read the same files.

## What they are for

| Side | Use |
|---|---|
| Frontend | Renders screens against these payloads before the backend implements the endpoint. |
| Backend | API tests assert that real responses match these shapes. |
| Both | The daily golden-path integration check compares a real response against its fixture. |

Because both sides validate against the same payloads, a shape disagreement surfaces the moment
either side changes — not on integration day.

## The rule

> Fixtures must conform **exactly** to [`../docs/API_CONTRACT.md`](../docs/API_CONTRACT.md).

`API_CONTRACT.md` is authoritative. Where a fixture and the contract disagree, **the fixture is
wrong** and gets fixed. A fixture never becomes a second, unofficial API specification.

Changing a field name, an enum value, or a response shape here is a contract change: it requires
both developers to agree, an entry in [`../docs/DECISIONS.md`](../docs/DECISIONS.md), and updates
to `API_CONTRACT.md`, the Pydantic schemas, and the TypeScript types in the same change window.

## Expected files

One file per frozen endpoint response, named after what it returns:

```
platforms.json
payments-systems.json
payment-gateway.json
payment-gateway-graph.json
incident-recovery.json
incident-recovery-evidence.json
alex-simulation.json
backup-candidates.json
mitigation-plan.json
```

## Content rules

- All keys `snake_case`; all dates ISO-8601.
- Typed identifiers only — `system_payment_gateway`, `cap_incident_recovery`, `eng_alex_chen`.
- Every fixture uses the one canonical scenario: NovaPay → Payments Platform → Payment Gateway →
  Gateway Integration → Incident Recovery, with Alex, Maria, and Jordan. The same scenario is used
  in backend tests, frontend mocks, integration tests, screenshots, and the demo.
- Values must be reproducible by the rule engine. A number no rule can produce is a bug, not a
  placeholder — the seeded baseline and its risk class must reconcile with the counts around them.
- No employee productivity, value, ranking, or match-percentage field, in any fixture, ever.

## Fixture policy: always captured under `AI_PROVIDER=deterministic`

Fixtures are the rule-based baseline, on purpose and permanently. Whoever runs
`scripts/refresh_fixtures.py` runs it with `AI_PROVIDER` unset (or explicitly `deterministic`,
which is the default in `backend/.env.example`) — never with `watsonx` or `openrouter` set.

**Why.** `AI_PROVIDER=openrouter` (`backend/app/ai/openrouter.py`) writes model-generated prose for
three narrative fields — the simulation summary, a candidate's strengths and gaps, and the
mitigation plan's task titles/descriptions/acceptance criteria — and a model at temperature 0 is
still not guaranteed byte-identical across calls or across model versions. A fixture is a frozen
contract payload two developers build against; freezing it against non-reproducible text would make
`refresh_fixtures.py --check` fail on prose alone, forever, for a difference that carries no
information about whether the contract shape is right. Every non-narrative value — the risk index,
readiness level, exposure state, evidence rows, graph edges — is identical whether `deterministic`
or `openrouter` is selected, because `OpenRouterProvider.extract_artifact_semantics` delegates
straight to `DeterministicProvider`: extraction is rule-based under both, and only `openrouter`'s
three narrative fields differ. So freezing fixture capture under `deterministic` costs nothing on
the numbers and buys reproducibility on the one thing that would otherwise never hold still.

**This needs no change to `scripts/refresh_fixtures.py` or `scripts/verify_golden_path.py`.** Both
scripts read whatever `AI_PROVIDER` the process environment carries at run time; neither hardcodes a
provider. `AI_PROVIDER` defaults to `deterministic` (`backend/app/core/config.py`,
`backend/.env.example`), so run either script with no override and both already do the right thing.
`refresh_fixtures.py --check` keeps passing exactly because the default provider is the one the
fixtures were captured under — nothing about that behaviour changed when the OpenRouter provider was
added.

**Running `verify_golden_path` under `AI_PROVIDER=openrouter` will report narrative-field
differences — `simulation.summary`, `candidates[].strengths`, `candidates[].gaps`, and the
mitigation plan's task text.** This is expected, not drift, and not something to "fix" by editing
the fixtures or the script:

- `verify_golden_path.py` exits 0 whether or not differences are found — that is its documented
  design ("Exit code is 0 even when differences exist: some are expected and deliberate"), and
  differences are printed for a human to triage, not treated as failures.
- Every difference under `openrouter` will be confined to the same handful of narrative fields, and
  every other field — risk index, readiness, exposure, evidence, graph — will still read identical
  to the fixture, because extraction and every deterministic rule downstream of it are unaffected by
  the provider switch.
- A model-written narrative that differs from the frozen template text is not a contract violation;
  it is validated prose (`backend/app/ai/validation.py`) that says the same thing a different way, or
  it has already fallen back to the deterministic template because validation rejected it. Either
  way the shape is unchanged — only the wording of up to three fields per response can move.

A future reader seeing those diffs under `openrouter` should not treat them as a fixture that needs
regenerating, and should not treat them as a bug in `refresh_fixtures.py` or `verify_golden_path.py`.
They are the expected effect of pointing `verify_golden_path` at a provider that writes prose
instead of one that recites a template — and `verify_golden_path` is deliberately still runnable
that way, so a live pass under `openrouter` remains useful for confirming grounding and latency
(see `README.md`), even though `refresh_fixtures.py --check` is never run under it.
