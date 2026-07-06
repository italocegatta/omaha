## Context

`src/omaha/templates/patrimonio.html` is 2186 lines after F02 (rename from
`dashboard.html`) absorbed the F05 surface expansion, the F06 family-mode
branches (`view == "family"`), and the F07 sentinel-aware empty-state
hint. Reading or editing any one section currently requires the whole
file in context, which slows every follow-up slice (R02 already
flagged it as a candidate in its post-archive reality check; F06 noted
the read-only branch made the template harder to navigate).

The existing precedent for partialization lives in `rebalance.html`,
which already `{% include %}`s `_rebalance_empty.html`,
`_rebalance_placeholder.html`, and `_rebalance_plan.html`. The same
underscore-prefix convention and the same plain `{% include %}` pattern
(without `with context` arguments — partials read directly from the
rendering context) is the canonical way to split a template in this
codebase.

Stakeholders: the next R-slice / F-slice that touches patrimonio
(Future R04 deltas, eventual F03/Rentabilidade related cross-links,
possible chart re-render in a polish pass). None of those slices
should have to scroll past 1500 lines of unrelated markup to land a
change.

## Goals / Non-Goals

**Goals:**

- Reduce `patrimonio.html` to a thin shell (~30 lines of `{% include %}`
  directives + page header + closing tag).
- Split the existing sections into 6 partials, one section each, named
  with the `_patrimonio_*` prefix to match the `_rebalance_*` siblings.
- Preserve every `data-testid`, class, Alpine `x-data`/`x-show`/
  `x-text` expression, and `{% if %}`/`{% for %}` control structure
  byte-for-byte.
- Keep the file count reasonable (6 partials + 1 shell — not 20).
- Land the refactor in a single commit so `git blame` cleanly attributes
  every line to either the original section or the partial move.

**Non-Goals:**

- No design change, no CSS change, no token change.
- No Alpine behaviour change — every component (`x-data="{}"`,
  `@click`, `x-init`, `x-effect`, `x-show`, etc.) is moved verbatim
  with its partial.
- No new tests. The existing test suite (`tests/test_patrimonio_*`,
  `tests/test_class_section_*`, BDD `class_crud.feature`, e2e
  selector inventory) continues to assert against the same rendered
  DOM; refactor must remain byte-equivalent at the rendered HTML level.
- No spec delta. Every requirement across the 39 existing specs
  continues to bind to the same `data-testid` at the same parent.
- No `{% extends %}` blocks or template inheritance — partials are
  plain `{% include %}` snippets that share the rendering context.
- No macro extraction — Jinja macros would add an abstraction layer
  the project does not currently use (`rebalance` partials are not
  macros either).
- No partial arguments (`{% with foo=bar %}`). Each partial reads
  exactly the variables `patrimonio.html` reads today; the rendering
  context flows unchanged.

## Decisions

### D-R04.1 — Section granularity matches visual sections, not lines.

The 6 partials map to the 6 existing top-level `<section>` /
`<article>` blocks in the template. This matches the reading pattern
("edit the portfolio header" → open `_patrimonio_portfolio_header.html`),
keeps file sizes balanced (the largest partial — class section — is
~320 lines, the smallest — portfolio header — is ~30), and avoids the
"20 micro-partials" anti-pattern where each helper gets its own file.

### D-R04.2 — Partial naming: `_patrimonio_<section>.html`.

Siblings the existing `_rebalance_<variant>.html` pattern. The
underscore prefix signals "include-only, not rendered directly". The
`patrimonio_` middle prevents collision with the rebalance partials in
Jinja's loader (`FileSystemLoader` does not dedupe, but the namespacing
keeps `include` paths readable: `{% include "_patrimonio_actions.html" %}`).

### D-R04.3 — Plain `{% include %}`, no `{% with %}`, no macros.

Each partial reads the same context variables the section reads today
(`class_data`, `c`, `a`, `view`, `profile`, `portfolio_header`, etc.).
Passing explicit arguments would (a) duplicate the context surface in
every `{% include %}` call, (b) require deciding which context vars
each partial needs (an under-specified contract), and (c) diverge from
the `_rebalance_*` precedent, which also uses plain `{% include %}`.

### D-R04.4 — Modal lives in its own partial, not inline in the shell.

`add-asset-modal` is ~600 lines and conditionally rendered
(`{% if show_add_asset_modal %}`). Keeping it inline in the shell
would re-inflate the shell. Putting it in
`_patrimonio_add_asset_modal.html` keeps both files small. The `{% if %}`
guard moves with the partial; the shell no longer needs to know the
modal exists.

### D-R04.5 — Empty states grouped into one partial.

