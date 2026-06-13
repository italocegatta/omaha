---
phase: 01-audit
plan: 02
subsystem: audit
tags: [css, wcag, contrast, coloraide, tinycss2, oklch]

# Dependency graph
requires: []
provides:
  - CSS token inventory with WCAG 2.1 AA contrast status for every --* custom property
  - var() resolution, color-mix() parsing, filter brightness simulation
  - Path-traversal-safe stylesheet parsing via tinycss2
affects: [03-contrast-audit]

# Tech tracking
tech-stack:
  added: [coloraide>=8.8.1, tinycss2>=1.5.1, beautifulsoup4>=4.15.0, lxml>=6.1.1]
  patterns:
    - "Pure-function module shape: frozen dataclasses, no DB/FastAPI deps, deterministic transforms"
    - "Dataclass output contracts following csv_import.py MatchResult pattern"
    - "Recursive var() resolution with depth guard (max 10)"
    - "Path traversal protection via repo-root resolution (threat T-01-02-01)"

key-files:
  created:
    - src/omaha/audit/__init__.py
    - src/omaha/audit/css_parser.py
    - src/omaha/audit/color_resolver.py
    - tests/test_audit_css_parser.py
    - tests/test_audit_color_resolver.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Adjacent-background mapping: foreground tokens (--ink, --positive, etc.) paired against --bg; surface tokens (--bg, --surface, etc.) paired against --ink — giving the most useful readability ratio for each token"
  - "var() resolution uses iterative regex substitution with max-depth guard (10) to prevent circular-reference infinite loops"
  - "Non-color --* properties (--spacing-xs, --border as non-color) silently excluded from inventory"
  - "First-definition-wins for custom-property registry — :root tokens take precedence over component-scoped re-declarations"

patterns-established:
  - "Pure function library with frozen dataclass outputs — followed in both css_parser.py and color_resolver.py"
  - "Test fixture CSS string inline (no external fixture file dependency)"
  - "Repo-root path resolution for file reads (Path(__file__).resolve().parents[3])"

requirements-completed: [AUDT-02]

# Metrics
duration: 6min
completed: 2026-06-13
---

# Phase 01 Plan 02: CSS Parser and Color Resolver Summary

**CSS token inventory with recursive var() resolution and WCAG 2.1 AA contrast computation — 23 tokens discovered in app.css, each with Passa/Falha status.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-13T14:42:21Z
- **Completed:** 2026-06-13T14:48:34Z
- **Tasks:** 3 (1 checkpoint + 2 auto)
- **Files modified:** 7
- **Tests:** 38 passing

## Accomplishments

- Installed `coloraide`, `tinycss2`, `beautifulsoup4`, `lxml` as dev dependencies after package legitimacy verification
- Built `src/omaha/audit/css_parser.py` with `parse_stylesheet()`, `resolve_var()`, and `color_token_inventory()` — returns `TokenInventoryRow` dataclass rows for every color-valued `--*` custom property
- Built `src/omaha/audit/color_resolver.py` wrapping coloraide: `contrast_ratio()`, `aa_status()`, `apply_brightness()`, `composite_over()` — all with error-tolerant fallbacks
- `color_token_inventory` against real `app.css` discovers 23 color tokens including `--bg` (ratio 16.85 Passa), `--accent` (ratio 2.23 Falha vs --ink — correct: accent needs accent-ink text), and `--positive`/`--negative` status tokens
- var() chain resolution verified: `--fg → --ink → oklch(...)` resolves correctly; `var(--missing, #fff)` fallback works

## Task Commits

Each task was committed atomically:

1. **Task 1: Package legitimacy checkpoint** — User approved via human-verify (no code commit)
2. **Task 2: Add dev deps and create audit package stubs** — `aee9f4a` (feat)
3. **Task 3: Implement CSS parser, color resolver, and token inventory** — `2daa1da` (feat)

## Files Created/Modified

- `src/omaha/audit/__init__.py` — Package init following routes/__init__.py convention
- `src/omaha/audit/css_parser.py` — CSS parsing, var() resolution, token inventory (290 lines)
- `src/omaha/audit/color_resolver.py` — contrast_ratio, aa_status, brightness, compositing (120 lines)
- `tests/test_audit_css_parser.py` — 18 tests: imports, resolve_var chains/fallbacks, token inventory with real app.css
- `tests/test_audit_color_resolver.py` — 20 tests: hex/oklch/color-mix contrast, AA thresholds, brightness, alpha compositing
- `pyproject.toml` — Added coloraide, tinycss2, beautifulsoup4, lxml to dev dependencies
- `uv.lock` — Updated lockfile

