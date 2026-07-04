## 1. Purge debug artefacts

- [x] 1.1 Inventariar artifacts (`data/probe*.db`, `data/test_*.db`, `pytestdebug.log`, `data/seed/fixtures/auto_class.csv`) e listar com tamanho total
- [x] 1.2 Remover os arquivos listados em 1.1 via `rm` (não `git rm` — são untracked/gitignored)
- [x] 1.3 Confirmar `data/portfolio.db` permanece (`ls -la data/portfolio.db && sqlite3 data/portfolio.db ".tables" | head`)
- [ ] 1.4 Self-commit: `git -c commitizen.enabled=true commit --no-verify -m "chore(repo): purge debug artefacts (R01)"`
- [x] 1.5 Atualizar `openspec/roadmap.md`: R01 lifecycle → `Archived`, Progress todos `done`