## Why

`verify-m002-fix-s06-real-browser` (arquivado) confirmou que a suíte
e2e estava morta neste host e que a suíte não-e2e também está vermelha
desde `35bf15d feat(phase-02): palette contrast fixes, multi-user
seed, openspec infra` (2026-06-16 11:49). Esse commit trocou o seed de
um único usuário `family` para dois usuários `Italo` + `Ana`, mas
**não atualizou nenhum dos testes** que fazem login hard-coded como
`family`. Resultado: 83 testes falhando + 12 errors na suíte não-e2e
(confirmado com `git stash` na change anterior — falha pré-existente,
não introduzida pela minha mudança).

Adicionalmente, `test_s05_user_journey.py:333` ainda asser
`assert v.startswith("#")` para tokens `--class-N` lidos do CSS, mas
o mesmo `35bf15d` converteu `--class-4` e `--class-6` para
`oklch(...)` (Phase 2 contrast fix). Esse assertion não bate mais
com o formato real e bloqueia a verificação visual do S05.

Sem corrigir isso, **a Phase 2 palette (v1.2) não tem como ser
verificada end-to-end**, e qualquer mudança futura em auth/seed
reintroduz o mesmo drift.

## What Changes

Substituir o username `family` por `Italo` em todos os testes
que fazem login como esse usuário (21 arquivos TestClient +
3 arquivos e2e Playwright — ver `Impact`); atualizar
`test_t02_seed.py` para refletir que o seed agora cria 2 users
(não 1) e que o segundo profile se chama `Ana` (não `Ana Livia` —
assertion stale que ficou escondida atrás da quebra maior do
`family`); e relaxar o `startswith("#")` em
`test_s05_user_journey.py:333` para aceitar qualquer cor CSS
parseável, já que o `oklch()` é o formato canônico pós-Phase 2.

- **Sem mudança de produção.** `src/omaha/` intocado.
- **Sem migration de banco.** Seed já cria 2 users; só alinha
  assertions.
- **Sem mudança de fixtures.** O `posicao_italo.csv` e
  `sample_broker.csv` continuam válidos — o que estava quebrado
  era o setup do login, não os dados de teste.

## Capabilities

### New Capabilities

Nenhuma. Mudança puramente de teste.

### Modified Capabilities

- `import-class-auto-suggest`: o scenario E2E real-browser
  "S06 roda verde com posicao_italo.csv" adicionado em
  `verify-m002-fix-s06-real-browser` continua válido como
  goal final, mas só fica exercitável depois desta change.
  Sem delta de spec — só dependência de execução.
- `import-modal-class-binding`: mesma situação, sem delta
  de spec.

## Impact

**Arquivos modificados — 22 no total (escopo mecânico):**

Auth hard-coded `family` → `Italo` em 21 testes:
- `tests/test_t02_assets_routes.py:99`
- `tests/test_t02_classes_routes.py:93`
- `tests/test_t03_assets_e2e.py:55`
- `tests/test_t03_auth.py:65,88,110,125,145` (5 ocorrências no mesmo
  arquivo — também muda o `username: "WRONG"` em :65 para um usuário
  válido + senha errada, não um user inexistente)
- `tests/test_t03_classes_e2e.py:49`
- `tests/test_t03_imports_routes.py:33`
- `tests/test_t03_pages_routes.py:198`
- `tests/test_t04_e2e.py:69`
- `tests/test_t99_assets_patch.py:117`
- `tests/test_s02_t01_classes_patch.py:69`
- `tests/test_s02_t02_classes_post.py:65`
- `tests/test_s02_t03_classes_delete.py:67`
- `tests/test_s02_t07_classes_retire.py:18`
- `tests/test_s03_t01_assets_post.py:77`
- `tests/test_s03_t02_assets_delete.py:74`
- `tests/test_s03_t05_assets_retire.py:22`
- `tests/test_s04_t02_import_commit.py:54`
- `tests/test_s04_t03_import_get_preview.py:50,112`
- `tests/test_s04_t04_real_csv_flow.py:65`
- `tests/test_s04_t09_import_retire.py:18,33`
- `tests/e2e/test_s03_user_journey.py:51`
- `tests/e2e/test_s04_user_journey.py:190`

**Seed assertions (não é troca de string; é lógica de contagem):**
- `tests/test_t02_seed.py:120-151` — `test_seed_creates_user_and_profiles`
  e `test_seed_is_idempotent`: ajustar contagens
  `1 → 2`, username esperado `"Italo"` + `"Ana"`, e profile names
  `["Italo", "Ana Livia"]` → `["Italo", "Ana"]` (assertion stale
  pré-existente que ficou mascarada pelo bug `family`).

**Color format check:**
- `tests/e2e/test_s05_user_journey.py:333` — dropar
  `assert v.startswith("#")`. A linha acima (`assert v, f"--class-{k}
  token is empty..."`) já é o invariante real.

**Não modificados (intencionalmente):**
- `tests/test_audit_color_resolver.py:162,177,200` — `startswith("#")`
  testa o color_resolver que retorna hex; correto, mantém.
- `src/omaha/seed.py` — produção, não toca.
- `src/omaha/templates/login.html` — produção, não toca.

## Outcome esperado

Após `opsx-apply`:
- `uv run pytest tests/ --ignore=tests/e2e` → **verde**
  (213 passed, 0 failed, 0 errors — 3 skipped permanecem)
- `uv run pytest tests/e2e/test_s05_user_journey.py` → **verde**
  (login + class tokens)
- `uv run pytest tests/e2e/test_s06_full_journey.py` → ainda
  vermelho se houver regressão real no fix `a8b1d13`; verde
  se não houver.
- `src/omaha/**` intocado.
