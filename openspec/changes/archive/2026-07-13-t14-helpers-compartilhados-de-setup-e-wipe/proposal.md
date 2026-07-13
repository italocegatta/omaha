## Why

As suítes e2e/bdd/visual repetem bootstrap, wipe de DB e utilitários de browser em vários `conftest.py` e no fluxo de import. A duplicação já funciona, mas cria drift fácil: qualquer ajuste de isolamento precisa ser replicado em mais de um lugar. Precisamos centralizar esses helpers sem mudar porta, DB, ordem de wipe ou comportamento dos testes.

## What Changes

- Extrair helpers compartilhados de setup e wipe para módulos de suporte comuns.
- Reduzir `tests/conftest.py`, `tests/e2e/conftest.py`, `tests/bdd/conftest.py`, `tests/visual/conftest.py` e `tests/e2e/test_import_user_journey.py` a wrappers finos sobre esses helpers.
- Centralizar primitives de wipe usadas por `scripts/seed_from_csv/modes.py` para que a lógica destrutiva fique em um único ponto, preservando semântica e saída.
- Manter inalterados: nomes de fixtures, ports, URLs, DB paths, `busy_timeout`, ordem de remoção, dados seed e asserts dos testes.
- **BREAKING**: nenhuma.

## Capabilities

### New Capabilities
- `shared-test-support`: helpers compartilhados para bootstrap de suíte, wipe de DB, browser/uvicorn e fluxo de import.

### Modified Capabilities
- `csv-seed-internals`: reorganização interna do pacote para mover primitive de wipe para helper compartilhado, sem mudar comportamento do modo `reset`.

## Impact

- Novos módulos de suporte sob `tests/support/` e `scripts/seed_from_csv/`.
- `tests/conftest.py`
- `tests/e2e/conftest.py`
- `tests/bdd/conftest.py`
- `tests/visual/conftest.py`
- `tests/e2e/test_import_user_journey.py`
- `scripts/seed_from_csv/modes.py`
