## Why

F68 precisa aumentar espera do browser somente quando evidência mostrar que
`Atualizar posição` excede limite atual por motivo legítimo. Hoje fluxo tem
limites independentes — polling Alpine, expiração do job/preview e timeouts por
etapa Playwright — mas não há amostra repetida, percentis ou regra registrada
para escolher margem sem mascarar `failed`/`expired`.

## What Changes

- Adicionar harness de medição **somente em teste**, usando connector fake/mock,
  DB temporário e diretório temporário; nenhum connector real, credencial,
  rede, DB de produção ou reset destrutivo.
- Medir exatamente **15 repetições por execução**, sempre com connector
  fake/mock, e registrar `n`, sucessos, falhas, média, p50, p95,
  p99, mínimo, máximo, desvio padrão, IQR/MAD e taxa de falha.
- Inventariar limites efetivos atuais: `pollDelay × maxPolls`, job expiry,
  preview TTL/retention e timeouts Playwright independentes, sem alterá-los.
- Definir critério reproduzível de margem e valor candidato para F68, com
  decisão explícita quando limite atual já cobre p99 ou quando evidência é
  insuficiente.
- Persistir evidência de execução em `tasks.md`, em seção JSON versionada do
  change; não executar medição nesta etapa.

Não haverá alteração de timeout runtime, connector, API, modelo, template
produtivo, mensagem sanitizada, polling, status, expiração, commit manual ou
ordenação/classificação F65/D06.

## Capabilities

### New Capabilities

- `sync-duration-measurement`: contrato interno de medição repetível e offline
  para duração do job e decisão de margem; não é superfície de produto.

### Modified Capabilities

Nenhuma. Stable specs `myprofit-sync-job`, `myprofit-position-csv-connector` e
`import-modal` permanecem sem mudança de requisito. O único delta é o contrato
durável interno de teste/observabilidade acima.

## Impact

- Código de produção: nenhum arquivo alterado.
- Testes: harness explícito e isolado poderá ser adicionado a
  `tests/test_myprofit_sync_jobs.py`, arquivo já classificado como integration;
  alterações em testes E2E não fazem parte do change.
- Evidência: `openspec/changes/t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao/tasks.md`, em bloco JSON com metadados de ambiente, limites observados, amostras e decisão.
- Delta aplicável: `specs/sync-duration-measurement/spec.md`, limitado ao
  contrato interno de harness/evidência; stable product specs não mudam.
- F68 consumirá apenas critério/valor candidato aprovado; T36 não implementa
  aumento de espera.
