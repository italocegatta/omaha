## Context

`/patrimonio` renders class table blocks via the Jinja loop `{% for c in class_aggregates %}` (L2 of `src/omaha/templates/_patrimonio_class_section.html`). `class_aggregates` comes from `src/omaha/routes/pages.py` L251 `.order_by(AssetClass.display_order)`. `AssetClass.display_order` is seeded from the per-profile class CSVs (`data/seed/{profile}_classes.csv`, column `display_order`) — the single source of truth for seed per PRD §4.3.

Current order in both profiles (`ana_classes.csv` and `italo_classes.csv`): `RF Dinâmica(0), RF Pós(1), Internacional(2), FII(3), Cripto(4), Ações(5)`. Owner normative order: `RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`.

F53 (archived `2026-07-29-f53-ordem-dos-cards-de-classe-no-rebalanceamento`) resolved the same normative order on `/rebalanceamento` with a client-side name→position map and explicitly deferred the seed-based order for `/patrimonio` to this slice (F54).

## Goals / Non-Goals

**Goals:**
- `/patrimonio` class blocks render in owner normative order for both seed profiles, achieved as a data-only change (two CSVs) + `task db-reset`.
- Family view (`?view=household`) stays correct with no code change — it sorts by the min `display_order` of member classes (pages.py L1294/L1338).
- Preserve the CSV convention "rows physically ordered by `display_order` ascending", required by the dynamic CSV↔DB comparison in `tests/test_seed_from_csv.py` (L233-238).

**Non-Goals:**
- Any change to `src/omaha/routes/pages.py`, templates, CSS, aggregations, filters, routes, or the rebalance solver.
- Remapping class colors by name (`_CLASS_COLORS` stays positional — owner accepted the rotation).
- Renaming classes or changing `target_pct` / `quote_kind` values, or adding/removing classes.
- A client-side ordering mechanism for `/patrimonio` (the F53 JS-map approach is rebalanceamento-only by design).

## Decisions

### D1 — Renumber + physically reorder both class CSVs (data only)

Exact renumbering mapping (before → after), applied identically to `data/seed/ana_classes.csv` and `data/seed/italo_classes.csv`:

| Classe          | display_order antes | display_order depois |
|-----------------|---------------------|----------------------|
| RF Pós          | 1                   | 0                    |
| RF Dinâmica     | 0                   | 1                    |
| FII             | 3                   | 2                    |
| Ações           | 5                   | 3                    |
| Internacional   | 2                   | 4                    |
| Cripto          | 4                   | 5                    |

Each row keeps its own `name`, `target_pct`, and `quote_kind` (e.g. Ana: RF Pós stays `29.00`; Italo: RF Pós stays `15.00`). Only the `display_order` cell changes, and rows are physically reordered to ascending `display_order`. The sum invariant (`sum(target_pct) == 100` per file) is unaffected — reordering does not change values (Ana: 29.00+25.00+15.00+10.90+20.00+0.10; Italo: 15.00+25.00+15.00+15.00+20.00+10.00).

Why physical row reorder too: `scripts/seed_from_csv/loaders.load_classes` returns rows in file order, and `tests/test_seed_from_csv.py` L236-238 compares the DB (queried with `.order_by(AssetClass.display_order)`) against the CSV list in file order. The files today satisfy "file order == display_order order"; keeping that convention keeps the suite green with zero test edits.

Alternatives considered:
- Change only the numeric cells, keep row positions: rejected — breaks the dynamic CSV↔DB comparison above and violates the file convention.
- Renumber in the DB only (SQL): rejected — PRD §4.3 makes the CSV the single source of truth; any `db-reset` would revert it.

### D2 — Accept positional color rotation (owner decision 2026-07-28 — BINDING)

`_CLASS_COLORS` (pages.py L935-951) is a positional palette: the Nth rendered block receives the Nth color. The owner decision of 2026-07-28 explicitly ACCEPTS that classes inherit the color of their new position (e.g. RF Pós takes the color previously rendered at position 0). The palette stays untouched; minimal scope is CSV renumbering only, zero changes in `pages.py`.

Alternatives rejected by owner as scope expansion:
- Remap the palette by class name so colors travel with classes.
- Add a per-class color column to the seed CSV / model.

### D3 — No code change; mechanism is already display_order-driven

The route already orders blocks by `AssetClass.display_order`, and the seed CSV is the single seed path (PRD §4.3), so the visible effect is fully achieved by `task db-reset` after the renumbering. Runtime-created classes (UI/import) get `display_order = max+1`, so they render after the normative six — no impact. F53's rebalance cards use their own client-side map and do not read `display_order` — unaffected.

### D4 — Visual baseline

Patrimônio block positions shift, so only the `patrimonio` visual baseline is regenerated (repo visual task with `UPDATE_VISUAL_BASELINES=1`, per the F53 precedent), then rerun without update to confirm green. Diff inspection must show only block order (and the positional colors that follow position) moving — nothing else.

## Risks / Trade-offs

- [Color semantics shift] → owner explicitly accepted the rotation (D2); recorded here as binding.
- [Other `display_order` consumers] → profile switcher / profile landing order by `Profile.display_order` (a different table — unaffected); rebalance builders sort client-side via the F53 map (unaffected); family view sorts by min member `display_order` (follows the new order automatically, desired).
- [Snapshot round-trip] → `task db-snapshot` exports classes ordered by `display_order`; after reset with the new CSVs the snapshot reproduces the new order deterministically.
- [Visual snapshot diff] → expected; regenerate only the `patrimonio` baseline and inspect for unrelated diffs before committing.
- [Test coupling to file order] → the physical reorder in D1 preserves the "file order == display_order order" convention the seed suite relies on; no test edits needed.
