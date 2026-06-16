## Purpose

Inline asset class and asset management on the dashboard — edit target
percentages, add/remove assets, remove classes, and collapse sections
without leaving the dashboard view. Replaces the standalone editor
pages.

## Requirements

### Requirement: Inline editing de target % da classe

O dashboard DEVE permitir editar o target % de uma classe clicando no valor percentual,
que se transforma em input inline. O save faz PATCH /api/classes/{id} e atualiza o
valor local sem recarregar a página.

#### Scenario: Clique no % abre input inline

- **WHEN** usuário clica no target % da classe (data-testid="class-target-pct-view")
- **THEN** o span some e um input numérico (data-testid="class-inline-edit-input") aparece
- **AND** o input contém o valor atual preenchido

#### Scenario: Enter salva e atualiza localmente

- **WHEN** usuário digita novo valor e pressiona Enter
- **THEN** PATCH /api/classes/{id} é enviado
- **AND** em caso de 200, o valor local (classTargetPct) é atualizado
- **AND** o input some e o novo valor aparece no span

### Requirement: Remoção de classe com confirmação

O dashboard DEVE exibir botão × no header da classe que, ao clicar, mostra confirmação
"Remover classe {nome}?". Confirmar faz DELETE /api/classes/{id} e recarrega a página.

#### Scenario: Confirmar exclusão recarrega

- **WHEN** usuário clica × (data-testid="class-delete-btn")
- **THEN** div de confirmação (data-testid="class-delete-confirm") aparece
- **AND** ao clicar "Sim, remover", DELETE /api/classes/{id} é enviado
- **AND** em 204, página recarrega

### Requirement: Remoção de ativo com confirmação

O dashboard DEVE exibir botão × por ativo que, ao clicar, mostra confirmação
"Remover ativo {nome}?". Confirmar faz DELETE /api/assets/{id} e recarrega a página.

#### Scenario: Confirmar exclusão de ativo recarrega

- **WHEN** usuário clica × no ativo (data-testid="dashboard-asset-delete-btn")
- **THEN** div de confirmação (data-testid="dashboard-asset-delete-confirm") aparece
- **AND** ao clicar "Sim, remover", DELETE /api/assets/{id} é enviado
- **AND** em 204, página recarrega
- **AND** em 409, exibe erro (classe tem posições)

### Requirement: Criação inline de ativo

O dashboard DEVE exibir botão "+ Ativo" por classe que, ao clicar, mostra formulário
inline com campos nome + target %. Salvar faz POST /api/assets e recarrega a página.

#### Scenario: Formulário inline cria ativo e recarrega

- **WHEN** usuário clica "+ Ativo" (data-testid="dashboard-add-asset-btn")
- **THEN** formulário inline aparece com campos nome + target %
- **AND** ao clicar "Salvar", POST /api/assets é enviado
- **AND** em 201, página recarrega
- **AND** em 409/422, exibe erro no formulário

### Requirement: Seções colapsáveis

Cada classe no dashboard DEVE ser colapsável via chevron no header. O estado default
é fechado (D016).

#### Scenario: Chevron expande/recolhe seção

- **WHEN** usuário clica no chevron (data-testid="class-chevron")
- **THEN** a seção de assets da classe expande/recolhe
- **AND** o chevron gira visualmente (classe CSS .is-open)

### Requirement: Total da soma de classes

O dashboard DEVE exibir a soma total dos target % de todas as classes no topo da
seção de distribuição, atualizando reativamente via Alpine store `classSum` conforme
o usuário edita valores inline.

#### Scenario: Soma aparece e reage a edições

- **WHEN** há classes cadastradas
- **THEN** o total (data-testid="class-summary-total") exibe a soma dos target %
- **AND** se a soma for diferente de 100%, exibe delta "Falta X%" ou "Sobra X%"
- **AND** quando usuário edita um target %, o total reatualiza sem recarregar
