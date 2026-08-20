# runtime-environment-mode Specification

## Purpose

Define loaded environment-mode semantics for logging and session-cookie security.

## Requirements

### Requirement: Loaded environment mode controls default logs and session-cookie security

The application SHALL consume one eagerly loaded `Settings.OMAHA_ENV` value for
both default logging mode and session-cookie security. The session middleware
SHALL NOT perform a separate `os.environ` lookup for `OMAHA_ENV`.

Mode matching SHALL be exact and case-sensitive:

- exact `production` SHALL set the session cookie Secure attribute and, when
  `LOG_FORMAT` is unset, SHALL select JSON logs;
- exact `development` SHALL omit the session cookie Secure attribute and, when
  `LOG_FORMAT` is unset, SHALL select text logs;
- any other value SHALL retain non-production defaults: no Secure attribute and
  text logs when `LOG_FORMAT` is unset.

An explicit valid `LOG_FORMAT` value (`json` or `text`) SHALL continue to take
precedence for logging and SHALL NOT alter cookie security.

#### Scenario: `.env`-loaded production mode secures cookie

- **WHEN** a temporary settings file contains `OMAHA_ENV=production` and no process override is present
- **AND** the application is created from those loaded settings
- **THEN** session middleware sets `https_only` to `True`
- **AND** effective log format is `json`

#### Scenario: `.env`-loaded development mode keeps local cookie usable

- **WHEN** a temporary settings file contains `OMAHA_ENV=development` and no process override is present
- **AND** the application is created from those loaded settings
- **THEN** session middleware sets `https_only` to `False`
- **AND** effective log format is `text`

#### Scenario: Process environment wins before settings are loaded

- **WHEN** `.env` contains `OMAHA_ENV=development`
- **AND** process environment contains exact `OMAHA_ENV=production`
- **AND** `Settings` is loaded using existing Pydantic Settings precedence
- **THEN** loaded `settings.OMAHA_ENV` is `production`
- **AND** session middleware is secure
- **AND** default log format is `json`

#### Scenario: Cookie ignores later process-environment drift

- **WHEN** loaded settings contain `OMAHA_ENV=development`
- **AND** process environment is later changed to exact `production`
- **AND** the application is created from the already loaded settings
- **THEN** session middleware remains non-secure
- **AND** it does not re-read process environment

#### Scenario: Mode comparison remains case-sensitive

- **WHEN** loaded settings contain `OMAHA_ENV=Production`
- **THEN** session middleware remains non-secure
- **AND** default log format remains `text`

#### Scenario: Explicit log format does not change cookie mode

- **WHEN** loaded settings contain `OMAHA_ENV=development` and `LOG_FORMAT=json`
- **THEN** effective log format is `json`
- **AND** session middleware remains non-secure
