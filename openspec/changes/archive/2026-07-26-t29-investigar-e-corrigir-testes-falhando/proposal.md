## Why

Canonical `uv run task test` was one serial pytest collection: 1,024 passed,
2 skipped, 610.17 seconds. After authorized mobile visual removal, desktop-only
population is 1,045 nodes; run 1 was green in 285.45 seconds, but run 2
exceeded 300 seconds. Owner authorizes exactly two remaining duplicated or
minimally covered desktop visual nodes for removal. No production defect exists,
and authorization does not prove a <=300-second full routine.

## What Changes

- Keep concurrent taskipy orchestration for unit, integration, audit, E2E, BDD,
  and visual lanes.
- Keep full routine complete; expected post-apply immutable manifest/checksum
  population is exactly 1,043 nodes with two exact accepted skip identities.
- Keep 18 focused T29 harness nodes as deliberate contract coverage.
- Remove exactly `test_assets_table_snapshot[desktop]` and
  `test_classes_snapshot[desktop]` plus matching baseline PNGs, manifest/audit,
  and visual-documentation entries.
- Keep prior mobile-removal history, all other desktop visual nodes, all
  non-visual coverage, runner safety, and audit coverage.
- Keep proof protocol unchanged: three fresh canonical <=300-second runs;
  stop at first failure, ceiling miss, population mismatch, or cleanup failure.

## Guardrails

- No deletion, skip, xfail, disable, lane removal, or coverage move is allowed
  except prior owner-approved mobile removal and exact two desktop removals.
- Same seeded `/patrimonio` full-page state remains pixel-covered by
  `test_patrimonio_snapshot[desktop]`; integration covers distribution/class
  summary; E2E covers table sorting/column geometry and dashboard structural
  gate.
- Trade-off: focused independent pixel-diff baseline for assets/classes is lost.
- Desktop-only coverage does not prove mobile CSS, layout, or interaction.
- No claim of <=300-second fix until three fresh proofs succeed.
- `src/` remains out of scope; no CSS, template, or runtime-source change.

## Capabilities

### Modified Capabilities

- `dev-tasks`: full-run reconciliation uses 1,043-node accepted population.
- `test-suite-quality`: proof gate, audit population, and removal guard reflect
  exact two-node desktop authorization.
- `test-suite-audit`: immutable audit inventory reconciles 1,043 nodes.
- `visual-regression-baseline`: retained desktop matrix becomes eight nodes;
  assets/classes desktop baselines are removed.

## Impact

- Expected implementation: visual parametrization, two desktop PNG baseline
  deletions, manifest/checksum, `tests/AUDIT.md`, and visual documentation.
- No test, runtime, application, CSS, template, or source file changes in this
  proposal revision.
- Current receipt is not performance proof: one green 285.45-second run and one
  >300-second run. Apply must clean two nodes from every artifact, verify retained
  desktop matrix, then run three fresh canonical proofs against 1,043 nodes.
