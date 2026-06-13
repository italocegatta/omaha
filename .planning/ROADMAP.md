# Roadmap: Omaha — v1.2 bug de visualização

## Overview

This milestone audits every interactive state and color token in the app, replaces the broken palette with contrast-safe tokens, fixes every component and data-viz surface, validates WCAG 2.1 AA conformance, and adds regression protection so the same defects do not return.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Audit** - Inventory interactive states and compute contrast ratios
- [ ] **Phase 2: Palette** - Define corrected color tokens and update DESIGN.md
- [ ] **Phase 3: Components** - Fix buttons, links, inputs, feedback, and data visualization states
- [ ] **Phase 4: Validation** - Verify WCAG AA contrast and document exceptions
- [ ] **Phase 5: Regression Protection** - Add pre-merge checks and manual review steps

## Phase Details

### Phase 1: Audit

**Goal**: Every interactive state and color token is inventoried with computed contrast ratios so the visibility defects are known before fixes are applied.
**Depends on**: Nothing (first phase)
**Requirements**: AUDT-01, AUDT-02
**Success Criteria** (what must be TRUE):

  1. Auditor can open a generated inventory that lists every page and interactive element with its default, hover, active, focus, and disabled text/background color pairs.
  2. Auditor can see every CSS custom property that sets text or background color together with its computed contrast against the adjacent background.
  3. The inventory flags every pair that falls below WCAG 2.1 AA thresholds (body < 4.5:1, UI/large < 3:1).

**Plans**: TBD
Plans:
**Wave 1**

- [ ] 01-02: Inventory CSS color tokens and compute adjacent contrasts

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-01: Inventory interactive elements and state color pairs

### Phase 2: Palette

**Goal**: A contrast-safe color token system replaces the broken palette and is fully documented in DESIGN.md.
**Depends on**: Phase 1
**Requirements**: PALT-01, PALT-02, PALT-03
**Success Criteria** (what must be TRUE):

  1. `app.css` defines unambiguous foreground/background custom properties for every surface (base, raised, primary, secondary, danger, success, info, disabled, etc.).
  2. Each token pair has a documented minimum contrast ratio that meets WCAG 2.1 AA (body ≥ 4.5:1, UI/large ≥ 3:1).
  3. `DESIGN.md` reflects the corrected token values and includes the rationale for each change.

**Plans**: TBD
**UI hint**: yes

Plans:

- [ ] 02-01: Define corrected color tokens in `app.css`
- [ ] 02-02: Update `DESIGN.md` with token values and rationale

### Phase 3: Components

**Goal**: All interactive components and data visualization surfaces are readable in every state.
**Depends on**: Phase 2
**Requirements**: COMP-01, COMP-02, COMP-03, COMP-04, COMP-05, COMP-06
**Success Criteria** (what must be TRUE):

  1. Primary button text remains readable in default, hover, active, focus, and disabled states.
  2. Secondary/default button text remains readable in default, hover, active, focus, and disabled states.
  3. Text links remain readable in default, hover, active, visited, and focus states.
  4. Form inputs, selects, and textareas remain readable in default, hover, focus, and disabled states.
  5. Error, success, and info feedback blocks remain readable.
  6. Class color swatches and data visualization fills (compare bars, progress bars) remain distinguishable from their surroundings.

**Plans**: TBD
**UI hint**: yes

Plans:

- [ ] 03-01: Fix button and link states
- [ ] 03-02: Fix input, select, textarea, and feedback block states
- [ ] 03-03: Fix class swatches and data visualization fills

### Phase 4: Validation

**Goal**: WCAG 2.1 AA conformance is verified and any unavoidable exceptions are documented.
**Depends on**: Phase 3
**Requirements**: CONV-01, CONV-02
**Success Criteria** (what must be TRUE):

  1. A documented method confirms every text/background pair meets WCAG 2.1 AA contrast.
  2. Any pair that cannot meet AA has an explicit accessibility exception documented with the reason and affected states.

**Plans**: TBD

Plans:

- [ ] 04-01: Run contrast validation across all fixed pairs
- [ ] 04-02: Document any accepted AA exceptions

### Phase 5: Regression Protection

**Goal**: Future color/contrast regressions are caught before merge and manual review steps are documented.
**Depends on**: Phase 4
**Requirements**: REGR-01, REGR-02
**Success Criteria** (what must be TRUE):

  1. A checklist or automated check exists and runs before merge to catch new color-contrast regressions.
  2. Manual UI review steps document how to verify the fixed states in the running app.

**Plans**: TBD

Plans:

- [ ] 05-01: Add automated or checklist-based regression guard
- [ ] 05-02: Write manual UI review steps for fixed states

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Audit | TBD | Not started | - |
| 2. Palette | TBD | Not started | - |
| 3. Components | TBD | Not started | - |
| 4. Validation | TBD | Not started | - |
| 5. Regression Protection | TBD | Not started | - |
