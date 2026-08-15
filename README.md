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

*TODO.*

```bash
# backend
cd backend && uvicorn app.main:app --reload

# frontend
cd frontend && npm run dev
```

Expand with: prerequisites, environment variables, the deterministic seed command, and a
clean-clone verification walkthrough.

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
| [`fixtures/`](fixtures/) | Shared mock payloads — the contract fixtures both sides validate against. |
| `frontend/` | Next.js / React / TypeScript application. |
| `backend/` | FastAPI / Python application. |
| [`BUILD_WITH_BOB.md`](BUILD_WITH_BOB.md) | Development log. |
| [`HANDOFF.md`](HANDOFF.md) | Session handoff notes. |
