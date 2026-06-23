# language: pt
Funcionalidade: Exibição do percentual derivado da carteira
  Como operador da carteira
  Eu quero ver o percentual de cada ativo na carteira total
  Para entender a contribuição real de cada posição

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Derived portfolio % recomputes on class PATCH
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "50%"
    E clico no campo "Alocação alvo da carteira" da classe "RF Pós"
    E digito "70"
    E pressiono "Enter"
    Então o derivado "Tesouro Selic 2029" na carteira é "35.00%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Derived portfolio % recomputes on asset PATCH
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "100%"
    E clico no campo "Alocação alvo da carteira" do ativo "Tesouro Selic 2029"
    E digito "35"
    E pressiono "Enter"
    Então o derivado "Tesouro Selic 2029" na carteira é "35.00%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
