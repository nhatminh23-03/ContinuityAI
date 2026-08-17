"""Render an evaluation report. PRD section 25.3.

The reporting policy is part of the deliverable, not decoration: state what was tested, state the
dataset and rule version, and do not dress a synthetic result up as real-world accuracy. The
caveat is printed inside the report so it travels with the numbers.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.evaluation.evaluator import EvaluationReport

CAVEAT = (
    "Controlled prototype validation against a synthetic organisation with hidden ground truth. "
    "The generator emits evidence patterns chosen to be classifiable, so these figures measure "
    "whether the pipeline is self-consistent end to end — ingestion, extraction, aggregation, "
    "readiness, exposure, risk. They are NOT evidence of real-world accuracy and must not be "
    "quoted as such (PRD section 25.3)."
)


def _dataset_summary() -> dict:
    manifest_path = settings.data_path / "synthetic" / "manifest.json"
    if not manifest_path.exists():
        return {}
    manifest = json.loads(manifest_path.read_text())
    return {
        "total_artifacts": manifest.get("total_artifacts"),
        "generator_version": manifest.get("generator_version"),
        "random_seed": manifest.get("random_seed"),
        "reference_date": manifest.get("reference_date"),
    }


def to_markdown(report: EvaluationReport, rule_version: str = "1.0") -> str:
    dataset = _dataset_summary()
    lines = [
        "# ContinuityAI — Evaluation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat(timespec='seconds')}  ",
        f"**Rule version:** {rule_version}  ",
        f"**Dataset:** {dataset.get('total_artifacts', 'unknown')} synthetic artifacts, "
        f"generator {dataset.get('generator_version', '?')}, seed {dataset.get('random_seed', '?')}  ",
        f"**Reference date:** {dataset.get('reference_date', '?')}",
        "",
        "> " + CAVEAT.replace("\n", " "),
        "",
        "## Results",
        "",
        "| Check | Passed | Total | Rate |",
        "|---|---:|---:|---:|",
    ]
    for check in report.checks:
        lines.append(
            f"| {check.name} | {check.passed} | {check.total} | {check.rate * 100:.1f}% |"
        )

    lines += ["", "## Detail", ""]
    for check in report.checks:
        status = "pass" if check.ok else "attention"
        lines.append(f"### {check.name} — {status}")
        lines.append("")
        if check.notes:
            for note in check.notes:
                lines.append(f"- note: {note}")
        if check.failures:
            lines.append(f"- {len(check.failures)} discrepancy(ies):")
            for failure in check.failures:
                lines.append(f"  - {failure}")
        elif not check.notes:
            lines.append("- no discrepancies")
        lines.append("")

    lines += [
        "## What this does not test",
        "",
        "- Whether the readiness heuristics reflect real human expertise. They are prototype",
        "  thresholds for transparent demo logic (PRD section 16.2), not calibrated standards.",
        "- Extraction quality on unseen prose. The shipped provider resolves capabilities by",
        "  matching names and aliases in the artifact text, so it finds what the text names and",
        "  nothing more (RECOMMENDATIONS.md R-01).",
        "- Anything about real people. Every engineer, artifact, and incident here is synthetic.",
        "",
    ]
    return "\n".join(lines)


def to_json(report: EvaluationReport, rule_version: str = "1.0") -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule_version": rule_version,
        "dataset": _dataset_summary(),
        "caveat": CAVEAT,
        "all_passed": report.all_passed,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "total": check.total,
                "rate": round(check.rate, 4),
                "failures": check.failures,
                "notes": check.notes,
            }
            for check in report.checks
        ],
    }


def write(report: EvaluationReport, output_dir: Path | None = None) -> tuple[Path, Path]:
    target = output_dir or (settings.data_path / "generated")
    target.mkdir(parents=True, exist_ok=True)
    markdown_path = target / "evaluation_report.md"
    json_path = target / "evaluation_report.json"
    markdown_path.write_text(to_markdown(report) + "\n")
    json_path.write_text(json.dumps(to_json(report), indent=2) + "\n")
    return markdown_path, json_path
