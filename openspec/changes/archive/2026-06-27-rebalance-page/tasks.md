# Tasks: rebalance-page

## 1. Contract extension — `rebalance-route` schema accepts any finite float

- [x] 1.1 Edit `src/omaha/rebalance/schemas.py`: `RebalanceRequest.
  contribution` drops `Field(gt=0)`, becomes plain `float`. Update
  the docstring to document the new range (0 = rebalance-only,
  negative = withdrawal, supported by the engine in Phase 4).
- [x] 1.2 Edit `openspec/specs/rebalance-route/spec.md`:
  - Replace requirement "Request validates contribution greater
    than zero" with "Request validates contribution as a finite
    float" (`NaN` / `inf` 422, missing field 422, zero and
    negative 200).
  - Remove scenarios "Zero contribution returns 422" and
    "Negative contribution returns 422".
  - Add scenario "NaN contribution returns 422".
  - Update requirement "POST /api/rebalance returns a
    RebalancePlanResponse" scenario "Active profile with classes
    and assets returns a populated plan" to use `contribution = 0`
    as the canonical case (was `5000.00`).
- [x] 1.3 Update `tests/test_rebalance_schemas.py`: drop or invert
  the `gt=0` assertions (zero / negative now valid). Add a
  `nan` / `inf` 422 test case. Prefix already registered as
  `tests/test_rebalance_schemas` (no change to
  `_INTEGRATION_PREFIXES`).
- [x] 1.4 Update `tests/test_rebalance_route.py`: same as 1.3
  for the route-boundary tests.

## 2. Sidebar extraction

- [x] 2.1 Create `src/omaha/templates/_sidebar.html`. Move the
  `<aside class="app-sidebar" ...>` block from
  `dashboard.html:5-46` verbatim. Add the 4th button area:
  ```html
  <form method="post" action="/rebalance"
        data-testid="rebalance-form"
        x-data="rebalanceForm()"
        @submit="validate($event)">
    <label for="sidebar-contribution" class="sidebar-form-label">
      Aporte (R$)
    </label>
    <input type="number" step="any" name="contribution"
           id="sidebar-contribution"
           x-model="contribution"
           inputmode="decimal"
           data-testid="sidebar-contribution-input"
           :class="{'rebalance-form-input--error': error}"
           :disabled="inert" required />
    <p class="rebalance-form-error" data-testid="sidebar-form-error"
       x-show="error" x-text="error"></p>
    <button type="submit"
            data-testid="sidebar-rebalance-btn"
            :disabled="inert || computing">
      <span x-show="!computing">Rebalancear</span>
      <span x-show="computing">Calculando...</span>
    </button>
  </form>
  ```
- [x] 2.2 Edit `src/omaha/templates/dashboard.html`: replace
  lines 5-46 (`<div class="app-sidebar-backdrop">` + `<aside>`)
  with `{% include "_sidebar.html" %}`. Conditional Jinja:
  the active-state on "Rebalancear" is
  `{% if request.url.path == '/rebalance' %}aria-current="true"{% endif %}`.
- [x] 2.3 Verify byte-equivalence of rendered dashboard: render
  `/` before and after, diff with `uv run python -c
  "..."` or eyeball. The 3 existing buttons must render
  identically; the 4th form is appended.

## 3. Routes — GET + POST `/rebalance`

- [x] 3.1 Edit `src/omaha/routes/pages.py`: add `GET /rebalance`
  handler. Loads profile, checks `len(asset_classes) == 0`,
  passes `plan=None, zero_classes=True/False, profile=...`
  to Jinja. Returns 200 always (no 4xx for empty profile —
  empty state renders).
