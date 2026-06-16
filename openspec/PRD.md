# PRD: Omaha — Gestão de Investimentos Familiares

**Data:** 2026-06-16
**Versão:** 1.0
**Status:** Documento de referência
**Origem:** Migração do sistema GSD (`.planning/`) para OpenSpec (`openspec/`)

---

## 1. Definição do Produto

### 1.1 Proposta de Valor

Abrir o app, ver onde o portfólio está, confiar nos números, fechar a aba.

### 1.2 Usuários

| Perfil | Papel | Uso |
|--------|-------|-----|
| **Italo** | Operador | Importa CSV, edita classes/ativos, gerencia backup, mantém nginx/certificados |
| **Ana Livia** | Visualizadora | Acessa para conferir distribuição e saldo |

Contexto: residência única, self-hosted, acesso de laptops/celulares na rede doméstica. Sem tráfego multi-tenant, sem escala pública.

### 1.3 Stack Tecnológica

```
Frontend:  Jinja2 + Alpine.js + CSS vanilla (app.css)
Backend:   FastAPI + SQLAlchemy 2 + Pydantic V2
Banco:     SQLite
Testes:    pytest + Playwright
Ferramentas auditivas: tinycss2 + beautifulsoup4 + coloraide
Deploy:    Docker Compose + nginx TLS
Idioma UI: Português (PT-BR)
```

### 1.4 Funcionalidades Essenciais

1. Armazenar holdings por perfil com classes e alocações-alvo
2. Importar CSV de corretora com preview/review/commit + matching automático de ativos
3. Renderizar dashboard de distribuição: header por portfólio, seções por classe, barras de comparação target-vs-current, barras de progresso por ativo
4. Validar percentuais (soma 100%) antes de salvar
5. Autenticação por senha compartilhada + isolamento de dados por perfil

---

## 2. Arquitetura Atual

```
src/omaha/
├── __init__.py
├── auth.py                  # Autenticação shared-password
├── config.py                # Config (pydantic-settings)
├── csv_import.py            # Parser de CSV de corretora
├── db.py                    # Sessão SQLAlchemy
├── logging_config.py
├── main.py                  # FastAPI app factory
├── middleware.py
├── models.py                # ORM: Profile, Class, Asset, Position
├── seed.py                  # Dados iniciais
├── validators.py
├── audit/                   # ★ Fase 1: ferramenta de auditoria de contraste
│   ├── __init__.py
│   ├── cli.py
│   ├── color_resolver.py
│   ├── css_parser.py
│   ├── inventory.py
│   └── report.py
├── routes/
│   ├── assets.py
│   ├── auth.py
│   ├── classes.py
│   ├── health.py
│   ├── imports.py
│   └── pages.py
├── static/
│   └── app.css              # ★ Tema visual (alvo da Fase 2)
└── templates/
    ├── assets.html
    ├── audit_report.html     # ★ Relatório de auditoria (329 KB)
    ├── base.html
    ├── classes.html
    ├── dashboard.html        # ★ Superfície principal
    ├── import.html
    ├── import_review.html
    ├── login.html
    └── profiles.html
```

---

## 3. Mapa de Features: Implementado vs Pendente

### 3.1 Marcos Completos

| Marco | Versão | Conclusão | Entregues |
|-------|--------|-----------|-----------|
| **M001** | v1.0 | 2026-06-12 | CSV import, CRUD classes/ativos, dashboard, Playwright e2e |
| **M002** | v1.1 | 2026-06-12 | Workspace single-page, inline target editing, modal import, colapso/expansão de classes |
| **M002 ressalva** | — | `needs-attention` | 1 regressão e2e + 2 gaps de escopo (detalhados §5) |

### 3.2 Fase 1 (Audit) — ✅ COMPLETA

| Requisito | Status | Artefatos |
|-----------|--------|-----------|
| AUDT-01: Inventário de elementos interativos por página | ✅ Satisfeito | `inventory.py`, `report.py`, `audit_report.html` (329 KB), `scripts/generate_contrast_audit.py` |
| AUDT-02: Inventário de tokens CSS com contraste computado | ✅ Satisfeito | `css_parser.py`, `color_resolver.py` |
| Testes | ✅ 4 arquivos | `test_audit_css_parser.py`, `test_audit_color_resolver.py`, `test_audit_inventory.py`, `test_audit_report.py` |

