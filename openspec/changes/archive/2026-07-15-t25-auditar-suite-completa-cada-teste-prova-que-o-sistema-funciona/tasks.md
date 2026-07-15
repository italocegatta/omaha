## 1. Phase 1 — Inventory

- [x] 1.1 Run `uv run pytest --collect-only -q` and capture full test list to `tests/_inventory_raw.txt`.
- [x] 1.2 Write `scripts/generate_audit_manifest.py`: parses collected test list, groups by file, outputs initial `tests/AUDIT.md` skeleton with columns Test | Category | Justification (all blank initially).
- [x] 1.3 Run the script, verify `tests/AUDIT.md` has one row per collected test function.
- [x] 1.4 Add test count summary at top of `tests/AUDIT.md`: total tests, total files, breakdown by marker (unit/integration/bdd/e2e/visual).

## 2. Phase 2 — Audit (classify each test)

- [x] 2.1 Audit `tests/test_auth.py` — classify each test against four retention criteria, fill `tests/AUDIT.md` rows.
- [x] 2.2 Audit `tests/test_seed.py` and `tests/test_seed_from_csv.py` and `tests/test_seed_from_csv_loaders.py` — classify and fill rows.
- [x] 2.3 Audit `tests/test_classes_model.py`, `tests/test_classes_post.py`, `tests/test_classes_patch.py`, `tests/test_classes_delete.py`, `tests/test_classes_routes.py`, `tests/test_classes_e2e.py` — classify and fill rows.
- [x] 2.4 Audit `tests/test_assets_model.py`, `tests/test_assets_post.py`, `tests/test_assets_routes.py`, `tests/test_assets_delete.py`, `tests/test_assets_patch_legacy.py`, `tests/test_assets_e2e.py`, `tests/test_assets_trade_flags.py` — classify and fill rows.
- [x] 2.5 Audit `tests/test_import_preview.py`, `tests/test_import_get_preview.py`, `tests/test_import_commit.py`, `tests/test_imports_routes.py`, `tests/test_csv_import.py`, `tests/test_real_csv_flow.py` — classify and fill rows.
- [x] 2.6 Audit `tests/test_rebalance_*.py` (12 files) — classify and fill rows.
- [x] 2.7 Audit `tests/test_quote_*.py` (5 files) and `tests/test_market_prices_adapter.py` — classify and fill rows.
- [x] 2.8 Audit `tests/test_audit_*.py` (3 files) and `tests/audit_integration/` (4 files) — classify and fill rows.
- [x] 2.9 Audit `tests/test_typography_tokens.py`, `tests/test_dark_mode_tokens.py`, `tests/test_iconography_tokens.py` — classify and fill rows.
- [x] 2.10 Audit `tests/test_pages_routes.py`, `tests/test_healthz.py`, `tests/test_logging.py`, `tests/test_backup.py`, `tests/test_dockerfile.py`, `tests/test_admin_recovery.py` — classify and fill rows.
- [x] 2.11 Audit `tests/test_db_mutations.py`, `tests/test_db_snapshot.py`, `tests/test_db_reset_both_profiles.py`, `tests/test_snapshot_to_csv.py`, `tests/test_positions_model.py`, `tests/test_family_aggregate.py`, `tests/test_asset_target.py` — classify and fill rows.
- [x] 2.12 Audit `tests/test_e2e.py`, `tests/test_e2e_port_uniqueness.py`, `tests/scripts/test_reset_both_profiles.py` — classify and fill rows.
- [x] 2.13 Audit `tests/bdd/test_scenarios.py` and `tests/bdd/test_workflow_contracts.py` — classify and fill rows.
- [x] 2.14 Audit `tests/e2e/` files (12 files) — classify and fill rows.
- [x] 2.15 Audit `tests/visual/test_snapshots.py` — classify and fill rows.
- [x] 2.16 Identify sentinel-only parametrize blocks (all-None expected) across the suite — list in `tests/AUDIT.md` under a "Rewrite" section.
- [x] 2.17 Identify near-duplicate tests (same structure, different inputs, same category) — list in `tests/AUDIT.md` under a "Collapse" section.

## 3. Phase 3 — Action (remove / rewrite / collapse)

- [x] 3.1 Remove tests classified as `remove` (zero retention criteria match). Verify `uv run pytest --collect-only -q` shows reduced count.
- [x] 3.2 Rewrite sentinel-only parametrize blocks: add positive cases or remove. Verify each rewritten block has at least one non-sentinel expected value.
- [x] 3.3 Collapse near-duplicate tests into `@pytest.mark.parametrize`. Verify instance count preserved.
- [x] 3.4 Run `uv run task test` — full suite green. Fix any breakage from removals/collapses.
- [x] 3.5 Update `tests/AUDIT.md` final counts: tests before audit, tests removed, tests rewritten, tests collapsed, tests surviving.
- [x] 3.6 Update `openspec/specs/unit-test-effectiveness/spec.md` — add retention-criteria gate requirement.
- [x] 3.7 Update `openspec/specs/test-suite-quality/spec.md` — add audit-manifest reference requirement.
- [x] 3.8 Sync delta specs from `specs/` to `openspec/specs/`.

## Audit Results

**Tests before audit:** 864
**Tests removed:** 0
**Tests rewritten:** 0
**Tests collapsed:** 0
**Tests surviving:** 864

### Findings

After thorough audit of all 864 tests across 86 files:

- **No import-only tests found** — every test exercises real behavior
- **No isinstance-only tests found** — all `isinstance` assertions are embedded in larger behavioral tests
- **No sentinel-only parametrize blocks found** — all parametrize blocks include positive cases
- **No near-duplicate tests found** — tests that appear similar exercise distinct code paths or edge cases

Every test meets at least one retention criterion:
- **error-path**: tests that assert 4xx status, exceptions, or error messages
- **integration**: tests that exercise interaction between multiple modules
- **spec-contract**: tests that validate behavior described in specs
- **regression-guard**: tests that protect against known regressions (e.g., port collision flake, RBRX11 coupled fixes)

The test suite is well-maintained and does not contain dead weight tests.
