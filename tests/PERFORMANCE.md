# Performance baseline — Omaha test suite

Date: 2026-06-23
Environment: Linux x86_64, Python 3.12.13, uv 0.11.21, SQLite
Branch: `bdd-refactor-login`

## Commands

```bash
uv run pytest -m unit              # 124 passed, 2 skipped
uv run pytest -m integration       # 192 passed
uv run pytest tests/e2e -v         # 28 passed
uv run pytest tests/bdd -v         # 38 passed, 1 failed
uv run pytest --durations=0 -q     # full suite (see Revisão de testes for status)
```

## Summary per group

| Grupo          | Coletados | Passaram | Falharam | Erro | Pulados | Tempo total |
|----------------|-----------|----------|----------|------|---------|-------------|
| unit           | 127       | 124      | 0        | 0    | 2       | ~1.3 s      |
| integration    | 192       | 192      | 0        | 0    | 0       | ~58 s       |
| e2e            | 28        | 28       | 0        | 0    | 0       | ~86 s       |
| bdd            | 39        | 38       | 1        | 0    | 0       | ~110 s      |
| **full suite** | **386**   | **355**  | **1**    | **28*** | **2**  | **~256 s** (sem erros de infra) |

*Os 28 erros no full suite são de infraestrutura: o Playwright Sync API falha quando o pytest roda e2e junto com outros grupos porque já existe um asyncio event loop em execução. Rodados isolados, os e2e passam.

## Top 20 mais lentos — unit

| Tempo | Teste |
|-------|-------|
| 0.08s | tests/test_phase02_tokens.py::test_class_swatches_against_bg[4] |
| 0.08s | tests/test_t06_dockerfile.py::test_prod_yml_is_valid_yaml |
| 0.06s | tests/test_phase02_tokens.py::test_legacy_aliases_intact |
| 0.05s | tests/test_phase02_tokens.py::test_class_swatches_against_bg[2] |
| 0.04s | tests/test_phase02_tokens.py::test_class_swatches_against_bg[3] |
| 0.04s | tests/test_phase02_tokens.py::test_class_swatches_against_bg[5] |
| 0.04s | tests/test_phase02_tokens.py::test_positive_ink_on_positive_passes_aa |
| 0.04s | tests/test_phase02_tokens.py::test_negative_ink_on_negative_passes_aa |
| 0.04s | tests/test_phase02_tokens.py::test_class_swatches_against_bg[6] |
| 0.04s | tests/test_phase02_tokens.py::test_error_fg_on_error_bg_passes_aa |
| 0.04s | tests/test_phase02_tokens.py::test_class_swatches_against_bg[1] |
| 0.03s | tests/test_phase02_tokens.py::test_documented_pairs_pass |
| 0.02s | setup tests/test_audit_report.py::test_render_report_contains_substring[Inventário de contraste — Omaha-title] |
| 0.01s | call tests/test_audit_report.py::test_render_report_no_failures_shows_empty_state |
| 0.01s | call tests/bdd/test_workflow_contracts.py::test_wrappers_delegate_to_workflows |

## Top 20 mais lentos — integration

