# ContinuityAI — Person A & Person B Collaboration Playbook

**Version:** 1.0  
**Status:** Team working agreement  
**Project:** ContinuityAI  
**Companion documents:** `PRD.md`, `API_CONTRACT.md`, `DOMAIN_MODEL.md`, `ARCHITECTURE.md`

---

# 1. Purpose

This document defines **how Person A and Person B should work together while building ContinuityAI**.

It is not another architecture document. Its purpose is to prevent the most common two-person project failures:

- one person waiting for the other;
- frontend and backend drifting apart;
- large unmerged branches;
- silent API changes;
- duplicated work;
- unclear ownership;
- integration being postponed until the end;
- one person becoming the only person who understands a critical subsystem;
- polishing low-value features while the main demo flow is still broken.

The operating principle is:

> **Work independently behind shared contracts, integrate frequently, and protect the same end-to-end golden path every day.**

---

# 2. Team Roles

The team uses clear primary ownership without creating knowledge silos.

## Person A — Intelligence / Backend Lead

Person A primarily owns:

- FastAPI backend;
- Pydantic request/response schemas;
- SQLite persistence;
- synthetic NovaPay data;
- hidden ground truth;
- artifact ingestion;
- AI semantic extraction;
- evidence normalization;
- knowledge graph service;
- readiness engine;
- continuity-risk engine;
- simulation engine;
- backup candidate engine;
- mitigation-plan backend;
- evaluation.

Person A's primary question is:

> **Does ContinuityAI reach a defensible technical conclusion?**

---

## Person B — Product / Frontend Lead

Person B primarily owns:

- Next.js / React frontend;
- TypeScript API types;
- mock API adapter;
- portfolio dashboard;
- system detail;
- contextual graph visualization;
- evidence/provenance experience;
- simulation interface;
- before/after continuity visualization;
- candidate comparison;
- mitigation-plan interface;
- loading/error states;
- visual polish;
- demo usability.

Person B's primary question is:

> **Can an engineering manager understand, trust, and act on the conclusion?**

---

## Shared Ownership

Both people jointly own:

- product direction;
- API contracts;
- domain terminology;
- architectural changes;
- integration;
- acceptance testing;
- responsible-AI boundaries;
- README;
- IBM Bob usage documentation;
- demo script;
- demo recording;
- final submission.

The rule is:

> **Every component has one primary owner, but no critical concept has only one person who understands it.**

---

# 3. How Work Should Be Divided

Do **not** divide the project like this:

```text
Person A:
Finish the entire backend.

THEN

Person B:
Connect the frontend.
```

That creates waiting and late integration risk.

Instead, divide by **vertical milestones**.

Example:

```text
Simulation Milestone

Person A
- simulation engine
- simulation API
- tests

Person B
- simulation selector
- before/after visualization
- error/loading states

Together
- integrate endpoint
- run Alex scenario
- verify expected result
```

Both developers make progress on the same product capability simultaneously.

---

# 4. Collaboration Model

The standard workflow for every meaningful feature is:

```text
1. Contract already exists
        ↓
2. Person B builds against mock data
        ↓
3. Person A implements real backend behavior
        ↓
4. Both integrate
        ↓
5. Both test the golden path
        ↓
6. Merge to main
```

Neither person should wait unnecessarily.

---

# 5. Source of Truth Hierarchy

Authority is split by subject matter, not by document rank. A flat ranking would let the PRD
silently override frozen enums and field names, which is the opposite of what a frozen contract
means.

| Subject | Authoritative document |
|---|---|
| Product scope, user journey, UX requirements, acceptance criteria | `PRD.md` |
| Wire format — endpoints, field names, enum spelling, JSON shape | `API_CONTRACT.md` |
| Internal semantics — entity meaning, invariants, rule intent | `DOMAIN_MODEL.md` |
| Module layout, technology, testing, deployment | `ARCHITECTURE.md` |
| Process, ownership, decision categories | This collaboration document |

Current implementation is never authoritative over any of them.

