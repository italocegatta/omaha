"""F52 regression — bridge charts must self-heal when echarts arrives late.

On a cold load (hard refresh) the vendored ``echarts.min.js`` may still
be downloading when Alpine's ``x-init`` microtask invokes
``renderBridgeChart``: Alpine starts at its own ``defer`` execution
(readyState is already ``'interactive'``), before the later echarts
defer script has run. Before the fix the helper's silent
``if (!window.echarts) return`` left every chart uninitialized forever
(no chart instance, no ResizeObserver/registry entry to recover it).

The bug is invisible on localhost, where the 1.1 MB bundle downloads
instantly — so this suite intercepts the echarts route and fulfills it
~700 ms late, reproducing the cold-load race deterministically. The
delayed test FAILS without the requestAnimationFrame retry in
``renderBridgeChart`` and PASSES with it; the warm test locks the
instant-load path against regressions in the retry itself.

Lane: files under ``tests/e2e/`` are intentionally left un-marker'd
(marker rule in ``tests/conftest.py`` — Playwright suites are filtered
by path and run via ``task test-e2e``), so no marker registration is
required for this file.
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

from tests.e2e.conftest import (
    _seed_assets_with_positions_via_import,
    _set_asset_target_pcts_via_db,
)
from tests.support.constants import REPO_ROOT

from .selectors import SELECTORS
from .test_import_user_journey import _create_three_classes, _login_and_select_italo
from .test_rebalance_page import _disable_quotes_for_rebalance_fixture

ECHARTS_URL_RE = re.compile(r"/static/vendor/echarts\.min\.js$")
ECHARTS_PATH = REPO_ROOT / "src" / "omaha" / "static" / "vendor" / "echarts.min.js"
# Long enough that Alpine's x-init always fires first, short enough to
# keep the suite fast.
ECHARTS_DELAY_S = 0.7

_CHART_SEL = '[data-testid="rebalance-class-chart"]'

_ALL_CHARTS_HAVE_SVG_JS = (
    "() => {"
    f"  const charts = document.querySelectorAll('{_CHART_SEL}');"
    "  if (charts.length === 0) return false;"
    "  return Array.from(charts).every((el) => el.querySelector('svg') !== null);"
    "}"
)


def _delay_echarts(route: Route) -> None:
    """Fulfill the vendored echarts bundle late, with no-store headers.

    Serving from disk (instead of ``route.fetch``) with an explicit
    ``Cache-Control: no-store`` guarantees every navigation — including
    the PRG redirect after the aporte submit — goes through the delay,
    so ``window.echarts`` is undefined when Alpine's x-init fires.
    """
    time.sleep(ECHARTS_DELAY_S)
    route.fulfill(
        status=200,
        content_type="application/javascript",
        headers={"Cache-Control": "no-store"},
        path=str(ECHARTS_PATH),
    )


def _seed_plan_fixture(page: Page, live_url: str, prefix: str) -> None:
    """Seed 3 classes with positions/targets so a plan can render."""
    _seed_assets_with_positions_via_import(
        page,
        live_url,
        [
            ("RF Pós", f"{prefix}_A"),
            ("Acoes", f"{prefix}_B"),
            ("Reserva", f"{prefix}_C"),
        ],
        positions={
            f"{prefix}_A": (100.0, 100.0),
            f"{prefix}_B": (100.0, 100.0),
            f"{prefix}_C": (100.0, 100.0),
        },
    )
    # CSV import leaves target_pct=0; the CVXPY engine rejects that.
    _set_asset_target_pcts_via_db(
        {f"{prefix}_A": 100.0, f"{prefix}_B": 100.0, f"{prefix}_C": 100.0},
    )


def _submit_aporte_and_wait_for_plan(page: Page) -> None:
    """Navigate to /rebalanceamento, submit aporte 5000, wait for the
    server-rendered plan payload."""
    page.click(SELECTORS["app_tab_btn_rebalanceamento"])
    page.wait_for_url(re.compile(r"/rebalanceamento$"))
    page.wait_for_selector(SELECTORS["rebalance_form"], timeout=5000)

    contribution = page.locator(SELECTORS["rebalance_contribution_input"])
    contribution.fill("5000")
    contribution.press("Enter")
    page.wait_for_function(
        """() => {
            const el = document.querySelector('[data-testid="rebalance-plan-data"]');
            return el && JSON.parse(el.textContent).metrics.contribution === 5000;
        }""",
        timeout=10000,
    )


class TestRebalanceChartColdLoad:
    """Bridge charts render even when echarts.min.js arrives late (F52)."""

    def test_bridge_charts_self_heal_when_echarts_is_delayed(
        self, page: Page, live_url: str
    ) -> None:
        """Cold-load race: echarts lands ~700 ms after x-init; every
        chart container must still end up with an SVG (retry fix)."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)
        _disable_quotes_for_rebalance_fixture()
        _seed_plan_fixture(page, live_url, "COLD")

        # Delay echarts on every request for this page, then load the
        # plan. Alpine's x-init fires while window.echarts is undefined.
        page.route(ECHARTS_URL_RE, _delay_echarts)
        _submit_aporte_and_wait_for_plan(page)

        # The retry loop must self-heal every chart once echarts lands.
        page.wait_for_function(_ALL_CHARTS_HAVE_SVG_JS, timeout=15000)
        chart_count = page.locator(_CHART_SEL).count()
        assert chart_count >= 1, "expected at least one bridge chart container"
        svg_count = page.evaluate(f"() => document.querySelectorAll('{_CHART_SEL} svg').length")
        assert svg_count == chart_count, (
            f"{svg_count}/{chart_count} bridge charts carry an SVG after the "
            "delayed echarts load — the retry did not initialize every chart."
        )

    def test_bridge_charts_render_on_warm_load(self, page: Page, live_url: str) -> None:
        """Instant echarts (normal localhost condition) still renders
        every bridge chart — guards the retry change itself."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)
        _disable_quotes_for_rebalance_fixture()
        _seed_plan_fixture(page, live_url, "WARM")

        _submit_aporte_and_wait_for_plan(page)

        page.wait_for_function(_ALL_CHARTS_HAVE_SVG_JS, timeout=10000)
        chart_count = page.locator(_CHART_SEL).count()
        assert chart_count >= 1, "expected at least one bridge chart container"
