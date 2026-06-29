"""Constants used by the CVXPY rebalance solver.

Literal transcription of `src/portfolio_rebalancing/domain/rebalancing.py:20-44`
(commit ``ca867ba``) and section 4 of
``docs/portfolio-rebalance-algorithm-reference.md``. Diff against the
reference is part of the port contract; the regression guard in
``tests/test_rebalance_constants.py`` asserts each value matches.

The constants are grouped by purpose:

* **Numerical tolerance** (``ALLOCATION_TOLERANCE``, ``DISPLAY_TOLERANCE``,
  ``TARGET_VALUE_NEUTRAL_TOLERANCE``, ``SHORTFALL_RELATIVE_FLOOR_VALUE``,
  ``ZERO_TARGET_VALUE_TOLERANCE``) — gap between the LP solver's notion of
  "exactly zero" and the operator's notion of "close enough to render".
* **Post-processing thresholds** (``MIN_BUY_AMOUNT``, ``MIN_SELL_AMOUNT``,
  ``LOT_SIZE``, ``REQUIRES_INTEGER_QUANTITIES``).
* **Contribution-only acceptance band** — five tolerances the
  ``contribution-only`` stage must meet to skip the sales cascade.
* **Staged-sales gates** — minimum improvements to escalate from one
  policy stage to the next.
* **Policy-name strings** — emitted by ``simulation_frame.metrics``
  and surfaced in the dashboard. Transcribed verbatim from the
  reference (PT-BR rationale inside the algorithm does not apply here
  — these are machine-comparable identifiers).
"""

from __future__ import annotations

ALLOCATION_TOLERANCE = 1e-6
DISPLAY_TOLERANCE = 1e-4
TARGET_VALUE_NEUTRAL_TOLERANCE = DISPLAY_TOLERANCE

PRIORITIZED_ASSET_GAP_COUNT = 5
PRIORITIZED_CATEGORY_GAP_COUNT = 2
SHORTFALL_RELATIVE_FLOOR_VALUE = 100.0
MIN_BUY_AMOUNT = 1_000.0
MIN_SELL_AMOUNT = 1_000.0
LOT_SIZE: float | None = None
REQUIRES_INTEGER_QUANTITIES = False

CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE = 0.02
CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE = 0.01
CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE = 0.02
CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE = 0.02
CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE = 0.01
ZERO_TARGET_VALUE_TOLERANCE = 100.0
STAGED_SALES_MIN_CATEGORY_IMPROVEMENT = 0.05
STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT = 0.05

CONTRIBUTION_ONLY_POLICY = "contribution-only"
OVERWEIGHT_SALES_POLICY = "contribution-with-overweight-sales"
FULL_SALES_POLICY = "contribution-with-full-sales"
CURRENT_PORTFOLIO_REBALANCE_POLICY = "current-portfolio-rebalance"


__all__ = [
    "ALLOCATION_TOLERANCE",
    "CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE",
    "CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE",
    "CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE",
    "CONTRIBUTION_ONLY_POLICY",
    "CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE",
    "CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE",
    "CURRENT_PORTFOLIO_REBALANCE_POLICY",
    "DISPLAY_TOLERANCE",
    "FULL_SALES_POLICY",
    "LOT_SIZE",
    "MIN_BUY_AMOUNT",
    "MIN_SELL_AMOUNT",
    "OVERWEIGHT_SALES_POLICY",
    "PRIORITIZED_ASSET_GAP_COUNT",
    "PRIORITIZED_CATEGORY_GAP_COUNT",
    "REQUIRES_INTEGER_QUANTITIES",
    "SHORTFALL_RELATIVE_FLOOR_VALUE",
    "STAGED_SALES_MIN_CATEGORY_IMPROVEMENT",
    "STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT",
    "TARGET_VALUE_NEUTRAL_TOLERANCE",
    "ZERO_TARGET_VALUE_TOLERANCE",
]
