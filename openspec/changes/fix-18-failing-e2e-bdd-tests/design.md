## Context

18 E2E/BDD tests fail after recent feature commits. Root cause analysis identified 5 groups: 2 code bugs, 3 test assertion drift. The code bugs affect production behavior (stale filters hide rows after PATCH; double currency symbol in import modal). The test drift is straightforward assertion mismatch.

## Goals / Non-Goals

**Goals:**
- Fix the 2 production bugs so the UI behaves correctly
- Update 3 test assertions to match current code behavior
- All 18 tests green after changes

**Non-Goals:**
- Refactoring the filter system architecture
- Changing the `formatBRL`/`formatMoney` API contract
- Adding new test coverage for edge cases discovered during analysis

## Decisions

### D1: Re-run `_initFilterBounds()` after PATCH vs. lazy filter

**Choice**: Re-run `_initFilterBounds()` at the end of `commitEdit` and `commitEditTotal` success handlers.

**Alternatives considered**:
- *Only apply filter when `openFilter[key] === true`*: More complex, requires tracking filter panel state per column. Correct behavior but higher implementation cost for a bugfix.
- *Watch `displayAssets` with Alpine `x-effect`*: Would require restructuring the component to use reactive getters. Overkill for a bugfix.

**Rationale**: Minimal code change (2 lines), directly addresses root cause, no architectural shift. `_initFilterBounds()` is already a pure function that reads from `this.assets` — calling it again after `displayAssets` mutation re-derives correct bounds from the updated data.

### D2: Remove hardcoded `R$ ` from template vs. change `formatBRL`

**Choice**: Remove hardcoded `R$ ` from the 4 `<td>` lines in the template.

**Alternatives considered**:
- *Change `formatBRL` to not include currency symbol*: Would break all other callers that expect `R$` in the output (rebalance table, class summary, etc.).
- *Create a `formatBRLPlain` variant*: Adds API surface for a one-off fix.

**Rationale**: The template added `R$ ` when `formatBRL` didn't include the symbol. Now it does. Removing the hardcoded prefix is the correct fix — `formatBRL` is the single source of truth for currency formatting.

### D3: Single change vs. split into code + test slices

**Choice**: Single change covering all 18 tests.

**Rationale**: The 5 groups share context (same files, same root cause analysis). Splitting adds overhead without reducing risk. The proposal clearly marks which tasks are code fixes vs. test-only.

## Risks / Trade-offs

- **[Risk] `_initFilterBounds()` called twice per PATCH**: Negligible perf impact — iterates ~10 columns, reads from memory. No network or DOM cost.
- **[Risk] Filter bounds reset clears user-set filters**: If user manually set a filter range (e.g., max=50), re-running `_initFilterBounds()` would reset it to the new data bounds. **Mitigation**: Only the `headerRangeFilters` init-time values are overwritten; user-set values live in the same object. Need to check if `_initFilterBounds` clobbers user-set values. If so, guard with `if (!headerRangeFilters[key])` or preserve user overrides.
- **[Risk] Column count may be 16 not 17**: Explore agent said 17 `<th>` elements but manual count shows 16. **Mitigation**: Verify by running the test after fix; adjust `_N_COLS` accordingly.

## Migration Plan

No migration needed. Changes are template JS + test assertions only. No DB, API, or config changes.

1. Apply code fixes (GROUP 2 + GROUP 4)
2. Apply test fixes (GROUP 1 + GROUP 3 + GROUP 5)
3. Run `task test-e2e` and `task test-bdd` to verify all 18 pass
4. Run `task test-unit` to confirm no regressions
