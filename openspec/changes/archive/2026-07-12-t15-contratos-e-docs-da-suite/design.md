## Context

Change is doc-only. Runtime behavior already lives in `pyproject.toml`, `tests/conftest.py`, and BDD harness files; current drift is in human-facing docs and performance snapshot text. The goal is to make reader-facing contracts match actual task names, marker behavior, serial BDD execution, and suite lane boundaries.

## Goals / Non-Goals

**Goals:**
- Keep `README.md` aligned with actual task entrypoints and full-suite wording.
- Keep `tests/bdd/README.md` aligned with current workflow names and BDD replay/serial semantics.
- Refresh `tests/PERFORMANCE.md` into dated baseline that uses task wrappers and current lane framing.
- Preserve low-risk, doc-only scope.

**Non-Goals:**
- No app/runtime code changes.
- No test behavior changes.
- No marker logic changes in `tests/conftest.py` or task definitions in `pyproject.toml` unless a text-only clarification is needed.

## Decisions

**D1 — Source-of-truth mapping is explicit, not inferred.**
Docs will name taskipy entrypoints directly (`uv run task ...`) and describe suites using current lane behavior instead of stale shorthand. This avoids ambiguity when task names or lane boundaries change later.

**D2 — BDD docs follow current canonical workflow names.**
`tests/bdd/README.md` will use the workflow identifiers that match current contract names and will highlight `task test-bdd-single` as replay/debug helper. Alternative was leaving old names for backwards familiarity; rejected because it preserves drift.

**D3 — Performance baseline is a snapshot, not a contract.**
`tests/PERFORMANCE.md` will keep timestamp/environment/branch context and treat counts/timings as dated evidence. Alternative was to remove numbers entirely; rejected because the file's value is regression triage, not prose only.

**D4 — Keep comments stable in `tests/conftest.py`.**
If any comment is touched, it will only clarify marker allow-list / `UnknownTestPath` ownership. No logic churn. Alternative was to move docs out of the file; rejected because the file already owns marker contract commentary.

## Risks / Trade-offs

- Baseline numbers age quickly → keep date/branch header and treat file as snapshot.
- Docs can drift again when tasks change → anchor wording to canonical task names and lane labels.
- BDD terminology can lag workflow renames → use current identifiers and avoid aliases in docs.

## Migration Plan

- Update docs in place.
- Run doc/spec validation against proposed deltas.
- No rollback plan needed beyond normal git revert because no runtime state changes.

## Open Questions

- None blocking.
