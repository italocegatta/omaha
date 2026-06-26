## Context

O importador CSV do dashboard (`src/omaha/csv_import.py`) hoje extrai
5 campos numéricos por linha: `qty`, `avg_price`, `current_price`,
mais o `broker_ticker` e `name`. Os totais publicados pela corretora
(`Total investido` = `qty × avg_price` arredondado, `Total atual` =
`qty × current_price` arredondado) **não são parseados** — viraram
output calculado no template (`dashboard.html:631,686`):

```html
<td>R$ <span x-text="$store.importModal.formatBRL(Number(row.qty) * Number(row.current_price), 0)"></span></td>
```

O backend (`routes/pages.py:201-216`) também calcula via Python:

```python
asset_invested += qty * avg
asset_current += qty * cur
```

Esse caminho de cálculo é a raiz do drift observado: a corretora
arredonda cada total por linha (não é o mesmo arredondamento que
`qty × price` no Decimal), e em alguns ativos (fracionários,
internacionais com FX implícito) a diferença por linha pode chegar
a R$ 1-2. No portfolio inteiro, o footer do CSV
(`R$ 1.017.614,61` investido / `R$ 1.101.357,67` atual) **nunca
confere** com a soma exibida.

Os stakeholders são o operador (Italo) que faz upload do CSV da
corretora brasileira (B3/Avenue/NuInvest etc.) e espera ver os
mesmos números que ele vê na planilha.

Schema atual:
- `Position` (`src/omaha/models.py:249`): `qty` (Numeric 18,8),
  `avg_price` (Numeric 18,8), `current_price` (Numeric 18,8),
  `broker_ticker`, `imported_at`. Sem `total_invested` /
  `total_current`.
- `RawPosition` (`src/omaha/csv_import.py:109-130`): mesmo conjunto
  de campos, sem totais.
- `_detect_columns` (`src/omaha/csv_import.py:480-510`): reconhece
  labels de header (`_KNOWN_TICKER_LABELS`, `_KNOWN_QTY_LABELS`,
  `_KNOWN_AVG_LABELS`, `_KNOWN_CUR_LABELS`). Não reconhece labels de
  total.
- Commit endpoint (`src/omaha/routes/imports.py:502-510`): UPSERT
  na tabela `positions` com colunas `qty`, `avg_price`,
  `current_price`, `broker_ticker`, `imported_at`.

## Goals / Non-Goals

**Goals:**
- Adicionar colunas `total_invested` e `total_current` ao schema
  `positions` (Numeric 18,4 nullable, sem default).
- Adicionar campos `total_invested` e `total_current` ao
  `RawPosition` (Decimal ou None).
- O parser MUST reconhecer labels `Total investido` / `Total atual`
  no header (case-insensitive, accent-insensitive, com ou sem
  prefixo `R$`) e parsear os valores correspondentes de cada linha.
- O commit endpoint MUST persistir `total_invested` /
  `total_current` por posição.
- O dashboard MUST exibir `invested` / `current_value` diretamente
  do backend (soma de `pos.total_invested` / `pos.total_current`),
  sem multiplicar `qty × price` em nenhuma camada.
- Cobertura de teste MUST incluir asserts do somatório portfolio =
  `1.017.614,61` investido / `1.101.357,67` atual (footer do fixture
  `tests/posicao_italo.csv`, byte-a-byte).

**Non-Goals:**
- Não adicionar fallback `qty × price` quando a coluna não está
  presente. Se o CSV não publica totais, o campo fica `None` e a
  linha contribui `0` para o portfolio total. Sem inferência.
- Não recalcular totais em nenhum ponto (parser, commit, dashboard
  calc, template). Valor publicado = valor exibido.
- Não alterar `_parse_brazilian_number` (parsing numérico das
  colunas de total é idêntico ao de qualquer outro número BR).
- Não alterar `scripts/seed_from_csv.py` (caminho de seed usa
  `Decimal(raw.strip())` direto, posições de seed não precisam de
  totais do broker).
- Não fazer backfill retroativo de posições pré-existentes — colunas
  novas são nullable; posições legadas ficam com `total_invested =
  NULL`, dashboard as trata como contribuição zero (template mostra
  `R$ 0,00` ou `—`).
