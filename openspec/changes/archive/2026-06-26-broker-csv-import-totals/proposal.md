## Why

O importador CSV (S04) do dashboard hoje armazena apenas
`qty`/`avg_price`/`current_price` lidos do arquivo de corretora. O
**total investido** e o **total atual** que a corretora publica no
mesmo arquivo (colunas `Total investido` e `Total atual`, prefixadas
com `R$`) **não são persistidos** — o dashboard reconstrói esses
valores multiplicando `qty × avg_price` e `qty × current_price` no
template (`dashboard.html:631,686`).

Em linhas onde o cálculo `qty × price` difere do total publicado
(arredondamento na corretora, frações de moeda em ativos fracionários
como `BTC = 0,2528`, conversão de moeda implícita em ativos
internacionais como `VT`/`QQQ`/`IAU`), o dashboard mostra um valor
distinto do que o investidor vê na planilha/corretora. Resultado
prático: o `footer` da planilha ("Total: R$ 1.017.614,61" / "R$
1.101.357,67") **nunca confere** com o total somado pelo dashboard, e
o investidor desconfia do cálculo. Exemplo concreto do fixture
`tests/posicao_italo.csv`:

- `VT`: `qty=10,9`, `cur=794,49`, arquivo `Total atual = R$ 8.658,02`,
  dashboard mostra `10.9 × 794.49 = R$ 8.659,94` (R$ 1,92 de drift).
- `BTC`: `qty=0,2528`, `cur=333.968,87`, arquivo `Total atual = R$
  84.437,99`, dashboard mostra `0.2528 × 333968.87 = R$ 84.439,37`
  (R$ 1,38 de drift — vem do arredondamento por unidade na corretora).
- `IVVB11`: `qty=127`, `cur=432,21`, arquivo `Total atual = R$
  54.890,67`, dashboard mostra `R$ 54.890,67` (bate — quando a
  corretora não arredonda).

O drift é pequeno por linha mas sistemático no portfolio inteiro:
soma dos drifts parciais diverge do footer em dezenas de reais. O
**arquivo da corretora é a fonte da verdade para o investidor** — o
dashboard precisa refletir essa fonte byte-a-byte, sem recomputar
nada internamente.

## What Changes

- Adicionar campos `total_invested` e `total_current` ao dataclass
  `RawPosition` em `src/omaha/csv_import.py`, parseados das colunas
  `Total investido` e `Total atual` do CSV (R$-prefixed, formato BR).
- Adicionar migration Alembic para duas colunas `Numeric(18, 4)` em
  `positions` (`total_invested`, `total_current`), nullable, sem
  default — o NULL sinaliza "CSV não tinha essa coluna".
- Atualizar `_detect_columns` e `_parse_data_row` para extrair e
  popular esses campos por linha do CSV. Quando a coluna não está
  presente no CSV (corretoras que não publicam totais), o campo fica
  `None` — **nenhum cálculo interno**; o dashboard exibe `0` ou `—`
  para esses casos.
- Atualizar a tabela `positions` (commit endpoint em
  `routes/imports.py`) para escrever os novos campos no INSERT/UPSERT.
- Atualizar `routes/pages.py` (cálculo de `asset_invested` /
  `asset_current`): usar **diretamente** `pos.total_invested` /
  `pos.total_current` somados por asset (sem multiplicação). Linha
  com `total_invested=None` contribui `0` para a soma.
- Atualizar `dashboard.html` (linhas 631, 686) para renderizar os
  totais vindos do backend (`row.invested`, `row.current_value`) em
  vez de recomputar `qty × price` no template.
- Atualizar fixtures e testes do `tests/test_csv_import.py` e
  `tests/test_real_csv_flow.py` para cobrir os novos campos; manter
  os testes existentes verdes.

**Garantia explícita:** nenhuma multiplicação `qty × price` em
qualquer camada (parser, commit, dashboard, template) para gerar
`invested`/`current_value`. O valor exibido é o valor que veio do CSV,
ponto.

Sem mudança no payload JSON de `/api/import/preview` e
`/api/import/commit` (os campos novos fluem como propriedades extras
do dict `RawPosition`). Sem mudança no shape do `dashboard` JSON
(`invested`/`current_value` continuam sendo as chaves; só o método
de cálculo muda).

## Capabilities

### New Capabilities

- `broker-csv-import-totals`: o parser MUST extrair `Total investido`
  e `Total atual` quando presentes no CSV (formato BR `R$`/`1.234,56`)
  e MUST expor como `RawPosition.total_invested` /
  `RawPosition.total_current`. O commit endpoint MUST persistir
  esses valores em `positions.total_invested` /
  `positions.total_current`. O dashboard MUST usar esses valores
  diretamente — sem multiplicar `qty × price` em nenhuma camada.

### Modified Capabilities

- `broker-csv-number-parsing`: requirement existente (criada em
  `fix-br-number-parser`) cobre parsing numérico dos campos
  individuais; nenhum REQUIREMENT textual muda, mas a capability
  passa a cobrir também as colunas `Total investido`/`Total atual`
  — adicionar 1 scenario cobrindo `R$ 8.658,02` → `Decimal("8658.02")`.

## Impact

- `src/omaha/csv_import.py:110` (dataclass), `:499-510`
  (`_detect_columns`), `:380-410` (`_parse_data_row`).
- `src/omaha/models.py:283-295` (Position table) — 2 colunas novas,
  nullable, sem default.
- Nova migration Alembic `0016_add_position_totals.py` (+2 colunas
  `Numeric(18,4)` nullable, sem default).
- `src/omaha/routes/imports.py:502-510` (UPSERT) — 2 colunas novas
  no SQL.
- `src/omaha/routes/pages.py:201-216` (cálculo portfolio) — somar
  `pos.total_invested` / `pos.total_current` diretamente, sem
  multiplicação.
- `src/omaha/templates/dashboard.html:631,686` — render
  `row.invested` / `row.current_value` em vez de multiplicar
  `qty × price`.
- `tests/test_csv_import.py`, `tests/test_real_csv_flow.py` — novos
  asserts para `RawPosition.total_invested`/`total_current` + asserts
  do portfolio total (somatório = `1.017.614,61` investido /
  `1.101.357,67` atual, byte-a-byte).
- Sem mudança em `scripts/seed_from_csv.py` (seed path não passa
  pelo parser — usa `Decimal(raw.strip())` direto, posições de
  seed não precisam de totais do broker).
