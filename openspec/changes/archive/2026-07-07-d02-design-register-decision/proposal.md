## Why

Owner abriu frente visual 2026-07-06 após critique de que a paleta
"não está bonita" e "não ajuda a entender informação". Sessão
exploratória comparou 4 referências (Status Invest, híbrido SI+Omaha,
Moleskine+ caderno, outra referência) e levantou 7 gates. Decisão
precisa ser memorializada em PRD §4.10 (re-escrita como memorial, não
prescritiva) + DESIGN.md §Color strategy + §Typography + §Component
inventory antes de F08+ poder propor.

## What Changes

- Resolve os 7 gates com decisões owner (2026-07-07):
  1. Register: **Status Invest maximal, sidebar NÃO**
  2. Class-3 hue destino: **350 magenta-red** (separa de `--negative` hue 25)
  3. Display face: **Red Hat Display** (sans, 700+ portfolio header)
  4. Sidebar reintroduzida: **NÃO** (top nav F02 preservado)
  5. Light/dark toggle: **NÃO** (dark-only D-F05.10 mantido, F13 Blocked)
  6. Body warmth: **hue 60 mantém** (warm-neutral sutil, chroma ~0.012)
  7. Escopo de entrega: **3 fatias** (F08 palette → F09 typography → F10 componentes)
- Re-escreve `openspec/PRD.md` §4.10 como memorial descritivo
  (sem prescrever tokens; tokens vivem em DESIGN.md)
- Re-escreve `DESIGN.md` §Color strategy + §Typography + §Component
  inventory refletindo register SI maximal + decisões owner
- Marca §5.3 do PRD como "gate D02 resolvido, séries visuais liberadas"
- Captura decisões em nova spec `design-register-decision` para
  auditoria (D02 é gate absoluto de F08+; spec é memorial,
  não contrato runtime)

## Capabilities

### New Capabilities

- `design-register-decision`: memorializa as 7 decisões owner
  (register / class-3 hue / display face / sidebar / toggle / warmth /
  escopo) e os artefatos documentais que devem refleti-las (PRD §4.10
  memorial + DESIGN.md §Color + §Typography + §Component inventory).
  Spec descreve o contrato documental, não comportamento runtime.

### Modified Capabilities

<!-- Nenhuma. D02 é doc-only memorial; não altera REQUIREMENTS de
     nenhum spec runtime. F08+ é que vai re-derivar tokens e sincronizar
     `color-tokens` spec. -->

## Impact

**Documentos (PRD + DESIGN.md)**:

- `openspec/PRD.md` §4.10: rewrite de regras prescritivas para memorial
  descritivo do register SI maximal escolhido
- `openspec/PRD.md` §5.3: marca gate D02 como resolvido, libera F08-F12
  (F11 effectively Blocked por register ≠ A; F13 Blocked por owner
  não pedir toggle)
- `DESIGN.md` §Color strategy: re-derivação conceitual dos tokens
  per SI maximal (emerald accent 0.68 0.20 152, positive 0.79 0.19
  145, negative 0.69 0.20 25, warning amber, surface warm-neutral
  dark; class-3 magenta-red 350 — F08 vai materializar em código)
- `DESIGN.md` §Typography: Red Hat Display 700+ para portfolio header
  + Inter variable com feature-settings `tnum, cv01, ss01, ss02` em body
  (F09 vai materializar)
- `DESIGN.md` §Component inventory: tabela de 5 estados (idle/hover/
  focus/disabled/error) por elemento + table pattern upgrade (sticky
  headers, hover row bg lift, total row emphasis, action column
  só-on-hover) + section dividers hairline + ::selection + form
  autofill override + eyebrow labels + compare bar + rebalance
  warnings border-left 4px + form R$ prefix (F10 vai materializar)
- `DESIGN.md` §Iconography: "None required" vira "Material Symbols
  Outlined, scoped" (F12 vai materializar)
- `DESIGN.md` §Anti-patterns: estado feedback vocabulary table + nota
  "no sidebar reintroduce — top nav F02 preserved"

**Sem código**: zero arquivos em `src/omaha/**`, zero tests, zero
seeds. D02 não toca runtime; F08+ aplicam as decisões em código.

**Sem migration**: nenhum schema change. D02 é decisão + docs.

**Sem CI / infra**: zero `prod.yml`, zero workflows, zero scripts.

**Sem dependências novas**: nenhuma dep em `pyproject.toml`. Font face
vem via Google Fonts (mesmo padrão atual Source Serif 4), resolvido
em F09.

**Unblocks**: F08 (palette overhaul v2), F09 (typography refresh),
F10 (component state language + table pattern), F12 (Material Symbols),
R05 (hex literal audit, depende de F08), T06 (visual regression,
depende de F08+F09+F10 aplicados).

**Blockers resolved**: F11 (sidebar reintroduce) deixa de fazer
sentido (register ≠ A) — effectively Blocked; F13 (light/dark toggle)
continua Blocked (owner não pediu).
