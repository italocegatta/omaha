## Why

Execuções MyProfit hoje deixam ciclo de job, falha sanitizada e polling
visíveis em superfícies separadas, mas não produzem evidência correlacionável
por execução. T38 cria observabilidade mínima, bounded e analisável para
decidir diagnóstico futuro sem alterar timeout, retry ou F68 deprecated.

## What Changes

- Emitir eventos estruturados por `job_id`/run para início, transições de
  estado, etapas do connector/preview, resultado terminal e duração total e
  por etapa.
- Registrar somente dimensões allowlisted e bounded: resultado, etapa, código
  sanitizado, estado, duração e sinal de que UI atingiu limite local antes do
  job terminar.
- Medir o sinal de limite local no store Alpine sem mudar `pollDelay` ou
  `maxPolls`, mantendo polling, handoff de preview, erro seguro e commit manual.
- Usar logger estruturado `omaha` existente em stdout; não criar tabela,
  arquivo, sink, serviço externo ou infraestrutura de retenção. Sinal UI usa
  somente uma fronteira autenticada de observação no próprio app.
- Criar runbook em `docs/runbooks/myprofit-sync-telemetry.md` para coleta por
  `stage/code`, distinção de connector, polling/UI, browser/processo,
  preview/handoff e concorrência, com janela de 4–8 semanas ou 4–8 execuções
  reais semanais e critério explícito para abrir diagnóstico de causa raiz.
- Adicionar oracles focados para sucesso, falha, concorrência, polling, sinal
  de limite local e ausência de dados sensíveis.

## Capabilities

### New Capabilities

- `myprofit-sync-observability`: contrato de telemetria runtime bounded e
  runbook operacional para análise de execuções MyProfit.

### Modified Capabilities

Nenhuma. O ciclo funcional de `myprofit-sync-job`, connector e `import-modal`
permanece igual; telemetria é capacidade adicional e não altera seus
requisitos de status, timeout, retry, expiração ou commit.

## Impact

- Código: pontos de coleta em `MyProfitSyncService`, connector, fronteira de
  status/polling e Alpine `patrimonioSync`; `Settings` somente se uma chave
  existente precisar ser referenciada, sem novo timeout.
- Modelo/DB: nenhum modelo, migration, tabela ou linha de produto nova.
- Logs: eventos no logger `omaha` existente, formatados pelo contrato JSON/text
  atual; aplicação não persiste nem pruna telemetria.
- Documentação: novo runbook operacional versionado.
- Testes: `tests/test_myprofit_sync_jobs.py` para backend e
  `tests/e2e/test_patrimonio_sync_action.py` para UI/polling, além de teste de
  formato/sanitização conforme oracle existente.
- Não inclui mudança em serviço externo, credencial, CSV, URL sensível,
  exceção bruta, timeout, retry, F68, T36, T37, F67 ou D06.
