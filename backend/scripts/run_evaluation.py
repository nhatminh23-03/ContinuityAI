"""Compare the seeded application state against the hidden ground truth.

    python -m scripts.run_evaluation        # from backend/

Writes `data/generated/evaluation_report.{md,json}` and prints a summary. Requires a seeded
database: run `python -m scripts.seed_demo` first.

This script and the data generator are the only two places that read `data/ground_truth/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.db.session import session_scope  # noqa: E402
from app.evaluation import evaluate, load_ground_truth, write  # noqa: E402


def main() -> int:
    truth = load_ground_truth()
    with session_scope() as session:
        report = evaluate(session, truth)

    markdown_path, json_path = write(report)

    print("evaluation\n" + "=" * 72)
    for check in report.checks:
        status = "PASS" if check.ok else "----"
        print(f"  [{status}] {check.name}: {check.passed}/{check.total} ({check.rate * 100:.1f}%)")
        for note in check.notes:
            print(f"          note: {note}")
        for failure in check.failures[:8]:
            print(f"          - {failure}")
        if len(check.failures) > 8:
            print(f"          ... and {len(check.failures) - 8} more")

    print("=" * 72)
    print(f"report: {markdown_path.relative_to(REPO_ROOT)}")
    print(f"        {json_path.relative_to(REPO_ROOT)}")
    print("\nThese are synthetic-dataset results. Do not quote them as real-world accuracy.")
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