Where the PRD requires a product behaviour the contract cannot carry, the contract is amended
through the change process in section 6 — the PRD does not win by default at the wire level.

Code does not automatically become the new specification.

If implementation conflicts with a frozen contract, either:

- fix the implementation; or
- deliberately change the contract together.

---

# 6. Contract Rule

No developer may silently change:

- endpoint names;
- request fields;
- response fields;
- enum values;
- readiness semantics;
- risk semantics;
- graph node/edge meanings;
- simulation semantics.

If a contract change is necessary:

```text
1. Identify the problem.
2. Explain why the current contract cannot support it.
3. Discuss impact together.
4. Update the relevant Markdown specification.
5. Update mock JSON.
6. Update backend Pydantic schema.
7. Update frontend TypeScript type.
8. Integrate in one coordinated change.
```

Contract changes should be rare after Phase 0.

---

# 7. Git Working Agreement

Primary branch:

```text
main
```

`main` should always be runnable.

Do not use long-lived branches named after developers.

Avoid:

```text
person-a
person-b
john-work
mary-work
backend-final
frontend-final
```

Use short-lived feature branches.

Examples:

```text
feature/backend-schemas
feature/dashboard
feature/evidence-engine
feature/evidence-ui
feature/simulation-engine
feature/simulation-ui
feature/recommendation-engine
feature/candidate-comparison
feature/mitigation-api
feature/mitigation-ui
```

---

# 8. Branch Lifetime

Target:

> **A branch should usually live less than one working day.**

Some larger features may take longer, but avoid branches that diverge from `main` for several days.

The longer a branch lives, the more integration risk it creates.

---

# 9. Pull Request Rule

Every non-trivial change should go through a pull request.

A pull request should answer:

```text
What changed?
Why?
What contract does it implement?
How was it tested?
What should the other developer review carefully?
```

Recommended PR template:

```markdown
## What changed

## Why

## Contract / requirement

## Validation

## Screenshots or API examples

## Risks / follow-up
```

---

# 10. Review Responsibilities

Person A reviews Person B's work for:

- incorrect domain interpretation;
- unsupported claims;
- risk/readiness misuse;
- API mismatches;
- broken data assumptions.

Person B reviews Person A's work for:

- confusing outputs;
- unusable response structures;
- missing display information;
- terminology that users may misunderstand;
- results that cannot be explained clearly.

This cross-review is intentional.

---

# 11. Merge Rule

A PR can merge when:

- it builds;
- relevant tests pass;
- contract matches;
- owner has self-reviewed;
- the other developer has reviewed when practical;
- it does not break the current golden path.

Do not delay every merge waiting for perfection.

Prefer:

> small, safe, frequent merges.

---

# 12. Daily Working Rhythm

## Morning Sync — 15 minutes

Each person answers four questions:

### Person A

```text
What did I complete yesterday?
What will I complete today?
What do I need from Person B?
What could block me?
```

### Person B

Same questions.

Then confirm:

> **What is the one integration result we want working by the end of today?**

Example:

```text
Today's integration goal:
Payment Gateway dashboard loads from real FastAPI data.
```

---

# 13. Midday Sync — 5 minutes

This is not a meeting.

Check:

- new contract issues;
- blocking questions;
- open PRs;
- schema changes;
- merge conflicts.

If nothing is blocked, continue working.

---

# 14. End-of-Day Integration — 20 to 30 minutes

Both developers run the application together.

Always walk through as much of the golden path as currently exists:

```text
Dashboard
  ↓
Payments Platform
  ↓
Payment Gateway
  ↓
Incident Recovery
  ↓
Evidence
  ↓
Simulate Alex unavailable
  ↓
Critical gap
  ↓
Compare Maria / Jordan
  ↓
Select candidate
  ↓
Generate plan
  ↓
Approve
```

Early in development some steps will still be mocked.

That is acceptable.

The important part is that the product stays coherent.

---

# 15. Golden Path Rule

The golden path is the highest-priority feature in the project.

If it breaks:

