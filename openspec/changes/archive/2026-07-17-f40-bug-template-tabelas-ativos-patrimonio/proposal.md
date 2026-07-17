## Why

Três bugs visuais na tabela de ativos do patrimônio degradam a usabilidade: nomes de ativos longos não quebram linhas, colunas de desvio e percentuais não exibem conteúdo, e o painel de filtros não abre ao clicar no ícone. Todos são regressões ou omissões introduzidas após as refatorações de tabela (R30, F32, F28).

## What Changes

- **Bug 1 — Quebra de linha na coluna Ativo**: adicionar `white-space: normal` na primeira `<td>` da tabela de ativos para que nomes longos quebrem linhas em vez de transbordar. Comportamento deve se aplicar à tabela de ativos no patrimônio.
- **Bug 2 — Conteúdo ausente em colunas Classe/Desvio e Carteira/Atual/Desvio**: investigar e corrigir por que as colunas `class-deviation`, `portfolio-current` e `portfolio-deviation` não exibem valores. Possível causa: Alpine expression retorna `null`/`undefined` ou `formatDeviationPp` não está acessível no escopo do `classSection`.
- **Bug 3 — Painel de filtros não abre**: o `<th>` da tabela de ativos usa `overflow: hidden` (necessário para `text-overflow: ellipsis`), o que recorta o painel de filtro posicionado com `position: absolute`. Corrigir para que o painel escape do clipping, espelhando o comportamento da tabela de rebalanceamento.

## Capabilities

### New Capabilities

Nenhuma nova capability.

### Modified Capabilities

- `shared-table-pattern`: atualizar regras de CSS para permitir quebra de linha na coluna Ativo e corrigir overflow de painéis de filtro em `<th>` com `overflow: hidden`.
- `shared-filter-panel`: garantir que o painel de filtro funcione corretamente dentro de `<th>` com `table-layout: fixed` e `overflow: hidden`.

## Impact

- `src/omaha/static/app.css` — CSS fixes para word-break, overflow, filter panel visibility
- `src/omaha/templates/_patrimonio_class_section.html` — possível ajuste de template para filter panel positioning
- `src/omaha/templates/_patrimonio_add_asset_modal.html` — possível correção de método `formatDeviationPp` ou `filterPanelStyle` no escopo `classSection`
- Testes e2e existentes devem continuar passando (nenhum seletor muda)
