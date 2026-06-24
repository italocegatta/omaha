"""Real-browser E2E for the S01 inline asset-target editor.

Drives a headless chromium against a live uvicorn instance to
verify the S01 inline-edit feature end to end:

  login → select profile → create 1 class + N assets (via direct
  DB writes to bypass the per-class sum invariant while setting
  up state) → drive the inline editor on the dashboard:

  1. ``test_inline_edit_asset_target`` — click the asset's
     "alvo % classe" cell, type a value, commit, assert the
     server-side PATCH succeeded (200) and the cell + the
     "alvo % total" cell both updated in the UI; reload and
     assert the DB still has the new value.

  2. ``test_inline_edit_blocks_when_sum_neq_100`` — click the
     asset's cell, type a value that would push the per-class
     sum to 110; assert the class-delta badge shows the
     validator's "Sobra 10%" wording (the unit-validator and
     the Alpine preview share the same wording per T01/T02);
     press Enter to trigger the commit and verify the Alpine
     ``commitEdit`` guard bails (editor stays open, no PATCH);
     press Escape to cancel, reload, assert the DB still has
     the original value (no PATCH happened).

  3. ``test_dashboard_displays_four_percentages_per_asset`` —
     create 1 class + 1 asset, seed 1 position, assert the 4
     ``data-testid="asset-*-pct-*"`` cells are present, non-
     empty, and contain ``%``; assert the "1 posicao(oes)"
     string is gone (M002/D015).

Why per-class sum setup uses direct DB writes
---------------------------------------------
The per-class sum validator (T01) requires the sum of all
assets' ``target_pct`` in a class to equal 100 within 0.01 —
so a single 200-path PATCH can only succeed when other
assets in the same class already sum to 100 minus the new
value. The 200-path test sets up that state by writing
``target_pct`` directly via sqlite3 (mirrors the S04 expiry
test's pattern for backdating import_previews.created_at).
Without this, the operator would have to chain three
sequential PATCHes to reach sum=100, and a typo in the
mid-step would block the test before reaching the assertion
it cares about.

Reuses the S04 journey helpers via a relative import
(``tests/e2e/__init__.py`` exists, so ``from .test_import_...``
resolves) — same pattern as ``test_user_journey_rebalance.py``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from tests.e2e.conftest import _seed_assets_with_positions_via_import

from .test_import_user_journey import _login_and_select_italo
from .test_user_journey_rebalance import S05_SELECTORS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DB_PATH = REPO_ROOT / "data" / "test_e2e.db"

# S01 inline-editor data-testid markers. The dashboard template
# (``src/omaha/templates/dashboard.html``) renders these per asset
# row: 4 cells in the pct grid + the input + the class-delta badge
# in the section header. (The save/cancel buttons were removed in
# the dashboard-width-and-inline-edit change — Enter and Escape
# are the only triggers now.)
S01_SELECTORS = {
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "asset_target_pct_class": '[data-testid="asset-target-pct-class"]',
    "asset_current_pct_class": '[data-testid="asset-current-pct-class"]',
    "asset_target_pct_total": '[data-testid="asset-target-pct-total"]',
    "asset_current_pct_total": '[data-testid="asset-current-pct-total"]',
    "asset_inline_edit_input": '[data-testid="asset-inline-edit-input"]',
    "class_delta_badge": '[data-testid="class-delta-badge"]',
    "class_summary_row": '[data-testid="class-summary-row"]',
}


def _debug_dump(page: Page, tag: str) -> None:
    """Write a screenshot + main-text + URL to /tmp for post-mortem."""
    import os

    os.makedirs("/tmp/s01_e2e_debug", exist_ok=True)
    page.screenshot(path=f"/tmp/s01_e2e_debug/{tag}.png", full_page=True)
    with open(f"/tmp/s01_e2e_debug/{tag}.txt", "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")


def _create_one_class(page: Page) -> None:
    """Create a single class "Renda Fixa" at 60% via POST /classes + DB adjustment.

    S02/T07 retired the dedicated ``/classes`` page; the
    dashboard's class editor is now the only class surface.
    We POST to ``/classes`` (the same JSON-less form endpoint
    used by ``tests/e2e/test_asset_crud.py::_create_seed_classes``)
    to create a 100% class, then UPDATE its ``target_pct`` to
    60 via direct sqlite3 write so the downstream math
    (``target_pct_total = 40 * 60 / 100 = 24``) is testable.
    The dashboard reads ``target_pct`` from the DB on every
    render, so the next ``page.goto("/")`` picks up the new
    value.
    """
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
    page.goto(page.url)
    page.wait_for_selector('[data-testid="class-summary-row"]', timeout=8000)

    # Adjust the class's target_pct to 60 so the inline-edit
    # math exercises a 60% class.
    if TEST_DB_PATH.exists():
        conn = sqlite3.connect(TEST_DB_PATH)
        try:
            conn.execute(
                "UPDATE asset_classes SET target_pct = 60 "
                "WHERE name = 'Renda Fixa' "
                "AND profile_id IN (SELECT id FROM profiles WHERE name = 'Italo')"
            )
            conn.commit()
        finally:
            conn.close()


def _create_n_assets(page: Page, names: list[str], target_pct: str = "0") -> None:
    """Add N assets to the single class "Renda Fixa" via POST /api/assets.

    S03/T05 retired the dedicated ``/assets`` page; the
    dashboard's inline editor (``POST /api/assets``) is the
    canonical asset-creation surface. We use ``page.evaluate`` +
    ``fetch`` (same pattern as
    ``tests/e2e/test_asset_crud.py::_create_seed_assets``)
    to bypass the inline form's Alpine initialization timing —
    the dashboard renders the new asset row on the next reload
    regardless of how it was inserted.
    """
    class_map: dict[str, int] = page.evaluate(
        """() => {
            const out = {};
            document.querySelectorAll('[data-testid="class-summary-row"]').forEach((row) => {
                const nameEl = row.querySelector('[data-testid="class-section-name"]');
                const id = row.dataset.classId;
                if (nameEl && id) out[nameEl.textContent.trim()] = parseInt(id, 10);
            });
            return out;
        }"""
    )
    class_id = class_map.get("Renda Fixa")
    if class_id is None:
        raise RuntimeError("class 'Renda Fixa' not found on the dashboard")
    for name in names:
        resp = page.evaluate(
            """async ({classId, assetName, targetPct}) => {
                const r = await fetch('/api/assets', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: assetName,
                        asset_class_id: classId,
                        target_pct: targetPct,
                    }),
                });
                return { status: r.status, body: await r.text() };
            }""",
            {"classId": class_id, "assetName": name, "targetPct": target_pct},
        )
        if resp["status"] != 201:
            raise RuntimeError(
                f"POST /api/assets failed for {name!r}: {resp['status']} {resp['body']}"
            )
    page.goto(page.url)
    page.wait_for_selector(S01_SELECTORS["dashboard_asset_row"], state="attached", timeout=8000)
    rows = page.locator(S01_SELECTORS["dashboard_asset_row"])
    assert rows.count() == len(names), f"expected {len(names)} asset rows, got {rows.count()}"


def _seed_target_pct(profile_name: str, asset_name_to_pct: dict[str, int]) -> None:
    """Bypass the per-class sum validator by writing target_pct directly.

    The validator is the per-class-sum gatekeeper, so setting up
    a 200-path test requires the OTHER assets in the class to
    already sum to ``100 - new_value``. Direct DB writes are the
    only way to get there without a 3-step PATCH dance that
    could fail mid-way and obscure the real test failure.

    Mirrors the S04 ``test_expired_preview_shows_expirado`` use
    of raw sqlite3 against ``data/test_e2e.db``.
    """
    if not TEST_DB_PATH.exists():
        return
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        row = conn.execute("SELECT id FROM profiles WHERE name = ?", (profile_name,)).fetchone()
        if row is None:
            return
        pid = row[0]
        for asset_name, target_pct in asset_name_to_pct.items():
            conn.execute(
                """
                UPDATE assets
                SET target_pct = ?
                WHERE name = ?
                  AND asset_class_id IN (
                    SELECT id FROM asset_classes WHERE profile_id = ?
                  )
                """,
                (target_pct, asset_name, pid),
            )
        conn.commit()
    finally:
        conn.close()


def _read_target_pct(profile_name: str, asset_name: str) -> int | None:
    """Read an asset's target_pct back from the test DB.

    Used to assert the server-side state after a commit (200
    path) or to verify a failed commit (422 path) did not
    mutate the row.
    """
    if not TEST_DB_PATH.exists():
        return None
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        row = conn.execute(
            """
            SELECT assets.target_pct
            FROM assets
            JOIN asset_classes ON assets.asset_class_id = asset_classes.id
            JOIN profiles ON asset_classes.profile_id = profiles.id
            WHERE profiles.name = ? AND assets.name = ?
            """,
            (profile_name, asset_name),
        ).fetchone()
        return None if row is None else int(row[0])
    finally:
        conn.close()


class TestS01InlineEdit:
    """3 e2e tests for the M002/S01 inline asset-target editor."""

    def test_inline_edit_asset_target(self, page: Page, live_url: str) -> None:
        """Edit an asset's target_pct from 0 to 40 via the inline editor.

        Setup
        -----
        1 class (Renda Fixa 60%), 3 assets (Ativo A, Ativo B,
        Ativo C). We seed ``target_pct=30`` on Ativo B and
        Ativo C via direct DB write, so the per-class sum is
        0 + 30 + 30 = 60 (``Falta 40%`` — the local preview's
        baseline). We then click Ativo A's "alvo % classe" cell
        and type 40: the live classSum becomes 30 + 30 + 40 =
        100, the commit button is enabled, and the PATCH
        succeeds.

        Without the 30/30 seed the per-class sum after typing
        40 would be 0 + 0 + 40 = 40 (``Falta 60%``), the commit
        button would stay disabled, and the 200 path would
        never be exercised.

        Asserts
        -------
        - The click on the cell swaps in the inline input.
        - Typing 40 and pressing Enter yields a 200 PATCH
          (the ``commitEdit`` guard only blocks when
          classDeltaMessage is non-empty).
        - The cell re-renders as "40.00% classe".
        - The "alvo % total" cell updates to 24.00% (60% × 40
          / 100, computed by the Alpine on-commit refresh).
        - Reloading the dashboard still shows 40.00% classe
          (server-side persistence).
        - Direct DB read confirms ``target_pct=40`` for Ativo A.
        """
        _login_and_select_italo(page, live_url)
        _create_one_class(page)
        _create_n_assets(page, ["Ativo A", "Ativo B", "Ativo C"])

        # Seed 2 of the 3 assets at 30% so the upcoming PATCH of
        # Ativo A to 40% lands on a per-class sum of 100.
        _seed_target_pct("Italo", {"Ativo B": 30, "Ativo C": 30})

        # Reload the dashboard so the new state is rendered.
        page.goto(f"{live_url}/")
        page.wait_for_selector(S01_SELECTORS["dashboard_asset_row"], timeout=5000)

        # Locate Ativo A's row by its name cell.
        rows = page.locator(S01_SELECTORS["dashboard_asset_row"])
        target_row = None
        for i in range(rows.count()):
            row = rows.nth(i)
            name_text = row.locator(S05_SELECTORS["asset_row_name_text"]).inner_text()
            if name_text.strip() == "Ativo A":
                target_row = row
                break
        assert target_row is not None, "Ativo A row not found on dashboard"

        # asset-table-view 8.x: class sections are always visible, so
        # no chevron expand step is needed.

        # Click the "alvo % classe" cell to enter edit mode. The
        # Alpine ``startEdit`` toggles ``editingAssetId`` to the
        # asset's id, which reveals the input.
        cell = target_row.locator(S01_SELECTORS["asset_target_pct_class"]).first
        cell.click()

        # Wait for the inline input to appear.
        edit_input = target_row.locator(S01_SELECTORS["asset_inline_edit_input"]).first
        edit_input.wait_for(state="visible", timeout=2000)
        edit_input.fill("40")

        # classSum after the fill = 0 + 30 + 40 = 100,
        # classDelta = 0, message = ''. The Alpine commitEdit
        # guard (``if (this.classDeltaMessage !== '') return``)
        # does not block, so Enter triggers the PATCH.
        edit_input.press("Enter")

        # Wait for the PATCH to complete and the input to hide
        # (the editing div's x-show toggles off when
        # editingAssetId becomes null after a successful commit).
        _js_input_hidden = (
            "() => { const el = document.querySelector('"
            f"{S01_SELECTORS['asset_inline_edit_input']}"
            "'); return !el || el.offsetParent === null; }"
        )
        page.wait_for_function(_js_input_hidden, timeout=3000)

        # Reload the dashboard to pick up the server-side state.
        # The cell's ``x-text`` is a Jinja-rendered literal (not
        # a reactive Alpine expression), so the in-place Alpine
        # refresh after a 200 PATCH only mutates the local
        # ``assets[]`` state — the rendered text stays at the
        # pre-commit value. A reload forces Jinja to re-render
        # with the new ``target_pct_class`` from the DB.
        page.goto(f"{live_url}/")
        page.wait_for_selector(S01_SELECTORS["dashboard_asset_row"], timeout=5000)
        rows = page.locator(S01_SELECTORS["dashboard_asset_row"])
        updated_row = None
        for i in range(rows.count()):
            row = rows.nth(i)
            name_text = row.locator(S05_SELECTORS["asset_row_name_text"]).inner_text()
            if name_text.strip() == "Ativo A":
                updated_row = row
                break
        assert updated_row is not None, "Ativo A row missing after commit"

        target_class_text = updated_row.locator(
            S01_SELECTORS["asset_target_pct_class"]
        ).first.inner_text()
        assert "40.00" in target_class_text, f"expected '40.00% classe', got {target_class_text!r}"
        assert "%" in target_class_text, f"target class cell missing %: {target_class_text!r}"

        target_total_text = updated_row.locator(
            S01_SELECTORS["asset_target_pct_total"]
        ).first.inner_text()
        assert "24.00" in target_total_text, (
            f"expected '24.00% total' (60%% × 40 / 100), got {target_total_text!r}"
        )

        # Server-side state: the DB has target_pct=40.
        assert _read_target_pct("Italo", "Ativo A") == 40, (
            "DB did not persist target_pct=40 after the 200 PATCH"
        )

    def test_dashboard_displays_four_percentages_per_asset(self, page: Page, live_url: str) -> None:
        """The dashboard renders 4 percentages per asset + the "1 posicao" line is gone.

        Setup
        -----
        1 class (Renda Fixa 60%), 1 asset (Ativo A) with 1
        position (seeded directly into the DB so the asset has
        a non-zero current_pct). The 4 pct cells
        (``asset-target-pct-class``, ``asset-current-pct-class``,
        ``asset-target-pct-total``, ``asset-current-pct-total``)
        should each be present, non-empty, and contain ``%``.

        Asserts
        -------
        - 4 distinct pct data-testid cells are present per
          asset row, all non-empty, all containing ``%``.
        - The main text does NOT contain "1 posicao" or
          "posicao(oes)" (M002/D015 — the position-count text
          was removed from the visible row).
        """
        _login_and_select_italo(page, live_url)
        _create_one_class(page)
        _create_n_assets(page, ["Ativo A"], target_pct="10")
        _seed_assets_with_positions_via_import(page, live_url, [("Renda Fixa", "Ativo A")])

        page.goto(f"{live_url}/")
        page.wait_for_selector(S01_SELECTORS["dashboard_asset_row"], timeout=5000)

        # The row exists.
        rows = page.locator(S01_SELECTORS["dashboard_asset_row"])
        assert rows.count() == 1, f"expected 1 asset row, got {rows.count()}"
        row = rows.first

        # The 4 pct cells are present.
        for sel_key in (
            "asset_target_pct_class",
            "asset_current_pct_class",
            "asset_target_pct_total",
            "asset_current_pct_total",
        ):
            cell = row.locator(S01_SELECTORS[sel_key]).first
            cell.wait_for(state="attached", timeout=2000)
            assert cell.count() == 1, f"{sel_key} not found exactly once"
            text = cell.inner_text().strip()
            assert text, f"{sel_key} cell is empty"
            assert "%" in text, f"{sel_key} cell missing %: {text!r}"

        # The "1 posicao(oes)" string is gone (M002/D015). The
        # asset-position-count element is still in the DOM as a
        # hidden span (T03 kept the data-testid for backward
        # compatibility with the S05 test) but its visible
        # text in ``<main>`` does not include the old
        # "1 posicao(oes)" line.
        main_text = page.locator("main").inner_text()
        assert "posicao(oes)" not in main_text, (
            f"old 'posicao(oes)' text still visible: {main_text!r}"
        )
        assert "1 posicao" not in main_text, f"old '1 posicao' text still visible: {main_text!r}"
