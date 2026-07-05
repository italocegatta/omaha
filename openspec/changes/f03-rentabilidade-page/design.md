# f03-rentabilidade-page — Design

## Context

- Página `/rentabilidade` é o stub F02 que será substituído.
- Domínio de dados:
  - `Position` (`src/omaha/models.py:306`): `qty`, `avg_price`,
    `current_price`, `imported_at`. `current_price` reflete a última
    cotação importada via CSV (ou o valor congelado, sem TTL).
  - `Quote` (`src/omaha/models.py:419`): `price`, `fetched_at`,
    `source`. Cache com TTL (`quote-cache`); histórico acumulativo.
  - `AssetClass`, `Asset`: relacionamentos via FK; agregado por classe
    já existe em `family_aggregates` / `_aggregate_assets_by_name` de
    `routes/pages.py` (F06).
- Suporte cross-cutting:
  - Read-only gate Família: `require_profile_writable` em
    `src/omaha/auth.py` retorna 409 `household_read_only` em mutações;
    leituras passam.
  - Profile routing: F07 introduziu sentinel `Família` + helper
    `_real_profiles` / `_resolve_view_mode`; bind via sentinel
    dispara `view='family'` no template.
  - Helper de agregação F06 (`family_aggregates`,
    `_aggregate_assets_by_name`, `family_asset_classes`) é reusado
    sem retrabalho quando `view='family'`.
- UI house-style: tab nav 4-tabs (`base.html` já pintada por F02);
  profile-switcher com Família como peer (F07); `patrimonio.html`
  usa hero `patrimonio-portfolio-header` (3 métricas: Investido /
  Valor Atual / Ganho).

## Goals / Non-Goals

**Goals:**
- Oferecer uma leitura de rentabilidade em **janelas temporais** fixas
  (1M / 3M / 6M / 12M / YTD / All) e uma **série mensal** de até 12
  pontos.
- Reusar infraestrutura existente: agregação F06 no modo Família,
  QuoteCache para refresh manual, gate read-only F01.
- Permanecer minimalista (sem chart lib, sem TWR/MWR).

**Non-Goals:**
- Sem gráfico de linha/candlestick.
- Sem TWR/MWR.
- Sem comparação contra benchmark (CDI/Ibovespa).
- Sem snapshot diário explícito (carrega `Position` + `Quote`).
- Sem exportação CSV.
- Sem nova coluna em tabela existente.

## Decisions

### D-F03.1 — Janelas fixas (1M / 3M / 6M / 12M / YTD / All)

Rentabilidade é calculada **para 6 janelas**, sempre ancoradas em
`now()`: janela de 1 mês (mês corrente), 3 meses, 6 meses, 12 meses,
YTD (1º de jan até hoje), All-time (desde `min(imported_at)`).

Para cada janela o sistema MUST retornar:
- `invested`: soma cumulativa de `qty * avg_price` para posições
  *cuja `imported_at <= as_of`* (somente posições ativas na data de
  corte; sem carry-over retroativo).
- `current`: soma de `qty * quote_price(ativo, as_of)` na data de
  corte.
- `gain`: `current - invested`.
- `gain_pct`: `gain / invested * 100` quando `invested > 0`; senão
  `null` (sem divisão por zero).

**Por quê:** janelas fixas evitam запрос arbitrária do usuário (sem
picker), são universais e batem com a convenção de mercado. All-time
ancora em `min(imported_at)` para evitar início artificial em
2020-01-01 quando o portfolio começou em 2024.

### D-F03.2 — Carry-forward de quote (D-F03.2)

Quando um mês da série tem **nenhuma cotação** para um dado ativo
(`Quote` rows ausentes naquele mês), o cálculo MUST usar a **última
cotação conhecida** (data anterior mais próxima com `Quote` para o
ativo). Se o ativo nunca teve cotação (caso degenerado de
`quote_kind='none'`), a posição entra na série como valor congelado
na `current_price` importada.

Janela retorna `as_of` ISO explícito e o endpoint MUST listar
`quote_stale_assets: [asset_id, ...]` para os ativos cujas cotações
são carry-forward com mais de 30 dias desde a última atualização
efetiva.

**Por quê:** a QuoteCache acumula histórico mas não garante cobertura
diária (só roda em refresh manual/automático). Carry-forward evita
linhas vazias na série sem inventar dados sintéticos; a flag
`quote_stale_assets` documenta onde o número é menos confiável.

### D-F03.3 — Granularidade mensal, 12 pontos default

Série MUST ter granularidade **mensal**, retornando um ponto por mês
(primeiro dia do mês UTC) desde o `min(imported_at)` do perfil até
`now()`. Limite máximo: 12 pontos mais recentes (`window=12`,
default). `window=all` retorna todos os pontos do histórico.

**Por quê:** PRD §1.5 "página pode ser pequena". 12 pontos cobrem
1 ano — alinhado com a maior janela de rentabilidade. Série diária
rangeria centenas de pontos para 5 anos de histórico, sem ganho
visual. Granularidade mensal é o grão útil para "como variou" sem
overhead.

### D-F03.4 — Família mode reusa agregação F06

