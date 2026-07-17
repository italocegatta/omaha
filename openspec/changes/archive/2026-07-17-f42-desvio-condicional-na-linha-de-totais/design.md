## Context

The class totals row in the patrimônio page renders two deviation columns: "Classe / Desvio" and "Carteira / Desvio". Currently, both columns always render a formatted value — even when deviation is exactly 0%. This produces "0%" with neutral (`metric-neutral`) styling, which adds visual noise when the class is perfectly on target.

The `signClass` function (line 728 of `_patrimonio_add_asset_modal.html`) already returns `'metric-neutral'` for values where `Math.abs(Number(value)) < 0.0001`. The `formatDeviationPp` function formats zero as `0%`. The change is to intercept the zero case at the template level and render "—" instead.

## Goals / Non-Goals

**Goals:**
- Deviation cells in the totals row render "—" when deviation is zero
- Non-zero deviation retains existing green (positive) / red (negative) formatting
- Change is template-only — no backend, no new CSS classes

**Non-Goals:**
- Changing deviation display logic for individual asset rows (only totals row)
- Modifying the `signClass` or `formatDeviationPp` JavaScript functions
- Touching the Sobra/Falta pill (`classDeltaMessage`) — that already hides when on-target

## Decisions

### Decision: Conditional rendering via Alpine.js `x-show` + em-dash span

**Approach**: Add a new `<span>` with `x-show` that checks if deviation is ~0, showing "—". The existing metric-stack span gets an inverted `x-show` to hide when ~0.

**Rationale**:
- Minimal template change — two `<span>` additions per deviation cell
- Reuses existing `signClass` threshold (`Math.abs(value) < 0.0001`) via a computed check
- No JS function changes needed — the zero check is expressed inline in Alpine

**Alternatives considered**:
- Modifying `formatDeviationPp` to return "—" for zero: rejected because it changes the function contract used by asset rows too
- Adding a new `isZeroDeviation` helper: unnecessary — inline `Math.abs(value) < 0.0001` is clear and matches existing pattern

### Decision: Keep `signClass` binding on the `<td>` unchanged

The `<td>` keeps its `:class="signClass(...)"` binding. When deviation is zero, `signClass` returns `metric-neutral`, which is the correct styling for the em-dash fallback. No CSS changes needed.

## Risks / Trade-offs

- **Risk**: Alpine expression duplication (inline zero-check in two places per cell) → **Mitigation**: The check is trivial (`Math.abs(v) < 0.0001`); duplication is acceptable for two cells
- **Risk**: Sobra/Falta pill already handles zero-deviation differently (hides via `x-show="classDeltaMessage"`) → **Mitigation**: The Classe/Desvio cell has two branches — the pill branch and the metric-stack branch. The em-dash only applies to the metric-stack branch when pill is absent AND deviation is zero
