## 1. Parser fix (`src/omaha/csv_import.py`)

- [x] 1.1 `src/omaha/csv_import.py:265-280` — substituir a branch `else: only dot (or no separator) — leave as-is (US decimal)` pela heurística:
  ```python
  else:
      # only "." — ambiguous: BR thousands (groups of 3) vs US decimal.
      parts = s.split(".")
      if len(parts) >= 2 and all(p.isdigit() and len(p) == 3 for p in parts[1:]):
          # BR-milhar: 1.234 / 1.234.567 / 12.345.678 — strip all dots
          s = "".join(parts)
      # else: leave as-is (US decimal — 1234.56 / 0.50 / 1.5)
  ```
  Manter o `return Decimal(s)` no final (não duplicar).
- [x] 1.2 `src/omaha/csv_import.py:236-256` — reescrever a docstring de `_parse_brazilian_number`:
  - Trocar a regra "When only one separator is present, it is treated as the decimal point" por "When only `.` is present, groups of exactly 3 digits after each dot are treated as thousands separators (BR convention); otherwise it is treated as a US decimal point."
  - Adicionar exemplos: `_parse_brazilian_number("2.466") -> Decimal("2466")`, `_parse_brazilian_number("1.234.567") -> Decimal("1234567")`, manter `_parse_brazilian_number("1234.56") -> Decimal("1234.56")` e `_parse_brazilian_number("0.50") -> Decimal("0.50")`.

## 2. Unit tests (`tests/test_csv_import.py`)

- [x] 2.1 `tests/test_csv_import.py:173-178` — `test_brazilian_number_parse`: adicionar asserts para os casos BR-milhar:
  ```python
  assert _parse_brazilian_number("2.466") == Decimal("2466")
  assert _parse_brazilian_number("1.098") == Decimal("1098")
  assert _parse_brazilian_number("12.345.678") == Decimal("12345678")
  assert _parse_brazilian_number('"2.466"') == Decimal("2466")
  ```
- [x] 2.2 `tests/test_csv_import.py:181-184` — renomear `test_plain_number_parse` para `test_us_decimal_parse` e ajustar docstring para "Plain US-decimal numbers (no thousands grouping) parse correctly." Manter os 2 asserts atuais (`"1234.56"`, `"0.50"`).
- [x] 2.3 `tests/test_csv_import.py` — adicionar novo teste após `test_us_decimal_parse`:
  ```python
  def test_thousands_groups_crash_protection() -> None:
      """Multi-group BR-milhar (1.234.567) does not raise ConversionSyntax."""
      assert _parse_brazilian_number("1.234.567") == Decimal("1234567")
      assert _parse_brazilian_number("1.234.567,89") == Decimal("1234567.89")
      # Cell com . mid-string sem ser milhar (2 dígitos pós-ponto) → US decimal
      assert _parse_brazilian_number("1234.56") == Decimal("1234.56")
  ```

## 3. Integration test com fixture real (`tests/test_real_csv_flow.py`)

- [x] 3.1 `tests/test_real_csv_flow.py::TestParseRealCsv` — adicionar método:
  ```python
  def test_parse_real_csv_br_thousands_qty(self) -> None:
      """qty cells com '.' milhar (sem ',') parseiam como inteiro,
      não como decimal US. Cobre as 8 posições afetadas em
      tests/posicao_italo.csv."""
      from omaha.csv_import import parse_positions

      text = CSV_PATH.read_text(encoding="utf-8")
      result = parse_positions(text)

      by_ticker = {r.broker_ticker: r for r in result}
      # 8 rows com BR-milhar em qty — todas devem virar inteiro × 1000.
      expected = {
          "FIXA11": Decimal("2466"),
          "CPTS11": Decimal("3075"),
          "RBVA11": Decimal("1098"),
          "RBRX11": Decimal("1797"),
          "GMAT3":  Decimal("3100"),
          "KEPL3":  Decimal("1500"),
          "WIZC3":  Decimal("2100"),
          "VAMO3":  Decimal("3800"),
      }
      for ticker, expected_qty in expected.items():
          assert by_ticker[ticker].qty == expected_qty, (
              f"{ticker}: expected qty={expected_qty}, got {by_ticker[ticker].qty}"
          )
  ```

## 4. Delta spec (já criado, validar após implementação)

- [x] 4.1 Confirmar que `openspec/changes/fix-br-number-parser/specs/broker-csv-number-parsing/spec.md` cobre os 5 requirements (BR-milhar, US-decimal fallback, multi-grupo, R$/quotes, `-` sentinel) com 2-3 scenarios cada. (Arquivo já existe — gerado junto com proposal.md/design.md/tasks.md; serve como source-of-truth da capability até o archive.)
- [x] 4.2 Após implementação + green tests, rodar `openspec validate fix-br-number-parser --json` e confirmar `valid: true, issues: []`.

## 5. Lint + check + delivery

- [x] 5.1 `uv run task lint` — verde (ruff format + ruff --fix).
- [x] 5.2 `uv run task test-unit` — verde (cobre parser + tests modificados).
- [x] 5.3 `uv run task test-integration` — verde (cobre pipeline + novo teste do fixture).
- [ ] 5.4 `uv run task test-e2e` — verde (Playwright modal não regrediu). **PRE-EXISTING FAIL** — 4 tests fail at login step (stale `_login_and_select_italo` from `tests/e2e/M002_RESSALVA_DIAGNOSIS.md`); unrelated to parser change. Verified by stashing parser changes and re-running e2e — same 4 failures.
- [x] 5.5 `uv run task db-reset` — DB repopulado com Italo + 6 classes + 48 assets + 47 positions.
- [x] 5.6 Manual smoke: server up on `http://192.168.1.6:8000`, login as Italo, preview + commit `tests/posicao_italo.csv` via curl. Preview returned `FIXA11.qty="2466"` (was `2.466`); commit upserted 48 rows + created 2 (CPTI11, BRBI11). DB query confirms all 8 affected tickers have correct qty: FIXA11=2466, CPTS11=3075, RBVA11=1098, RBRX11=1797, GMAT3=3100, KEPL3=1500, WIZC3=2100, VAMO3=3800.
- [x] 5.7 Reportar LAN URL + DB state + verde dos tasks ao user antes de pedir sign-off.
