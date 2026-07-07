#!/usr/bin/env bash
#
# Periodic certbot renew wrapper for the prod stack (D-I02.2 + D-I02.6).
#
# Loops `certbot renew` every CERTBOT_RENEW_INTERVAL seconds (default
# 43200 = 12h). On every successful renewal, the embedded
# --deploy-hook copies the renewed certs into nginx's expected
# location and reloads nginx in-place. Failures are logged at ERROR
# and the loop continues so a transient error (CA unreachable,
# rate-limit) does not take the scheduler down. The container
# therefore stays in `running` state across individual renewal
# failures (mirrors the failure-tolerance semantics from
# backup_scheduler.py, D-I01.5).
#
# Invoked from prod.yml as the `certbot` service:
#
#     docker compose -f prod.yml up -d certbot
#
# The image (`certbot/certbot`) and bind mount layout are
# separate from the existing `web` + `backup-scheduler`
# services (D-I02.1). This script is bind-mounted read-only at
# /scripts/certbot_loop.sh inside the container.
#
# Exit codes:
#   0  normal exhaustion of the interval (or successful renew)
#   2  FATAL configuration error (interval or domain unset/invalid);
#      the container exits so the operator notices the misconfig
#      instead of silently running a broken loop.
#
# Log format: ISO-8601 UTC timestamp + level + message, one event
# per line. Matches the format used by `backup_scheduler.py` and
# `scripts/backup.py` so a single `docker compose logs` tail
# surfaces consistent event timestamps.

set -u

CERTBOT_RENEW_INTERVAL="${CERTBOT_RENEW_INTERVAL:-43200}"

now_iso() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

log() {
  printf '%s %s\n' "$(now_iso)" "$*"
}

log_err() {
  printf '%s %s\n' "$(now_iso)" "$*" >&2
}

# Validate CERTBOT_RENEW_INTERVAL — fail fast on misconfig.
case "$CERTBOT_RENEW_INTERVAL" in
  ''|*[!0-9]*)
    log_err "ERROR certbot_loop FATAL: CERTBOT_RENEW_INTERVAL=$CERTBOT_RENEW_INTERVAL is not a positive integer"
    exit 2
    ;;
esac

if [ "$CERTBOT_RENEW_INTERVAL" -le 0 ]; then
  log_err "ERROR certbot_loop FATAL: CERTBOT_RENEW_INTERVAL must be positive, got $CERTBOT_RENEW_INTERVAL"
  exit 2
fi

# Validate CERTBOT_DOMAIN — required (no default; bootstrap is
# one-shot manual per D-I02.7).
: "${CERTBOT_DOMAIN:?CERTBOT_DOMAIN env var is required (set in shell before 'up -d')}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL env var is required (set in shell before 'up -d')}"

# Build the deploy-hook command. certbot invokes it ONLY when a
# certificate was actually renewed — failures skip it, which is
# exactly what we want (nginx keeps serving the previously valid
# cert). The three steps are atomic-on-success:
#   1. Copy the renewed fullchain.pem into nginx's expected path.
#   2. Copy the renewed privkey.pem into nginx's expected path.
#   3. Reload nginx so the new files take effect on the next request.
DEPLOY_HOOK="cp \"/etc/letsencrypt/live/${CERTBOT_DOMAIN}/fullchain.pem\" \"/etc/nginx/certs/fullchain.pem\" && cp \"/etc/letsencrypt/live/${CERTBOT_DOMAIN}/privkey.pem\" \"/etc/nginx/certs/privkey.pem\" && docker compose -f /app/prod.yml exec -T nginx nginx -s reload"

log "INFO certbot_loop started interval=${CERTBOT_RENEW_INTERVAL}s domain=${CERTBOT_DOMAIN}"

while true; do
  log "INFO certbot renew started"
  # `certbot renew` exits 0 on success OR when no renewal was
  # needed (cert not within 30d of expiry). Either way, the
  # loop continues — we only care that the exit code is logged.
  set +e
  certbot renew --deploy-hook "$DEPLOY_HOOK"
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    log "INFO certbot renew OK"
  else
    log_err "ERROR certbot renew failed exit=$rc"
  fi
  sleep "$CERTBOT_RENEW_INTERVAL"
done
