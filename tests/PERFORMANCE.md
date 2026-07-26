# Performance baseline — Omaha test suite

Visual policy: desktop-only (`1440x900`) by owner authorization dated
2026-07-26. Omaha is not used or supported on mobile. Exactly ten mobile visual
nodes and matching mobile baselines were removed; this does not claim mobile
CSS, layout, or interaction works. All desktop visual scenarios, lanes, browser
harnesses, and non-visual coverage remain.

Data da coleta: 2026-07-25
Ambiente: Linux x86_64, Python 3.12.13, pytest 9.1.1, SQLite
Branch: T29 working tree

> Snapshot de baseline: contagens e tempos registrados abaixo servem para
> triagem de regressão nesta coleta; não são contrato de duração.

## Commands

```bash
uv run task gate-fast             # fast gate pré-merge: lint + unit (< 2 min)
uv run task test-unit              # lane rápida: unit
uv run task test-integration       # lane rápida: integration
uv run task test-audit-integration # audit pesado, separado
uv run task coverage               # unit + integration; único comando que grava reports/coverage.xml
uv run task test-e2e               # lane de navegador: e2e
uv run task test-bdd               # lane de navegador: BDD serial
uv run task test-visual            # lane de navegador: regressão visual
uv run task test                   # suite completa concorrente: seis lanes
```

## Resumo por grupo

| Grupo | Comando observado | Coletados | Passaram | Falharam | Pulados | Deselecionados | Tempo total |
|---|---|---:|---:|---:|---:|---:|---:|
| unit | `uv run task test-unit` | 1026 | 490 | 0 | 2 | 534 | 14,72 s |
| integration | `uv run task test-integration` | 1026 | 377 | 0 | 0 | 649 | measured in full runner |
| audit integration | `uv run task test-audit-integration` | 40 | 40 | 0 | 0 | 0 | measured in full runner |
| e2e | `uv run task test-e2e` | 49 | 48 | 1 | 0 | 0 | 195,31 s |
| BDD | `uv run task test-bdd` | 51 | 51 | 0 | 0 | 0 | 198,00 s |
| visual | `uv run task test-visual` | 20 | 20 | 0 | 0 | 0 | 82,24 s |

> **Reconciliação:** Coletados = Passaram + Falharam + Pulados + Deselecionados.
> Deselecionados em unit/integration são testes filtrados pelo marcador
> (`-m unit` ou `-m integration`) — cada lane vê a suíte completa coletada
> e descarta os testes da outra lane.

Na coleta original, `uv run task test-e2e` teve uma falha em
`tests/e2e/test_user_journey_rebalance.py::TestS05DashboardJourney::test_dashboard_full_journey_renders_s05_polish`
por `KeyError: 'import_upload_btn'`. Correção posterior removeu a interação
obsoleta: selecionar arquivo dispara upload automático e aguarda a prévia.

## Lanes de execução

A **lane rápida** cobre unit + integration. Quando coverage é necessária, o
comando canônico é `uv run task coverage`; ele é o único que gera
`reports/coverage.xml` para esse grupo. Audit integration fica em task
separada pelo custo alto.

A **lane de navegador** roda `uv run task test-e2e`, `uv run task test-bdd` e
`uv run task test-visual` isoladamente. BDD é serial: compartilha SQLite
semeado e o wipe autouse entre cenários. Essas suítes validam fluxo e visual,
não produzem coverage XML e não devem pagar custo de instrumentação.

## Gate definitions

### Fast gate (`task gate-fast`)

**Comando:** `uv run prek run --all-files && uv run pytest -m unit --cov=src/omaha --cov-report=xml:reports/coverage.xml`

Roda lint (prek hooks: ruff format, ruff --fix, hygiene) + testes unitários
com coverage XML. Exclui integration, e2e, BDD, visual, audit integration.

**Target:** < 2 min wall-clock. **Baseline:** ~30 s (lint ~5 s + unit ~17 s).

Gate pré-merge para PRs. Coverage XML vai para `reports/coverage.xml`.

### Full suite (`task test`)

**Comando:** `uv run task test`

Roda tudo: unit + integration + audit integration + e2e + visual + BDD.

**Baseline serial:** 610.17 s, 1,024 passed + 2 skipped.
**Concurrent profile runs:** historical observations only; not proof.
Three consecutive canonical runs completed the Phase B final gate.

## Phase B proof receipt

