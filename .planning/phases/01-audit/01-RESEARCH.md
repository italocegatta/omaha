# Phase 1: audit — Research

**Researched:** 2026-06-13
**Domain:** Python static analysis of CSS/Jinja2 for WCAG 2.1 contrast auditing
**Confidence:** MEDIUM

## Summary

Phase 1 must produce a self-contained, Portuguese-language static HTML report that inventories every interactive state and color token in the Omaha app and computes WCAG 2.1 AA contrast ratios before any palette fixes are applied. The source of truth is the existing `src/omaha/static/app.css` and the Jinja2 templates under `src/omaha/templates/`.

The recommended implementation is a build-time Python audit tool (not a runtime FastAPI feature) that:
1. Parses `app.css` with `tinycss2` to extract selectors, declarations, and custom properties.
2. Renders each page template with a minimal dummy context using Jinja2.
3. Uses `BeautifulSoup4` to discover interactive elements (`button`, `a`, `input`, `select`, `textarea`, `[tabindex]`).
4. Resolves effective foreground/background pairs for `default`, `hover`, `active`, `focus`, and `disabled` states, including `var()`, `color-mix()`, and `filter()` brightness transforms.
5. Computes contrast ratios with `coloraide` and flags failures (body `< 4.5:1`, UI/large `< 3:1`).
6. Renders a static HTML report titled **"Inventário de contraste — Omaha"** with summary cards, TOC, per-page inventory, CSS token inventory, and failure log.

**Primary recommendation:** implement `src/omaha/audit/` plus a CLI entry point (`scripts/generate_contrast_audit.py` or `uv run python -m omaha.audit`) and add focused pytest coverage before implementation work begins.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDT-01 | Auditor can generate a per-page inventory of interactive elements and their default/hover/active/focus/disabled color pairs | Render templates with Jinja2, parse with BeautifulSoup4, cross-reference CSS rules parsed by tinycss2, compute pairs with coloraide |
| AUDT-02 | Auditor can list every CSS custom property that sets text or background color and its computed contrast against the adjacent background | Parse `:root` and component-scoped custom properties from app.css; resolve adjacent background (usually `--bg` or `--surface`); compute contrast with coloraide |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Interactive element inventory | Build-time script | Rendered-HTML parser (BeautifulSoup4) | Templates + CSS are the authoritative source; no runtime state needed |
| CSS custom-property inventory | Build-time script | CSS parser (tinycss2) | `app.css` is the single source of token definitions |
| Color resolution and contrast computation | Build-time script | Color library (coloraide) | Pure math on controlled project files |
| Static HTML report generation | Build-time script | Jinja2 templating | Self-contained file, no external CDN or server |
| Test validation | pytest | uv-run environment | Existing project test infrastructure |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `coloraide` | 8.8.1 [CITED: pypi.org] | Parse `oklch()`, `color-mix()`, hex, convert to sRGB, and compute WCAG 2.1 contrast ratios | Pure Python, modern CSS color spaces, built-in `contrast(method='wcag21')` [CITED: Context7 /facelessuser/coloraide] |
| `tinycss2` | 1.5.1 [CITED: pypi.org] | Parse `app.css` into selectors, declarations, and at-rules | Low-level CSS Syntax Level 3 parser, no heavy dependencies [CITED: Context7 /kozea/tinycss2] |
| `beautifulsoup4` | 4.15.0 [CITED: pypi.org] | Parse rendered templates and select interactive elements | De facto Python HTML parser; supports `html.parser` and `lxml` backends [CITED: Context7 /wention/beautifulsoup4] |
| `lxml` | 6.1.1 [CITED: pypi.org] | Optional faster parser backend for BeautifulSoup4 | Speed advantage if templates grow; falls back to `html.parser` if unavailable |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `cssselect` | 1.4.0 [CITED: pypi.org] | Translate CSS3 selectors to XPath | Only if robust selector matching beyond class/tag is needed |
| `Jinja2` | already in project | Render templates with dummy contexts | Already required by FastAPI; no new dependency |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `coloraide` | `colour-science` | More complete color science but heavier API; `coloraide` is simpler for CSS strings |
| `tinycss2` | `cssutils` | `cssutils` is higher-level but older and larger; `tinycss2` is lighter and actively maintained |
| `beautifulsoup4` | `lxml.html` | `lxml` is faster but less forgiving; BS4 plus `html.parser` is sufficient for controlled template output |
| Manual OKLCH math | `colorsys` | `colorsys` does not support OKLCH; hand-rolling the conversion is error-prone |

