# Performance baseline — Omaha test suite

Data da coleta: 2026-07-12
Ambiente: Linux x86_64, Python 3.12.13, uv 0.11.21, SQLite
Branch: `main` (commit `8fea2b0`)

> Snapshot de baseline: contagens e tempos registrados abaixo servem para
> triagem de regressão nesta coleta; não são contrato de duração.

## Commands

```bash
uv run task test-unit              # lane rápida: unit
uv run task test-integration       # lane rápida: integration
uv run task test-audit-integration # audit pesado, separado
uv run task coverage               # unit + integration; único comando que grava reports/coverage.xml
uv run task test-e2e               # lane de navegador: e2e
uv run task test-bdd               # lane de navegador: BDD serial
uv run task test-visual            # lane de navegador: regressão visual
uv run task test                   # suite completa: unit + integration + audit + e2e + visual + BDD
```

## Resumo por grupo

| Grupo | Comando observado | Coletados | Passaram | Falharam | Pulados | Deselecionados | Tempo total |
|---|---|---:|---:|---:|---:|---:|---:|
| unit | `uv run task test-unit` | 869 | 349 | 0 | 2 | 518 | 16,82 s |
| integration | `uv run task test-integration` | 856 | 386 | 0 | 2 | 468 | 219,26 s |
| audit integration | `uv run task test-audit-integration` | 13 | 13 | 0 | 0 | 0 | 22,53 s |
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
| 11.35s | tests/test_audit_inventory.py::test_inventory_rows_carry_template_field |
| 8.85s | tests/test_audit_inventory.py::test_inventory_for_patrimonio_produces_rows |
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
