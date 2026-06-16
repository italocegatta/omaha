## Context

M002 fechou em 2026-06-12 com `needs-attention` (PRD §5.1). A ressalva lista:
- 1 regressão e2e em `test_s05_user_journey.py` (sem diagnóstico)
- 2 gaps de escopo (R12, R13 — não-bloqueantes)

Pior: a infraestrutura e2e está **morta neste host**. O `conftest.py:185`
hard-coda `executable_path="/usr/bin/chromium-browser"`, que não existe
em `/usr/bin/`. A justificativa do comentário em `conftest.py:8-12` ("Playwright
bundled browsers do not have a build for ubuntu26.04-x64") explica o porquê
do workaround — mas o workaround aponta para um binário que também não está
instalado. Resultado: zero testes `tests/e2e/` rodam; toda a suite depende
de TestClient + httpx.

Os fixes mais recentes do projeto — `a8b1d13 fix(import-modal): select
binding + seed rule + openspec sync` (descendente de `35bf15d feat(phase-02):
palette contrast fixes, multi-user seed, openspec infra`) — tocaram
exatamente o código que `test_s06_full_journey.py` foi escrito para travar:

- `dashboard.html:510` e `:553` (auto-matched e unmatched) — padrão
  `x-init $nextTick` + `x-effect` no `<select>` com `<template x-for>`
  interno (regra do AGENTS.md local)
- `csv_import.suggest_class_id` chamado no `_build_preview_response`

Sem rodar S06, não há prova de que esses dois fixes funcionam ponta-a-ponta
no browser real com `posicao_italo.csv` (8 categorias distintas — exercita
os 3 caminhos do matcher: Tier 1 exato, Tier 2 substring, e sem match).

## Goals / Non-Goals

**Goals:**

1. Tornar `tests/e2e/conftest.py` resiliente: preferência por binário do
   Playwright (`playwright install chromium --with-deps`), fallback para
   system chromium em `/usr/bin/chromium-browser`, e erro explícito se
   nenhum dos dois estiver disponível.
2. Executar `test_s06_full_journey.py` num browser real contra uvicorn
   real. Esperado: verde. Se vermelho, isolar qual assertion falha e
   abrir change separada para o fix.
3. Executar `test_s05_user_journey.py` para confirmar/reproduzir a
   regressão listada em M002 ressalva §5.1.
4. Atualizar `README.md` §Tests com o setup real (`uv run playwright
   install chromium --with-deps` é o passo concreto que falta).

**Non-Goals:**

- Não tocar `src/omaha/` (código de produção).
- Não adicionar novos cenários de teste além dos que S06/S05 já cobrem.
- Não implementar R12 (inline class edit frontend) ou R13 (live
  client-side recalc) — gaps separados, fora do escopo desta change.
- Não migrar a suite e2e para CI (GitHub Actions, etc.) — mudança de
  infra separada.
- Não consertar regressão S05 aqui — se reproduzir, abre change
  dedicada após esta verificação.

## Decisions

### Decision 1: Preferir binário do Playwright sobre system chromium

**Escolha:** `conftest.py` lê env var `E2E_CHROMIUM_PATH` (default:
binário instalado por `playwright install chromium`, encontrado via
`/usr/bin/env python -m playwright install --dry-run` ou caminho
hard-coded em `~/.cache/ms-playwright/chromium-*/chrome-linux/chrome`).

**Rationale:** O comentário original do conftest cita "Playwright bundled
browsers do not have a build for ubuntu26.04-x64" — mas isso era
referente a versões antigas. Playwright 1.60 (versão fixada no
`pyproject.toml` via `>=1.60.0`) mantém builds para Linux x64.
Manter `/usr/bin/chromium-browser` como fallback cobre hosts que já têm
o binário de sistema, mas não deve ser o caminho primário.

**Alternativa rejeitada:** continuar hard-coded em `/usr/bin/chromium-browser`
— quebra silenciosamente em qualquer host sem o binário (caso atual).

### Decision 2: Tornar path configurável via env var, não autodetect complexo

**Escolha:** env var simples `E2E_CHROMIUM_PATH` com default razoável.
Sem `shutil.which("chromium")` magic — autodetect adiciona branches que
falham em silêncio.

**Rationale:** O time de testes do projeto é 1 pessoa (Italo) e o
ambiente é self-hosted em residência única. Overhead de autodetect não
se paga. Env var com default documentado em `README.md` é o suficiente.

### Decision 3: `--with-deps` no `playwright install`

**Escolha:** Documentar e usar `uv run playwright install chromium
--with-deps` (não apenas `playwright install chromium`).

**Rationale:** `--with-deps` instala pacotes do sistema (`libnss3`,
`libxkbcommon0`, `libgbm1`, `libasound2t64`, etc.) que o chromium
precisa e que muitas distros não trazem por default. Sem isso, o
chromium instala mas falha ao lançar com erros crípticos de "shared
library not found".

### Decision 4: Não consertar regressão S05 dentro desta change

**Escolha:** Rodar S05, capturar output, screenshot, e stack trace.
Se falha, anotar o achado em `tests/e2e/M002_RESSALVA_DIAGNOSIS.md` e
abrir change dedicada para o fix.

**Rationale:** Misturar verificação de S06 + fix de S05 numa única
change viola o princípio de mudança atômica. S06 verde (esperado)
fecha o item mais crítico do ressalva. S05 fica como follow-up se
reproduzir.

## Risks / Trade-offs

- **Setup do host pode falhar com permissões.** `playwright install
  --with-deps` usa `apt-get install` internamente; pode pedir sudo.
  → Mitigation: rodar com `sudo` se necessário, ou documentar o
  passo no README e parar o `opsx-apply` se o usuário preferir
  setup manual.

- **S06 pode falhar e expor bug real no fix `a8b1d13`.** Verde é o
  esperado, mas se vermelho, S06 vira o "canário" que o integration
  test do `fix-import-class-suggestion` não cobriu.
  → Mitigation: design.md desta change já isola "se S06 falhar,
  abrir change separada". Sem pânico, sem fix apressado.

- **Suite e2e inteira (~480+ linhas S06 + 5 outros arquivos) pode
  tomar 5-10 min para rodar.** Tempo de iteração longo.
  → Mitigation: rodar S06 isolado primeiro. Rodar S05 isolado.
  Rodar suite full só se ambos passarem.

- **Mudança no conftest pode quebrar setup em CI futuro (se existir).**
  → Mitigation: env var tem default compatível com setup Playwright
  padrão; CI que tenha o binário em path não-Padrão pode setar
  `E2E_CHROMIUM_PATH=...` explicitamente.

## Migration Plan

Sem migration de dados ou schema. Sequência linear. Pré-requisito
**já satisfeito** no host:

- Chromium 1226 instalado em
  `~/.cache/ms-playwright/chromium-1226/chrome-linux64/chrome`
  (265 MB, `--with-deps` aplicado)
- Headless shell em
  `~/.cache/ms-playwright/chromium_headless_shell-1226/chrome-headless-shell-linux64/chrome-headless-shell`
  (180 MB)
- `DEPENDENCIES_VALIDATED` e `INSTALLATION_COMPLETE` markers presentes

Passos restantes:

1. Modificar `tests/e2e/conftest.py:177-191` (fixture `_browser`) para
   usar env var + fallback explícito para o binário já instalado.
2. Atualizar `README.md:237` para mencionar `uv run playwright install
   chromium --with-deps` como passo concreto (one-time, já feito).
3. Smoke test do conftest modificado (Task 1).
4. Executar `uv run pytest tests/e2e/test_s06_full_journey.py -v`.
5. Se 4 verde: executar `uv run pytest tests/e2e/test_s05_user_journey.py -v`.
6. Reportar achados; se 5 reproduz regressão, anotar em
   `tests/e2e/M002_RESSALVA_DIAGNOSIS.md` e abrir change dedicada.

**Rollback:** trivial — `git checkout` dos 2 arquivos modificados
(`conftest.py` + `README.md`) restaura o estado anterior. Sem migration
de banco, sem mudança de produção.

## Open Questions

- O host atual tem `apt`/sudo disponível para `playwright install
  --with-deps`? Verificar antes de rodar.
- O conftest atual tem `try/except` no `_wait_for_port`? Se sim,
  mensagem de erro do chromium-launcher será enterrada — convém
  adicionar `try/except` específico em volta de `p.chromium.launch`.
- S05 reprodução: se o assertion que falha é de polimento visual
  (screenshot diff, swatch color), pode ser flake de ordem de
  animação CSS — capturar screenshot e diff lado-a-lado antes de
  declarar regressão real.
