# Roadmap

PRD: [`openspec/PRD.md`](PRD.md) (última revisão 2026-07-03).
Skill de orquestração: `openspec-roadmap`.

Roadmap é registro curto de execução. Gera `OpenSpec changes` por fatia.
Não duplicar `proposal.md` / `design.md` / `tasks.md` aqui.

## How To Use This Roadmap

1. Escolher fatia `Ready` de maior prioridade em `Recommended Execution Order`.
2. Delegar `openspec-propose` usando `Candidate OpenSpec change id` exato.
3. Mover lifecycle e atualizar `Progress` após cada gate.
4. Manter escopo limitado à fatia; mudança adicional vira nova fatia.
5. Após finalização, compactar histórico quando limite de 8 slices arquivadas
   for atingido. Preservar apenas resumo operacional e links arquivados.

Comandos: `status`, `next`, `next:dry`, `start <id>`, `add "<intent>"`,
`add-next "<intent>"`, `update <id> "<delta>"`, `block <id>`,
`deprecate <id>`, `restore <id>`, `reorder`.

## Status Model

`Ready` → `Spec Proposed` → `Applying` → `Applied` → `Archived`, mais `Blocked`.

`Applying` inclui apply e review. Apply retorna `READY_FOR_REVIEW`; somente
review `APPROVED` move fatia para `Applied`. Owner valida antes de archive e
commit. Decisões, evidências e findings vivem na change, não neste roadmap.

## Finalization and Compaction Procedure

- `propose`, `apply` e `archive` atualizam status, progress log e spec link.
- Após archive, executar verificação de specs antes de escolher próxima fatia.
- Depois de 8 slices arquivadas, mover blocos históricos detalhados para
  `Compacted history`, mantendo IDs, status, data, resultado e referência ao
  archive quando relevante.
- Não apagar histórico de forma silenciosa; não copiar artefatos da change.
- Remover fatias arquivadas da fila ativa e corrigir duplicatas ou texto stale.

## Parallelism and WIP limits

- Múltiplas fatias podem coexistir em `Spec Proposed`.
- Máximo de 2 fatias em `Applying` simultaneamente.
- Máximo de 1 fatia em `Applying` em domínio crítico.
- `next` move exatamente um gate de uma fatia.

## Spec verification gate

- Após `openspec-propose`, verificar spec antes de `openspec-apply-change`.
- Após `openspec-apply-change`, review verifica change antes de `Applied`.
- Após `openspec-archive-change`, verificar spec antes da próxima fatia.
- Falha bloqueia progressão até resolução e nova verificação.

Operacionalmente: `opsx list --specs` conforme `openspec/config.yaml`.

## Compacted history

Histórico detalhado permanece em `openspec/changes/archive/`. IDs abaixo
preservam rastreabilidade sem manter blocos de execução no roadmap.

| Encerramento | Slices | Resumo |
|---|---|---|
| 2026-07-03–07-10 | F01, F02, F05–F10, F12, R01–R06, T01–T12, I01–I04, D01–D02 | Layout principal, família, tema/tipografia/ícones, seed, quote adapter, DB guards, BDD/e2e, visual baseline, CI e documentação. Archived. F03/F04 deferred. |
| 2026-07-11–07-15 | F21–F23, F26–F29, R30–R34, I05–I06, T21–T26 | POCs e padrão de tabelas, rebalance/import automático, formatters/filtros compartilhados, hooks, poda/auditoria de testes e mutation policy. Archived. F26 split em F27–F29. |
| 2026-07-16–07-20 | F24–F25, F35–F47 | Polimento de inputs/cards, consistência de tabelas, alertas, margens, totais, colunas e filtros de patrimônio. Archived. |
| 2026-07-25–07-29 | T27–T30, F48–F56, I07, D03–D04 | Correções de suite, harness, profile OpenCode, POC MyProfit, waterfall ECharts, ordenação visual e contratos de rebalance. Archived. F49 superseded by F52; F50/F51 deprecated. |
| 2026-08-20–08-22 | F57–F61, R42, T32–T35, I08–I10 | Credenciais e automação MyProfit, jobs/preview/ação de atualização, logger, runner/harness, ownership de temporários e boundary canônico. Archived. F62, T35 e I09 deprecated/absorvidos. |
| 2026-08-23 | F64–F65, I11 | Favicon, triagem do preview de posição e diagnóstico do push. Archived; receipts e owner validation registrados nas changes. |

