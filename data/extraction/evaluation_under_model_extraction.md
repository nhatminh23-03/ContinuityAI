# ContinuityAI — Evaluation Report

**Generated:** 2026-08-24T20:14:59+00:00  
**Rule version:** 1.0  
**Dataset:** 520 synthetic artifacts, generator 1.0, seed 20260815  
**Reference date:** 2026-08-15

> Controlled prototype validation against a synthetic organisation with hidden ground truth. The generator emits evidence patterns chosen to be classifiable, so these figures measure whether the pipeline is self-consistent end to end — ingestion, extraction, aggregation, readiness, exposure, risk. They are NOT evidence of real-world accuracy and must not be quoted as such (PRD section 25.3).

## Results

| Check | Passed | Total | Rate |
|---|---:|---:|---:|
| Knowledge reconstruction (engineer-capability readiness) | 54 | 56 | 96.4% |
| Capability exposure classification | 24 | 25 | 96.0% |
| Critical gap detection (no misses, no false positives) | 2 | 2 | 100.0% |
| Declared-versus-demonstrated ownership mismatch | 1 | 1 | 100.0% |
| Counterfactual simulation | 15 | 25 | 60.0% |
| Backup candidate recommendation | 1 | 2 | 50.0% |
| Evidence grounding (every coverage claim cites a source) | 62 | 62 | 100.0% |

## Detail

### Knowledge reconstruction (engineer-capability readiness) — attention

- note: 1 of 2 miss(es) are within one bucket
- 2 discrepancy(ies):
  - eng_jordan_lee / cap_incident_recovery: expected EXPOSED, inferred PRACTICED (2 buckets out)
  - eng_maria_gomez / cap_incident_recovery: expected ASSISTED, inferred PRACTICED (1 bucket out)

### Capability exposure classification — attention

- 1 discrepancy(ies):
  - cap_incident_recovery: expected DEGRADED, got COVERED

### Critical gap detection (no misses, no false positives) — pass

- no discrepancies

### Declared-versus-demonstrated ownership mismatch — pass

- no discrepancies

### Counterfactual simulation — attention

- 10 discrepancy(ies):
  - before.continuity_risk_index: expected 74, got 72
  - before.degraded_capability_count: expected 2, got 1
  - before.covered_capability_count: expected 3, got 4
  - after.continuity_risk_index: expected 93, got 91
  - after.critical_gap_count: expected 2, got 1
  - after.covered_capability_count: expected 2, got 3
  - cap_certificate_management.remaining_best_readiness: expected EXPOSED, got ASSISTED
  - cap_incident_recovery.before: expected DEGRADED, got COVERED
  - cap_incident_recovery.after: expected CRITICAL_GAP, got COVERED
  - cap_incident_recovery.remaining_best_readiness: expected ASSISTED, got PRACTICED

### Backup candidate recommendation — attention

- note: cap_incident_recovery: additional candidates returned: ['eng_omar_haddad']
- 1 discrepancy(ies):
  - cap_incident_recovery/eng_jordan_lee: expected overlap MEDIUM, got HIGH

### Evidence grounding (every coverage claim cites a source) — pass

- no discrepancies

## What this does not test

- Whether the readiness heuristics reflect real human expertise. They are prototype
  thresholds for transparent demo logic (PRD section 16.2), not calibrated standards.
- Extraction quality on unseen prose. The shipped provider resolves capabilities by
  matching names and aliases in the artifact text, so it finds what the text names and
  nothing more (RECOMMENDATIONS.md R-01).
- Anything about real people. Every engineer, artifact, and incident here is synthetic.

