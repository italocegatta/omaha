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
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    E abro o formulário de ativo da classe "RF Pós"
    E preencho o campo "Nome do ativo" com "Tesouro Selic 2029"
    E preencho o campo "Alocação alvo" do modal de ativo com "50"
    E clico em "Adicionar ativo"
    Quando clico no campo "Alocação alvo da carteira" da classe "RF Pós"
    E digito "70"
    E pressiono "Enter"
    Então o derivado "Tesouro Selic 2029" na carteira é "35,0%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Derived portfolio % recomputes on asset PATCH
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    E abro o formulário de ativo da classe "RF Pós"
    E preencho o campo "Nome do ativo" com "Tesouro Selic 2029"
    E preencho o campo "Alocação alvo" do modal de ativo com "50"
    E clico em "Adicionar ativo"
    Quando clico no campo "Alocação dentro da classe" do ativo "Tesouro Selic 2029"
    E digito "70"
    E pressiono "Enter"
    Então o derivado "Tesouro Selic 2029" na carteira é "42,0%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