### Recent closure receipts

- **F65** — archived 2026-08-23; follow-up cirúrgico aprovado, focused API/E2E/lint verdes, refresh entregue.
- **I11** — archived 2026-08-23; bloqueio de push diagnosticado sem enfraquecer enforcement.
- **D06** — archived 2026-08-24; superfícies de atualização/importação inventariadas; PUSH-01 resolvido.
- **F67** — archived 2026-08-24; grupos de revisão ordenados; owner autorizou archive.
- **T36** — archived 2026-08-24; evidência não justificou mudança de timeout.
- **D07** — archived 2026-08-24; escopo mobile documentado sem mascarar testes.
- **D08** — archived 2026-08-24; runbook MyProfit concluído e sincronizado.
- **T38** — archived conforme registro em 2026-08-25; telemetria bounded + runbook, focused integration/unit/lint/spec verdes, commit `a31f77c`.

## Active slices

### T37 - Governança prática do DB E2E e processos Omaha

Status: `Archived` — 2026-08-24
Goal: tornar governança do DB E2E e processos Omaha segura e prática.
Archive: `openspec/changes/archive/2026-08-24-t37-governanca-pratica-do-db-e2e-e-processos-omaha/`

## Recommended Execution Order

**Active queue:** nenhuma slice imediata.

Order note: T38 e D08 foram finalizadas antes da compactação. Slices arquivadas
foram removidas da fila, não reabertas.

## Dependencies

- T37 dependeu de T36 archived e foi finalizada após autorização do owner.
- T36 encerrou investigação de timeout; decisão de timeout foi descartada e não
  permanece como slice ativa.
- T38 dependia de T36 e foi finalizada com D08 como runbook complementar.
- D08 dependia do contrato Applied de T38 e não altera comportamento de T38.
- F58 → F59 → F60 formaram cadeia MyProfit já arquivada.
- T34 absorveu T35/I09; T33, I08 e I10 permanecem histórico.
- F65 dependia de F59/F60 e preserva preview, confirmação e guard de Família.

## Decisions

Decisões históricas permanecem nas changes arquivadas. Últimas decisões
operacionais:

- T38 coleta telemetria bounded por 4–8 semanas/execuções reais antes de novo
  diagnóstico de causa principal; qualquer futura mudança de timeout exige nova
  demanda e nova slice.
- Compactação preserva rastreabilidade por slice e archive, sem duplicar
  `proposal.md`, `design.md` ou `tasks.md`.

## Post-implementation reality check

- Nenhuma slice em `Spec Proposed`, `Applying`, `Applied` ou `Blocked`.
- Nenhuma slice arquivada permanece na fila ativa.
- Não há archive duplicado no registro compactado.
- `openspec/config.yaml` continua fonte dos limites de token e da política de
  compactação (`compact_history_after_archived_slices: 8`).
- Registro de T38 contém data `2026-08-25`, posterior à data desta revisão;
  preservar como evidência registrada e confirmar em próxima manutenção se
  necessário.

## Checklist

- [x] PRD link no topo.
- [x] How-to, status model, WIP e spec verification gate.
- [x] Procedimento de finalização e compactação documentado.
- [x] Histórico antigo compactado após limite de 8 slices arquivadas.
- [x] Slices ativas/deferred mantidas com campos operacionais.
- [x] Candidate change ids e spec links preservados para fatias não arquivadas.
- [x] Fila ativa sem slices arquivadas.
- [x] Nenhum artefato `proposal.md` / `design.md` / `tasks.md` duplicado.
- [x] Post-implementation reality check atualizado.
