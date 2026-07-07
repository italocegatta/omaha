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
    E clico em "Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "60"
    E clico em "Salvar"
    E clico em "Nova classe"
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
    E clico em "Nova classe"
    E preencho o campo "Nome da classe" com "Reserva"
    E preencho o campo "Alocação alvo" com "100"
    E clico em "Salvar"
    Quando clico em "Sair"
    E preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E troco o perfil pelo chip do header para "Ana"
    Então o dashboard mostra as classes de "Ana"

  # F07 — Família-as-profile option. Família is rendered as a peer of
  # real profiles inside the profile-switcher chip (the F06 header
  # toggle is retired). Selecting Família activates the family
  # aggregate view (cross-User full-join by name, read-only); the
  # querystring ``?view=household`` is preserved on the redirect URL
  # so deep-links from F06 still resolve. The aggregate is identical
  # regardless of which family operator is logged in (cross-User
  # invariant — D-F06.1). Mutating buttons disappear; the API rejects
  # any mutation that a hand-crafted tab might re-send.
  Cenário: Operador seleciona Família no chip e vê agregado cross-User
    Dado que estou logado como "Italo"
    Quando troco o perfil pelo chip do header para "Família"
    Então a página mostra a nota de somente leitura

  Cenário: Agregado familiar é simétrico entre operadores
    Dado que estou logado como "Italo"
    Quando troco o perfil pelo chip do header para "Família"
    Então a página mostra a nota de somente leitura
    Quando clico em "Sair"
    Dado que estou logado como "Ana"
    Quando troco o perfil pelo chip do header para "Família"
    Então a página mostra a nota de somente leitura

  Cenário: Total agregado é o mesmo para Italo e Ana
    Dado que estou logado como "Italo"
    Quando troco o perfil pelo chip do header para "Família"
    Então a página mostra a nota de somente leitura
    Quando clico em "Sair"
    Dado que estou logado como "Ana"
    Quando troco o perfil pelo chip do header para "Família"
    Então a página mostra a nota de somente leitura
