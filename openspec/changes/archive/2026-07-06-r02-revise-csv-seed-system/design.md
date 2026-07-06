## Context

`scripts/seed_from_csv.py` is the **only** sanctioned path for
creating `AssetClass` / `Asset` / `Position` rows (PRD §4.3,
`seeded-state` spec, `data-driven-seed` spec). The script reads the
per-profile CSV triplet under `data/seed/`, validates sums and
cross-references, and writes in one of three modes (`reset`,
`upsert`, `diff`). The current file is 1010 lines and mixes six
distinct concerns separated only by `# --- XXX ---` section headers.

The script has four external consumers that depend on its public
surface:

- `scripts/snapshot_to_csv.py:80` — `from scripts.seed_from_csv
  import abort`
- `scripts/reset_both_profiles.py:42` — `from scripts.seed_from_csv
  import PROFILES, load_assets, load_classes, load_positions,
  run_reset`
- `tests/test_seed_from_csv.py` — runs the script via subprocess
  (`python -m scripts.seed_from_csv …`) **and** imports it as a module
  (`import scripts.seed_from_csv as seed_mod`) so it can patch
  `seed_mod.SEED_DIR` and call `seed_mod.load_classes(...)` directly
- `tests/scripts/test_reset_both_profiles.py` — `from
  scripts.seed_from_csv import PROFILES`

The refactor must keep all four consumers unchanged: same module
path, same importable names, same `python -m` invocation, same
abort messages, same exit codes.

The `data-driven-seed` capability spec (in `openspec/specs/`) pins the
CSV schema, validation rules, and abort semantics. This refactor
leaves that contract untouched.

## Goals / Non-Goals

**Goals:**

- Reduce `scripts/seed_from_csv.py` from one 1010-line file to a small
  package whose internal structure mirrors the existing section
  headers (one module per concern). No single file in the package
  exceeds ~300 lines.
- Keep every external consumer working unchanged (see Context).
- Drop the stale F01-fixture narrative from the script's
  `PROFILE_OWNER_TO_NAME` block — the fixture rows are gone, the
  comment is dead history.
- Add focused unit tests for the loader and validator layers. Today
  every seed-path assertion goes through the subprocess runner in
  `tests/test_seed_from_csv.py`; there is no per-layer regression
  harness.

**Non-Goals:**

- No change to the CSV schema (column names, order, encoding,
  parsing rules). The `data-driven-seed` spec stays byte-identical.
- No change to the three modes' observable behaviour (rows
  inserted/updated, summary counts, abort messages, exit codes).
- No change to the Taskipy tasks (`db-seed-from-csv`, `db-seed-diff`,
  `db-seed-upsert`). They invoke `python -m scripts.seed_from_csv`
  which still resolves.
- No change to the runtime path (no routes / models / templates
  touched). The refactor is internal to `scripts/`.
- No new public API on the package. The `__init__.py` re-exports the
  same names external consumers import today; no new symbols leak.

## Decisions

### D-R02.1 — Convert to a package, not a single file

`scripts/seed_from_csv.py` (1010 lines) becomes
`scripts/seed_from_csv/` with one module per concern. Rationale: the
section-header pattern in the current file already names the
concerns (`CSV row dataclasses`, `CSV loaders`, `Validation
pipeline`, `Profile resolution`, `Modes`, `Driver`). Making each
concern a real file turns the existing comments into the file
layout — no new naming scheme, no discoverability tax for new
contributors. A package also gives us a place to hang
`__main__.py` (the CLI driver) so `python -m scripts.seed_from_csv`
keeps working.

**Alternative considered:** keep one file, add internal `# region`
markers. Rejected — does not reduce the line count, does not let
editors fold the regions reliably, and does not give the next
contributor an obvious place to add a per-layer test.

### D-R02.2 — Module layout mirrors the existing section headers

Six files, one per concern:

| File                              | Lines (approx) | Contains                                                                              |
|-----------------------------------|---------------:|---------------------------------------------------------------------------------------|
| `__init__.py`                     | ~80            | Re-exports the public API; module constants (`abort`, headers, dataclasses, funcs).  |
| `__main__.py`                     | ~70            | `parse_args` + `main` — the CLI driver. Makes `python -m` work.                        |
| `loaders.py`                      | ~250           | Row dataclasses + `_read_csv` + `_decimal`/`_optional_decimal`/`_int`/`_bool` + `load_classes`/`load_assets`/`load_positions`. |
| `validation.py`                   | ~80            | `validate(profile, classes, assets, positions)` — cross-refs + sum invariants.        |
| `profiles.py`                     | ~50            | `PROFILES`, `PROFILE_OWNER_TO_NAME` (dead history trimmed), `get_profile_id`.        |
| `modes.py`                        | ~550           | `_wipe_profile`, `run_reset`, `run_upsert`, `run_diff`.                                |

