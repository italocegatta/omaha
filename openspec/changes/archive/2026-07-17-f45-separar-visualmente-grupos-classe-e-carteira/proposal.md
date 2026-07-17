## Why

A linha de borda entre os cabeçalhos agrupados "Classe" e "Carteira" na tabela de patrimônio é contínua, dificultando a distinção visual entre os dois grupos. O usuário precisa identificar rapidamente onde termina um grupo e começa o outro.

## What Changes

- Adicionar classes CSS para separar visualmente os grupos "Classe" e "Carteira"
- Criar uma quebra na borda inferior entre os dois grupos de cabeçalho
- Usar border-right no "Classe" e border-left no "Carteira" para criar separação visual
- Alternativa: gap/padding entre os grupos para criar espaço visual

## Capabilities

### New Capabilities

Nenhuma nova capacidade — é correção visual de UI existente.

### Modified Capabilities

Nenhuma capacidade com mudança de requisito. Apenas ajuste de apresentação.

## Impact

- Arquivos: `src/omaha/templates/_patrimonio_class_section.html` (linhas 109-110) + `src/omaha/static/app.css`
- Sem mudança de comportamento, backend, ou testes
- Sem breaking changes
- Impacto visual: separação clara entre grupos de colunas