### 3.3 Fase 2 (Palette) — 🔶 PESQUISA PRONTA, EXECUÇÃO PENDENTE

**Pesquisa realizada:** context, research, patterns, UI-spec, discussion-log — tudo documentado.
**Tarefas de execução ainda não realizadas:**

| Plano | Tarefa | Requisito | Descrição | Status |
|-------|--------|-----------|-----------|--------|
| 02-01 | 1 | PALT-01/02 | Corrigir tokens `:root` no `app.css`: `--class-4`, `--class-6`, adicionar `--negative-ink`/`--positive-ink`, converter `--error-bg`/`--error-fg` para OKLCH | ⬜ Pendente |
| 02-01 | 2 | PALT-01/02 | Substituir `color: #fff` hardcoded por `var(--negative-ink)` em botões delete-confirm | ⬜ Pendente |
| 02-02 | 1 | PALT-03 | Reescrever seções de cor no DESIGN.md: tabela com coluna "Contrast" (D-02), swatches corrigidos (D-04) | ⬜ Pendente |
| 02-03 | 1 | PALT-01/02 | Criar `tests/test_phase02_tokens.py` com verificação automatizada | ⬜ Pendente |

**Decisões de Design (Fase 2) já capturadas em CONTEXT.md:**

| Código | Decisão |
|--------|---------|
| D-01 | Refresh completo da seção de cores no DESIGN.md |
| D-02 | Adicionar coluna "Contrast" na tabela de tokens |
| D-03 | Sem changelog no DESIGN.md (git é o audit trail) |
| D-04 | Anotar tabela de inventário de componentes com nomes de tokens |

**Estado da validação:** `status: draft`, `nyquist_compliant: false`, `wave_0_complete: false`

### 3.4 Fases 3-5 — ⬜ NÃO INICIADAS

| Fase | Requisitos | Descrição | Depende de |
|------|-----------|-----------|------------|
| **3. Componentes** | COMP-01 a COMP-06 | Corrigir botões, links, inputs, feedback blocks, data viz fills | Fase 2 |
| **4. Validação** | CONV-01, CONV-02 | Verificar WCAG AA, documentar exceções | Fase 3 |
| **5. Regressão** | REGR-01, REGR-02 | Adicionar guarda automatizada ou checklist, documentar passos de revisão manual | Fase 4 |

**3 planos previstos (sem detalhamento ainda):**
- 03-01: Botões e links
- 03-02: Inputs, selects, textareas, feedback blocks
- 03-03: Class swatches e data viz fills

---

## 4. Mapa de Dependências

```
Fase 1 (Audit) ──────┐
                      ├──▶ Fase 2 (Palette) ──▶ Fase 3 (Components) ──▶ Fase 4 (Validation) ──▶ Fase 5 (Regression)
                      │
M002 (Single Page) ───┘
  └── needs-attention ╰── (itens paralelos, não bloqueiam)

Nenhuma fase depende de M002 estar fechado.
```

---

## 5. Itens Pendentes / Débitos Técnicos

### 5.1 M002: `needs-attention` (não bloqueante para v1.2)

| Item | Tipo | Descrição |
|------|------|-----------|
| R12 | Gap de escopo | Frontend de edição inline de classe (não implementado) |
| R13 | Gap de escopo | Recalculo live client-side (não implementado) |

> **Resolvido 2026-06-16** — `test_s05_user_journey.py` regressão
> e2e fechada por `fix-stale-test-user-after-multi-user-seed`.
> S05 + S06 verdes; ver `tests/e2e/M002_RESSALVA_DIAGNOSIS.md`
> secção "Resolution". R12/R13 permanecem como gaps de escopo.

### 5.2 Post-mortem S04 Import

5 bugs corrigidos durante a fase INSERTED (`phase-s04-import/`):

| Bug | Causa | Correção |
|-----|-------|----------|
| 1 | Alpine.js bracket notation com `x-model` | Substituir por `:value` + `@change` |
| 2 | Default class para unmatched (primeira classe) | Fallback para `''` |
| 3 | Auto-matched sem visibilidade (UX) | Mostrar tabela completa com class editável |
| 4 | Auto-matched ignorava assignment no commit | Unificar loop com 3 regras |
| 5 | Classe inválida retornava HTTP 422 | Silent skip |

87 testes de import passando, 229 total, 2 flaky e2e pré-existentes.

### 5.3 Pendências Transversais

