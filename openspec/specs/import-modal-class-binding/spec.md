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