- [x] 3.2 Edit `src/omaha/routes/pages.py`: add `POST /rebalance`
  handler. Reads `contribution` from `Form(...)`. Validates
  finite float (Pydantic: `form.contribution = float(...)`
  inside try/except; on ValueError or non-finite, re-render
  `/rebalance` GET with `form_error="Valor inválido. Use um
  número finito."` in context. On valid finite float, calls
  `run_rebalance(db, profile, contribution)` and renders the
  template with the resulting `RebalancePlanResponse` in
  context.
- [x] 3.3 Catch `RebalanceValidationError` from the glue; map
  to `form_error=str(exc)` + re-render GET template. Do NOT
  return 400 — page must render with the error inline.
- [x] 3.4 Register no new router — `pages.py` already mounts
  via `routes.pages.router` (verify in `main.py`).

## 4. Template — `rebalance.html`

- [x] 4.1 Create `src/omaha/templates/rebalance.html` extending
  `base.html`. Block `content`:
  ```html
  <div class="dashboard">  {# reuses grid #}
    {% include "_sidebar.html" %}
    <div class="dashboard-card rebalance-card"
         data-testid="rebalance-card">
      <!-- header nav -->
      <nav class="rebalance-nav">
        <a href="/" class="rebalance-nav-link"
           data-testid="rebalance-nav-dashboard">← Dashboard</a>
        <span class="rebalance-nav-link rebalance-nav-link--active"
              data-testid="rebalance-nav-plan">Plano de aporte</span>
      </nav>

      {% if zero_classes %}
        {% include "_rebalance_empty.html" %}
      {% elif plan is none %}
        {% include "_rebalance_placeholder.html" %}
      {% else %}
        {% include "_rebalance_plan.html" %}
      {% endif %}
    </div>
  </div>
  ```
- [x] 4.2 Create `src/omaha/templates/_rebalance_empty.html`:
  empty-state card with copy "Nenhuma classe cadastrada" +
  body "Crie ao menos uma classe antes de rebalancear." +
  link `[← Voltar ao dashboard]`.
- [x] 4.3 Create `src/omaha/templates/_rebalance_placeholder.
  html`: friendly message "Defina um valor de aporte e clique
  em Rebalancear para ver o plano." (shown when the user
  navigates to `/rebalance` via the sidebar before submitting
  — rare, but covers the "I'm just looking" case).
- [x] 4.4 Create `src/omaha/templates/_rebalance_plan.html`:
  the full layout — 6 metric cards grid, policy line, stub
  banner `<details>`, warnings list, asset plan table
  (8 cols + Alpine sort), category summary table.

## 5. Alpine — sort + form validation

- [x] 5.1 In `rebalance.html`, define `rebalancePage({...plan...})`
  Alpine component (local `x-data`, NOT a global store).
  Carries: `plan`, `sortKey='class'`, `sortDir='asc'`,
  `displayRows` (computed from `plan.asset_plan` + sort),
  `sortBy(key)`, `sortIndicator(key)`, `formatBRL(v, d=2)`.
- [x] 5.2 In `_sidebar.html`, define `rebalanceForm()` Alpine
  component. Carries: `contribution` (bound to input),
  `computing` (false; reserved for future fetch-based mode),
  `error` (empty string), `inert` (bound to `request.url.path
  == '/rebalance' and profile has zero classes` — passed via
  Jinja context), `validate($event)` (gate `< 0`).
- [x] 5.3 Sort function: re-export from
  `dashboard.html`'s pattern. Compare numeric fields
  numerically, strings case-insensitively. Tiebreak by
  original index.

## 6. CSS — `.rebalance-*` classes

- [x] 6.1 Edit `src/omaha/static/app.css`: add a new section
  after the dashboard-action-sidebar block (line 2201
  end-of-file or wherever the section breaks). New classes:
  - `.rebalance-card` — wraps the main content area.
  - `.rebalance-nav` — flex row, 2 links, border-bottom
    hairline.
  - `.rebalance-nav-link` — same color as `.app-sidebar`
    text; `--active` variant uses `--ink` + weight 600.
  - `.rebalance-stat-grid` — CSS grid `repeat(3, 1fr)`,
    `gap: 1rem`, `margin: 1rem 0`.
  - `.rebalance-stat` — reuses `.portfolio-stat` aesthetic
    (label uppercase muted, value Source Serif 4 weight 600).
  - `.rebalance-action-badge` — `display: inline-block`,
    `padding: 0.125rem 0.5rem`, `border-radius: 4px`,
    `font-size: 0.85rem`, `font-weight: 500`. Three variants:
    `--buy` (`--positive` 12% bg + `--positive-ink`),
    `--sell` (`--negative` 12% bg + `--negative-ink`),
    `--hold` (`--bg-hover` bg + `--ink`).
  - `.rebalance-stub-banner` — `<details>` styling:
    `padding: 0.5rem 0.75rem`, `border: 1px solid
    var(--border)`, `border-radius: 4px`, `margin: 0.75rem
    0`. `<summary>` cursor pointer, muted color.
  - `.rebalance-warnings` — `list-style: disc inside`,
    `padding: 0.5rem 0.75rem`, `background: var(--alert-warn)`
    at 12% opacity, `border-radius: 4px`. Each `<li>` has
    `<code>` for the code (monospace) + body text.
  - `.rebalance-table` — table styling mirroring
    `.asset-table` (hairline borders, sortable `<th>` with
    cursor pointer + indicator).
  - `.rebalance-form-input--error` — `border-color:
    var(--negative)` + `outline: 1px solid var(--negative)`.
  - `.rebalance-form-error` — `color: var(--negative)`,
    `font-size: 0.85rem`, `margin: 0.25rem 0`.
  - `.rebalance-form-label` — uppercase, muted, font-size
    `0.7rem`, matching `.portfolio-stat-label`.