Total roughly 1010 lines (same code, six files instead of one). No
line-count budget is imposed during apply; the table is a
rough-planning aid, not a contract. The validator and the modes are
the two biggest files; both are essentially the same code in
smaller wrappers.

**Alternative considered:** seven files (split `modes.py` into
`modes_reset.py` / `modes_upsert.py` / `modes_diff.py`). Rejected —
the three modes share `_wipe_profile` and the "print summary" idiom;
splitting them forces a fourth helper file just to host the shared
bits. Net complexity higher, not lower.

### D-R02.3 — `__init__.py` re-exports the existing public API

Every name imported today by `snapshot_to_csv.py`,
`reset_both_profiles.py`, `tests/test_seed_from_csv.py`, or
`tests/scripts/test_reset_both_profiles.py` is re-exported verbatim:

- `abort`
- `PROFILES`, `PROFILE_OWNER_TO_NAME`, `REPO_ROOT`, `SEED_DIR`
- `CLASS_HEADER`, `ASSET_HEADER`, `POSITION_HEADER`
- `VALID_QUOTE_KINDS`, `VALID_CURRENCY_CODES`
- `ClassRow`, `AssetRow`, `PositionRow`
- `load_classes`, `load_assets`, `load_positions`, `validate`
- `get_profile_id`, `run_reset`, `run_upsert`, `run_diff`

Rationale: zero-touch migration of every external consumer. Tests
that patch `seed_mod.SEED_DIR` still work because `SEED_DIR` is a
module-level binding that the test rebinds via `seed_mod.SEED_DIR =
tmp_path`; re-exporting the symbol keeps that pattern working.

The `__init__.py` does **not** re-export the leading-underscore
helpers (`_read_csv`, `_decimal`, `_optional_decimal`, `_int`,
`_bool`, `_wipe_profile`). Those stay private to the new internal
modules.

### D-R02.4 — Drop the F01-fixture narrative from `PROFILE_OWNER_TO_NAME`

Current block (lines 56–63):

```python
# Maps each CLI ``--profile`` value to the ``(user.username,
# Profile.name)`` pair the seed targets. The canonical pair
# (``italo`` → ``Italo`` / ``Italo``) keeps the legacy 1-to-1 shape;
# the F01 fixture pair (``italo_rf2`` → ``Italo`` / ``Italo RF2``)
# was retired in F07 because the F01 multi-profile intra-User
# invariant is dead — the Família sentinel (seed.py) is the only
# cross-User aggregator now. Use ``italo`` and ``ana`` only.
PROFILE_OWNER_TO_NAME: dict[str, tuple[str, str]] = {
    "italo": ("Italo", "Italo"),
    "ana": ("Ana", "Ana"),
}
```

After refactor:

```python
# Maps each CLI ``--profile`` value to the ``(user.username,
# Profile.name)`` pair the seed targets. The Família sentinel lives
# in ``seed.py`` and is not seeded via this CSV path — Família has
# no class/asset/position rows in this triplet.
PROFILE_OWNER_TO_NAME: dict[str, tuple[str, str]] = {
    "italo": ("Italo", "Italo"),
    "ana": ("Ana", "Ana"),
}
```

Rationale: the F01→F07 supercession belongs in the roadmap/PRD
history (already there), not in a code comment next to a five-line
dict. The new comment explains the current invariant (Família is
seeded elsewhere) without dredging up retired fixtures.

### D-R02.5 — Two new unit test files, no DB

- `tests/test_seed_from_csv_loaders.py` — covers `load_classes`,
  `load_assets`, `load_positions` and the row-parsing helpers
  (`_decimal`, `_optional_decimal`, `_int`, `_bool`). Uses
  `tmp_path` + inline CSV strings + `monkeypatch` on
  `scripts.seed_from_csv.SEED_DIR` (same pattern as the existing
  module-import tests in `tests/test_seed_from_csv.py`).
- `tests/test_seed_from_csv_validation.py` — covers `validate()`
  and its abort messages. Pure-function tests over pre-built
  `ClassRow` / `AssetRow` / `PositionRow` lists; no DB.

Both files are added to `_UNIT_FILES` in `tests/conftest.py` so they
pick up the `unit` marker cleanly without triggering the
`UnknownTestPath` warning. They are pure functions (no DB, no HTTP,
no Playwright); the unit allow-list is the right home.

**Alternative considered:** put the new tests under
`tests/scripts/` (mirroring `test_reset_both_profiles.py`). Rejected
— `tests/scripts/` does not match the auto-marker rule for new
files; the unit allow-list is the established way to mark
script-layer unit tests as `unit`.

