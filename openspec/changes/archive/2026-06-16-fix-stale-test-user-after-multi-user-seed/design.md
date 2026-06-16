## Context

`35bf15d feat(phase-02): palette contrast fixes, multi-user seed, openspec infra`
mudou o seed (`src/omaha/seed.py:25-27`) de um único usuário `family`
para dois usuários per-conta: `Italo` e `Ana`, cada um com seu próprio
profile. O commit também converteu `--class-4` e `--class-6` no
`app.css` de hex para `oklch()` para ganhar contraste WCAG AA.

Os testes não foram migrados. Resultado: 83 TestClient tests +
12 errors + 6 e2e tests (s01–s06) bloqueados no passo de login, mais
1 assertion S05 falhando por mudança de formato de cor. Detalhamento
completo em `tests/e2e/M002_RESSALVA_DIAGNOSIS.md` (escrito pela
change anterior `verify-m002-fix-s06-real-browser`).

A mudança é **mecânica** mas volumosa: 21 testes + 2 funções do
`test_t02_seed.py` + 1 assertion em `test_s05_user_journey.py:333`.
Sem redesign — só alinhamento com o estado real do seed/seed pós-`35bf15d`.

## Goals / Non-Goals

**Goals:**

1. Substituir `family` → `Italo` em 21 TestClient tests (form
   `data={"username": "family", "password": ...}` →
   `data={"username": "Italo", "password": ...}`).
2. Substituir `family` → `Italo` em 2 e2e tests Playwright
   (`test_s03_user_journey.py:51`, `test_s04_user_journey.py:190`).
3. Atualizar `test_t03_auth.py:65` — o teste "wrong password" assume
   usuário existente; trocar de `username=family` (que não existe)
   para `username=Italo` (que existe) + senha errada.
4. Atualizar `test_t02_seed.py:120-151`:
   - `len(users) == 1` → `len(users) == 2`
   - `users[0].username == "family"` → checar ambos `Italo` e `Ana`
   - `prior == 1` → `prior == 2`
   - `session.query(User).count() == 1` → `== 2`
   - `[p.name for p in profiles] == ["Italo", "Ana Livia"]` →
     `["Italo", "Ana"]` (assertion stale pré-existente que
     ficou mascarada pela quebra maior)
5. Drei `assert v.startswith("#")` em `test_s05_user_journey.py:333` —
   aceitar qualquer cor CSS (hex, oklch, rgb, named) já que o
   navegador computa todas. Manter a linha acima que checa non-empty.
6. Verificar verde: `uv run pytest tests/ --ignore=tests/e2e` (213
   passed) + `uv run pytest tests/e2e/test_s05_user_journey.py`
   (verde) + `uv run pytest tests/e2e/test_s06_full_journey.py`
   (verde, ou abrir change dedicada se vermelho por regressão real).

**Non-Goals:**

- Não tocar `src/omaha/**`.
- Não renomear `Ana` → `Ana Livia` no seed (questão de UX, fora de
  escopo).
- Não consertar a regressão S05 do polish visual (swatches, compare
  bars) — só a quebra do `#` check. Se houver regressão real de
  polish, abre change separada.
- Não consertar S06 se ele falhar por outra razão após esta
  change — também vira change separada.
- Não migrar testes para o estilo `Italo` parametrizado (ex:
  `@pytest.mark.parametrize("user", ["Italo", "Ana"])`) — fora de
  escopo; só corrigir o `family` que está quebrando.

## Decisions

### Decision 1: `family` → `Italo` (não `Ana`)

**Escolha:** Trocar para `Italo` em todos os pontos.

**Rationale:** O `_login_and_select_italo` em s04 já espera
selecionar o profile "Italo" depois do login. Trocar para `Italo`
mantém o resto do helper (seleção de profile) inalterado. Trocar
para `Ana` quebraria a próxima linha (`page.locator("form.profile-picker
button").filter(has_text="Italo").click()`).

**Alternativa rejeitada:** parametrizar login + seleção de profile
por usuário — aumenta o escopo desta change para 1 usuário apenas.
Refator depois, se necessário.

### Decision 2: `test_t02_seed.py:135` correção inline

**Escolha:** Atualizar a assertion `[p.name for p in profiles] == ["Italo", "Ana Livia"]`
para `["Italo", "Ana"]`.

