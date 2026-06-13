---
phase: 1
slug: audit
status: approved
shadcn_initialized: false
preset: none
created: 2026-06-13
reviewed_at: 2026-06-13
---

# Phase 1 — UI Design Contract

> Contrato visual e de interação para o entregável de auditoria do Omaha. Esta fase não redesenha componentes do app; define como o inventário de cores e estados interativos será apresentado.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none (server-rendered HTML + Alpine.js app; audit report is static HTML) |
| Icon library | none |
| Font | Inter 400/600, with system sans-serif fallback |

---

## Spacing Scale

Declared values (all multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Inline gaps, compact table cell padding |
| sm | 8px | Tight element spacing |
| md | 16px | Default element spacing |
| lg | 24px | Section padding |
| xl | 32px | Major section breaks |
| 2xl | 48px | Page-level spacing |

Exceptions: 12px field gaps and 20px card inner padding are inherited from existing app patterns and remain valid; the audit report itself uses only the scale above.

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16px (1rem) | 400 | 1.55 |
| Label / caption | 12px (0.75rem) | 400 | 1.4 |
| Heading | 18px (1.125rem) | 600 | 1.2 |
| Display | clamp(1.75rem, 3vw, 2.5rem) | 600 | 1.2 |

Body text length is capped at ~80ch for report readability.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `oklch(0.975 0.003 60)` (~#fafaf7) | Report page background |
| Secondary (30%) | `oklch(1.0 0 0)` (#fff) | Cards, tables, summary panels |
| Accent (10%) | `oklch(0.42 0.09 150)` | Page TOC links, primary "Exportar inventário" action, current sort indicator |
| Destructive | `oklch(0.50 0.18 25)` (~#c62828) | Fail badges, fail counts, severity markers |

Accent reserved for:
- In-page anchor links in the table of contents.
- The primary "Exportar inventário" action.
- The currently sorted column indicator.

It is not used for general body text, table borders, or passive status badges.

---

## Copywriting Contract

All user-visible strings are in Portuguese (PT-BR).

| Element | Copy |
|---------|------|
| Primary CTA | Exportar inventário |
| Empty state heading | Nenhuma falha de contraste encontrada |
| Empty state body | Todos os pares de cores auditados atingem o limite mínimo WCAG 2.1 AA. |
| Error state | Não foi possível gerar o inventário. Verifique se o app está rodando e se o CSS é válido, depois tente novamente. |
| Destructive confirmation | Nenhuma ação destrutiva nesta fase. |

---

## Audit Report Structure

The Phase 1 deliverable is a self-contained, static HTML inventory file.

### Visual Hierarchy

- **Primary anchor:** the report header with the title "Inventário de contraste — Omaha" and the summary counts (total pairs audited, failures, pass rate).
- **Reading order:** summary cards → table of contents → collapsible per-page inventory → CSS token inventory → failure log.
- The failure log is visually de-emphasized when empty and surfaced prominently when failures exist.

Sections, in order:

1. **Header** — title "Inventário de contraste — Omaha", generation timestamp, and summary counts (total pairs audited, failures, pass rate).
2. **Summary cards** — three cards showing: total interactive elements inventoried, total CSS color tokens inventoried, total WCAG AA failures.
3. **Table of contents** — anchors to each audited page/template.
4. **Per-page interactive inventory** — one collapsible section per page. Each section contains a table with the following columns:
   - Elemento (selector + semantic role)
   - Estado (default, hover, active, focus, disabled)
   - Cor do texto (computed foreground)
   - Cor do fundo (computed background)
   - Razão de contraste (computed)
   - Limite (AA: body 4.5:1, UI/large 3:1)
   - Status (Passa / Falha)
5. **CSS token inventory** — table with columns:
   - Token
   - Valor computado
   - Fundo adjacente padrão
   - Contraste
   - Status
6. **Failure log** — consolidated list of every failing pair, grouped by page or token, with exact selector/token and computed ratio.

Status indicators:
- **Passa** badge: green-tinted background (`--positive` mixed at 10% with `--surface`) + text label.
- **Falha** badge: destructive-tinted background (`--negative` mixed at 10% with `--surface`) + text label.
- Contrast ratios render with `font-feature-settings: "tnum"`.
- Each row shows 16×16px color swatches for both foreground and background values.

---

## Interaction Contract

- The report is read-only by default.
- Page TOC anchors scroll to the corresponding per-page section.
- Each per-page section is collapsible so the auditor can focus on one page at a time.
- A "Mostrar apenas falhas" toggle filters rows to show only failing pairs. When no failures exist, the empty state copy is shown.
- No form submissions, modals, or destructive actions are part of the report.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable |
| Third-party | none | — |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending

---

## Assumptions & Notes

- Output format is assumed to be a self-contained HTML file. If a different format (Markdown, JSON viewer) is required, update this contract before implementation.
- Report styling references the existing `app.css` token names for consistency. Because Phase 1 documents the current broken state, the report generator must inline the audited color values rather than rely on live tokens that may change in later phases.
