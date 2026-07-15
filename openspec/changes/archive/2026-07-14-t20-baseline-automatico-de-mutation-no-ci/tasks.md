## 1. Add mutation-ci taskipy task

- [x] 1.1 Add `mutation-ci` task to `[tool.taskipy.tasks]` in `pyproject.toml`: `mutation-ci = { cmd = "uv run task mutation && uv run task mutation-baseline", help = "Run mutation testing and capture baseline (CI single-command)" }`

## 2. Add mutation-baseline job to CI workflow

- [x] 2.1 Add `mutation-baseline` job to `.github/workflows/ci.yml` with `on: push: branches: [main]` trigger (not `pull_request`)
- [x] 2.2 Job steps: checkout, install uv (3.12), cache uv, install deps, delete `mutants/`, run `task mutation-ci`
- [x] 2.3 Add git commit-back step: `git config user.name/github-actions`, `git add .mutmut-baseline`, conditional commit + push (skip if baseline unchanged)
- [x] 2.4 Set `permissions: contents: write` on the job for push access
- [x] 2.5 Add `[skip ci]` to commit message to prevent infinite loop

## 3. Update spec

- [x] 3.1 Sync the delta spec from `openspec/changes/t20-baseline-automatico-de-mutation-no-ci/specs/rebalance-mutation-testing/spec.md` to `openspec/specs/rebalance-mutation-testing/spec.md` using `openspec-sync-specs`

## 4. Verify and update roadmap

- [x] 4.1 Run `openspec verify --change t20-baseline-automatico-de-mutation-no-ci` and resolve any issues
- [x] 4.2 Update roadmap: move T20 from `Ready` to `Spec Proposed` with progress log entry
