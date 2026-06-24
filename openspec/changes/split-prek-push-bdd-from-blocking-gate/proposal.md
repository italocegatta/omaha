## Why

The pre-push `pytest` gate in `prek.toml` currently runs the **entire**
test discovery (`uv run pytest` minus `tests/e2e` and
`tests/audit_integration`). That worked when the suite was a flat
collection of integration tests, but the BDD split (`feat(tests): add
pytest-bdd suite + disable legacy e2e`, `7a8c1f7`) introduced 33+ BDD
scenarios under `tests/bdd/` that **require a live dev server** on
`http://127.0.0.1:8766`. Pre-push hooks run on the developer's box
without orchestrating the dev server, so the BDD scenarios block the
push with `TimeoutError: Page.goto: Timeout 30000ms exceeded` and
`commitizen-branch` fails on `origin/HEAD..HEAD` because the push is
rejected before any new commits land.

A working push of `bdd-refactor-login` + `refactor/decision-5-import-via-ui`
(2026-06-24) had to ship `--ignore=tests/bdd` (commit `19db56d`)
without a spec describing **why** or **under what contract** BDD is
excluded. This change formalises the carve-out.

## What Changes

- **`prek.toml`:** add `--ignore=tests/bdd` to the pre-push pytest
  hook entry, with a comment explaining the dev-server dependency.
  *(Already shipped in `19db56d`. This change documents the rationale.)*
- **`openspec/specs/prek-hooks/spec.md`:** add a new requirement
  describing the BDD exclusion and the path that BDD scenarios take
  (CI job + `task test-bdd`).
- **`tests/conftest.py` and `tests/bdd/conftest.py`:** **no change**.
  The marker partition (`bdd` marker + `_INTEGRATION_PREFIXES`
  allow-list) already gates BDD correctly; the only missing piece is
  the prek hook entry.
- **`task test-bdd`:** **no change**. The task already runs the BDD
  suite with the dev server live and is the canonical execution path.

## Capabilities

### New Capabilities

*(none)*

### Modified Capabilities

- `prek-hooks`: add a new requirement for **BDD exclusion from pre-push
  pytest gate** and refine the existing "Pytest full gate on pre-push"
  requirement to acknowledge that "full" excludes BDD, `e2e`, and
  `audit_integration` by design (orchestrated elsewhere).

## Impact

- **Affected code:**
  - `prek.toml` (already updated in `19db56d`; this change locks the
    behavior in a spec).
  - `openspec/specs/prek-hooks/spec.md` (new requirement, no breaking
    scenario edits).
- **Affected developers:** anyone pushing from a local clone. Pushes
  that previously hung on BDD server timeouts now complete in ~50s.
- **Affected CI:** unchanged. The CI pipeline already runs BDD
  separately via `task test-bdd`.
- **Migration:** none. The carve-out is already live; this change is
  the spec for that decision.