> **Stop adding features and repair it.**

The team should never knowingly allow the core demo workflow to stay broken while working on secondary functionality.

---

# 16. Phase Structure

Use phases, but allow parallel work inside every phase.

Recommended sequence:

```text
Phase 0 — Contracts and architecture
Phase 1 — Project skeletons
Phase 2 — Data foundation + dashboard
Phase 3 — Evidence + knowledge graph
Phase 4 — Readiness + risk
Phase 5 — Counterfactual simulation
Phase 6 — Candidate comparison
Phase 7 — Mitigation
Phase 8 — Evaluation
Phase 9 — Demo hardening
Phase 10 — Submission
```

---

# 17. Phase 0 — Complete

Shared work:

- PRD;
- API contract;
- domain model;
- architecture;
- ownership agreement.

Exit condition:

> Both developers accept the frozen contracts.

---

# 18. Phase 1 — Skeletons

## Person A

Create:

- FastAPI project;
- `/api/v1`;
- Pydantic schemas;
- 10 frozen endpoints;
- mock responses;
- SQLite setup;
- health test;
- API tests.

Suggested branch sequence:

```text
feature/backend-bootstrap
feature/backend-schemas
feature/backend-mock-routes
```

---

## Person B

Create:

- Next.js + TypeScript project;
- application shell;
- TypeScript types;
- mock data;
- mock API service;
- dashboard shell;
- Payment Gateway detail shell.

Suggested branches:

```text
feature/frontend-bootstrap
feature/frontend-types
feature/dashboard-shell
```

---

## Phase 1 Integration Gate

Both developers prove:

```text
Frontend mock response
        ==
Backend real mock response
```

Specifically:

```text
GET /api/v1/platforms
```

should replace local JSON without requiring component redesign.

Do not move forward until this works.

---

# 19. Phase 2 — Data Foundation + Dashboard

## Person A

Own:

- NovaPay hidden organization model;
- systems;
- components;
- capabilities;
- engineers;
- synthetic artifacts;
- initial database seed.

Primary deliverable:

> A reproducible seeded organization.

---

## Person B

Own:

- portfolio hierarchy;
- system risk cards;
- critical-gap count;
- drift indicators;
- filters;
- loading states;
- empty/error states.

Primary deliverable:

> A dashboard that already feels like the real product.

---

## Integration

Replace dashboard mock data with seeded backend data.

Exit condition:

> Dashboard loads real systems from FastAPI.

---

# 20. Phase 3 — Evidence + Knowledge Graph

## Person A

Own:

- artifact model;
- ingestion adapters;
- AI provider abstraction;
- structured extraction;
- Evidence persistence;
- coverage aggregation;
- graph service;
- graph DTO endpoint.

---

## Person B

Own:

- capability coverage table;
- engineer readiness badges;
- contextual graph;
- evidence drawer;
- provenance cards;
- declared-vs-demonstrated ownership UI.

---

## Integration

Start with one capability only:

```text
Payment Gateway
→ Incident Recovery
```

Validate:

```text
Alex    VALIDATED
Maria   ASSISTED
Jordan  EXPOSED
```

and show the supporting evidence.

Exit condition:

> The user can click “Why?” and see a defensible answer.

---

# 21. Phase 4 — Readiness + Risk

## Person A

Own:

- evidence-strength rules;
- evidence diversity;
- freshness;
- evidence confidence;
- readiness rules;
- capability exposure;
- Continuity Risk Index;
- fired-rule explanations.

---

## Person B

Own:

- risk visualization;
- exposure badge;
- readiness display;
- “Why this risk?” explanation;
- confidence display;
- insufficient-evidence UI.

---

## Integration

Verify that the frontend never computes:

- readiness;
- risk;
- confidence.

Exit condition:

> Risk is understandable and traceable.

---

# 22. Phase 5 — Simulation

## Person A

Own:

- baseline state;
- temporary graph/coverage snapshot;
- engineer-coverage removal;
- affected-capability recalculation;
- before/after risk;
- simulation endpoint;
- simulation tests.

