## Contexto

A suite BDD (`tests/bdd/`) tem 30 cenários em PT-BR. Os cenários
seguem um padrão recorrente de setup:

1. **Bootstrap de auth** — login + seleção de perfil. Repetido
   em ~25 cenários.
2. **Bootstrap de profile switch** — logout + login como outro
   perfil. Repetido nos cenários de `profile_isolation.feature`
   e em cenários futuros que precisem de cross-profile
   visibility.
3. **Bootstrap de classes** — criar 1 classe (`+ Nova classe`
   inline) ou 2 classes (`RF Pós` 50% + `RF Dinâmica` 50% via
   snapshot). 1-classe aparece em ~3 cenários, 2-classes em
   ~10.
4. **Bootstrap de ativos** — criar 1 ativo (modal direto) ou 4
   ativos com distribuição não-igual (loop sobre classes).
   1-ativo em ~2 cenários hoje, 4-ativos em 2 cenários
   (tendência de crescer).

Total de duplicação: ~150 steps redundantes entre os arquivos
`.feature`. pytest-bdd NÃO suporta composição de cenários
(limite confirmado por docs oficiais e source do `scenario.py`),
então não dá pra escrever "executar cenário de login como step".

A documentação do pytest-bdd oferece três mecanismos de reuso:

| Mecanismo | Cobertura | Limitação |
|-----------|-----------|-----------|
| `Contexto:` (Background) | Por arquivo | Repete entre arquivos |
| Steps em `conftest.py` | Cross-file | Cada step é uma ação atômica, não uma sequência |
| Step aliases | Mesma função | Não compõe ações |

A lacuna: **sequência multi-step que se repete cross-file**.

## Decisões

### Decisão 1: Workflow Python + step wrapper fino

**Por quê:** encapsula a sequência multi-step em uma função
Python reutilizável. Step wrapper Gherkin vira uma linha.
Workflow é o "single source of truth" — mudança de regra de
negócio = editar 1 função, propagação automática para todos os
cenários que usam o wrapper.

**Como:**

```python
# tests/bdd/step_defs/_workflows.py (novo)

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassSpec:
    name: str
    target_pct: int


@dataclass(frozen=True)
class AssetSpec:
    class_name: str
    ticker: str
    target_pct: int


DEFAULT_TWO_CLASSES: list[ClassSpec] = [
    ClassSpec("RF Pós", 50),
    ClassSpec("RF Dinâmica", 50),
]

DEFAULT_FOUR_ASSETS: list[AssetSpec] = [
    AssetSpec("RF Pós", "TESOURO_SELIC_2029", 60),
    AssetSpec("RF Pós", "CDB_LIQUIDEZ_2027", 40),
    AssetSpec("RF Dinâmica", "FII_HSML11", 30),
    AssetSpec("RF Dinâmica", "ACAIO_PETR4", 70),
]


def login_and_pick_profile(
    page, live_url, profile: str, password: str = "test-password"
):
    """Login + profile pick.

    Pré-condição: nenhuma (entry point).

    data-testids:
      - input[name=username]
      - input[name=password]
      - button[type=submit]
      - form.profile-picker button
    """
    page.goto(f"{live_url}/login")
    page.fill('input[name="username"]', profile)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url(re.compile(r"/profiles$"), timeout=5000)
    page.locator("form.profile-picker button").filter(
        has_text=profile
    ).first.click()
    page.wait_for_url(re.compile(r"/$"), timeout=5000)


# tests/bdd/step_defs/common_steps.py (modificado)

@given(parsers.re(r'(que )?estou logado como "(?P<profile>[^"]+)"'))
def _w_logged_in_as(page, live_url, profile):
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
+    Dado que estou logado como "<profile>"
     Quando abro o editor de classes
     ...
```

**Alternativas consideradas:**

- **Contexto:** — cobre só dentro do arquivo. Login teria que
  aparecer em `Contexto:` de 6 arquivos diferentes = ainda
  duplicação cross-file.
- **Step generation via `stacklevel`** — útil para gerar N
  steps similares (ex: 1 step por campo de modelo). Overkill
  para 6 sequências.
- **Fixture pytest complexa com side-effects** — esconde a
  intenção do teste. Step text fica "mágico".
- **Refactor para `.feature` minimalista + workflows Python
  só** (sem step wrapper) — perde a legibilidade do Gherkin.
  Step texts são o "contrato" lido por humanos.

### Decisão 2: Tabela de carve-out per-workflow

**Por quê:** o carve-out do spec original (login inteiro +
profile_isolation inteiro) é restritivo demais. Um cenário em
`login.feature` que testa "login OK + criar 1 classe" deve
poder usar o wrapper de criar-classe. Apenas o wrapper de login
precisa ser evitado nesse arquivo.

**Tabela de carve-out:**

| Workflow | Carve-out (arquivos que NÃO usam) |
|---|---|
| `login_and_pick_profile` | `login.feature`, `profile_isolation.feature` |
| `switch_profile` | `profile_isolation.feature` |
| `create_one_class` | (nenhum) |
| `create_two_default_classes` | (nenhum) |
| `add_one_asset` | (nenhum) |
| `create_four_assets` | (nenhum) |

