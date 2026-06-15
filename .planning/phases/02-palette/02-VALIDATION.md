---
phase: 02
slug: palette
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-13
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing, Phase 1 tests) |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `uv run pytest tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x` |
| **Full suite command** | `uv run pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run python3 -c "from omaha.audit.css_parser import ... ; [token verification]"` 
- **After every plan wave:** Run `uv run pytest tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | PALT-01 | T-02-01 / — | Token inventory returns all Passa after correction | unit | `uv run python3 -c "from omaha.audit.css_parser import parse_stylesheet, color_token_inventory; from pathlib import Path; sheet = parse_stylesheet(Path('src/omaha/static/app.css')); rows = color_token_inventory(sheet); assert all(r.status == 'Passa' for r in rows), [r.token for r in rows if r.status == 'Falha']"` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | PALT-02 | T-02-02 / — | Each corrected token pair meets WCAG AA threshold | unit | `uv run python3 -c "from omaha.audit.color_resolver import contrast_ratio, aa_status; pairs = [('oklch(0.53 0.13 50)', 'oklch(0.975 0.003 60)'), ('oklch(0.52 0.10 200)', 'oklch(0.975 0.003 60)'), ('#ffffff', 'oklch(0.50 0.18 25)')]; [print(f'{fg} on {bg}: {contrast_ratio(fg,bg):.2f} {aa_status(contrast_ratio(fg,bg))[1]}') for fg,bg in pairs]"` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | PALT-03 | — / — | DESIGN.md token table has Contrast column with correct ratios | manual-only | Grep DESIGN.md for "Passa" and "Falha" in token rows | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase02_tokens.py` — covers PALT-01 (token inventory all Passa), PALT-02 (real-pair contrast thresholds)
- [ ] Token verification inline script — wrap in a test function with fixture for `app.css` path
- [ ] `tests/conftest.py` — already exists, may need `app_css_path` fixture
- [ ] Framework install: `uv run pytest --version` — already working

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DESIGN.md token table matches app.css values | PALT-03 | Markdown static content — no programmatic assertion on DESIGN.md structure | Grep DESIGN.md token table rows for Passa/Falha; verify each token value matches app.css |
| Visual character of replacement colors | PALT-01 | OKLCH hue preservation at lowered L values needs human eye-check | Open app in browser; inspect --class-4 and --class-6 swatches; verify still look like "burnt orange" and "teal" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
