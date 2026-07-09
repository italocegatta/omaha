"""Validation pipeline for the rebalance solver inputs.

Eleven checks ported from section 7.1 of the reference docs
(``docs/portfolio-rebalance-algorithm-reference.md``) and the reference's
``_validate_rebalance_inputs`` helper
(``src/portfolio_rebalancing/domain/rebalancing.py:108-197``).

Omaha additions (per design Decision 2):

* **Check 1** — ``contribution < 0`` rejects with the reference's
  PT-BR message. The HTTP contract is permissive (accepts any finite
  float) but the solver itself enforces ``contribution >= 0``. The
  dashboard's client-side gate (``min="0"``) keeps users from sending
  negatives in practice, so this check exists for defense-in-depth and
  for callers that bypass the route (tests, scripts).

* **Check 11** — surface ``NaN`` / ``inf`` in any numeric column as a
  validation error rather than letting CVXPY raise an opaque "invalid
  value" exception deep inside the problem setup.

The function returns ``None`` on success and raises
:class:`omaha.rebalance.models.RebalanceValidationError` on failure
with the concatenated error messages (one per line).
"""

from __future__ import annotations

import math
from decimal import Decimal

import numpy as np
import pandas as pd

from omaha.rebalance.constants import ALLOCATION_TOLERANCE
from omaha.rebalance.models import PortfolioSetup, RebalanceValidationError

_DECIMAL_TOLERANCE = Decimal("0.000001")
_DECIMAL_ONE = Decimal("1")


def _validate_rebalance_inputs(
    setup: PortfolioSetup,
    position: pd.DataFrame,
    contribution: float,
) -> None:
    """Run all checks; raise :class:`RebalanceValidationError` on any failure.

    Mirrors ``_validate_rebalance_inputs`` from the reference algorithm.
    All checks run even when an earlier one has fired; the resulting
    error message concatenates every failure so the operator sees the
    complete list (not "fix one error to discover the next").

    The 11 checks (PT-BR messages are literal):

    1.  ``contribution < 0``
    2.  ``setup.categories.empty``
    3.  ``setup.assets.empty``
    4.  duplicate ``asset_key`` in ``setup.assets``
    5.  sum of canonical class targets over categories ≠ 1.0
    6.  asset rows referencing a category that does not exist in
        ``setup.categories``
    7.  per-category sum of canonical ``target_weight_in_category``
        differs from 1.0 by more than Decimal storage tolerance
    8.  position ``asset_key`` not present in ``setup.assets``
    9.  ``current_value`` column is empty / zero / negative
    10. ``NaN`` or ``inf`` in any numeric column of ``position``
    """
    errors: list[str] = []

    if contribution < 0:
        errors.append("O aporte informado nao pode ser negativo.")

    if setup.categories.empty:
        errors.append("O setup nao possui categorias carregadas.")
    if setup.assets.empty:
        errors.append("O setup nao possui ativos carregados.")

    if setup.assets["asset_key"].duplicated().any():
        duplicated = sorted(
            set(setup.assets.loc[setup.assets["asset_key"].duplicated(), "asset_name"].tolist())
        )
        errors.append("O setup possui ativos duplicados: " + ", ".join(duplicated) + ".")

    category_weights = _decimal_column(setup.categories, "target_weight")
    category_sum = sum(category_weights, Decimal("0"))
    if not _decimal_close(category_sum, _DECIMAL_ONE):
        errors.append(
            "Os pesos-alvo das categorias devem somar 100%; "
            f"valor encontrado: {float(category_sum):.6f}."
        )

    category_keys = setup.categories["category_key"].tolist()
    category_names = setup.categories["category_name"].tolist()
    category_name_by_key = dict(zip(category_keys, category_names, strict=False))

    asset_category_keys = setup.assets["category_key"].tolist()
    missing_categories = sorted(set(asset_category_keys) - set(category_keys))
    if missing_categories:
        errors.append(
            "Existem ativos vinculados a categorias ausentes no setup: "
            + ", ".join(missing_categories)
            + "."
        )

    asset_weights_in_category = _decimal_column(setup.assets, "target_weight_in_category")
    weights_by_category: dict[str, Decimal] = {}
    for key, weight in zip(asset_category_keys, asset_weights_in_category, strict=False):
        weights_by_category[key] = weights_by_category.get(key, Decimal("0")) + weight

    for category_key, target_weight_in_category in weights_by_category.items():
        if category_key not in category_name_by_key:
            continue
        if not _decimal_close(target_weight_in_category, _DECIMAL_ONE):
            category_name = category_name_by_key[category_key]
            errors.append(
                f"A categoria '{category_name}' deve ter ativos somando 100%; "
                f"valor encontrado: {float(target_weight_in_category):.6f}."
            )

    aggregated_position = _aggregate_position(position)
    setup_keys = set(setup.assets["asset_key"])
    unmatched_assets = aggregated_position.loc[~aggregated_position["asset_key"].isin(setup_keys)]
    if not unmatched_assets.empty:
        asset_names = sorted(unmatched_assets["asset_name"].tolist())
        errors.append(
            "Existem ativos na posicao sem correspondencia no setup: "
            + ", ".join(asset_names)
            + "."
        )

    current_values = aggregated_position["current_value"].fillna(0.0)
    if float(current_values.sum()) <= ALLOCATION_TOLERANCE:
        errors.append("O patrimonio atual precisa ser positivo para rodar a simulacao.")
    if (current_values < -ALLOCATION_TOLERANCE).any():
        errors.append("A posicao atual nao pode conter valores de patrimonio negativos.")

    numeric_columns = [
        column
        for column in ("quantity", "invested_value", "current_value")
        if column in position.columns
    ]
    for column in numeric_columns:
        series = pd.to_numeric(position[column], errors="coerce")
        if not np.isfinite(series).all():
            errors.append(f"Existem valores invalidos (NaN/inf) na coluna '{column}' da posicao.")
            break

    if errors:
        raise RebalanceValidationError(errors)


