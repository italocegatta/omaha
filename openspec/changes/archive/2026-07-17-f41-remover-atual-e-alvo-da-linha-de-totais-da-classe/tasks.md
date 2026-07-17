## 1. Template

- [x] 1.1 Em `src/omaha/templates/_patrimonio_class_section.html`, substituir a célula 137 (`data-testid="class-total-current-pct-class"`) — remover `x-text="formatPctRounded(classCurrentPctClass)"` e inserir texto estático "—"
- [x] 1.2 Na mesma arquivo, substituir a célula 138 (`data-testid="class-total-target-pct-class"`) — remover `x-text="formatPctRounded(classTargetPctClass)"` e inserir texto estático "—"

## 2. Verificação

- [x] 2.1 Rodar `task serve` e inspecionar visualmente a linha "Total da classe" no `/patrimonio` — confirmar que Desvio ainda exibe valor e Atual/Alvo mostram "—"
- [x] 2.2 Rodar `task test-unit` para confirmar que nenhum teste existente quebra
