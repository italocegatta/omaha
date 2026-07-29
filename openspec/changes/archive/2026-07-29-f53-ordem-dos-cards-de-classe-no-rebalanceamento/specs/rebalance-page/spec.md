## ADDED Requirements

### Requirement: Class summary cards render in normative order

The rebalance page SHALL render the class summary cards in the fixed normative order `RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`, regardless of the order in which `category_plan` rows arrive from the server. Order SHALL be resolved client-side from `category_name` using a fixed name→position map; no order field SHALL be added to `RebalanceCategoryPlanRow`.

A class name absent from the normative map SHALL render after all mapped classes, with unknown classes ordered alphabetically by `category_name`. The normative order SHALL NOT alter card content, card shell, waterfall chart, CSS, asset plan table, global metrics, or the rebalance solver.

#### Scenario: Known classes render in normative sequence

- **WHEN** the rebalance plan contains category rows for `Ações`, `RF Pós`, `Internacional`, `FII`, `Cripto`, and `RF Dinâmica` in any server order
- **THEN** the rendered class summary cards appear in the sequence `RF Pós`, `RF Dinâmica`, `FII`, `Ações`, `Internacional`, `Cripto`

#### Scenario: Unknown classes render after normative classes

- **WHEN** the rebalance plan contains mapped classes plus unknown classes `Zebra` and `Alpha`
- **THEN** all mapped classes render first in normative order
- **AND** `Alpha` renders before `Zebra` after the mapped classes

#### Scenario: Category payload contract remains unchanged

- **WHEN** the rebalance page renders class summary cards in normative order
- **THEN** `RebalanceCategoryPlanRow` continues to expose exactly the existing seven fields
- **AND** the server `category_plan` payload is not mutated to carry display order
