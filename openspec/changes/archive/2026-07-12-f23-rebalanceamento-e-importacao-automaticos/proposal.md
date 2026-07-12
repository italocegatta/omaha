## Why

Rebalanceamento e importação ainda pedem clique manual extra para avançar. Isso quebra fluxo de ação imediata, aumenta atrito, e deixa operador esperar mais do que precisa para ver plan ou preview atualizado.

## What Changes

- Rebalanceamento recalcula plan quando operador confirma aporte ou thresholds com Enter, sem botão "Rebalancear" visível.
- Import CSV dispara preview automaticamente ao selecionar arquivo, sem botão "Enviar" no step 1.
- Review/commit do import continua após preview bem-sucedido; só etapa de disparo inicial muda.
- **BREAKING**: remove affordance manual que hoje dispara recálculo/importação.

## Capabilities

### New Capabilities
- Nenhuma.

### Modified Capabilities
- `rebalance-page`: comportamento de UI muda para refresh no Enter do plan em vez de botão manual.
- `import-modal`: step 1 muda para upload automático no `change` do input file, sem botão manual de envio.

## Impact

Templates `rebalance.html` e `_patrimonio_add_asset_modal.html`, JS Alpine embutido, CSS da barra de parâmetros/modal, rotas de página em `src/omaha/routes/pages.py`, e suites de teste/e2e que hoje assumem botão manual.