def _aggregate_position(position: pd.DataFrame) -> pd.DataFrame:
    """Aggregate multiple ``Position`` rows per ``asset_key``.

    Lifted from the reference's same-named helper (lines 200-231) so the
    validator runs against the same per-asset view the solver uses,
    eliminating duplicate-key edge cases before checks 9-11 fire.

    Empty input → empty frame copy. Available columns are summed per
    ``asset_key``; ``current_weight`` is recomputed from the aggregated
    ``current_value`` so the validation reads the same numbers the
    solver downstream consumes.
    """
    if position.empty:
        return position.copy()

    aggregate_map: dict[str, str] = {
        "asset_name": "first",
        "category_name": "first",
        "category_key": "first",
        "quantity": "sum",
        "invested_value": "sum",
        "current_value": "sum",
    }
    available_columns = {
        column: rule for column, rule in aggregate_map.items() if column in position.columns
    }
    aggregated = (
        position.groupby("asset_key", as_index=False, dropna=False)
        .agg(available_columns)
        .sort_values("asset_name")
        .reset_index(drop=True)
    )
    total = float(aggregated["current_value"].fillna(0.0).sum())
    if total > 0:
        aggregated["current_weight"] = aggregated["current_value"].fillna(0.0) / total
    else:
        aggregated["current_weight"] = 0.0
    return aggregated


def _decimal_column(frame: pd.DataFrame, column: str) -> list[Decimal]:
    stored = frame.attrs.get("decimal_columns", {}) if hasattr(frame, "attrs") else {}
    values = stored.get(column)
    if isinstance(values, list) and len(values) == len(frame):
        return [value if isinstance(value, Decimal) else Decimal(str(value)) for value in values]
    return [Decimal(str(value)) for value in frame[column].tolist()]


def _decimal_close(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) <= _DECIMAL_TOLERANCE


__all__ = ["_validate_rebalance_inputs"]