- Não introduzir nova lib — Decimal + regex + SQL existente cobrem
  tudo.
- Não alterar shape do JSON de `/api/import/preview` e
  `/api/import/commit` — campos novos fluem como propriedades extras
  no dict `RawPosition` (já serializado como JSON).
- Não suportar múltiplos formatos de label de total (só o formato
  padrão BR: `Total investido`, `Total atual`).

## Decisions

### 1. Numeric(18,4) nullable sem default para `total_invested` / `total_current`

A coluna destino usa `Numeric(18,4)` (4 casas decimais — casas de
centavo em BRL) nullable, sem default. NULL sinaliza "linha importada
sem essa coluna no CSV" e contribui `0` para o portfolio total no
backend. Sem default para forçar o caller a decidir (commit
endpoint sempre passa o valor ou NULL).

**Rationale**: nullable + sem default é a única forma de distinguir
"linha não tem essa coluna" (corretora X não publica) de "linha tem
a coluna com valor `R$ 0,00`" (corretora Y publica CDB zerado). O
backend trata as duas como contribuição zero, mas a auditoria futura
consegue diferenciar.

**Alternativas consideradas:**
- `Numeric(18,4) NOT NULL DEFAULT 0` — rejeitado: apaga a
  informação "linha não tem a coluna"; depois do import fica
  indistinguível de "linha tem coluna zerada".
- `Numeric(18,4) NOT NULL DEFAULT 0` + flag separado
  `has_broker_total` boolean — rejeitado: model com 2 colunas
  redundantes para o mesmo fato.
- Guardar JSON `{total_invested, total_current, source}` — rejeitado:
  shape dinâmico complica queries do dashboard e do seed
  reproduzível.

### 2. Parser: novos labels + campos opcionais no `ColumnMap` e `RawPosition`

`_detect_columns` ganha dois campos opcionais:

```python
@dataclass(frozen=True)
class ColumnMap:
    ...
    total_invested: int | None  # None quando a coluna não está no header
    total_current: int | None   # None idem
```

`_KNOWN_TOTAL_INVESTED_LABELS = ("total investido", "total aplicado",
"valor aplicado")` e `_KNOWN_TOTAL_CURRENT_LABELS = ("total atual",
"valor atual", "saldo atual")` — variações comuns em corretoras BR.

`_parse_data_row` extrai as duas colunas quando presentes; quando
ausentes, `RawPosition.total_invested = None` /
`RawPosition.total_current = None`. Os valores parseiam via
`_parse_brazilian_number` (já lida com `R$`, `1.234,56`, aspas).

**Rationale**: a estrutura atual já tem `category: int | None`
opcional em `ColumnMap` (linha 150); replicar o padrão para totais é
mecânico e consistente. Não exige refactor do detector.

**Alternativas consideradas:**
- Tornar totais obrigatórios e levantar erro se faltar — rejeitado:
  corretora X pode não publicar; quebrar import por isso é pior
  que aceitar a coluna faltando.
- Inferir do cálculo `qty × price` quando a coluna falta — rejeitado
  pelo usuário explicitamente: "eu não quero que internamente vc
  multiplique a quantidade de preço medio para chegar no valor total".
- Adicionar detecção fuzzy (similaridade de Levenshtein) — rejeitado:
  overhead sem ganho real; labels BR são padronizados.

### 3. Commit endpoint: UPSERT estendido +2 colunas

O SQL de UPSERT em `routes/imports.py:502-510` ganha
`total_invested` e `total_current` na lista de colunas e de
parâmetros. Quando o `RawPosition` tem `None`, o commit grava SQL
`NULL` (não `0`).

```sql
INSERT INTO positions (asset_id, qty, avg_price, current_price,
  broker_ticker, total_invested, total_current, imported_at)
VALUES (:asset_id, :qty, :avg_price, :current_price, :broker_ticker,
  :total_invested, :total_current, CURRENT_TIMESTAMP)
ON CONFLICT(asset_id, broker_ticker) DO UPDATE SET
  qty = excluded.qty,
  avg_price = excluded.avg_price,
  current_price = excluded.current_price,
  total_invested = excluded.total_invested,
  total_current = excluded.total_current,
  imported_at = excluded.imported_at
```

