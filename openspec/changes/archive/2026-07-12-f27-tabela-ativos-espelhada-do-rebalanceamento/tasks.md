## 1. Tabela patrimônio: sort + filtros

- [x] 1.1 Mapear coluna, sortKey, e filterKind da asset table de patrimônio no Alpine da seção de classe
- [x] 1.2 Implementar header controls de sort/filter e panel state por coluna, mantendo scope por class section
- [x] 1.3 Atualizar computação de `displayAssets` para aplicar filtros AND e ordering determinístico em empates

## 2. CSS: chrome da tabela espelhado do rebalance

- [x] 2.1 Ajustar shell, header band, row striping, e hover/focus da asset table para seguir padrão visual do rebalance
- [x] 2.2 Posicionar triggers e panels de filtro no header sem quebrar layout, collapse, ou inline edit existente
- [x] 2.3 Validar que nenhuma mudança atinge numeric formatting, emoji toggle, ou outros slices fora do escopo

## 3. Testes e validação

- [x] 3.1 Cobrir ordenação e filtros por coluna em patrimônio com teste browser/integration verifiable
- [x] 3.2 Cobrir parity visual básica do shell/header/body sem alterar selectors já existentes
- [x] 3.3 Rodar subset de testes alvo e revisar resultados antes de seguir para apply

## 4. Correção de follow-up

- [x] 4.1 Remover filtro de `Preço médio`, preservando ordenação por header
- [x] 4.2 Reduzir coluna `Ativo` em 25% e permitir quebra de nomes longos
- [x] 4.3 Remover filtro de `Qtd`, preservando ordenação por header

## 5. Correção de review

- [x] 5.1 Declarar formato e passo dos filtros numéricos; `Desvio` de posição usa BRL
- [x] 5.2 Trocar ícone de filtro por item do catálogo bloqueado
- [x] 5.3 Centralizar seletores E2E introduzidos pela tabela
- [x] 5.4 Usar sombra documentada de popover
- [x] 5.5 Regenerar somente baselines visuais afetadas e validar suite alvo
