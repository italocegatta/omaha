## Why

Tabela de ativos em `/patrimonio` ainda lê como surface antiga: header/body não espelham rebalanceamento, ordenação fica menos legível, e falta filtro por coluna para scan rápido em classes grandes. Reusar UX já validada no rebalance reduz atrito sem mudar dados nem fluxo de edição.

## What Changes

- Portar para tabela de ativos em patrimônio shell visual do rebalance: header, corpo, zebra/hover e separação de regiões mais consistentes.
- Adicionar filtro por coluna na tabela de ativos, exceto `Preço médio` e `Qtd`, com affordance no header e painel de filtro no mesmo padrão do rebalance.
- Manter ordenação por clique nos headers, com comportamento e indicador alinhados ao rebalance.
- Preservar contratos existentes de inline edit, delete, add-asset, números e trade toggles. **Não** entra formatação numérica nova nem toggle de emoji.
- Sem mudança de rota, API, modelo, seed ou solver.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `dashboard-inline-editing`: contract da asset table do patrimônio ganha filtros por coluna, ordenação e tratamento visual espelhados do rebalance, sem mexer em edição inline ou dados.

## Impact

- `src/omaha/templates/_patrimonio_class_section.html`
- `src/omaha/templates/_rebalance_plan.html` (como referência de padrão visual/UX)
- `src/omaha/static/app.css`
- Testes e screenshots da tabela de ativos em patrimônio
- Sem mudanças de backend, banco, endpoints ou seed
