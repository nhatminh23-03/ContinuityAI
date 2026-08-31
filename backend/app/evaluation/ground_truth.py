"""The only module permitted to read the hidden ground truth.

docs/ARCHITECTURE.md section 40 draws the boundary; this module is the single door through it.
`app/core/config.py` deliberately exposes no ground-truth path, so nothing outside `app/evaluation/`
can even name the directory, and `tests/test_ground_truth_isolation.py` fails the build if any
module under `app/` other than this package mentions it.

Why the isolation is the experiment rather than a formality: the product's claim is that readiness
is *inferred from evidence*. If the application could read the labels, every number it displayed
would be unfalsifiable and the comparison below would measure nothing at all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Resolved here, not in application configuration, on purpose.
GROUND_TRUTH_PATH = Path(__file__).resolve().parents[3] / "data" / "ground_truth" / "novapay_truth.json"


@dataclass
class CoverageLabel:
    engineer_id: str
    capability_id: str
    true_readiness: str
    evidence_profile: str = "default"


@dataclass
class GroundTruth:
    coverage: list[CoverageLabel] = field(default_factory=list)
    expected_capability_exposure: dict[str, str] = field(default_factory=dict)
    expected_declared_owner_mismatch: list[str] = field(default_factory=list)
    expected_simulation: dict = field(default_factory=dict)
    expected_backup_candidates: dict = field(default_factory=dict)
    # Artifacts written to fool the rules, and the constraint each one must not breach.
    # RECOMMENDATIONS.md R-02. Kept here rather than in the corpus so the answer key stays on the
    # hidden side of the boundary: the traps are visible to anyone reading `data/synthetic/`, but what
    # they are supposed to *fail* to do is not.
    adversarial_artifacts: list[dict] = field(default_factory=list)

    @property
    def by_pair(self) -> dict[tuple[str, str], str]:
        return {(c.engineer_id, c.capability_id): c.true_readiness for c in self.coverage}

    @property
    def expected_critical_gaps(self) -> set[str]:
        return {
            capability_id
            for capability_id, exposure in self.expected_capability_exposure.items()
            if exposure == "CRITICAL_GAP"
        }

    @property
    def expected_insufficient_evidence(self) -> set[str]:
        return {
            capability_id
            for capability_id, exposure in self.expected_capability_exposure.items()
            if exposure == "INSUFFICIENT_EVIDENCE"
        }


def load_ground_truth(path: Path | None = None) -> GroundTruth:
    source = path or GROUND_TRUTH_PATH
    if not source.exists():
        raise FileNotFoundError(f"{source} is missing.")
    payload = json.loads(source.read_text())
    return GroundTruth(
        coverage=[
            CoverageLabel(
                engineer_id=entry["engineer_id"],
                capability_id=entry["capability_id"],
                true_readiness=entry["true_readiness"],
                evidence_profile=entry.get("evidence_profile", "default"),
            )
            for entry in payload.get("coverage", [])
        ],
        expected_capability_exposure=payload.get("expected_capability_exposure", {}),
        expected_declared_owner_mismatch=payload.get("expected_declared_owner_mismatch", []),
        expected_simulation=payload.get("expected_simulation", {}),
        expected_backup_candidates=payload.get("expected_backup_candidates", {}),
        adversarial_artifacts=payload.get("adversarial_artifacts", []),
    )