- **Run stamps:** `20260726T190307`, `20260726T190824`, `20260726T191307`
- **Wall time per run (receipt JSON):** `280.98s`, `276.10s`, `274.77s` (all <=300s)
- **Baseline collection checksum:** `a77e2a45fa2ff6c9854a945870f0489c54c332aa2a3dd4845970e256f06d40c8` (1,043 nodes)
- **Lane checksums:** unit `bdfe4cb037d726636f0899bc72618f7cbe3ba255497fa0ac7c481bd33b9b057c`; integration `6711cc2ff451cabc34e2ac7c74ad3519dfec8bf4034027456f5985545c33b7a2`; audit `0d0832484bd349cb35aa77573321597780721c1a9f6df2ca95be22fc22d2eab6`; e2e `6d81bb92d6101042427dbeea230d2e633ee089f842e6df7fd1a032cfea034e40`; bdd `a8543643bbf371fcd508c4822a79aa609b0abdd6b1e2a74a184f629e807e57db`; visual `d7481c04e1d95966d4965284d324c67dbcda21923c080932a1801f011a03c031`
- **Skip IDs:** `tests/test_dockerfile.py::test_docker_build_pro_image_succeeds`, `tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user`
- **Per-lane exit codes:** all six lanes `0` on all three runs
- **Resolved DB targets:** unit/integration/audit dynamic `/tmp/omaha-conftest-safe-*/portfolio.db`; e2e `/home/juca/github/omaha/data/test_e2e.db`, `/home/juca/github/omaha/data/test_e2e_short_ttl.db`; bdd `/home/juca/github/omaha/data/test_bdd.db`; visual `/home/juca/github/omaha/data/test_visual.db`
- **clean_children:** `true` on all three runs
- **Source inventory checksum:** `a77e2a45fa2ff6c9854a945870f0489c54c332aa2a3dd4845970e256f06d40c8`

Runner writes transient lane logs and JSON under `reports/test-profile/`;
directory is gitignored. Durable per-node decisions live in `tests/AUDIT.md`.
Profile method uses existing taskipy lanes three times with
`PYTEST_ADDOPTS='--durations=0 -vv'`; medians use reported durations. Compare
node IDs and skip identities before accepting timing changes. Scheduled lane
movement is not full-routine coverage.

## Final hotspot decision

Phase B proof is complete. Owner-authorized mobile removal remains exactly ten
mobile visual nodes; owner-authorized desktop duplicate removal is exactly
`assets-table[desktop]` and `classes[desktop]`, with matching desktop baselines.
No further node, lane, skip, xfail, or coverage change is accepted.

### Browser lanes

| Lane | Comando | Requisito | Parte do fast gate? |
|------|---------|-----------|---------------------|
| e2e | `task test-e2e` | Playwright + Chromium | Não |
| BDD | `task test-bdd` | Playwright + Chromium, serial | Não |
| visual | `task test-visual` | Playwright + Chromium | Não |

Browser lanes rodam assíncrono no CI. Não participam do fast gate.

## Top 20 mais lentos — unit

| Tempo | Teste |
|-------|-------|
| 0.40s | tests/test_rebalance_postprocessing.py::test_simulate_rebalance_recomputes_totals_after_threshold_suppression |
| 0.39s | tests/test_db_mutations.py::test_asset_delete_api_writes_audit_and_snapshot |
| 0.38s | tests/test_db_mutations.py::test_import_commit_writes_audit_and_snapshot |
| 0.37s | tests/test_db_mutations.py::test_class_delete_form_writes_audit_and_snapshot |
| 0.37s | tests/test_db_mutations.py::test_audit_count_equals_one_per_destructive_op |
| 0.35s | tests/test_db_mutations.py::test_asset_delete_form_writes_audit_and_snapshot |
| 0.34s | tests/test_db_mutations.py::test_class_delete_api_writes_audit_and_snapshot |
| 0.33s | tests/test_db_mutations.py::test_snapshot_replace_writes_audit_and_snapshot |
| 0.33s | tests/test_dark_mode_tokens.py::test_color_focus_against_bg_passes_3to1 |
| 0.32s | tests/test_rebalance_engine_regression.py::test_phase2_does_not_sell_asset_at_target_when_category_receives_contribution |
| 0.32s | tests/test_db_mutations.py::test_snapshot_file_is_valid_sqlite_with_pre_mutation_state |
| 0.32s | tests/test_admin_recovery.py::test_admin_restore_happy_path_copies_and_returns_202 |
| 0.32s | tests/test_rebalance_engine_regression.py::test_phase1_does_not_drain_underweight_category_even_with_internal_overweights |
| 0.32s | tests/test_admin_recovery.py::test_admin_snapshots_lists_platform_snapshots |
| 0.31s | tests/test_admin_recovery.py::test_admin_audit_paginates_with_since |
| 0.31s | tests/test_dark_mode_tokens.py::test_class_colors_tuple_parity_with_class_3 |
| 0.30s | tests/test_admin_recovery.py::test_admin_snapshots_skips_missing_files |
| 0.29s | tests/test_dark_mode_tokens.py::test_negative_ink_on_negative_passes_aa |
| 0.28s | tests/test_admin_recovery.py::test_admin_audit_returns_recorded_mutations |
| 0.27s | tests/test_dark_mode_tokens.py::test_legacy_aliases_intact |

