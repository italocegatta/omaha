## 1. Renumber the seed CSVs

- [x] 1.1 In `data/seed/ana_classes.csv`, set the normative `display_order` mapping (RF Pós=0, RF Dinâmica=1, FII=2, Ações=3, Internacional=4, Cripto=5) and physically reorder the rows to ascending `display_order`; keep each row's `name`, `target_pct` (RF Pós 29.00, RF Dinâmica 25.00, FII 15.00, Ações 10.90, Internacional 20.00, Cripto 0.10), and `quote_kind` unchanged; confirm `sum(target_pct) == 100`
- [x] 1.2 Apply the identical mapping and row order to `data/seed/italo_classes.csv` (keeping Italo's own `target_pct` values: RF Pós 15.00, RF Dinâmica 25.00, FII 15.00, Ações 15.00, Internacional 20.00, Cripto 10.00); confirm `sum(target_pct) == 100`
- [x] 1.3 Verify the diff is data-only: header unchanged, still exactly 6 rows per file, and no change to any `name`/`target_pct`/`quote_kind` cell beyond the `display_order` renumber + row reorder

## 2. Reseed and test

- [x] 2.1 Run `uv run task db-reset` (reseeds both profiles from the CSVs)
- [x] 2.2 Run the seed suite: `uv run pytest tests/test_seed_from_csv.py -q` (L233-238 compares `display_order` CSV↔DB dynamically; stays green because file order == display_order order is preserved)
- [x] 2.3 Run the full suite: `uv run task test` — confirm green
- [x] 2.4 Run lint (`uv run task lint` or repo hook equivalent) and confirm clean

## 3. Visual baseline and delivery

- [x] 3.1 Regenerate ONLY the `patrimonio` visual baseline (repo visual task with `UPDATE_VISUAL_BASELINES=1`), then rerun visual without update to confirm green
- [x] 3.2 Inspect the visual diff: only block order (and the positional colors that follow position) may change — no unrelated style/content changes
- [x] 3.3 Run `refresh-for-test` and emit the mandatory PRD §4.9 delivery receipt
- [x] 3.4 Run the spec verification gate `openspec validate f54-ordem-dos-blocos-de-classe-no-patrimonio --strict` before archive

**Scope guard (all sections):** NÃO alterar conteúdo/estilo dos blocos, agregações, filtros, rotas, templates, CSS, `src/omaha/routes/pages.py` ou solver. A mudança se limita aos dois CSVs de classe (+ baseline visual `patrimonio` regenerado).
