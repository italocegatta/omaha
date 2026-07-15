## 1. prek.toml — reorganizar hooks entre stages

- [x] 1.1 Adicionar `ruff-format` ao pre-commit (priority 1, `continue-on-error: true`)
- [x] 1.2 Mover `ruff` de pre-push para pre-commit com `--fix` (priority 2, `continue-on-error: true`)
- [x] 1.3 Mover `trailing-whitespace` de pre-push para pre-commit (priority 3)
- [x] 1.4 Mover `end-of-file-fixer` de pre-push para pre-commit (priority 3)
- [x] 1.5 Adicionar `ruff` SEM `--fix` ao pre-push (priority 1, validation-only)
- [x] 1.6 Remover `trailing-whitespace` e `end-of-file-fixer` do pre-push
- [x] 1.7 Atualizar comentários de stage para refletir nova semântica

## 2. Spec — atualizar prek-hooks/spec.md

- [x] 2.1 Aplicar delta spec: MODIFIED `Stage-split hook layout`, MODIFIED `Mutating Python tooling on pre-commit`, ADDED `Validation-only ruff on pre-push`, REMOVED `Mutating Python tooling on pre-push`
- [x] 2.2 Verificar que spec resultante está coerente com `prek.toml`

## 3. Validação

- [x] 3.1 Rodar `prek run --all-files` para validar configuração
- [x] 3.2 Verificar que pre-commit stage inclui ruff-format, ruff --fix, trailing-whitespace, end-of-file-fixer
- [x] 3.3 Verificar que pre-push stage tem ruff (sem --fix) e não tem hooks mutantes
