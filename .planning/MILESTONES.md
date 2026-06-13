# Milestones

## Completed

### v1.0 — M001: Setup + Importer + Visualization

- CSV import, asset/class CRUD, dashboard visualization, Playwright e2e coverage.
- Completed 2026-06-12.

### v1.1 — M002: Single-Page Portfolio Workspace

- Schema migration for `asset.target_pct`, inline asset target editing.
- Class collapse/expand, inline class CRUD, retired `/classes` route.
- Asset inline create/delete, retired `/assets` route.
- Import modal two-step flow, retired `/import` route.
- Visual polish, accessibility, responsive layout.
- Full UAT journey e2e + regression sweep.
- Validation verdict: `needs-attention` — one e2e regression (`test_s05_user_journey.py`) and two scope gaps (R12 class inline edit frontend, R13 live client-side recalculation) noted before closure.

## Active

(None)

## Pending

- v1.2 — Visual bug fix / color palette audit