**Rationale:** O `seed.py:55` cria profile com `name=username`, e
o `DEFAULT_USERS` é `(("Italo", 0), ("Ana", 1))`. A assertion
`["Italo", "Ana Livia"]` está errada mesmo antes do `family`
bug — é stale. Corrigir inline mantém o teste útil.

**Alternativa rejeitada:** trocar o seed para criar `"Ana Livia"` —
mudança de produção, fora de escopo.

### Decision 3: Manter `password_hash.startswith("$2")` no test_t02_seed.py

**Escolha:** Deixar a verificação de bcrypt hash como está.

**Rationale:** É o teste de formato de hash, não de usuário. Não
quebra e é correto.

### Decision 4: `test_t03_auth.py:65` (wrong password) → `Italo` + `WRONG`

**Escolha:** Trocar `username=family` para `username=Italo` mantendo
`password=WRONG`.

**Rationale:** O teste quer verificar "senha errada re-renderiza
form com erro". Antes do `35bf15d`, `family` existia e tinha uma
senha — senha errada → erro. Depois do `35bf15d`, `family` não
existe, então a query `db.query(User).filter_by(username="family")`
retorna `None` — o erro é mostrado mas por motivo diferente
(usuário não existe, não senha errada). Trocar para `Italo` + `WRONG`
mantém a semântica: usuário existe, senha bate errado, vê erro.

**Alternativa rejeitada:** Manter `family` (que não existe) —
tecnicamente o teste passaria (response 200 + "Usuário ou senha
inválidos"), mas a assertion `assert "Usuário ou senha inválidos"`
já passaria; o teste perde o valor de testar "wrong password" vs
"nonexistent user".

### Decision 5: `startswith("#")` em s05 → drop check

**Escolha:** Remover só a linha 333 (`assert v.startswith("#")`).
Manter linha 332 (`assert v, f"--class-{k} token is empty..."`).

**Rationale:** A invariante real é "token não-vazio". O
`startswith("#")` foi um atalho pré-Phase 2; o browser
parseia `oklch()` e `hex` igualmente. A presença/ausência é o
único invariante testável em string sem computar cor.

**Alternativa rejeitada:** Computar a cor via coloraide no teste
— adiciona dep, fora de escopo. Teste de cor real já existe
em `test_phase02_tokens.py`.

## Risks / Trade-offs

- **Quebrar sem querer se o test_t02_seed.py tiver assertions
  adicionais que dependem de "1 user".** Mitigação: rodar a
  suíte completa após a mudança; ver `tasks.md` §3.
- **`test_t03_auth.py:65` mudar para `Italo` + `WRONG` ainda
  testa o caminho "senha errada para usuário existente" — mas
  pode haver um teste separado para "user não existe".** Se
  não houver, perdemos cobertura desse caminho. Mitigação:
  verificar; se não houver, abrir issue para adicionar teste
  explícito de "user inexistente".
- **Performance:** rodar suite não-e2e (~300 testes) + 1 e2e
  (S05) = ~1-2 min total. Aceitável.

## Migration Plan

Sem migration. Sequência linear:

1. Sweep de `family` → `Italo` em 21 TestClient files + 2 e2e
   files. Pode ser feito com `sed -i 's/"username": "family"/"username": "Italo"/g'`
   em batch + verificação manual.
2. `test_t03_auth.py:65` — `family` → `Italo` (já coberto pelo
   sweep, mas manter password `WRONG`).
3. `test_t02_seed.py:120-151` — atualização de contagens e
   profile names.
4. `test_s05_user_journey.py:333` — drop `startswith("#")`.
5. Rodar suíte não-e2e completa → verde esperado.
6. Rodar `test_s05_user_journey.py` → verde esperado.
7. Rodar `test_s06_full_journey.py` — se verde, M002 ressalva
   fecha; se vermelho, abre change dedicada.

**Rollback:** trivial — `git checkout` dos 22 arquivos restaura
o estado anterior. Sem migration, sem mudança de produção.

## Open Questions

- A suíte não-e2e tem outros lugares com assertion stale
  escondida atrás do `family` bug? Vai aparecer quando rodar
  o sweep. Aceitar e tratar incrementalmente.
- S06 vai passar? A verificar — se vermelho, vira change
  dedicada.
- O test_t02_seed.py:135 assertion `["Italo", "Ana Livia"]` é
  correção inline ou deveria virar issue separada? Decidi
  inline (decision 2) para não inflar a change.
