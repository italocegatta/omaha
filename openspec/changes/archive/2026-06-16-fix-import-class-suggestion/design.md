## Context

`import_class_suggest_id` em `csv_import.py:618` implementa matching em 3 tiers (exato → substring → interseção de palavras) entre a categoria do CSV e os nomes das classes do perfil. A função é chamada em `_build_preview_response` (`routes/imports.py:391`) para cada linha unmatched.

O pipeline está correto — o bug é de cobertura de teste: nenhum teste de integração valida o cenário onde o match acontece. Testes existentes (`test_s04_t01`, `test_s04_t04`) criam classes com nomes que deliberadamente não casam com as categorias do CSV, então `suggested_class_id` sempre retorna `None`. O teste do cenário feliz (classes casadas) existe apenas em nível unitário (`test_t02_csv_import.py`), não em integração com o endpoint HTTP.

## Goals / Non-Goals

**Goals:**
- Adicionar teste de integração em `test_s04_t01_import_preview.py` que valida `suggested_class_id` preenchido quando classes do perfil casam com categorias do CSV
- Cobrir os 3 tiers de matching (exato, substring, interseção) via fixture CSV existente
- Garantir que o teste falhe se o pipeline quebrar (parse → suggest → response)

**Non-Goals:**
- Alterar a lógica de `suggest_class_id` — a função já funciona
- Adicionar mapa de sinônimos ou melhorar o algoritmo de matching
- Modificar fixtures CSV existentes

## Decisions

**Decisão 1: Teste novo em `test_s04_t01` vs classe helper separada**
- `test_s04_t01` já testa `POST /api/import/preview` e tem helpers (`_create_asset_classes`, `_create_assets`, `_read_fixture`)
- Adicionar o novo teste na mesma class `TestPostImportPreview` mantendo a coerência
- Criar helper `_create_matching_asset_classes` que gera classes com nomes que casam com as categorias do CSV

**Decisão 2: Usar `sample_broker.csv` existente**
- O CSV já contém categorias variadas: `RF Pós`, `Ações`, `(Não configurado)`
- Criar classes `RF Pós`, `Ações` no perfil de teste para validar Tier 1 (exato)
- A classe `(Não configurado)` não deve ser criada — testa que `None` ainda funciona quando não há classe correspondente

## Análise Crítica dos Testes Existentes

### `test_s04_t01_import_preview.py`
Testa `POST /api/import/preview` — 8 testes. O único que toca em `suggested_class_id` (linha 234) **explicitamente espera `None`**:
```python
# suggested_class_id should be None for these unmatched rows
# because the test classes (Renda Fixa, Renda Variavel,
# Fundos Imobiliarios) don't match any CSV category names
assert um["suggested_class_id"] is None
```
O comentário documenta a limitação, mas o teste não valida O CONTRÁRIO. Resultado: o pipeline quebra no cenário feliz e ninguém descobre.

### `test_s04_t04_real_csv_flow.py`
Idem — 6 testes, 543 linhas. A validação de `suggested_class_id` (linha 336) também espera `None` para TODAS as unmatched:
```python
for um in data["unmatched"]:
    assert um["suggested_class_id"] is None
```
Testa exaustivamente o caso "sem match" mas nunca o caso "com match". Cobertura unilateral — a função pode ser deletada que o teste continua verde.

### `test_t03_imports_routes.py`
Tem `test_review_preselects_class_via_preview_api` que cria classes `RF Pós` e `Acoes` — nomes que CASARIAM com o CSV. Mas o teste só verifica redirect HTTP 302, **nunca lê o `suggested_class_id`** na resposta da API. Testa o roteamento, não o domínio.

### Síntese
Os testes passam porque cobrem apenas o lado "não match" do problema. A função `suggest_class_id` pode retornar `None` para sempre — ou ser removida por completo — que os testes continuam verdes. É cobertura que dá falsa confiança. O teste que prova que a FUNÇÃO FUNCIONA (match → id) não existe em nível de integração.

## Risks / Trade-offs

- **[Baixo]** Teste pode ficar frágil se a fixture CSV mudar — mitigado por usar tickers específicos para verificação, não índices posicionais
- **[Baixo]** Criação de classes adicionais no perfil 1 não afeta outros testes devido ao `_clean_data` fixture que limpa tudo antes de cada teste
