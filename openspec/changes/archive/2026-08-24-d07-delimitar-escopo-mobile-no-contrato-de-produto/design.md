## Context

D07 é uma mudança de contrato/documentação. Roadmap define aplicação posterior
limitada a `openspec/PRD.md`; nenhum runtime, teste, lane, comando, cobertura,
spec estável ou artefato deste change deve ser implementado nesta fatia.

### Code map

Não há código de produto a alterar. Estes são os documentos e símbolos exatos
que Apply deve inspecionar:

| Arquivo | Símbolo/seção | Papel no fluxo atual |
|---|---|---|
| `openspec/roadmap.md` | bloco `### D07` e dependência D07 | Fonte de escopo, arquivo permitido na aplicação futura e critérios de aceitação da fatia. |
| `openspec/PRD.md` | `§1.5 Não-objetivos`, `§3.3 Tarefas taskipy canônicas`, `§4.13 Testes — entrega só vale com suíte verde e sem máscara` | Contrato canônico de produto, entrypoints operacionais e política de aceitação/testes. |
| `tests/PERFORMANCE.md` | `Visual policy`, `## Commands`, `## Lanes de execução`, `## T32 selective-pruning record`, `## Browser lanes` | Registra desktop-only blocking visual lane, casos mobile versionados/runnable, lanes e comandos taskipy. |
| `tests/AUDIT.md` | cabeçalho de população, `## T32 selective-pruning register` | Registra população auditável, casos mobile fora da lane blocking, replacement coverage e evidência de retenção. |
| `openspec/specs/test-suite-quality/spec.md` | `Delivery gate preserves focused protection`, `Delivery gate requires full suite green`, `Canonical test bucket matrix`, `Masked-pass test constructs`, `T32 selective pruning` | Contratos estáveis de gates, lanes, cobertura, duração e proibição de mascaramento; D07 delta adiciona somente fronteira verificável de aceitação mobile. |
| `openspec/specs/dev-tasks/spec.md` | `Test coverage report` e cenários de full task/browser tasks | Mantém `uv run task test`, seis lanes, coverage assignment e comandos browser executáveis. |
| `openspec/specs/visual-regression-baseline/spec.md` | `Visual coverage SHALL include desktop and mobile viewports`, cenários `Retained desktop baselines reconcile` e `Prior mobile policy remains clean` | Contrato de viewport e histórico da remoção mobile; não será alterado por D07. |

### Current relevant flow

1. **Input:** leitura do contrato no PRD, do bloco D07 do roadmap e dos
   registros operacionais de testes acima.
2. **Transformation:** futura edição textual, mínima e localizada, em
   `openspec/PRD.md`; nenhum símbolo runtime, teste ou comando é transformado.
3. **Output:** PRD distingue explicitamente ausência de caso de uso mobile,
   não-requisito corrente de testes de browser mobile, e fronteira obrigatória
   desktop/browser.
4. **Boundaries:** testes mobile versionados continuam descobríveis e
   executáveis quando existentes; testes/lanes/comandos/cobertura não podem ser
   removidos, desabilitados, skipados, xfailed, retryados, reduzidos ou
   convertidos em passe falso. Falha mobile continua evidência, sem ocultar
   regressão desktop/browser.

## Goals / Non-Goals

**Goals:**

- Fixar contrato de produto atual: não há caso de uso mobile.
- Fixar que browser mobile não é requisito de aceitação corrente.
- Manter desktop/browser como fronteira obrigatória de aceitação.
- Preservar integralmente política de testes sem máscara, incluindo testes
  mobile versionados/runnable, seis lanes, comandos, cobertura e evidência.
- Entregar dossier implementável sem inventar alteração de código ou teste.

**Non-Goals:**

- Não afirmar que CSS, layout ou interação mobile funcionam.
- Não remover, editar ou tornar não executáveis testes mobile existentes.
- Não alterar `tests/PERFORMANCE.md`, `tests/AUDIT.md`, specs estáveis,
  `openspec/config.yaml`, `openspec/roadmap.md`, código, templates, CSS,
  browser harness, comandos ou cobertura.
- Não criar nova capability runtime nem alterar spec estável fora do delta;
  `specs/test-suite-quality/spec.md` é somente o delta verificável desta
  proposta.
