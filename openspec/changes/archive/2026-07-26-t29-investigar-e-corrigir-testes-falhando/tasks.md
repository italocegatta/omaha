## 1. Exact authorized desktop cleanup

- [x] 1.1 Remove only `test_assets_table_snapshot[desktop]` and
  `test_classes_snapshot[desktop]` from visual parametrization; preserve mobile
  removal history and all other visual nodes.
- [x] 1.2 Delete only matching assets/classes desktop baseline PNGs. Do not
  modify remaining desktop PNGs, runtime, CSS, templates, application files,
  runner safety, or non-visual tests.
- [x] 1.3 Remove exact two-node references from visual manifest/audit/docs;
  preserve retained eight-node desktop matrix and two exact accepted skips.

## 2. Post-removal reconciliation

- [x] 2.1 Regenerate committed immutable manifest/checksum for exactly 1,043
  nodes, lane membership, two exact skip identities, and retained 18 focused
  T29 harness nodes.
- [x] 2.2 Regenerate `tests/AUDIT.md` to exactly 1,043 node rows; record prior
  mobile-removal history, exact two-node desktop removal, retained matrix, and
  lost independent focused pixel-diff trade-off.
- [x] 2.3 Verify focused collection and baseline inventory: eight retained
  desktop visual nodes; no assets/classes desktop node or PNG; no mobile node or
  PNG; all other lanes and runner safeguards unchanged.

## 3. Unchanged canonical proof protocol

- [x] 3.1 Run fresh canonical `uv run task test` proof run 1. Require green,
  <=300 seconds through cleanup, 1,043 nodes/checksum/lanes, two exact skips,
  and clean children.
- [x] 3.2 Only if 3.1 passes, run fresh proof run 2 with identical acceptance
  checks.
- [x] 3.3 Only if 3.2 passes, run fresh proof run 3 with identical acceptance
  checks; publish acceptance only after all three pass. Receipts: 280.98s,
  276.10s, and 274.77s.

## 4. Stop condition

- [x] 4.1 At first failed, >300-second, population-mismatched, or
  child-cleanup-failed proof run, stop remaining proof runs; record receipt,
  bottleneck, forecast, and measured alternatives for owner decision.
- [x] 4.2 Do not remove, skip, xfail, disable, move, or replace further
  coverage; do not claim <=300-second fix without all three fresh proofs.
