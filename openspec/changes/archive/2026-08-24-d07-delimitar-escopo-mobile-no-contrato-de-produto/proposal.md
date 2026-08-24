## Why

Omaha não possui caso de uso mobile atual, mas documentação de viewport e
testes versionados pode ser interpretada como requisito de produto. D07 torna
essa fronteira explícita antes da atualização correspondente do PRD, sem
confundir não-requisito corrente de browser mobile com remoção, desativação ou
mascaramento de cobertura.

## What Changes

- Registrar no contrato de produto que não existe caso de uso mobile atual.
- Declarar que testes de browser mobile não são requisito da aceitação corrente.
- Fixar desktop/browser como fronteira obrigatória da aceitação atual.
- Preservar testes mobile versionados e runnable quando existentes, lanes,
  comandos, cobertura e aceitação browser existente.
- Reafirmar proibição integral de `skip`, `skipif`, `xfail`, retry, remoção de
  testes, remoção de lanes ou redução de cobertura para fabricar passe.
- Manter failure mobile visível como evidência, sem tratá-la como passe falso
  nem permitir regressão desktop/browser oculta.
- Aplicação posterior fica limitada a `openspec/PRD.md`; esta proposta não
  autoriza alteração de código, testes, roadmap, config ou specs estáveis.

## Capabilities

### New Capabilities

Nenhuma. D07 delimita contrato de produto existente; não introduz capacidade
runtime.

### Modified Capabilities

- `test-suite-quality`: adiciona delta normativo que espelha a fronteira de
  aceitação mobile no contrato de produto, sem autorizar alteração de testes,
  lanes, comandos ou cobertura.

## Impact

- **Documentação/contrato:** aplicação posterior altera apenas
  `openspec/PRD.md`, em seção própria junto às regras de teste relevantes.
- **Testes e execução:** nenhum arquivo ou comando muda. `tests/PERFORMANCE.md`,
  `tests/AUDIT.md`, matriz de buckets, lanes, cobertura e casos mobile
  versionados permanecem fontes operacionais existentes.
- **Runtime, APIs e dependências:** nenhum impacto.
- **Delta specs:** `specs/test-suite-quality/spec.md` registra a regra
  verificável que acompanha a edição futura do PRD; não altera spec estável,
  código ou testes nesta gate.
