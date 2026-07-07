## 1. PRD §4.10 rewrite (memorial)

- [x] 1.1 Read current PRD §4.10 to inventory existing prescriptive rules
- [x] 1.2 Rewrite §4.10 as a descriptive memorial of the SI maximal register
  (status quo: register chosen, sidebar not reintroduced, light/dark
  toggle not introduced, hue 60 warmth maintained, scope = 3 slices)
- [x] 1.3 Add cross-reference from §4.10 to DESIGN.md as canonical source
  for token values
- [x] 1.4 Verify §4.10 does not prescribe specific OKLCH / hex values
  (token values live in DESIGN.md)

## 2. PRD §5.3 marker (gate resolution)

- [x] 2.1 Mark D02 as resolved in §5.3 (date 2026-07-07 + register chosen)
- [x] 2.2 List F08-F10 + F12 as unblocked (gate D02 cleared)
- [x] 2.3 List F11 + F13 as effectively blocked (F11 = register ≠ A;
  F13 = owner did not request toggle)

## 3. DESIGN.md updates

- [x] 3.1 §Color strategy rewrite — document emerald accent
  (oklch 0.68 0.20 152), fern-leaning positive (oklch 0.79 0.19 145),
  coral negative (oklch 0.69 0.20 25), amber warning, class-3
  magenta-red (hue 350), surface warm-neutral dark (hue 60, chroma
  ~0.012)
- [x] 3.2 §Typography rewrite — Red Hat Display 700+ for portfolio
  header; Inter variable body with feature-settings `tnum, cv01,
  ss01, ss02`; Google Fonts URL pattern
- [x] 3.3 §Component inventory rewrite — enumerate 5 states (idle/
  hover/focus/disabled/error) for inputs, buttons, tabs, table rows
- [x] 3.4 §Component inventory table pattern upgrade — sticky
  headers, hover row bg lift, total row emphasis, action column
  visible only on hover, numeric tnum + right-alignment
- [x] 3.5 §Component inventory extras — section dividers hairline,
  `::selection` accent, form autofill override, eyebrow labels
  uppercase `.label-xs`, compare bar pattern (target/atual/
  over-target), rebalance warnings border-left 4px, form R$ prefix
- [x] 3.6 §Iconography rewrite — "None required" → "Material
  Symbols Outlined, scoped" with catalog (add class, add asset,
  import, sign out, warning triangle, close, expand chevron)
- [x] 3.7 §Anti-patterns update — add state feedback vocabulary
  table; add note "no sidebar reintroduce — top nav F02 preserved"
- [x] 3.8 §Migration path — note that F08-F10 + F12 will materialize
  D02 decisions in code

## 4. Roadmap updates

- [x] 4.1 Mark F11 (sidebar reintroduce) as `Blocked` (effectively,
  register ≠ A)
- [x] 4.2 Mark F13 (light/dark toggle) as `Blocked` (owner did not
  request toggle)
- [x] 4.3 Update F08 + F09 + F10 + F12 + R05 + T06 Notes to
  reference D02 archived + the 7 decisions applied
- [x] 4.4 Update D02 Progress log (Proposed → Applying → Applied →
  Archived)

## 5. Spec gate + verify

- [x] 5.1 Run `openspec validate d02-design-register-decision --json`
  → expect `valid: true`
- [x] 5.2 Run `openspec list --specs` → confirm new spec
  `design-register-decision` appears with `requirements: 2` (no
  regressions)
- [x] 5.3 Run `task lint` → expect green (no code changes, but verify
  PRD + DESIGN.md don't break prek checks)
- [x] 5.4 No `task test-*` execution required — D02 is doc-only,
  zero runtime impact
- [x] 5.5 No `refresh-for-test` skill invocation — D02 doesn't touch
  runtime, server state unchanged
