# F39 — Tasks

## T1. Restore `.patrimonio-page` vertical padding ✓

File: `src/omaha/static/app.css`
Line 820: change `padding: 1rem 0.75rem;` → `padding: 0.75rem 0.75rem;`

## T2. Restore `.rebalance-card` vertical padding ✓

File: `src/omaha/static/app.css`
Line 833: change `padding: 1rem 0.75rem;` → `padding: 0.75rem 0.75rem;`

## T3. Restore `.asset-table th/td` horizontal cell padding ✓

File: `src/omaha/static/app.css`
Line 1918: change `padding: 0.35rem 0.3rem;` → `padding: 0.35rem 0.4rem;`

## T4. Restore `.class-section` vertical padding ✓

File: `src/omaha/static/app.css`
Line 1868: change `padding: 0.35rem 0.25rem 0.4rem;` → `padding: 0.5rem 0.3rem 0.5rem;`

## T5. Restore `.patrimonio-actions` margin-bottom ✓

File: `src/omaha/static/app.css`
Line 898: change `margin-bottom: 0.25rem;` → `margin-bottom: 0.5rem;`

## Verification

- Visual check: both pages should feel less cramped vertically
- No horizontal expansion: table columns unchanged
- Same rules on patrimonio and rebalancemaneto pages
