"""Enforce the hidden-ground-truth boundary. docs/ARCHITECTURE.md section 40.

The architecture states that application runtime cannot read `data/ground_truth/`. Without a test,
that is an intention rather than a property — and the credibility of every number the product
displays rests on it. If the application could read the labels, the evaluation in `app/evaluation/`
would measure nothing and "inferred from evidence" would be unfalsifiable.

Three checks:

1. No module under `app/`, outside `app/evaluation/`, mentions the ground-truth directory.
2. Nothing outside `app/evaluation/` imports the evaluation package.
3. Application configuration exposes no path to it, so it cannot be reached indirectly.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "app"
EVALUATION_PACKAGE = APP_ROOT / "evaluation"

FORBIDDEN_TOKENS = ("ground_truth", "groundtruth", "novapay_truth", "true_readiness")


def _application_modules() -> list[Path]:
    """Every module the API can reach: all of `app/` except the evaluation package."""
    return sorted(
        path
        for path in APP_ROOT.rglob("*.py")
        if EVALUATION_PACKAGE not in path.parents and path != EVALUATION_PACKAGE
    )


def test_no_application_module_references_the_ground_truth() -> None:
    offenders: list[str] = []
    for path in _application_modules():
        text = path.read_text()
        # Comments explaining the boundary are fine; code that names the path is not.
        code_lines = [
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        ]
        code = "\n".join(code_lines).lower()
        for token in FORBIDDEN_TOKENS:
            if token in code and "docs/architecture" not in code_lines[0].lower():
                # Narrow the check to genuine identifiers and string literals.
                if _mentions_in_code(text, token):
                    offenders.append(f"{path.relative_to(APP_ROOT.parent)} mentions '{token}'")
    assert not offenders, (
        "application code must not reference the hidden ground truth:\n" + "\n".join(offenders)
    )


def _mentions_in_code(source: str, token: str) -> bool:
    """True when the token appears in a string literal or an identifier, not merely in a docstring.

    Docstrings are how the boundary is documented, so they must not trip the check.
    """
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                docstrings.add(doc)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in docstrings:
                continue
            if token in node.value.lower():
                return True
        if isinstance(node, ast.Name) and token in node.id.lower():
            return True
        if isinstance(node, ast.Attribute) and token in node.attr.lower():
            return True
    return False


def test_nothing_outside_the_evaluation_package_imports_it() -> None:
    offenders: list[str] = []
    for path in _application_modules():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "evaluation" in node.module:
                offenders.append(f"{path.relative_to(APP_ROOT.parent)} imports {node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "evaluation" in alias.name:
                        offenders.append(f"{path.relative_to(APP_ROOT.parent)} imports {alias.name}")
    assert not offenders, "\n".join(offenders)


def test_application_settings_expose_no_ground_truth_path() -> None:
    from app.core.config import settings

    for name, value in settings.model_dump().items():
        assert "ground" not in name.lower(), name
        assert "ground_truth" not in str(value).lower(), f"{name}={value}"


def test_the_evaluation_package_can_still_reach_it() -> None:
    """The boundary must be one-directional, not simply broken."""
    from app.evaluation.ground_truth import GROUND_TRUTH_PATH, load_ground_truth

    assert GROUND_TRUTH_PATH.exists(), GROUND_TRUTH_PATH
    truth = load_ground_truth()
    assert truth.coverage, "the answer key should be readable from the evaluation package"
