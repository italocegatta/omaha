# language: pt
Funcionalidade: Jornada completa do operador em uma única sessão
  Como Italo, operador da carteira
  Eu quero configurar 2 classes com 2 ativos cada via interface
  Para validar que o fluxo login → classe → ativo → alvo → derivado
  funciona de ponta a ponta

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Cenário: Jornada completa via modal de importação (perfil "Italo")
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    Então estou na página "/profiles"
    Quando clico no botão do perfil "Italo"
    Então estou na página "/"
    E o dashboard mostra o nome do perfil "Italo"

    Quando clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Dinâmica"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    Então o dashboard mostra 2 seções de classe
    E a seção "RF Pós" mostra "50%"
    E a seção "RF Dinâmica" mostra "50%"

    Quando abro o modal "Importar posições"
    E seleciono o arquivo "tiny_portfolio.csv"
    E clico em "Enviar"
    Então o modal mostra 0 linhas não correspondidas
    E clico em "Confirmar importação"
    Então o dashboard mostra 4 linhas de ativos
    E a seção "RF Pós" contém 2 ativos
    E a seção "RF Dinâmica" contém 2 ativos

    Quando clico no campo "Alocação dentro da classe" do ativo "Tesouro Selic 2029"
    E digito "60"
    E pressiono "Enter"
    Então a alocação salva do ativo "Tesouro Selic 2029" é "60%"

    Quando clico no campo "Alocação alvo da carteira" da classe "RF Pós"
    E digito "70"
    E pressiono "Enter"
    Então a alocação salva da classe "RF Pós" é "70%"

    Então o derivado "Tesouro Selic 2029" na carteira é "42,0%"
