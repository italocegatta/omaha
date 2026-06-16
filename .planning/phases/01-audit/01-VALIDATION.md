---
phase: 01-audit
slug: audit
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-13
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/test_audit_*.py -q` |
| **Full suite command** | `uv run pytest tests -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_audit_*.py -q`
- **After every plan wave:** Run `uv run pytest tests -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 2 | AUDT-01 | T-01-01-01 | Resolve paths under repo root | unit | `uv run pytest tests/test_audit_inventory.py -q` | ❌ W2 | ⬜ pending |
| 01-01-02 | 01 | 2 | AUDT-01 | — | N/A | integration | `uv run pytest tests/test_audit_report.py -q` | ❌ W2 | ⬜ pending |
| 01-01-03 | 01 | 2 | AUDT-01 | T-01-01-01 | Resolve paths under repo root | cli/integration | `uv run python scripts/generate_contrast_audit.py && test -f reports/contrast_audit.html` | ❌ W2 | ⬜ pending |
| 01-02-01 | 02 | 1 | AUDT-02 | T-01-02-02 | Confirm package legitimacy on official PyPI pages | human-check | User approves package legitimacy checkpoint | N/A | ⬜ pending |
| 01-02-02 | 02 | 1 | AUDT-02 | T-01-02-02 | Confirm package legitimacy before `uv add` | integration | `uv run pytest tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -q` | ❌ W1 | ⬜ pending |
| 01-02-03 | 02 | 1 | AUDT-02 | T-01-02-01 / T-01-02-03 | Resolve CSS paths under repo root; never `eval()` parsed values | unit | `uv run pytest tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -q` | ❌ W1 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Stub / Pre-execution Requirements

Stub dependencies are covered by `01-02-PLAN.md` Task 2 (Wave 1: dev dependencies + audit package/test stubs).

- [x] `tests/test_audit_css_parser.py` — stubs for AUDT-02
- [x] `tests/test_audit_color_resolver.py` — stubs for AUDT-02
- [x] `tests/test_audit_inventory.py` — stubs for AUDT-01
- [x] `tests/test_audit_report.py` — stubs for AUDT-01 report generation
- [x] `pyproject.toml` — add `coloraide`, `tinycss2`, `beautifulsoup4`, `lxml` to `[dependency-groups] dev`
- [x] `src/omaha/audit/` package created with module stubs for import tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Report visual layout matches UI-SPEC | AUDT-01 | Visual/spacing judgment | Open `reports/contrast_audit.html` in browser; compare sections to 01-UI-SPEC.md |
| Audit dependency package legitimacy | AUDT-02 | Requires human judgment on PyPI source/authorship | Open official PyPI pages for beautifulsoup4, tinycss2, coloraide, lxml; confirm versions match `01-RESEARCH.md` minimums; type `approved` to continue |

---

## Validation Sign-Off

- [x] All automated tasks have `<automated>` verify or stub dependencies; human-verify checkpoints (e.g., `01-02` Task 1) are excluded from this claim
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 1 covers all stub / MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
