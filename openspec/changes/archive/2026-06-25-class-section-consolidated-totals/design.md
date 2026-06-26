# Design — class-section-consolidated-totals

## Visual contract

```
┌── col 1 ──┬─ col 2 ─┬────── col 3 ──────────────┬── col 4 ──┬─ col 5 ──┬ col 6 ┬─ col 7 ──┬─ col 8 ──┐
│           │         │                            │           │          │       │          │         │
│  [▸]      │   [■]   │   Nome da classe   [×]    │  R$ 9.389 │ Sobra 1% │       │ Alvo 25% │Atual 23% │
│           │         │                            │           │          │       │          │         │
└───────────┴─────────┴────────────────────────────┴───────────┴──────────┴───────┴──────────┴─────────┘
                                  ↑                            ↑                  ↑          ↑          ↑
                          hdr-leading                    hdr-valor         hdr-delta   hdr-alvo   hdr-atual
                          (grid-col 1-3)                (col 4)            (col 5)    (col 7)    (col 8)
                                                     plain text        pill ex.    pill ex.   pill ex.
                                                     BRL sem dec.      (existente) (existente)(existente)

Class section body (collapsed state):

[▸] [■] Nome da classe   [×]    R$ 9.389    Sobra 1%            Alvo 25%   Atual 23%
─────────────────────────────────────────────────────────────────────────────────────
   (asset table hidden via .class-section-body--collapsed)
```

Column 6 stays empty: `Atual % classe` has no consolidated
counterpart (it's an intra-class property, not a class-level
property).

## Single source of truth for column widths

`src/omaha/static/app.css`:

```css
:root {
  /* Single source of truth for asset table column proportions.
     Read by .class-section-header (grid-template-columns) and
     by .asset-table <colgroup> (width per column). Change once,
     both realign. */
  --col-ativo: 2.5fr;
  --col-classe: 1.5fr;
  --col-qtd: 0.6fr;
  --col-valor: 1.2fr;
  --col-alvo-classe: 1fr;
  --col-atual-classe: 1fr;
  --col-alvo-total: 1fr;
  --col-atual-total: 1fr;
}

.class-section-header {
  display: grid;
  grid-template-columns:
    var(--col-ativo) var(--col-classe) var(--col-qtd)
    var(--col-valor) var(--col-alvo-classe) var(--col-atual-classe)
    var(--col-alvo-total) var(--col-atual-total);
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.hdr-leading { grid-column: 1 / span 3; display: flex; align-items: center; gap: 0.6rem; }
.hdr-valor   { grid-column: 4; text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; }
.hdr-delta   { grid-column: 5; justify-self: start; }
.hdr-alvo    { grid-column: 7; justify-self: start; }
.hdr-atual   { grid-column: 8; justify-self: start; }

.asset-table { table-layout: fixed; width: 100%; }
.asset-table col:nth-child(1) { width: var(--col-ativo); }
.asset-table col:nth-child(2) { width: var(--col-classe); }
.asset-table col:nth-child(3) { width: var(--col-qtd); }
.asset-table col:nth-child(4) { width: var(--col-valor); }
.asset-table col:nth-child(5) { width: var(--col-alvo-classe); }
.asset-table col:nth-child(6) { width: var(--col-atual-classe); }
.asset-table col:nth-child(7) { width: var(--col-alvo-total); }
.asset-table col:nth-child(8) { width: var(--col-atual-total); }

.asset-table td { overflow-wrap: break-word; }
```

Adding a column? Update `:root` only. Removing? Same. Changing
proportions? Same. The header cannot drift because it reads the
same variable list as the table.

## Template changes (`dashboard.html`)

`class_data` blob gains one field:

```jinja
{% set class_data = {
  "id": c.id,
  "name": c.name,
  "target_pct": (c.target_pct | float),
  "color": c.color,
  "current_pct": (c.current_pct | float),
  "current_value": (c.current_value | float),
  "assets": [...]
} %}
```

`.class-section-header` HTML restructured:

```html
<header class="class-section-header"
        data-testid="class-section-header"
        @click="isOpen = !isOpen">
  <div class="hdr-leading">
    <span class="class-chevron"
          data-testid="class-chevron"
          :class="{'class-chevron--open': isOpen}">▸</span>
    <span class="class-color-swatch"
          data-testid="class-color-swatch"
          style="background:{{ c.color }}"></span>
    <span class="class-section-name"
          data-testid="class-section-name">{{ c.name }}</span>
    <button type="button"
            class="class-section-delete-btn"
            data-testid="class-delete-btn"
            @click.stop="showDeleteConfirm = true"
            x-show="!showDeleteConfirm && !deleting"
            title="Remover classe">×</button>
  </div>

  <span class="hdr-valor"
        data-testid="class-total-value"
        x-text="classCurrentValue > 0
                ? formatBRLCompact(classCurrentValue)
                : '—'"></span>

  <span class="hdr-delta">
    <span class="pct-delta-pill"
          :class="classDelta > 0 ? 'pct-delta-pill--short' : 'pct-delta-pill--long'"
          data-testid="class-delta-badge"
          x-show="classDeltaMessage"
          x-text="classDeltaMessage"></span>
  </span>

  <span class="hdr-alvo">
    <span class="pct-target-pill"
          data-testid="class-target-pct-view"
          x-show="!editingClassPct"
          @click.stop="startEditClassPct()"
          title="Clique para editar">
      Alvo <span x-text="classTargetPct"></span>%
    </span>
    <span class="pct-target-pill"
          data-testid="class-target-pct-edit"
          x-show="editingClassPct"
          x-cloak>
      Alvo
      <input type="number"
             step="0.01" min="0" max="100"
             class="class-inline-edit-input"
             data-testid="class-inline-edit-input"
             x-model="editClassPctValue"
             @keyup.enter="commitEditClassPct()"
             @keyup.escape.window="cancelEditClassPct()"
             @blur="commitEditClassPct()"
             :disabled="savingClassPct"
             @click.stop>
      <span class="class-inline-edit-error"
            data-testid="class-inline-edit-error"
            x-show="editClassPctError"
            x-text="editClassPctError"
            x-cloak></span>
    </span>
  </span>

  <span class="hdr-atual">
    <span class="pct-current-pill"
          :class="'pct-current-pill--' + classCurrentStatus"
          data-testid="class-current-pct">
      Atual <span x-text="Number(classCurrentPct).toFixed(2)"></span>%
    </span>
  </span>
</header>
```

