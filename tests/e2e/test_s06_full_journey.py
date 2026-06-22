"""Real-browser E2E for the M002/S06 full import journey with posicao_italo.csv.

Drives a headless chromium against a live uvicorn instance to
verify the complete import flow using the user's real broker
statement, including the automatic class association via
``suggest_class_id`` (the backend fix for the bug where the
Alpine store always picked ``classes[0].id`` for every unmatched
row regardless of the broker's "Minha Categoria" column).

This test is critical because:

1. The import + class association is the app's primary user loop.
2. The previous e2e tests (S04) used ``sample_broker.csv`` which
   has only 5 unmatched rows and ALL rows get the same first-class
   assignment -- the bug was masked by the fact that the old fixture's
   unmatched rows mostly belonged to the same class.
3. ``posicao_italo.csv`` has 8 distinct categories
   (Internacional, RF Pos, RF Dinamica, Acoes, FII,
   BR Dividendos, Cripto, Nao configurado) which exercises
   the exact-match, substring-match, and no-match paths of
   ``suggest_class_id``.

What the test covers
--------------------
  login -> select profile -> create 5 classes matching CSV
  categories (RF Pos, RF Dinamica, Acoes, FII, Internacional)
  -> open import modal -> upload posicao_italo.csv ->
  verify suggested_class_id from the server for each category:
    - Internacional rows -> Internacional class
    - RF Pos rows -> RF Pos class
    - RF Dinamica rows -> RF Dinamica class
    - Acoes rows -> Acoes class
    - FII rows -> FII class
    - BR Dividendos / Cripto / Nao configurado -> None (first class)
  -> assign the remaining unmatched rows manually ->
  commit -> verify assets on dashboard with positions

References
----------
- M002/S06: Posicao Italo CSV import + automatic class association
- S04: Dashboard import modal infrastructure
- csv_import.suggest_class_id: The 2-tier matcher (exact + substring)
- The bug: Alpine store's uploadFile() used classes[0].id for ALL
  unmatched rows instead of the server-suggested class_id.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from omaha.csv_import import parse_positions

from .test_s04_user_journey import _login_and_select_italo

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "posicao_italo.csv"

# Per-ticker expected class map. The M002/S06 fixture has 48 unique tickers;
# each ticker's expected class is derived from its broker category, with
# manual overrides for the 3 categories the matcher cannot resolve
# (BR Dividendos / Cripto / (Nao configurado)).
_MANUAL_OVERRIDES: dict[str, str] = {
    "BR Dividendos": "FII",
    "Cripto": "Internacional",
    "(Não configurado)": "RF Pos",
}

# The 5 classes the test creates, matching CSV categories.
CLASS_NAMES = [
    "RF Pos",
    "RF Dinamica",
    "Acoes",
    "FII",
    "Internacional",
]

# Known suggested_category -> expected_class mapping via suggest_class_id.
# The server's suggest_class_id() does exact normalized match first
# (Tier 1) then one-way substring (Tier 2).
#
# Exact matches (Tier 1):
#   "RF Pos" -> normalize("RF Pos") = "rf pos" == normalize("RF Pos") ✓
#   "RF Dinamica" -> normalize("RF Dinamica") = "rf dinamica" ✓
#   "Acoes" -> normalize("Acoes") = "acoes" == normalize("Acoes") ✓
#   "FII" -> normalize("FII") = "fii" == normalize("FII") ✓
#   "Internacional" -> normalize("Internacional") = "internacional" ✓
#
# Substring matches (Tier 2):
#   "Acoes" (from CSV "Ações") -> normalize("Ações") = "acoes"
#     -> substring of "Acoes" ✓
#
# No matches:
#   "BR Dividendos" -> normalize("br dividendos") doesn't match any class
#   "Cripto" -> normalize("cripto") doesn't match any class
#   "(Nao configurado)" -> normalize("nao configurado") doesn't match
CATEGORY_CLASS_MAP: dict[str, str | None] = {
    # Exact match (Tier 1): category normalizes to the same string
    # as the class name.
    "Internacional": "Internacional",
    "RF Pós": "RF Pos",  # normalize("RF Pós") = "rf pos" == normalize("RF Pos")
    "RF Dinâmica": "RF Dinamica",  # normalize("RF Dinâmica") = "rf dinamica"
    "Ações": "Acoes",  # normalize("Ações") = "acoes" == normalize("Acoes")
    "FII": "FII",
    # These categories have no exact or substring match with any
    # of the 5 classes so suggest_class_id returns None:
    "BR Dividendos": None,
    "Cripto": None,
    "(Não configurado)": None,
}

# Selectors reused from S04/S05 with the same data-testid markers.
SELECTORS = {
    "login_user": 'input[name="username"]',
    "login_pass": 'input[name="password"]',
    "login_submit": 'button[type="submit"]',
    "profile_picker": "form.profile-picker button",
    "class_summary_row": '[data-testid="class-summary-row"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "dashboard_import_btn": '[data-testid="dashboard-import-btn"]',
    "import_modal_overlay": '[data-testid="import-modal-overlay"]',
    "import_file_input": '[data-testid="import-file-input"]',
    "import_matched_summary": '[data-testid="import-matched-summary"]',
    "import_unmatched_table": '[data-testid="import-unmatched-table"]',
    "import_unmatched_row": '[data-testid="import-unmatched-row"]',
    "import_commit_btn": '[data-testid="import-commit-btn"]',
    "import_assignment_class": '[data-testid="import-assignment-class"]',
    "profile_name": '[data-testid="profile-name"]',
    "class_section_name": '[data-testid="class-section-name"]',
}


def _debug_dump(page: Page, tag: str) -> None:
    import os

    os.makedirs("/tmp/s06_e2e_debug", exist_ok=True)
    page.screenshot(path=f"/tmp/s06_e2e_debug/{tag}.png", full_page=True)
    with open(f"/tmp/s06_e2e_debug/{tag}.txt", "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")


def _create_seed_classes(page: Page, classes: list[tuple[str, int]]) -> None:
    """Create classes via fetch POST /classes (snapshot form), then reload.

    The snapshot form accepts parallel name[]/target_pct[] arrays
    and requires the per-profile sum to equal 100.
    """
    page.evaluate(
        """async (items) => {
            const fd = new FormData();
            for (const [name, pct] of items) {
                fd.append('name[]', name);
                fd.append('target_pct[]', String(pct));
            }
            const r = await fetch('/classes', { method: 'POST', body: fd });
            if (!r.ok) {
                throw new Error('POST /classes ' + r.status + ': ' + await r.text());
            }
        }""",
        classes,
    )
    page.goto(page.url)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=8000)
    assert page.locator(SELECTORS["class_summary_row"]).count() == len(classes)


class TestS06PosicaoItaloImport:
    """End-to-end test for importing posicao_italo.csv with class association.

    Tests both the happy path (import works end to end) and the
    specific fix: that the server suggests correct ``suggested_class_id``
    for unmatched rows based on the broker's "Minha Categoria" column,
    and the Alpine store uses that suggestion instead of always picking
    the first class.
    """

    def test_import_posicao_italo_with_class_association(self, page: Page, live_url: str) -> None:
        """Full import journey with posicao_italo.csv and class association.

        Setup
        -----
        Login -> create 5 classes (RF Pos, RF Dinamica, Acoes, FII,
        Internacional) at 20% each.
        No pre-existing assets -- every CSV row is unmatched.

        Steps
        -----
        1. Open import modal, upload posicao_italo.csv.
        2. Read the Alpine store's assignments (post-uploadFile) and
           verify that rows in each category got the correct suggested
           class_id from the server.
        3. Override BR Dividendos, Cripto, and (Nao configurado) rows
           since their suggested_class_id is None and default to the
           first class (RF Pos).
        4. Commit the import.
        5. Verify the dashboard shows assets with positions.

        Asserts
        -------
        - At least EXPECTED_MIN_PARSED rows were parsed.
        - Every category that has a matching class has the correct
          class_id suggested by the server.
        - Rows with no matching category get default to first class.
        - After commit, the dashboard shows asset rows with >= 1 position.
        """
        # ------------------------------------------------------------------
        # Setup: login + create 5 classes matching CSV categories
        # ------------------------------------------------------------------
        _login_and_select_italo(page, live_url)

        # Derive the expected parsed-row count + per-ticker expected class
        # from the fixture + the matcher rules. The fixture has 48 unique
        # tickers; each one maps to a class via its broker category, with
        # manual overrides for the 3 unmatched categories.
        parsed_positions = parse_positions(FIXTURE_PATH.read_text())
        expected_count = len(parsed_positions)
        expected_ticker_class: dict[str, str] = {}
        for p in parsed_positions:
            cat = (p.suggested_category or "").strip()
            expected = CATEGORY_CLASS_MAP.get(cat)
            if expected is None:
                expected = _MANUAL_OVERRIDES.get(cat)
            assert expected is not None, f"no class rule for category {cat!r}"
            expected_ticker_class[p.broker_ticker] = expected

        # Create 5 classes at 20% each (sum = 100).
        _create_seed_classes(page, [(name, 20) for name in CLASS_NAMES])

        # Build a name -> id map from the dashboard DOM.
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
        assert len(class_map) == 5, f"expected 5 classes, got {len(class_map)}: {class_map}"
        for name in CLASS_NAMES:
            assert name in class_map, f"class {name!r} not found in dashboard"

        # ------------------------------------------------------------------
        # Step 1: Open import modal and upload CSV
        # ------------------------------------------------------------------
        page.click(SELECTORS["dashboard_import_btn"])
        page.wait_for_selector(SELECTORS["import_modal_overlay"], state="visible", timeout=5000)

        page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
        page.wait_for_timeout(300)

        # Upload via the Alpine store.
        page.evaluate("Alpine.store('importModal').uploadFile()")

        # Wait for the modal to transition to step 2 (review).
        # The matched summary is hidden by Alpine x-show when there are
        # 0 auto-matched rows (no pre-existing assets), so we wait for
        # the unmatched table which is always visible in step 2.
        page.wait_for_selector(SELECTORS["import_unmatched_table"], state="visible", timeout=15000)

        # ------------------------------------------------------------------
        # Step 2: Read the Alpine store to verify class suggestions
        # ------------------------------------------------------------------
        store_data: dict = page.evaluate(
            """() => {
                const s = Alpine.store('importModal');
                return {
                    unmatched: s.unmatched.map(function(r) {
                        return {
                            broker_ticker: r.broker_ticker,
                            suggested_category: r.suggested_category,
                            suggested_class_id: r.suggested_class_id,
                        };
                    }),
                    assignments: Object.keys(s.assignments).reduce(function(acc, k) {
                        acc[k] = { class_id: s.assignments[k].class_id };
                        return acc;
                    }, {}),
                    assetClasses: s.assetClasses,
                };
            }"""
        )

        unmatched = store_data["unmatched"]
        assignments = store_data["assignments"]
        asset_classes = store_data["assetClasses"]

        assert len(unmatched) == expected_count, (
            f"expected exactly {expected_count} unmatched rows, got {len(unmatched)}"
        )

        # Build a ticker -> category lookup from the raw data.
        ticker_category: dict[str, str] = {}
        for r in unmatched:
            ticker_category[r["broker_ticker"]] = r["suggested_category"] or ""

        # Build a class name -> id map from the server response.
        ac_map: dict[str, int] = {ac["name"]: ac["id"] for ac in asset_classes}

        # ----- Verify suggested_class_id for each category (exact equality) -----
        mismatches: list[str] = []
        for r in unmatched:
            cat = (r["suggested_category"] or "").strip()
            expected_class = CATEGORY_CLASS_MAP.get(cat)
            ticker = r["broker_ticker"]

            if expected_class is not None:
                # This category should have a specific class suggestion.
                expected_id = ac_map.get(expected_class)
                if expected_id is not None and r["suggested_class_id"] != expected_id:
                    mismatches.append(
                            f"{ticker}: cat={cat!r} "
                            f"suggested={r['suggested_class_id']} "
                            f"expected={expected_id} ({expected_class})"
                        )
            else:
                # Categories with no match should have None suggested.
                # This applies to BR Dividendos, Cripto, (Nao configurado).
                if r["suggested_class_id"] is not None:
                    mismatches.append(
                        f"{ticker}: cat={cat!r} expected None suggestion "
                        f"but got {r['suggested_class_id']}"
                    )

        assert not mismatches, (
            f"{len(mismatches)}/{len(unmatched)} rows have incorrect "
            f"suggested_class_id. First 10: {mismatches[:10]}"
        )

        # ----- Verify the Alpine store assignments use suggested_class_id -----
        # For rows with a suggested_class_id, the assignment must match it.
        # For rows without (None), the assignment must be the empty string
        # — the user picks a class in the modal before commit. The commit
        # function (see src/omaha/templates/dashboard.html) skips rows with
        # empty class_id, so the test must override the empty ones before
        # calling commit. (See the page.evaluate block below.)
        wrong_assignments: list[str] = []
        for r in unmatched:
            ticker = r["broker_ticker"]
            assignment = assignments.get(ticker)
            if assignment is None:
                wrong_assignments.append(f"{ticker}: no assignment found")
                continue

            expected = r["suggested_class_id"] if r["suggested_class_id"] is not None else ""
            if assignment["class_id"] != expected:
                wrong_assignments.append(
                    f"{ticker}: assignment={assignment['class_id']!r} "
                    f"expected={expected!r} "
                    f"(suggested={r['suggested_class_id']!r})"
                )

        assert not wrong_assignments, (
            f"{len(wrong_assignments)} wrong Alpine assignments. First 10: {wrong_assignments[:10]}"
        )

        # ------------------------------------------------------------------
        # Step 2b: Verify the DOM <select> values match the server suggestion
        # ------------------------------------------------------------------
        # Read the actual select.value from the DOM (not just the Alpine
        # store) so the test catches a regression where the store has the
        # right value but the <select> renders with the placeholder option
        # selected. This is the regression guard for the
        # :value/@change -> x-model fix on the modal's <select> bindings.
        select_loc = page.locator(SELECTORS["import_assignment_class"])
        assert select_loc.count() == len(unmatched), (
            f"expected {len(unmatched)} <select> rows in DOM, got {select_loc.count()}"
        )
        dom_mismatches: list[str] = []
        matched_rows = 0
        for i, r in enumerate(unmatched):
            if r["suggested_class_id"] is None:
                continue
            matched_rows += 1
            expected_id = str(r["suggested_class_id"])
            actual_id = select_loc.nth(i).input_value()
            if actual_id != expected_id:
                dom_mismatches.append(
                    f"{r['broker_ticker']}: select.value={actual_id!r} expected={expected_id!r}"
                )
        assert matched_rows > 0, "expected at least one unmatched row with a server suggestion"
        assert not dom_mismatches, (
            f"{len(dom_mismatches)} DOM <select> values diverged from the "
            f"server suggestion. First 10: {dom_mismatches[:10]}"
        )

        # ------------------------------------------------------------------
        # Step 3: Override rows with no suggested category
        # ------------------------------------------------------------------
        # BR Dividendos, Cripto, (Nao configurado) rows have no suggestion
        # and default to the first class (RF Pos). Assign them to
        # appropriate classes:
        #   BR Dividendos -> FII (no exact match, user picks close class)
        #   Cripto -> Internacional (no exact match)
        #   (Nao configurado) -> RF Pos (no exact match, user picks default)
        page.evaluate(
            """() => {
                const s = Alpine.store('importModal');
                const fii = s.assetClasses.find(function(c) {
                    return c.name === 'FII';
                });
                const intl = s.assetClasses.find(function(c) {
                    return c.name === 'Internacional';
                });
                const rfPos = s.assetClasses.find(function(c) {
                    return c.name === 'RF Pos';
                });
                for (var ticker in s.assignments) {
                    if (s.assignments.hasOwnProperty(ticker)) {
                        var row = s.unmatched.find(function(r) {
                            return r.broker_ticker === ticker;
                        });
                        if (row) {
                            var cat = (row.suggested_category || '').trim();
                            if (cat === 'BR Dividendos' && fii) {
                                s.assignments[ticker].class_id = fii.id;
                            } else if (cat === 'Cripto' && intl) {
                                s.assignments[ticker].class_id = intl.id;
                            } else if (cat === '(Não configurado)' && rfPos) {
                                s.assignments[ticker].class_id = rfPos.id;
                            }
                        }
                    }
                }
            }"""
        )

        # ------------------------------------------------------------------
        # Step 4: Commit the import
        # ------------------------------------------------------------------
        page.click(SELECTORS["import_commit_btn"])

        # Wait for the page reload (modal calls window.location.reload()).
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                "'[data-testid=\"dashboard-asset-row\"]').length > 0",
                timeout=15000,
            )
        except Exception:
            _debug_dump(page, "post_commit_dashboard")
            raise

        # ------------------------------------------------------------------
        # Step 5: Verify assets on dashboard with positions
        # ------------------------------------------------------------------
        page.wait_for_load_state("networkidle", timeout=10000)
        dashboard_rows = page.locator(SELECTORS["dashboard_asset_row"])

        try:
            page.wait_for_function(
                f"() => document.querySelectorAll("
                f"'[data-testid=\"dashboard-asset-row\"]').length === {expected_count}",
                timeout=15000,
            )
        except Exception:
            _debug_dump(page, "post_commit_asset_count")
            raise

        row_count = dashboard_rows.count()
        assert row_count == expected_count, (
            f"expected exactly {expected_count} asset rows after import, got {row_count}"
        )

        # Verify asset rows have position counts.
        for i in range(row_count):
            row = dashboard_rows.nth(i)
            count_str = row.get_attribute("data-position-count")
            assert count_str is not None, f"row {i} missing data-position-count"
            count = int(count_str)
            assert count >= 1, f"row {i} has {count} positions, expected >= 1"

        # Verify every parsed ticker landed in the expected class.
        # Walk the dashboard DOM: each asset row lives inside a
        # .class-section whose data-testid="class-summary-row" carries
        # the class name in a [data-testid="class-section-name"] child.
        asset_class_map: dict[str, str] = page.evaluate(
            """() => {
                const out = {};
                document.querySelectorAll('.class-section').forEach((sec) => {
                    const nameEl = sec.querySelector('[data-testid="class-section-name"]');
                    if (!nameEl) return;
                    const className = nameEl.textContent.trim();
                    sec.querySelectorAll('[data-testid="dashboard-asset-row"]').forEach((row) => {
                        const assetNameEl = row.querySelector(
                            '[data-testid="asset-row-name-text"]'
                        );
                        if (assetNameEl) {
                            out[assetNameEl.textContent.trim()] = className;
                        }
                    });
                });
                return out;
            }"""
        )

        ticker_class_mismatches: list[str] = []
        for ticker, expected_class in expected_ticker_class.items():
            actual = asset_class_map.get(ticker)
            if actual is None:
                ticker_class_mismatches.append(f"{ticker}: not found on dashboard")
            elif actual != expected_class:
                ticker_class_mismatches.append(
                    f"{ticker}: expected class={expected_class!r} got {actual!r}"
                )

        assert not ticker_class_mismatches, (
            f"{len(ticker_class_mismatches)}/{len(expected_ticker_class)} "
            f"tickers landed in the wrong class. First 10: "
            f"{ticker_class_mismatches[:10]}"
        )

        # Verify some expected tickers appear on the dashboard.
        dashboard_text = page.locator("main").inner_text()
        for expected_ticker in ["SMH", "PRIO3", "BTC", "LVBI11"]:
            assert expected_ticker in dashboard_text, (
                f"expected ticker {expected_ticker!r} not found on dashboard"
            )

        # Verify the 5 classes still exist.
        class_rows = page.locator(SELECTORS["class_summary_row"])
        assert class_rows.count() == 5, (
            f"expected 5 class rows after import, got {class_rows.count()}"
        )
