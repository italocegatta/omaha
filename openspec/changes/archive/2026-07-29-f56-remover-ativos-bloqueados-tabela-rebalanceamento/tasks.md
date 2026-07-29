## 1. Propagar `sell_enabled` até o glue

- [x] 1.1 Adicionar campo `sell_enabled: bool = True` ao dataclass `RebalanceAssetPlanRowNative` em `src/omaha/rebalance/solver_stub.py`
- [x] 1.2 Passar `sell_enabled=bool(row.get("sell_enabled", True))` em `_translate_asset_plan()` em `src/omaha/rebalance/engine.py`
- [x] 1.3 Verificar que `task test-unit` passa (campo novo com default não quebra testes existentes)

## 2. Filtrar ativos bloqueados em `glue.py`

- [x] 2.1 Em `run_rebalance()` (`src/omaha/rebalance/glue.py`), adicionar filtro no loop que constrói `asset_plan`: pular iteração quando `row.buy_enabled == False and getattr(row, 'sell_enabled', True) == False`
- [x] 2.2 Verificar que `task test-unit` passa

## 3. Testes

- [x] 3.1 Adicionar teste em `tests/test_rebalance_glue.py`: ativo com `buy_enabled=False, sell_enabled=False` NÃO aparece no `asset_plan` da resposta
- [x] 3.2 Adicionar teste: ativo com `buy_enabled=False, sell_enabled=True` APARECE no `asset_plan`
- [x] 3.3 Adicionar teste: ativo com `buy_enabled=True, sell_enabled=False` APARECE no `asset_plan`
- [x] 3.4 Adicionar teste: category_plan e metrics permanecem inalterados quando ativos são filtrados

## 4. Verificação final

- [x] 4.1 Executar `task test-unit` completo — zero regressões
- [ ] 4.2 Executar `task test-integration` se aplicável
- [x] 4.3 Verificar que specs delta refletem o comportamento implementado
