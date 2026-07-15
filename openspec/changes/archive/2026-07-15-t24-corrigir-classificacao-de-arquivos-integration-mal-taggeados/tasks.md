## 1. Atualizar allow-list de markers

- [x] 1.1 Adicionar `"tests/test_admin_recovery.py"` a `_INTEGRATION_PREFIXES` em `tests/conftest.py` (posição alfabética: após `"tests/test_assets_trade_flags.py"`, antes de `"tests/test_auth.py"`)
- [x] 1.2 Adicionar `"tests/test_db_mutations.py"` a `_INTEGRATION_PREFIXES` em `tests/conftest.py` (posição alfabética: após `"tests/test_db_reset_both_profiles.py"`, antes de `"tests/test_e2e.py"`)

## 2. Verificação

- [x] 2.1 Rodar `uv run pytest tests/test_admin_recovery.py -m integration --collect-only` — confirmar que todos os testes recebem marker `integration`
- [x] 2.2 Rodar `uv run pytest tests/test_db_mutations.py -m integration --collect-only` — confirmar que todos os testes recebem marker `integration`
- [x] 2.3 Rodar `uv run pytest tests/test_admin_recovery.py tests/test_db_mutations.py -m unit --collect-only` — confirmar que ZERO testes são coletados
- [x] 2.4 Rodar `uv run task test-unit` — confirmar que os dois arquivos não aparecem mais no unit lane
- [x] 2.5 Rodar `uv run task test-integration` — confirmar que os dois arquivos rodam no integration lane e passam
- [x] 2.6 Verificar que nenhum `UnknownTestPath` warning é emitido para os dois arquivos
