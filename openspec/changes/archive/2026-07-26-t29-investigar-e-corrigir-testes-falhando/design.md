## Context

Historic serial collection had 1,026 nodes, 1,024 passed, 2 skipped, and took
610.17 seconds. Focused T29 harness coverage raised population to 1,055 nodes.
Authorized mobile removal reduced desktop-only population to 1,045. Run 1 was
green in 285.45 seconds; run 2 exceeded 300 seconds. Owner authorizes exact
removal of two duplicated/minimally covered desktop nodes. Browser lanes retain
separate ports/databases. No production defect is proven.

## Goals / Non-Goals

**Goals**

- Preserve complete concurrent routine and runner safety.
- Remove exact two authorized desktop visual nodes and all matching artifacts.
- Establish 1,043 nodes as post-apply immutable accepted population.
- Retain eight-node desktop visual matrix and every non-visual contract.
- Keep three-fresh-run <=300-second proof protocol; stop first failed proof.

**Non-Goals**

- Claim a <=300-second fix from current receipts.
- Remove additional coverage, change lane selection, or alter skips.
- Modify tests beyond exact node/baseline/manifest/audit/documentation cleanup.
- Change runtime, CSS, templates, routes, source, or browser harness safety.

## Decisions

### D1 — Exact two-node desktop authorization

Remove only:

1. `tests/visual/test_snapshots.py::test_assets_table_snapshot[desktop]`
2. `tests/visual/test_snapshots.py::test_classes_snapshot[desktop]`

Remove matching PNGs and every manifest/audit/documentation reference. Prior
mobile-removal history remains intact. This 1,045 − 2 calculation yields exact
post-apply population of 1,043 nodes.

### D2 — Retained desktop matrix and coverage rationale

Retain eight 1440x900 desktop nodes:

1. `test_login_snapshot[desktop]`
2. `test_patrimonio_snapshot[desktop]`
3. `test_rebalance_form_snapshot[desktop]`
4. `test_rebalance_plan_snapshot[desktop]`
5. `test_import_form_snapshot[desktop]`
6. `test_import_review_snapshot[desktop]`
7. `test_rentabilidade_stub_snapshot[desktop]`
8. `test_proventos_stub_snapshot[desktop]`

Same seeded `/patrimonio` full-page state remains pixel-covered by
`test_patrimonio_snapshot[desktop]`. Integration covers distribution/class
summary. E2E covers table sorting/column geometry and dashboard structural gate.
Trade-off: no independent focused pixel-diff baseline remains for assets/classes.

### D3 — Immutable population and runner safeguards

Regenerate manifest/checksum for 1,043 nodes, lane membership, and two exact
skip identities. Keep 18 focused harness nodes. Runner comparison, taskipy-only
lane entrypoints, test-DB preflight, process groups, failure propagation, signal
forwarding, cleanup, and child reaping remain unchanged.

### D4 — Proof protocol remains strict

Current receipts are observations, not proof. Run three fresh canonical full
routines sequentially after cleanup. Each must be green, <=300 seconds through
cleanup, match 1,043 nodes/lanes/checksum/two skips, and report clean children.
Stop immediately at first failure, ceiling miss, population mismatch, or cleanup
failure; record measured alternatives and await owner decision.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Lost focused assets/classes pixel diff | Retained full-page Patrimônio visual plus stated integration/E2E coverage. |
| Silent extra coverage loss | Exact node list, eight-node matrix, 1,043-node manifest, two exact skips. |
| Misstated performance result | Three fresh canonical proofs; current receipts explicitly non-proof. |
| Browser/process safety regression | Preserve existing taskipy runner lifecycle and test-target safeguards. |

## Migration Plan

1. Remove only two D1 node parametrizations and matching desktop PNGs.
2. Remove their manifest/audit/documentation entries; regenerate 1,043-node
   manifest/checksum and audit inventory.
3. Inspect retained eight-node desktop matrix, absent two nodes/PNGs, absent
   mobile artifacts, and two exact skips.
4. Execute D4 proof protocol unchanged; stop first failed proof.
5. Rollback restores two nodes, PNGs, and 1,045-node manifest state. No runtime
   behavior or production data changes.
