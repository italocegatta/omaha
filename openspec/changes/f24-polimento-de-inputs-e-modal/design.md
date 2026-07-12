## Context

F24 is visual polish only. Current add-asset modal uses default 480px shell and modal inputs still feel dense; header profile selector also benefits from clearer left-aligned presentation. Change must stay CSS/template-only and avoid broad regressions in other number inputs or selects.

## Goals / Non-Goals

**Goals:**
- Make add-asset modal easier to scan and fill.
- Improve legibility of modal numeric inputs.
- Keep profile selector readable, left-aligned, and compact.
- Limit CSS effects to this slice's surfaces.

**Non-Goals:**
- No backend, route, validation, or data-model changes.
- No redesign of import modal, rebalance forms, or dashboard tables.
- No global input/select restyling beyond this slice's surfaces.

## Decisions

1. **Use surface-specific CSS modifiers**
   - Apply width/contrast/spinner rules to add-asset modal and profile-switcher selectors only.
   - Avoid changing shared `.modal-panel`, `input`, or `select` rules.

2. **Keep modal width change small**
   - Add-asset modal gets a modest desktop width bump instead of import-modal's wide treatment.
   - Reason: fix cramped feel without making simple create flow look heavy.

3. **Suppress spinner chrome only where the form is modal-based**
   - Number inputs in this modal lose native steppers but keep arrow-key stepping.
   - Reason: reduce visual noise while preserving behavior.

4. **Left-align profile selector text instead of reworking content order**
   - Keep profile order and sentinel logic untouched.
   - Only visual alignment and contrast change.

## Risks / Trade-offs

- **Browser-native select rendering varies** → left-alignment may need browser-specific tuning.
- **Width bump can overflow narrow screens** → keep mobile fallback at 100% width.
- **Selector scope may accidentally hit other forms** → use modal/header-specific classes only.

## Migration Plan

1. Add spec and CSS contract for dashboard form legibility.
2. Apply modal width and input contrast adjustments.
3. Apply profile-switcher alignment tweak in header.
4. Validate visually and tighten selectors if any unrelated inputs change.
