## ADDED Requirements

### Requirement: Estado de seleção de classe por linha tem 2 modos visuais distintos

Para cada linha das tabelas de revisão (`data-testid="import-existing-table"` e `data-testid="import-unmatched-table"`), a coluna "Classe" MUST distinguir visualmente entre dois estados de seleção:

1. **Com classe selecionada (matched row com `asset_class_id`, OU unmatched com `suggested_class_id`, OU classe escolhida manualmente pelo usuário):** o `<select>` exibe a classe; o `<td class="import-class-cell">` tem classe CSS modificadora `.import-class-cell--cls-N` (N = índice da classe no `assetClasses`); o background e a border-left refletem a cor da classe via regra CSS fixa; o swatch à esquerda mostra a cor cheia.
2. **Pendente (perfil sem `asset_classes`):** o `<select>` exibe o placeholder "Selecione..."; o `<td>` tem classe CSS modificadora `.import-class-cell--pending` (borda dashed + fundo neutro) comunicando que o usuário precisa escolher — e que o backend não tem classes para sugerir.

A comunicação visual entre os 2 estados DEVE ser inequívoca: linhas com classe ficam coloridas; linhas pendentes ficam com borda dashed. Nunca há sobreposição (uma linha está em exatamente um estado por vez).

**Importante:** linhas unmatched sem `suggested_class_id` mas COM `asset_classes` no payload NÃO são consideradas "pendentes" — o sistema não inventa uma classe para elas (pre-seleção de fallback foi explicitamente rejeitada pelo usuário). O estado "pendente" é exclusivo para o caso "perfil sem classes configuradas".

#### Scenario: Linha matched com asset_class_id é colorida

- **WHEN** a linha está em `auto_matched[]` e tem `asset_class_id` não-nulo
- **THEN** o `<select>` exibe o nome da classe
- **AND** o `<td>` tem classe CSS `import-class-cell--cls-N` (N correto)
- **AND** o background computado é `color-mix(in srgb, <color> 38%, var(--surface))`
- **AND** o swatch tem `style="background: <color>"`

#### Scenario: Linha unmatched com categoria casada é colorida pela sugestão

- **WHEN** a linha está em `unmatched[]` com `suggested_class_id` não-nulo
- **THEN** o `<td>` tem classe CSS `import-class-cell--cls-N` (N da classe sugerida)
- **AND** o background computado reflete a cor da classe sugerida

#### Scenario: Linha unmatched sem categoria casada E sem asset_classes no payload é pendente

- **WHEN** a linha está em `unmatched[]` com `suggested_class_id === null`
- **AND** o payload tem `asset_classes[].length === 0`
- **THEN** `assignments[ticker].class_id` permanece `''`
- **AND** o `<td>` tem classe `import-class-cell--pending`
- **AND** o swatch tem `style="background: transparent"`
- **AND** o `<select>` exibe o placeholder "Selecione..."

#### Scenario: Trocar classe manualmente atualiza a cor visualmente

- **WHEN** o usuário troca a classe via `<select>` (de classe A para classe B)
- **THEN** o `<td>` muda de `import-class-cell--cls-A` para `import-class-cell--cls-B`
- **AND** o background computado muda de `color-mix(...cor A...)` para `color-mix(...cor B...)`
- **AND** o swatch muda de `style="background: <cor A>"` para `style="background: <cor B>"`
