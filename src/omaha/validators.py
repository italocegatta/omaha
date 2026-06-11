"""Pure validators for the Omaha portfolio domain.

The validators in this module are side-effect-free functions that
return a ``(ok, error_message)`` tuple. The PATCH ``/api/assets/{id}``
route added in S01/T02 calls :func:`validate_target_pct_sum` to
enforce the "per-class sum equals 100" invariant — the validator is
the single source of truth for the message returned to the browser,
so the T03 Alpine inline editor and the T02 PATCH route display
identical wording regardless of where the check ran.

Why a separate module from the route
------------------------------------

* **Pure functions are testable without a DB session.** The
  per-class sum invariant is locked at the cheapest layer
  possible. The DB column's ``NOT NULL`` constraint is the last
  line of defense (a backstop against a hand-crafted ``INSERT``),
  not the primary check.
* **The T02 PATCH route and the T03 Alpine ``classSum`` getter
  can both call the same function** for the same answer, so the
  operator sees the same "Sobra 10%" / "Falta 10%" wording
  whether the validation runs locally (preview) or server-side
  (commit). The slice plan's verification contract relies on
  this — the unit test asserts the exact error string and the
  PATCH route's 422 body re-emits it verbatim.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

# Sum target + tolerance mirror the S02 ``classes`` route's
# snapshot validator (1-cent tolerance so the message can be
# reported as a whole number — "Falta 10" / "Sobra 10"). The S01
# per-class validator adds the ``%`` suffix because the editor
# surfaces the delta inline next to a percentage input.
SUM_TARGET = Decimal("100")
SUM_TOLERANCE = Decimal("0.01")


def validate_target_pct_sum(values: list[Decimal]) -> tuple[bool, str | None]:
    """Return ``(True, None)`` iff ``sum(values)`` is within 0.01 of 100.

    On failure, the returned error message follows the
    ``"Sobra X%"`` / ``"Falta X%"`` format used by the S01 Alpine
    inline editor's class-delta badge. The ``%`` suffix is part
    of the contract — the unit test for the under-100 case asserts
    it literally, and the S01 PATCH route surfaces the same
    string in ``{"detail": "..."}`` so the editor can render the
    message without translation.

    Empty input
    -----------
    An empty list returns ``(False, "Defina a alocação")`` — the
    class has no assets at all, so the editor's "Sobra/Falta"
    message (which would say ``Falta 100%``) is misleading. The
    T02 PATCH route is unlikely to ever pass an empty list (it
    always supplies the new value), but the T03 Alpine preview
    can: when the user clears the input, the live preview is
    "the class has 0% allocated" — better wording is "set the
    allocation".

    Tolerance
    ---------
    A 1-cent tolerance (``abs(sum - 100) <= 0.01``) means a sum
    of 100.005 still validates as ok. This matches the S02
    class-level validator's tolerance — the operator can
    legitimately enter ``[33.33, 33.33, 33.34]`` (sum 100.00) or
    ``[33.34, 33.33, 33.33]`` (sum 100.00 after rounding) without
    hitting the "Sobra/Falta" path.

    Parameters
    ----------
    values
        Per-asset ``target_pct`` values within one asset class.
        The caller (T02 PATCH route) is responsible for gathering
        the class's other assets' current ``target_pct`` plus the
        new value being applied — the validator does not look at
        the DB.

    Returns
    -------
    (True, None)
        Sum is within 0.01 of 100.
    (False, "Defina a alocação")
        Input is an empty list. Distinct from the "Falta 100%"
        case so the editor can show an actionable "please set
        a target" hint instead of "you owe 100%".
    (False, "Sobra X%")
        Sum is over 100 by more than 0.01. ``X`` is the
        integer-rounded absolute delta (``ROUND_HALF_UP`` to
        match the S02 class-level validator's rounding style).
    (False, "Falta X%")
        Sum is under 100 by more than 0.01. ``X`` is the
        integer-rounded absolute delta.
    """
    if not values:
        return False, "Defina a alocação"
    total = sum(values, Decimal("0"))
    delta = SUM_TARGET - total
    if abs(delta) <= SUM_TOLERANCE:
        return True, None
    if delta < 0:
        # Over 100: round the absolute delta to the nearest int.
        # Using ``to_integral_value(rounding=ROUND_HALF_UP)``
        # matches the S02 "Sobra 10" rounding for ``[40, 30, 40]``
        # (sum 110, Sobra 10).
        return (
            False,
            f"Sobra {int((-delta).to_integral_value(rounding=ROUND_HALF_UP))}%",
        )
    # Under 100: round the absolute delta to the nearest int.
    return (
        False,
        f"Falta {int(delta.to_integral_value(rounding=ROUND_HALF_UP))}%",
    )


__all__ = ["SUM_TARGET", "SUM_TOLERANCE", "validate_target_pct_sum"]
