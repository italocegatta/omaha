"""Smoke test for the central selector inventory (spec e2e-selector-pinning).

Walks every entry in ``tests/e2e/selectors.SELECTORS`` against a
live ``/patrimonio`` render and confirms each named element
resolves within 2 seconds.

If an inventory entry names a testid that no template renders,
the smoke fails loudly — preventing silent per-file test rot.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .selectors import DASHBOARD_SELECTORS
from .test_asset_crud import _create_seed_assets
from .test_import_user_journey import _login_and_select_italo

if TYPE_CHECKING:
    from playwright.sync_api import Page


# Per spec: walk inventory against /patrimonio with at least one class.
# Empty profile means many selectors (class_summary_row, etc.) don't
# resolve, so we seed one before the assertion loop.
def _seed_one_class(page: Page, live_url: str) -> None:
    """Seed a single ``Renda Fixa`` class via fetch + reload."""
    page.evaluate(
        """async () => {
            const fd = new FormData();
            fd.append('name[]', 'Renda Fixa');
            fd.append('target_pct[]', '100');
            const r = await fetch('/classes', { method: 'POST', body: fd });
            if (!r.ok) {
                throw new Error('POST /classes ' + r.status + ': ' + await r.text());
            }
        }"""
    )
    # The class needs to be on the rendered DOM before
    # ``_create_seed_assets`` can look it up via the dashboard's
    # ``[data-testid="class-summary-row"]`` rows.
    page.goto(f"{live_url}/patrimonio")
    page.wait_for_selector('[data-testid="class-summary-row"]', timeout=5000)


def _seed_one_asset(page: Page, live_url: str) -> None:
    """Seed one asset + one position so the dashboard renders the
    asset row + table + portfolio header.
    """
    _create_seed_assets(page, [("Renda Fixa", "INVENTORY_ASSET", 0)])
    # Insert one position so the portfolio header has current_value > 0
    # and the asset row's BRL cells render. Direct sqlite3 write — same
    # pattern the inline-edit suite uses (PRD §4.3 allows test setup
    # outside the asset/position seed invariant).
    import sqlite3
    from pathlib import Path

    db_path = Path(live_url.replace("http://127.0.0.1:", ""))  # unused
    repo_root = Path(__file__).resolve().parent.parent.parent
    db_path = repo_root / "data" / "test_e2e.db"
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO positions "
                "(asset_id, qty, avg_price, current_price, broker_ticker, "
                " total_invested, total_current) "
                "SELECT a.id, 100, 10.0, 12.0, a.name, 1000.0, 1200.0 "
                "FROM assets a JOIN asset_classes ac ON ac.id = a.asset_class_id "
                "JOIN profiles p ON p.id = ac.profile_id "
                "WHERE p.name = 'Italo' AND a.name = 'INVENTORY_ASSET'"
            )
            # CVXPY rejects target_pct=0 across a class; the asset
            # imported via _create_seed_assets also has 0 by default.
            conn.execute("UPDATE assets SET target_pct = 100 WHERE name = 'INVENTORY_ASSET'")
            conn.commit()
        finally:
            conn.close()


class TestSelectorInventory:
    """Spec: e2e-selector-pinning — central map smoke."""

    def test_every_inventory_entry_resolves_on_patrimonio(self, page: Page, live_url: str) -> None:
        _login_and_select_italo(page, live_url)
        _seed_one_class(page, live_url)
        _seed_one_asset(page, live_url)
        page.goto(f"{live_url}/patrimonio")
        page.wait_for_selector('[data-testid="dashboard-asset-row"]', timeout=5000)
        # Give Alpine a beat to hydrate the action modals so that
        # selectors behind ``x-show`` resolve.
        page.wait_for_timeout(300)

        missing: list[str] = []
        for name, selector in DASHBOARD_SELECTORS.items():
            count = page.locator(selector).count()
            if count < 1:
                missing.append(f"{name} -> {selector}")

        assert not missing, (
            "Selectors in the central inventory that did NOT resolve on "
            "/patrimonio (seeded with one class):\n  - " + "\n  - ".join(missing)
        )

    def test_inventory_module_is_pytest_free(self) -> None:
        """The central selectors module imports no pytest machinery.

        This guards against accidental coupling that would break
        non-test consumers (lint, doc-build, etc.).
        """
        import importlib
        import inspect

        mod = importlib.import_module("tests.e2e.selectors")
        source = inspect.getsource(mod)
        # ``import pytest`` would show up as ``import pytest`` exactly.
        assert "import pytest" not in source, (
            "tests/e2e/selectors.py must remain pytest-free; "
            "use TYPE_CHECKING-only imports if you need types."
        )
        assert "from pytest" not in source
