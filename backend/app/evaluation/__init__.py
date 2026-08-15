"""Evaluation against hidden ground truth.

Separated from production domain logic (docs/ARCHITECTURE.md section 39) and the only package
allowed to read `data/ground_truth/`. Nothing the API serves imports from here.
"""

from .evaluator import CheckResult, EvaluationReport, evaluate
from .ground_truth import GroundTruth, load_ground_truth
from .report import to_json, to_markdown, write

__all__ = [
    "CheckResult",
    "EvaluationReport",
    "GroundTruth",
    "evaluate",
    "load_ground_truth",
    "to_json",
    "to_markdown",
    "write",
]
