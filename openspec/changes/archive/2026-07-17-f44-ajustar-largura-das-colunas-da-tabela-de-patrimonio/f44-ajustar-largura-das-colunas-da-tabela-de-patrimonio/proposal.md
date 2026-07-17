## Why

As colunas da tabela de patrimônio não otimizam o espaço horizontal. Colunas como "Posição", "Classe/Atual", "Classe/Alvo", "Carteira/Atual" e "Carteira/Alvo" ocupam mais espaço do que necessário, enquanto a coluna "Ativo" fica comprimida com nomes longos que precisam quebrar linha.

## What Changes

- Ajustar variáveis CSS `--col-*` em `:root` para otimizar largura das colunas
- Aumentar largura da coluna "Ativo" (~20-25%) para acomodar nomes longos
- Reduzir largura das colunas de percentual em 10-20% (Posição, Classe/Atual, Classe/Alvo, Carteira/Atual, Carteira/Alvo)
- Reduzir largura das colunas de desvio em 5-10% (Classe/Desvio, Carteira/Desvio)
- Manter `table-layout: fixed` para controle preciso de larguras

## Capabilities

### New Capabilities

Nenhuma nova capacidade — é otimização de layout existente.

### Modified Capabilities

Nenhuma capacidade com mudança de requisito. Apenas ajuste de apresentação.

## Impact

- Arquivo: `src/omaha/static/app.css` (linhas 1690-1705, variáveis CSS `--col-*`)
- Sem mudança de comportamento, backend, ou testes
- Sem breaking changes
- Impacto visual: tabela fica mais equilibrada horizontalmente
