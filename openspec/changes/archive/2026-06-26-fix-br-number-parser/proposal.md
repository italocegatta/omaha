## Why

O importador CSV (S04) do dashboard trata pontos (`.`) como separador
decimal quando a célula só tem `.` (sem vírgula). Em arquivos de
corretora brasileira (formato `1.234,56`) isso é o **milhares**, não
o decimal. Resultado: células como `2.466` viram `2.466` em vez de
`2466`, deflacionando 1000× a qty de 8 posições no fixture
`tests/posicao_italo.csv` (FIXA11, CPTS11, RBVA11, RBRX11, GMAT3,
KEPL3, WIZC3, VAMO3). Bonus: `1.234.567` (multi-grupo) crasha com
`ConversionSyntax` e a linha inteira é dropada em silêncio.

A suíte de testes passa porque nenhum caso cobre qty com `.` milhar
sem vírgula — `test_plain_number_parse` chega a fixar o
comportamento errado (`"1234.56"` → `1234.56`, sem reservar o caso
BR).

## What Changes

- Reescrever a branch "only-dot" de `_parse_brazilian_number` em
  `src/omaha/csv_import.py:236` com a heurística BR: dígitos-depois-do-ponto
  em grupos de 3 = milhar; caso contrário decimal US.
- Atualizar a docstring da função com a nova regra e novos exemplos.
- Atualizar `tests/test_csv_import.py`: `test_brazilian_number_parse`
  ganha casos BR-milhar; `test_plain_number_parse` é renomeado e
  reduzido para o caso US-decimal; novo teste
  `test_thousands_groups_crash_protection` cobre `"1.234.567"` →
  `1234567`.
- Adicionar `test_parse_real_csv_br_thousands_qty` em
  `tests/test_real_csv_flow.py` validando as 8 qty quebradas do
  fixture.
- Adicionar nova capability `broker-csv-number-parsing` com
  requirements para o parser (heurística BR, US-decimal fallback,
  crash protection em multi-grupo, `R$` prefix, `,` decimal).

Sem mudança de schema, sem mudança de UI, sem mudança de payload
JSON. Endpoint `/api/import/preview` e `/api/import/commit`
continuam devolvendo o mesmo shape — só os valores numéricos saem
corretos.

## Capabilities

### New Capabilities

- `broker-csv-number-parsing`: a função `_parse_brazilian_number`
  MUST reconhecer ambos os formatos (BR `1.234,56` e US `1234.56`),
  MUST preferir BR quando o sinal for ambíguo (`.` sozinho com
  exatamente 3 dígitos depois), MUST não crashar em multi-grupo
  (`1.234.567`), e MUST strippar prefixo `R$` e aspas.

### Modified Capabilities

Nenhuma — `import-modal`, `import-class-auto-suggest`,
`import-class-color-via-css-class`, `import-modal-class-binding` e
`import-position-totals` já pressupõem qty/avg/current corretos; o
fix é puramente no parser subjacente.

## Impact

- `src/omaha/csv_import.py:236-280` — reescrita da branch
  only-dot da função `_parse_brazilian_number`. ~10 linhas
  modificadas.
- `tests/test_csv_import.py:181-184` — atualização do teste
  plain-number + novo teste thousands-groups.
- `tests/test_csv_import.py:173-178` — adição de casos BR-milhar
  no teste brazilian-number.
- `tests/test_real_csv_flow.py::TestParseRealCsv` — novo método
  cobrindo as 8 qty afetadas.
- Sem migration de banco, sem mudança de payload HTTP, sem mudança
  no dashboard template.
- Sem impacto em `scripts/seed_from_csv.py` — esse caminho não
  passa pelo parser (espera decimal limpo no CSV de seed).
