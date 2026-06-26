# language: pt
Funcionalidade: Login e seleção de perfil
  Como um membro da família
  Eu quero entrar no sistema com a senha compartilhada
  Para acessar o dashboard da minha carteira diretamente

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Cenário: Login + dashboard direto
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    Então estou na página "/"
    E o dashboard mostra o nome do perfil "Italo"

  Cenário: Login fail — senha errada
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Italo"
    E preencho o campo "password" com "senha-errada"
    E clico em "Entrar"
    Então não estou na página /profiles
    E a página mostra a mensagem de erro "Senha"