**Installation:**

```bash
uv add --dev coloraide tinycss2 beautifulsoup4 lxml
```

**Version verification:** Verified against PyPI JSON API on 2026-06-13.

```bash
# Manual verification performed:
for pkg in coloraide tinycss2 beautifulsoup4 lxml; do
  curl -s "https://pypi.org/pypi/$pkg/json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['info']['name'], d['info']['version'])"
done
```

## Package Legitimacy Audit

> Required: every phase that installs external packages must run the legitimacy gate. All candidate packages were checked with `gsd-tools query package-legitimacy check --ecosystem pypi <pkg>`.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `beautifulsoup4` | PyPI | ~8 yrs | unknown to seam | crummy.com/BeautifulSoup | [SUS] | Flagged — planner must add `checkpoint:human-verify` before install |
| `tinycss2` | PyPI | ~10 yrs | unknown to seam | courtbouillon.org/tinycss2 | [SUS] | Flagged — planner must add `checkpoint:human-verify` before install |
| `coloraide` | PyPI | ~4 yrs | unknown to seam | github.com/facelessuser/coloraide | [SUS] | Flagged — planner must add `checkpoint:human-verify` before install |
| `lxml` | PyPI | ~17 yrs | unknown to seam | lxml.de | [SUS] | Flagged — planner must add `checkpoint:human-verify` before install |
| `cssselect` | PyPI | ~12 yrs | unknown to seam | github.com/scrapy/cssselect | [SUS] | Flagged — planner must add `checkpoint:human-verify` if used |

