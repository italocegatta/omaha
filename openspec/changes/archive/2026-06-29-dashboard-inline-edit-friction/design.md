## Context

The dashboard renders three inline editors for target-% values:
the class header `Alvo NN%` pill and the per-asset
`alvo % classe` / `alvo % total` cells. Today each editor hides
its display value behind an `<input type="number">` toggled by an
`x-show` Alpine directive; the user must click once to mount the
input and a second time to focus it before they can type. Empty
commits return 422 from the server because `_parse_pct("")` is
treated as invalid. The Chrome / Firefox native number-input
spinner draws `▲`/`▼` glyphs that read as scrollbar chrome on a
flat dashboard pill.

Three small client-side changes (`dashboard.html` + `app.css`)
fix all three without touching the server contract — `_parse_pct`
already accepts `"0"` and stores zero, so the empty-to-zero
coercion can live entirely in the client.

## Goals / Non-Goals

**Goals:**

- Make every inline edit reachable in a single click (mouse /
  touch) with no follow-up click to focus the input.
- Make empty commit equal zero without an error round-trip.
- Strip the native number-input spinner from the inline editors
  so the visual matches the surrounding pill (a flat field,
  not a numeric stepper).

**Non-Goals:**

- Server-side changes — `_parse_pct` and the PATCH routes are
  untouched.
- Changing the re-entrance guard, the
  `Escape`-cancels / `Enter`-or-blur-commits semantics, or any
  other behavior of the inline editors.
- Adding save / cancel buttons (the design explicitly forbids
  them — see `dashboard-inline-editing/spec.md`).
- Touching any `<input type="number">` outside the dashboard's
  three inline editors (asset create modal, class create modal,
  import modal — those keep the spinner because they are
  modal forms, not inline pill editors, and rely on the native
  stepper).

## Decisions

### D1 — Auto-focus via `this.$nextTick` in `startEdit*`

**Decision:** add `x-ref` on each inline `<input>`; in the
matching `startEditClassPct` / `startEdit` /
`startEditTotal` handler, call
`this.$nextTick(() => { this.$refs.X.focus();
this.$refs.X.select(); })` immediately after the `x-show`
toggle (`editingXxx = true`).

**Why `$nextTick` instead of `x-init`.**

`x-show` toggles `display: none`; it does **not** mount /
unmount the DOM. An `x-init` on the input fires once on the
first page render, when the input is still hidden — useless for
later activations. `$nextTick` defers the focus call to the
microtask immediately after Alpine has flipped `display` back
to `block`, so the freshly visible input is the focus target.

**Why `x-ref` instead of `document.querySelector`.**

Each `classSection` Alpine instance owns its own scope. Using
`document.querySelector('.class-inline-edit-input')` would
return the *first* class section's input on a multi-class
dashboard and not be safe under async render. `x-ref` resolves
to the input inside the current component scope; safe for
multiple parallel class sections, multiple parallel rows, and
multiple parallel total / class editor cells in the same row.

**Why `select()` after `focus()`.**

`<input type="number">` does NOT auto-select on focus the way
`<input type="text">` does. Calling `.select()` highlights the
whole value so the user's first keystroke replaces it — the
"click → type" mental model.

**Alternatives considered:**

- `x-effect="editingXxx && $nextTick(() => $el.focus())"` —
  rejected because `$el` resolves to the bound element (the
  `<span>` in the class header pill, or the `<button>` in the
  asset table cell), not the `<input>`. Would need an additional
  `x-effect` inside the input subtree, splitting the directive
  across two elements for no benefit.
- `contenteditable` `<span>` — rejected because numeric input,
  percent / decimal validation, and the existing `min`/`max`
  HTML hints all come for free with `<input type="number">`.
- A `keyup` handler that toggles `editingXxx` and an
  autofocus-on-render via Alpine `$el.focus()` — same issue as
  `x-init` (fires once on first mount, not on each show).

### D2 — Empty-to-zero coercion in the commit functions

**Decision:** in `commitEditClassPct`, `commitEdit`, and
`commitEditTotal`, replace an empty / whitespace-only value
with `"0"` before building the PATCH body.

```text
var pct = (self.editXxxValue ?? '').trim();
pct = pct === '' ? '0' : pct;
```

The trim → empty → `0` coercion lives in exactly three places
(the three commits). The server `target_pct` schema already
accepts `"0"`; `_parse_pct("0")` returns `Decimal("0")`. No
backend change.

**Why client-side coercion, not server-side "empty = 0".**

- Keeps `_parse_pct` semantics pure (invalid → `None`). A
  special "empty string means zero" branch would couple the
  PATCH body contract to a string coercion that's only useful
  for the dashboard's empty-input flow.
