## Contexto

A suite BDD (`tests/bdd/`) tem 30 cenários em PT-BR. Os cenários
seguem um padrão recorrente de setup:

1. **Bootstrap de auth** — login + seleção de perfil. Repetido em
   ~25 cenários.
2. **Bootstrap de classes** — criar 2 classes (`RF Pós` 50% +
   `RF Dinâmica` 50%). Repetido em ~10 cenários.
3. **Bootstrap de ativos** — criar 4 ativos com distribuição
   não-igual (60/40 + 30/70). Repetido em 2 cenários hoje;
   tendência de crescer.

Cada sequência tem 5-10 steps Gherkin. Total de duplicação: ~150
steps redundantes entre os arquivos `.feature`. pytest-bdd
NÃO suporta composição de cenários (limite confirmado por docs
oficiais e source do `scenario.py`), então não dá pra escrever
"executar cenário de login como step".

A documentação do pytest-bdd oferece três mecanismos de reuso:

| Mecanismo | Cobertura | Limitação |
|-----------|-----------|-----------|
| `Contexto:` (Background) | Por arquivo | Repete entre arquivos |
| Steps em `conftest.py` | Cross-file | Cada step é uma ação atômica, não uma sequência |
| Step aliases | Mesma função | Não compõe ações |

A lacuna: **sequência multi-step que se repete cross-file**.

## Decisões

### Decisão 1: Helper Python + step wrapper fino

**Por quê:** encapsula a sequência multi-step em uma função Python
reutilizável. Step wrapper Gherkin vira uma linha. Helper é o
"single source of truth" — mudança de regra de negócio = editar 1
função, propagação automática para todos os cenários que usam o
wrapper.

**Como:**

```python
# tests/bdd/step_defs/_workflows.py (novo)

def login_and_pick_profile(page, live_url, profile):
    """Bootstrap: navigate to /login, fill, submit, pick profile."""
    page.goto(f"{live_url}/login")
    page.fill('input[name="username"]', profile)
    page.fill('input[name="password"]', "test-password")
    page.click('button[type="submit"]')
    page.wait_for_url(re.compile(r"/profiles$"), timeout=5000)
    page.locator("form.profile-picker button").filter(has_text=profile).first.click()
    page.wait_for_url(re.compile(r"/$"), timeout=5000)


# tests/bdd/step_defs/common_steps.py (modificado)

@when(parsers.re(r'que estou logado como "(?P<profile>[^"]+)"'))
def logged_in_as(page, live_url, profile):
    login_and_pick_profile(page, live_url, profile)
```

**Feature file refatorado:**

```diff
-  Esquema do Cenário: Snapshot create 2 classes
-    Dado que estou na página "/login"
-    Quando preencho o campo "username" com "<profile>"
-    E preencho o campo "password" com "test-password"
-    E clico em "Entrar"
-    E clico no botão do perfil "<profile>"
+  Esquema do Cenário: Snapshot create 2 classes
+    Quando que estou logado como "<profile>"
     Quando abro o editor de classes
     ...
```

**Alternativas consideradas:**

- **Contexto:** — cobre só dentro do arquivo. Login teria que
  aparecer em `Contexto:` de 6 arquivos diferentes = ainda
  duplicação cross-file.
- **Step generation via `stacklevel`** — útil para gerar N steps
  similares (ex: 1 step por campo de modelo). Overkill para 3
  sequências.
- **Fixture pytest complexa com side-effects** — esconde a
  intenção do teste. Step text fica "mágico".
- **Refactor para `.feature` minimalista + helpers Python só**
  (sem step wrapper) — perde a legibilidade do Gherkin. Step
  texts são o "contrato" lido por humanos.

### Decisão 2: Carve-out para `login.feature` e `profile_isolation.feature`

**Por quê:** esses dois arquivos testam o fluxo de login
diretamente. Se usassem o wrapper, estariam testando o wrapper
contra si mesmo — bug no wrapper passaria silencioso.

`login.feature` cobre: login OK (Italo/Ana), login fail senha
errada. Precisa escrever os steps de login inline para cada
cenário.

`profile_isolation.feature` cobre: Italo → Ana switch (logout +
login), Ana → Italo switch. Precisa escrever os steps de
**logout + login** inline porque testa a transição entre
perfis.

**Regra:** step wrapper de login pode ser usado em qualquer
cenário QUE NÃO TESTA o login. Cenários que testam login usam
steps inline.

### Decisão 3: Localização dos helpers

**Por quê `_workflows.py`:** o prefixo `_` deixa claro que NÃO é
um módulo de step definitions — é uma coleção de helpers. pytest-
bdd NÃO escaneia arquivos `_*.py` como step defs (só
`@given`/`@when`/`@then` decorators são reconhecidos), então um
arquivo sem esses decorators não polui a descoberta de steps.

Localização: `tests/bdd/step_defs/_workflows.py`. Mesmo diretório
dos step_defs para fácil descoberta, mas separado por convenção.

**Alternativa: helpers em `tests/bdd/conftest.py`** — funciona, mas
mistura fixtures de teste (autouse, session-scoped) com lógica de
workflow. Separação é mais clara.

### Decisão 4: Helpers parametrizáveis

**Por quê:** os 3 helpers têm variações reais entre cenários
(ex: `RF Pós` 60 vs 50, distribuição 60/40 vs 30/70). Helpers
com defaults fixos + kwargs override:

```python
def create_two_default_classes(
    page, live_url,
    pct_rfpos: int = 50,
    pct_rfdinamica: int = 50,
    name_rfpos: str = "RF Pós",
    name_rfdinamica: str = "RF Dinâmica",
):
```

Step wrappers expõem o subconjunto útil de variações:

```python
@when('criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%')
def _default_classes(page, live_url):
    create_two_default_classes(page, live_url)
```

Cenários que precisam de pct customizado usam um wrapper
parametrizado:

```python
@when(parsers.parse('criei as 2 classes padrão RF Pós {p1:d}% e RF Dinâmica {p2:d}%'))
def _default_classes_custom(page, live_url, p1, p2):
    create_two_default_classes(page, live_url, p1, p2)
```

**Trade-off aceito:** mais wrappers = mais superfície. Mas cada
wrapper é 3 linhas; helper central é a fonte da verdade.

## Riscos / Trade-offs

- **Helpers ficam desatualizados se a UI mudar** — mesma situação
  atual dos step defs. Mitigação: helpers documentam os
  data-testids que usam; PR review cobre.
- **Step wrappers viram "magia"** se crescerem para 20+ — manter
  ≤10 helpers. Acima disso, reavaliar.
- **Perda de granularidade** — cenários que precisam de setup
  intermediário (ex: criar 1 classe, depois 2) ficam mais
  difíceis. Mitigação: oferecer helper `create_one_class(name,
  pct)` além do helper de 2.
- **`login.feature` precisa ser mantido separado** — se o helper
  de login evoluir (ex: 2FA), `login.feature` precisa ser
  atualizado manualmente. Trade-off aceito: `login.feature` é
  o contrato do login.

## Questões em aberto

- **Versão inicial: 1 ou 3 helpers?** Recomendo 1 (login) +
  expandir depois. Iterar com base no feedback da equipe.
- **Onde colocar helpers?** Convenção `_workflows.py` em
  `step_defs/`. Alternativa: arquivo único `tests/bdd/_helpers.py`.
