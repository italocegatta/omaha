# F39 — Delta Spec: margin revision

## Changed spec: `page-margins` (F38)

### Section: Page wrapper padding

**SHALL** use `0.75rem 0.75rem` padding on `.patrimonio-page` and `.rebalance-card`.
(Horizontal 0.75rem maximizes table width; vertical 0.75rem restores breathing room.)

### Section: Table cell padding

**SHALL** use `0.35rem 0.4rem` padding on `.asset-table th` and `.asset-table td`.
(Vertical stays compact; horizontal prevents numbers from touching column borders.)

### Section: Class section padding

**SHALL** use `0.5rem 0.3rem 0.5rem` padding on `.class-section`.
(Top/bottom 0.5rem restores inter-section breathing; horizontal 0.3rem stays tight.)

### Section: Action row spacing

**SHALL** use `margin-bottom: 0.5rem` on `.patrimonio-actions`.
(Restores gap between action buttons and content below.)

## Unchanged

- Horizontal page margins (0.75rem) — no change
- Mobile breakpoints — no change
- All other selectors — no change
