# Phase 02: Palette — Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 3
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `DESIGN.md` | documentation | static-reference | `DESIGN.md` (self) | self-analog |
| `src/omaha/static/app.css` | config | static-token-definition | `src/omaha/static/app.css` (self, `:root` block) | self-analog |
| `tests/test_phase02_tokens.py` | test | computation-verification | `tests/test_audit_css_parser.py` | exact |

## Pattern Assignments

### `DESIGN.md` (documentation, static-reference)

**Analog:** `DESIGN.md` (self — existing structure is the pattern)

**Token table pattern** (lines 30–42):
```markdown
| Token             | OKLCH                     | Hex (current→target) | Role                                           |
|-------------------|---------------------------|----------------------|------------------------------------------------|
| `--bg`            | `oklch(0.975 0.003 60)`   | `#fafaf7` → off-white | Body. True off-white, chroma ≈ 0. NOT cream.   |
| `--surface`       | `oklch(1.0 0 0)`          | `#fff`               | Cards, modals, popovers. Slightly lifted.      |
```

**Phase 2 update:** Add `Pair` and `Contrast` and `Status` columns per RESEARCH.md §DESIGN.md Update Strategy (lines 412–427). New structure:
```markdown
| Token | OKLCH | Hex (approx) | Role | Pair | Contrast | Status |
|-------|-------|-------------|------|------|----------|--------|
| `--bg` | `oklch(0.975 0.003 60)` | `#fafaf7` | Body surface | vs `--ink` | 16.85 | Passa |
```

**Class swatches table pattern** (lines 58–65):
```markdown
| Slot  | OKLCH                    | Role                                    |
|-------|--------------------------|-----------------------------------------|
| 1     | `oklch(0.50 0.14 250)`   | Deep blue (replaces `#0a66c2` brand-ish)|
| 4     | `oklch(0.62 0.15 50)`    | Burnt orange (not tangerine)            |
```
**Phase 2 update:** Correct slot 4 to `oklch(0.53 0.13 50)`. Add Contrast column showing ratio vs `--bg` per RESEARCH.md §DESIGN.md Class Swatch Target Correction (lines 293–295).

**Component inventory table pattern** (lines 175–192):
```markdown
| Component           | Where                  | Notes                                  |
|---------------------|------------------------|----------------------------------------|
| App header          | `base.html`            | Logo, nav, profile, signout. Flat.     |
| Primary button      | various                | —                                      |
| Class section       | `dashboard.html`       | Swatch + name + compare bar + asset list. |
| Error message       | various                | Inline, top of form. No toast.         |
```
**Phase 2 update:** Add `Color Tokens` column per D-04. New structure per RESEARCH.md §Component Inventory Annotations (lines 433–446):
```markdown
| Component | Where | Color Tokens | Notes |
|-----------|-------|-------------|-------|
| App header | base.html | `--surface`, `--border`, `--fg`, `--muted`, `--accent` | Flat, border-bottom |
| Primary button | various | `--accent`, `--accent-ink` | hover: brightness(1.1) |
| Delete confirm | dashboard | `--negative`, `--negative-ink` | Confirm dialog |
```

**Color strategy section pattern** (lines 14–23):
```markdown
**Restrained, with one committed accent.**

The body surface is a true off-white, not a cream. …
The accent is one color, used at ≤10% of the surface, committed.
```
**Phase 2 update:** Add token verification provenance — note that all tokens were verified against WCAG AA via scripted `contrast_ratio()` + `aa_status()` checks.

**Accent rationale preservation** (lines 44–51):
Keep as-is per CONTEXT.md §Specific Ideas: "DESIGN.md accent rationale (hue 150 fern green) should be preserved — it's a deliberate design choice, not a defect."

**Migration path update** (lines 212–227):
Step 1 currently reads: "Update `:root` tokens in `app.css` to the OKLCH values above." Update to reference the corrected values (class-4 at 0.53, class-6 at 0.52). Steps 2–6 unchanged.

---

### `src/omaha/static/app.css` (config, static-token-definition)

**Analog:** `src/omaha/static/app.css` (self — `:root` block lines 3–58)

**Comment header for surface tokens** (lines 6–8):
```css
  /* Surface tokens — OKLCH, target values per DESIGN.md.
     The body uses --bg (off-white); cards and modals lift to --surface;
     form wells, input strips, and table headers sink to --surface-sunk. */
```

**Token declaration pattern** (lines 9–11):
```css
  --bg: oklch(0.975 0.003 60);          /* off-white body. Not cream. */
  --surface: oklch(1.0 0 0);            /* cards, modals, popovers. */
  --surface-sunk: oklch(0.96 0.003 60); /* form wells, input strips. */