| Item | Prioridade | Notas |
|------|-----------|-------|
| Contraste `--accent` vs `--ink` em 2.23:1 | 🔴 Falha WCAG | Descoberto na Fase 1; correção na Fase 2 |
| Remover `box-shadow` de cards (ghost-card tell) | 🟡 Polish | Documentado no DESIGN.md §Migration path |
| Migrar body bg de `#fafaf7` para off-white verdadeiro | 🟡 Polish | Documentado no DESIGN.md |
| Adicionar `font-feature-settings: "tnum"` | 🟢 Fácil | Documentado no DESIGN.md |
| Adicionar animações de barra de compare/progresso | 🟢 Fácil | Documentado no DESIGN.md (400ms/300ms staggered) |
| Adicionar face display (Source Serif 4) | 🟡 Médio | Escopo do dashboard apenas |
| `prefers-reduced-motion` media query | 🟢 Fácil | Já existe no CSS? Verificar |

---

## 6. Plano de Migração: GSD → OpenSpec

### 6.1 Situação Atual

| Sistema | Localização | Conteúdo | Estado |
|---------|------------|----------|--------|
| **GSD** | `.planning/` | PROJECT, ROADMAP, STATE, REQUIREMENTS, MILESTONES + fases | Ativo |
| **OpenSpec** | `openspec/` | `config.yaml` vazio, `specs/` vazio, `changes/` vazio | Setup inicial |
| **Comandos OpenSpec** | `.opencode/commands/` | 8 comandos opsx | Configurados |
| **Skills OpenSpec** | `.opencode/skills/` | 8 skills openspec-* | Instalados |

### 6.2 Estrutura OpenSpec

```
openspec/
├── config.yaml              # Contexto do projeto, regras por artefato
├── specs/                   # Especificações canônicas (capacidades)
│   └── ...                  # specs.md por capacidade
└── changes/                 # Mudanças ativas/arquivadas
    ├── archive/             # Mudanças concluídas
    └── ...                  # Mudanças ativas (proposta → design → spec delta → tasks)
```

### 6.3 Fluxo de Trabalho OpenSpec

```
1. Propor mudança        → opsx-propose    (gera proposal.md + design.md + spec + tasks)
2. Explorar / pensar      → opsx-explore    (modo investigação, sem implementar)
3. Aplicar tarefas        → opsx-apply      (implementa tarefas sequencialmente)
4. Verificar              → opsx-verify     (valida implementação vs artefatos)
5. Arquivar               → opsx-archive    (move para changes/archive/)
6. Sincronizar specs      → opsx-sync-specs  (delta spec → main spec)
```

### 6.4 Recomendação de Migração

A abordagem recomendada é **por fase/plano da v1.2**, não uma migração bulk:

| Passo | Ação | Resultado |
|-------|------|-----------|
| 1 | Popular `config.yaml` com contexto do projeto | Agentes OpenSpec têm visão correta |
| 2 | Criar change "phase-02-palette" via `opsx-propose` | Proposal + design + spec + tasks para Fase 2 |
| 3 | Executar Fase 2 via `opsx-apply` | Implementação com verificação |
| 4 | Arquivar change | `changes/archive/phase-02-palette` |
| 5 | Repetir 2-4 para Fases 3, 4, 5 | Cada fase como change independente |
| 6 | Sincronizar specs canônicas | `openspec/specs/` com especificações finais |
| 7 | Manter GSD como referência histórica | `.planning/` READ-ONLY após migração |

### 6.5 O Que Precisa Ser Configurado no OpenSpec

- [ ] **`config.yaml`**: Adicionar context (tech stack, convenções, domínio) e regras por artefato
- [ ] **`specs/`**: Criar specs canônicas para capacidades core: import, dashboard, classes, assets, auth, audit
- [ ] **Primeira change**: "phase-02-palette" trazendo as 3 tarefas de execução pendentes
- [ ] **Integração com agentes**: Skills OpenSpec já instalados, comandos opsx disponíveis

---

## 7. Matriz de Rastreabilidade (v1.2)

