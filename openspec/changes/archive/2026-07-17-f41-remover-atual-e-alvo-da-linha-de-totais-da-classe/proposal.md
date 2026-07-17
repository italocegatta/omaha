## Why

Na linha de totais da classe ("Total da classe") da tabela de patrimônio, as colunas "Classe/Atual" e "Classe/Alvo" sempre exibem 100%/100% — valores que não agregam informação ao operador. A soma dos percentuais de uma classe é sempre 100% por definição; mostrar isso desperdiça espaço visual e distrai do dado útil (Desvio).

## What Changes

- As células `class-total-current-pct-class` e `class-total-target-pct-class` na linha de totais da classe passam a exibir "—" em vez de `100%`
- Nenhuma alteração no backend, modelos ou lógica de cálculo
- Alteração limitada ao template Jinja2 `_patrimonio_class_section.html`

## Capabilities

### New Capabilities

_(nenhuma)_

### Modified Capabilities

- `class-section-totals`: Requisito de alinhamento da linha de totais muda — as colunas Classe/Atual e Classe/Alvo na linha de totais passam a exibir "—" em vez dos percentuais redundantes.

## Impact

- **Template**: `src/omaha/templates/_patrimonio_class_section.html` (linhas 137-138)
- **CSS**: possivelmente ajuste de estilo para células com "—" (herda estilo existente de `metric-placeholder`)
- **Testes**: e2e ou BDD que verificam o conteúdo dessas células na linha de totais podem precisar de ajuste
- **Backend**: inalterado