```
**Phase 2 change:** Values unchanged for surface tokens. Comments updated to note WCAG AA status.

**Accent token pattern** (lines 21–23):
```css
  /* Accent — single committed color (deep fern, hue 150). */
  --accent: oklch(0.42 0.09 150);
  --accent-ink: oklch(0.98 0.005 150);
```
**Phase 2 change:** Add contrast note in comment: `/* Contrast: --accent-ink on --accent = 7.67:1 Passa */`

**Status colors pattern** (lines 25–27):
```css
  /* Status colors — gain/positive and loss/negative. */
  --positive: oklch(0.52 0.13 145);
  --negative: oklch(0.50 0.18 25);
```
**Phase 2 change:** Add `--negative-ink` and `--positive-ink` tokens after status colors per RESEARCH.md §Tokens to Add (lines 299–302):
```css
  /* Status ink tokens — text on status backgrounds.
     --negative-ink: text on --negative fill (6.59:1, Passa).
     --positive-ink: text on --positive fill (future). */
  --negative-ink: #ffffff;
  --positive-ink: #ffffff;
```

**Error token hex→OKLCH conversion** (lines 36–38):
```css
  /* App-specific error feedback — not in the design token table. */
  --error-bg: #fde8e8;
  --error-fg: #8a1f1f;
```
**Phase 2 change:** Convert to OKLCH per RESEARCH.md §Tokens to Convert (lines 306–309):
```css
  /* Error feedback — converted to OKLCH for consistency.
     Contrast: --error-fg on --error-bg = 7.79:1 Passa. */
  --error-bg: oklch(0.94 0.02 15);
  --error-fg: oklch(0.38 0.12 25);
```

**Legacy alias pattern** (lines 29–34):
```css
  /* Legacy aliases — point to the new OKLCH tokens so existing rules
     (still using var(--fg), var(--muted)) resolve to the same values
     without a sweeping rename. … */
  --fg: var(--ink);
  --muted: var(--ink-muted);
```
**Phase 2 change:** Unchanged. Keep indefinitely per RESEARCH.md §Pitfall 4 (lines 480–488).

**Class color tokens pattern** (lines 40–52):
```css
  /* Class color tokens (S05 T03) — kept as hex per DESIGN.md
     ("migration source until the swatch palette is committed"). … */
  --class-1: #0a66c2; /* blue   */
  --class-2: #2e7d32; /* green  */
  --class-3: #c62828; /* red    */
  --class-4: #ef6c00; /* orange */
  --class-5: #6a1b9a; /* purple */
  --class-6: #00838f; /* teal   */
```
**Phase 2 change:** Replace `--class-4` and `--class-6` with corrected OKLCH values. Add inline ratio comments per RESEARCH.md §Corrected Token Values (lines 286–289) and §Corrected :root Block (lines 542–546):
```css
  --class-1: #0a66c2;                        /* blue   — 5.29, Passa */
  --class-2: #2e7d32;                        /* green  — 4.77, Passa */
  --class-3: #c62828;                        /* red    — 5.23, Passa */
  --class-4: oklch(0.53 0.13 50);            /* orange — 5.16, Passa (was #ef6c00 at 2.87 Falha) */
  --class-5: #6a1b9a;                        /* purple — 8.73, Passa */
  --class-6: oklch(0.52 0.10 200);           /* teal   — 4.89, Passa (was #00838f at 4.21 Falha) */
```

**Delete-confirm button fix** — two locations in app.css:

Location 1 (line 1085):
```css
.class-delete-confirm-yes {
  …
  background: var(--negative);
  color: #fff;                              /* ← hardcoded, replace */
  border: 1px solid var(--negative);
  …
}
```
Location 2 (line 1186):
```css
.dashboard-asset-delete-confirm-yes {
  …
  background: var(--negative);
  color: #fff;                              /* ← hardcoded, replace */
  border: 1px solid var(--negative);
  …
}
```
**Phase 2 change:** Replace `color: #fff;` with `color: var(--negative-ink);` at both locations. This formalizes the fg/bg pair per PALT-01.

---

### `tests/test_phase02_tokens.py` (test, computation-verification)

**Analog:** `tests/test_audit_css_parser.py` (same test framework, same functions under test)

**Module docstring and coverage map** (lines 1–20):
```python
"""Tests for Phase 1 — AUDT-02 CSS parser and token inventory.

Unit tests for :mod:`omaha.audit.css_parser`. No DB, no FastAPI, no
session — the parser is a pure function library.

Coverage map (this file):
* Package import              — ``test_audit_css_parser_importable``
* Dataclass construction      — ``test_token_inventory_row_fields``
* …
"""
```

