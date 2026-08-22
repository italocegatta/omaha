# Desenvolvimento Agentico

## Regra padrão

Construir cada mudança como:

```text
spec -> dossiê técnico -> apply/teste focado -> review integral/suite única quando gate ativo -> validação owner -> finalize
```

Não exigir TDD mecânico para toda alteração. Usar TDD `RED -> GREEN -> REFACTOR`
quando houver regra de negócio crítica, cálculo financeiro ou bug reproduzível.

## Escolha de testes

| Mudança | Teste mínimo |
|---|---|
| Função, parser, cálculo ou regra | `unit` |
| Rota, DB, schema ou importação | `integration` |
| Jornada de usuário | `bdd` |
| Interação browser ou layout | `e2e` / `visual` |
| Rebalanceamento crítico | `unit` + mutation direcionado |

Não exigir todas as camadas para toda mudança.

## Fluxo do agente

1. `propose` produz `proposal.md`, delta spec, `design.md` e `tasks.md`.
2. `design.md` mapeia arquivos/símbolos, fluxo atual, decisões, invariantes,
   mudança por ponto, riscos e não-escopo.
3. `tasks.md` define mudança, comportamento preservado, aceite, teste focado e
   oracle independente por tarefa.
4. `apply` lê dossiê completo, faz preflight contra código real e implementa a
   menor mudança compatível. Retorna `READY_FOR_REVIEW`, nunca `Applied`.
5. `apply` registra em `design.md` decisões técnicas descobertas e em
   `tasks.md` execução, evidência e validação focada.
6. `review` audita escopo inteiro, registra em lote findings duráveis em
   `tasks.md` e roda exatamente uma vez `uv run task test` somente quando gate
   canônico está ativo; em `maintenance-suspended`, registra `NOT RUN` e audita
   evidência focada.
7. `review` aprova apenas testes de comportamento aplicáveis verdes, critérios
   atendidos e nenhum finding bloqueante aberto. Com gate canônico ativo, exige
   suite verde em <=300s; suspenso, ausência de suite é não-bloqueante.
   Só então slice vira `Applied`.
8. Apply resolve todos findings abertos da rodada juntos. Máximo duas
   remediações; falha desconhecida, decisão de escopo ou terceira rodada vira
   `Blocked` para owner.
9. Owner valida delivery manualmente antes de `finalize` arquivar e commitar.
10. Para mudança browser-visível, `apply` executa `refresh-for-test` antes de
    pedir validação owner.

Expected values devem vir da spec, regra de negócio ou oracle independente. Não
calcular expected usando mesma implementação testada.

### Contrato operacional de ownership, preflight e cleanup

Cada execução de validação mantém um ledger por run para todo recurso que cria
ou lança: processo filho/PID, grupo/PGID, porta, log, caminho temporário e
recurso de DB de teste. Cada entrada registra `resource_kind`, `resource_id`,
`owner`, `owner_evidence`, `started_at`, `ended_at`, `status`,
`classification`, `evidence` e `cleanup_result`. Owner evidence é registro
feito pelo run atual antes do uso, com identidade e timestamp; PID, PGID, nome,
porta, path, descendente ou DB path observado sozinho não prova ownership.

Classificações permitidas: `owned-current-run`, `pre-existing`, `foreign`,
`unknown`, `absent` e `owned-cleaned`.

- `apply` registra antes do uso e limpa somente entradas
  `owned-current-run`. Recurso já ausente/fechado/removido vira no-op
  idempotente registrado. Handoff precisa conter ledger, evidência, resultado,
  resíduos e decisão antes de `READY_FOR_REVIEW`.
- `review` faz preflight antes do único `uv run task test` canônico somente
  quando gate está ativo e postflight após cleanup dos lanes/processos, com
  recibo antes do veredicto. Durante suspensão, registra gate não executado e
  audita focused evidence. Para paths
  temporários, só paths exatos de run/lane declarados pelo runner são
  relevantes: match exato de receipt/ownership do run atual pode ser limpo em
  limite e vira `owned-cleaned`; path declarado exatamente ausente vira
  `absent`. Mismatch, unknown, foreign, contraditório ou incompleto dentro da
  boundary declarada fica intocado e bloqueia a operação afetada. Observação
  temporária fora de toda boundary declarada vira `preserved/non-target` e não
  bloqueia sozinha. Não inferir relevância por nome/parent, descobrir
  `pytest-of-*`, nem usar allowlist literal.
