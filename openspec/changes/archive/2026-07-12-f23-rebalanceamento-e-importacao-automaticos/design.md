## Context

Current rebalance page depends on explicit submit button. Current import modal also depends on explicit "Enviar" in step 1 before preview begins. Both flows are correct, but slower than intended for immediate-action UX.

Scope stays inside existing page/template stack: FastAPI page routes, Jinja templates, Alpine stores, and CSS. No model or database change.

## Goals / Non-Goals

**Goals:**
- Rebalance plan refreshes when operator confirms input values with Enter.
- Import preview starts automatically when operator picks CSV file.
- Keep current server-rendered rebalance response and current import review/commit flow.
- Avoid new endpoints or persistence changes.

**Non-Goals:**
- Auto-commit import without review.
- Change solver math or import parsing rules.
- Add background jobs, websockets, or new API routes.

## Decisions

1. **Keep rebalance on existing POST path.**
   - Use current `/rebalanceamento` POST contract and existing render path.
    - Trigger request from Alpine when operator presses Enter instead of visible submit button.
   - Alternative: add JSON endpoint + partial DOM patch. Rejected: more code, same user outcome.

2. **Auto-upload import preview from file input `change`.**
   - Reuse existing `importModal.uploadFile()` path.
   - Remove manual step-1 trigger button from markup.
   - Tag each selection so stale preview responses cannot overwrite newer file state.
   - Alternative: keep button hidden or soft-disabled. Rejected: still manual friction.

3. **Keep review step in import modal.**
   - Auto-upload only replaces preview start.
   - Step 2 confirmation remains explicit because commit changes DB state.
   - Alternative: auto-commit after preview. Rejected: unsafe for operator control.

4. **Commit rebalance edits on Enter.**
   - Keep local input text while operator types; no request runs per keystroke.
   - Use `requestSubmit()` from Enter so existing client validation and POST path remain intact.

## Risks / Trade-offs

- Solver work while typing → send request only after explicit Enter confirmation.
- Surprise upload when file selected → clear step-1 error/review state and keep explicit review before commit.
- Full page rerender on each rebalance edit may feel heavy → acceptable trade-off for small page and existing server-rendered contract.
- Button removal can break existing tests/selectors → update specs and tests in same slice.

## Migration Plan

1. Update specs for rebalance-page and import-modal.
2. Change templates/Alpine handlers to auto-trigger instead of manual buttons.
3. Adjust CSS for new parameter-bar width and removed step-1 button space.
4. Update unit/integration/e2e tests to assert Enter submit and auto-upload.
5. Rollback path: restore manual button handlers and previous selectors if auto-trigger causes regressions.

## Open Questions

- Nenhuma.
