## Why

Pre-push currently runs mutating hooks (`ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`) that silently rewrite code after the developer has already committed. This means `git push` can fail, modify files, and require a new commit — breaking the mental model that "push sends what I already approved." Moving code-correction hooks to pre-commit ensures the commit that lands is the commit that gets pushed. Pre-push becomes a pure validation gate.

## What Changes

- **Pre-commit gains mutating hooks**: `ruff-format` (format), `ruff --fix` (lint auto-fix), `trailing-whitespace`, `end-of-file-fixer` join the existing file-sanity and unit-test hooks. Commit auto-corrects code, developer reviews, then pushes.
- **Pre-push becomes validate-only**: `ruff` (without `--fix`), `uv-lock`, `commitizen-branch`, `pytest-integration-parallel`. If pre-push fails, it means pre-commit didn't run or something slipped — not that push is trying to fix things.
- **Spec update**: `prek-hooks` spec reflects the new stage semantics — pre-commit = mutate + gate, pre-push = validate only.

## Capabilities

### Modified Capabilities
- `prek-hooks`: Stage-split requirement changes — pre-commit becomes the mutating stage (ruff format+fix, whitespace, EOF), pre-push becomes validate-only (ruff check without fix, integration tests, commitizen, uv-lock).

## Impact

- `prek.toml` — hook assignments change between stages
- `openspec/specs/prek-hooks/spec.md` — requirement rewrite for stage semantics
- No production code, no tests, no seed data touched
