# F39 — Design: margin revision

## Principle

Horizontal space is precious (table columns). Vertical space is for breathing. Restore vertical, keep horizontal.

## Before/After values

### 1. Page wrappers — keep horizontal tight, restore some vertical

**`.patrimonio-page`** (line 820)
```
before (F38):  padding: 1rem 0.75rem;
after (F39):   padding: 0.75rem 0.75rem;
```
Rationale: 0.75rem vertical is midpoint between 0.5rem (pre-F38) and 1rem (F38). Horizontal stays 0.75rem.

**`.rebalance-card`** (line 833)
```
before (F38):  padding: 1rem 0.75rem;
after (F39):   padding: 0.75rem 0.75rem;
```
Same rationale. Unified rule for both pages.

### 2. Table cell padding — restore horizontal breathing in cells

**`.asset-table th, .asset-table td`** (line 1918)
```
before (F38):  padding: 0.35rem 0.3rem;
after (F39):   padding: 0.35rem 0.4rem;
```
Rationale: vertical stays compact (0.35rem). Horizontal restores pre-F38 feel (0.4rem vs 0.35rem) so numbers don't touch column borders.

### 3. Class section — restore vertical spacing

**`.class-section`** (line 1868)
```
before (F38):  padding: 0.35rem 0.25rem 0.4rem;
after (F39):   padding: 0.5rem 0.3rem 0.5rem;
```
Rationale: top/bottom back to 0.5rem (was 0.5rem pre-F38). Horizontal stays tight at 0.3rem (midpoint of 0.25 and pre-F38 0.6).

### 4. Action row margin — restore gap to table

**`.patrimonio-actions`** (line 898)
```
before (F38):  margin-bottom: 0.25rem;
after (F39):   margin-bottom: 0.5rem;
```
Rationale: restore pre-F38 gap between action buttons and content below.

## Visual outcome

- Pages feel less cramped vertically
- Tables still maximize horizontal space
- Consistent treatment for patrimonio and rebalancemaneto
- No layout shift, no column width changes
