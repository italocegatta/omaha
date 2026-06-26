## Context

A função `_parse_brazilian_number` em `src/omaha/csv_import.py:236`
é chamada por `_parse_data_row` (linhas 322-432) para converter as
células numéricas de cada linha do CSV (qty, avg_price, current_price)
em `Decimal`. A assinatura atual:

```python
def _parse_brazilian_number(s: str) -> Decimal:
    s = s.strip()
    if s == "-": return Decimal("0")
    if not s: raise InvalidOperation("empty value")
    s = _QR_PREFIX_RE.sub("", s).strip().strip('"').strip()
    has_dot = "." in s
    has_comma = "," in s
    if has_dot and has_comma:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")   # BR
        else:
            s = s.replace(",", "")                     # US
    elif has_comma:
        s = s.replace(",", ".")                       # BR decimal
    # else: only dot (or no separator) — leave as-is (US decimal)
    return Decimal(s)
```

A branch `else` (só `.`, sem `,`) trata `.` como decimal US.
Empíricamente (`uv run python`) o comportamento atual:

```
'2.466'   -> 2.466    ✗ (deveria 2466 — qty FIXA11)
'1.098'   -> 1.098    ✗
'1.234.567' -> ConversionSyntax → linha dropada
'1234.56' -> 1234.56  ✓ (US-decimal, 2 dígitos)
'0.50'    -> 0.50     ✓ (US-decimal, 2 dígitos)
'1.5'     -> 1.5      ✓
```

8 linhas de `tests/posicao_italo.csv` têm qty em BR-milhar sem
vírgula: FIXA11 (2.466), CPTS11 (3.075), RBVA11 (1.098), RBRX11
(1.797), GMAT3 (3.100), KEPL3 (1.500), WIZC3 (2.100), VAMO3
(3.800). Cada uma entra 1000× menor no DB; `total_invested` e
`total_atual` (calculados downstream como qty×avg / qty×cur)
ficam deflacionados. Colunas avg_price/current_price do mesmo
fixture passam OK porque sempre trazem `,` junto.

A suíte verde é falso-positivo:
- `tests/test_csv_import.py:181` `test_plain_number_parse` fixa o
  comportamento errado da branch only-dot (`"1234.56"` → `1234.56`).
- `tests/test_csv_import.py:301` `test_real_file_header_layout_no_name_col`
  usa qty="14" (sem separador) e qty="6.33" (US-decimal 2 dígitos).
- `tests/test_real_csv_flow.py:288` só verifica qty SMH = 14.

## Goals / Non-Goals

**Goals:**
- Branch only-dot da `_parse_brazilian_number` MUST reconhecer BR-milhar
  (`.` sozinho com grupos de 3 dígitos) e US-decimal (qualquer outra
  configuração).
- Função MUST não crashar em multi-grupo (`1.234.567`) — strippar
  pontos e parsear como inteiro.
- Heurística é determinística e pure-function (sem side-effects, sem
  locale, sem `babel`/`locale`).
- Cobertura de teste MUST incluir todas as 8 qty quebradas do fixture
  real e pelo menos 3 casos multi-grupo.

**Non-Goals:**
- Não trocar a estrutura da função nem adicionar parâmetros de hint
  por campo (qty vs price). Heurística única serve todos.
- Não adicionar lib nova (basta `Decimal` + `str.split`).
- Não alterar `_parse_data_row`, `_detect_columns` ou `parse_positions`
  — o fix é contido em `_parse_brazilian_number`.
- Não alterar o seed CSV path (`scripts/seed_from_csv.py` —
  usa `Decimal(raw.strip())` direto, não passa pelo parser).
- Não introduzir logger / warning em cells ambíguas — silent fix
  (a coluna destino no DB é Decimal, não tem como perder precisão
  no caminho feliz).
- Não cobrir formato europeu `1 234,56` (espaço como milhar) —
  nenhum broker BR usa.

## Decisions

### 1. Heurística: dígitos-depois-do-ponto em grupos de 3 = milhar

Branch only-dot reescrita como:

```python
parts = s.split(".")
if len(parts) >= 2 and all(p.isdigit() and len(p) == 3 for p in parts[1:]):
    # BR-milhar: 1.234, 1.234.567, 12.345.678,90 já tratado em branch anterior
    s = "".join(parts)
return Decimal(s)
```

A condição `all(len(p) == 3 for p in parts[1:])` exige que cada
grupo depois do primeiro tenha exatamente 3 dígitos — convenção
universal de milhar BR. Cobertura:

| Input      | Partes          | Grupos pós-0 = 3? | Resultado |
|------------|-----------------|-------------------|-----------|
| `2.466`    | `['2', '466']`  | sim (1 grupo)     | `2466` ✓  |
| `1.234.567`| `['1', '234', '567']` | sim (2 grupos) | `1234567` ✓ |
| `1234.56`  | `['1234', '56']`| não (56 ≠ 3)      | `1234.56` ✓ |
| `0.50`     | `['0', '50']`   | não               | `0.50` ✓  |
| `1.5`      | `['1', '5']`    | não               | `1.5` ✓   |
| `1.234`    | `['1', '234']`  | sim               | `1234` (BR) |

Risco residual: `"1.234"` é ambíguo (US-decimal 1.234 ou
BR-milhar 1234). Em arquivo de corretora BR, BR-milhar é a
interpretação dominante — casas decimais em preço são sempre
expressas com `,`. Default BR é a escolha certa.

**Rationale**: a heurística reflete a convenção BR (milhar em
grupos de 3) e mantém US-decimal como fallback natural. Sem
parâmetros novos, sem hint por campo.

