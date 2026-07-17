## Context

Na tabela de patrimônio, cada classe de ativos tem uma linha de totais ("Total da classe") que resume os valores agregados. As colunas "Classe/Atual" e "Classe/Alvo" nessa linha sempre exibem 100%/100% porque representam a soma dos percentuais dos ativos dentro da classe — que por definição é 100%. Esse dado é redundante e ocupa espaço visual sem agregar informação.

O template `src/omaha/templates/_patrimonio_class_section.html` renderiza essas células nas linhas 137-138, usando `x-text="formatPctRounded(classCurrentPctClass)"` e `x-text="formatPctRounded(classTargetPctClass)"` respectivamente.

## Goals / Non-Goals

**Goals:**
- Remover os valores redundantes de Atual e Alvo da linha de totais da classe
- Exibir "—" nas células para manter alinhamento visual com as colunas da tabela
- Manter a coluna Desvio intacta (ela exibe informação útil)

**Non-Goals:**
- Alterar o comportamento das colunas Atual/Alvo nas linhas de ativos individuais
- Modificar o backend, modelos ou lógica de cálculo
- Alterar o alinhamento das colunas (mantém `table-layout: fixed`)

## Decisions

**D1: Substituir conteúdo por "—" em vez de célula vazia**

Células vazias podem causar inconsistência visual com o restante da tabela. O em-dash "—" já é usado em outras células sem valor (ex: `class-total-value` quando `current_value == 0`). Usar "—" mantém consistência com o padrão existente de `metric-placeholder`.

**D2: Alterar apenas o template, não o JavaScript**

Os valores `classCurrentPctClass` e `classTargetPctClass` continuam disponíveis no `x-data` do Alpine.js — não removemos os dados, apenas não os exibimos na linha de totais. Isso evita efeitos colaterais em outras partes que possam usar esses valores.

**D3: Usar markup estático em vez de `x-text`**

Como o valor é sempre "—" (não depende de dados), usamos HTML estático em vez de binding Alpine.js. Isso elimina processamento reativo desnecessário.

## Risks / Trade-offs

- **[Risco] Testes e2e que verificam o conteúdo dessas células** → Mitigação: atualizar testes que usem `data-testid="class-total-current-pct-class"` ou `data-testid="class-total-target-pct-class"` para esperar "—" em vez de "100%"
- **[Risco] Usuários acostumados a ver 100%** → Mitigação: dado redundante; Desvio já consolida a informação útil
