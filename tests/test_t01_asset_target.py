"""Tests for T01: per-class sum validator and ``assets.target_pct`` column.

TDD contract: ``omaha.validators.validate_target_pct_sum`` is the
single source of truth for the "sum of asset target_pct within one
class must equal 100" invariant. The validator is pure (no DB, no
HTTP, no I/O) so the PATCH route in T02 and the Alpine editor in T03
can both call it for the same result.

The success-path test in this file proves the happy path. T02
extends this file with the failure-path tests (over-100, empty
input) and a per-class sum re-calculation route test that walks
the live DB.

Why the validator lives in ``omaha.validators`` and not in
``omaha.routes.assets``:

* The T02 PATCH route calls it on commit. The T03 Alpine inline
  editor's ``classSum`` getter will also call it for the live
  preview — the message returned to the browser is the same
  string the unit test asserts, so the operator sees identical
  wording whether the validation runs locally or server-side
  (slice plan verification contract).
* Pure functions are testable without a DB session, so the
  per-class sum invariant is locked at the cheapest layer
  possible. The DB column's ``NOT NULL`` constraint is the last
  line of defense (a backstop against a hand-crafted INSERT),
  not the primary check.
"""

from __future__ import annotations

from decimal import Decimal

from omaha.validators import validate_target_pct_sum


def test_sum_validator_100pct() -> None:
    """A list of percentages that sums to exactly 100 validates as ok.

    The error message is ``None`` on success — the T02 PATCH route
    treats ``(True, None)`` as "commit and return 200" and the
    T03 Alpine editor treats it as "clear the delta badge".
    """
    values = [Decimal(30), Decimal(30), Decimal(40)]
    ok, error = validate_target_pct_sum(values)

    assert ok is True, f"expected ok=True, got ok={ok!r} error={error!r}"
    assert error is None, f"expected error=None, got error={error!r}"
