## 1. Diagnose failures

- [x] 1.1 Reproduce failing suite groups and record exact failing tests.
- [x] 1.2 Classify each failure as test drift, spec drift, fixture/glue issue, or runtime regression.

## 2. Repair regressions

- [ ] 2.1 Fix shared fixture or glue issues that affect multiple families.
- [x] 2.2 Repair BDD/e2e/visual assertions that encode stale expectations.
- [ ] 2.3 Repair real CSV flow, seed-from-CSV, and rebalance schema/glue failures.

## 3. Verify stability

- [x] 3.1 Re-run affected focused suites until green.
- [ ] 3.2 Re-run `uv run task test` and confirm full-suite green.
- [ ] 3.3 Update spec text or visual baselines only for confirmed contract changes.
