# import-class-auto-suggest — delta spec

## ADDED Requirements

### Requirement: Real-browser E2E valida suggest_class_id contra posicao_italo.csv

O sistema DEVE passar o teste `tests/e2e/test_s06_full_journey.py` num
chromium real contra um uvicorn real, exercitando o pipeline completo
de import com o CSV real do operador (`tests/fixtures/posicao_italo.csv`,
8 categorias distintas: Internacional, RF Pos, RF Dinamica, Acoes, FII,
BR Dividendos, Cripto, Nao configurado).

A infraestrutura de teste (conftest + binário chromium) DEVE estar
funcional no host de desenvolvimento: o `executable_path` configurado
em `tests/e2e/conftest.py` DEVE apontar para um binário chromium
existente, e o teste DEVE ser executável via `uv run pytest
tests/e2e/test_s06_full_journey.py -v` sem erro de "shared library
not found" ou "executable doesn't exist".

#### Scenario: S06 roda verde com posicao_italo.csv

- **WHEN** host tem `playwright install chromium --with-deps` executado
- **AND** operador executa `uv run pytest tests/e2e/test_s06_full_journey.py -v`
- **THEN** o teste `TestS06PosicaoItaloImport::test_import_posicao_italo_with_class_association` passa
- **AND** as assertions sobre `suggested_class_id` por categoria casam:
  Internacional→Internacional, RF Pós→RF Pos, RF Dinâmica→RF Dinamica,
  Ações→Acoes, FII→FII
- **AND** linhas com categoria `BR Dividendos`, `Cripto`,
  `(Não configurado)` permanecem com `suggested_class_id = null` na
  resposta do servidor
- **AND** o commit do import cria assets visíveis no dashboard com
  posições e percentuais corretos

#### Scenario: Setup do conftest usa env var configurável

- **WHEN** o host define `E2E_CHROMIUM_PATH=/caminho/do/chrome`
- **THEN** o `_browser` fixture em `tests/e2e/conftest.py` lança o
  chromium usando esse path
- **WHEN** o host NÃO define `E2E_CHROMIUM_PATH`
- **THEN** o fixture usa o binário instalado por `playwright install`
  (em `~/.cache/ms-playwright/chromium-*/chrome-linux/chrome`)
- **AND** se nenhum dos dois paths existir, o fixture falha com
  `RuntimeError("chromium binary not found: ...")`

#### Scenario: S05 regressão é diagnosticada (não consertada) por esta change

- **WHEN** operador executa `uv run pytest tests/e2e/test_s05_user_journey.py -v`
- **THEN** se o teste passa, a regressão listada em M002 ressalva §5.1
  não se reproduz no estado atual
- **AND** se o teste falha, o output (stack trace + screenshot em
  `/tmp/s05_e2e_screenshots/`) é capturado em
  `tests/e2e/M002_RESSALVA_DIAGNOSIS.md` para abrir change dedicada