## Top 20 mais lentos — integration

| Tempo | Teste |
|-------|-------|
| 11.35s | tests/audit_integration/test_audit_inventory.py::test_inventory_rows_carry_template_field |
| 8.85s | tests/audit_integration/test_audit_inventory.py::test_inventory_for_patrimonio_produces_rows |
| 4.51s | tests/test_db_reset_both_profiles.py::test_reset_both_profiles_seeds_both_profiles |
| 3.51s | tests/test_assets_trade_flags.py::test_alembic_downgrade_then_upgrade_round_trip |
| 3.07s | tests/test_seed_from_csv.py::test_upsert_updates_changes_creates_missing |
| 2.17s | setup tests/test_seed_from_csv.py::test_reset_is_idempotent |
| 2.14s | setup tests/test_seed_from_csv.py::test_loader_rejects_unknown_quote_kind |
| 2.04s | tests/test_seed_from_csv.py::test_diff_lists_changes_no_write |
| 2.02s | setup tests/test_seed_from_csv.py::test_non_ascii_asset_name_round_trips |
| 1.93s | setup tests/test_seed_from_csv.py::test_sum_violating_class_csv_is_rejected |
| 1.90s | setup tests/test_seed_from_csv.py::test_non_tradeable_position_explicit_totals_preserve_value |
| 1.90s | tests/test_seed_from_csv.py::test_reset_is_idempotent |
| 1.89s | tests/test_seed_from_csv.py::test_upsert_rejects_sum_violation_before_write |
| 1.88s | setup tests/test_seed_from_csv.py::test_legacy_four_column_asset_header_is_rejected |
| 1.86s | setup tests/test_seed_from_csv.py::test_reset_preserves_totals_verbatim_no_recompute |
| 1.85s | setup tests/test_seed_from_csv.py::test_reset_preserves_divergent_broker_ticker |
| 1.83s | setup tests/test_seed_from_csv.py::test_diff_lists_changes_no_write |
| 1.82s | setup tests/test_seed_from_csv.py::test_invalid_currency_in_assets_csv_aborts |
| 1.78s | setup tests/test_seed_from_csv.py::test_run_reset_populates_trade_fields_from_csv |
| 1.77s | setup tests/test_seed_from_csv.py::test_position_referencing_missing_asset_is_rejected |

## Top 20 mais lentos — e2e

| Tempo | Teste |
|-------|-------|
| 6.72s | tests/e2e/test_import_user_journey.py::TestS04ImportJourney::test_import_journey_43_matched_5_unmatched_5_assigned_confirm_dashboard |
| 6.19s | tests/e2e/test_import_modal.py::TestS04ImportModal::test_import_modal_happy_path |
| 5.88s | tests/e2e/test_rebalance_page.py::TestRebalancePage::test_editing_contribution_refreshes_plan_automatically |
| 5.77s | setup tests/e2e/test_import_user_journey.py::TestS04ImportJourney::test_expired_preview_shows_expirado |
| 5.69s | setup tests/e2e/test_asset_crud.py::TestS03AssetCRUD::test_assets_route_redirects_to_dashboard |
| 5.52s | tests/e2e/test_asset_table.py::TestS10AssetTable::test_table_sort_by_each_column |
| 5.02s | tests/e2e/test_asset_table.py::TestS10AssetTable::test_edit_alvo_pct_total_updates_class_sum_and_alert |
| 4.71s | tests/e2e/test_user_journey_rebalance.py::TestS05DashboardJourney::test_dashboard_full_journey_renders_s05_polish |
| 4.31s | tests/e2e/test_rebalance_page.py::TestRebalancePage::test_asset_table_poc_parity_interactions |
| 4.00s | tests/e2e/test_full_journey.py::TestS06PosicaoItaloImport::test_import_posicao_italo_with_class_association |
| 3.99s | tests/e2e/test_user_journey.py::TestS03UserJourney::test_full_crud_journey_classes_assets_delete |
| 3.81s | tests/e2e/test_import_user_journey.py::TestS04ImportJourney::test_expired_preview_shows_expirado |
| 3.35s | tests/e2e/test_asset_table.py::TestS10AssetTable::test_patch_does_not_reorder_rows |
| 3.22s | tests/e2e/test_asset_table.py::TestS10AssetTable::test_modal_add_asset_flow |
| 3.19s | tests/e2e/test_asset_table.py::TestS10AssetTable::test_alert_card_disappears_on_convergence |
| 3.04s | tests/e2e/test_class_crud.py::TestS02ClassCRUD::test_delete_class_with_assets_shows_409 |
| 2.98s | tests/e2e/test_asset_table.py::TestS10AssetTable::test_class_header_toggle_collapses_and_expands_assets |
| 2.88s | tests/e2e/test_inline_edit.py::TestS01InlineEdit::test_dashboard_displays_four_percentages_per_asset |
| 2.82s | tests/e2e/test_asset_table.py::TestS10AssetTable::test_alert_card_shows_severity_for_small_and_large_deviations |
| 2.77s | tests/e2e/test_asset_crud.py::TestS03AssetCRUD::test_full_asset_crud_journey |

