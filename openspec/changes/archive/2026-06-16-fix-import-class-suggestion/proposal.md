## Why

`import_class_suggest_id` existe e funciona em testes unitários, mas nenhum teste de integração valida o pipeline completo: CSV → parse → match com classes do perfil → `suggested_class_id` preenchido na resposta da API. Os testes de integração atuais (`test_s04_t01`, `test_s04_t04`) usam classes com nomes que propositalmente NÃO casam com as categorias do CSV, então o campo `suggested_class_id` sempre vem `None`. Falta cobertura do cenário feliz — onde o nome da classe do perfil coincide com a coluna "Minha Categoria" do arquivo importado — para garantir que o fluxo funciona e não regride.

## What Changes

- Integração: `suggest_class_id` agora é chamado no `_build_preview_response` para cada unmatched row
- Nenhuma mudança na lógica de matching — a função já existe e funciona
- Será adicionado um teste de integração que:
  - Cria classes com nomes que casam com as categorias do CSV (`RF Pós`, `Ações`)
  - Faz upload do CSV fixture
  - Verifica que `suggested_class_id` vem preenchido (não `None`) nas rows unmatched com categoria correspondente
  - Confirma que o valor do `suggested_class_id` é o ID correto da classe

## Capabilities

### New Capabilities
- `import-class-auto-suggest`: Garantir que o importador preencha automaticamente a classe do ativo na tela de validação quando houver match entre o campo "Minha Categoria" do CSV e o nome de uma classe cadastrada no perfil do usuário ativo.

### Modified Capabilities
Nenhuma — a capability já existe na implementação, só não tem cobertura de integração.

## Impact

- `tests/test_s04_t01_import_preview.py`: novo teste de integração `test_preview_suggests_class_when_names_match`
- Nenhuma alteração em código de produção — apenas adição de teste
