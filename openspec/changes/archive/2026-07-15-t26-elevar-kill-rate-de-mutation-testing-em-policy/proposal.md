# Proposal: Elevar kill rate de mutation testing em policy.py

## Problem

`policy.py` contribui com 69% dos sobreviventes de mutation testing (145/211).
Baseline: 90% killed (3468/3867). Quatro funções concentram 87 dos 145
sobreviventes:

| Função | Survived | % do total policy.py |
|--------|----------|---------------------|
| `_evaluate_progressive_sales_stage_solution` | 44 | 30% |
| `_build_contribution_only_rejection_reason` | 16 | 11% |
| `_calculate_solution_top_gaps` | 14 | 10% |
| `_build_overweight_projected_value_floor` | 13 | 9% |
| Outras | 58 | 40% |

Testes atuais validam smoke (pipeline roda, resultado não quebra) mas não
exercitam caminhos de decisão, boundary conditions, nem integração com
engine. Mutantes em `if/else`, operadores de comparação, constantes, e
lógica condicional sobrevivem porque nenhum teste verifica o valor exato
do resultado ou o caminho tomado.

## Solution

Escrever testes unitários direcionados que matem mutantes específicos.
Sem mudar código de produção. Foco:

1. **Boundary conditions** — valores que cruzam thresholds exatos
2. **Decision paths** — cada `if/else` exercitado com resultado verificável
3. **Integration with engine** — `simulate_rebalance` com cenários que
   produzem diferentes políticas e verificam métricas exatas

## Scope

- `tests/test_rebalance_policy.py` — novos testes
- Zero alteração em `src/omaha/rebalance/policy.py`
- Zero alteração em fixtures existentes (usar builders já disponíveis)

## Success Criteria

- `mutmut results` mostra < 30 survived em `policy.py`
- Todos os testes novos passam em `task test-unit`
- Nenhum teste existente quebrado
