# ContinuityAI — Specification Index

Start with [`ENGINEERING_RULES.md`](ENGINEERING_RULES.md). It is a working reference distilled
from everything below, and it is enough for most day-to-day work. Come back here when you need
the reasoning behind a rule, or when a rule does not cover your case.

---

## Authority

Authority is split by subject, not by document rank. A flat ranking would let the PRD silently
override frozen enums and field names.

| Subject | Authoritative document |
|---|---|
| Product scope, user journey, UX requirements, acceptance criteria | `PRD.md` |
| Wire format — endpoints, field names, enum spelling, JSON shape | `API_CONTRACT.md` |
| Internal semantics — entity meaning, invariants, rule intent | `DOMAIN_MODEL.md` |
| Module layout, technology, testing, deployment | `ARCHITECTURE.md` |
| Process, ownership, decision categories | `TEAM_WORKFLOW_PERSON_A_B.md` |

Current implementation is never authoritative over any of them. Where the PRD requires behaviour
the contract cannot carry, the contract is amended — it is not overridden.

---

## The documents

### `PRD.md`
**Authority:** product scope, user journey, UX requirements, functional requirements, acceptance
criteria.
**Consult when:** you need to know what a screen must show, what counts as done, who the user is,
or whether something is in scope. Functional requirements are `FR-nnn`; acceptance criteria are
`AC-nn`. The three-minute demo script in §27 is the definition of the golden path.
**Do not use it for:** endpoint paths, field names, or enum spelling. §24's API outline predates
the frozen contract and is retained only as design history.

### `API_CONTRACT.md`
**Authority:** everything that crosses the frontend/backend boundary — the 10 frozen endpoints,
DTO shapes, field names, enum values, error envelope, JSON casing, ID format.
**Consult when:** you are writing a fixture, a TypeScript type, a Pydantic schema, or an API
call. This is the document both developers build against in parallel.
**Change control:** §17. No field, path, or enum changes without both developers agreeing and a
matching entry in `DECISIONS.md`.

### `DOMAIN_MODEL.md`
**Authority:** what the product means internally — entity definitions, invariants, readiness and
exposure semantics, graph node and edge meaning, the responsible-AI and employment-decision
boundaries.
**Consult when:** you need to know what `PRACTICED` actually means, why exposure is separate from
risk, or whether a field belongs in the domain at all. §47's invariant list is the shortest
statement of what the product is.
**Note:** internal persistence models may legitimately differ from the API DTOs.

### `ARCHITECTURE.md`
**Authority:** module layout, technology choices, layering, testing strategy, deployment,
performance expectations.
**Consult when:** you are deciding where a file goes, whether to add a library, or how a subsystem
should be tested. §93 lists what is frozen; §94 lists what is deliberately deferred.

### `TEAM_WORKFLOW_PERSON_A_B.md`
**Authority:** how the two developers work — ownership, branching, review, integration rhythm,
decision categories, scope control.
**Consult when:** you are unsure whether a decision is yours alone (Category A), needs a heads-up
(Category B), or needs both developers (Category C). §32 has the categories; §43 has the demo
scenario contract.

### `DECISIONS.md`
**Authority:** the record of Category C decisions, including every resolution from the Phase 0
contract audit.
**Consult when:** you want to know why a specification says what it says, or whether a question
has already been settled. Check the Open items table before raising something as new.
**Append to it** whenever a Category C decision is made. Do not rewrite past entries.

### `CONTRACT_ISSUES.md`
**Authority:** none. Historical record.
**Consult when:** you want the full evidence behind a Phase 0 resolution — it quotes each
document's original wording before the amendments were applied. Resolutions live in
`DECISIONS.md`; this file is deliberately not updated to match the current specifications.

### `ENGINEERING_RULES.md`
**Authority:** none of its own — it restates the documents above.
**Consult when:** starting any task. If it and an authoritative document disagree, the
authoritative document wins and `ENGINEERING_RULES.md` gets fixed.

### `archive/`
Non-authoritative exports kept for reference. `ContinuityAI_PRD_v1.0.docx` is a stale copy of the
PRD from before the Phase 0 audit; `PRD.md` is the live document.

---

## Related files outside `docs/`

| File | Purpose |
|---|---|
| `../fixtures/` | Shared mock payloads. Jointly owned; both sides validate against them. Must conform exactly to `API_CONTRACT.md`. |
| `../BUILD_WITH_BOB.md` | Development log — what was built, which requirement it implements, how it was validated. |
| `../HANDOFF.md` | Session handoff notes. Assumes the next session starts with no memory. |
| `../README.md` | Submission README — problem, solution, AI approach, challenge theme, tooling, setup, demo. |