| Req | Descrição | Fase | Status | Change OpenSpec |
|-----|-----------|------|--------|-----------------|
| AUDT-01 | Inventário elementos interativos | 1 | ✅ | Histórico GSD |
| AUDT-02 | Inventário tokens CSS com contraste | 1 | ✅ | Histórico GSD |
| PALT-01 | Tokens design com pairs foreground/background | 2 | 🔶 Pendente execução | phase-02-palette |
| PALT-02 | Cada token pair com contraste mínimo documentado | 2 | 🔶 Pendente execução | phase-02-palette |
| PALT-03 | DESIGN.md atualizado | 2 | 🔶 Pendente execução | phase-02-palette |
| COMP-01 | Botão primary legível todos estados | 3 | ⬜ | phase-03-components |
| COMP-02 | Botão secondary legível todos estados | 3 | ⬜ | phase-03-components |
| COMP-03 | Links legíveis todos estados | 3 | ⬜ | phase-03-components |
| COMP-04 | Inputs/selects/textareas legíveis | 3 | ⬜ | phase-03-components |
| COMP-05 | Feedback blocks (erro/sucesso/info) legíveis | 3 | ⬜ | phase-03-components |
| COMP-06 | Class swatches e data viz fills distinguíveis | 3 | ⬜ | phase-03-components |
| CONV-01 | Método documentado para verificar contraste WCAG AA | 4 | ⬜ | phase-04-validation |
| CONV-02 | Exceções de acessibilidade documentadas | 4 | ⬜ | phase-04-validation |
| REGR-01 | Guarda automatizada ou checklist pré-merge | 5 | ⬜ | phase-05-regression |
| REGR-02 | Passos de revisão manual documentados | 5 | ⬜ | phase-05-regression |

**Total:** 15 requisitos v1 — 2 satisfeitos, 3 com pesquisa pronta (execução pendente), 10 não iniciados.

### 7.1 Requisitos Futuros (v2+)

| Req | Descrição | Prioridade |
|-----|-----------|------------|
| THEM-01 | Modo claro/escuro | Baixa |
| THEM-02 | Cor de destaque configurável | Baixa |

---

## 8. Apêndice: Estado dos Artefatos GSD

### 8.1 `.planning/` — Inventory

| Artefato | Conteúdo | Atualizado | Notas |
|----------|----------|-----------|-------|
| `PROJECT.md` | Definição do projeto, milestones, context, decisões, constraints | 2026-06-13 | Após iniciar v1.2 |
| `ROADMAP.md` | Fases 1-5 com detalhes, dependências, planos, progresso | 2026-06-13 | Phase 2 status ainda "Not started" (desatualizado) |
| `STATE.md` | Posição atual, progresso, blockers, decisões recentes | 2026-06-13 | Indica Fase 1 EXECUTING (desatualizado) |
| `REQUIREMENTS.md` | 15 reqs v1, 2 reqs v2, out of scope, traceability matrix | 2026-06-13 | Status "Pending" para todos (desatualizado) |
| `MILESTONES.md` | M001 completo, M002 completo (needs-attention), v1.2 pending | — | Desatualizado (v1.2 é o ativo) |
| `config.json` | Workflow config | — | `_auto_chain_active: false` |
| `phase-s04-import/POST-MORTEM.md` | 5 bugs do import, causas e correções | 2026-06-13 | Completo |

### 8.2 `.planning/phases/` — Inventory

| Fase | Arquivos | Estado |
|------|----------|--------|
| `01-audit/` | 11 arquivos (planos, summaries, patterns, research, review, UAT, UI-spec, validation, verification) | ✅ Completo |
| `02-palette/` | 7 arquivos (planos, context, discussion, patterns, research, UI-spec, validation) | 🔶 Pesquisa/criação completa, execução pendente |

---

## 9. Recomendações Imediatas

1. **Popular `openspec/config.yaml`** com contexto do projeto (tech stack, PT-BR UI, WCAG target, etc.)
2. **Criar change "phase-02-palette"** via `opsx-propose` para executar as 3 tarefas pendentes da Fase 2
3. **Corrigir `--accent` vs `--ink` contrast failure** (2.23:1) — prioridade máxima dentro da Fase 2
4. **Diagnosticar `test_s05_user_journey.py`** regressão e decidir se corrige ou descope
5. **Atualizar artefatos GSD** com status real ou marcar como READ-ONLY históricos

---

*PRD sintetizado a partir de: PRODUCT.md, DESIGN.md, `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/MILESTONES.md`, `.planning/phases/01-audit/*`, `.planning/phases/02-palette/*`, `.planning/phase-s04-import/POST-MORTEM.md`, `openspec/config.yaml`*