**Regra per-workflow:** um cenário em arquivo carve-out pode
usar wrappers de workflows NÃO-carved-out. Ex: cenário em
`login.feature` que valida pós-login pode usar
`create_one_class` sem violar o carve-out.

### Decisão 3: Pré-condições via assertion explícita no workflow

**Por quê:** workflows compostos têm dependências implícitas.
`create_two_default_classes` exige login prévio; sem assertion
explícita, o erro aparece longe da causa (no step seguinte, com
mensagem confusa de "elemento não encontrado").

**Como:**

```python
def create_two_default_classes(page, live_url, classes=None):
    """Snapshot: cria N classes via POST /classes.

    Pré-condição: usuário logado (chame
    ``login_and_pick_profile`` antes).

    data-testids:
      - new-class-name-input
      - new-class-pct-input
      - classes-save-button
    """
    if classes is None:
        classes = DEFAULT_TWO_CLASSES
    if not page.url.endswith("/"):
        raise RuntimeError(
            f"create_two_default_classes requer login prévio. "
            f"Chame login_and_pick_profile antes. URL atual: {page.url}."
        )
    ...
```

**Alternativa: auto-login no workflow** — workflow chama
`login_and_pick_profile` se não estiver logado. Rejeitado:
esconde intenção, torna o workflow "auto-suficiente" mas com
perfil default mágico.

**Alternativa: fixture pytest `logged_in`** — wrapper declara
dependência no nome. Rejeitado: indirection extra, mas falha
de forma similar.

**Decisão final:** docstring documenta pré-condição, função
asserta com mensagem clara, contribuidor recebe erro útil
quando viola.

### Decisão 4: Localização dos workflows

**Por quê `_workflows.py`:** o módulo vive em
`tests/bdd/step_defs/_workflows.py` (mesmo diretório dos
`step_defs`). Não tem decorators `@given`/`@when`/`@then`, então
pytest-bdd não tenta registrar step definitions dele. O prefixo
`_` é cosmético (convenção local) — o motivo real é a ausência
de decorators, não o underscore.

**Migrar `_wipe_profile` do conftest para cá?** NÃO.
`_wipe_profile` é fixture de setup de teste (sqlite, autouse),
não workflow de UI. Convenção: workflows são funções que
tocam a página Playwright e encapsulam steps Gherkin
repetidos. Fixtures de DB/servidor ficam no conftest.

### Decisão 5: Workflows parametrizáveis via dataclasses

**Por quê:** os 6 workflows têm variações reais entre cenários
(ex: `RF Pós` 60 vs 50, distribuição 60/40 vs 30/70, switch
de perfil). Workflows com dataclass como input (default =
constante) escalam pra N items sem quebrar signature.

**Como:**

```python
def create_two_default_classes(
    page, live_url, classes: list[ClassSpec] | None = None
):
    if classes is None:
        classes = DEFAULT_TWO_CLASSES
    ...


def create_four_assets(
    page, live_url, assets: list[AssetSpec] | None = None
):
    if assets is None:
        assets = DEFAULT_FOUR_ASSETS
    ...
```

**Step wrappers expõem o subconjunto útil de variações:**

```python
# default
@given('criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%')
def _w_default_classes(page, live_url):
    create_two_default_classes(page, live_url)


# parametrizado
@given(parsers.parse('criei as 2 classes padrão RF Pós {p1:d}% e RF Dinâmica {p2:d}%'))
def _w_default_classes_pct(page, live_url, p1, p2):
    create_two_default_classes(page, live_url, [
        ClassSpec("RF Pós", p1),
        ClassSpec("RF Dinâmica", p2),
    ])
```

**Convenção de nomenclatura dos wrappers:** prefixo `_w_`
(workflow-wrapper) para os wrappers que chamam workflows.
Contract test `test_wrappers_delegate_to_workflows` itera por
todos os wrappers com esse prefixo e verifica que o body chama
uma função de `_workflows.py`.

**Trade-off aceito:** dataclass + constantes adicionam ~20
linhas de boilerplate, mas eliminam inconsistência entre
`create_two_default_classes` (kwargs flat) e
`create_four_assets` (lista de tuplas).

## Riscos / Trade-offs

- **Workflows ficam desatualizados se a UI mudar** — mesma
  situação atual dos step defs. Mitigação: docstrings
  documentam os data-testids; PR review cobre.
- **Step wrappers viram "magia"** se crescerem para 20+ —
  manter ≤10 workflows. Acima disso, reavaliar.
- **Refactor blast radius no `git blame`** — refatorar 6
  `.feature` files num único commit confunde autoria.
  Mitigação: task 14.0 da change força 1 commit por arquivo
  refatorado.
- **pytest-xdist race em `clean_seeded_profiles`** — autouse
  fixture que limpa profiles antes de cada cenário compartilha
  o mesmo SQLite (`data/test_bdd.db`) com uvicorn
  session-scoped. Hoje `test-bdd` roda serial (sem xdist) —
  risco teórico. Se a equipe adicionar xdist no futuro, race
  vira flake. Fora do escopo desta change; ticket separado.
- **Carve-out só pega regressão por teste, não por linter** —
  contract test `test_carve_out_files_use_inline_steps` parse
  `login.feature` + `profile_isolation.feature` e falha se
  alguém refatorar. Mitigação coberta pelo spec
  §Requirement: Contract test — carve-out enforcement.
