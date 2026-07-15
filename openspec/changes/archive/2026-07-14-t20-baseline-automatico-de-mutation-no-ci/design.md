## Context

T03 introduced mutation testing for `rebalance/solver.py` + `validation.py`. T19 expanded scope to 8 files (~3867 mutants, 94.5% killed, ~15 min wall-clock with `num_workers=3`). Current workflow: developer runs `task mutation` locally, then `task mutation-baseline` to capture `.mutmut-baseline`. This file is committed manually.

Problem: if a PR merges code that drops mutation score (e.g., weakens tests), nobody detects it until someone manually runs mutation testing. The baseline goes stale silently.

Current CI (`ci.yml`) runs lint → test-unit/integration → coverage on every push/PR. No mutation job exists. The `mutation` task takes 10-18 min — too expensive for PR checks, but acceptable for a post-merge-only job.

## Goals / Non-Goals

**Goals:**
- Automate `task mutation` + `task mutation-baseline` as a CI job on push to `main`
- Commit the updated `.mutmut-baseline` back to `main` automatically
- Keep the job isolated from PR checks (cost control)
- Add a `mutation-ci` taskipy task that chains the two steps

**Non-Goals:**
- Promoting mutation score to a blocking gate (no `fail_under` threshold)
- Running mutation testing on PRs (cost too high)
- Adding new tests or changing mutation scope (T19 already did that)
- Caching `mutants/` across CI runs (mutmut3 cache is fragile; clean run each time)

## Decisions

### D-T20.1 — Post-merge only, not on PR

**Choice:** Job triggers on `push` to `main` only, not on `pull_request`.

**Rationale:** `task mutation` takes 10-18 min with 3 workers. Running on every PR would add significant CI cost and slow feedback loops. Mutation testing is a regression detector, not a per-commit gate. The baseline file is a signal for the next developer, not a blocker for the current PR.

**Alternatives considered:**
- *PR check with `continue-on-error: true`:* Wastes CI minutes without blocking anything. Rejected.
- *Nightly cron:* Delays detection by up to 24h. Post-merge gives immediate feedback. Rejected.
- *Manual trigger only:* Defeats the "automatic" goal. Rejected.

### D-T20.2 — Commit-back via git push (not PR)

**Choice:** Job runs `task mutation` → `task mutation-baseline` → `git add .mutmut-baseline` → `git commit` → `git push` directly to `main`.

**Rationale:** The baseline file is a single-line change that doesn't need PR review. Creating a PR per merge adds noise. Direct push to `main` is acceptable for this automated, non-code artifact. The job uses `contents: write` permission.

**Alternatives considered:**
- *Create PR with baseline update:* Adds PR noise for a 7-line file. Rejected.
- *Upload as artifact only:* No persistent signal; requires manual download. Rejected.
- *Skip commit, just log:* Loses the diff-detection capability. Rejected.

### D-T20.3 — Fresh run each time (no mutants/ cache)

**Choice:** Delete `mutants/` before each CI run. No cache across runs.

**Rationale:** mutmut3's cache is source-hash-dependent. If source files change between merges, stale cache entries cause incorrect results. A fresh run takes ~15 min but guarantees correctness. GitHub Actions cache adds complexity for marginal gain.

**Alternatives considered:**
- *Cache `mutants/` with `actions/cache`:* Fragile — cache invalidation depends on source file hashes that mutmut3 tracks internally. Risk of stale baseline. Rejected.
- *Incremental run (skip cache delete):* Works if only test files changed. Breaks silently if source files changed. Rejected.

### D-T20.4 — `mutation-ci` taskipy task

**Choice:** Add `mutation-ci = { cmd = "uv run task mutation && uv run task mutation-baseline", help = "..." }` to `[tool.taskipy.tasks]`.

**Rationale:** CI job calls a single task. Keeps `ci.yml` clean. Developers can also use it locally. The `&&` chain fails fast if mutation run errors.

### D-T20.5 — No `fail_under` threshold

**Choice:** Job always succeeds regardless of killed share. Baseline is committed even if score drops.

**Rationale:** Mutation score is a signal, not a gate (per T03 decision D-T03.2). Promoting to a gate is a separate slice. If the job blocked on low score, a single weak test could block all merges.

## Risks / Trade-offs

- **[Risk] CI job takes 15-20 min** → Mitigation: runs post-merge only, not blocking PR feedback. Acceptable cost for regression detection.

- **[Risk] Direct push to `main` fails if branch protection requires PR** → Mitigation: GitHub Actions token (`GITHUB_TOKEN`) bypasses branch protection by default for Actions-triggered pushes. If branch protection is configured to require PRs, the job would need a PAT or the commit-back strategy would need to change. Verify on first run.

- **[Risk] `git push` race condition on concurrent merges** → Mitigation: two rapid merges could cause the second job's push to fail. The job should pull before pushing, or use `--force-with-lease`. Low probability in a solo-developer repo.

- **[Risk] `mutants/` directory is large (~100MB)** → Mitigation: `git clean` or `rm -rf mutants/` before run. The directory is already in `.gitignore`.

- **[Risk] Mutations in CI environment behave differently than local** → Mitigation: mutmut3 runs pytest under `mutants/` cwd. CI has same Python 3.12 + uv setup. DB is not needed (mutation tests are unit-only per `pytest_add_cli_args_test_selection`). Low risk.
