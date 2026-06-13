# Phase 01: audit — Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 14
**Analogs found:** 13 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/omaha/audit/__init__.py` | config | static | `src/omaha/routes/__init__.py` | exact |
| `src/omaha/audit/css_parser.py` | utility | transform | `src/omaha/csv_import.py` | exact |
| `src/omaha/audit/color_resolver.py` | utility | transform | `src/omaha/csv_import.py` | exact |
| `src/omaha/audit/inventory.py` | service | transform | `src/omaha/routes/pages.py` | role-match |
| `src/omaha/audit/report.py` | service | transform | `src/omaha/routes/pages.py` | role-match |
| `src/omaha/audit/cli.py` | controller | request-response | `scripts/backup.py` | role-match |
| `scripts/generate_contrast_audit.py` | script | file-I/O | `scripts/backup.py` | exact |
| `reports/.gitkeep` | config | static | none | no-analog |
| `tests/test_audit_css_parser.py` | test | transform | `tests/test_t02_csv_import.py` | exact |
| `tests/test_audit_color_resolver.py` | test | transform | `tests/test_t02_csv_import.py` | exact |
| `tests/test_audit_inventory.py` | test | transform | `tests/test_t03_pages_routes.py` | exact |
| `tests/test_audit_report.py` | test | transform | `tests/test_t03_pages_routes.py` | exact |
| `pyproject.toml` | config | static | `pyproject.toml` | exact |
| `src/omaha/templates/audit_report.html` | component | transform | `src/omaha/templates/base.html` | role-match |

## Pattern Assignments

### `src/omaha/audit/__init__.py` (config, static)

**Analog:** `src/omaha/routes/__init__.py`

**Package init pattern** (lines 1-12):

```python
"""HTTP route packages for the Omaha app.

Each submodule mounts a :class:`fastapi.APIRouter` and ``main.py``
includes them with their respective prefixes (most are mounted at the
root for now). The package itself is intentionally empty so future
slices can add new route modules without touching ``main.py``'s import
list.
"""

from __future__ import annotations

__all__: list[str] = []
```

**Copy:** same shape — docstring, `from __future__ import annotations`, and an empty `__all__`. Expose `audit` package without forcing imports.

---

### `src/omaha/audit/css_parser.py` (utility, transform)

**Analog:** `src/omaha/csv_import.py`

**Imports + future annotations** (lines 39-48):

```python
from __future__ import annotations

import csv
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Protocol
```

**Dataclass + Protocol pattern** (lines 98-130):

```python
class AssetLike(Protocol):
    """Anything with an id and a name is enough for the matcher."""

    id: int
    name: str


@dataclass(frozen=True)
class RawPosition:
    """A single broker-supplied position row, in the importer's neutral shape."""

    broker_ticker: str
    name: str
    qty: Decimal
    ...
```

**Pure function docstring contract** (lines 500-524):

```python
def parse_positions(text: str) -> list[RawPosition]:
    """Parse the text of a broker CSV into a list of :class:`RawPosition`.

    Detection order: skip blank lines, then skip leading banner
    rows, then detect a header row (>=2 label hits) and use it to
    align columns by label, then parse every remaining row
    against the resulting :class:`ColumnMap`.
    ...
    """
```

**Constants block** (lines 51-82):

```python
# Known header labels (lowercased, accent-stripped, no punctuation).
_KNOWN_TICKER_LABELS = ("codigo", "papel", "ticker", "ativo", "simbolo")
_KNOWN_NAME_LABELS = ("ativo", "nome", "descricao", "papel")
...
_HEADER_MIN_LABEL_HITS = 2
```

**Error handling pattern** (lines 570-573):

```python
        parsed = _parse_data_row(row, row_index, col_map)
        if parsed is not None:
            out.append(parsed)
    return out
