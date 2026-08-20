## MODIFIED Requirements

### Requirement: README documents local environment mode and production distinction

The `README.md` Quick start SHALL tell local operators to use the ignored
`.env` copied from `.env.example` with `OMAHA_ENV=development`. It SHALL state
that exact, case-sensitive `OMAHA_ENV=production` enables secure session cookies
and default JSON logs, while development/non-production modes keep cookies
usable over local plain HTTP and use default text logs. It SHALL preserve the
existing `task serve` and `0.0.0.0` network guidance.

#### Scenario: Local setup documents development mode

- **WHEN** an operator follows the README Quick start
- **THEN** the documented `.env` setup includes exact `OMAHA_ENV=development`
- **AND** the command remains `uv run task serve`
- **AND** the network bind remains `0.0.0.0`

#### Scenario: README explains exact production mode

- **WHEN** an operator reads the environment-mode guidance
- **THEN** the README identifies exact case-sensitive `production` as the
  secure-cookie/JSON-log mode
- **AND** it does not suggest changing `ADMIN_PASSWORD=distendidos`
- **AND** it does not include real `.env` or MyProfit credential values

#### Scenario: Existing README freshness contracts remain intact

- **WHEN** the updated README is validated
- **THEN** four-tab navigation, Família profile guidance, OpenSpec links, dark
  palette wording, current task table, and canonical test-lane wording remain
  present
- **AND** legacy `/dashboard`, sidebar, `.gsd`, host-cron, and superseded manual
  certbot instructions remain absent as required by existing scenarios
