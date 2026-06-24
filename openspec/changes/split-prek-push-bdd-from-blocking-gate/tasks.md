## 1. Verify prek.toml carve-out is in place

- [ ] 1.1 Confirm `prek.toml` pre-push pytest entry contains `--ignore=tests/bdd` and the explanatory comment

## 2. Spec alignment

- [ ] 2.1 Archive this change via `openspec archive split-prek-push-bdd-from-blocking-gate` after merge to `main`
- [ ] 2.2 Confirm `openspec/specs/prek-hooks/spec.md` reflects the three new requirements (BDD exclusion, dev-server carve-out, flakiness non-blocking)
