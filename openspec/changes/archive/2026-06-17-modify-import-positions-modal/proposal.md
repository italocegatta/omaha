## Why

A modal "Importar posições" do dashboard mostra colunas redundantes (`Ticker` repetido em `Nome do ativo`), não exibe o **Total atual** de cada posição (dado que o backend já calcula), tem largura insuficiente para nomes de classe longos, mistura visualmente ativos já existentes com novos, e não comunica a cor da classe escolhida — recurso já disponível no dashboard (`class-color-swatch`) e que ajuda o operador a conferir a categoria de cada ativo sem precisar abrir a seção correspondente.

## What Changes

- **Remover** as colunas `Ticker` e `Nome do ativo` das duas tabelas (auto-matched e unmatched). `broker_ticker` continua sendo usado internamente como chave do `<template x-for>` e do objeto `assignments` — só deixa de ser renderizado.
- **Adicionar** coluna `Total atual` (`R$ {qty * current_price}`, 0 casas decimais) em ambas as tabelas.
- **Renomear** o cabeçalho `P. Medio` → `Preço médio` e formatar o valor como moeda (`R$ X.XXX`, 0 casas decimais).
- **Aumentar** largura máxima do modal de `720px` para `1100px` (e ajustar o breakpoint mobile para `100%`).
- **Corrigir** ortografia nos textos exibidos: `Importar posicoes` → `Importar posições`, `posicoes` → `posições`, `Sessao` → `Sessão`, `P. Medio` → `Preço médio`, `Erro ao processar arquivo` → `Erro ao processar o arquivo`, `Erro ao confirmar importacao` → `Erro ao confirmar a importação`.
- **Reforçar** a separação visual entre as seções "Ativos existentes na carteira" e "Novos ativos" com borda lateral colorida + título estilizado por seção.
- **Colorir** o campo `Classe` com a cor da classe selecionada (incluindo o swatch ao lado do `<select>` e o destaque da `<option>` ativa), refletindo a mesma cor usada no dashboard (`style="background:{{ c.color }}"`). O backend precisa passar `color` no array `asset_classes` da resposta de `/api/import/preview` e `/api/import/preview/{preview_id}` (hoje envia só `{id, name}`).

## Capabilities

### New Capabilities

- `import-position-totals`: exibe o total atual de cada posição (qty × current_price) na tabela de revisão do modal.

### Modified Capabilities

- `import-modal`: a tabela do Step 2 perde duas colunas, ganha `Total atual`, aumenta de largura, separa visualmente as seções existentes/novos, e a coluna `Classe` reflete a cor da classe. Ortografia dos textos do modal é corrigida. O endpoint `POST /api/import/preview` (e o GET re-fecth) passam a devolver `color` em cada item de `asset_classes`.

## Impact

- Backend: `src/omaha/routes/imports.py:361` — incluir `color` (hex derivado de `_CLASS_COLORS` por índice, idêntico ao dashboard) no dict `asset_classes` retornado por `_build_preview_response`.
- Frontend: `src/omaha/templates/dashboard.html` — Alpine store `importModal` (linhas 1120-1278) e markup do Step 2 (linhas 488-576).
- CSS: `src/omaha/static/app.css:1248-1252` — `max-width` do `.import-modal-panel`; estilos novos para swatch/cor da coluna classe e separação das seções.
- Sem mudança de schema do banco: `AssetClass` não tem coluna `color`; a cor é derivada da paleta `_CLASS_COLORS` em `routes/pages.py` (índice da classe dentro do perfil), mesma fonte que o dashboard usa. O endpoint passa o hex calculado no payload.
- Sem mudança de contrato JSON a nível de cliente (apenas campo extra em `asset_classes`); clientes existentes que ignoram campos desconhecidos seguem funcionando.