- A suite canônica de `review` exige runner isolado: preflight só é confiável
  sem processo, listener, DB de teste ou recurso temporário dentro de boundary
  declarada com estado unowned. Não existe exceção de baseline estrangeiro nem
  allowlist para recursos declarados. Ao encontrar estado relevante
  pre-existing, foreign, unknown, contraditório ou incompleto, `review`
  bloqueia antes de lançar `uv run task test`, registra inventário e evidência,
  e solicita ambiente isolado. Não adotar, matar, liberar, apagar, mascarar ou
  allowlistar recurso estrangeiro; parada segura, não limpeza do host.
- PID-not-found, PID reuse, child desaparecido e EPIPE são corridas a registrar;
  preservar falha original de lane/fail-fast/deadline e escalar quando receipt
  não for confiável. Não adotar processo/porta/path por semelhança.

Proibidos: broad kill, kill por nome/pattern, limpeza host-wide de porta,
término indiscriminado de descendentes, takeover de recurso estrangeiro,
limpeza de DB de produção ou exclusão de arquivo não registrado. Este
protocolo não autoriza operação de processo em D05; mecânica fica em I08.

Ownership não cria lane, retry, skip, máscara ou timeout novo. Permanecem
taskipy entrypoints, seis lanes (unit, integration, audit integration, e2e,
bdd, visual), fail-fast, cobertura, todos testes/skips e teto absoluto de 300s.

### Suspensão temporária I10

`maintenance-suspended` afeta somente resultado da suíte canônica paralela como
gate obrigatório apply/review/pre-push. Cada change ainda roda comandos focados
aplicáveis; testes de comportamento de produto continuam obrigatórios. `task
test` e comandos individuais permanecem disponíveis. Reativação exige resolver
diagnóstico concorrente de SQLite dinâmico readonly e timeout BDD browser, então
obter uma suíte canônica isolada verde em seis lanes e `<=300s` através cleanup.

## Registro durável da change

Artefatos OpenSpec são audit trail permanente. Não usar prompt de orquestrador
ou ledger temporário como fonte de implementação.

- `proposal.md`: intenção e escopo aprovados. Alterar apenas após autorização
  owner para mudança de escopo.
- Delta spec: contrato formal. Nunca reescrever para acomodar código.
- `design.md`: anexar `## Implementation Decisions` para descoberta técnica
  relevante, contexto, decisão, impacto e evidência.
- `tasks.md`: anexar `## Execution Evidence` e `## Review Findings`. Findings
  têm ID estável, evidência, ação exigida, escopo excluído, aceite e estado.
- Review inicial cobre toda a slice e devolve conjunto completo. Finding tardio
  exige prova de remediação causadora ou área antes `not assessable`.
- Execution/review receipt deve conservar run id, ledger completo, owner
  evidence, timestamps, classificações de resíduo, resultado de cleanup,
  decisão de stop/escalation e, no review, comando canônico, lanes, cobertura,
  skips, fail-fast, duração, teto e precondition de isolamento do runner com
  inventário de processos/listeners/temporários relevantes. Receipt ausente ou
  contraditório bloqueia; baseline ou allowlist de recurso estrangeiro é inválido.

## Gate de duração

Quando gate canônico está ativo, `uv run task test` deve terminar em **até 300
segundos**, medidos desde início até cleanup dos processos filhos. Suspensão
não relaxa esse teto; apenas torna resultado ausente não-bloqueante até
reativação.

- Suite verde acima de 300 segundos = falha de delivery quando gate ativo.
- Review não aprova acima do teto quando gate ativo.
- Finalize não arquiva acima do teto.
- Não remover testes, skips ou cobertura para caber no teto.
- Investigar gargalo e otimizar harness, isolamento, paralelismo seguro ou setup.
- Receipt registra preflight/postflight, estado de cleanup, resultado, duração
  e teto; ownership não relaxa lanes, fail-fast, cobertura, testes/skips ou
  limite, nem autoriza uma segunda suite de reparo.

## Critério de pronto

```text
Spec atendida.
Testes de comportamento aplicáveis passaram.
Suíte completa passou e duração <= 300s quando gate canônico ativo; ou receipt
`NOT RUN — maintenance-suspended` durante suspensão owner-authorized.
Nenhum teste foi enfraquecido.
Review independente aprovou.
Owner validou antes de archive/commit.
```
