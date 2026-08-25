## Why

O harness E2E já registra processos, portas, DBs e receipts, mas recuperação
operacional ainda mistura recurso efêmero conhecido com ownership de execução.
Isso torna stale process, DB E2E residual e restart do servidor Omaha difíceis de
resolver sem risco de adotar ou apagar recurso estrangeiro. T37 transforma essa
fronteira em protocolo executável e auditável, sem alterar comportamento do
produto.

## What Changes

- Tornar preflight prático e bounded: inventariar somente portas, processos,
  grupos, logs, temporários e DBs canônicos declarados pelo runner.
- Definir ownership por identidade composta de run/lane, PID/PGID, comando,
  cwd, porta, DB e timestamps; nome `uvicorn`, PID, porta ou caminho isolado
  nunca bastam sozinhos.
- Separar `data/test_e2e.db` como DB de teste efêmero e recriável, com
  disposição explícita de recreate para caminho exato e regular, sem adotar
  estado de processo estrangeiro; manter `data/portfolio.db` protegido e
  intocável.
- Formalizar cleanup idempotente e bounded: graceful stop, espera limitada,
  escalada somente para grupo current-run-owned e recuperação de stale process
  somente após diagnóstico de identidade; recurso estrangeiro permanece vivo.
- Fazer readiness, restart e teardown emitirem receipts de processo Omaha,
  owner, DB, porta, log, sinal, retorno, residue e resultado final.
- Adicionar oráculos focados para preflight, ownership, recreate seguro,
  identificação de processo, restart gracioso, receipts completos e stale
  recovery, preservando seis lanes, fail-fast, coverage, skips e teto de 300 s.

### Non-goals

- Não alterar produto, rotas, modelos, migrations, seed CSV, UI, APIs ou
  comportamento de negócio.
- Não executar cleanup host-wide, `kill` por nome/pattern, adoção de recurso
  estrangeiro, scan amplo de `/tmp`, ou alteração de `data/portfolio.db`.
- Não reabrir nem modificar escopo de T36, F67, D06, T38 ou D08.
- Não trocar taskipy entrypoints, remover lanes/testes, mascarar falhas,
  adicionar retry/skip/xfail ou relaxar teto de duração.

## Capabilities

### New Capabilities

Nenhuma. T37 concretiza e amplia contratos de governança de harness já
existentes.

### Modified Capabilities

- `test-run-ownership-contract`: preflight operacional, identidade de processo,
  recreate explícito de DB efêmero, stale recovery, restart e receipts.
- `dev-tasks`: runner canônico deve aplicar essas decisões antes, durante e
  depois das seis lanes, sem tocar DB de produção.
- `shared-test-support`: helpers de DB e servidor devem publicar identidade,
  restart gracioso, teardown bounded e receipts reconciliáveis.
- `e2e-fixture-isolation`: `data/test_e2e.db` deve ser tratado como alvo E2E
  recriável, preservando o mesmo arquivo durante cada fixture e bloqueando
  qualquer confusão com `data/portfolio.db`.

## Impact

- **Harness:** `scripts/run_full_suite.py` ganha decisões explícitas para
  preflight, lifecycle, receipts e reconciliação.
- **Suporte de testes:** `tests/conftest.py`, `tests/support/db.py` e
  `tests/support/server.py` alinham receipts de DB, temporário e processo.
- **Oráculos:** `tests/scripts/test_t29_harness.py` cobre cenários positivos,
  foreign/stale/contradictory e no-op; nenhum teste de produto é alterado.
- **Operação:** apply/review recebem evidência concreta de ownership,
  cleanup/recreate, restart e recuperação; canonical full suite continua
  sujeito à política `maintenance-suspended` vigente em `openspec/config.yaml`.