**Imports pattern** (lines 22–39):
```python
from __future__ import annotations

import importlib
import textwrap
from pathlib import Path

import pytest

from omaha.audit.css_parser import (
    CssRule,
    CssToken,
    Stylesheet,
    TokenInventoryRow,
    color_token_inventory,
    parse_stylesheet,
    resolve_var,
)
```
**Phase 2 copy:** Import `color_token_inventory`, `contrast_ratio`, `aa_status`, and `parse_stylesheet` from `omaha.audit.css_parser` and `omaha.audit.color_resolver`.

**Fixture / constant pattern** (lines 46–66):
```python
FIXTURE_CSS = textwrap.dedent("""\
    :root {
      --bg: oklch(0.975 0.003 60);
      …
    }
""")

APP_CSS_PATH = Path(__file__).resolve().parents[1] / "src" / "omaha" / "static" / "app.css"
```
**Phase 2 copy:** Define `APP_CSS_PATH` constant for the real `app.css` path. Use `color_token_inventory(parse_stylesheet(APP_CSS_PATH))` in tests.

**Test function pattern** (lines 84–100):
```python
def test_audit_css_parser_importable() -> None:
    """The CSS parser module is importable."""
    assert css_parser is not None

def test_token_inventory_row_fields() -> None:
    """TokenInventoryRow exposes the fields described in the artifact spec."""
    row = TokenInventoryRow(
        token="--ink",
        computed_value="oklch(0.20 0.01 60)",
        adjacent_background="#ffffff",
        ratio=4.5,
        status="Passa",
    )
    assert row.token == "--ink"
    assert row.ratio == 4.5
    assert row.status == "Passa"
```
**Phase 2 copy:** Same pattern — `def test_X() -> None:` with docstring. Assert on computed values.

**Real-app integration test pattern** (lines 283–297):
```python
def test_inventory_from_real_app_css() -> None:
    """color_token_inventory runs against the real app.css without errors."""
    if not APP_CSS_PATH.exists():
        pytest.skip("app.css not found")
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    assert len(rows) >= 15  # :root has ~20 custom props, most are colors

    by_name = {r.token: r for r in rows}
    assert "--bg" in by_name
    assert "--ink" in by_name
    assert "--accent" in by_name
```
**Phase 2 copy:** PALT-01 test — verify all tokens return `Passa` status after correction:
```python
def test_all_tokens_pass_aa() -> None:
    """After Phase 2 corrections, color_token_inventory() returns zero Falha rows."""
    if not APP_CSS_PATH.exists():
        pytest.skip("app.css not found")
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    failures = [r for r in rows if r.status == 'Falha']
    assert len(failures) == 0, f"Tokens failing: {[r.token for r in failures]}"
```

**Real-pair test pattern** — cross-reference from `test_audit_color_resolver.py` (lines 71–87):
```python
def test_contrast_ratio_oklch_body() -> None:
    """The app.css --ink against --bg pair returns >= 4.5 (must pass AA)."""
    ratio = contrast_ratio(
        "oklch(0.20 0.01 60)",  # --ink
        "oklch(0.975 0.003 60)",  # --bg
    )
    assert ratio >= 4.5, f"Expected >= 4.5 for --ink/--bg, got {ratio}"
```
**Phase 2 copy:** PALT-02 test — verify corrected real pairs:
```python
def test_corrected_pairs_pass_aa() -> None:
    """Corrected token pairs meet WCAG AA thresholds."""
    pairs = [
        ("class-4 on bg", "oklch(0.53 0.13 50)", "oklch(0.975 0.003 60)", 4.5),
        ("class-6 on bg", "oklch(0.52 0.10 200)", "oklch(0.975 0.003 60)", 4.5),
        ("negative-ink on negative", "#ffffff", "oklch(0.50 0.18 25)", 4.5),
        ("error-fg on error-bg", "oklch(0.38 0.12 25)", "oklch(0.94 0.02 15)", 4.5),
    ]
    for label, fg, bg, threshold in pairs:
        ratio = contrast_ratio(fg, bg)
        _, status = aa_status(ratio)
        assert ratio >= threshold, f"{label}: {ratio:.2f} < {threshold}"
        assert status == "Passa", f"{label}: expected Passa, got {status}"
```

**conftest.py integration** — existing `tests/conftest.py` (lines 1–3, generic):
No DB/fixture needed for Phase 2 tests (pure function library, no FastAPI). The `conftest.py` already exists but the new test file does not use its fixtures. No changes to `conftest.py` required.

---

## Shared Patterns

### CSS Token Comment Convention
**Source:** `src/omaha/static/app.css` lines 6–58
**Apply to:** All token declarations in app.css `:root` block
```css
  /* Category header — brief purpose.
     Detail line. Detail line. */
  --token-name: oklch(L C H);          /* short inline note */
```
Use block comments for category headers (surface, ink, border, accent, status, error, class, focus). Use inline `/* … */` for per-token notes including contrast ratio after Phase 2.

