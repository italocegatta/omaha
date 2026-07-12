## 1. Rebalance auto-refresh

- [ ] 1.1 Replace visible rebalance submit button with automatic trigger wiring on input edits.
- [ ] 1.2 Preserve live negative-aporte validation and keep threshold defaults at 1000 / 1.
- [ ] 1.3 Confirm rebalance page still renders plan through existing POST path with current session persistence.

## 2. Import auto-upload

- [ ] 2.1 Trigger import preview automatically from file selection on step 1 and remove manual "Enviar" action.
- [ ] 2.2 Keep step 2 review and commit flow unchanged after successful preview.
- [ ] 2.3 Preserve upload and preview error handling for invalid or failed CSV submissions.

## 3. Layout and styling

- [ ] 3.1 Reflow rebalance parameter bar to three inline inputs and adjust spacing for no submit button.
- [ ] 3.2 Adjust import modal step 1 spacing so auto-upload state reads cleanly without the removed button.

## 4. Tests and verification

- [ ] 4.1 Update unit and integration tests for auto-refresh rebalance behavior.
- [ ] 4.2 Update modal tests and e2e coverage for file-select auto-upload and step-2 advance.
- [ ] 4.3 Run targeted test suite and verify rendered markup matches new spec contracts.
