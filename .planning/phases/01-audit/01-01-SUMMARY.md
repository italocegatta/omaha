---
phase: 01-audit
plan: 01-01
subsystem: audit
tags: [wcag, contrast, css, html-report, jinja2, beautifulsoup4, tinycss2, coloraide, portuguese]

# Dependency graph
requires:
  - phase: 01-audit
    plan: 01-02
    provides: CSS parser (tinycss2), color resolver (coloraide), token inventory
provides:
  - Per-page interactive-element inventory with default/hover/active/focus/disabled color pairs
  - Self-contained Portuguese HTML audit report with summary cards, TOC, per-page tables, token inventory, failure log
  - CLI entry point and wrapper script for generating the report artifact
affects: [02-fix-palette, 03-apply-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pure-function module shape (from __future__ import annotations, dataclasses, no DB/FastAPI)
    - Jinja2 Environment with FileSystemLoader for template rendering (no Request object)
    - argparse + main(argv) pattern for CLI (analog: scripts/backup.py)
    - CSS rule cascade: base (default) + overlay (state-specific) for color resolution
    - Path traversal guard: reject parent-dir escapes on input paths, relax on output paths

key-files:
  created:
    - src/omaha/audit/inventory.py
    - src/omaha/audit/report.py
    - src/omaha/audit/cli.py
    - src/omaha/templates/audit_report.html
    - scripts/generate_contrast_audit.py
    - reports/.gitkeep
    - reports/contrast_audit.html
    - tests/test_audit_inventory.py
    - tests/test_audit_report.py
  modified: []

key-decisions:
  - "CSS cascade for state colors: base (default) declarations form the foundation; state-specific rules overlay properties like background/filter while inheriting color"
  - "Report template is standalone (no base.html extension) with inline CSS — self-contained, no CDN, fully portable"
  - "Output path validation relaxed for generated reports (can write outside repo root); only input paths (CSS, templates) enforce path-traversal guard"

patterns-established:
  - "InteractiveStateRow dataclass: frozen, carries template/selector/element_snippet/state/fg/bg/ratio/status/hidden_by_default"
  - "AuditContextFactory: returns SimpleNamespace-based dummy contexts per template name"
  - "CLI error handling: return non-zero exit code with 'audit FAIL: <ExceptionType>: <msg>' on stderr"

requirements-completed: [AUDT-01]

# Metrics
duration: 25min
completed: 2026-06-13
---

# Phase 01 Plan 01: Audit Inventory Summary

**Interactive-element inventory discovers 300+ state color pairs across 8 templates and renders a self-contained 329 KB Portuguese audit report with WCAG 2.1 AA contrast ratios.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-06-13T14:50:00Z
- **Completed:** 2026-06-13T15:15:00Z
- **Tasks:** 3
- **Files modified:** 9 created

## Accomplishments
- Inventory discovers interactive elements (`button, a[href], input, select, textarea, [tabindex]`) from all 8 rendered templates
- State color pairs cascade correctly: default declarations form the base, state-specific rules overlay background/filter while inheriting color
- 329 KB self-contained Portuguese report with summary cards, per-page collapsible tables, CSS token inventory, failure log, and "Mostrar apenas falhas" toggle
- CLI with `--css`, `--templates-dir`, `--output` flags generates report artifact in one command

## Task Commits

Each task was committed atomically:

1. **Task 1: Interactive element inventory and state color pairs** - `ee0395c` (feat)
2. **Task 2: Self-contained Portuguese HTML report** - `c48777f` (feat)
3. **Task 3: CLI and audit artifact generation** - `61ddf13` (feat)

## Files Created/Modified
- `src/omaha/audit/inventory.py` - Interactive element discovery, CSS rule matching, state color pair computation
- `src/omaha/audit/report.py` - Full audit pipeline: CSS parse → inventory → token inventory → report render → write
- `src/omaha/audit/cli.py` - Argparse CLI with `--css`, `--templates-dir`, `--output` flags
- `src/omaha/templates/audit_report.html` - Standalone Jinja2 report template with inline CSS, lang="pt-BR"
- `scripts/generate_contrast_audit.py` - Thin wrapper around `omaha.audit.cli.main`
- `reports/.gitkeep` - Directory marker for `reports/`
- `reports/contrast_audit.html` - Generated audit artifact (329 KB)
- `tests/test_audit_inventory.py` - 35 tests for context factory, rendering, element discovery, state pairs
- `tests/test_audit_report.py` - 21 tests for report structure, badges, swatches, toggle, CLI integration

## Decisions Made
- **CSS cascade for state colors:** Base (default) declarations form the foundation; state-specific rules overlay properties like `background` and `filter` while inheriting `color`. This correctly handles `.btn-primary:hover { filter: brightness(1.1) }` which doesn't re-declare `color`.
- **Standalone report template:** `audit_report.html` does not extend `base.html` — it's fully self-contained with inline CSS. No CDN dependencies, no external requests.
- **Output path relaxation:** The path-traversal guard (threat T-01-01-01) is enforced only on input paths (CSS, templates). The output path may be outside the repo root (e.g., `/tmp` for tests).
- **AuditContextFactory shape:** Uses `SimpleNamespace` objects nested in plain dicts — matches the Jinja2 attribute-dot access pattern (`profile.name`, `asset.id`) without SQLAlchemy overhead.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CSS hover state returned None due to missing cascade**
- **Found during:** Task 1 (state_color_pairs implementation)
- **Issue:** For non-default states, only state-specific rules were collected. But CSS doesn't re-declare `color` on hover — it inherits from the base `.btn-primary` rule. The function returned `None` because `fg` was missing.
- **Fix:** Rewrote `state_color_pairs` to merge base (default) declarations with state-specific overlay. Base rules provide `color`; state rules override `background` and `filter`.
- **Files modified:** `src/omaha/audit/inventory.py`
- **Verification:** `test_hover_state_differs_from_default` passes — hover row now computes correctly with different bg from brightness filter
- **Committed in:** `ee0395c` (Task 1 commit)

**2. [Rule 2 - Missing Critical] AuditContextFactory missing `assets_by_class` and `class_suggestions`**
- **Found during:** Task 2 (report generation — templates failed to render)
- **Issue:** `assets.html` references `assets_by_class[c.id]` and `import_review.html` references `class_suggestions.get(rp.broker_ticker)`. The factory didn't provide these keys, causing render_page to return empty strings.
- **Fix:** Added `assets_by_class` dict to `_assets_context()` and `class_suggestions` dict to `_import_review_context()`.
- **Files modified:** `src/omaha/audit/inventory.py`
- **Verification:** All 8 template rendering tests pass
- **Committed in:** `ee0395c` (Task 1 commit)

**3. [Rule 3 - Blocking] generate_report rejected output paths outside repo root**
- **Found during:** Task 2 (test_generate_report_writes_file)
- **Issue:** The path-traversal guard treated output paths the same as input paths. Writing to `tmp_path` (pytest temp dir) was rejected with "outside the repository root".
- **Fix:** Made output path resolution accept absolute paths directly, without enforcing repo-root containment. Input paths (CSS, templates) still enforce the guard.
- **Files modified:** `src/omaha/audit/report.py`
- **Verification:** `test_generate_report_writes_file` and all other generate_report tests pass
- **Committed in:** `c48777f` (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 bug, 1 missing critical, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep. The cascade fix in particular is essential — without it, hover/active/focus/disabled states would all return None.

## Issues Encountered
- Templates extend `base.html` which imports Alpine.js (external CDN). The audit report template is standalone and doesn't have this issue.
- The login page button (`<button type="submit">Entrar</button>`) has no CSS class, so no color rules match via static analysis. This is correct — the audit can only analyze what CSS defines. The login inventory returns 0 rows by design.

## Threat Flags

None — all files are within the threat model's scope. Path-traversal guard (T-01-01-01) is enforced for input paths. The report is internal (T-01-01-02 accepted). Rendering errors are caught without retry loops (T-01-01-03).

## Next Phase Readiness
- Audit inventory complete — ready for Phase 02 (fix-palette) which will analyze failure log and correct color tokens
- Report artifact (`reports/contrast_audit.html`) documents current WCAG AA violations for reference
- All AUDT-01 requirements fulfilled

---
*Phase: 01-audit*
*Completed: 2026-06-13*
