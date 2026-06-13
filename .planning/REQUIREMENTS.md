# Requirements: Omaha

**Defined:** 2026-06-13
**Core Value:** The family opens the app, sees where the portfolio is, trusts the numbers, and closes the tab.

## v1 Requirements

### Audit

- [ ] **AUDT-01**: Auditor can generate a per-page inventory of interactive elements and their default/hover/active/focus/disabled color pairs
- [ ] **AUDT-02**: Auditor can list every CSS custom property that sets text or background color and its computed contrast against the adjacent background

### Palette

- [ ] **PALT-01**: Design tokens in `app.css` define unambiguous foreground/background pairs for every surface
- [ ] **PALT-02**: Each token pair has a documented minimum contrast ratio (body ≥ 4.5:1, UI/large ≥ 3:1)
- [ ] **PALT-03**: `DESIGN.md` reflects the corrected token values and the rationale for each change

### Components

- [ ] **COMP-01**: Primary button text remains readable in default, hover, active, focus, and disabled states
- [ ] **COMP-02**: Secondary/default button text remains readable in default, hover, active, focus, and disabled states
- [ ] **COMP-03**: Text links remain readable in default, hover, active, visited, and focus states
- [ ] **COMP-04**: Form inputs, selects, and textareas remain readable in default, hover, focus, and disabled states
- [ ] **COMP-05**: Error, success, and info feedback blocks remain readable
- [ ] **COMP-06**: Class color swatches and data visualization fills (compare bars, progress bars) remain distinguishable from their surroundings

### Contrast validation

- [ ] **CONV-01**: A documented method confirms every text/background pair meets WCAG 2.1 AA contrast
- [ ] **CONV-02**: Any pair that cannot meet AA has an explicit accessibility exception documented

### Regression protection

- [ ] **REGR-01**: A checklist or automated check exists to catch new color-contrast regressions before merge
- [ ] **REGR-02**: Manual UI review steps document how to verify the fixed states in the running app

## v2 Requirements

### Themes

- **THEM-01**: User can switch between light and dark modes
- **THEM-02**: User can choose an accent color from a small predefined set

## Out of Scope

| Feature | Reason |
|---------|--------|
| Layout or typography redesign | This milestone only fixes color/state visibility; layout and type changes are deferred to a future polish pass |
| New components or pages | No new surfaces are added; scope is existing UI only |
| Animation or motion changes | `prefers-reduced-motion` already honored; motion is not the defect being fixed |
| Browser extension or external contrast tool integration | Manual/browser-devtools validation is sufficient for a single-household app |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDT-01 | Phase 1 | Pending |
| AUDT-02 | Phase 1 | Pending |
| PALT-01 | Phase 2 | Pending |
| PALT-02 | Phase 2 | Pending |
| PALT-03 | Phase 2 | Pending |
| COMP-01 | Phase 3 | Pending |
| COMP-02 | Phase 3 | Pending |
| COMP-03 | Phase 3 | Pending |
| COMP-04 | Phase 3 | Pending |
| COMP-05 | Phase 3 | Pending |
| COMP-06 | Phase 3 | Pending |
| CONV-01 | Phase 4 | Pending |
| CONV-02 | Phase 4 | Pending |
| REGR-01 | Phase 5 | Pending |
| REGR-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-13*
*Last updated: 2026-06-13 after initial definition*
