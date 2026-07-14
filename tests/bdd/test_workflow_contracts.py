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
    Workflows that declare ``@carve_out(...)`` in
    ``_workflows.py`` MUST NOT be used in their carve-out
    feature files (e.g. ``login.feature`` cannot use the
    ``login_and_land`` wrapper, because it tests the auth
    flow itself). The contract test parses the workflow
    decorators via AST and asserts each carve-out file does
    NOT contain a step matching the workflow's declared
    ``step_regex``.

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

CARVE_OUT_FEATURES = frozenset({LOGIN_FEATURE})


def _carve_out_decorators() -> dict[str, tuple[frozenset[str], str]]:
    """Discover carve-out declarations on workflows in ``_workflows.py``.

    Parses ``_workflows.py`` via AST and returns a mapping
    ``{workflow_name: (files_frozenset, step_regex)}`` for every
    top-level ``FunctionDef`` whose decorator list contains a
    ``@carve_out(files=..., step_regex=...)`` call.

    Workflows WITHOUT the ``@carve_out`` decorator are not in
    the result — they have no carve-out constraint.

    Decorator arguments are read positionally by keyword. Only
    string literals (``ast.Constant``) are supported for both
    ``files`` (which must be a ``Set`` of strings in source —
    expanded by AST into a ``ast.Set`` of ``ast.Constant``
    nodes) and ``step_regex`` (single string literal).
    """
    tree = ast.parse(WORKFLOWS_PATH.read_text())
    carve_outs: dict[str, tuple[frozenset[str], str]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not (isinstance(decorator.func, ast.Name) and decorator.func.id == "carve_out"):
                continue
            files: set[str] = set()
            step_regex = ""
            for kw in decorator.keywords:
                if kw.arg == "files":
                    value = kw.value
                    if isinstance(value, ast.Set):
                        elements = value.elts
                    elif (
                        isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Name)
                        and value.func.id in {"frozenset", "set"}
                        and len(value.args) == 1
                        and isinstance(value.args[0], ast.Set)
                    ):
                        # ``frozenset({"a.feature", "b.feature"})`` pattern.
                        elements = value.args[0].elts
                    else:
                        raise ValueError(
                            f"carve_out on {node.name}: 'files' must be a set literal "
                            f"or frozenset({{...}}) (got {type(value).__name__})"
                        )
                    for elt in elements:
                        if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
                            raise ValueError(
                                f"carve_out on {node.name}: "
                                f"'files' must contain only string literals"
                            )
                        files.add(elt.value)
                elif kw.arg == "step_regex":
                    value = kw.value
                    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                        raise ValueError(
                            f"carve_out on {node.name}: 'step_regex' must be a string literal"
                        )
                    step_regex = value.value
            if not files or not step_regex:
                raise ValueError(
                    f"carve_out on {node.name}: both 'files' and 'step_regex' are required"
                )
            carve_outs[node.name] = (frozenset(files), step_regex)
    return carve_outs


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
    """Workflows with ``@carve_out`` MUST NOT be used in their carve-out feature files.

    Carve-outs are declared on the workflow function itself
    (see :mod:`tests.bdd.step_defs._carve_out`) and discovered
    via AST. Each declared carve-out is enforced here; adding
    a new carve-out workflow = add the decorator, no manual
    test maintenance required.
    """
    import re

    carve_outs = _carve_out_decorators()
    if not carve_outs:
        pytest.fail(
            "No workflows declare @carve_out — at least "
            "login_and_land MUST be carved out from login.feature."
        )
    for workflow_name, (files, regex) in carve_outs.items():
        for feature_filename in files:
            feature_path = FEATURES_DIR / feature_filename
            if not feature_path.exists():
                pytest.fail(
                    f"carve_out on {workflow_name}: file "
                    f"{feature_filename!r} declared but missing "
                    f"from {FEATURES_DIR}"
                )
            body = feature_path.read_text(encoding="utf-8")
            if re.search(regex, body):
                pytest.fail(
                    f"{feature_filename} uses the {workflow_name!r} "
                    f"wrapper step text (regex {regex!r}); carve-out "
                    f"files must keep this flow's steps inline so a "
                    f"bug in the workflow doesn't silently pass on "
                    f"tests of the flow itself."
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
