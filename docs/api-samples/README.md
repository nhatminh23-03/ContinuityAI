# API samples — captured live backend payloads

Captured 2026-08-17 from `uvicorn app.main:app` on a freshly reseeded database
(`python -m scripts.seed_demo`, provider `deterministic`). Each file is the verbatim JSON body of
one call; `manifest.json` records the method, path, request body, and HTTP status for every
capture. The database was reseeded again after capture, so the mutating calls (plan approval,
challenge) left no residue.

These are observations, not a specification. `docs/API_CONTRACT.md` remains authoritative; where a
sample and the contract disagree, the sample documents a defect.

| File | Endpoint | Status |
|---|---|---|
| `health.json` | `GET /health` | 200 |
| `platforms.json` | `GET /api/v1/platforms` | 200 |
| `payments-systems.json` | `GET /api/v1/platforms/platform_payments/systems` | 200 |
| `identity-systems.json` | `GET /api/v1/platforms/platform_identity/systems` | 200 |
| `payment-gateway.json` | `GET /api/v1/systems/system_payment_gateway` | 200 |
| `payment-gateway-graph.json` | `GET /api/v1/systems/{id}/graph` | 200 |
| `payment-gateway-graph-focused.json` | same, `?focus_capability_id=cap_incident_recovery` | 200 |
| `incident-recovery.json` | `GET /api/v1/capabilities/cap_incident_recovery` | 200 |
| `incident-recovery-evidence.json` | `GET /api/v1/capabilities/{id}/evidence` | 200 |
| `incident-recovery-evidence-alex.json` | same, `?engineer_id=eng_alex_chen` | 200 |
| `alex-simulation.json` | `POST /api/v1/simulations` (Alex unavailable, SYSTEM scope) | 200 |
| `backup-candidates.json` | `POST /api/v1/recommendations/backup-candidates` | 200 |
| `mitigation-plan.json` | `POST /api/v1/mitigation-plans` | 201 |
| `mitigation-plan-approved.json` | `POST /api/v1/mitigation-plans/plan_001/approve` (with edited `tasks`, CI-12) | 200 |
| `permission-audit-insufficient.json` | `INSUFFICIENT_EVIDENCE` designed state — null index and class | 200 |
| `sofia-simulation-no-loss.json` | simulation losing no coverage — empty `capability_impacts` | 200 |
| `challenge-attest-jordan.json` | `POST /api/v1/capabilities/{id}/challenge` (DEC-10, attestation) | 201 |
| `error-404-unknown-system.json` | unknown id → `NOT_FOUND` envelope | 404 |
| `error-422-platform-scope.json` | `PLATFORM` scope → `VALIDATION_ERROR` (CI-22) | 422 |
| `error-422-candidate-limit.json` | `limit: 9` → `VALIDATION_ERROR` (framework-level) | 422 |
| `error-double-approve.json` | approving an `APPROVED` plan → `VALIDATION_ERROR` | 422 |

Notes for consumers:

- Nine of the ten golden-path payloads are byte-identical to the shared `fixtures/`; the tenth
  (`mitigation-plan-approved.json`) differs only in `approved_at`, which the fixture pins to an
  illustrative instant.
- The approve response does not echo the task list; the edited tasks submitted with the approval
  are persisted server-side but there is no GET endpoint to read a plan back.
- `error-422-candidate-limit.json` shows the framework-level validation envelope: `details.errors`
  is a stringified list, unlike the structured `details` of domain-raised errors.
