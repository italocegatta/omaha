## 1. Classe / Desvio — conditional rendering

- [x] 1.1 In `_patrimonio_class_section.html` lines 139-145, add an em-dash `<span>` with `x-show` that checks `Math.abs(classDeviationPctClass) < 0.0001` (when no `classDeltaMessage` is present)
- [x] 1.2 Wrap the existing metric-stack `<span>` (lines 141-144) with inverted `x-show` so it hides when deviation is ~0
- [x] 1.3 Verify the Sobra/Falta pill branch (`x-show="classDeltaMessage"`) still takes precedence over both new spans

## 2. Carteira / Desvio — conditional rendering

- [x] 2.1 In `_patrimonio_class_section.html` lines 186-191, add an em-dash `<span>` with `x-show` that checks `Math.abs(classPortfolioDeviationPct) < 0.0001`
- [x] 2.2 Wrap the existing metric-stack `<span>` (lines 187-190) with inverted `x-show` so it hides when deviation is ~0

## 3. Verification

- [ ] 3.1 Run `task serve` and visually verify: class with zero deviation shows "—" in both Desvio columns
- [ ] 3.2 Verify: class with non-zero deviation still shows green/red formatted value
- [ ] 3.3 Verify: Sobra/Falta pill still appears when per-asset targets exceed 100%
- [x] 3.4 Run `task test-unit` to confirm no regressions
