"""Reusable S04 import-journey browser setup."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Any

from tests.e2e.selectors import SELECTORS

UNMATCHED_NAMES = ["MXRF11", "BPAC11", "HGLG11", "XPLG11", "VINO11"]
MATCHED_NAMES: list[str] = [
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "ABEV3",
    "MGLU3",
    "BBAS3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "B3SA3",
    "SUZB3",
    "CSAN3",
    "PETR3",
    "VBBR3",
    "PRIO3",
    "IVVB11",
    "IVV",
    "VOO",
    "QQQ",
    "SMH",
    "SOXX",
    "VTI",
    "SPY",
    "VT",
    "HASH11",
    "BTLG11",
    "KNCR11",
    "IRDM11",
    "XPML11",
    "VISC11",
    "BRCR11",
    "TORD11",
    "MALL11",
    "DEVA11",
    "RBVA11",
    "VRTA11",
    "BPRP11",
    "PVBI11",
    "HCTR11",
    "XPIN11",
    "Tesouro Selic 2029",
    "Tesouro IPCA+ 2035",
]
RF_POS_NAMES = {
    "HASH11",
    "BTLG11",
    "KNCR11",
    "IRDM11",
    "XPML11",
    "VISC11",
    "BRCR11",
    "TORD11",
    "MALL11",
    "DEVA11",
    "RBVA11",
    "VRTA11",
    "BPRP11",
    "PVBI11",
    "HCTR11",
    "XPIN11",
    "Tesouro Selic 2029",
    "Tesouro IPCA+ 2035",
}
ACOES_NAMES = {
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "ABEV3",
    "MGLU3",
    "BBAS3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "B3SA3",
    "SUZB3",
    "CSAN3",
    "PETR3",
    "VBBR3",
    "PRIO3",
    "IVVB11",
}
RESERVA_NAMES = {"IVV", "VOO", "QQQ", "SMH", "SOXX", "VTI", "SPY", "VT"}


def login_and_select_italo(page: Any, base_url: str) -> None:
    """Drive direct-landing login for Italo."""
    page.goto(f"{base_url}/login")
    page.fill(SELECTORS["login_user"], "Italo")
    page.fill(SELECTORS["login_pass"], "test-password")
    page.click(SELECTORS["login_submit"])
    page.wait_for_url(re.compile(r"/$"))


def create_classes_via_form(page: Any, base_url: str, classes: list[tuple[str, int]]) -> None:
    """Submit snapshot class editor form through authenticated browser fetch."""
    page.evaluate(
        """async ({ url, cls }) => {
            const fd = new FormData();
            for (const [name, pct] of cls) {
                fd.append('name[]', name);
                fd.append('target_pct[]', String(pct));
            }
            const r = await fetch(url, { method: 'POST', body: fd });
            if (!r.ok) {
                throw new Error('POST /classes ' + r.status + ': ' + await r.text());
            }
        }""",
        {"url": f"{base_url}/classes", "cls": classes},
    )


def create_three_classes(page: Any, base_url: str) -> None:
    """Create the canonical S04 RF Pós / Acoes / Reserva class setup."""
    create_classes_via_form(page, base_url, [("RF Pós", 60), ("Acoes", 30), ("Reserva", 10)])
    page.goto(f"{base_url}/")
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)
    assert page.locator(SELECTORS["class_summary_row"]).count() == 3


def seed_43_assets(page: Any) -> None:
    """Seed S04's 43 auto-matched assets through the JSON API."""
    class_ids: dict[str, int] = page.evaluate(
        """() => {
            const rows = document.querySelectorAll('[data-testid="class-summary-row"]');
            const result = {};
            for (const row of rows) {
                const nameEl = row.querySelector('[data-testid="class-section-name"]');
                const name = nameEl ? nameEl.textContent.trim() : '';
                result[name] = parseInt(row.getAttribute('data-class-id'), 10);
            }
            return result;
        }"""
    )
    assert "RF Pós" in class_ids, f"RF Pós not found in class_ids: {class_ids}"
    assert "Acoes" in class_ids, f"Acoes not found in class_ids: {class_ids}"
    assert "Reserva" in class_ids, f"Reserva not found in class_ids: {class_ids}"

    for asset_name in MATCHED_NAMES:
        class_id = (
            class_ids["RF Pós"]
            if asset_name in RF_POS_NAMES
            else class_ids["Acoes"]
            if asset_name in ACOES_NAMES
            else class_ids["Reserva"]
        )
        success = page.evaluate(
            """async ({ name, class_id }) => {
                const r = await fetch('/api/assets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, asset_class_id: class_id }),
                });
                return r.status === 201;
            }""",
            {"name": asset_name, "class_id": class_id},
        )
        assert success, f"Failed to create asset {asset_name!r} via API"
    page.goto(page.url)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)