## Decisions Made

- **Adjacent-background mapping:** Foreground-ish tokens (--ink, --positive, --class-1..6, etc.) paired against the resolved --bg value; surface-ish tokens (--bg, --surface, --accent, etc.) paired against --ink. This produces the most useful readability ratio: "is this text readable on the body?" or "is default text readable on this surface?"
- **var() resolution:** Iterative regex with `_MAX_VAR_DEPTH=10` guard. Handles chained refs (--fg→--ink→oklch), fallback values, and silently leaves unresolvable refs as-is
- **Non-color exclusion:** Properties like `--spacing-xs: 4px` are excluded by testing resolution with `coloraide.Color()` — only values that parse as colors appear in inventory
- **Path safety:** `parse_stylesheet()` resolves paths under `Path(__file__).resolve().parents[3]` (repo root) and rejects paths outside the repository

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Frozen dataclass dict mutation test assertion**
- **Found during:** Task 2 (stub creation)
- **Issue:** Test asserted `rule.declarations["--bg"] = "#000"` would raise — but `frozen=True` only prevents field reassignment, not dict-content mutation
- **Fix:** Changed assertion to test field reassignment (`rule.declarations = {...}`) which correctly raises
- **Files modified:** `tests/test_audit_css_parser.py`
- **Committed in:** `aee9f4a` (Task 2 commit)

**2. [Rule 1 - Bug] composite_over alpha channel access via Color.get()**
- **Found during:** Task 3 (implementation)
- **Issue:** `Color.get("alpha", 1.0)` threw TypeError — coloraide's `get()` doesn't accept a default argument (only 2 positional params)
- **Fix:** Used `Color["alpha"]` with try/except KeyError fallback to 1.0
- **Files modified:** `src/omaha/audit/color_resolver.py`
- **Committed in:** `2daa1da` (Task 3 commit)

**3. [Rule 1 - Bug] Test expectation: --accent-ink vs --bg contrast >= 4.0**
- **Found during:** Task 3 (testing)
- **Issue:** `--accent-ink` (off-white, oklch 0.98) paired against `--bg` (off-white, oklch 0.975) has ratio 1.02 — expected, since accent-ink is never used on the body background. Test was incorrectly asserting >= 4.0
- **Fix:** Changed test to assert `status == "Falha"` (correctly flagging that accent-ink on body fails)
- **Files modified:** `tests/test_audit_css_parser.py`
- **Committed in:** `2daa1da` (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (3 Rule 1 bugs)
**Impact on plan:** All fixes were test/API corrections. No scope creep. No architectural changes.

## Issues Encountered

- `uv add --dev` left 4 zero-byte garbage files (`=1.5.1`, `=4.15.0`, `=6.1.1`, `=8.8.1`) in repo root — removed before Task 2 commit
- coloraide `Color.get()` API doesn't match Python dict convention (no default arg) — switched to `Color["alpha"]` with KeyError fallback

## Known Stubs

None — all planned functions are fully implemented. `resolve_var`, `color_token_inventory`, `contrast_ratio`, `aa_status`, `apply_brightness`, `composite_over` all have complete logic.

## Threat Flags

None — all three threat mitigations from the plan's threat model are implemented:
- **T-01-02-01** (path traversal): `parse_stylesheet()` resolves under repo root, rejects `..` escapes
- **T-01-02-02** (package install): blocking human-verify checkpoint in Task 1
- **T-01-02-03** (untrusted CSS execution): uses tinycss2 and coloraide parsers; no `eval()`

## Next Phase Readiness

- CSS token inventory with contrast ratios is ready for Phase 01 Plan 01 (interactive element inventory — AUDT-01)
- `color_token_inventory()` returns 23 rows from real `app.css` with Passa/Falha status — ready to feed into the report generator
- Blocked by: none

---
*Phase: 01-audit*
*Completed: 2026-06-13*

## Self-Check: PASSED

- All 5 key files exist on disk
- Both plan commits (aee9f4a, 2daa1da) present in git log
- 38 tests passing
- All 5 acceptance criteria verified (see Task 3 verification)
- No remaining stubs
