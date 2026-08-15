# Hidden ground truth — do not read from application code

`novapay_truth.json` holds the **true** simulated readiness distribution for the NovaPay demo
organisation. It is the answer key.

## The rule

```
data/ground_truth/   →  readable by  backend/scripts/generate_synthetic_data.py
                                     backend/app/evaluation/*
                                     backend/scripts/run_evaluation.py

                     →  NOT readable by  anything the API serves
```

`docs/ARCHITECTURE.md` section 40 states the boundary. Three things enforce it rather than
merely asserting it:

1. **No configuration path.** `app/core/config.py` deliberately exposes no ground-truth path.
   Only `app/evaluation/ground_truth.py` resolves one, and nothing outside `app/evaluation/`
   imports that module.
2. **A test.** `backend/tests/test_ground_truth_isolation.py` walks every module under
   `backend/app/`, excluding `app/evaluation/`, and fails if any of them mentions the
   directory, imports the evaluation package, or reads the file.
3. **Direction of dependency.** The generator writes artifacts into `data/synthetic/`. The seed
   reads `data/org/` and `data/synthetic/` only. Readiness is always recomputed from evidence.

## Why it matters

The product's central claim is that readiness is *inferred from evidence*. If the application
could read the labels, every number it displays would be unfalsifiable and the evaluation in
`app/evaluation/` would measure nothing. The isolation is the experiment.

## What is in the file

| Key | Purpose |
|---|---|
| `coverage` | The true `(engineer, capability) → readiness` label the generator emits artifacts for. |
| `expected_capability_exposure` | What the continuity rules should conclude per capability. |
| `expected_simulation` | The expected before/after for the hero counterfactual. |
| `expected_backup_candidates` | Which engineers should surface, and at what technical overlap. |
| `expected_declared_owner_mismatch` | Systems where declared ownership should not match demonstrated coverage. |

`evidence_profile` on a coverage entry steers generation without changing the label:
`aging` emits older artifacts, `sparse` emits too few to support a responsible assessment
(which is how `cap_permission_audit` reaches `INSUFFICIENT_EVIDENCE` and satisfies AC-12).

## Honest limitation

The generator emits evidence patterns chosen to be classifiable, so the reconstruction metric
measures whether the pipeline is *self-consistent* end to end — ingestion, extraction,
aggregation, readiness, exposure, risk — not whether the readiness heuristics match real human
expertise. Nothing here is evidence of real-world accuracy. See `RECOMMENDATIONS.md` R-02.
