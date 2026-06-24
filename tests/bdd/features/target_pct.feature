# language: pt
Funcionalidade: Ajuste da alocação alvo (PATCH)
  Como operador da carteira
  Eu quero ajustar a alocação alvo de cada classe e de cada ativo
  Para refletir uma rebalanceação manual sem recriar a carteira

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: PATCH per-class target reflects in dashboard
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando clico no campo "Alocação alvo da carteira" da classe "RF Pós"
    E digito "70"
    E pressiono "Enter"
    Então a alocação salva da classe "RF Pós" é "70%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: PATCH per-asset total reflects in dashboard
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "100%"
    E clico no campo "Alocação alvo da carteira" do ativo "Tesouro Selic 2029"
    E digito "30"
    E pressiono "Enter"
    Então a alocação salva do ativo "Tesouro Selic 2029" é "30.00%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Per-class sum off-100 é aceito (D006)
    Dado que estou logado como "<profile>"
    E criei a classe "Ações" com "100%"
    Quando adicionei o ativo "PETR4" à classe "Ações" com "60%"
    E adicionei o ativo "VALE3" à classe "Ações" com "50%"
    Então o dashboard mostra 2 linhas de ativos
    E a seção "Ações" contém 2 ativos

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Inline edit off-100 é aceito (D006)
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    E adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "40%"
    E adicionei o ativo "Tesouro IPCA 2029" à classe "RF Pós" com "40%"
    Quando clico no campo "Alocação alvo da carteira" do ativo "Tesouro Selic 2029"
    E digito "80"
    E pressiono "Enter"
    Então a alocação salva do ativo "Tesouro Selic 2029" é "80.00%"
    E a seção "RF Pós" contém 2 ativos

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