| Tempo | Teste |
|-------|-------|
| 3.73s | tests/audit_integration/test_report_pipeline.py::test_generate_report_writes_file |
| 3.69s | tests/audit_integration/test_report_pipeline.py::test_cli_writes_report |
| 3.68s | tests/audit_integration/test_report_pipeline.py::test_generate_report_is_self_contained |
| 2.03s | tests/test_audit_inventory.py::test_inventory_for_dashboard_produces_rows |
| 2.02s | tests/test_audit_inventory.py::test_inventory_rows_carry_template_field |
| 1.12s | setup tests/audit_integration/test_logging_middleware.py::test_access_log_middleware_emits_http_request_line_for_get_healthz |
| 0.64s | setup tests/test_t01_assets_model.py::test_deleting_asset_class_cascades_to_assets |
| 0.64s | setup tests/test_t01_positions_model.py::test_unique_constraint_rejects_duplicate_ticker_per_asset |
| 0.64s | setup tests/test_t01_assets_model.py::test_alembic_upgrade_creates_assets_table |
| 0.63s | setup tests/test_t01_positions_model.py::test_deleting_asset_cascades_to_positions |
| 0.63s | setup tests/test_t01_classes_model.py::test_alembic_upgrade_creates_asset_classes_table |
| 0.63s | setup tests/test_t01_assets_model.py::test_repr_round_trip |
| 0.63s | setup tests/test_t01_classes_model.py::test_unique_constraint_rejects_duplicate_name |
| 0.63s | setup tests/test_t01_positions_model.py::test_deleting_profile_cascades_to_positions |
| 0.63s | setup tests/test_t01_assets_model.py::test_unique_constraint_rejects_duplicate_name_in_class |
| 0.62s | setup tests/test_t01_positions_model.py::test_alembic_upgrade_creates_positions_table |
| 0.62s | setup tests/test_t01_positions_model.py::test_repr_round_trip |
| 0.61s | setup tests/test_t01_classes_model.py::test_deleting_profile_cascades_to_asset_classes |
| 0.61s | setup tests/test_t01_assets_model.py::test_deleting_profile_cascades_to_assets |
| 0.61s | setup tests/test_t01_classes_model.py::test_repr_round_trip |

## Top 20 mais lentos — e2e

| Tempo | Teste |
|-------|-------|
| 7.22s | tests/e2e/test_s05_user_journey.py::TestS05DashboardJourney::test_dashboard_full_journey_renders_s05_polish |
| 6.04s | setup tests/e2e/test_s01_inline_edit.py::TestS01InlineEdit::test_inline_edit_asset_target |
| 5.52s | tests/e2e/test_s04_import_modal.py::TestS04ImportModal::test_import_modal_happy_path |
| 5.51s | tests/e2e/test_s04_user_journey.py::TestS04ImportJourney::test_import_journey_43_matched_5_unmatched_5_assigned_confirm_dashboard |
| 4.56s | tests/e2e/test_s10_asset_table.py::TestS10AssetTable::test_table_sort_by_each_column |
| 4.43s | tests/e2e/test_s03_user_journey.py::TestS03UserJourney::test_full_crud_journey_classes_assets_delete |
| 3.91s | tests/e2e/test_s06_full_journey.py::TestS06PosicaoItaloImport::test_import_posicao_italo_with_class_association |
| 3.77s | tests/e2e/test_s03_asset_crud.py::TestS03AssetCRUD::test_full_asset_crud_journey |
| 3.35s | tests/e2e/test_s01_inline_edit.py::TestS01InlineEdit::test_inline_edit_asset_target |
| 3.04s | tests/e2e/test_s02_class_crud.py::TestS02ClassCRUD::test_delete_class_with_assets_shows_409 |
| 2.67s | tests/e2e/test_s10_asset_table.py::TestS10AssetTable::test_modal_add_asset_flow |
| 2.66s | tests/e2e/test_s02_class_crud.py::TestS02ClassCRUD::test_delete_class_via_confirm_dialog |
| 2.60s | tests/e2e/test_s03_asset_crud.py::TestS03AssetCRUD::test_add_asset_via_modal |
| 2.50s | tests/e2e/test_s03_asset_crud.py::TestS03AssetCRUD::test_delete_asset_via_x_button |
| 2.47s | tests/e2e/test_s04_user_journey.py::TestS04ImportJourney::test_expired_preview_shows_expirado |
| 2.44s | tests/e2e/test_s04_import_modal.py::TestS04ImportModal::test_import_modal_pending_visual |
| 2.25s | tests/e2e/test_s02_class_crud.py::TestS02ClassCRUD::test_create_first_class_from_empty_state |
| 2.07s | tests/e2e/test_s10_asset_table.py::TestS10AssetTable::test_edit_alvo_pct_total_updates_class_sum_and_alert |
| 2.03s | tests/e2e/test_s10_asset_table.py::TestS10AssetTable::test_alert_card_disappears_on_convergence |
| 1.74s | tests/e2e/test_s05_visual_gate.py::TestS05VisualGate::test_capture_dashboard_polish_screenshot |

