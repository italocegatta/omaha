## Context

The project has four orthogonal test partitions:

| Partition | Lives in | Marker | Triggered by |
|---|---|---|---|
| Unit | `tests/test_*.py` (allow-listed) | `unit` | pre-commit pytest + pre-push pytest |
| Integration | `tests/test_*.py` (allow-listed) | `integration` | pre-push pytest |
| E2E (legacy) | `tests/e2e/*.py` | none | `task test-e2e` (Playwright) |
| BDD | `tests/bdd/**/*.feature` | `bdd` | `task test-bdd` (Playwright + dev server) |

BDD scenarios live under `tests/bdd/` and require a live dev server on
`http://127.0.0.1:8766`. The pre-push hook runs on the developer's box
without orchestrating a server, so BDD must be excluded from the pre-push
pytest entry. This carve-out was applied in commit `19db56d` and is now
documented in `openspec/specs/prek-hooks/spec.md` via this change.

## Goals / Non-Goals

**Goals:**
- Lock the `--ignore=tests/bdd` exclusion in `prek.toml` so future
  contributors don't accidentally re-add BDD to the pre-push gate.
- Document the canonical execution path (`task test-bdd`) in the spec.

**Non-Goals:**
- Change the BDD marker logic in `tests/conftest.py` (already correct).
- Run BDD scenarios in pre-push (architecturally infeasible without
  orchestrating a dev server in the hook).
- Add a new task for flake stabilisation (out of scope; tracked
  separately if the 1-in-5 flake becomes blocking).

## Decisions

**Decision 1: BDD is excluded from pre-push pytest.**
- *Rationale:* BDD scenarios need a dev server. The pre-push hook does
  not orchestrate services, so adding `--ignore=tests/bdd` is the only
  way to keep the hook fast and deterministic.
- *Alternatives considered:*
  - **Spin up the dev server inside the pre-push hook.** Rejected: hooks
    are expected to be fast and side-effect-free. Adding process
    orchestration makes them slow and platform-dependent.
  - **Run BDD only in CI, never locally.** Rejected: developers lose
    signal. `task test-bdd` remains available locally.

**Decision 2: The carve-out is documented in `prek-hooks` spec, not a new capability.**
- *Rationale:* BDD partitioning is a *configuration* concern of the
  hook, not a new capability. The existing `prek-hooks` spec already
  covers the pytest gate; adding requirements there is the natural home.
- *Alternatives considered:*
  - **Create a `test-partitioning` capability spec.** Rejected: would
    duplicate the marker logic that already lives in `tests/conftest.py`
    and `AGENTS.md`.

**Decision 3: No re-classification of flaky scenarios as `@pytest.mark.skip`.**
- *Rationale:* The 1-in-5 flake from
  `test_per_class_sum_off_100_accepted_target_pct[Italo]` does not block
  pushes (BDD excluded). Marking it `skip` would hide a real signal
  when the flake is correlated with a regression. The flake is observed
  and tracked; if the rate increases, a follow-up change will investigate.

## Risks / Trade-offs

- **Risk:** A regression in BDD scenarios ships to `main` because
  pre-push doesn't gate them.
  *Mitigation:* `task test-bdd` is wired into CI and gates `main`
  before merge. The developer must run it locally before merging a
  branch with BDD-touching changes.

- **Risk:** A contributor re-adds `tests/bdd` to the pre-push pytest
  hook entry, unaware of the carve-out.
  *Mitigation:* The `prek.toml` comment plus the spec requirement
  "Pre-push pytest hook entry documents the dev-server carve-out" make
  the intent discoverable.

- **Trade-off:** Pre-push is faster but gives less signal than running
  the full suite locally. Accepted because `task test-bdd` and CI
  provide the missing signal.

## Migration Plan

- **Deployment:** none required — the change is already live in `prek.toml`.
- **Rollback:** revert commit `19db56d` and the spec delta in this change.

## Open Questions

- Should the 1-in-5 flake from
  `test_per_class_sum_off_100_accepted_target_pct[Italo]` be tracked
  as a follow-up change with a stabilisation plan? *Current answer: no,
  unless the flake rate climbs above 1-in-10.*