**Packages removed due to [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** `beautifulsoup4`, `tinycss2`, `coloraide`, `lxml`, `cssselect`

> **Note:** The [SUS] verdicts are driven by missing weekly-download metadata in the legitimacy seam, not by malicious signals. All packages are referenced by official documentation/Context7 and have long publication histories. The planner should still gate each install behind a `checkpoint:human-verify` task per protocol.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐
│  src/omaha/     │     │  src/omaha/     │
│  static/app.css │     │  templates/*.html│
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  tinycss2       │     │  Jinja2         │
│  parse_stylesheet│     │  render(dummy_ctx)│
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    CSS rules + vars   │    rendered HTML
         │                       │
         └──────────┬────────────┘
                    ▼
         ┌─────────────────────┐
         │  BeautifulSoup4     │
         │  select interactive │
         │  elements           │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Selector matcher   │
         │  (tag / class /     │
         │  pseudo-state)      │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Color resolver     │
         │  var() / color-mix()│
         │  / filter()         │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  coloraide          │
         │  convert + contrast │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Jinja2 report      │
         │  (inline CSS, PT-BR)│
         └──────────┬──────────┘
                    │
                    ▼
            contrast_audit.html
```

### Recommended Project Structure

```
src/omaha/
├── audit/
│   ├── __init__.py
│   ├── css_parser.py        # parse app.css, resolve var(), list tokens
│   ├── color_resolver.py    # coloraide wrapper: parse, mix, brighten, contrast
│   ├── inventory.py         # render templates, find interactive elements
│   ├── report.py            # render static HTML report
│   └── cli.py               # uv run python -m omaha.audit entry point
scripts/
└── generate_contrast_audit.py   # thin wrapper around omaha.audit.cli
reports/.gitkeep
tests/
├── test_audit_css_parser.py
├── test_audit_color_resolver.py
├── test_audit_inventory.py
└── test_audit_report.py
```

### Pattern 1: Parsing CSS with tinycss2

**What:** Read the stylesheet, iterate qualified rules, and extract selector + declaration pairs.

**When to use:** Building the CSS token inventory and discovering interactive-element rules.

**Example:**

```python
# Source: Context7 /kozea/tinycss2
import tinycss2

def parse_rules(css_text: str):
    rules = tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True)
    for rule in rules:
        if rule.type == "qualified-rule":
            selector = tinycss2.serialize(rule.prelude).strip()
            declarations = tinycss2.parse_blocks_contents(rule.content, skip_whitespace=True)
            for decl in declarations:
                if decl.type == "declaration":
                    value = tinycss2.serialize(decl.value).strip()
                    yield selector, decl.name, value
```

### Pattern 2: Discovering Interactive Elements

**What:** Render each template with a minimal context and use BeautifulSoup4 to select focusable/interactive tags.

**When to use:** AUDT-01 per-page inventory.

**Example:**

```python
# Source: Context7 /wention/beautifulsoup4
from bs4 import BeautifulSoup

INTERACTIVE_SELECTOR = "button, a[href], input, select, textarea, [tabindex]"

def find_interactive(html: str):
    soup = BeautifulSoup(html, "html.parser")
    return soup.select(INTERACTIVE_SELECTOR)
```

### Pattern 3: Computing Contrast with coloraide

**What:** Parse foreground and background strings (including `oklch()` and `color-mix()`), then call `contrast(method='wcag21')`.

**When to use:** Every color pair in the inventory.

**Example:**

```python
# Source: Context7 /facelessuser/coloraide
from coloraide import Color

def contrast_ratio(fg: str, bg: str) -> float:
    return Color(fg).contrast(bg, method="wcag21")
```

### Pattern 4: Generating a Self-Contained Report

**What:** Render a Jinja2 template whose `<style>` block contains all report CSS inline; no external requests.

**When to use:** Final report output.

**Example:**

```html
<!-- Source: curated / project convention -->
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Inventário de contraste — Omaha</title>
  <style>
    :root { /* report tokens only */ }
    /* ... */
  </style>
</head>
<body>
  <h1>Inventário de contraste — Omaha</h1>
  <!-- report sections -->
