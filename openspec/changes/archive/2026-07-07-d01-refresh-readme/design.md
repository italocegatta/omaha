## Context

README defasado após a onda F01-F07 + R-slice + T-slice recente. Múltiplas referências a estrutura antiga (side panel, `/dashboard`, `.gsd/`) e a milestones que já entregaram (rebalancing, quotes).

I01 + I02 (paralelos a este slice) vão adicionar seções próprias de "Operação / Backup scheduler" e "Operação / TLS renewal". D01 foca no resto: intro, task table, deploy step manual → referência a I02, host-cron backup → referência a I01, testing flow atualizado, project layout, project specs aponta para `openspec/`.

## Goals / Non-Goals

**Goals:**
- README reflete o estado pós-F-slice (tabs, Família sentinel, dark mode, partials).
- Remover referências a estrutura removida (`/dashboard`, sidebar, `.gsd/`, `Italo RF2`).
- Manter compatibilidade com a audiência do README: operador que instala o app pela primeira vez.

**Non-Goals:**
- Mudança de tom/voz (PT-BR vs EN na descrição) — fora; copy mantém o estilo atual.
- Adicionar tutoriais novos (ex: "como configurar yfinance API key") — fora; é operacional.
- Reescrever AGENTS.md — fora do escopo; D01 só toca README.md.
- Adicionar badges, screenshots, GIFs — fora; manter escopo textual.

## Decisions

**D-D01.1 — Reescrita cirúrgica, não full rewrite.** Diff focado em seções defasadas; não tocar Quick Start structure, Network access section, ou Tests section (continuam válidos).

**D-D01.2 — Sem `design.md` formal.** Slice é simples o suficiente para que `proposal.md` cubra as decisões; alinhamento com precedent de slices triviais.

**D-D01.3 — I01 + I02 escrevem suas próprias seções README em paralelo.** D01 não toca "Operação / Backup" nem "Operação / TLS renewal" — as fatias I-slice são responsáveis por essas seções (cada uma tem task `4.1 Update README`). D01 foca no resto.

## Risks / Trade-offs

- **Conflito de merge com I01 + I02** → mitigação: D01 roda depois dos I-slice landarem (sequência no execution order). Se landing em paralelo, sections do D01 evitam tocar mesmas âncoras que I01/I02.
- **README longo fica pior que curto** → trade-off aceito; reflete superfície real (4 tabs + Família + Família sentinel + scheduler + certbot). Documentação sintética > documentação ausente.

## Migration Plan

- `git pull` + leem README atualizado — sem migração de dados / runtime.

## Open Questions

- (Nenhuma bloqueante.)
