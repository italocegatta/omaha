## Why

`test_admin_recovery.py` e `test_db_mutations.py` usam `TestClient` + `SessionLocal` + DB wipe, mas não estão em `_INTEGRATION_PREFIXES`. Caem no default `unit` via `UnknownTestPath`. Resultado: rodam no pre-commit (unit lane) quando deveriam rodar no pre-push (integration lane). Custo: ~1.5s no gate mais frequente + classificação incorreta que viola o contrato de markers.

`test_db_snapshot.py` foi investigado — docstring diz "unit" e está correto: usa apenas `tmp_path`, cria SQLite temporários, sem `TestClient` nem `SessionLocal`. Não precisa de correção.

## What Changes

- Adicionar `"tests/test_admin_recovery.py"` a `_INTEGRATION_PREFIXES` em `tests/conftest.py`.
- Adicionar `"tests/test_db_mutations.py"` a `_INTEGRATION_PREFIXES` em `tests/conftest.py`.
- Nenhuma alteração em `test_db_snapshot.py` (genuinamente unit).

## Capabilities

### New Capabilities

Nenhuma. Correção de classificação existente.

### Modified Capabilities

Nenhuma. Os requirements existentes em `unit-test-effectiveness` e `test-suite-quality` já cobrem este caso. Este change traz o código em compliance com esses specs — não altera os specs.

## Impact

- `tests/conftest.py`: 2 linhas adicionadas a `_INTEGRATION_PREFIXES`.
- Pre-commit (unit lane): ~1.5s mais rápido (2 arquivos removidos).
- Pre-push (integration lane): 2 arquivos adicionados (~1.5s de custo absorvido pelo gate paralelo).
- Nenhum impacto em código de produção, rotas, templates ou seed.
