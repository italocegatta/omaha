"""Regression guard for the literal transcription of §4 constants.

Every public constant in :mod:`omaha.rebalance.constants` is asserted
against the value quoted in the reference docs. A diff against the
reference docs is part of the port contract — typos here propagate to
every downstream tolerance comparison.

If you intentionally change a constant, update this test in the same
commit, then propagate to the reference docs / OpenSpec spec if the
contract change is global.
"""

from __future__ import annotations

import importlib

from omaha.rebalance import constants


def test_allocation_tolerance_matches_reference() -> None:
    assert constants.ALLOCATION_TOLERANCE == 1e-6


def test_display_tolerance_matches_reference() -> None:
    assert constants.DISPLAY_TOLERANCE == 1e-4


def test_target_value_neutral_tolerance_is_display_tolerance() -> None:
    assert constants.TARGET_VALUE_NEUTRAL_TOLERANCE == constants.DISPLAY_TOLERANCE


def test_prioritized_asset_gap_count_matches_reference() -> None:
    assert constants.PRIORITIZED_ASSET_GAP_COUNT == 5


def test_prioritized_category_gap_count_matches_reference() -> None:
    assert constants.PRIORITIZED_CATEGORY_GAP_COUNT == 2


def test_shortfall_relative_floor_value_matches_reference() -> None:
    assert constants.SHORTFALL_RELATIVE_FLOOR_VALUE == 100.0


def test_min_buy_amount_matches_reference() -> None:
    assert constants.MIN_BUY_AMOUNT == 1_000.0


def test_min_sell_amount_matches_reference() -> None:
    assert constants.MIN_SELL_AMOUNT == 1_000.0


def test_lot_size_is_none() -> None:
    assert constants.LOT_SIZE is None


def test_requires_integer_quantities_is_false() -> None:
    assert constants.REQUIRES_INTEGER_QUANTITIES is False


def test_contribution_only_asset_deviation_tolerance() -> None:
    assert constants.CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE == 0.02


def test_contribution_only_category_deviation_tolerance() -> None:
    assert constants.CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE == 0.01


def test_contribution_only_max_residual_cash_share() -> None:
    assert constants.CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE == 0.02


def test_contribution_only_top_asset_gap_tolerance() -> None:
    assert constants.CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE == 0.02


def test_contribution_only_top_category_gap_tolerance() -> None:
    assert constants.CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE == 0.01


def test_zero_target_value_tolerance_matches_reference() -> None:
    assert constants.ZERO_TARGET_VALUE_TOLERANCE == 100.0


def test_staged_sales_min_category_improvement() -> None:
    assert constants.STAGED_SALES_MIN_CATEGORY_IMPROVEMENT == 0.05


def test_staged_sales_min_top_asset_improvement() -> None:
    assert constants.STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT == 0.05


def test_policy_name_strings_match_reference() -> None:
    assert constants.CONTRIBUTION_ONLY_POLICY == "contribution-only"
    assert constants.OVERWEIGHT_SALES_POLICY == "contribution-with-overweight-sales"
    assert constants.FULL_SALES_POLICY == "contribution-with-full-sales"
    assert constants.CURRENT_PORTFOLIO_REBALANCE_POLICY == "current-portfolio-rebalance"


def test_dunder_all_lists_every_public_constant() -> None:
    """Every public module attribute must be listed in ``__all__``.

    Catches accidental removal when constants are deleted — ``__all__``
    is the surface that downstream tests / docs import.
    """
    module = importlib.import_module(constants.__name__)
    declared = {name for name in constants.__all__}
    public_attrs = {
        name
        for name in dir(module)
        if not name.startswith("_")
        and name != "annotations"
        and not callable(getattr(module, name))
    }
    assert public_attrs.issubset(declared), (
        f"Constants module is missing names from __all__: declared={public_attrs - declared}"
    )
