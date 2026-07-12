## 1. Rebalance Enter submit

- [x] 1.1 Replace visible rebalance submit button with Enter-triggered submit wiring on input edits.
- [x] 1.2 Preserve live negative-aporte validation and keep threshold defaults at 1000 / 1.
- [x] 1.3 Confirm rebalance page still renders plan through existing POST path with current session persistence.

## 2. Import auto-upload

- [x] 2.1 Trigger import preview automatically from file selection on step 1 and remove manual "Enviar" action.
- [x] 2.2 Keep step 2 review and commit flow unchanged after successful preview.
- [x] 2.3 Preserve upload and preview error handling for invalid or failed CSV submissions.

## 3. Layout and styling

- [x] 3.1 Reflow rebalance parameter bar to three inline inputs and adjust spacing for no submit button.
- [x] 3.2 Adjust import modal step 1 spacing so auto-upload state reads cleanly without the removed button.

## 4. Tests and verification

- [x] 4.1 Update unit and integration tests for Enter-submitted rebalance behavior.
- [x] 4.2 Update modal tests and e2e coverage for file-select auto-upload and step-2 advance.
- [x] 4.3 Run targeted test suite and verify rendered markup matches new spec contracts.
