## 1. Patrimônio: ganho e densidade

- [x] 1.1 Consolidar `Ganho` em célula única na tabela de ativos de `_patrimonio_class_section.html`, preservando testids, sign classes e leitura PT-BR.
- [x] 1.2 Ajustar comparator de ordenação para `Ganho` usar magnitude absoluta como chave principal, com desempate estável.
- [x] 1.3 Atualizar formatadores numéricos usados no patrimônio para 0 casas decimais em valores monetários e quantidades, com BTC em 3 casas.
- [x] 1.4 Revisar `src/omaha/static/app.css` para manter largura, alinhamento e densidade após fusão da coluna de ganho.

## 2. Rebalanceamento: quantidade compacta

- [x] 2.1 Ajustar formatação de `trade_quantity` em `_rebalance_plan.html` / `rebalance.html` para 3 casas em BTC e 0 casas nos demais ativos.
- [x] 2.2 Confirmar que a célula de operação continua unificada (`ação + valor + quantidade`) e que empty-state segue intacto.

## 3. Verificação

- [x] 3.1 Atualizar ou adicionar testes focados para ordenação por ganho absoluto e precisão de BTC.
- [x] 3.2 Executar suíte alvo via taskipy nos fluxos afetados (`task test-unit` e/ou subset integrado relevante).

## 4. Reparo de revisão

- [x] 4.1 Remover clipping dos painéis de filtro da tabela de ativos sem alterar tabela de rebalanceamento.
- [x] 4.2 Adicionar filtros range de `Qtd` e `Preço médio` ao modelo de filtros da tabela de ativos.
- [x] 4.3 Restringir percentuais arredondados às seis colunas pedidas e alinhar spec delta.
- [x] 4.4 Cobrir ordenação de magnitude de ganho, quantidade BTC/não-BTC e filtros numéricos em browser.
- [x] 4.5 Corrigir feedback da segunda revisão: scroll horizontal com popover visível, labels BTC, `0%` normalizado e desvio total arredondado.
- [x] 4.6 Corrigir feedback da revisão final: valores-alvo numéricos `0` renderizam `0%`; `—` fica para valor ausente ou inválido.
