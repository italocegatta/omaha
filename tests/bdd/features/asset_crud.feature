# language: pt
Funcionalidade: CRUD manual de ativos no dashboard
  Como operador da carteira
  Eu quero adicionar ativos diretamente pelo dashboard
  Para popular uma classe sem usar a importação CSV

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Manual add 4 ativos não-igual por classe
    Dado que estou logado como "<profile>"
    E criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%
    Quando adicionei o ativo "TESOURO_SELIC_2029" à classe "RF Pós" com "60%"
    E adicionei o ativo "CDB_LIQUIDEZ_2027" à classe "RF Pós" com "40%"
    E adicionei o ativo "FII_HSML11" à classe "RF Dinâmica" com "30%"
    E adicionei o ativo "ACAIO_PETR4" à classe "RF Dinâmica" com "70%"
    Então o dashboard mostra 4 linhas de ativos
    E a seção "RF Pós" contém 2 ativos
    E a seção "RF Dinâmica" contém 2 ativos

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