- [x] 6.2 Verify contrast ratios for action badges meet
  WCAG AA (≥ 4.5:1). The 12% bg-opacity approach was used
  in S05 T03 — same pattern, should pass.

## 7. Tests — integration

- [x] 7.1 Create `tests/test_rebalance_page.py` (integration
  marker). Scenarios:
  - `GET /rebalance` with empty profile → 200, empty state
    markup present.
  - `GET /rebalance` with seeded Italo profile, no POST → 200,
    placeholder markup present.
  - `POST /rebalance` with valid contribution (e.g. 5000.00)
    → 200, plan markup present (6 metric cards, asset table
    with N rows).
  - `POST /rebalance` with `contribution=0` → 200, plan renders
    (validates the contract extension).
  - `POST /rebalance` with `contribution=-100` → 200, plan
    renders (validates the contract accepts negative; the
    page would gate this client-side, but the server is
    permissive).
  - `POST /rebalance` with `contribution=abc` → 200, form
    error inline "Valor inválido".
  - `POST /rebalance` with missing `contribution` field → 200,
    form error inline.
  - Plan response has applied_policy badge visible when
    `applied_policy == "stub-fixture-v1"`.
  - Plan response has 8 visible `<th>` cells in the asset
    table (data-testid checks).
  - Plan response has 4 visible `<th>` cells in the category
    table.
- [x] 7.2 Add prefix `tests/test_rebalance_page` to
  `_INTEGRATION_PREFIXES` in `tests/conftest.py` (AGENTS.md
  rule).
- [x] 7.3 Run `uv run task test-integration -k rebalance_page`
  and confirm all scenarios pass.

## 8. Tests — Playwright e2e smoke

- [x] 8.1 Create `tests/e2e/test_rebalance_page.py` reusing
  the S04 helpers (`_login_and_select_italo`, `_seed_43_
  assets` if needed). Scenarios:
  - Sidebar shows the 4th form area with input + button.
  - Type `5000`, click "Rebalancear", page navigates to
    `/rebalance` and shows the plan.
  - Empty profile: dashboard has zero classes → visit
    `/rebalance` → empty state visible, sidebar form input
    has `disabled` attribute.
  - Asset plan table is sortable: click "Valor atual" th,
    second click reverses.
  - Stub banner `<details>` visible when on plan page.
- [x] 8.2 Run `uv run task test-e2e -k rebalance_page` and
  confirm pass.

## 9. Verification + delivery

- [x] 9.1 Run `uv run task lint` and resolve any ruff
  violations in new files.
- [x] 9.2 Run `uv run task check` (lint + unit) — confirm
  no regressions.
- [x] 9.3 Run `uv run task db-reset` (Italo + Ana seeded
  fresh) so the dev DB has populated state for manual
  browser test.
- [x] 9.4 Run `uv run task serve` (background), open
  `http://192.168.1.6:8000/rebalance` in browser (LAN
  URL per AGENTS.md "Network access"), confirm:
  - Sidebar form is present with input + button.
  - Click "Rebalancear" with empty input → form validation
    error appears, page stays.
  - Type `5000`, click → page renders 6 metric cards +
    asset table + category summary + warnings.
  - Sort by "Valor atual" works.
  - Stub banner `<details>` is collapsed but expandable.
  - Dashboard `/` still renders identically (3 buttons +
    sidebar form).
- [x] 9.5 `openspec validate rebalance-page` passes
  (proposal + design + tasks + specs delta).
- [x] 9.6 Commit + push per AGENTS.md. No PR until user
  approves.