### D-R02.6 — `python -m scripts.seed_from_csv` resolves via `__main__.py`

The Taskipy tasks and `tests/test_seed_from_csv.py` subprocess runner
all invoke `python -m scripts.seed_from_csv`. With the file-to-package
conversion, Python resolves `-m scripts.seed_from_csv` against the
package's `__main__.py` automatically. The CLI logic in
`__main__.py` is byte-for-byte the same as today's `parse_args` +
`main` (lines 920–1009 of the current file). No behavioural change.

## Risks / Trade-offs

- **Risk:** Re-export surface misses a symbol an external consumer
  imports → consumer breaks on first import after refactor.
  **Mitigation:** before deleting the old file, run `task test-unit
  && task test-integration && task test-bdd` and grep for every
  `from scripts.seed_from_csv import …` and `import
  scripts.seed_from_csv` call site. The four known consumers are
  enumerated in Context; if a new one shows up in the grep, add it
  to `__init__.py` before deleting the file.

- **Risk:** Circular import between `__init__.py` and the internal
  modules (e.g. `modes.py` imports `load_*` from `loaders.py`,
  which needs `CLASS_HEADER` re-exported by `__init__.py`).
  **Mitigation:** the internal modules import each other directly
  (`from scripts.seed_from_csv.loaders import load_classes, …`)
  rather than going through `__init__.py`. The `__init__.py` is
  pure re-export; it does no logic. The dependency graph is
  acyclic: `profiles.py` and `loaders.py` and `validation.py` are
  leaves; `modes.py` depends on `loaders.py` + `profiles.py`;
  `__main__.py` depends on `loaders.py` + `validation.py` +
  `profiles.py` + `modes.py`.

- **Risk:** `seed_mod.SEED_DIR` monkeypatching in
  `tests/test_seed_from_csv.py` breaks when `SEED_DIR` is imported
  via re-export rather than defined in the same module.
  **Mitigation:** `SEED_DIR` is defined in `loaders.py` (where it
  is used) and re-exported in `__init__.py`. The test currently
  patches the name on `seed_mod`; the patch rebinds the attribute
  on the `scripts.seed_from_csv` module namespace. Since the
  internal `load_classes` resolves `SEED_DIR` via module attribute
  lookup (not a captured closure), the test's rebind flows through
  naturally. Verified manually against the existing import in
  `tests/test_seed_from_csv.py:665` (`seed_mod.SEED_DIR = tmp_path`).

- **Trade-off:** the package adds one extra file (`__init__.py`) and
  one extra directory level. Cost is small (a few hundred bytes
  on disk; one extra `__init__.py` import per CLI invocation) for
  the readability win.

- **Trade-off:** the new test files duplicate some coverage that
  already exists in `tests/test_seed_from_csv.py` (e.g. the
  `quote_kind` enum assertion exists in both places). Accepted —
  the per-layer test gives a fast, focused failure when a parsing
  rule regresses, without paying the cost of a subprocess boot.

## Migration Plan

Single deploy. Steps, in order:

1. Create `scripts/seed_from_csv/` directory.
2. Create `scripts/seed_from_csv/__init__.py` (re-exports).
3. Create `scripts/seed_from_csv/__main__.py` (CLI driver).
4. Create `scripts/seed_from_csv/loaders.py` (dataclasses +
   `_read_csv` + parsers + `load_*`).
5. Create `scripts/seed_from_csv/validation.py` (`validate()`).
6. Create `scripts/seed_from_csv/profiles.py` (`PROFILES`,
   `PROFILE_OWNER_TO_NAME`, `get_profile_id`).
7. Create `scripts/seed_from_csv/modes.py` (`_wipe_profile`,
   `run_reset`, `run_upsert`, `run_diff`).
8. Delete `scripts/seed_from_csv.py` (the old file).
9. Add `tests/test_seed_from_csv_loaders.py` +
   `tests/test_seed_from_csv_validation.py`.
10. Update `tests/conftest.py::_UNIT_FILES` to add the two new test
    paths.
11. Update `data/seed/README.md` to mention the package layout
    (one sentence, no operator-facing change).
12. Run `task test-unit && task test-integration && task test-bdd &&
    task lint`. All must pass with the same counts as pre-refactor
    (the refactor is behaviour-preserving).

No DB migration. No restart required. Rollback = `git revert` the
single commit. The change is local to `scripts/seed_from_csv/`,
`tests/`, and one sentence in `data/seed/README.md`.

## Open Questions

None. The external-consumer list is known (four files in Context),
the per-layer module split is dictated by the existing section
headers, and the contract preservation is verified by running the
existing test suite against the refactor.