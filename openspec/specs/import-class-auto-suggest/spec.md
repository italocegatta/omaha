# import-class-auto-suggest Specification

## Purpose
TBD - created by syncing change fix-import-class-suggestion. Update Purpose after archive.
## Requirements
### Requirement: Import preview sugere classe automaticamente quando há match

O sistema SHALL preencher `suggested_class_id` na resposta de `POST /api/import/preview` quando o nome de uma classe do perfil ativo corresponder ao valor da coluna "Minha Categoria" do CSV importado, seguindo a estratégia de matching definida em `suggest_class_id` (exato → substring → interseção de palavras).

O preenchimento automático DEVE considerar APENAS as classes do perfil do usuário ativo no momento da importação. Perfis diferentes podem ter classes diferentes, e o matching DEVE refletir as classes do perfil que está importando.

Se não houver correspondência entre nenhuma classe do perfil e a categoria do CSV, `suggested_class_id` DEVE vir `None`, e o usuário poderá selecionar manualmente na tela de validação.

#### Scenario: Categoria do CSV casa exatamente com nome da classe

- **WHEN** Perfil possui uma classe chamada "RF Pós"
- **AND** CSV importado contém linha não-match com categoria "RF Pós"
- **AND** Usuário faz POST /api/import/preview
- **THEN** Resposta JSON contém `suggested_class_id` igual ao ID da classe "RF Pós" para aquela linha

#### Scenario: Categoria do CSV casa por substring com nome da classe

- **WHEN** Perfil possui uma classe chamada "Renda Fixa"
- **AND** CSV importado contém linha não-match com categoria "RF" (substring de "Renda Fixa")
- **AND** Usuário faz POST /api/import/preview
- **THEN** Resposta JSON contém `suggested_class_id` igual ao ID da classe "Renda Fixa" para aquela linha

#### Scenario: Categoria do CSV casa por interseção de palavras

- **WHEN** Perfil possui uma classe chamada "Fundos Imobiliarios"
- **AND** CSV importado contém linha não-match com categoria "FII Imobiliarios"
- **AND** Usuário faz POST /api/import/preview
- **THEN** Resposta JSON contém `suggested_class_id` igual ao ID da classe "Fundos Imobiliarios" para aquela linha

#### Scenario: Nenhuma classe do perfil corresponde à categoria do CSV

- **WHEN** Perfil possui classes "Renda Fixa", "Renda Variavel", "Fundos Imobiliarios"
- **AND** CSV importado contém linha não-match com categoria "(Não configurado)"
- **AND** Usuário faz POST /api/import/preview
- **THEN** Resposta JSON contém `suggested_class_id` = `null` para aquela linha

#### Scenario: Perfil sem classes retorna lista vazia

- **WHEN** Perfil não possui nenhuma asset class cadastrada
- **AND** CSV importado contém linhas
- **AND** Usuário faz POST /api/import/preview
- **THEN** Resposta JSON contém `asset_classes` = `[]`
- **AND** `suggested_class_id` = `null` para todas as linhas unmatched

### Requirement: Real-browser E2E valida suggest_class_id contra posicao_italo.csv

O sistema SHALL passar o teste `tests/e2e/test_s06_full_journey.py` num
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