### Semantic Token Naming Convention
**Source:** `src/omaha/static/app.css` lines 3–58, RESEARCH.md §Pattern 1
**Apply to:** All new tokens (--negative-ink, --positive-ink)
- `--ink-*` = text color tokens (foreground)
- `--surface-*` = background fill tokens (surface)
- `--accent`, `--positive`, `--negative` = semantic color tokens (used as both fg and bg depending on context)
- `--*-ink` = text specifically meant for that fill (e.g., `--accent-ink` for text on `--accent` fill)
- `--class-N` = data palette tokens (1-indexed, 6 slots)
- Never: `--btn-*`, `--text-on-*`, `--color-*` (except `--color-focus`, legacy)

### OKLCH Value Format
**Source:** `src/omaha/static/app.css` lines 9–57
**Apply to:** All corrected and new token values
```css
oklch(L C H)
```
- `L`: lightness (0–1), 2 decimal places (e.g., 0.42, 0.975)
- `C`: chroma (0–0.4), 2 decimal places (e.g., 0.09, 0.18)
- `H`: hue (0–360), integer (e.g., 150, 60, 25)
- White/black use `oklch(1.0 0 0)` or hex `#ffffff` for `--negative-ink`/`--positive-ink` (these are intentionally pure white to maximize contrast on colored fills)

### Legacy Alias Pattern
**Source:** `src/omaha/static/app.css` lines 33–34
**Apply to:** Unchanged — keep `--fg` → `--ink` and `--muted` → `--ink-muted`
```css
--fg: var(--ink);
--muted: var(--ink-muted);
```
Keep indefinitely. Cost: 2 lines. Benefit: 19+ existing `var(--fg)` / `var(--muted)` call sites continue resolving without renames.

### Python Test File Structure
**Source:** `tests/test_audit_css_parser.py` (full file, 314 lines)
**Apply to:** `tests/test_phase02_tokens.py`
```python
"""Tests for Phase 2 — PALT token verification.

Unit tests for corrected token values. No DB, no FastAPI, no
session — the verification is a pure function library.

Coverage map (this file):
* PALT-01 all-tokens-pass  — ``test_all_tokens_pass_aa``
* PALT-02 real-pair check  — ``test_corrected_pairs_pass_aa``
* PALT-02 class-4 check    — ``test_class_4_corrected_value``
* PALT-02 class-6 check    — ``test_class_6_corrected_value``
* PALT-02 new tokens check — ``test_new_tokens_pass_aa``
"""

from __future__ import annotations

from pathlib import Path

from omaha.audit.css_parser import color_token_inventory, parse_stylesheet
from omaha.audit.color_resolver import aa_status, contrast_ratio

APP_CSS_PATH = Path(__file__).resolve().parents[1] / "src" / "omaha" / "static" / "app.css"
```

### DESIGN.md Table Format
**Source:** `DESIGN.md` lines 30–42, 58–65, 175–192
**Apply to:** Updated token table, class swatches table, component inventory
```markdown
| Column1 | Column2 | Column3 | Column4 |
|---------|---------|---------|---------|
| `code`  | value   | description | more |
```
- Backtick-wrap CSS token names: `` `--bg` ``
- Backtick-wrap OKLCH values: `` `oklch(0.975 0.003 60)` ``
- Backtick-wrap file names: `` `base.html` ``
- Contrast column: numeric ratio (e.g., `16.85`) + `Passa` or `Falha`

### Verification Script Pattern (inline, not a file)
**Source:** RESEARCH.md §Verification Script (lines 556–591)
**Apply to:** Pre-commit verification (manual, not a committed script file)
```bash
uv run python3 -c "
from omaha.audit.css_parser import parse_stylesheet, color_token_inventory
from omaha.audit.color_resolver import contrast_ratio, aa_status
from pathlib import Path

sheet = parse_stylesheet(Path('src/omaha/static/app.css'))
rows = color_token_inventory(sheet)
failures = [r for r in rows if r.status == 'Falha']
if failures:
    print('FAILURES:')
    for r in failures:
        print(f'  {r.token}: ratio={r.ratio} vs {r.adjacent_background}')
else:
    print('All tokens pass WCAG AA')
"
```
Run before committing any `app.css` `:root` block change.

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All 3 files have clear analogs |

---

## Metadata

**Analog search scope:** `src/omaha/static/`, `tests/`, `DESIGN.md`, `.planning/`
**Files scanned:** 48 test files via glob, 1 CSS file, 1 design doc, 22 planning docs
**Pattern extraction date:** 2026-06-13
**Key insight:** Phase 2 is a modification-only phase — no new source files beyond the test. All patterns come from the files being modified (self-analog) or the test suite established in Phase 1.
