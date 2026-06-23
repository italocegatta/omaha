# language: pt
Funcionalidade: Isolamento de dados entre perfis
  Como um membro da família
  Eu quero que minhas classes e ativos não apareçam no dashboard do outro perfil
  Para manter a privacidade da estratégia individual de cada investidor

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Cenário: Italo's classes invisible to Ana
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "Italo"
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
    E clico no botão do perfil "Ana"
    Então o dashboard mostra a mensagem de estado vazio

  Cenário: Ana's classes invisible to Italo
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Ana"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "Ana"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "Reserva"
    E preencho o campo "Alocação alvo" com "100"
    E clico em "Salvar"
    Quando clico em "Sair"
    E preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "Italo"
    Então o dashboard mostra a mensagem de estado vazio
