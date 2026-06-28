# Design: rebalance-page

## Context

`rebalance-route` (archived 2026-06-27) shipped:

* `POST /api/rebalance` (JSON, `routes/rebalance.py`) — thin shell
  around `run_rebalance()`.
* `rebalance.glue.run_rebalance(db, profile, contribution, *,
  solver=stub_solver)` — orchestrates builders + adapter + solver
  + maps native shape to wire format.
* `rebalance.solver_stub.stub_solver` — loads frozen fixture
  `tests/fixtures/rebalance_stub_fixture.json` (5 assets, 2 classes,
  `applied_policy = "stub-fixture-v1"`).
* `rebalance.schemas.RebalancePlanResponse` — wire format with 9
  asset_plan fields + 4 category_plan + 6 metric keys + warnings +
  applied_policy.

The dashboard sidebar has 3 buttons (`dashboard.html:20-45`):
Importar CSV / + Novo ativo / + Nova classe. The user has
confirmed (2026-06-27 session):

1. The 4th button area in the sidebar becomes a **form** with input
   `Aporte (R$)` + button "Rebalancear" — form submits to `/rebalance`
   (POST) and renders the plan on the same URL (server-side render,
   no JSON fetch, no client-side state machine).
2. The form lives in the sidebar on **every authenticated page**
   (dashboard + `/rebalance`), extracted to a Jinja include.
3. The plan page is a single new URL `/rebalance` — no separate
   results page. Header nav: `Dashboard` + `Plano de aporte`
   (the latter is an anchor / state indicator on the same URL).
4. **Contract extension**: `contribution` accepts any finite float
   (including 0 = rebalance-only, and negative = withdrawal —
   gated client-side for v1).

Single-user household; concurrency not a concern.

## Goals / Non-Goals

**Goals:**

* Wire the sidebar form to `run_rebalance()` server-side, render
  the resulting plan on `/rebalance` via Jinja2.
* Render the full v1 plan shape defined in
  `openspec/specs/rebalance-route/spec.md` (asset_plan × 9 fields,
  category_plan × 4, metrics × 6, warnings list, applied_policy).
* Extract the sidebar to `_sidebar.html` so dashboard + rebalance
  share the form/trigger.
