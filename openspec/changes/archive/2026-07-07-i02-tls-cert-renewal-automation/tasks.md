## 1. Service definition

- [x] 1.1 Add `certbot` service to `prod.yml` (image `certbot/certbot:latest`, no profile, `restart: unless-stopped`)
- [x] 1.2 Add `CERTBOT_RENEW_INTERVAL` env var (default `43200`)
- [x] 1.3 Add `CERTBOT_DOMAIN` and `CERTBOT_EMAIL` env vars (operator-supplied at deploy time)
- [x] 1.4 Mount `./certs:/etc/letsencrypt` with read-write access (certbot writes renewed certs here)
- [x] 1.5 Mount `./certs/webroot:/var/www/certbot:ro` for ACME http-01 challenge webroot
- [x] 1.6 Mount `/var/run/docker.sock:/var/run/docker.sock:ro` so the deploy hook can exec into the nginx container
- [x] 1.7 `command:` runs a wrapper script `certbot-loop.sh` that loops `certbot renew --deploy-hook "..."`

## 2. Scheduler entrypoint script

- [x] 2.1 Create `scripts/certbot_loop.sh` (bash) — reads `CERTBOT_RENEW_INTERVAL`, runs `certbot renew --deploy-hook "..."`, captures exit code, logs timestamp + exit code, sleeps interval
- [x] 2.2 Embed the deploy hook directly in the wrapper: `docker compose -f /app/prod.yml exec -T nginx nginx -s reload` (or read `COMPOSE_FILE` env if operator overrides)
- [x] 2.3 Validate `CERTBOT_RENEW_INTERVAL` at startup (positive integer, fail fast)
- [x] 2.4 Log format: ISO-8601 UTC timestamp + level + message

## 3. Webroot directory

- [x] 3.1 Commit `certs/webroot/.gitkeep` so the bind mount has a directory to mount even when empty
- [x] 3.2 Update `.gitignore` if necessary (certs contents remain untracked; only the directory + `.gitkeep` are versioned)

## 4. README documentation

- [x] 4.1 New section "TLS renewal" explaining: initial bootstrap (one-shot `certonly`), the scheduler behavior, how to override interval, how to stop the service, how the deploy hook reloads nginx
- [x] 4.2 Runbook for "first-time setup": `mkdir -p ./certs/webroot`, then `docker compose -f prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d <domain> --email <email> --agree-tos --no-eff-email`, then `docker compose -f prod.yml up -d`

## 5. Local smoke test (best-effort)

- [x] 5.1 `docker compose -f prod.yml config` parses the new service without errors
- [x] 5.2 Document the smoke test in README (real cert renewal requires a reachable domain + Let's Encrypt rate-limit budget; CI does not exercise end-to-end)

## 6. Spec gate + archive

- [x] 6.1 `openspec validate i02-tls-cert-renewal-automation --json` returns `valid: true`
- [x] 6.2 Run `task lint` (ruff + prek) — green
- [x] 6.3 Run `task test-unit` + `task test-integration` — no regressão (zero `src/omaha/**` tocado)
- [ ] 6.4 Archive via `openspec archive i02-tls-cert-renewal-automation`; sync spec delta into `openspec/specs/tls-cert-renewal/spec.md`
- [ ] 6.5 `openspec validate tls-cert-renewal --json` returns `valid: true` (deferred to archive step)