---

## Person B

Own:

- engineer selector;
- simulation action;
- before/after layout;
- capability impact cards;
- risk transition;
- loading/error state.

---

## Integration Scenario

Use:

```text
ENGINEER_UNAVAILABLE
Engineer: Alex
Scope: Payment Gateway
```

Expected:

```text
Incident Recovery
DEGRADED → CRITICAL_GAP

Provider Failover
COVERED → DEGRADED

Retry Logic
COVERED → COVERED
```

Exit condition:

> The hackathon's core “what if?” experience works end-to-end.

---

# 23. Phase 6 — Candidate Comparison

## Person A

Own:

- candidate discovery;
- adjacent-capability lookup;
- technical-overlap logic;
- evidence support;
- strengths;
- gaps;
- top-three candidate response.

---

## Person B

Own:

- candidate cards;
- side-by-side comparison;
- evidence drill-down;
- manager selection;
- disclaimer that non-technical staffing factors are not modeled.

---

## Integration

Primary scenario:

```text
Incident Recovery gap
```

Expected:

```text
Maria  → HIGH technical overlap
Jordan → MEDIUM technical overlap
```

Do not present:

```text
Maria = 87% best employee
```

Exit condition:

> The manager receives technical decision support without automated staffing.

---

# 24. Phase 7 — Mitigation

## Person A

Own:

- context assembly;
- AI plan generation;
- structured plan validation;
- DRAFT persistence;
- approval endpoint.

---

## Person B

Own:

- plan screen;
- task cards;
- capability-gap explanation;
- approval interaction;
- approved state.

---

## Integration

Expected plan for Maria should focus on missing capabilities such as:

```text
Incident Recovery
Provider Failover
```

rather than:

```text
Learn everything Alex knows.
```

Exit condition:

> Risk becomes an actionable human-approved plan.

---

# 25. Phase 8 — Evaluation

## Person A

Lead:

- hidden-ground-truth evaluator;
- reconstruction comparison;
- critical-gap checks;
- simulation checks;
- backup-candidate checks.

---

## Person B

Cross-test:

- whether evaluation outputs match visible UI;
- whether claims are understandable;
- whether the app overstates uncertain evidence;
- whether source evidence actually supports displayed conclusions.

---

## Shared

Review every evaluation result together.

Do not manipulate rules just to make the demo answer look correct without understanding why.

Exit condition:

> The team can defend what was tested and what was not tested.

---

# 26. Phase 9 — Demo Hardening

Both developers work together.

Allowed work:

- bug fixes;
- copy improvements;
- visual consistency;
- deterministic seed data;
- performance improvements;
- loading states;
- error handling;
- accessibility fixes;
- demo pacing;
- responsible-AI wording.

Avoid adding major new features.

---

# 27. Phase 10 — Submission

Divide the writing but review together.

## Person A first draft

Suggested sections:

- architecture;
- AI approach;
- evidence model;
- risk engine;
- simulation;
- evaluation;
- technical setup.

## Person B first draft

Suggested sections:

- problem;
- product story;
- user journey;
- screenshots;
- demo flow;
- impact;
- UX;
- responsible-use explanation.

Then cross-review.

Both must understand the final README.

---

# 28. IBM Bob Working Model

Do not ask IBM Bob to build the whole application in one giant prompt.

Use Bob as a development partner on tightly scoped tasks.

Recommended pattern:

```text
Inspect relevant files.
Implement one clearly bounded task.
Run focused validation.
Update handoff notes.
Stop.
```

Example Person A task:

```text
Implement the Pydantic schemas for the frozen Simulation request and response
from docs/API_CONTRACT.md.

Do not implement simulation logic yet.

Add focused schema tests.
Do not change the API contract.
Stop when tests pass.
```

Example Person B task:

```text
Build the SimulationImpactCard component against the frozen mock simulation
response.

Do not connect the real API yet.
Do not redesign the simulation contract.
Stop when the component renders the three expected capability states.
```

