# import-class-auto-suggest Specification

## Purpose
TBD - created by syncing change fix-import-class-suggestion. Update Purpose after archive.
## Requirements
### Requirement: Import preview sugere classe automaticamente quando há match

O sistema DEVE preencher `suggested_class_id` na resposta de `POST /api/import/preview` quando o nome de uma classe do perfil ativo corresponder ao valor da coluna "Minha Categoria" do CSV importado, seguindo a estratégia de matching definida em `suggest_class_id` (exato → substring → interseção de palavras).

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
