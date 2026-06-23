"""Workflow-library contract tests.

These tests enforce the structural invariants documented in
``openspec/specs/bdd-workflow-reuse/spec.md`` and
``openspec/changes/bdd-workflow-reuse-helpers/design.md``
(Decision 2 — per-workflow carve-out). They run as part of
``task test-unit`` (no DB, no HTTP, no Playwright) so a
contributor who violates the contract on a refactor sees the
failure in the unit-tier feedback loop rather than after a full
BDD run.

Tests
------

``test_workflow_count_under_ceiling``
    ``_workflows.py`` exposes ≤10 public callables. Beyond that,
    the suite's extraction thesis (one workflow per repeated
    multi-step setup) breaks down and the file becomes a god
    module.

``test_carve_out_files_use_inline_steps``
    ``login.feature`` and ``profile_isolation.feature`` are
    carve-out files — they MUST NOT use the
    ``login_and_pick_profile`` or ``switch_profile`` wrappers,
    because they're testing the auth flow itself. The contract
    parses the feature files via ``pytest-bdd`` and asserts no
    scenario contains a step whose text matches the wrapper
    regexes.

``test_wrappers_delegate_to_workflows``
    Every step function whose name starts with ``_w_`` (the
    workflow-wrapper convention) MUST contain a single ``Call``
    AST node whose function is defined in ``_workflows.py``.
    This catches the regression where a contributor copies
    workflow logic into a wrapper instead of delegating, which
    would silently bypass the workflow's pre-condition
    assertions and data-testid documentation.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_PATH = REPO_ROOT / "tests" / "bdd" / "step_defs" / "_workflows.py"
STEP_DEFS_DIR = REPO_ROOT / "tests" / "bdd" / "step_defs"
FEATURES_DIR = REPO_ROOT / "tests" / "bdd" / "features"
LOGIN_FEATURE = "login.feature"
PROFILE_ISOLATION_FEATURE = "profile_isolation.feature"

CARVE_OUT_FEATURES = frozenset({LOGIN_FEATURE, PROFILE_ISOLATION_FEATURE})
WRAPPER_REGEXES: dict[str, str] = {
    "login_and_pick_profile": r"estou logado como",
    "switch_profile": r"troquei para o perfil",
}


def _public_callables(module_path: Path) -> list[str]:
    """Return names of public callables defined in ``module_path``.

    "Public" = top-level ``def`` whose name does not start with
    ``_``. Includes classes (callables too). The module is parsed
    via ``ast`` rather than imported so the contract is enforced
    even if the module imports pull in heavy dependencies.
    """
    tree = ast.parse(module_path.read_text())
    names: list[str] = []
    for node in tree.body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ) and not node.name.startswith("_"):
            names.append(node.name)
    return names


def test_workflow_count_under_ceiling() -> None:
    """``_workflows.py`` exposes ≤10 public callables."""
    names = _public_callables(WORKFLOWS_PATH)
    assert len(names) <= 10, (
        f"_workflows.py has {len(names)} public callables, exceeds the "
        f"10-workflow ceiling: {sorted(names)}"
    )


def test_carve_out_files_use_inline_steps() -> None:
    """``login.feature`` + ``profile_isolation.feature`` MUST NOT use login/switch wrappers.

    Parses the carve-out feature files with the same regex the
    scenario step matcher would use, so a wrapper-step text
    sneaking in is caught the moment the file is touched, not at
    the next CI run.
    """
    import re

    for feature_filename in CARVE_OUT_FEATURES:
        feature_path = FEATURES_DIR / feature_filename
        # Walk every ``Cenário:`` / ``Esquema do Cenário:`` block
        # by hand — we only need the step text, not full
        # pytest-bdd resolution. The regex matches the wrapper's
        # Gherkin step text so a wrapper sneaking back into a
        # carve-out file is flagged.
        body = feature_path.read_text(encoding="utf-8")
        for workflow_name, regex in WRAPPER_REGEXES.items():
            if re.search(regex, body):
                pytest.fail(
                    f"{feature_filename} uses the '{workflow_name}' "
                    f"wrapper (regex {regex!r}); carve-out files must "
                    f"keep login/switch steps inline so a bug in the "
                    f"workflow doesn't silently pass on auth-flow tests."
                )


def _workflow_function_names() -> set[str]:
    """Return the set of function names defined in ``_workflows.py``."""
    tree = ast.parse(WORKFLOWS_PATH.read_text())
    return {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _wrapper_function_sources() -> list[tuple[str, str, ast.Module]]:
    """Yield ``(module_name, function_name, parsed_module)`` for every ``_w_*`` step definition."""
    workflow_names = _workflow_function_names()
    for py_path in sorted(STEP_DEFS_DIR.glob("*.py")):
        if py_path.name == "_workflows.py":
            continue
        module_name = py_path.stem
        module = ast.parse(py_path.read_text())
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
                "_w_"
            ):
                # Body must call at least one workflow function.
                called = _called_names(node)
                if not called & workflow_names:
                    pytest.fail(
                        f"{module_name}.{node.name} is a workflow wrapper "
                        f"(name starts with _w_) but its body does not call "
                        f"any function defined in _workflows.py. Wrappers must "
                        f"delegate to a workflow rather than reimplement "
                        f"the logic, so the workflow's pre-condition "
                        f"assertion and data-testid documentation can't be "
                        f"silently bypassed."
                    )


def _called_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Return the set of function names called anywhere in ``func``'s body."""
    called: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # ``module.workflow_fn(...)`` — capture the attribute name.
                called.add(node.func.attr)
            self.generic_visit(node)

    Visitor().visit(func)
    return called


def test_wrappers_delegate_to_workflows() -> None:
    """Every ``_w_*`` step body must call a function defined in ``_workflows.py``."""
    _wrapper_function_sources()
