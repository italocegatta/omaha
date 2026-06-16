## 0. Crítica: entender por que os testes atuais escondem o bug

- [x] 0.1 Analisar `test_s04_t01_import_preview.py`: teste `test_preview_with_fixture_returns_correct_shape` verifica `suggested_class_id is None` — mas só porque as classes de teste não casam com o CSV. O teste PASSARIA mesmo se `suggest_class_id` fosse removida.
- [x] 0.2 Analisar `test_s04_t04_real_csv_flow.py`: mesmo padrão — 6 testes, 543 linhas, zero validação do cenário com match.
- [x] 0.3 Analisar `test_t03_imports_routes.py`: `test_review_preselects_class_via_preview_api` cria classes que casariam, mas só verifica redirect — nunca o `suggested_class_id`.
- [x] 0.4 Conclusão: testes existentes só cobrem o fluxo "None". Teste novo precisa validar o pipeline inteiro com classes que efetivamente casam.

## 1. Criar helper de classes casadas com CSV

- [x] 1.1 Criar `_create_matching_asset_classes` que cria classes `RF Pós`, `Ações` (nomes que casam com `sample_broker.csv`)
- [x] 1.2 Criar lista `_MATCHING_CLASS_ASSETS` com ativos pertencentes a essas classes, excluindo as 5 linhas unmatched

## 2. Adicionar teste de integração do cenário feliz

- [x] 2.1 Adicionar `test_preview_suggests_class_when_category_matches_class_name` em `TestPostImportPreview`
- [x] 2.2 Criar classes com `_create_matching_asset_classes`, criar assets, fazer upload do CSV
- [x] 2.3 Verificar que `suggested_class_id` das linhas com categoria `RF Pós` é o ID da classe `RF Pós`
- [x] 2.4 Verificar que `suggested_class_id` das linhas com categoria `Ações` é o ID da classe `Ações`
- [x] 2.5 Verificar que linhas com `(Não configurado)` continuam com `suggested_class_id = None`

## 3. Verificar execução

- [x] 3.1 Executar `pytest tests/test_s04_t01_import_preview.py -v` e confirmar verde
- [x] 3.2 Executar suite completa non-e2e para garantir que não há regressão