**Alternativas consideradas**:
- Per-field hint (qty vs price) — rejeitado: adiciona parâmetro,
  duplica a chamada em `_parse_data_row`, e a heurística única já
  cobre todos os campos do BR.
- Default BR sempre (strippar todos os `.`) — rejeitado: quebra
  `0.50` → `050` = 50.
- Usar `locale.atof` — rejeitado: side-effect global, não-determinístico
  em CI, sem suporte explícito a `pt_BR` no stdlib.
- Babel `parse_decimal` — rejeitado: dep nova só para 1 função.

### 2. Crash protection para multi-grupo

Antes do fix, `"1.234.567"` crashava com `ConversionSyntax` no
`Decimal(s)` final. Caller (`_parse_data_row:369`) captura
`InvalidOperation` e devolve `None`, dropando a linha inteira em
silêncio. Pior que o bug original: linha perdida sem aviso no UI.

A heurística da Decisão 1 já cobre esse caso (multi-grupo com
todos os grupos de 3 → strippar). Sem código adicional.

**Alternativa considerada**: try/except em volta do `Decimal(s)`
com fallback para `Decimal(s.replace(".", ""))` — rejeitado:
heurística da Decisão 1 já trata todos os multi-grupo
válidos; try/except esconderia bugs reais (ex: `1.234.56` —
input genuinamente mal-formado, deve levantar).

### 3. Docstring rewrite

A docstring atual lista `"1234.56"` → `1234.56` como exemplo sem
explicitar a ambiguidade. Rewrite MUST:
- Documentar a regra geral: "quando só `.` presente, grupos de 3
  dígitos = milhar BR; caso contrário decimal US".
- Adicionar exemplos cobrindo: `"2.466"` → 2466, `"1.234.567"` →
  1234567, `"1234.56"` → 1234.56, `"0.50"` → 0.50, `"R$ 1.234,56"`
  → 1234.56.
- Remover a frase "When only one separator is present, it is
  treated as the decimal point" — essa é a regra que causou o bug.

**Rationale**: a docstring é a fonte de verdade do contrato da
função. Texto atual ensina o comportamento errado.

### 4. Cobertura de teste

Dois testes existentes precisam de atualização; dois novos casos
são adicionados:

- `test_brazilian_number_parse` ganha: `"2.466"` → 2466,
  `"1.098"` → 1098, `"1.234.567"` → 1234567, `"12.345.678"` →
  12345678.
- `test_plain_number_parse` é renomeado para `test_us_decimal_parse`
  e reduzido para o subdomínio US (`"1234.56"`, `"0.50"`,
  `"1.5"`). Mantém a sanity check de que US ainda funciona.
- Novo `test_thousands_groups_crash_protection`: `"1.234.567"` →
  1234567 (sem raise).
- Novo `TestParseRealCsv::test_parse_real_csv_br_thousands_qty`
  em `tests/test_real_csv_flow.py`: assert `parse_positions` sobre
  `tests/posicao_italo.csv` retorna `FIXA11.qty == Decimal("2466")`,
  `CPTS11.qty == Decimal("3075")`, etc. (8 asserts).

**Rationale**: cobre o subdomínio BR (que estava cego) sem perder
a sanity check US (que estava fixando o bug). Teste do fixture
real ancora o parser no comportamento de produção.

## Risks / Trade-offs

- **Risco**: `"1.234"` ambíguo, default BR pode surpreender se um
  broker US exportar CSV sem vírgula → **Mitigação**: docstring
  explicita o default; app é pt-BR only (dashboard e modal em
  português); nenhum broker BR testado exporta `1.234` como
  US-decimal.
- **Risco**: regressão em algum parser de outra rotina que
  dependa do comportamento antigo → **Mitigação**: só
  `_parse_brazilian_number` muda; grep confirma que não há outro
  caller além de `_parse_data_row` e `_count_non_numeric_unknown`.
- **Trade-off**: heurística tem 1 caso ambíguo (`.` sozinho com
  3 dígitos pós-ponto) — aceito porque o default BR é o
  comportamento correto em 99% dos arquivos de corretora brasileira.
- **Trade-off**: nenhum warning/log em cell ambíguo — aceito:
  mantém a função pure e silenciosa (consistente com o resto do
  módulo); dado destino é `Decimal` sem perda de precisão.

## Migration Plan

1. Editar `src/omaha/csv_import.py:236-280` — substituir a branch
   `else: only dot` pela heurística de grupos-de-3.
2. Editar docstring de `_parse_brazilian_number` (linhas 237-256)
   para refletir a nova regra.
3. Editar `tests/test_csv_import.py:173-184` — atualizar os dois
   testes existentes + adicionar novo teste de multi-grupo.
4. Editar `tests/test_real_csv_flow.py::TestParseRealCsv` —
   adicionar método de cobertura das 8 qty BR-milhar.
5. Rodar `uv run task test-unit` — verde (cobre só o parser).
6. Rodar `uv run task test-integration` — verde (cobre o pipeline
   preview + commit).
7. Rodar `uv run task test-e2e` — verde (cobre o modal Playwright).
8. Manual smoke: `uv run task db-reset`, abrir dashboard em
   `http://192.168.1.6:8000`, importar `tests/posicao_italo.csv`,
   verificar que FIXA11 mostra `qty = 2.466` e total calculado
   bate com o footer do broker.

Rollback: reverter os 2 arquivos (`csv_import.py` + 2 testes).
Sem migration de banco, sem dado corrompido (parser só lê CSV).

## Open Questions

- Nenhuma. As decisões cobrem os casos observados no fixture
  (`tests/posicao_italo.csv`) e os edge cases razoáveis (multi-grupo,
  US-decimal, R$ prefix). Se aparecer caso novo (ex: formato
  europeu com espaço como milhar), é enhancement separado.