- Não alterar política de duração `<=300s`, I10, matriz de buckets ou
  replacement coverage T32.

## Decisions

### D1 — Contrato fica no PRD, acompanhado por delta verificável

A aplicação futura edita somente `openspec/PRD.md`, pois roadmap define PRD como
entrega e proíbe alteração de specs estáveis nesta fatia. O delta em
`specs/test-suite-quality/spec.md` existe para tornar a fronteira verificável no
dossier e não autoriza implementação, sync ou mudança em testes nesta gate.

**Alternativa rejeitada:** modificar `visual-regression-baseline` ou
`dev-tasks` com cópias do contrato. Isso duplicaria fontes de verdade e
violaria o arquivo permitido pelo roadmap; `test-suite-quality` recebe apenas
delta verificável, sem aplicação nesta gate.

### D2 — Separar produto mobile de executabilidade da suíte

Texto futuro deve dizer, em frases distintas, que mobile não possui caso de uso
atual e que browser mobile não é requisito de aceitação corrente. Deve também
deixar explícito que isso não apaga, desabilita ou torna não-runnable qualquer
caso mobile versionado, nem muda a aceitação desktop/browser.

**Alternativa rejeitada:** dizer apenas “mobile fora do escopo”. Formulação
curta permitiria interpretar exclusão como remoção de cobertura ou como prova
de suporte mobile, ambas proibidas.

### D3 — Preservar governança vigente como invariantes

PRD deve apontar/ser compatível com §4.13 e preservar: `uv run task test` como
entrypoint canônico; seis lanes e seus comandos individuais; coverage somente
nas lanes definidas; casos mobile versionados/runnable; desktop/browser
acceptance; T32 auditável; e proibição de `skip`, `skipif`, `xfail`,
`pytest.skip`, retry, remoção de testes/lanes/cobertura e qualquer máscara.

**Alternativa rejeitada:** criar exceção de aceite mobile dentro da política de
   testes. Isso confundiria critério de produto com resultado de teste e
   enfraqueceria a regra sem máscara.

### D4 — Falha mobile permanece visível e não reclassifica falha desktop/browser

O contrato pode declarar mobile não-critical para aceitação de produto atual,
mas não pode converter falha em sucesso, esconder saída, ou permitir que
desktop/browser regressão deixe de bloquear. Qualquer ajuste futuro de
viewport, lane ou baseline exige slice própria e decisão explícita.

**Alternativa rejeitada:** remover mobile do inventário ou usar skip/xfail para
   obter passe. Contradiz `tests/AUDIT.md`, `tests/PERFORMANCE.md` e §4.13.

## Risks / Trade-offs

- **[Leitura como prova de suporte mobile]** → declarar expressamente que
  ausência de requisito não prova CSS, layout ou interação mobile.
- **[Leitura como autorização para apagar testes]** → citar preservação de
  casos versionados/runnable, lanes, comandos, cobertura e proibição de
  `skip`/`xfail`/retry/remoção.
- **[Drift entre PRD e registros operacionais]** → conferir wording contra
  `tests/PERFORMANCE.md`, `tests/AUDIT.md`, §4.13 e specs estáveis durante
  Apply/Review; não editar esses arquivos nesta change.
- **[Ambiguidade do contrato de viewport existente]** → manter intactos
  histórico T32 e matriz desktop atual; qualquer correção da spec de viewport
  é trabalho separado, não inventado neste dossier.

## Migration Plan

1. Apply lê este dossier e altera somente a seção documental apropriada de
   `openspec/PRD.md`.
2. Apply verifica diff com allow-list de um arquivo e confirma que todos os
   comandos, lanes, testes e specs estáveis permanecem intocados.
3. Apply executa apenas validações documentais/focadas definidas em `tasks.md`;
   não executa testes de implementação nem refresh de runtime.
4. Rollback: reverter apenas o hunk documental de `openspec/PRD.md`; nenhum
   banco, processo ou artefato de teste é envolvido.

## Open Questions

Nenhuma. Escopo, arquivo de aplicação futura, fronteira de aceitação e
invariantes foram definidos no bloco D07 do roadmap e na solicitação do owner.
