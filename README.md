# ContinuityAI

**Engineering Knowledge Resilience**

> ContinuityAI turns fragmented engineering evidence into an evidence-backed knowledge graph so
> engineering managers can see which critical capabilities become exposed when expertise
> disappears — and prepare targeted knowledge-transfer work before the gap becomes an operational
> problem.

*Submission README — sections below are stubs to be completed before submission.*

---

## Problem

*TODO.* Engineering organisations eliminate infrastructure single points of failure while leaving
a less visible failure mode untreated: critical technical knowledge concentrated in one person. A
service may be redundant across regions, but the ability to recover it, deploy it, rotate its
credentials, or diagnose its failures may still depend on one engineer.

Expand with: why declared ownership is not demonstrated capability, why activity volume is not
expertise, and the trigger scenarios (resignation, leave during an incident, reorganisation,
architecture change).

## Solution

*TODO.* One decision loop for an engineering manager:

```
Dashboard → System Detail → Graph + Evidence ("Why?") → Simulate engineer unavailable
  → Capability loss analysis → Compare technical backup candidates
  → Generate knowledge-transfer plan → Manager approves
```

Expand with: screenshots, the four scored concepts (readiness, exposure, continuity risk,
evidence confidence), and what the product deliberately does not do.

## AI approach and architecture

*TODO.* The governing rule is **AI understands, rules decide**:

```
Engineering artifacts → AI semantic extraction → structured evidence
  → deterministic aggregation → readiness / exposure / continuity risk
  → counterfactual simulation → grounded recommendation
```

AI interprets unstructured artifacts (incidents, pull requests, tickets, runbooks) into typed
evidence. It never assigns readiness, risk, employee value, or a chosen candidate — a
deterministic rule engine owns those, and every conclusion traces back to source evidence.

Expand with: the architecture diagram, the AI provider abstraction, structured-output validation,
and hidden-ground-truth evaluation.

## Challenge theme

*TODO.* Wildcard Challenge — Build Intelligent Systems for the Future of Work.

Expand with: how the product addresses planning, coordination, decision-making, and execution,
and how it maps to the judging criteria.

## Development tooling

*TODO.* How the prototype was built — see [`BUILD_WITH_BOB.md`](BUILD_WITH_BOB.md) for the
development log covering planning, implementation, testing, debugging, and documentation.

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
| `python -m scripts.verify_golden_path` | Walk all ten endpoints and diff each response against its shared fixture |
| `python -m scripts.refresh_fixtures --check` | Fail if any fixture has drifted from live output |
| `python -m scripts.generate_synthetic_data` | Regenerate the artifact corpus from the hidden model |

### Checks

```bash
cd backend && .venv/bin/python -m pytest -q                 # 101 tests
cd ../frontend && npm run typecheck && npm run build
```

### Clean-clone walkthrough

```bash
git clone <repo> && cd ContinuityAI
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python -m scripts.seed_demo          # 520 artifacts -> 124 evidence records
PYTHONPATH=. .venv/bin/python -m scripts.run_evaluation     # every check should pass
.venv/bin/python -m uvicorn app.main:app --reload
```

The seeded organisation, the hidden ground truth, and the generated artifact corpus are all
committed, so the demo reproduces byte for byte from a fresh clone.

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
| `data/synthetic/` | Generated artifact corpus — 520 incidents, pull requests, reviews, issues, tickets, documents. Committed for reproducibility. |
| [`data/ground_truth/`](data/ground_truth/) | Hidden readiness labels. Readable by the generator and the evaluator only, never by application runtime. |
| `frontend/` | Next.js / React / TypeScript application. |
| `backend/` | FastAPI / Python application. Engines under `app/{evidence,continuity,simulation,recommendation,mitigation}/`. |
| [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) | Open concerns and improvements, ranked by risk. |
| [`BUILD_WITH_BOB.md`](BUILD_WITH_BOB.md) | Development log. |
| [`HANDOFF.md`](HANDOFF.md) | Session handoff notes. |
