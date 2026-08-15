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