`excluded.total_invested` segue o `NULL` do INSERT — UPSERT sobrescreve
com NULL quando o novo import tem a coluna faltando.

**Rationale**: ON CONFLICT(asset_id, broker_ticker) garante idempotência
do re-import (já documentado em `fix-br-number-parser`). Estender a
lista de colunas mantém a garantia.

**Alternativas consideradas:**
- Não estender UPSERT, fazer UPDATE separado — rejeitado: 2 round-trips,
  mais código, atomicidade pior.
- Gravar `Decimal('0')` em vez de NULL quando faltando — rejeitado:
  perde a informação de "linha não tinha coluna".

### 4. Dashboard calc: somar `total_invested` / `total_current` diretamente

`routes/pages.py:201-216` substitui:

```python
asset_invested += qty * avg
asset_current += qty * cur
```

por:

```python
asset_invested += pos.total_invested or ZERO
asset_current += pos.total_current or ZERO
```

Posição com `total_invested = NULL` (legada ou CSV sem coluna)
contribui `0` para a soma do asset. Asset sem nenhuma posição com
total mostra `invested = 0` / `current_value = 0` no dashboard — não
recombina nada.

**Rationale**: a regra do usuário é "valor publicado = valor
exibido". O backend reproduz exatamente o mesmo somatório que o
operador faz na planilha. Sem multiplicação em nenhuma camada.

**Alternativas consideradas:**
- `or ZERO` via `Decimal('0')` em vez de `or ZERO` literal — mesma
  coisa, mas com type cast explícito. Mantém o padrão atual do
  módulo (`ZERO = Decimal("0")` no topo da função, linha 193).
- Multi-tier fallback (broker total → qty × price → 0) — rejeitado
  explicitamente pelo usuário.

### 5. Template: render `row.invested` / `row.current_value` (sem JS math)

`dashboard.html:631,686` substitui:

```html
<td>R$ <span x-text="$store.importModal.formatBRL(Number(row.qty) * Number(row.current_price), 0)"></span></td>
```

por:

```html
<td>R$ <span x-text="$store.importModal.formatBRL(row.current_value, 0)"></span></td>
```

`row.invested` e `row.current_value` já chegam prontos do backend.
Template não calcula nada.

**Rationale**: Alpine `x-text` recebe o valor direto. Sem `Number(...)`
e sem `*` no template. Eliminação mecânica do cálculo.

**Alternativas consideradas:**
- Manter o cálculo no JS mas ler `row.total_current` — rejeitado:
  mesma aritmética, mesma oportunidade de drift, mesma violação da
  regra do usuário.
- Criar um helper Alpine `$store.importModal.formatTotal(row)` que
  decide se usa `row.current_value` ou faz fallback — rejeitado:
  não há fallback.

### 6. Migration Alembic nova

Migration `0016_add_position_totals.py` (autogenerated) adiciona:

```python
op.add_column("positions", sa.Column("total_invested", sa.Numeric(18, 4), nullable=True))
op.add_column("positions", sa.Column("total_current", sa.Numeric(18, 4), nullable=True))
```

Sem `server_default` (deixar NULL explícito). Downgrade remove as
colunas (destructive; usuário avisado).

**Rationale**: padrão do projeto (todas as colunas adicionadas desde
S02 usam Alembic). Nullable=True é o requisito do Negócio 1.

**Alternativas consideradas:**
- `op.execute("UPDATE positions SET total_invested = qty * avg_price,
  total_current = qty * current_price")` no upgrade — rejeitado:
  reproduz exatamente o cálculo que estamos eliminando. Posições
  legadas ficam com `NULL` e contribuem `0` para o dashboard, que é
  o comportamento correto (dados antigos não têm fonte da verdade).

### 7. Sem mudança no `seed_from_csv.py`

O path de seed (`scripts/seed_from_csv.py`) usa `Decimal(raw.strip())`
direto, não passa pelo parser. Posições seedadas ficam com
`total_invested = NULL` (default da coluna nova). Dashboard mostra
`R$ 0,00` para elas — mesmo comportamento que posições importadas
de CSV sem coluna de total. Consistente.

