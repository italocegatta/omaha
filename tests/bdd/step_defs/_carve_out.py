"""BDD carve-out marker — declarative carve-out for workflow functions.

A workflow that must NOT be called from certain feature files
(e.g. a feature file that tests the workflow itself) declares
its carve-out via the :func:`carve_out` decorator. The contract
test :func:`tests.bdd.test_workflow_contracts.test_carve_out_files_use_inline_steps`
parses these decorators via AST and asserts that each carve-out
file does NOT contain a step matching the workflow's
``step_regex``.

Why this exists
---------------

The previous design hardcoded the carve-out mapping in the
contract test as a ``dict[str, str]``. New carve-out workflows
had to update that dict manually — easy to forget, so the
test silently passed for new carve-outs that weren't tracked.

This marker co-locates the carve-out metadata with the
workflow itself, so adding a new carve-out workflow = add
the decorator; the contract test enforces automatically.

Usage
-----

::

    from tests.bdd.step_defs._carve_out import carve_out

    @carve_out(
        files=frozenset({"login.feature", "profile_isolation.feature"}),
        step_regex=r"estou logado como",
    )
    def login_and_pick_profile(page, live_url, profile, password="test-password"):
        ...
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class CarveOut:
    """Carve-out metadata attached to a workflow via :func:`carve_out`.

    Attributes:
        files: Set of feature filenames (basename only, e.g.
            ``"login.feature"``) that MUST NOT use the workflow's
            step wrapper.
        step_regex: Regular expression matching the step text
            that the workflow's wrapper exposes to Gherkin. The
            contract test fails if any file in ``files`` contains
            a step matching this regex.
    """

    files: frozenset[str]
    step_regex: str


def carve_out(
    *, files: Iterable[str], step_regex: str
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Declare a carve-out for the decorated workflow.

    Args:
        files: Feature filenames (basename) that must not use
            this workflow's wrapper.
        step_regex: Regex matching the wrapper's Gherkin step
            text. The contract test uses this to detect
            regressions where the wrapper sneaks into a
            carve-out file.

    Returns:
        A decorator that attaches a :class:`CarveOut` dataclass
        to the function's ``__carve_out__`` attribute and returns
        the function unchanged. The contract test reads the
        attribute via AST (it parses the source — the attribute
        is for documentation / type-checker access only; the
        test never imports the module).
    """

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        func.__carve_out__ = CarveOut(files=frozenset(files), step_regex=step_regex)
        return func

    return decorator
