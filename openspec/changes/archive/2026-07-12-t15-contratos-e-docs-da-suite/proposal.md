## Why

Docs da suíte divergiram do comportamento real de taskipy, marker logic e contratos do BDD/performance. Isso enfraquece legibilidade e confiança operacional: operador lê um guia, mas a fonte real está em `pyproject.toml` / `tests/conftest.py` / harness da suíte.

## What Changes

- Atualizar `README.md` para espelhar taskipy real, invocação canônica `task <name>` e sumário da suíte sem drift.
- Atualizar `tests/bdd/README.md` para refletir contrato real do BDD: execução serial, replay por `test-bdd-single`, threshold de extração e carve-outs.
- Atualizar `tests/PERFORMANCE.md` para virar baseline datado, com comandos e lanes coerentes com taskipy e com o comportamento atual da suíte.
- Ajustar comentários/contratos textuais em `tests/conftest.py` para deixar explícito onde mora o allow-list de markers e o aviso de caminhos novos.
- **BREAKING**: nenhuma mudança runtime; só contrato/documentação.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `readme-freshness`: README deve documentar tasks, layout e pontos de operação que batem com comportamento atual.
- `bdd-workflow-reuse`: docs do BDD devem espelhar contrato real de workflow/serialidade sem inventar comportamento.
- `test-suite-quality`: baseline/perf docs devem registrar lanes, custo relativo e limites de execução atuais.

## Impact

- `README.md`
- `tests/bdd/README.md`
- `tests/PERFORMANCE.md`
- `tests/conftest.py` (comentários/contrato textual)
- Sem mudança em runtime, deps, DB, ou behavior de app.