The two empty-state sections (`empty-assets` inline + onboarding)
share visual vocabulary and class names. Grouping them in
`_patrimonio_empty_states.html` keeps related markup together and
keeps the partial count at 6 (not 7). If a future slice needs to
edit only one, the file is small enough (~40 lines) that splitting
later is a 5-minute follow-up.

### D-R04.6 — No template comments preserved in the shell.

The 30-line shell has only `{% include %}` directives and the
surrounding `<main>` element. Any section-level narrative comments
("Section: portfolio header — see spec X") move with their partial,
so each partial stands alone when opened in isolation.

### D-R04.7 — Refactor lands as a single `apply` step, not multiple.

Each partial depends on the shell to declare it; the shell depends on
all 6 partials to render. Splitting into multiple commits would leave
intermediate states with broken renders. One commit: `extract 6
partials, rewrite shell, render unchanged`. Pre-apply and post-apply
HTML diff (`GET /patrimonio` rendered output) is the verification step.

## Risks / Trade-offs

- **Risk:** Jinja's `FileSystemLoader` cache invalidation could trip
  during dev if partial paths change mid-render. → **Mitigation:** the
  dev server (`task serve`) reloads on every request via the FastAPI
  debug flag; no caching layer is involved. uvicorn's reload picks up
  partial additions on the next request.

- **Risk:** An Alpine `x-data` component that lives in one section
  needs to mutate DOM in another section (cross-section binding).
  → **Mitigation:** none of the existing `classSection`, `portfolio`,
  or `addAssetModal` Alpine components touch DOM outside their own
  block. All bindings are scoped via `x-data` element boundaries.
  Verified by inspecting the current `x-data` declarations: each
  is a section-level root, not a template-level root.

- **Risk:** `{% include %}` without `with context` (which is the
  default — included partials DO see the parent's context) might be
  misread by a future reader as "partial is isolated". →
  **Mitigation:** D-R04.3 records this in design.md; the `_rebalance_*`
  partials set the precedent. Future contributors who try to pass
  explicit args will find no precedent to copy.

- **Risk:** A partial grows over time and needs to be split further.
  → **Mitigation:** the largest partial (`_patrimonio_class_section.html`,
  ~320 lines) still fits in a single screen. Future growth can be
  handled by extracting sub-sections (header, table, edit modal) into
  `_patrimonio_class_section_<sub>.html` partials in a follow-up R-slice.
  Out of scope for R04.

- **Risk:** `git blame` loses history if the refactor is a single
  `git mv` + edit. → **Mitigation:** use a single commit, but
  preserve `git log --follow` semantics — Jinja partials are tracked
  individually by git, so `git log --follow _patrimonio_portfolio_header.html`
  will point at the R04 commit (and prior history through the rename
  detector if the file ever gets split further upstream). The refactor
  is mechanical and the diff is reviewable in one sitting.

- **Trade-off:** more files in `src/omaha/templates/` (6 new files).
  Acceptable because each file is small, focused, and discoverable by
  name. The `_rebalance_*` precedent already validated this pattern.

## Migration Plan

Single deployment step. No data migration, no schema change, no env
change. The refactor is source-only and the rendered DOM is
byte-equivalent (verifiable via `curl /patrimonio | diff -` before and
after).

**Rollback:** `git revert <R04 commit>`. The refactor touches only
`src/omaha/templates/patrimonio.html` and the 6 new partials under
`src/omaha/templates/`. One revert restores the pre-refactor state.

**Verification (apply gate):**

1. `task test-unit` — green (no unit-test surface change; partials are
   templates, not Python).
2. `task test-integration` — green (no integration-test surface
   change; the rendered DOM is equivalent).
3. `task test-bdd` — green for the patrimonio scenarios
   (`class_crud.feature`, `profile_sharing.feature`); the 4
   pre-existing T05 failures remain unchanged (out of scope).
4. `task test-e2e` — green for `test_patrimonio_*` and
   `test_class_section_*`; the 5 pre-existing chromium stalls remain
   unchanged (out of scope).
5. `task lint` — green (`ruff format` may reformat one or two lines
   if a partial lands with non-canonical indentation; trivially fixable
   via `ruff format --fix`).
6. `openspec validate r04-partialize-patrimonio-template` —
   `valid: true`.
7. **Render diff:** capture `GET /patrimonio` rendered HTML before and
   after the apply (with the same seed + auth cookie + querystring);
   the two outputs must be byte-equivalent except for whitespace
   inside Jinja control tags (which Jinja strips uniformly).

## Open Questions

None. The slice is bounded, the precedent exists, and the
verification gate (rendered-DOM byte-equivalence) is mechanical. Any
future growth that requires re-splitting a partial is a follow-up
R-slice, not a blocker for R04.