**Rationale**: o seed path é a fonte da verdade da carteira no DB;
ele não precisa de totais do broker porque não há broker envolvido.
O cálculo interno `qty × price` que o seed path **não** faz é o que
estamos matando no resto do sistema.

**Alternativas consideradas:**
- Adicionar coluna `total_invested` / `total_current` ao CSV de seed
  — rejeitado: AGENTS.md "Seed data" rule proíbe inline seeds; CSV
  triplet sob `data/seed/` é a fonte, e adicionar colunas é uma
  mudança de schema que precisa de OpenSpec change separada.

## Risks / Trade-offs

- **Risco**: posições legadas (pré-migration) ficam com
  `total_invested = NULL`, dashboard mostra `R$ 0,00` para elas.
  → **Mitigação**: usuário roda `db-clear-assets` + novo import. O
  fixture `tests/posicao_italo.csv` traz os totais corretos;
  portfolio fica exato.
- **Risco**: corretora X publica `Total atual` em formato não-BR
  (ex: `8658.02` sem `R$`, sem milhar) → parser trata como US-decimal
  e cai no path existente (US-decimal com 2 dígitos pós-ponto).
  → **Mitigação**: `_parse_brazilian_number` já lida com ambos;
  coberto por testes existentes em `fix-br-number-parser`.
- **Risco**: drift entre `qty × avg_price` e `total_invested` em CSV
  mal-exportado (corretora bugada). Dashboard usa o total da
  corretora (fonte da verdade do investidor); ignora o cálculo.
  → **Mitigação**: o investidor confia no que vê na corretora; se a
  corretora diverge de si mesma, é problema da corretora, não nosso.
- **Trade-off**: linha com `total_invested = NULL` (CSV sem coluna)
  some do portfolio total (contribui `0`). Operador pode não
  perceber.
  → **Mitigação**: dashboard mostra `R$ 0,00` no `Total atual` da
  linha (template já trata None como zero via `or ZERO`); a soma do
  portfolio fica visível abaixo para confronto. Footnote textual
  "linhas sem total publicado contribuem 0" pode entrar em change
  futura se virar problema real.
- **Trade-off**: migration adiciona colunas sem backfill. Re-import
  é o caminho de recuperação.
  → **Mitigação**: AGENTS.md já recomenda `db-reset` ou
  `db-clear-assets` antes de qualquer delivery que mexa em
  positions; rotina estabelecida.

## Migration Plan

1. **Migration** — `uv run task db-revision -m "add position totals"`
   → `uv run task db-migrate`. Adiciona `total_invested` /
   `total_current` (Numeric 18,4, nullable, sem default).
2. **Parser** — editar `src/omaha/csv_import.py` (RawPosition +
   ColumnMap + _KNOWN_TOTAL_*_LABELS + _detect_columns +
   _parse_data_row). Sem migration.
3. **Commit endpoint** — editar
   `src/omaha/routes/imports.py:502-510` (UPSERT).
4. **Dashboard calc** — editar `src/omaha/routes/pages.py:201-216`.
5. **Template** — editar `src/omaha/templates/dashboard.html:631,686`.
6. **Testes** — adicionar asserts em `tests/test_csv_import.py`
   (parser) + `tests/test_real_csv_flow.py` (portfolio total).
7. **Verificação** — `uv run task lint` + `uv run task test-unit` +
   `uv run task test-integration` + `uv run task test-e2e`.
8. **Delivery** — `uv run task db-clear-assets` (dev DB limpo) +
   `uv run task serve` + smoke manual: import
   `tests/posicao_italo.csv`, dashboard footer =
   `R$ 1.017.614,61` investido / `R$ 1.101.357,67` atual (byte-a-byte
   com o CSV).

**Rollback**: reverter os 5 arquivos editados. Migration downgrade
remove as 2 colunas (perda de dado aceitável — o CSV original é a
fonte). Sem impacto em outros sistemas.

## Open Questions

- Nenhuma. As decisões cobrem o fixture
  (`tests/posicao_italo.csv`), os formatos BR (R$/milhares/decimal),
  e a regra explícita do usuário (sem multiplicação interna). Se
  aparecer caso novo (ex: corretora publica `Total` único sem
  separar investido/atual), é enhancement separado via novo
  OpenSpec change.
