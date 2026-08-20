# Desenvolvimento Agentico

## Regra padrão

Construir cada mudança como:

```text
spec -> dossiê técnico -> apply/teste focado -> review integral/suite única -> validação owner -> finalize
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
   `tasks.md` e roda exatamente uma vez `uv run task test`.
7. `review` aprova apenas suite verde em <=300s, critérios atendidos e nenhum
   finding bloqueante aberto. Só então slice vira `Applied`.
8. Apply resolve todos findings abertos da rodada juntos. Máximo duas
   remediações; falha desconhecida, decisão de escopo ou terceira rodada vira
   `Blocked` para owner.
9. Owner valida delivery manualmente antes de `finalize` arquivar e commitar.
10. Para mudança browser-visível, `apply` executa `refresh-for-test` antes de
    pedir validação owner.

Expected values devem vir da spec, regra de negócio ou oracle independente. Não
calcular expected usando mesma implementação testada.

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

## Gate de duração

`uv run task test` deve terminar em **até 300 segundos**, medidos desde início
até cleanup dos processos filhos.

- Suite verde acima de 300 segundos = falha de delivery.
- Review não aprova acima do teto.
- Finalize não arquiva acima do teto.
- Não remover testes, skips ou cobertura para caber no teto.
- Investigar gargalo e otimizar harness, isolamento, paralelismo seguro ou setup.

## Critério de pronto

```text
Spec atendida.
Teste adequado passou.
Suite completa passou.
Duração <= 300s.
Nenhum teste foi enfraquecido.
Review independente aprovou.
Owner validou antes de archive/commit.
```
