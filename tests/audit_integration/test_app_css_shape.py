"""Integration tests for the live ``src/omaha/static/app.css`` shape.

Verifies two Phase-2 structural guarantees that read the production
CSS file directly:

* the two ``*.delete-confirm-yes`` rules use ``var(--negative-ink)``
  for their text colour (no hardcoded ``#fff``)
* the Phase-2-corrected tokens (``--class-4``, ``--class-6``,
  ``--error-bg``, ``--error-fg``, ``--negative-ink``,
  ``--positive-ink``) resolve to OKLCH, not hex

These are marked ``@pytest.mark.integration`` so they run with the
audit-integration subset (``task test-integration``), not with the
fast unit subset (``task test-unit``).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from omaha.audit.css_parser import color_token_inventory, parse_stylesheet

APP_CSS_PATH = Path(__file__).resolve().parents[2] / "src" / "omaha" / "static" / "app.css"

pytestmark = pytest.mark.integration


# Tokens whose value must parse as OKLCH (not hex) after Phase 2.
_OKLCH_ONLY_TOKENS = (
    "--class-4",
    "--class-6",
    "--error-bg",
    "--error-fg",
    "--negative-ink",
    "--positive-ink",
)


def test_delete_confirm_no_white() -> None:
    """The two delete-confirm rules must not hardcode ``color: #fff``.

    Phase 2 replaced the hardcoded white with ``var(--negative-ink)``
    so the foreground tracks the negative fill across theme changes.
    """
    css = APP_CSS_PATH.read_text(encoding="utf-8")

    for selector in (
        ".class-delete-confirm-yes",
        ".dashboard-asset-delete-confirm-yes",
    ):
        pattern = re.compile(
            rf"{re.escape(selector)}\s*\{{([^}}]*)\}}",
            re.MULTILINE,
        )
        match = pattern.search(css)
        assert match is not None, f"Rule {selector!r} not found in app.css"
        body = match.group(1)
        assert "color: #fff" not in body, (
            f"{selector} still hardcodes 'color: #fff' — must use var(--negative-ink)"
        )
        assert "var(--negative-ink)" in body, (
            f"{selector} must reference 'var(--negative-ink)' for its text color"
        )


@pytest.mark.parametrize("token", _OKLCH_ONLY_TOKENS)
def test_corrected_tokens_are_oklch(token: str) -> None:
    """Tokens corrected in Phase 2 resolve to OKLCH (no hex)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    assert token in by_name, f"{token} missing from inventory"
    value = by_name[token].computed_value.lower()
    assert value.startswith("oklch"), f"{token} = {value!r} — Phase 2 requires OKLCH, not hex"