Asset table gains `<colgroup>`:

```html
<table class="asset-table" data-testid="asset-table">
  <colgroup>
    <col class="col-ativo">
    <col class="col-classe">
    <col class="col-qtd">
    <col class="col-valor">
    <col class="col-alvo-classe">
    <col class="col-atual-classe">
    <col class="col-alvo-total">
    <col class="col-atual-total">
  </colgroup>
  <thead>...</thead>
  <tbody>...</tbody>
</table>
```

## JS changes (`classSection` factory)

```javascript
classCurrentValue: initial.current_value,

formatBRLCompact: function (value) {
  // BRL without decimals: "R$ 9.389" instead of "R$ 9.389,96".
  // Caller already gates on `classCurrentValue > 0` to swap in
  // the em-dash for empty classes, so this is always called with
  // a positive value.
  var n = Number(value) || 0;
  return n.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
},
```

## Reactivity story

- `classCurrentValue` flows from the server-rendered `class_data`
  blob. After `PATCH /api/assets/{id}` (inline asset edit), the
  server doesn't recompute `current_value` (the value depends on
  `current_price`, not `target_pct`). The page reloads on
  `POST /api/assets` and `DELETE /api/assets/{id}` (existing
  contract), which re-fetches the aggregate. **No client-side
  reactivity work needed for this delta.**
- `classTargetPct` and `classCurrentPct` keep their existing
  reactivity via the `classSection` Alpine component (the
  `commitEditClassPct` PATCH path mutates the local model and
  updates `Alpine.store('classSum')` in place).
- `classDelta` / `classDeltaMessage` keep their existing
  reactivity (derived from `assets` + `classTargetPct`).

## Why this is the right shape (decisions)

1. **Grid + colgroup over subgrid or full refactor.** Subgrid
   support is now universal in evergreen browsers but the project
   already uses grid + colgroup patterns elsewhere; staying
   consistent avoids introducing a third layout primitive. A full
   refactor to CSS Grid for the table would touch the sort
   indicator, the column-header click handlers, the `colspan="8"`
   delete-confirm row, and all e2e selectors — disproportionate
   to the goal.

2. **`table-layout: fixed` over `auto`.** Fixed is the only way
   `<colgroup>` widths are authoritative. The wrap behaviour for
   long asset names is preserved via `overflow-wrap: break-word`
   on `td`. The dashboard container already has
   `max-width: 1400px` (dashboard-inline-editing spec) so the
   table has a finite horizontal space to distribute.

3. **8 columns with 4 unused slots in the header (col 6, etc.).**
   The header uses `grid-column: 1 / span 3` for the leading
   group (chevron + swatch + name + ×), so the layout already
   compresses to "leading | valor | delta | alvo | atual" — 5
   visible cells in 8 columns. Column 6 is intentionally empty
   (no consolidated equivalent for `Atual % classe`). The empty
   column keeps the alignment semantic: `Alvo` pill stays in col
   7 because that's where the `Alvo % total` column lives in the
   table.

4. **`Sobra|Falta` aligned with `Alvo % classe`, not floating.**
   The pill measures `100 - sum(asset.target_pct_class)` — it is
   metadata about the `Alvo % classe` column. Placing it in col 5
   gives it a column to anchor to; placing it elsewhere would
   make it a free-floating indicator with no horizontal
   relationship.

5. **`×` next to class name, not at far right.** The delete
   button is destructive; grouping it with the class identity
   (name) instead of with the stats makes the affordance
   scannable and prevents the stats row from being terminated by
   a destructive control.

## Tradeoffs accepted

- **Table column widths become CSS-driven, breaking one
  precedent.** The existing
  `dashboard-inline-editing/spec.md` "Column widths" requirement
  hard-codes percentages (`Ativo 24%`, `Classe 18%`, ...). The new
  variables translate to roughly the same proportions (in `fr`
  units) but expressed differently. The OLD hard-coded
  percentage table is **removed** in favor of the CSS variables;
  the spec delta below captures the new contract.

- **Long asset names wrap instead of overflowing.** A name like
  `"Tesouro Selic 2029"` wraps to two lines instead of
  overflowing horizontally. Acceptable per user direction:
  "deixa quebrar a linha, mas o ideal é que não precise,
  aproveite o maximo possivel a largura da tela".

- **Header leading area collapses names with `flex: 1` lost.**
  `.class-section-name` was `flex: 1` in the old flex layout.
  In the new grid, the leading slot is `grid-column: 1 / span 3`
  — the name grows to fill the slot up to the col 4 boundary.
  Names longer than the slot wrap to two lines (acceptable; same
  behaviour as table cells).