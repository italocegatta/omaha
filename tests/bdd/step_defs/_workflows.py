"""BDD workflow library — single source of truth for repeated UI sequences.

The pytest-bdd suite under :mod:`tests.bdd` follows the
**workflow + wrapper** pattern: any multi-step Gherkin sequence
that appears in ≥2 scenarios with a clear growth trend is
extracted into a Python workflow here and exposed to scenarios
via a thin step-definition wrapper.

Why this lives in ``_workflows.py`` (not a step-definition
module):

- This file has no ``@given`` / ``@when`` / ``@then`` decorators.
  pytest-bdd therefore does NOT try to register step definitions
  from it — the module is a library, not a step registry.
- Workflows take ``page`` and ``live_url`` as positional args so
  wrappers can call them transparently with the same signature
  shape that pytest-bdd binds step args.
- Each workflow documents (a) its pre-condition, (b) the
  ``data-testid`` selectors it touches, and (c) raises
  ``RuntimeError`` with an actionable message when the
  pre-condition fails.

The dataclasses (:class:`ClassSpec`, :class:`AssetSpec`) are the
canonical input shape for the workflows that create domain
objects. The two module-level constants
(:data:`DEFAULT_TWO_CLASSES`, :data:`DEFAULT_FOUR_ASSETS`) are
the "happy path" payloads — ``None`` on the workflow's
``classes`` / ``assets`` kwarg means "use the default".

Threshold for extraction: **≥2 scenarios with growth trend**
(not ≥3). The suite today has 30 scenarios; new feature files
are expected to land that share these bootstraps. Without
extraction, a business-rule change in any flow (login, class
creation, asset modal) requires editing N ``.feature`` files
by hand. With extraction, the operator edits ONE workflow and
all scenarios inherit the new behavior.

Ceiling: ≤10 public workflows. Above that, re-evaluate whether
the suite shares enough structure to justify another workflow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tests.bdd.step_defs._carve_out import carve_out

if TYPE_CHECKING:
    from playwright.sync_api import Page


@dataclass(frozen=True)
class ClassSpec:
    """One asset class to create via the snapshot editor.

    Attributes:
        name: Human-readable class name (e.g. ``"RF Pós"``).
        target_pct: Portfolio-level target percentage (0-100).
            The snapshot editor enforces sum-to-100 across all
            rows; the workflow itself does not validate that —
            it surfaces whatever the editor returns.
    """

    name: str
    target_pct: int


@dataclass(frozen=True)
class AssetSpec:
    """One asset to create via the dashboard per-class modal.

    Attributes:
        class_name: Name of the (already-existing) class the
            asset belongs to. Used to pick the right per-class
            ``+ Ativo`` button on the dashboard.
        ticker: Asset name shown in the dashboard asset table.
            Convention: uppercase with underscores (e.g.
            ``"TESOURO_SELIC_2029"``).
        target_pct: Within-class target percentage (0-100). The
            modal enforces sum-to-100 across assets within the
            same class.
    """

    class_name: str
    ticker: str
    target_pct: int


DEFAULT_TWO_CLASSES: list[ClassSpec] = [
    ClassSpec("RF Pós", 50),
    ClassSpec("RF Dinâmica", 50),
]


DEFAULT_FOUR_ASSETS: list[AssetSpec] = [
    AssetSpec("RF Pós", "TESOURO_SELIC_2029", 60),
    AssetSpec("RF Pós", "CDB_LIQUIDEZ_2027", 40),
    AssetSpec("RF Dinâmica", "FII_HSML11", 30),
    AssetSpec("RF Dinâmica", "ACAIO_PETR4", 70),
]


@carve_out(
    files=frozenset({"login.feature"}),
    step_regex=r"estou logado como",
)
def login_and_land(
    page: Page,
    live_url: str,
    profile: str,
    password: str = "test-password",
) -> None:
    """Log in and land directly on the operator's own dashboard.

    direct-landing-with-header-profile-switcher: ``POST /login``
    auto-binds ``active_profile_id`` to the logged-in user's first
    profile (by ``display_order``) and 303s to ``/``. There is no
    intermediate ``/profiles`` picker page — login lands directly
    on the dashboard.

    The function is renamed from ``login_and_pick_profile`` to
    ``login_and_land`` to reflect the new flow. The carve-out
    shrinks: only ``login.feature`` (which exercises the picker
    carve-out path for the wrong-password case) is exempt;
    ``profile_isolation.feature`` is renamed/repurposed in this
    change (it inherits the new flow).

    data-testids:
      - input[name=username]
      - input[name=password]
      - button[type=submit]
    """
    page.goto(f"{live_url}/login")
    page.fill('input[name="username"]', profile)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url(re.compile(r"/$"), timeout=5000)


def create_one_class(page: Page, live_url: str, name: str, target_pct: int) -> None:
    """Create one class via the dashboard's inline ``+ Nova classe`` form.

    Pré-condição: usuário logado (chame
    :func:`login_and_pick_profile` antes). Valida
    ``page.url.endswith("/")`` no início.

    The workflow waits for the form to be visible (Alpine's
    ``x-show`` toggles on the next tick after the click) before
    filling. After the save click, the dashboard calls
    ``window.location.reload()`` on 201 — we wait for the new
    class-summary-row to appear before returning so the next
    iteration of :func:`create_two_default_classes` doesn't
    race the re-init.

    data-testids:
      - empty-state-create-class (sidebar entry that opens the modal)
      - new-class-modal-overlay
      - new-class-modal-name-input
      - new-class-modal-pct-input
      - new-class-modal-submit
      - class-summary-row
    """
    if not page.url.endswith("/"):
        raise RuntimeError(
            "create_one_class requer login prévio. "
            "Chame login_and_pick_profile antes. "
            f"URL atual: {page.url}."
        )
    page.locator('[data-testid="empty-state-create-class"]').wait_for(state="visible", timeout=5000)
    page.locator('[data-testid="empty-state-create-class"]').click()
    modal = page.locator('[data-testid="new-class-modal-overlay"]')
    modal.wait_for(state="visible", timeout=5000)
    modal.locator('[data-testid="new-class-modal-name-input"]').fill(name)
    modal.locator('[data-testid="new-class-modal-pct-input"]').fill(str(target_pct))
    modal.locator('[data-testid="new-class-modal-submit"]').click()
    page.wait_for_load_state("networkidle", timeout=10000)
    page.locator(
        f'[data-testid="class-summary-row"]:has('
        f'[data-testid="class-section-name"]:text-is("{name}"))'
    ).wait_for(state="visible", timeout=10000)


def create_two_default_classes(
    page: Page,
    live_url: str,
    classes: list[ClassSpec] | None = None,
) -> None:
    """Create N classes by looping :func:`create_one_class` over the spec list.

    Pré-condição: usuário logado (chame
    :func:`login_and_pick_profile` antes). Valida
    ``page.url.endswith("/")`` no início.

    The legacy ``/classes`` snapshot editor was retired by S02/T07
    (the GET endpoint is now a 302 → ``/``), so the only path to
    create classes from the UI is the dashboard's inline
    ``+ Nova classe`` form. The workflow loops over
    :func:`create_one_class` so each row gets its own
    inline-add cycle.

    data-testids:
      - empty-state-create-class (sidebar entry)
      - new-class-modal-name-input
      - new-class-modal-pct-input
      - new-class-modal-submit
    """
    if classes is None:
        classes = DEFAULT_TWO_CLASSES
    if not page.url.endswith("/"):
        raise RuntimeError(
            "create_two_default_classes requer login prévio. "
            "Chame login_and_pick_profile antes. "
            f"URL atual: {page.url}."
        )
    for cls in classes:
        create_one_class(page, live_url, cls.name, cls.target_pct)


def add_one_asset(
    page: Page,
    live_url: str,
    class_name: str,
    ticker: str,
    target_pct: int,
) -> None:
    """Add one asset to an existing class via the dashboard modal.

    Pré-condição: usuário logado + classe existe (chame
    :func:`login_and_pick_profile` e
    :func:`create_one_class` / :func:`create_two_default_classes`
    antes). Valida ``page.url.endswith("/")`` no início.

    The dashboard exposes a single ``+ Ativo`` button at the top
    of the Distribuição section; clicking it opens the asset
    modal whose class ``<select>`` lets the operator pick the
    target class. The workflow: click global button → wait for
    modal → select class → fill name + pct → submit → wait for
    the new row to appear.

    data-testids:
      - dashboard-add-asset-open (sidebar entry)
      - add-asset-modal-overlay
      - dashboard-add-asset-modal-class
      - dashboard-add-asset-name
      - dashboard-add-asset-target-pct
      - dashboard-add-asset-submit
      - dashboard-asset-row
    """
    if not page.url.endswith("/"):
        raise RuntimeError(
            "add_one_asset requer login prévio. "
            "Chame login_and_pick_profile antes. "
            f"URL atual: {page.url}."
        )
    page.locator('[data-testid="dashboard-add-asset-open"]').wait_for(state="visible", timeout=5000)
    page.locator('[data-testid="dashboard-add-asset-open"]').click()
    modal = page.locator('[data-testid="add-asset-modal-overlay"]')
    modal.wait_for(state="visible", timeout=5000)
    modal.locator('[data-testid="dashboard-add-asset-modal-class"]').select_option(label=class_name)
    modal.locator('[data-testid="dashboard-add-asset-name"]').fill(ticker)
    modal.locator('[data-testid="dashboard-add-asset-target-pct"]').fill(str(target_pct))
    before = page.locator('[data-testid="dashboard-asset-row"]').count()
    modal.locator('[data-testid="dashboard-add-asset-submit"]').click()
    page.wait_for_load_state("networkidle", timeout=10000)
    page.locator('[data-testid="dashboard-asset-row"]').nth(before).wait_for(
        state="visible", timeout=10000
    )
