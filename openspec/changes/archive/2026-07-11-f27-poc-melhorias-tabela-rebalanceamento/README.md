# f27-poc-melhorias-tabela-rebalanceamento

POC isolada da tabela de rebalanceamento em `/teste`.

Base de implementação para change oficial futura em `/rebalanceamento`.

Resumo do que a POC entrega:
- tabela legada real com dados do plano do perfil ativo
- ordenação, filtros e busca no mesmo wire format do rebalance
- CSS e badges legados reaproveitados
- rota isolada, sem side effect

O que a change oficial deve herdar:
- estrutura declarativa de colunas
- padrões de filtro e ordenação
- formato de células e badges
- contrato de dados vindo de `run_rebalance`

Migração oficial fica em outra change, conforme roadmap.

Handoff detalhado: [`handoff-poc-to-official.md`](../../../handoff-poc-to-official.md)