def debug_dump(page: Any, tag: str, *, directory: Path = Path("/tmp/s04_e2e_debug")) -> None:
    """Write screenshot, page text, and URL for import-journey post-mortem."""
    os.makedirs(directory, exist_ok=True)
    page.screenshot(path=str(directory / f"{tag}.png"), full_page=True)
    with (directory / f"{tag}.txt").open("w") as output:
        output.write(f"URL: {page.url}\n\n")
        try:
            output.write("MAIN TEXT:\n")
            output.write(page.locator("main").inner_text())
        except Exception as exc:
            output.write(f"main inner_text failed: {exc}\n")


def seed_assets_with_positions_via_import(
    page: Any,
    live_url: str,
    class_assignments: list[tuple[str, str]],
    positions: dict[str, tuple[float, float]] | None = None,
) -> None:
    """Drive the dashboard import modal with a small inline CSV.

    Builds a 1-line-header + N-data-rows CSV in /tmp, uploads via
    dashboard import modal (existing flow), auto-matches everything
    (no unmatched names), commits. End state: N assets with 1
    position each, assigned to the requested classes.

    Replaces _seed_one_position_for_asset and _seed_positions,
    which violated the project's "assets come from import, never
    from seed" rule (AGENTS.md).
    """
    csv_path = Path("/tmp") / f"omaha-test-{uuid.uuid4().hex[:8]}.csv"
    with csv_path.open("w") as f:
        f.write('"Posicao consolidada","Cliente: TEST"\n')
        # broker-csv-import-totals: include ``Total investido`` /
        # ``Total atual`` columns so the parsed positions carry the
        # broker-published totals. Without these, the dashboard's
        # portfolio header (gated on current_value > 0) hides and
        # downstream e2e selectors that wait on it timeout. We use
        # ``R$`` prefix + BR-milhar to exercise the parser's
        # number-format path the same way the real broker CSV does.
        f.write(
            "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,"
            "Total investido,Total atual,Minha Categoria\n"
        )
        for class_name, asset_name in class_assignments:
            qty, price = (positions or {}).get(asset_name, (100.0, 100.0))
            total_invested = qty * 100.00
            total_current = qty * price

            # Use BR-milhar formatting for prices > 1000 so the
            # parser exercises the dot-as-thousands path.
            def _fmt(value: float) -> str:
                # Renders 12345.67 → "12.345,67"; small values stay
                # as "100,00".
                s = f"{value:,.2f}"
                return s.replace(",", "X").replace(".", ",").replace("X", ".")

            f.write(
                f"{asset_name},{asset_name},{qty:.2f},100.00,{price:.2f},"
                f'"R$ {_fmt(total_invested)}","R$ {_fmt(total_current)}",{class_name}\n'
            )

    # Drive the modal — reuse the flow from test_import_user_journey.py
    page.click(SELECTORS["dashboard_import_btn"])
    page.wait_for_selector('[data-testid="import-modal-overlay"]', state="visible", timeout=5000)
    page.wait_for_timeout(300)  # Alpine modal mounts
    page.set_input_files(SELECTORS["import_file_input"], str(csv_path))
    page.wait_for_selector(SELECTORS["import_commit_btn"], timeout=10000)
    # No unmatched — direct commit
    page.click(SELECTORS["import_commit_btn"], force=True)
    page.wait_for_timeout(300)
    error_text = ""
    try:
        error_el = page.locator(SELECTORS["import_commit_error"])
        if error_el.count() and error_el.is_visible():
            error_text = error_el.inner_text()
    except Exception:
        pass
    if error_text:
        raise RuntimeError(f"import commit failed: {error_text}")
    page.wait_for_selector('[data-testid="import-modal-overlay"]', state="hidden", timeout=10000)
    csv_path.unlink(missing_ok=True)  # cleanup


def login_as_italo(page: Any, base_url: str) -> None:
    """Drive direct-landing login for Italo (visual suite compatible)."""
    page.goto(f"{base_url}/login")
    page.fill(SELECTORS["login_user"], "Italo")
    page.fill(SELECTORS["login_pass"], "test-password")
    page.click(SELECTORS["login_submit"])
    page.wait_for_url(f"{base_url}/")