```

**Apply:** define dataclasses like `CssRule`, `CssToken`, `Stylesheet`; expose `parse_stylesheet(path)` returning parsed rules; silently skip malformed rules; keep module pure (no DB/FastAPI).

---

### `src/omaha/audit/color_resolver.py` (utility, transform)

**Analog:** `src/omaha/csv_import.py` (pure function library) + `src/omaha/main.py` (filter registration style)

**Dataclass output pattern** (lines 153-165):

```python
@dataclass
class MatchResult:
    """Output of :func:`match_positions`.

    ``auto_matched`` is a list of ``(RawPosition, asset_id)`` pairs
    — the broker's position and the existing Asset id the parser
    confidently mapped it to. ``unmatched`` is a list of
    :class:`RawPosition` rows that did not match any existing asset
    and therefore need a user decision in the review screen.
    """

    auto_matched: list[tuple[RawPosition, int]]
    unmatched: list[RawPosition]
```

**Function signature style** (lines 577-580):

```python
def match_positions(
    raw: Iterable[RawPosition],
    existing_assets: Iterable[AssetLike],
) -> MatchResult:
```

**Apply:** define `ContrastResult` dataclass; expose `contrast_ratio(fg: str, bg: str) -> float` and `aa_status(ratio: float, is_large: bool) -> tuple[float, str]`; wrap `coloraide.Color(...).contrast(..., method="wcag21")`; composite transparent colors over ancestor background.

---

### `src/omaha/audit/inventory.py` (service, transform)

**Analog:** `src/omaha/routes/pages.py` (template rendering + data assembly)

**Template rendering pattern** (lines 37-39, 67-77):

```python
def _templates(request: Request):
    """Return the application-wide Jinja2 templates instance."""
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse, response_model=None)
def index(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    ...
    return _templates(request).TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "profile": profile,
            "asset_classes": asset_classes,
            ...
        },
    )
```

**Apply:** build a `render_page(name: str, context: dict) -> str` helper using `jinja2.Environment(loader=FileSystemLoader(...))`; render each template with a minimal dummy context; feed rendered HTML to BeautifulSoup4; select interactive elements with `soup.select("button, a[href], input, select, textarea, [tabindex]")`.

---

### `src/omaha/audit/report.py` (service, transform)

**Analog:** `src/omaha/routes/pages.py` (template response) + `src/omaha/main.py` (Jinja2 setup)

**Jinja2Templates setup + filter registration** (lines 137-146):

```python
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    # Register the BRL currency filter on the shared templates
    # instance — the dashboard (S05) is the only consumer for now,
    # but a future reports slice will reuse the same formatter.
    templates.env.filters["brl"] = _brl
    app.state.templates = templates