Quando `view='family'` (querystring `?view=household` ou Família
sentinel bind via F07), a série MUST usar `family_aggregates` /
`_aggregate_assets_by_name` de `routes/pages.py`. Classes/ativos com
mesmo nome em perfis distintos colapsam em uma linha (full-join por
`name`, mesma regra de F06).

`target_pct` MUST ser omitido nas tabelas (mesma razão de F06 /
D-F06.3: alocação-alvo cross-User é ambígua).

Mutações em modo Família MUST retornar 409 `household_read_only`
(gate F01 sem retrabalho — D-F06.5). A página é read-only nesse
modo.

**Por quê:** F06 já cravou a semântica cross-User full-join. Reusar
mantém consistência com o toggle/perfil Família que o owner já viu
em Patrimônio. Sem retrabalho.

### D-F03.5 — Render sem chart library

A série MUST ser renderizada em HTML `<table>` simples
(`<thead>` + `<tbody>` com linhas por mês: data, investido, valor
atual, ganho, % ganho). Sem JS chart, sem SVG inline, sem canvas.

**Por quê:** PRD §1.5 "página pode ser pequena"; PRD §4.10 register
domestic minimal. Chart vira slice dedicada depois se virar pedido
do owner — não cabe em F03.

### D-F03.6 — Hero reusa `patrimonio-portfolio-header`

A seção superior da página MUST reusar o componente
`patrimonio-portfolio-header` (mesmo card 3 métricas: Investido /
Valor Atual / Ganho) com `window='all'` aplicado. Tabela **Por
janela** logo abaixo detalha 1M/3M/6M/12M/YTD.

**Por quê:** minimiza variação visual entre as duas páginas;
reaproveita CSS já validado pelo F02. Diferencia visual fica por
conta da tabela de janelas + série mensal.

### D-F03.7 — Endpoint signature

Dois endpoints JSON:

- `GET /api/rentabilidade/series?window=<int|all>` (default 12):
  série mensal com pontos `{date, invested, current, gain, gain_pct,
  as_of}`. Profile vem do `active_profile`/`view_mode` (NÃO do
  querystring, mesma convenção de `/api/rebalance`). Família mode
  via querystring/sentinel mesmo padrão de F06.
- `GET /api/rentabilidade/summary`: retorna `{as_of,
  windows: [...6 janelas...], classes: [{class_id, name,
  invested, current, gain, gain_pct}], quote_stale_assets: [...]}`
  para popular as 3 seções da página.

Sem método POST/PATCH. Refresh de cotação reusa o botão "Atualizar
cotações" já cabeado em `routes/quotes.py` (F01+); F03 só chama o
serviço de cotação existente (`QuoteService.refresh`).

### D-F03.8 — Refresh sob demanda opcional

A página MUST mostrar um botão "Atualizar cotações" (reusando
`/api/quotes/refresh`, fetch Alpine AJAX). Opcional clicar; render
default usa cache atual.

**Por quê:** owner rodou `task quotes-refresh` antes da seção de
rebalance; replicar affordance em Rentabilidade mantém paridade
sem introduzir novo método.

## Risks / Trade-offs

- **Quote history sparse** → carry-forward mascara buracos.
  Mitigation: flag `quote_stale_assets` sinaliza ativos com >30 dias
  sem quote fresca.
- **TWR vs retorno nominal simples** → F03 entrega variação nominal
  simples, não ponderada por fluxo. Variação nominal é mais intuitiva
  mas não desconta efeitos de aporte/resgate. Mitigation: documentar
  em DESIGN.md + spec como primeira versão; TWR vira slice futura se
  virar pedido. Janela YTD e All-time mostram o acumulado bruto, que
  é o que owner tipicamente quer ver.
- **Sem chart** → série em tabela é menos "visual". Mitigation: PRD
  já permite; chart pode entrar em slice D-pós se virar pedido.
- **Família series perde detalhe por nome** → colisão "Renda Fixa" em
  dois perfis vira 1 linha na série (mesmo trade-off documentado em
  F06 D-F06.2). Acceptable porque série é analítica, não
  operacional.
- **Carry-forward durante janela onde posição ainda não existia** →
  MUST filtrar posições cuja `imported_at <= as_of`. Sem isso, ponto
  anterior ao aporte mostraria "valor investido 0" e "valor atual
  R$1k" (errado).

## Migration Plan

Sem migration. `Position` e `Quote` já existem; nenhuma coluna nova.
A página só passa a existir quando o handler novo substituir o stub.
Rollback = restaurar `rentabilidade.html` como stub (2 linhas
incluindo bloco).

## Open Questions

- **O1.** Quando um ativo tem `quote_kind='manual'`, a cotação usada
  é a `Quote` ou a `Position.current_price`? Decisão proposta D-F03.2
  cobre: usa `Quote.fetched_at`; se ausente, fallback
  `Position.current_price`. Confirmar durante o apply.
- **O2.** Janela `1M`: "último mês corrido" (últimos 30 dias) ou "mês
  atual" (dia 1 até hoje)? Proposta: "mês atual" (1º do mês até
  `now`), consistente com YTD. Confirmar no apply via teste BDD.
