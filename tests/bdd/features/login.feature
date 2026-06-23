# language: pt
Funcionalidade: Login e seleção de perfil
  Como um membro da família
  Eu quero entrar no sistema com a senha compartilhada e escolher meu perfil
  Para acessar o dashboard da minha carteira

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Login + profile pick OK
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    Então estou na página "/profiles"
    Quando clico no botão do perfil "<profile>"
    Então estou na página "/"
    E o dashboard mostra o nome do perfil "<profile>"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Cenário: Login fail — senha errada
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "Italo"
    E preencho o campo "password" com "senha-errada"
    E clico em "Entrar"
    Então não estou na página /profiles
    E a página mostra a mensagem de erro "Senha"