```

**Apply:** create a dedicated Jinja2 `Environment` (or inline `Template`) for the audit report; pass inventory data and computed contrasts; render a self-contained HTML file with inline `<style>` (no external CDN). Register a small `contrast_ratio` filter if needed.

---

### `src/omaha/audit/cli.py` (controller, request-response)

**Analog:** `scripts/backup.py`

**argparse + main() pattern** (lines 34-114):

```python
def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Hot SQLite backup via the stdlib Connection.backup() API. "
            ...
        )
    )
    parser.add_argument(
        "--source",
        default="./data/portfolio.db",
        help=(
            "Path to the source SQLite file. Resolved relative to the "
            "current working directory. Default: %(default)s"
        ),
    )
    parser.add_argument(
        "dest",
        help=(
            "Path to the destination SQLite file. The file is created if "
            "it does not exist; existing files are overwritten."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    source = Path(args.source)
    dest = Path(args.dest)

    if not source.exists():
        print(f"backup FAIL: source not found: {source}", file=sys.stderr)
        return 1

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        ...
    except sqlite3.Error as exc:
        print(f"backup FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"backup OK: {source} -> {dest} ({status})")
    return 0
```

**Entry point guard** (lines 117-118):

```python
if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
```

**Apply:** add `--css`, `--templates-dir`, `--output` arguments with defaults resolved under repo root; call `css_parser`, `inventory`, `color_resolver`, `report`; print success/failure; return non-zero on error.

---

### `scripts/generate_contrast_audit.py` (script, file-I/O)

**Analog:** `scripts/backup.py` (CLI + path handling) + `scripts/dev_reset.py` (module-level invocation)

**Path handling / repo-root resolution** (lines 62-78):

```python
def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    source = Path(args.source)
    dest = Path(args.dest)

    if not source.exists():
        print(f"backup FAIL: source not found: {source}", file=sys.stderr)
        return 1

    dest.parent.mkdir(parents=True, exist_ok=True)
```

**Module-level invocation** (lines 160-161):

```python
if __name__ == "__main__":  # pragma: no cover
    reset_for_italo()
```

**Apply:** thin wrapper that imports `omaha.audit.cli.main` and forwards `sys.argv[1:]`; resolve output path under `reports/`; ensure directory exists; exit with returned status.

---

### `reports/.gitkeep` (config, static)

**No analog.** Empty directory marker. Use standard `.gitkeep` convention.

---

### `tests/test_audit_css_parser.py` (test, transform)

**Analog:** `tests/test_t02_csv_import.py`

**Test imports + fixture path** (lines 28-46):

```python
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from omaha.csv_import import (
    MatchResult,
    _parse_brazilian_number,
    match_positions,
    normalize_name,
    parse_positions,
    suggest_class_id,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_broker.csv"
FIXTURE_TEXT = FIXTURE_PATH.read_text(encoding="utf-8")
```

**Pure-function test pattern** (lines 59-70):

```python
def test_header_detection_portuguese() -> None:
    """Portuguese headers are detected and consumed."""
    text = (
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\n"
        'PETR4,PETR4,100,"28,50","35,10"\n'
        ...
    )
    positions = parse_positions(text)
    assert len(positions) == 2
    assert positions[0].broker_ticker == "PETR4"
```

**Parametrize pattern** (lines 225-239):

```python
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("PETR4", "petr4"),
        ("  PETR4  ", "petr4"),
        ...
    ],
)
def test_normalize_name_canonicalization(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected
```

**Apply:** import `omaha.audit.css_parser`; define `FIXTURE_CSS = Path(...)` for a small CSS snippet; test `parse_rules`, `color_tokens`, custom-property resolution; assert selector/value tuples match expectations.

---

### `tests/test_audit_color_resolver.py` (test, transform)

**Analog:** `tests/test_t02_csv_import.py`

**Parametrized pure-function test** (lines 225-239, 344-389):

```python
@pytest.mark.parametrize(
    "category,expected_id",
    [
        ("Renda Fixa 60%", 1),
        ("renda fixa 60%", 1),
        ...
    ],
)
def test_suggest_class_id_mapping(
    demo_classes: list[SimpleNamespace], category: str | None, expected_id: int | None
) -> None:
    assert suggest_class_id(category, demo_classes) == expected_id
```

**Apply:** parametrize `(fg, bg, expected_ratio, expected_status)`; test `contrast_ratio()` with hex, `oklch()`, `color-mix()`; test `aa_status()` threshold at 4.5 and 3.0; test failure flagging.

---

### `tests/test_audit_inventory.py` (test, transform)

**Analog:** `tests/test_t03_pages_routes.py`

**TestClient import + fixture usage** (lines 14-20, 259-298):

```python
from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from omaha.models import Asset, AssetClass, Position, Profile
from omaha.routes.pages import portfolio_aggregates


def test_dashboard_renders_portfolio_totals(client: TestClient) -> None:
    profile_id = _login_and_select(client, profile_name="Italo")
    ...
    r = client.get("/")
    assert r.status_code == 200, r.text

    body = r.text
    assert "60.00%" in body, body
    assert "TESOURO" in body, body
```

**Apply:** no DB needed for the audit. Test `render_page(name, context)` returns a string; test `find_interactive(html)` returns expected counts; test state rows are generated for default/hover/active/focus/disabled where CSS defines them.

---

### `tests/test_audit_report.py` (test, transform)

**Analog:** `tests/test_t03_pages_routes.py` (rendered-output assertions)

**Rendered HTML assertions** (lines 300-375):

```python
def test_dashboard_renders_distribution_layout(client: TestClient) -> None:
    ...
    r = client.get("/")
    assert r.status_code == 200, r.text
    body = r.text

    assert 'data-testid="portfolio-header"' in body, body
    assert 'data-testid="portfolio-invested"' in body, body
    assert "R$" in body, body
```

**Apply:** generate the report HTML from test data; assert it contains summary cards, TOC anchors, per-page inventory sections, token inventory table, failure log, and Portuguese strings ("Inventário de contraste", "Passa", "Falha").

---

### `pyproject.toml` (config, static)

**Analog:** `pyproject.toml`

**Dependency group pattern** (lines 24-31):

```toml
[dependency-groups]
dev = [
    "pytest>=8.3",
    "httpx>=0.27",
    "ruff>=0.6",
    "prek>=0.2",
    "playwright>=1.60.0",
]
```

**Project script entry point** (lines 33-34):

```toml
[project.scripts]
omaha = "omaha.main:app"
```

**pytest config** (lines 54-56):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

**Apply:** append `"coloraide>=8.8.1"`, `"tinycss2>=1.5.1"`, `"beautifulsoup4>=4.15.0"`, `"lxml>=6.1.1"` to `[dependency-groups] dev`. Optionally add an audit console script if the UI-SPEC "Exportar inventário" action becomes a CLI command (start without it; research recommends CLI-only).

---

### `src/omaha/templates/audit_report.html` (component, transform)

**Analog:** `src/omaha/templates/base.html` + `src/omaha/templates/dashboard.html`

**Base template structure** (lines 1-18):

```html
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Omaha{% endblock %}</title>
  <link rel="stylesheet" href="/static/app.css">
  ...
</head>
<body>
  <header class="app-header">
    ...
  </header>

  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

**Template extension + blocks** (`src/omaha/templates/dashboard.html`, lines 1-2):

```html
{% extends "base.html" %}
{% block content %}
```

**Apply:** if the report uses a separate template, extend `base.html` or create a standalone HTML file with inline `<style>` (per UI-SPEC: self-contained, no CDN). Use Portuguese copy and data-testid markers for report sections. If report.py inlines the template, replicate the inline style block from RESEARCH.md pattern 4.

---

## Shared Patterns

### Pure function / no-DB module shape
**Source:** `src/omaha/csv_import.py`
**Apply to:** `css_parser.py`, `color_resolver.py`, `inventory.py` (core logic)
- Start with `from __future__ import annotations`.
- Use `dataclasses` for value objects.
- Keep functions deterministic and side-effect-free until `cli.py` / `report.py`.
- Document contracts in docstrings.

### Path resolution relative to repo root
**Source:** `src/omaha/main.py` (lines 51-53)
**Apply to:** `cli.py`, `scripts/generate_contrast_audit.py`, `report.py`

```python
_PACKAGE_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _PACKAGE_DIR / "templates"
_STATIC_DIR = _PACKAGE_DIR / "static"
```

### Jinja2 template rendering
**Source:** `src/omaha/routes/pages.py` (lines 37-39, 67-77)
**Apply to:** `inventory.py`, `report.py`

```python
def _templates(request: Request):
    return request.app.state.templates

return _templates(request).TemplateResponse(
    request,
    "dashboard.html",
    {"user": user, "profile": profile, ...},
)
```

For the audit, use `jinja2.Environment(loader=FileSystemLoader(templates_dir))` and `env.get_template(name).render(**context)` because there is no `Request` object.

### Static file serving convention
**Source:** `src/omaha/main.py` (lines 155-159)
**Apply to:** n/a for report generation, but relevant if a route is added later

```python
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
```

### Test fixture path
**Source:** `tests/test_t02_csv_import.py` (lines 45-46)
**Apply to:** all `tests/test_audit_*.py`

```python
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_broker.csv"
FIXTURE_TEXT = FIXTURE_PATH.read_text(encoding="utf-8")
```

### Test cleanup fixture
**Source:** `tests/test_t03_pages_routes.py` (lines 27-45)
**Apply to:** audit tests that touch the DB (if any)

```python
@pytest.fixture(autouse=True)
def _clean_dashboard_tables() -> None:
    from omaha.db import SessionLocal
    db = SessionLocal()
    try:
        db.query(Position).delete()
        ...
        db.commit()
    finally:
        db.close()
    yield
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `reports/.gitkeep` | config | static | Standard Git directory marker; no code analog needed |

## Metadata

**Analog search scope:** `src/omaha/`, `tests/`, `scripts/`, `pyproject.toml`
**Files scanned:** 50+
**Pattern extraction date:** 2026-06-13
