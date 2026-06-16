# import-modal-class-binding — delta spec

## ADDED Requirements

### Requirement: Real-browser E2E valida binding do <select> no modal após upload real

O `<select data-testid="import-assignment-class">` das linhas unmatched
no modal de import DEVE pré-selecionar a classe correta (a sugerida pelo
servidor via `suggested_class_id`, ou o placeholder se nula) no momento
em que o modal aparece, quando exercitado num browser real contra o
CSV `posicao_italo.csv` (8 categorias distintas).

Esta requirement existe porque o teste unitário do binding (`test_s05_*`,
`test_s06_*` em TestClient) não consegue exercitar o ciclo de vida
Alpine `x-init $nextTick` + `x-effect` que só dispara após a
renderização do `<template x-for>` interno.

#### Scenario: S06 valida binding com posicao_italo.csv real

- **WHEN** S06 (`test_s06_full_journey.py`) roda num chromium real
- **AND** o modal renderiza após upload de `posicao_italo.csv`
- **THEN** para cada linha unmatched com `suggested_class_id` não-nulo
  (Internacional, RF Pos, RF Dinamica, Acoes, FII), o
  `<select data-testid="import-assignment-class">` dessa linha tem
  `value === "<id_da_classe>"`
- **AND** para linhas com `suggested_class_id = null` (BR Dividendos,
  Cripto, Não configurado), o `<select>` tem `value === ""`
- **AND** a opção correta aparece com `selected` no DOM (sem precisar
  o usuário clicar)

#### Scenario: Padrão x-init $nextTick + x-effect sobrevive a teste real

- **WHEN** o modal é aberto (clique no botão de import)
- **AND** o CSV é enviado via `data-testid="import-file-input"`
- **AND** o servidor retorna as classes + sugestões
- **THEN** os `<select data-testid="import-assignment-class">` das
  linhas unmatched ficam com `value` correto **sem race condition**
  (a opção correspondente existe no DOM no momento do `select.value = X`)
- **AND** se o usuário escolhe outra classe manualmente via
  `@change`, a `assignments[ticker].class_id` no Alpine store é
  atualizada e persiste no commit