* Empty state when the active profile has zero `AssetClass` rows:
  copy PT-BR + CTA back to `/` (dashboard's "+ Nova classe" button).
* Client-side gate: aporte `< 0` blocked with explanatory copy
  ("saques serão suportados em versão futura"); `0` and positive
  flow through to the server.
* Maintain the contract extension: `RebalanceRequest.contribution`
  becomes `float` (no `gt=0`), with a finite-float validator so
  `NaN` / `inf` still 422.

**Non-Goals:**

* CVXPY solver (Phase 4 / `rebalance-engine`) — out of scope.
* Persistence of rebalance runs (decision locked from
  `rebalance-route/design.md` Decision 6 — stateless).
* Mobile responsiveness below 1024px (decision locked).
* Order execution (no broker integration).
* Charting the per-asset drift (Phase 5; not v1).
* Withdrawal policy in the solver (Phase 4's call; the contract
  permits it, the page doesn't expose it).

## Decisions

### Decision 1: Page flow is server-side render, no client-side fetch

The form in the sidebar submits to `/rebalance` (POST). The
`POST /rebalance` handler validates the aporte, calls
`run_rebalance()` synchronously, and renders `rebalance.html`
with the plan in the Jinja context. No JSON wire trip, no
Alpine state machine for the plan itself.

* **(A) Server-side render via form POST.** *Adopted.* Page is
  declarative and bookmarkable. Sort + stub banner + input mask
  are the only Alpine pieces. Failure modes (validation, solver
  error) render as inline Jinja blocks — no client error handling
  for plan display. Trade-off: each recompute is a full page
  render. CVXPY on 50 assets solves in <50ms; render is sub-100ms;
  acceptable for an interactive workflow (operator types,
  clicks, sees result).
* (B) Fetch `POST /api/rebalance` from Alpine, mutate a store.
  Smaller payload, smoother UX — but adds a client state
  machine (idle / computing / ready / error) the codebase
  doesn't have anywhere else. More JS, less Jinja, and the
  page can't be bookmarked with a fixed aporte value.
* (C) Two pages (`/rebalance` for form + `/rebalance/plan` for
  results). Server-side render with PRG pattern. Considered
  and rejected: the user clarified "não precisa de uma página
  só para o formulário"; the sidebar form is the form.

### Decision 2: Sidebar lives in a Jinja include

The 4th button + form block is moved from `dashboard.html:12-46`
into `templates/_sidebar.html` as a Jinja include. Both
`dashboard.html` and `rebalance.html` render the include.

* **(A) Jinja include macro.** *Adopted.* Single source of
  truth. The "Rebalancear" form is the same markup everywhere;
  the active state is a Jinja conditional (`{% if request.url.path
  == '/rebalance' %}`). Other pages (login, import_review,
  audit_report, healthz) do NOT include the sidebar — they have
  their own auth gates or no auth at all.
* (B) Move sidebar to `base.html`. Affects login, healthz, etc.
  Forces conditional rendering everywhere. More invasive.
* (C) Hardcode the sidebar in each page (3 copies). Drift risk.

### Decision 3: Sidebar form posts to `/rebalance` (HTML form, not JSON)

```html
<form method="post" action="/rebalance" data-testid="rebalance-form"
      x-data="rebalanceForm()" @submit="validate($event)">
  <label for="contribution">Aporte (R$)</label>
  <input type="number" step="any" name="contribution" id="contribution"
         x-model="contribution" :class="{'has-error': error}"
         required inputmode="decimal" />
  <p class="rebalance-form-error" x-show="error" x-text="error"></p>
  <button type="submit" :disabled="computing">
    <span x-show="!computing">Rebalancear</span>
    <span x-show="computing">Calculando...</span>
  </button>
</form>
```

The `validate()` Alpine helper short-circuits `submit` when
`contribution < 0` (sets `error = "Saques serão suportados em
versão futura. Por enquanto, deixe o aporte em zero ou
positivo."` and `event.preventDefault()`). Positive and zero
flow through to the server.

* **(A) Client-side gate on `< 0` only.** *Adopted.* The contract
  accepts negative (for Phase 4 / future withdrawal use); the
  page is more conservative than the contract. The server still
  validates the float is finite (no `NaN`/`inf`) — Pydantic does
  this by default for `float`.
* (B) Reject negative on the server with 422 + inline error.
  Symmetric to client gate, but adds a round-trip for a UX
  decision. Page is faster.
* (C) Allow negative end-to-end. Solver stub ignores the value
  (overlays contribution on fixture), but the displayed plan
  shows misleading "buy R$ -500" for the asset_plan rows. Bad
  UX. Defer to Phase 4 when the real solver interprets negative
  as withdrawal.

### Decision 4: Plan layout — 6 metric cards (3×2) + 8-col table + 4-col summary

```
┌── rebalance-card ──────────────────────────────────┐
│ [← Dashboard]  Plano de aporte            (nav)   │
├────────────────────────────────────────────────────┤
│ Aporte: R$ 5.000,00      [Refazer]                 │ ← form (sticky?)
├────────────────────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐                  │
│ │Contrib.│ │Comprar │ │ Vender │                  │
│ │ R$ ... │ │ R$ ... │ │ R$ ... │                  │
│ ├────────┤ ├────────┤ ├────────┤                  │
│ │Caixa r.│ │Desvio  │ │Desvio  │                  │
│ │ R$ ... │ │ atual %│ │proj. % │                  │
│ └────────┘ └────────┘ └────────┘                  │
├────────────────────────────────────────────────────┤
│ Política aplicada: contribution-only                │
│ <details>: Mostrando fixture stub (stub-fixture-v1) │
│ ⚠ Avisos (N)                                       │
│   • EMPTY_CLASS_NONZERO_TARGET — mensagem PT-BR    │
├────────────────────────────────────────────────────┤
│ ┌── Asset plan (8 cols) ────────────────────────┐ │
│ │ Ativo | Classe | Atual | Alvo | C|V|Proj|Ação │ │
│ └──────────────────────────────────────────────┘ │
│ ┌── Resumo por classe (4 cols) ─────────────────┐ │
│ │ Classe | Atual | Projetado | Δ                │ │
│ └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

* **(A) 3×2 grid for metrics.** *Adopted.* Matches the
  `.portfolio-header` aesthetic from the dashboard (3 cols,
  3 stats: Investido / Valor atual / Ganho). One extra row,
  same visual register.
* (B) Hero (Contribuição) large + 5 secondary stats.
  More striking, more risk of looking like a generic
  AI-templated dashboard.
* (C) 6 cols single row. Tighter horizontally but each
  card too narrow at 1024-1440px viewports.

The asset plan table renders **8 visible cols** (`asset_key`
stays as `data-asset-key` on the `<tr>` for tests / JS hooks).
Sort pattern mirrors the dashboard (`sortBy(key)` +
`sortIndicator(key)` + `displayRows` rebuilt on click).
Default order = solver order (category_order, then asset_order).

Action badge: square (border-radius 4px), bg-color sutil, ink
forte. `Comprar` → `--positive-ink` on `--positive` background
(opacity 0.12). `Vender` → `--negative-ink` on `--negative`
background (opacity 0.12). `Manter` → `--ink` on `--bg-hover`.
Matches the existing aesthetic (`.empty-state`, `.portfolio-stat`
both use radius 4px).

### Decision 5: Stub banner via `<details>`, conditional on `applied_policy`

When `applied_policy === "stub-fixture-v1"`, render a
collapsed `<details>` element above the warnings panel:

```html
<details class="rebalance-stub-banner" data-testid="stub-banner">
  <summary>Mostrando fixture stub (solver CVXPY chegará em
           <code>rebalance-engine</code>)</summary>
  <p>Os números abaixo são determinísticos e frozen no
     <code>tests/fixtures/rebalance_stub_fixture.json</code>.
     Quando o solver real entrar, este banner some sozinho.</p>
</details>
```

* **(A) `<details>` collapsed, conditional on `applied_policy`.**
  *Adopted.* Surgical, server-driven, no Alpine needed. When
  CVXPY lands, the policy changes and the banner disappears
  without code change.
* (B) Always show banner with version indicator. Polls v1
  with non-actionable noise.
* (C) Hide entirely. Dev loses the "is this real?" signal
  during Phase 3b.

### Decision 6: Empty state when profile has zero classes

`GET /rebalance` checks `profile.asset_classes`. If empty,
renders the same template but the main area shows:

```
┌── rebalance-empty-state ──────────────────┐
│ Nenhuma classe cadastrada                 │
│ Crie ao menos uma classe antes de        │
│ rebalancear.                              │
│ [← Voltar ao dashboard]                   │
└───────────────────────────────────────────┘
```

The sidebar form is **present but inert**: the input + button
render with `disabled` attribute. Operator must go to dashboard,
use the "+ Nova classe" button, save a class, return to
`/rebalance`. Empty state lives in the main area only — the
sidebar's 4th button stays visible so the user knows where
they are.

* **(A) Inline empty state + inert form.** *Adopted.* User
  always knows the layout; CTA is one click away via the
  header nav (`Dashboard`).
* (B) Redirect to `/`. Hides the page completely; loses
  context that this is the rebalance feature.
* (C) Render the empty plan (asset_plan = [], warning
  EMPTY_PROFILE). Misleading — looks like a working plan
  that says "nothing to do".

### Decision 7: Alpine scope — local x-data, not a global store

`rebalance.html` uses `x-data="rebalancePage({...plan...})"`
on the main container. `rebalanceForm()` is a separate
component on the sidebar form. No `$store.rebalancePage` /
`$store.rebalanceForm` global stores.

* **(A) Local x-data components.** *Adopted.* Self-contained
  page; sidebar form scope is independent of the plan display
  scope (form may live in another page that doesn't render
  the plan). No cross-scope coordination needed.
* (B) Global `$store.rebalancePage`. Matches `importModal` /
  `addAssetModal` / `newClassModal` — but those exist because
  a sidebar button (one x-data scope) opens a modal in a
  different scope. The rebalance form's "open" is a navigation,
  not a modal — so the cross-scope bridging isn't needed.

### Decision 8: Sort cycle = asc → desc → asc (no reset)

Mirror the dashboard's `sortBy` exactly:

```js
sortBy: function (key) {
  if (this.sortKey === key) {
    this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
  } else {
    this.sortKey = key;
    this.sortDir = 'asc';
  }
  this.displayRows = this.rows.slice().sort(sortFn(this.sortKey, this.sortDir));
}
```

* **(A) 3-state cycle.** *Adopted.* Matches dashboard.
  Trade-off: no way to "reset to solver order" without a
  separate "Limpar ordenação" button. Defer.
* (B) 4-state cycle (asc → desc → asc → reset). Adds UI
  surface for marginal value.

### Decision 9: Contract extension — `contribution: float` (no `gt=0`)

`src/omaha/rebalance/schemas.py`:

```python
class RebalanceRequest(BaseModel):
    contribution: float = Field(
        description="Aporte em R$ a ser aplicado no rebalanceamento. "
                    "Aceita 0 (rebalance sem dinheiro novo) e valores "
                    "negativos (saque; suporte do solver chega em "
                    "rebalance-engine).",
    )
```

* **(A) `float` with finite-value validation; no `gt=0`.**
  *Adopted.* Pydantic `float` rejects `NaN`/`inf` by default
  via the JSON parser; `contribution = 0` is a valid rebalance
  plan (no new money, just reallocation); negative is allowed
  in the wire for future withdrawal use. The page gates
  `< 0` client-side.
* (B) `Field(ge=0)` — permit zero, reject negative. Cleaner
  numeric range, but blocks future withdrawal without
  another schema change.
* (C) Keep `gt=0`. Status quo. Page rejects 0 client-side.
  Forces user to type R$ 0,01 minimum. Bad UX for
  rebalance-only scenarios.

The spec delta in `openspec/specs/rebalance-route/spec.md`
swaps the "Request validates contribution greater than zero"
requirement for "Request validates contribution as a finite
float". All scenarios referencing 422-on-zero / 422-on-negative
are removed; new scenario asserts 422 on `NaN` (server-side
defensive).

## Risks / Trade-offs

* **Stateless recompute on every POST.** Page latency is
  render + CVXPY. CVXPY stub loads JSON (microseconds); real
  CVXPY Phase 4 = <50ms for 50 assets. Render = <100ms.
  Total <200ms. Acceptable.
* **Sort state lost on recompute.** Submitting a new aporte
  re-renders the page; `sortKey` resets to the default. If
  the operator wants to keep their sort, they must not
  re-submit. Acceptable — re-sort is one click.
* **Stub fixture divergence.** Page tests must NOT pin numeric
  values (`R$ 1.500,00`); only structure (8 cols, 6 cards,
  badges present). When CVXPY lands, numbers change but the
  page renders the same.
* **Sidebar include extraction.** `dashboard.html` currently
  inlines 3 buttons + the sidebar shell. Extracting to
  `_sidebar.html` requires removing that block from
  `dashboard.html` and adding `{% include %}`. Test count
  for the sidebar is non-trivial (3 buttons × 2 states
  each = ~6 e2e selectors). Refactor must be byte-equivalent
  on the rendered output for existing tests to pass.
* **`/api/rebalance` becomes a parallel path.** The page
  uses `run_rebalance()` server-side; tests use the JSON
  route. Both paths must stay in sync (same glue, same
  solver). Risk is low because they share `glue.run_rebalance()`.
* **Client-side `< 0` gate is UX, not security.** Server
  accepts negative (per Decision 9). An operator who edits
  the form devtools and submits `-5000` will see a withdrawal
  plan once Phase 4 ships. For v1 (stub), the response is
  misleading. Document in the empty state copy.
* **Empty profile → empty plan overlap.** The 422 path (form
  field missing) and the 200-empty path (zero classes) are
  distinct states. Tests must cover both.

## Migration Plan

No DB migration. No schema migration (Pydantic change is
backward-compatible — `gt=0` removal relaxes a constraint).
No backward-incompatible behavior change for external
consumers of `/api/rebalance` (the route still validates
finite floats and emits 422 on missing field).

* `/rebalance` is a new GET + POST.
* `_sidebar.html` is a new include; `dashboard.html` refactored
  to consume it (byte-equivalent rendered output for the
  existing dashboard).
* `RebalanceRequest.contribution` accepts 0 and negative;
  existing 422 scenarios in `test_rebalance_schemas.py`
  need updating (zero / negative now return 200, not 422).
* `applied_policy` rendering depends on `stub-fixture-v1`
  string match. If Phase 4 emits `stub-fixture-v1` (it
  shouldn't), the banner shows. Defensive: log a warning
  if `applied_policy == "stub-fixture-v1"` is seen in
  production logs.

Rollback: delete `rebalance.html` + `_sidebar.html`, revert
`dashboard.html` refactor + the schema change. No DB state
to undo.

## Open Questions

* **Sort on category_plan table?** Probably yes (by Δ desc
  surfaces biggest movers first). Defer to first review.
* **Print stylesheet?** Operator might want to print the plan
  and bring it to the broker. Defer.
* **CSV export of the plan?** Same use case. Defer.
* **"Refazer" button placement?** Inline next to the aporte
  value (after submit) or in the form's submit area (always)?
  Defer to design pass.

## Cross-references

* Contract: `openspec/specs/rebalance-route/spec.md` (delta here)
* Glue: `src/omaha/rebalance/glue.py` (unchanged)
* Solver stub: `src/omaha/rebalance/solver_stub.py` (unchanged)
* Sort pattern: `src/omaha/templates/dashboard.html:1137-1150`
  (`sortBy`, `sortIndicator`)
* Sidebar shell: `src/omaha/templates/dashboard.html:5-46`
* Plan roadmap: `.planning/REBALANCE_PLAN.md` (Gaps C+D+parte F)
