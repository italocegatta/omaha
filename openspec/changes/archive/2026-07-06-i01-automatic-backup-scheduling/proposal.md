## Why

`prod.yml` já tem o serviço `backup` (one-shot, perfil `backup`, snapshot SQLite em `./backups/`) e `task backup` espelha isso em dev. Hoje a periodicidade é 100% manual — `docker compose -f prod.yml run --rm backup` ou `task backup` ad-hoc. PRD §3.4 cita "scheduled" como modo de operação mas ninguém cabeou o timer. Sem agendamento, backup só roda quando alguém lembra — em produção isso vira janela de perda de dados crescente até o próximo manual.

## What Changes

- Adicionar serviço `backup-scheduler` em `prod.yml` que executa o snapshot periodicamente (sem perfil, sobe com `up -d` por padrão).
- Reusar `omaha:prod` image + `command` do `backup` atual; o scheduler é um loop com `sleep` entre execuções, ou um sidecar `docker-compose-cron`-style.
- Documentar a janela de retenção / frequência como variáveis de ambiente (`BACKUP_INTERVAL`, padrão 24h).
- README seção "Operação" descreve o comportamento e como desabilitar.

## Capabilities

### New Capabilities
- `backup-scheduling`: capability descreve a periodicidade, o ponto de entrada (serviço Docker com loop), a frequência default, e o comportamento de falha (exit não-zero vira log, container continua tentando).

### Modified Capabilities

Nenhuma capability existente precisa de delta — `backup` em si já está documentado pelo nome do serviço e pelo `task backup`. O scheduling é uma camada nova, não uma mudança no contrato de backup.

## Impact

- `prod.yml` (novo serviço `backup-scheduler`, env vars).
- `README.md` (seção Operação / Backup).
- Sem mudança em `scripts/backup.py` — reusa verbatim.
- Sem mudança em DB / templates / solver / cotação / auth.
- Volume `omaha-data` continua read-only no serviço; volume `./backups` continua bind mount.
