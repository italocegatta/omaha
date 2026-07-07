# tls-cert-renewal Specification

## Purpose
TBD - created by archiving change i02-tls-cert-renewal-automation. Update Purpose after archive.
## Requirements
### Requirement: A scheduled service runs `certbot renew` periodically

The system SHALL run `certbot renew` automatically on a fixed
interval in production via a `certbot` service defined in `prod.yml`.
The service SHALL use the official `certbot/certbot` image and SHALL
loop with a sleep between invocations. Each invocation SHALL be
idempotent: `certbot renew` only acts on certificates within 30
days of expiry.

#### Scenario: Scheduler is up by default

- **WHEN** the operator runs `docker compose -f prod.yml up -d` after
  the initial certificate has been obtained
- **THEN** the `certbot` service starts alongside `web`, `nginx`,
  and `backup-scheduler` and begins its periodic loop without
  further input

#### Scenario: Renewal outside the 30-day window is a no-op

- **WHEN** the scheduler fires and the certificate in
  `/etc/letsencrypt/live/<domain>/` is more than 30 days from
  expiry
- **THEN** `certbot renew` exits 0 without modifying the certificate
  and the scheduler proceeds to sleep until the next interval

#### Scenario: Renewal inside the 30-day window produces a new cert

- **WHEN** the scheduler fires and the certificate is within 30
  days of expiry
- **THEN** `certbot renew` obtains a new certificate from Let's
  Encrypt, writes it under `/etc/letsencrypt/live/<domain>/`, and
  invokes the deploy hook

### Requirement: The deploy hook reloads nginx after a successful renewal

The system SHALL configure `certbot` with a `--deploy-hook` that
reloads `nginx` after every successful renewal. The hook SHALL use
`docker compose -f <prod.yml-path> exec -T nginx nginx -s reload`
so that the nginx container picks up the new
`/etc/nginx/certs/fullchain.pem` and `privkey.pem` without
restarting.

#### Scenario: Successful renewal triggers nginx reload

- **WHEN** `certbot renew` writes a new certificate to
  `/etc/letsencrypt/live/<domain>/fullchain.pem`
- **THEN** the deploy hook invokes
  `docker compose -f /app/prod.yml exec -T nginx nginx -s reload`
  and nginx begins serving the new certificate on its next request

#### Scenario: Failed renewal does not invoke the deploy hook

- **WHEN** `certbot renew` exits non-zero (e.g., CA unreachable,
  rate limit)
- **THEN** no deploy hook is invoked, nginx keeps serving the
  previously valid certificate, and the scheduler logs the failure

### Requirement: Renewal interval is configurable

The system SHALL expose the interval between `certbot renew`
invocations as the `CERTBOT_RENEW_INTERVAL` environment variable,
interpreted as integer seconds. The default value SHALL be `43200`
(12 hours). The service SHALL read the variable at start time.

#### Scenario: Default interval is 12 hours

- **WHEN** `prod.yml` is brought up without overriding
  `CERTBOT_RENEW_INTERVAL`
- **THEN** the scheduler waits 43200 seconds between renewal
  invocations

#### Scenario: Operator shortens the interval

- **WHEN** the operator sets `CERTBOT_RENEW_INTERVAL=21600` in the
  deploy environment before `docker compose -f prod.yml up -d`
- **THEN** the scheduler waits 21600 seconds (6 hours) between
  invocations

### Requirement: A failed renewal does not stop the scheduler

The system SHALL keep the `certbot` container running indefinitely
across individual renewal failures. A non-zero exit code from
`certbot renew` SHALL be logged with the run's UTC timestamp; the
scheduler SHALL then sleep `CERTBOT_RENEW_INTERVAL` seconds and
attempt the next run.

#### Scenario: Network failure during renewal logs and continues

- **WHEN** `certbot renew` exits non-zero because the Let's Encrypt
  CA endpoint is unreachable
- **THEN** the scheduler logs the exit code and error output to
  `docker compose logs certbot` and proceeds to the next scheduled
  run after `CERTBOT_RENEW_INTERVAL` seconds without exiting the
  container

#### Scenario: Three consecutive renewal failures still leave the scheduler up

- **WHEN** the scheduler has logged three consecutive non-zero
  exits from `certbot renew`
- **THEN** the container remains in `running` state and continues
  to attempt the next scheduled run

### Requirement: The certbot container has write access to the certificate directory

The system SHALL mount the host directory `./certs` as
`/etc/letsencrypt` with read-write access inside the `certbot`
container, so that renewed certificates are persisted on the host
and survive container restarts. The `nginx` service SHALL keep its
existing read-only mount of `./certs:/etc/nginx/certs:ro`.

#### Scenario: Renewed cert appears on the host

- **WHEN** `certbot renew` writes a new
  `/etc/letsencrypt/live/<domain>/fullchain.pem`
- **THEN** the file is visible at `./certs/live/<domain>/fullchain.pem`
  on the host after the run completes

#### Scenario: nginx keeps read-only mount

- **WHEN** the operator inspects the `nginx` service volumes
- **THEN** `./certs` is mounted as `:ro` and the `nginx` container
  cannot modify certificate files

### Requirement: The ACME http-01 challenge webroot is shared between nginx and certbot

The system SHALL mount `./certs/webroot` (a host directory the
operator creates once) as `/var/www/certbot` inside the `nginx`
container (read-only) and as the `--webroot` path inside the
`certbot` container. This allows certbot to write the challenge
file and nginx to serve it on port 80, satisfying the ACME http-01
challenge.

#### Scenario: ACME challenge round-trips through nginx

- **WHEN** Let's Encrypt requests
  `http://<domain>/.well-known/acme-challenge/<token>`
- **THEN** nginx serves the file from `/var/www/certbot` (which is
  the bind mount of `./certs/webroot`) and Let's Encrypt validates
  the challenge

#### Scenario: Missing webroot directory fails fast

- **WHEN** the operator runs `docker compose -f prod.yml up -d`
  without first creating `./certs/webroot/`
- **THEN** the bind mount for nginx fails and the operator sees a
  clear error message instructing them to `mkdir -p
  ./certs/webroot` (documented in README)

### Requirement: The certbot service can be disabled without affecting other services

The system SHALL allow the operator to start the rest of the
production stack (`web`, `nginx`, `backup-scheduler`) without
starting `certbot`. Disabling the certbot service SHALL NOT
require modifying `prod.yml`.

#### Scenario: Stopping the certbot scheduler does not touch other services

- **WHEN** the operator runs `docker compose -f prod.yml stop
  certbot`
- **THEN** the `certbot` container exits and `web`, `nginx`, and
  `backup-scheduler` continue running unaffected
