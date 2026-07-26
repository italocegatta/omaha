## MODIFIED Requirements

### Requirement: Visual coverage SHALL retain approved desktop matrix

Visual regression suite SHALL capture remaining covered states only at desktop
`1440x900`. Prior owner-approved mobile removal remains policy history and SHALL
NOT be interpreted as proof mobile CSS, layout, or interaction works. Owner
authorizes removal of exactly these additional desktop nodes and baselines:

- `tests/visual/test_snapshots.py::test_assets_table_snapshot[desktop]`
- `tests/visual/test_snapshots.py::test_classes_snapshot[desktop]`

Suite SHALL retain exactly this desktop visual matrix:

- `test_login_snapshot[desktop]`
- `test_patrimonio_snapshot[desktop]`
- `test_rebalance_form_snapshot[desktop]`
- `test_rebalance_plan_snapshot[desktop]`
- `test_import_form_snapshot[desktop]`
- `test_import_review_snapshot[desktop]`
- `test_rentabilidade_stub_snapshot[desktop]`
- `test_proventos_stub_snapshot[desktop]`

Same seeded `/patrimonio` full-page state remains covered by
`test_patrimonio_snapshot[desktop]`; integration covers distribution/class
summary; E2E covers table sorting/column geometry and dashboard structural gate.
No other desktop visual node, non-visual test, E2E coverage, integration
coverage, browser harness, runtime safety work, or visual lane SHALL be removed.

#### Scenario: Retained desktop baselines reconcile
- **WHEN** maintainer collects visual suite and inspects committed baselines
- **THEN** collection contains exactly retained eight desktop node IDs
- **AND** baseline directory contains corresponding eight desktop PNGs
- **AND** neither authorized removed desktop node nor matching PNG exists

#### Scenario: Prior mobile policy remains clean
- **WHEN** maintainer inspects visual collection, baselines, audit, and docs
- **THEN** no `[mobile]` visual node or `*-mobile.png` baseline exists
- **AND** documentation records mobile-removal history without asserting mobile support

#### Scenario: Manifest population reconciles exact desktop reduction
- **WHEN** post-removal canonical collection completes
- **THEN** manifest and lane checksums reconcile exactly 1,043 nodes
- **AND** audit inventory reconciles exactly 1,043 surviving nodes
- **AND** two exact accepted skip identities remain unchanged
