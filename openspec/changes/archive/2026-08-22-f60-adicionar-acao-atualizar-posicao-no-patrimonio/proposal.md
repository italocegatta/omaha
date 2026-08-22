## Why

F59 now exposes a profile-scoped asynchronous MyProfit job and a compatible
preview payload, but Patrimônio has no operator-facing control to start it.
F60 closes that browser boundary without replacing manual review or turning a
position refresh into an implicit portfolio commit. Owner visual validation
found four remediation requirements: action order, icon/state parity, reset of
success styling after review cancellation, and transient notification feedback.

## What Changes

- Add a visible `Atualizar posição` action immediately left of `Importar CSV` in
  the real-profile action strip, using the existing Material Symbols Outlined
  system's `sync` ligature.
- Give the new action the same typography, control dimensions, alignment,
  focus treatment, and idle/hover/focus/disabled/error state language as its
  sibling actions; success styling is transient and ends when review is
  cancelled.
- Start `POST /api/myprofit/sync` without navigation, keep the action disabled
  while polling `GET /api/myprofit/sync/{job_id}`, and render explicit idle,
  loading, success, error, and disabled states.
- On `succeeded`, hydrate the existing `$store.importModal` with F59's preview
  payload and open its existing classification/review window; do not create an
  alternative modal or call the commit endpoint.
- Replace the three sync page-inline strings (`Pronto para atualizar posição.`,
  `Atualizando posição...`, and `Atualização concluída. Revise posições antes de
  confirmar`) with bottom-corner notification cards. Cards use an exact
  8-second auto-dismiss timer, pause while hovered or focused, expose a manual
  close button, and preserve safe error copy.
- When the F59 review handoff is cancelled through `Cancelar` (and the existing
  close path), clear the sync success presentation and notification so the
  action returns to ordinary idle styling with no persistent green/highlighted
  treatment.
- On start, polling, failed, or expired job errors, keep the user on the page,
  show safe PT-BR feedback, and never open the review modal.
- Keep `Atualizar posição` visible but native-disabled/read-only in Família;
  preserve all existing Família mutation guards and manual import behavior.
- Add focused server-rendering, browser-state, endpoint-wiring, and existing
  modal handoff coverage; allow Apply to produce a browser-rendered visual
  artifact, then require the mandatory `refresh-for-test` receipt and explicit
  owner visual approval after Apply and before Review.

## Capabilities

### New Capabilities

- `patrimonio-position-sync-action`: Dashboard action, client state machine,
  F59 start/poll/preview handoff, notification feedback, visual parity, and
  no-navigation/no-auto-commit behavior.

### Modified Capabilities

- `import-modal`: The existing review modal accepts a successful F59 preview
  payload as a second entry path, while its manual assignment and explicit
  commit contract remain unchanged.
- `cross-profile-sharing`: Família renders the new synchronization action as
  visible but disabled/read-only, while rejecting synchronization before any
  connector side effect.
- `iconography-tokens`: Add the semantically correct `sync` ligature to the
  project icon catalog for this synchronization action.

## Impact

- Templates: `src/omaha/templates/_patrimonio_actions.html` and
  `src/omaha/templates/patrimonio.html`; directly required Alpine store code in
  `_patrimonio_add_asset_modal.html` if the existing preview hydration needs a
  shared method.
- Styling: `src/omaha/static/app.css` for action parity, transient state,
  bottom-corner notification cards, responsive layout, and disabled/read-only
  presentation.
- Server context and existing F59 route boundary: `src/omaha/routes/pages.py`
  and `src/omaha/routes/imports.py`; no F59 backend or connector behavior
  changes.
- Tests/specs: focused template/route and Playwright/browser-state coverage,
  explicit test-marker classification where required, plus this change's delta
  specs.
- No asset/position mutation, seed, migration, production DB operation,
  connector modification, alternative modal, or auto-commit.
