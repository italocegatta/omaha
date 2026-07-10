## 1. Diagnose failures

- [x] 1.1 Reproduce failing suite groups and record exact failing tests.
- [x] 1.2 Classify each failure as test drift, spec drift, fixture/glue issue, or runtime regression.

## 2. Repair regressions

- [ ] 2.1 Fix shared fixture or glue issues that affect multiple browser families.
- [x] 2.2 Repair BDD/e2e assertions that encode stale expectations.
- [x] 2.3 Repair import modal and visible navigation regressions in browser flows.

## 3. Verify stability

- [x] 3.1 Re-run affected focused suites until green.
- [ ] 3.2 Re-run `uv run task test` and confirm full-suite green.
- [ ] 3.3 Update spec text or visual baselines only for confirmed contract changes.
