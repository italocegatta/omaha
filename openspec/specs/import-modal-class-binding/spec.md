# import-modal-class-binding Specification

## Purpose
TBD - created by syncing change fix-import-modal-select-binding. Update Purpose after archive.
## Requirements
### Requirement: Import modal exibe classe pré-selecionada no dropdown

O modal de import (linhas auto-matched e unmatched da tabela de revisão) DEVE exibir a classe correta já selecionada no `<select>` do DOM no momento em que o usuário vê o modal — sem que precise clicar ou rolar para descobrir.

Para linhas auto-matched, o `<select>` DEVE ter como valor selecionado o `asset_class_id` retornado pelo servidor em `auto_matched[].asset_class_id`.

Para linhas unmatched com `suggested_class_id` não-nulo, o `<select>` DEVE ter como valor selecionado o id da classe sugerida pelo servidor.

Para linhas unmatched com `suggested_class_id` nulo, o `<select>` DEVE estar em "-- escolha --" (placeholder, valor vazio) e o usuário escolhe manualmente.

#### Scenario: Auto-matched row pre-selects current class

- **WHEN** o servidor retorna `auto_matched[0].asset_class_id = 7` (classe "Ações")
- **AND** o modal renderiza a linha auto-matched
- **THEN** o `<select data-testid="import-existing-class">` dessa linha tem `value === "7"`
- **AND** a opção "Ações" aparece com `selected` no DOM

#### Scenario: Unmatched row with suggestion pre-selects suggested class

- **WHEN** o servidor retorna `unmatched[2].suggested_class_id = 2` (classe "RF Pós")
- **AND** o modal renderiza a linha unmatched
- **THEN** o `<select data-testid="import-assignment-class">` dessa linha tem `value === "2"`
- **AND** a opção "RF Pós" aparece com `selected` no DOM

#### Scenario: Unmatched row without suggestion stays on placeholder

- **WHEN** o servidor retorna `unmatched[0].suggested_class_id = null`
- **AND** o modal renderiza a linha unmatched
- **THEN** o `<select data-testid="import-assignment-class">` dessa linha tem `value === ""`
- **AND** a opção "-- escolha --" aparece com `selected` no DOM

#### Scenario: User can still override the pre-selected class

- **WHEN** o `<select>` exibe a classe pré-selecionada
- **AND** o usuário escolhe outra classe no dropdown
- **THEN** o valor do `<select>` passa a refletir a nova escolha
- **AND** a `assignments[ticker].class_id` no Alpine store é atualizada com a nova escolha
- **AND** o commit subsequente envia o id da nova classe, não da pré-selecionada

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

### Requirement: Suíte e2e é executável contra o estado pós multi-user seed

A suíte e2e (`tests/e2e/`) DEVE ser executável contra o estado
atual do seed (commit `35bf15d`, que cria os usuários `Italo` e
`Ana` em vez do legado `family`) sem erro de autenticação no
passo de login. Concretamente:

- Todos os testes que fazem `POST /login` com `username=Italo`
  (ou `username=Ana`) e a senha compartilhada da família DEVEM
  receber `303 → /profiles` e seguir adiante.
- O helper `_login_and_select_italo` em
  `tests/e2e/test_s04_user_journey.py` DEVE usar `username=Italo`
  e em seguida selecionar o profile `Italo` no picker.

#### Scenario: TestClient login com Italo redireciona para /profiles

- **WHEN** operador (ou test harness) faz `POST /login` com
  `username=Italo` + senha da família
- **THEN** resposta HTTP 303 com `Location: /profiles`
- **AND** o cookie `omaha_session` é setado

#### Scenario: TestClient login com usuário inexistente re-renderiza form

- **WHEN** operador (ou test harness) faz `POST /login` com
  `username=` (string inexistente) + qualquer senha
- **THEN** resposta HTTP 200 com form de login re-renderizado
- **AND** HTML contém `data-testid="login-error"` com a mensagem
  "Usuário ou senha inválidos"
- **AND** nenhum cookie de sessão é setado

#### Scenario: TestClient login com senha errada re-renderiza form

- **WHEN** operador (ou test harness) faz `POST /login` com
  `username=Italo` + senha incorreta
- **THEN** resposta HTTP 200 com form de login re-renderizado
- **AND** HTML contém `data-testid="login-error"` com a mensagem
  "Usuário ou senha inválidos"
- **AND** nenhum cookie de sessão é setado
- **NOTE:** este cenário é semanticamente distinto do anterior
  (usuário existe vs não existe); ambos DEVEM produzir a mesma
  resposta genérica para não vazar qual account existe.

#### Scenario: e2e Playwright login + profile picker

- **WHEN** browser acessa `/login`, preenche `username=Italo` +
  senha, submete
- **THEN** URL final é `/profiles`
- **AND** clicar no botão do profile "Italo" em `form.profile-picker`
  redireciona para `/`
