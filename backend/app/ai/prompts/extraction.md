# Extraction prompt — v1

Versioned per the Definition of Done in PRD section 26.1 ("AI prompts/output schemas are
versioned and validated"). The shipped `DeterministicProvider` does not consume this file; it is
the specification a model-backed provider must satisfy, and it is kept beside the code so the
two cannot drift apart silently.

## Task

You are given one engineering artifact and a closed list of capabilities belonging to the
artifact's system. Decide what the artifact **demonstrates** about the engineers recorded as
participants.

## Hard constraints

1. Return only capabilities from the supplied list. Never invent one. If nothing matches, return
   an empty `claims` array — that is a correct answer, not a failure.
2. Attribute claims only to engineers in the artifact's `participants` list.
3. Do not output readiness, risk, seniority, employee value, or a recommendation. You classify
   individual artifacts. Aggregation and scoring happen downstream in deterministic rules.
4. One claim per `(capability, engineer)` pair.
5. Every claim carries a `rationale` naming the text that justified it. Uncited claims are
   rejected by `app/ai/validation.py`.
6. If the text names more than one capability and you cannot tell which the work targeted, say so
   in `ambiguity` rather than choosing.

## Evidence roles

| Role | Use when |
|---|---|
| `EXPOSURE` | Reviewed, commented, observed, discussed. No execution shown. |
| `CONTRIBUTION` | Implemented or changed something relevant, without evidence of independent operational execution. |
| `ASSISTED_EXECUTION` | Performed the work with another person leading or providing significant support. |
| `INDEPENDENT_EXECUTION` | Performed the work without significant support. The strongest claim available. |
| `KNOWLEDGE_CAPTURE` | Authored or substantially revised a runbook, architecture document, or operational guidance. |

Do not set `evidence_strength` from your own judgement — it is derived from the role and will be
overwritten if it disagrees.

## Participant roles

`participant_role` comes from the source system and is factual. An incident platform records who
resolved an incident and who assisted. Use it as the primary signal, and the text as
corroboration. Where the text contradicts the recorded role, prefer the recorded role and note
the discrepancy in `ambiguity`.

## Language

Never phrase an absence as an inability. "No qualifying independent recovery evidence was found"
is correct; "cannot recover the system" is prohibited (PRD section 22.3).

## Output

A single JSON object matching `ArtifactExtraction` in `app/ai/schemas.py`. No prose outside the
JSON. Output failing schema validation is rejected as `AI_EXTRACTION_FAILED` rather than being
partially accepted.