</body>
</html>
```

### Anti-Patterns to Avoid

- **Parsing CSS with regex:** CSS has comments, escaping, and nesting; regex will miss edge cases. Use `tinycss2`.
- **Hand-rolling OKLCH-to-sRGB math:** the conversion path (OKLCH → Oklab → XYZ → linear sRGB → sRGB with transfer function) is easy to get wrong. Use `coloraide`.
- **Running the audit against the production database:** Phase 1 is static analysis only. Dummy contexts are sufficient.
- **Relying on a headless browser for contrast:** Adds heavy dependencies (Playwright) for a task that can be done in Python.
- **Including Alpine.js directives in the parsed HTML without rendering:** Unrendered `x-show`, `x-cloak`, and template loops produce false positives. Render templates first.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS color parsing | String splitting / regex | `coloraide` | Handles `oklch()`, `color-mix()`, gamut mapping, and alpha |
| CSS stylesheet parsing | Regex over lines | `tinycss2` | Correctly handles at-rules, comments, escaping, and tokenization |
| WCAG 2.1 contrast ratio | Custom luminance math | `coloraide.Color(...).contrast(..., method='wcag21')` | Uses the official relative-luminance formula and ratio |
| HTML parsing | Regex over template source | `BeautifulSoup4` | Handles malformed markup and rendered Jinja2 output |
| Report templating | String concatenation | `Jinja2` | Already a project dependency; separation of data and presentation |

**Key insight:** the audit must be trustworthy. A hand-rolled color parser or contrast formula is a single bug away from hiding real defects or producing false failures.

## Runtime State Inventory

> Omitted: Phase 1 is greenfield audit tooling. It does not rename, migrate, or refactor existing runtime state. The audit reads `app.css` and Jinja2 templates from disk and writes a static report; it does not read from or write to the production SQLite database, OS scheduler, secret stores, or installed packages.

## Common Pitfalls

### Pitfall 1: CSS Custom Property Resolution

**What goes wrong:** `var(--accent)` is not automatically resolved by `tinycss2`. The parser returns the token list as written.

**Why it happens:** `tinycss2` is intentionally low-level and does not maintain a cascade or variable registry.

**How to avoid:** Build a small resolver that tracks custom-property declarations in `:root` and any component-scoped rules, then substitutes `var()` tokens before color parsing.

**Warning signs:** Contrast errors that all resolve to the same missing variable name, or every computed foreground showing as `--ink` literally.

### Pitfall 2: Template Rendering Context

**What goes wrong:** Templates contain `{% if asset_classes %}` and Alpine loops. Parsing the raw template with BeautifulSoup4 sees `{{ profile.name }}` as text and may miss or misclassify elements.

**Why it happens:** Jinja2 syntax is not valid HTML until rendered.

**How to avoid:** Render each page template with a minimal dummy context (e.g., a single profile, one class, one asset) before handing HTML to BeautifulSoup4.

**Warning signs:** Selectors returning zero elements on pages known to have buttons.

### Pitfall 3: `color-mix()` with Transparency

**What goes wrong:** `color-mix(in srgb, var(--accent) 15%, transparent)` produces a transparent color. Computing contrast against a transparent background without considering the underlying surface gives meaningless ratios.

**Why it happens:** Alpha blending must be resolved against the effective background (usually `--bg` or `--surface`).

**How to avoid:** When a computed background has alpha < 1, composite it over the nearest opaque ancestor background before contrast computation.

**Warning signs:** Focus-ring box-shadow colors reported as failing against white even though they sit on `--surface`.

### Pitfall 4: `filter()` Brightness Transforms

**What goes wrong:** `.btn-primary:hover:not(:disabled) { filter: brightness(1.1); }` brightens the whole element. If the script only reads the `background` declaration, it misses the hover-state change.

**Why it happens:** `filter` is not a color declaration; it is an effect applied at compositing time.

**How to avoid:** Detect `filter: brightness(N)` on interactive selectors and apply an equivalent sRGB scalar to the resolved background color before computing hover/active contrast.

**Warning signs:** Primary button hover states all pass or fail identically to the default state.

### Pitfall 5: Pseudo-Class State Explosion

**What goes wrong:** Some selectors (e.g., `.btn:hover`) overlap with others (e.g., `.btn-primary:hover`). The inventory duplicates rows or applies the wrong background.

**Why it happens:** CSS specificity and source order matter; a naive selector list ignores the cascade.

**How to avoid:** Keep rules in source order, compute specificity per selector, and for each element collect matching rules in cascade order when resolving a given state.

## Code Examples

### Parse CSS and extract color tokens

```python
# Source: Context7 /kozea/tinycss2
import tinycss2

def color_tokens(css_text: str):
    rules = tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True)
    for rule in rules:
        if rule.type == "qualified-rule":
            selector = tinycss2.serialize(rule.prelude).strip()
            if selector != ":root":
                continue
            decls = tinycss2.parse_blocks_contents(rule.content, skip_whitespace=True)
            for decl in decls:
                if decl.type == "declaration" and decl.name in ("color", "background-color"):
                    value = tinycss2.serialize(decl.value).strip()
                    yield decl.name, value
```

### Compute contrast between two CSS color strings

```python
# Source: Context7 /facelessuser/coloraide
from coloraide import Color

def aa_status(fg: str, bg: str, is_large: bool = False) -> tuple[float, str]:
    ratio = Color(fg).contrast(bg, method="wcag21")
    threshold = 3.0 if is_large else 4.5
    return ratio, "Passa" if ratio >= threshold else "Falha"