- Makes the dashboard's "blank input is zero" UX visible in
  client code where reviewers can grep for it.
- Avoids touching the assets / classes routes, which are
  governed by other specs and other tests.

**Alternatives considered:**

- Server-side "empty string → zero" in `_parse_pct` —
  rejected per above (couples semantics).
- An `x-effect` that writes a default `"0"` back into
  `editXxxValue` when the user clears it — rejected because
  it would visibly overwrite the user's empty field with `0`
  on every keystroke (interrupting the "clear to retype"
  flow).
- A separate "set to 0" button alongside the input — rejected
  because the design forbids any save / cancel button
  (`dashboard-inline-editing/spec.md` "Editor não renderiza
  botão salvar nem cancelar").

### D3 — Spinner suppression via CSS, not `type="text"`

**Decision:** keep `<input type="number">`; add CSS rules that
hide the WebKit / Blink spinner buttons and the Firefox
spinner.

**Why `type="number"` instead of `type="text"`.**

`<input type="number">` carries the keyboard hint, the mobile
numeric keypad layout, the `min` / `max` validation hint, and
the `step` value used by `↑` / `↓` arrows. The number-spinners
are the only unwanted piece. Stripping them via CSS keeps
every other affordance.

**Why CSS only — no JS.**

The spinner is rendered by the UA stylesheet on
`::-webkit-inner-spin-button` and `::-webkit-outer-spin-button`
(plus `-moz-appearance: textfield` for Firefox). Removing the
markup would require swapping `type="number"` for `type="text"`
and re-implementing numeric parsing and `min` / `max`. CSS
suppresses the chrome with no behavior change.

**Rule block (appended, not replacing existing input rules):**

```css
.asset-inline-edit-input,
.class-inline-edit-input {
  -moz-appearance: textfield;
}
.asset-inline-edit-input::-webkit-outer-spin-button,
.asset-inline-edit-input::-webkit-inner-spin-button,
.class-inline-edit-input::-webkit-outer-spin-button,
.class-inline-edit-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
```

**Alternatives considered:**

- Swap to `type="text"` + `inputmode="numeric"` —
  rejected because it drops the `min` / `max` HTML hint and
  the `step` value that `↑` / `↓` keyboard arrows consult.
- Delete just the WebKit rules and accept Firefox spinners —
  rejected because the Firefox rule is one line and zero
  risk.

## Risks / Trade-offs

- **`$nextTick` timing on slow renders** — if Alpine is busy
  (large reactive tree on a slow machine), the input may
  become visible after the `$nextTick` microtask has already
  run, and `focus()` would silently no-op. → Mitigation: the
  re-entrance pattern (`startEditClassPct` is only called from
  a click handler, which always runs in the browser's main
  loop) means Alpine is never mid-tick when `startEdit*` is
  invoked; in practice the microtask completes after the
  `x-show` flip.
- **Auto-focus steals focus from another widget** — e.g. user
  has the import modal open and clicks an `Alvo` pill in the
  background by mistake. → Mitigation: the modal
  (`data-testid="add-asset-modal-overlay"` /
  `data-testid="import-modal-overlay"`) covers the dashboard
  with a backdrop, so a click on the pill from the background
  is impossible while a modal is open. No interaction risk.
- **Coercing empty to zero masks user error** — a user who
  clears the field by accident and clicks away will save zero
  silently, no confirmation. → Mitigation: the field already
  validates out-of-range inputs with a 422 + inline error
  span; zero is *in* range, so this is intentional
  simplification in line with "empty means none" intent. The
  portfolio sticky alert card surfaces the resulting
  deviation, so the operator sees "Falta 100%" immediately
  if they really did mean to clear everything.
- **Spinner suppression might break `↑` / `↓` keyboard
  steppers** — it doesn't: those increment by `step` on the
  number value directly, independent of the UA spinner
  chrome.
- **Tab order** — call site moves focus inside an input on
  click; if the user was mid-Tab-traversal of the asset
  table, the click interrupts the sequence. → Mitigation:
  this is the standard browser behavior for any click that
  opens an editor; users who want pure keyboard flow can
  `Enter` on the pill (button) — the `startEdit*` path then
  handles focus the same way. Pressing Escape still exits.

## Migration Plan

Not applicable. Frontend-only patch in
`src/omaha/templates/dashboard.html` and
`src/omaha/static/app.css`. No schema, no migration, no
backward-compat flag. Existing PATCH routes handle `"0"`
already.

Rollback is `git revert` of the implementation commit.

## Open Questions

None. The three changes are independent and additive; the
spec captures the user-visible behavior; the design captures
the client-only enforcement; the existing `_parse_pct` already
accepts `"0"`.
