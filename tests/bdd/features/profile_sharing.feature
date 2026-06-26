# language: pt
Funcionalidade: Compartilhamento entre perfis
  Como um membro da família
  Eu quero ver o dashboard do outro perfil trocando o seletor do header
  Para acompanhar a estratégia do outro investidor

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Cenário: Ana vê as classes de Italo após trocar pelo chip
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "60"
    E clico em "Salvar"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Dinâmica"
    E preencho o campo "Alocação alvo" com "40"
    E clico em "Salvar"
    Quando clico em "Sair"
    E preencho o campo "username" com "Ana"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E troco o perfil pelo chip do header para "Italo"
    Então o dashboard mostra as classes de "Italo"

  Cenário: Italo vê as classes de Ana após trocar pelo chip
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Ana"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "Reserva"
    E preencho o campo "Alocação alvo" com "100"
    E clico em "Salvar"
    Quando clico em "Sair"
    E preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E troco o perfil pelo chip do header para "Ana"
    Então o dashboard mostra as classes de "Ana"