## Top 20 mais lentos — bdd

| Tempo | Teste |
|-------|-------|
| 13.77s | tests/bdd/test_scenarios.py::test_ana_sees_italo_classes_after_switch |
| 8.86s | tests/bdd/test_scenarios.py::test_italo_sees_ana_classes_after_switch |
| 7.96s | tests/bdd/test_scenarios.py::test_duplicate_class_name_409[Ana] |
| 7.89s | tests/bdd/test_scenarios.py::test_duplicate_class_name_409[Italo] |
| 6.76s | tests/bdd/test_scenarios.py::test_login_ok |
| 5.14s | tests/bdd/test_scenarios.py::test_manual_add_4_assets_unequal[Ana] |
| 5.06s | tests/bdd/test_scenarios.py::test_manual_add_4_assets_unequal[Italo] |
| 4.69s | tests/bdd/test_scenarios.py::test_inline_create_2_classes_soma_110[Ana] |
| 4.68s | tests/bdd/test_scenarios.py::test_row_pin_preserves_visual_position[Ana] |
| 4.10s | tests/bdd/test_scenarios.py::test_import_happy_auto_match[Italo] |
| 3.96s | tests/bdd/test_scenarios.py::test_row_pin_preserves_visual_position[Italo] |
| 3.95s | tests/bdd/test_scenarios.py::test_import_happy_auto_match[Ana] |
| 3.75s | tests/bdd/test_scenarios.py::test_derived_recomputes_on_asset_patch[Italo] |
| 3.67s | tests/bdd/test_scenarios.py::test_inline_add_with_patch_target[Italo] |
| 3.63s | tests/bdd/test_scenarios.py::test_per_class_sum_off_100_accepted_target_pct[Italo] |
| 3.53s | tests/bdd/test_scenarios.py::test_click_asset_class_cell_focuses_input[Italo] |
| 3.51s | tests/bdd/test_scenarios.py::test_clear_asset_class_target_enter_saves_zero[Ana] |
| 3.50s | tests/bdd/test_scenarios.py::test_per_class_sum_off_100_accepted_target_pct[Ana] |
| 3.43s | tests/bdd/test_scenarios.py::test_derived_recomputes_on_class_patch[Ana] |
| 3.40s | tests/bdd/test_scenarios.py::test_clear_asset_class_target_enter_saves_zero[Italo] |

## Oportunidades de paralelização

1. **Separar navegador do resto**: e2e + BDD + visual pertencem à lane de navegador. Rodá-los em jobs separados do CI reduz o feedback loop da lane rápida (unit + integration).

2. **pytest-xdist em unit/integration**: unit ainda é curto (16,82 s total) e não vale muito overhead. Integration já bate ~219,26 s e pode ganhar com `pytest-xdist -n auto`, porém os testes usam um banco SQLite por sessão compartilhado; paralelização só é segura se cada worker tiver seu próprio banco de testes (fixture de escopo `session` por worker ou mudança para banco em memória por worker).

3. **BDD serial obrigatório**: o `clean_seeded_profiles` do BDD é autouse e compartilha o arquivo SQLite `data/test_bdd.db`. Não adicionar `pytest-xdist` ao BDD sem isolar o banco por worker.

4. **e2e já reaproveita o browser**: o fixture `_browser` é session-scoped; paralelização exigiria múltiplas instâncias de chromium, o que pode ser mais lento. Manter e2e serial por enquanto.

5. **Gargalos de setup no integration**: os `setup` dos model tests (T01) consomem ~0.6 s cada porque rodam `omaha_db` com alembic + seed por teste. Migrar esses testes para usar o fixture session-scoped `_omaha_test_env`/`client` (como os T02/T03) eliminaria esse custo repetido.

6. **Gargalos do audit**: `test_report_pipeline.py` gera arquivos HTML/PNG no disco (~3.7 s cada). Avaliar se os screenshots e relatórios completos são necessários em cada execução ou podem ser opt-in/tamanho reduzido.