```

### Render a template for static analysis

```python
# Source: curated / project convention (Jinja2)
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path("src/omaha/templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def render_page(name: str, context: dict) -> str:
    template = env.get_template(name)
    return template.render(**context)
```

### Generate inline swatches in the report

```html
<!-- Source: curated -->
<span class="swatch" style="background: {{ fg }};" aria-label="Cor do texto {{ fg }}"></span>
<span class="swatch" style="background: {{ bg }};" aria-label="Cor do fundo {{ bg }}"></span>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hex-only palette | OKLCH tokens | Current `app.css` | Better perceptual uniformity; requires a color library that understands modern CSS |
| Manual browser-devtools contrast check | Programmatic audit | Phase 1 | Repeatable, documents defects before fixes |
| Cream/sand body background | True off-white / neutral | DESIGN.md target | Avoids the most common AI-default visibility defect |

**Deprecated/outdated:**
- Manual OKLCH-to-sRGB math: superseded by `coloraide` for reliability.
- CSS parsing via regex: superseded by `tinycss2` for correctness.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `coloraide` 8.x correctly parses CSS `oklch()` and `color-mix()` and computes WCAG 2.1 contrast | Standard Stack | Contrast values incorrect; audit report unreliable |
| A2 | Jinja2 templates can be rendered with dummy contexts without a running app or database | Architecture | Per-page inventory cannot be generated automatically |
| A3 | `filter: brightness(N)` can be approximated by scaling sRGB channels of the resolved background color | Pitfalls | Hover/active contrast values slightly inaccurate |
| A4 | The adjacent background for CSS tokens is either `--bg` or `--surface` unless a component explicitly overrides it | AUDT-02 design | Token inventory may use wrong background for some tokens |
| A5 | `beautifulsoup4`, `tinycss2`, `coloraide`, and `lxml` are acceptable dependencies despite the seam's [SUS] verdicts | Package Legitimacy Audit | Install may be blocked pending human verification |

**If this table is empty:** not applicable — assumptions are listed above.

## Open Questions

1. **Should the audit be exposed as a FastAPI route?**
   - What we know: the UI-SPEC describes a self-contained HTML report and an "Exportar inventário" action.
   - What's unclear: whether the action must be clickable inside the running app or only generated by a developer script.
   - Recommendation: start as a CLI-only script in `src/omaha/audit/`. A route can be added later if needed.

2. **How should Alpine.js `x-show` / `x-cloak` elements be handled?**
   - What we know: many interactive elements (delete confirms, inline editors, import modal) are hidden by default.
   - What's unclear: whether they should still appear in the inventory because they have states.
   - Recommendation: inventory all interactive elements regardless of initial visibility, but mark hidden-by-default states so the auditor knows they require an interaction to become visible.

3. **What is the exact dummy context for templates?**
   - What we know: templates use `profile`, `asset_classes`, `class_aggregates`, `portfolio`, etc.
   - What's unclear: whether some templates fail to render without real database objects.
   - Recommendation: build a small `AuditContextFactory` with primitive dicts/lists; fallback to static HTML parsing if rendering fails.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All audit code | ✓ | 3.14.4 | — |
| `uv` | Package management | ✓ | 0.11.17 | — |
| `pytest` | Tests | ✓ (via `uv run`) | 9.0.3 | — |
| `Jinja2` | Template rendering | ✓ (project dependency) | 3.1+ | — |
| `tinycss2` | CSS parsing | ✗ | — | `uv add --dev tinycss2` |
| `coloraide` | Color/contrast | ✗ | — | `uv add --dev coloraide` |
| `beautifulsoup4` | HTML parsing | ✗ | — | `uv add --dev beautifulsoup4` |
| `lxml` | Faster parser backend | ✗ | — | `uv add --dev lxml` (optional) |

**Missing dependencies with no fallback:** none

**Missing dependencies with fallback:** `lxml` can be omitted; BeautifulSoup4 will use `html.parser`.

## Validation Architecture

> `workflow.nyquist_validation` is enabled (key absent in `.planning/config.json`, defaults to enabled).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/test_audit_*.py -q` |
| Full suite command | `uv run pytest tests -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDT-01 | Audit inventories interactive elements (`button`, `a`, `input`, `select`, `textarea`, `[tabindex]`) per rendered page | unit | `uv run pytest tests/test_audit_inventory.py::test_interactive_elements_per_page -x` | ❌ Wave 0 |
| AUDT-01 | Each inventoried element has default, hover, active, focus, and disabled rows where the CSS defines them | integration | `uv run pytest tests/test_audit_inventory.py::test_state_rows_generated -x` | ❌ Wave 0 |
| AUDT-01 | Report renders summary cards, TOC, per-page inventory, and failure log | integration | `uv run pytest tests/test_audit_report.py::test_report_sections_present -x` | ❌ Wave 0 |
| AUDT-02 | Audit lists every `:root` and component-scoped custom property that sets `color` or `background-color` | unit | `uv run pytest tests/test_audit_css_parser.py::test_color_tokens_inventoried -x` | ❌ Wave 0 |
| AUDT-02 | Each token is paired with its adjacent background and a computed contrast ratio | unit | `uv run pytest tests/test_audit_color_resolver.py::test_token_contrast_computed -x` | ❌ Wave 0 |
| AUDT-02 | Failures are flagged when contrast is below WCAG 2.1 AA thresholds | unit | `uv run pytest tests/test_audit_color_resolver.py::test_failure_flagging -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_audit_*.py -q`
- **Per wave merge:** `uv run pytest tests -q`
- **Phase gate:** full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_audit_css_parser.py` — covers AUDT-02 token extraction
- [ ] `tests/test_audit_color_resolver.py` — covers AUDT-02 contrast computation
- [ ] `tests/test_audit_inventory.py` — covers AUDT-01 interactive element discovery
- [ ] `tests/test_audit_report.py` — covers AUDT-01 report generation
- [ ] `pyproject.toml` — add `coloraide`, `tinycss2`, `beautifulsoup4`, `lxml` to `[dependency-groups] dev`
- [ ] `src/omaha/audit/` package created with module stubs for import tests

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

## Security Domain

> Required: `security_enforcement` is enabled (absent in config, defaults to enabled). However, Phase 1 is read-only static analysis with minimal threat surface.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Audit tool does not authenticate |
| V3 Session Management | no | No session state |
| V4 Access Control | no | Operates on project files only |
| V5 Input Validation | yes (minimal) | Validate file paths are inside repo; do not execute parsed CSS/JS |
| V6 Cryptography | no | No crypto operations |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal during file read | Tampering | Resolve paths under `Path(__file__).resolve().parents[...]`; reject parent-directory escapes |
| Untrusted CSS/JS execution | Tampering | Use parsers (`tinycss2`, `BeautifulSoup4`) that do not execute code |
| Report contains project structure disclosure | Information Disclosure | Keep report internal; do not expose via public URL unless explicitly required |

## Sources

### Primary (MEDIUM confidence)
- **Context7 `/facelessuser/coloraide`** — color parsing, `oklch()` conversion, `contrast(method='wcag21')`
- **Context7 `/kozea/tinycss2`** — `parse_stylesheet()`, declaration extraction, at-rule handling
- **Context7 `/wention/beautifulsoup4`** — `select()` for interactive elements, attribute extraction
- **Context7 `/websites/w3_wai_wcag22`** — WCAG 2.1 AA thresholds (4.5:1 normal, 3:1 large)

### Secondary (LOW confidence)
- **BeautifulSoup official docs** (`crummy.com`) — verified package source and HTML parser options

### Tertiary (LOW confidence)
- PyPI JSON API version checks for `coloraide`, `tinycss2`, `beautifulsoup4`, `lxml`, `cssselect`

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — libraries confirmed via Context7 and PyPI, but legitimacy seam returned [SUS] due to missing download metadata.
- Architecture: MEDIUM — approach is standard static analysis, but exact template dummy-context shape is an assumption.
- Pitfalls: MEDIUM — derived from the actual `app.css` structure (e.g., `color-mix()`, `filter()` usage) and Context7 docs.

**Research date:** 2026-06-13
**Valid until:** 2026-07-13 (30 days; Python ecosystem is stable)