Small prompts reduce unintended changes and merge conflicts.

---

# 29. Agent Handoff Rule

Whenever either developer uses IBM Bob or another coding agent for meaningful work, the task should end with a concise handoff containing:

```text
Completed
Files changed
Important decisions
Validation performed
Known issues
Remaining work
Recommended next task
```

This keeps the human teammate from having to reverse-engineer what the agent changed.

Use the repository-root file:

```text
HANDOFF.md
```

It sits alongside `BUILD_WITH_BOB.md` at the root so both are found without going looking.

Task-specific notes may also go in PR descriptions.

---

# 30. Communication Rule

Prefer concrete questions.

Bad:

> “Backend isn't working.”

Good:

> “`POST /api/v1/simulations` currently returns `before.risk`, but the frozen contract expects `before.continuity_risk_index`. Which implementation should we correct?”

Bad:

> “The graph feels wrong.”

Good:

> “The graph DTO gives Engineer → Capability edges, but the evidence drawer needs evidence IDs for the selected coverage relationship. Should we query the existing evidence endpoint rather than expand the graph contract?”

Precise communication keeps decisions small.

---

# 31. Blocking Rule

If a developer is blocked for more than approximately 20–30 minutes by something only the other developer can answer:

> Ask.

Do not silently invent a new contract.

But if the blocked item is internal to your own implementation:

> investigate first.

Avoid turning every minor coding decision into a meeting.

---

# 32. Decision Rule

Use three categories.

## Category A — Owner may decide alone

Examples:

- function name;
- local component structure;
- test helper;
- private implementation technique;
- internal refactor that preserves behavior.

---

## Category B — Tell teammate before merging

Examples:

- adding a library;
- changing significant internal module structure;
- changing mock infrastructure;
- modifying database implementation.

---

## Category C — Must decide together

Examples:

- API contract change;
- enum change;
- domain semantics;
- risk/readiness rule meaning;
- UI interpretation of risk;
- responsible-AI boundary;
- major product scope change.

---

# 33. Conflict Resolution

If both developers disagree:

### Step 1
State the actual decision.

### Step 2
List constraints from PRD/contracts.

### Step 3
Compare options based on:

```text
demo value
technical correctness
time
integration risk
explainability
responsible use
```

### Step 4
Choose the smallest solution that satisfies the MVP.

Avoid choosing based on:

> “This would be cooler.”

unless it improves the core story.

---

# 34. Scope-Control Rule

Any proposed feature must answer:

> Does this materially improve the golden path or judging story?

If no, defer it.

Examples likely deferred:

- live Slack;
- live Jira;
- HR integration;
- multiple simulation types;
- advanced people dashboard;
- graph database;
- automatic task assignment;
- real-time monitoring;
- complex RBAC;
- microservices.

---

# 35. Shared Definition of Done

A feature is not complete because one developer finished their half.

A feature is complete when:

```text
backend behavior exists
frontend behavior exists
contract matches
integration works
tests exist where valuable
loading/error states exist
golden path still works
```

---

# 36. Definition of Done Example — Simulation

Not done:

```text
Person A:
Simulation engine implemented.
```

Still not done:

```text
Person B:
Simulation mock UI implemented.
```

Done:

```text
Frontend sends Alex simulation request.
Backend calculates result.
Frontend renders actual result.
Expected capabilities change.
Error state works.
Tests pass.
Golden path continues.
```

---

# 37. Knowledge Sharing Rule

At least once per major phase, the primary owner explains the subsystem to the other person.

Examples:

Person A explains:

```text
How readiness is computed.
```

Person B explains:

```text
How simulation result state flows through the UI.
```

The goal is not equal expertise.

The goal is preventing:

> “Only one person knows how that works.”

That would be an ironic failure for a Bus Factor product.

---

# 38. Pairing Sessions

Pair only when pairing has high leverage.

Good pairing moments:

- first API integration;
- difficult schema mismatch;
- simulation integration;
- complicated graph behavior;
- final golden-path debugging;
- demo rehearsal.

