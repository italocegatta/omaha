"""Dataclasses for the rebalance data bridges.

Two frozen dataclasses that the reference CVXPY solver consumes:

* :class:`PortfolioSetup` — categories + assets DataFrames matching
  the reference algorithm's expected schema. ``categories`` carries
  one row per :class:`~omaha.models.AssetClass` (target weight ∈ [0,1]
  + display order); ``assets`` carries one row per
  :class:`~omaha.models.Asset` (target weight split between the
  per-class and whole-portfolio views, plus the per-asset trade-control
  flags and currency code that Phase 4 reads as hard locks).
* :class:`RebalanceValidationError` — raised by Phase 3 / Phase 4 when
  the input data fails one of the 11 checks from the reference
  algorithm's ``_validate_rebalance_inputs`` (sum-to-100, USD requires
  ``BRL=X`` cache row, etc.). Defined here so Phase 4 can import the
  symbol from :mod:`omaha.rebalance` without forcing Phase 3 to
  re-export it.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PortfolioSetup:
    """The two-DataFrame input the CVXPY solver consumes.

    Both fields are :class:`pandas.DataFrame` with the column schema
    defined in spec §"PortfolioSetup builder translates ORM to DataFrame".
    Builders never produce ``None`` here; an empty profile yields two
    DataFrames with the full column schema and zero rows.

    Frozen so a downstream consumer can't mutate the solver's input
    mid-run (the algorithm indexes by position; a mutation in
    user-space would silently corrupt the LP).
    """

    categories: pd.DataFrame
    assets: pd.DataFrame


class RebalanceValidationError(ValueError):
    """Raised when the rebalance inputs fail one of the validation checks.

    Phase 4 (``rebalance-engine``) wires the reference algorithm's
    ``_validate_rebalance_inputs`` (sum-to-100, USD requires fresh
    ``BRL=X`` cache row, every asset_key unique, etc.) to this
    exception. Phase 3 (``rebalance-route``) catches it and returns a
    400 with the validation message; the modal renders the message
    next to the "Calcular" button so the operator knows which check
    fired without a stack trace.
    """


__all__ = ["PortfolioSetup", "RebalanceValidationError"]
