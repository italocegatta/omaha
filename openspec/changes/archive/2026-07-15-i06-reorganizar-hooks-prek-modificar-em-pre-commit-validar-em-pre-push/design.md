## Context

Current `prek.toml` has a broken stage assignment: mutating hooks (`ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`) live in pre-push. This means `git push` silently rewrites files, requiring a new commit and re-push cycle. The developer's mental model breaks — "I committed, I push, it should just go."

The fix: move all code-correction hooks to pre-commit (where they amend the commit in-place) and leave pre-push as a pure validation gate. This is a config-only change — no production code, no tests, no seed data.

## Goals / Non-Goals

**Goals:**
- Pre-commit corrects code: `ruff-format`, `ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`
- Pre-commit retains existing hooks: file-sanity checks + `pytest-unit`
- Pre-push validates only: `ruff` (no `--fix`), `uv-lock`, `commitizen-branch`, `pytest-integration-parallel`
- Push never modifies code — failure means pre-commit didn't catch it

**Non-Goals:**
- Changing ruff rules or fixing existing lint errors (separate slice)
- Modifying `continue-on-error` flags (separate slice)
- Touching `commit-msg` stage (unchanged)
- Changing `pyright` hook placement (manual stage, unchanged)

## Decisions

### D1: ruff-format before ruff --fix in pre-commit

`ruff-format` (formatting) runs at priority 1, `ruff --fix` (lint auto-fix) at priority 2. Format-first ensures lint fixes don't fight formatting. This mirrors the current pre-push ordering.

### D2: Pre-push ruff uses same config as pre-commit ruff

The pre-push `ruff` hook (no `--fix`) validates against the same `ruff.toml` / `pyproject.toml [tool.ruff]` config. If pre-commit's `ruff --fix` left unfixed issues, pre-push catches them. No separate config needed.

### D3: No priority changes for existing pre-commit hooks

Existing pre-commit hooks (file-sanity, pytest-unit) keep their current priorities. New mutating hooks get priority 1-3 (before pytest-unit at priority 4) so code is corrected before tests run.

### D4: uv-lock stays in pre-push

`uv-lock` is technically mutating (regenerates `uv.lock`), but it only fires when `pyproject.toml` changed. It's a lockfile sync check, not code correction. Keeping it in pre-push avoids slowing pre-commit with dependency resolution. Acceptable trade-off: if `uv.lock` is stale, push fixes it (rare, and the lockfile is auto-generated, not hand-written code).

## Risks / Trade-offs

- **Risk: pre-commit becomes slower** → Mitigation: ruff format+fix are fast (~100ms each). Added latency is negligible vs. existing pytest-unit gate.
- **Risk: Developer bypasses pre-commit with `--no-verify`** → Mitigation: pre-push ruff (no --fix) still catches unfixed issues. Defense in depth.
- **Risk: `continue-on-error` masks failures** → Mitigation: existing `continue-on-error` flags remain until lint debt is cleared (separate slice). Same behavior as before reorganization.

## Migration Plan

1. Edit `prek.toml` — move hooks between stages, add ruff-format to pre-commit, add ruff (no --fix) to pre-push
2. Update `openspec/specs/prek-hooks/spec.md` — rewrite stage-split requirement
3. Run `prek run --all-files` to validate config
4. Done. No rollback needed — config is additive, worst case is hooks run in wrong stage