Do not pair for every routine task.

Parallel work is still the default.

---

# 39. File Ownership

Ownership is not exclusive.

Person A primarily works in:

```text
backend/
data/
backend/tests/
```

Person B primarily works in:

```text
frontend/
```

Both work in:

```text
docs/
README.md
BUILD_WITH_BOB.md
```

Either person may fix another area after communicating.

---

# 40. Avoid Cross-Layer Shortcuts

Person B should not solve missing backend logic by calculating risk in React.

Person A should not solve UI problems by returning presentation-specific HTML.

Keep:

```text
Backend → domain truth
Frontend → presentation
```

---

# 41. Mock Data Ownership

Person B may create initial mock payloads based on `API_CONTRACT.md`.

Once Person A exposes the endpoint, compare:

```text
mock response
vs
real response
```

If they differ, the frozen contract decides which one is wrong.

Mock data must not become a second unofficial API specification.

---

# 42. Shared Demo Dataset

Use one canonical scenario:

```text
NovaPay Payments Platform
```

Primary system:

```text
Payment Gateway
```

Primary capability:

```text
Incident Recovery
```

Engineers:

```text
Alex
Maria
Jordan
```

This shared scenario should be used in:

- backend tests;
- frontend mocks;
- integration tests;
- screenshots;
- demo;
- evaluation explanation.

---

# 43. Demo Scenario Contract

Core story:

```text
Jordan is the declared owner.

Engineering evidence shows:
Alex has the strongest demonstrated Incident Recovery coverage.

Alex becomes unavailable.

ContinuityAI identifies:
Incident Recovery → CRITICAL_GAP

Maria is the strongest technical backup candidate.

Manager selects Maria.

ContinuityAI generates a targeted transfer plan.

Manager approves.
```

Do not casually change this story while developing unrelated features.

---

# 44. Bug Prioritization

Use:

## P0 — Demo blocker

Example:

```text
Simulation crashes.
```

Fix immediately.

---

## P1 — Core workflow incorrect

Example:

```text
Jordan displayed as VALIDATED when backend says EXPOSED.
```

Fix before new features.

---

## P2 — Important UX issue

Example:

```text
Evidence drawer is confusing.
```

Fix during current phase if possible.

---

## P3 — Cosmetic

Example:

```text
Spacing on secondary screen.
```

Polish later.

---

# 45. End-of-Phase Review

At the end of each phase, both developers answer:

```text
What is now truly working?
What is still mocked?
What is technically weak?
What could break the demo?
What have we learned?
Do any documents need updating?
What is the next smallest phase?
```

Then proceed.

---

# 46. Weekly or Major Milestone Review

For a short hackathon, do this every few days instead of literally weekly.

Review:

- scope;
- demo readiness;
- technical debt;
- test coverage;
- integration frequency;
- IBM Bob documentation;
- remaining time.

If behind schedule:

> Cut scope before cutting integration/testing.

---

# 47. What Not to Do

Do not:

```text
Person A builds backend for one week without integration.

Person B builds a completely separate fake frontend.

Change enums without telling each other.

Merge huge PRs.

Add major features during final polish.

Create different copies of the same domain types.

Let AI assign readiness directly.

Let frontend calculate risk.

Use the hidden ground truth at application runtime.

Treat missing evidence as proof of inability.

Add employee ranking.

Wait until submission day to write README.

Wait until the end to record a demo.
```

---

# 48. What Good Collaboration Looks Like

A healthy project should look like:

```text
Monday:
Both skeletons run.

Tuesday:
Dashboard uses real backend.

Wednesday:
Evidence and graph work.

Thursday:
Simulation works end-to-end.

Friday:
Candidate comparison works.

Saturday:
Mitigation works.

Sunday:
Evaluation, polish, demo.
```

Exact dates do not matter.

The pattern does:

> **Another thin end-to-end slice becomes real every day.**

---

# 49. Shared Quality Principles

Both developers should protect these principles.

## Evidence over assertion

Important conclusions must have provenance.

