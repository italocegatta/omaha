# import-modal-class-binding — delta spec

## ADDED Requirements

### Requirement: Suíte e2e é executável contra o estado pós multi-user seed

A suíte e2e (`tests/e2e/`) DEVE ser executável contra o estado
atual do seed (commit `35bf15d`, que cria os usuários `Italo` e
`Ana` em vez do legado `family`) sem erro de autenticação no
passo de login. Concretamente:

- Todos os testes que fazem `POST /login` com `username=Italo`
  (ou `username=Ana`) e a senha compartilhada da família DEVEM
  receber `303 → /profiles` e seguir adiante.
- O helper `_login_and_select_italo` em
  `tests/e2e/test_s04_user_journey.py` DEVE usar `username=Italo`
  e em seguida selecionar o profile `Italo` no picker.
- O cenário E2E "S06 roda verde com posicao_italo.csv" (adicionado
  em `verify-m002-fix-s06-real-browser`) SÓ conta como atendido
  depois que a suíte consegue passar o login.

#### Scenario: TestClient login com Italo redireciona para /profiles

- **WHEN** operador (ou test harness) faz `POST /login` com
  `username=Italo` + senha da família
- **THEN** resposta HTTP 303 com `Location: /profiles`
- **AND** o cookie `omaha_session` é setado

#### Scenario: TestClient login com usuário inexistente re-renderiza form

- **WHEN** operador (ou test harness) faz `POST /login` com
  `username=` (string inexistente) + qualquer senha
- **THEN** resposta HTTP 200 com form de login re-renderizado
- **AND** HTML contém `data-testid="login-error"` com a mensagem
  "Usuário ou senha inválidos"
- **AND** nenhum cookie de sessão é setado

#### Scenario: TestClient login com senha errada re-renderiza form

- **WHEN** operador (ou test harness) faz `POST /login` com
  `username=Italo` + senha incorreta
- **THEN** resposta HTTP 200 com form de login re-renderizado
- **AND** HTML contém `data-testid="login-error"` com a mensagem
  "Usuário ou senha inválidos"
- **AND** nenhum cookie de sessão é setado
- **NOTE:** este cenário é semanticamente distinto do anterior
  (usuário existe vs não existe); ambos DEVEM produzir a mesma
  resposta genérica para não vazar qual account existe.

#### Scenario: e2e Playwright login + profile picker

- **WHEN** browser acessa `/login`, preenche `username=Italo` +
  senha, submete
- **THEN** URL final é `/profiles`
- **AND** clicar no botão do profile "Italo" em `form.profile-picker`
  redireciona para `/`
