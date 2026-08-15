"""Source adapters: external records in, normalised `ArtifactInput` out.

docs/ARCHITECTURE.md sections 17-18. An adapter's only job is normalisation — no interpretation,
no capability attribution, no scoring. Its output is not yet Evidence.

Two adapters ship:

* `load_synthetic_corpus` reads the generated NovaPay corpus in `data/synthetic/`.
* `load_normalised_github_export` reads a public GitHub export that has already been flattened
  to the same shape offline.

The second is the seam for real public GitHub evidence (PRD section 14.1). It takes a
pre-normalised file rather than calling the API, because a demo that depends on a live third
party at judging time is a demo that can fail for reasons unrelated to the product
(docs/ARCHITECTURE.md section 85). See RECOMMENDATIONS.md R-07.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.ai.schemas import ArtifactInput, ArtifactParticipant
from app.schemas.enums import EvidenceSourceType

# file stem -> (source type, provenance label)
SYNTHETIC_SOURCES: dict[str, tuple[EvidenceSourceType, str]] = {
    "incidents": (EvidenceSourceType.INCIDENT, "synthetic_incident_dataset"),
    "pull_requests": (EvidenceSourceType.PULL_REQUEST, "synthetic_repository_export"),
    "code_reviews": (EvidenceSourceType.CODE_REVIEW, "synthetic_repository_export"),
    "issues": (EvidenceSourceType.ISSUE, "synthetic_issue_dataset"),
    "tickets": (EvidenceSourceType.TICKET, "synthetic_ticket_dataset"),
    "documents": (EvidenceSourceType.DOCUMENT, "synthetic_document_dataset"),
}


def artifact_id_for(source_reference: str) -> str:
    return f"artifact_{normalise_reference(source_reference)}"


def normalise_reference(source_reference: str) -> str:
    """`INC-184` -> `inc_184`. Drives artifact and evidence identifiers.

    Deterministic and human-debuggable, which is why the frozen fixtures can pin
    `evidence_inc_184` at all. docs/ENGINEERING_RULES.md, conventions.
    """
    return source_reference.strip().lower().replace("-", "_").replace(" ", "_").replace("/", "_")


def _to_artifact(
    record: dict, source_type: EvidenceSourceType, provenance: str
) -> ArtifactInput:
    reference = record["reference"]
    return ArtifactInput(
        artifact_id=artifact_id_for(reference),
        source_type=source_type,
        source_reference=reference,
        title=record.get("title"),
        body=record.get("body", ""),
        artifact_date=date.fromisoformat(record["date"]),
        participants=[
            ArtifactParticipant(
                engineer_id=p["engineer_id"], participant_role=p["participant_role"]
            )
            for p in record.get("participants", [])
        ],
        system_hint=record.get("system_id"),
        file_paths=list(record.get("file_paths", [])),
        provenance_source=record.get("provenance_source", provenance),
        source_url=record.get("source_url"),
    )


def load_synthetic_corpus(data_path: Path) -> list[ArtifactInput]:
    synthetic_dir = data_path / "synthetic"
    if not synthetic_dir.exists():
        raise FileNotFoundError(
            f"{synthetic_dir} is missing. Run: python backend/scripts/generate_synthetic_data.py"
        )

    artifacts: list[ArtifactInput] = []
    for stem, (source_type, provenance) in sorted(SYNTHETIC_SOURCES.items()):
        path = synthetic_dir / f"{stem}.json"
        if not path.exists():
            continue
        for record in json.loads(path.read_text()):
            artifacts.append(_to_artifact(record, source_type, provenance))

    # Stable order so evidence identifiers and simulation ids are reproducible across runs.
    artifacts.sort(key=lambda a: (a.artifact_date, a.source_reference))
    return artifacts


def load_normalised_github_export(path: Path) -> list[ArtifactInput]:
    """Real public GitHub evidence, normalised offline into the shape above.

    Expected record fields: `reference`, `title`, `body`, `date`, `system_id`, `participants`
    (with `participant_role` of AUTHOR or REVIEWER), `file_paths`, optional `source_url`, and
    `kind` of `pull_requests`, `code_reviews`, `issues`, or `commits`.
    """
    if not path.exists():
        return []

    kind_map = {
        "pull_requests": EvidenceSourceType.PULL_REQUEST,
        "code_reviews": EvidenceSourceType.CODE_REVIEW,
        "issues": EvidenceSourceType.ISSUE,
        "commits": EvidenceSourceType.COMMIT,
    }
    artifacts: list[ArtifactInput] = []
    for record in json.loads(path.read_text()):
        source_type = kind_map.get(record.get("kind", "pull_requests"), EvidenceSourceType.PULL_REQUEST)
        artifacts.append(_to_artifact(record, source_type, "public_github_export"))
    return artifacts


def load_declared_ownership(data_path: Path) -> list[dict]:
    """CODEOWNERS entries.

    Declared ownership arrives as an ingested artifact with provenance rather than as a
    hardcoded field, because the demo's opening beat is precisely the gap between what
    CODEOWNERS says and what the evidence shows. A hardcoded owner would make that gap an
    assertion instead of a finding.
    """
    path = data_path / "synthetic" / "codeowners.json"
    if not path.exists():
        return []
    return list(json.loads(path.read_text()).get("entries", []))