## Uncertainty over guessing

`INSUFFICIENT_EVIDENCE` is acceptable.

## Rules over fake AI precision

Readiness and risk remain deterministic.

## Systems over employee ranking

Risk belongs to technical continuity.

## Human decision over autonomous staffing

AI provides technical evidence and alternatives.

## Core workflow over feature count

A smaller coherent product beats six half-finished screens.

---

# 50. Daily Checklist

Before coding:

- [ ] Pull latest `main`.
- [ ] Read relevant contract.
- [ ] Confirm today's task.
- [ ] Confirm no overlapping file ownership conflict.

Before opening PR:

- [ ] Rebase or merge latest `main`.
- [ ] Run relevant tests.
- [ ] Verify contract.
- [ ] Self-review diff.
- [ ] Update handoff/PR notes.

Before ending day:

- [ ] Merge stable work.
- [ ] Run golden path.
- [ ] Record blockers.
- [ ] Decide tomorrow's integration target.

---

# 51. Phase Handoff Template

Use this after each phase.

```markdown
# Phase X Handoff

## Completed

## Person A
- ...

## Person B
- ...

## Integrated
- ...

## Still mocked
- ...

## Validation
- ...

## Known issues
- ...

## Contract changes
- None / list

## Demo status
- ...

## Next phase
- ...

## First task for Person A
- ...

## First task for Person B
- ...
```

---

# 52. Individual Task Handoff Template

When either person finishes a meaningful task:

```markdown
## Task Handoff

### Completed
- ...

### Files changed
- ...

### Decisions made
- ...

### Validation
- ...

### Remaining work
- ...

### Blockers
- ...

### Recommended next step
- ...
```

---

# 53. Recommended Initial Task Sequence

Once both developers begin Phase 1:

## Person A

### A1
Bootstrap FastAPI.

**Stop when:** health endpoint and test work.

### A2
Implement frozen enums and Pydantic DTOs.

**Stop when:** schemas validate examples.

### A3
Implement mock API routes.

**Stop when:** all frozen endpoints return valid payload shapes.

### A4
Set up SQLite and repositories.

**Stop when:** platform/system seed can be read through repository layer.

---

## Person B

### B1
Bootstrap Next.js + TypeScript.

**Stop when:** application runs.

### B2
Implement API types.

**Stop when:** mock payloads type-check.

### B3
Create mock service.

**Stop when:** components can request mock platform/system data.

### B4
Build dashboard shell.

**Stop when:** Payments Platform and Payment Gateway render.

---

# 54. First Shared Integration

As soon as A3 and B4 are complete:

Person A runs:

```text
FastAPI
```

Person B changes only the data adapter from:

```text
mock
```

to:

```text
/api/v1/platforms
```

If the dashboard needs major rewriting:

> the contract or implementation has drifted.

Fix that before continuing.

---

# 55. Shared Success Metric

Your collaboration is working if:

> **Person A can replace mocked intelligence with real intelligence without forcing Person B to rebuild the UI, and Person B can improve the experience without forcing Person A to redesign the domain engine.**

That is the real purpose of all the Phase 0 work.

---

# 56. Final Working Agreement

Person A and Person B agree to:

1. protect the frozen contracts;
2. own different areas but understand the shared product;
3. work in parallel rather than sequentially;
4. integrate continuously;
5. merge small changes;
6. communicate blocking contract issues immediately;
7. protect the golden path;
8. stop feature work when the core flow is broken;
9. use AI coding agents for narrow, reviewable tasks;
10. maintain handoff notes for meaningful agent-assisted work;
11. make technical continuity conclusions evidence-backed;
12. keep staffing decisions human-controlled;
13. prioritize a working, defensible demo over unnecessary scope;
14. keep `main` runnable;
15. finish each phase with an integrated product, not two disconnected halves.

---

# 57. One-Sentence Team Rule

If the team remembers only one rule, use this:

> **Build separately, integrate daily, and never let either the code or the knowledge of the project become a single point of failure.**
