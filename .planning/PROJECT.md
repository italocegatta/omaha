# Omaha

## What This Is

Omaha is a self-hosted family investment portfolio tracker for two profiles (Italo and Ana Livia). It stores holdings against user-defined asset classes with target allocations, imports broker CSV statements, and renders a distribution dashboard showing target-vs-current drift.

## Core Value

The family opens the app, sees where the portfolio is, trusts the numbers, and closes the tab.

## Current Milestone: v1.2 bug de visualização

**Goal:** Fix basic color-visibility defects and apply a robust, WCAG-aligned palette so text and interactive states remain readable everywhere.

**Target features:**
- Audit every interactive state (default, hover, active, focus, disabled) for text/background color collisions
- Fix buttons and links where state changes make text invisible
- Fix hover states where background and text end up the same color
- Apply corrected color tokens to `app.css` and update `DESIGN.md`
- Validate contrast ratios against WCAG 2.1 AA (body ≥ 4.5:1, large/UI ≥ 3:1)
- Add regression protection (visual tests, contrast assertions, or a documented manual checklist)

## Requirements

### Validated

- CSV import with preview, review, and commit flow
- Asset class CRUD with inline editing on the dashboard
- Asset CRUD with inline create/delete per class
- Per-asset target percentage editing with per-class sum validation
- Profile-aware data isolation (Italo / Ana Livia)
- Shared-password authentication
- Distribution dashboard with portfolio header, class sections, compare bars, and per-asset progress bars

### Active

- Audit and fix color-visibility defects across all UI states
- Define and lock a contrast-safe color token system
- Update `app.css` and `DESIGN.md` with corrected tokens
- Add regression protection for future color/contrast changes

### Out of Scope

- Live market quotes / BRL-USD conversion / rebalancing (deferred to future)
- Multi-tenancy or public access
- Mobile native app
- Real-time updates / WebSocket

## Context

- Two non-expert investors using the app on a home network from laptops and phones.
- Self-hosted FastAPI + SQLAlchemy 2 + SQLite + Jinja2 + Alpine.js stack.
- Dev server bound to `0.0.0.0`; production uses docker compose + nginx TLS terminator.
- UI language is Portuguese (PT-BR); code/comments may be English.
- Design direction in `DESIGN.md`: restrained palette, one accent, Inter + Source Serif 4, true off-white body, generous dashboard spacing.
- M002 closed all slices but validation returned `needs-attention`: one e2e regression in `test_s05_user_journey.py` and two scope gaps (R12 class inline edit frontend, R13 live client-side recalculation) remain to be addressed or explicitly descoped.

## Constraints

- **Tech stack**: FastAPI, Jinja2, Alpine.js, SQLite. No React/Vue rewrite.
- **Deployment**: Self-hosted Docker compose; no public CDN dependencies for fonts if possible.
- **Accessibility**: WCAG 2.1 AA target; `prefers-reduced-motion: reduce` honored.
- **Language**: User-visible strings in PT-BR.
- **Scope**: Single household; no multi-tenant traffic or scale requirements.
- **Network access (non-negotiable)**: The app is always opened from
  another machine on the LAN — the dev host is a server, not a client.
  The dev server MUST be bound with `--host 0.0.0.0`; the canonical
  URL the user opens is detected via `bash scripts/print_lan_url.sh`.
  Never `localhost`, never `127.0.0.1`. See `AGENTS.md` and README
  "Network access".

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Allocation sum-to-100 warns, never blocks class creation | Users build portfolios incrementally; first class at 60% must be valid | ✓ Good |
| Commit-to-main with per-task pytest + UI pause for visible changes | Human-in-the-loop validation catches visual/interactive regressions | — Pending |
| Caveman full mode for chat responses | Saves tokens while preserving technical accuracy | ✓ Good |
| Import modal + retired `/import` route | Single-page workspace goal | ✓ Good |
| Per-class asset sum validation retained; per-profile sum removed | Semantically different constraints | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-13 after starting milestone v1.2 bug de visualização*