## Top 20 mais lentos — bdd

| Tempo | Teste |
|-------|-------|
| 8.29s | tests/bdd/test_scenarios.py::test_login_ok[Italo] |
| 5.20s | tests/bdd/test_scenarios.py::test_manual_add_4_assets_unequal[Italo] |
| 5.08s | tests/bdd/test_scenarios.py::test_manual_add_4_assets_unequal[Ana] |
| 4.20s | tests/bdd/test_scenarios.py::test_row_pin_preserves_visual_position[Italo] |
| 3.99s | tests/bdd/test_scenarios.py::test_row_pin_preserves_visual_position[Ana] |
| 3.96s | tests/bdd/test_scenarios.py::test_per_class_sum_off_100_accepted[Ana] |
| 3.54s | tests/bdd/test_scenarios.py::test_import_happy_auto_match[Ana] |
| 3.43s | tests/bdd/test_scenarios.py::test_per_class_sum_off_100_accepted[Italo] |
| 3.42s | tests/bdd/test_scenarios.py::test_inline_create_2_classes_soma_100[Italo] |
| 3.31s | tests/bdd/test_scenarios.py::test_per_class_sum_off_100_accepted_target_pct[Ana] |
| 3.27s | tests/bdd/test_scenarios.py::test_per_class_sum_off_100_accepted_target_pct[Italo] |
| 3.18s | tests/bdd/test_scenarios.py::test_import_happy_auto_match[Italo] |
| 3.00s | tests/bdd/test_scenarios.py::test_derived_recomputes_on_asset_patch[Italo] |
| 2.88s | tests/bdd/test_scenarios.py::test_patch_per_asset_target[Ana] |
| 2.80s | tests/bdd/test_scenarios.py::test_derived_recomputes_on_class_patch[Ana] |
| 2.79s | tests/bdd/test_scenarios.py::test_derived_recomputes_on_asset_patch[Ana] |
| 2.76s | tests/bdd/test_scenarios.py::test_inline_create_2_classes_soma_110[Italo] |
| 2.66s | tests/bdd/test_scenarios.py::test_inline_create_2_classes_soma_90[Ana] |
| 2.61s | tests/bdd/test_scenarios.py::test_inline_create_2_classes_soma_110[Ana] |
| 2.60s | tests/bdd/test_scenarios.py::test_patch_per_asset_target[Italo] |

## Oportunidades de paralelização

1. **Separar e2e e BDD do resto**: os testes de navegador (e2e + bdd) já representam ~196 s dos ~256 s totais (77%). Rodá-los em jobs separados do CI reduz o feedback loop da parte rápida (unit + integration ≈ 60 s) para menos de 1 minuto.

2. **pytest-xdist em unit/integration**: unit é barato (1.3 s) e não vale o overhead. Integration (~58 s) pode ganhar com `pytest-xdist -n auto` porque os testes usam um banco SQLite por sessão compartilhado; porém o fixture `client` é function-scoped e reutiliza o mesmo DB, então paralelização só é segura se cada worker tiver seu próprio banco de testes (fixture de escopo `session` por worker ou mudança para banco em memória por worker).

3. **BDD serial obrigatório**: o `clean_seeded_profiles` do BDD é autouse e compartilha o arquivo SQLite `data/test_bdd.db`. Não adicionar `pytest-xdist` ao BDD sem isolar o banco por worker.

4. **e2e já reaproveita o browser**: o fixture `_browser` é session-scoped; paralelização exigiria múltiplas instâncias de chromium, o que pode ser mais lento. Manter e2e serial por enquanto.

5. **Gargalos de setup no integration**: os `setup` dos model tests (T01) consomem ~0.6 s cada porque rodam `omaha_db` com alembic + seed por teste. Migrar esses testes para usar o fixture session-scoped `_omaha_test_env`/`client` (como os T02/T03) eliminaria esse custo repetido.

6. **Gargalos do audit**: `test_report_pipeline.py` gera arquivos HTML/PNG no disco (~3.7 s cada). Avaliar se os screenshots e relatórios completos são necessários em cada execução ou podem ser opt-in/tamanho reduzido.
