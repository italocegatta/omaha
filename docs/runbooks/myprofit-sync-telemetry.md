# MyProfit sync telemetry runbook

This runbook produces descriptive evidence only. It does not change sync
behavior, timeout, retry, connector behavior, F68, or application
infrastructure. Application telemetry has one authoritative boundary:
`myprofit_telemetry` messages emitted by logger `omaha` to stdout. The
application does not own a telemetry file, table, query endpoint, collector,
or retention policy.

## 1. Source discovery and retention gate

### 1.1 Identify source before collecting

Record a local source worksheet before filtering anything:

| Field | Required value |
|---|---|
| `source_kind` | `dev-stdout-capture`, `compose-web-stdout`, or `operator-retained-segment` |
| `source_identity` | launcher/supervisor identity, or Compose service `web`; redact host/container details before sharing |
| `format` | `json` or `text`; determine from retained records, not guesswork |
| `window_start` / `window_end` | requested UTC coverage, with inclusive boundaries |
| `segments` | operator-declared segment sequence; use opaque labels in shared evidence |
| `earliest_seen` / `latest_seen` | timestamps found after extraction |
| `coverage_gaps` | missing, truncated, rotated-away, or unavailable intervals |

Development source is stdout of the currently used launcher (`task serve`,
`task serve-prod`, or an already configured supervisor capture). Inspect the
launcher or supervisor that owns that stdout and use only its retained output.
If stdout was displayed but never captured, historical lines cannot be
recovered. Do not convert a terminal, process descriptor, or arbitrary host
file into an application retention claim.

Production Compose source is stdout for the existing `web` service. This
bounded, non-following retrieval asks Docker for only the declared time window
and pipes directly into the safe extractor; it does not create a complete raw
Compose capture:

```sh
WINDOW_START='operator-supplied-utc-start'
WINDOW_END='operator-supplied-utc-end'
SOURCE_FORMAT='json'  # use json or text after inspecting retained output
case "$SOURCE_FORMAT" in
  json)
    timeout 30s docker compose -f prod.yml logs \
      --no-color --no-log-prefix \
      --since "$WINDOW_START" --until "$WINDOW_END" web \
      | jq -r -c 'select(type == "object" and .logger == "omaha" and .exc_info == null and (.msg | type) == "string" and (.msg | startswith("myprofit_telemetry "))) | [.ts, .msg] | @tsv' \
      > "$OPERATOR_CAPTURE"
    ;;
  text)
    timeout 30s docker compose -f prod.yml logs \
      --no-color --no-log-prefix \
      --since "$WINDOW_START" --until "$WINDOW_END" web \
      | sed -nE '/^[^[:space:]]+ (DEBUG|INFO|WARNING|ERROR|CRITICAL) omaha myprofit_telemetry /{s/^([^[:space:]]+) (DEBUG|INFO|WARNING|ERROR|CRITICAL) omaha (myprofit_telemetry .*)$/\1\t\3/p}' \
      > "$OPERATOR_CAPTURE"
    ;;
  *) exit 2 ;;
esac
```

`$OPERATOR_CAPTURE` is an operator-owned safe extraction destination, not an
application log path. The command does not follow, restart, reconfigure, or
write to Compose services. Docker's available stdout retention is
deployment-managed; an empty or truncated result is evidence loss, not proof
that no run occurred.

For already retained development or rotated output, use only the exact files
or segments declared by the operator. Do not glob directories or discover
unrelated files. Inventory each declared segment locally, then retain only
the safe extracted artifact:

```sh
for SEGMENT in "$SEGMENT_1" "$SEGMENT_2"; do
  test -r "$SEGMENT" || exit 2
  stat --format='bytes=%s modified=%y' -- "$SEGMENT"
done
```

Keep segment identity and coverage in the worksheet, not in shared telemetry
output. Rotation is not recovery: never concatenate inferred boundaries,
reconstruct missing lines, or treat adjacent timestamps as a join. If any
requested interval is unavailable, record the gap and continue only as a
limited descriptive analysis.

The minimum observation window is **four weeks**, targeting **4–8 real runs per
week**. The worksheet label is `4–8 real runs per week`. Extend to **eight weeks** when a week has fewer than four real
runs, retention is partial, terminal coverage is incomplete, or records are
invalid. If four complete weeks are unavailable, or the eight-week extension
still cannot supply defensible coverage and volume, report exactly
`insufficient-evidence`. Do not infer absence of runs, failures, expiry, or
UI-limit events from missing stdout.

## 2. Exact event contract and bounded extraction

### 2.1 Canonical message

The only accepted payload is this exact fixed-order message:

```text
myprofit_telemetry version=1 event=<event> job_id=<uuid> domain=<domain> status=<status> stage=<stage> code=<code> duration_ms=<integer-or-na> total_duration_ms=<integer-or-na>
```

Every field is present exactly once. `duration_ms` and
`total_duration_ms` are either the literal `na` or a non-negative decimal
integer from `0` through `86400000` inclusive. `job_id` is a UUID-shaped
version 1–5, RFC-4122-variant value. Grouping uses its lowercase-equivalent
form only when the same UUID differs by hexadecimal case; no other repair is
allowed.

Finite values are:

```text
event:  transition | stage | terminal | ui_limit
domain: job | connector | browser | preview_handoff | polling_ui | concurrency
status: queued | running | succeeded | failed | expired | rejected
stage:  credentials | browser | login | two_factor | navigation | export |
        download | cleanup | preview | connector | queue | poll | ui |
        handoff | terminal | concurrency | unknown
code:   household_read_only | ambiguous_profile | unknown_profile |
        controls_not_found | timeout | browser_failed | failed |
        authentication_unconfirmed | empty_file | file_failed | launch_failed |
        page_failed | preview_failed | browser_close_failed |
        temporary_files_failed | started | transitioned | local_limit_reached |
        sync_in_progress | success | unknown
```

`na` is the fixed value for a duration not applicable to an event. Do not
replace it with zero, null, an estimate, or a value copied from another
event. `failed` is an allowlisted status and code with different meanings;
the terminal status, not the code alone, classifies a run.

### 2.2 Extract only the message from each envelope

JSON mode is the existing seven-key `JsonFormatter` envelope. Its exact key
set is `ts`, `level`, `logger`, `msg`, `module`, `line`, `exc_info`. For
telemetry extraction, require `logger == "omaha"`, `exc_info == null`, and a
string `msg` beginning with `myprofit_telemetry `. Retain only `ts` and `msg`
in the analysis copy; discard the other envelope fields.

For each operator-declared JSON segment:

```sh
timeout 30s jq -r -c \
  'select(type == "object"
    and (keys | sort) == ["exc_info","level","line","logger","module","msg","ts"]
    and .logger == "omaha"
    and .exc_info == null
    and (.msg | type) == "string"
    and (.msg | startswith("myprofit_telemetry ")))
  | [.ts, .msg] | @tsv' \
  "$SEGMENT"
```

Text mode uses the configured prefix
`timestamp level logger message`. Remove only that known prefix, and only
from logger `omaha`; retain its timestamp with the message:

```sh
timeout 30s sed -nE \
  '/^[^[:space:]]+ (DEBUG|INFO|WARNING|ERROR|CRITICAL) omaha myprofit_telemetry /{
     s/^([^[:space:]]+) (DEBUG|INFO|WARNING|ERROR|CRITICAL) omaha (myprofit_telemetry .*)$/\1\t\3/p
   }' \
  "$SEGMENT"
```

Run extraction against the exact declared segment list and redirect its
bounded output to an operator-owned `$COLLECTED_TSV`. Do not retain complete
JSON envelopes, standard prefixes, unrelated application records, or failed
parse input. A no-match result is an absent record condition, not permission
to widen the filter.

### 2.3 Validate and create safe analysis copy

Validate `$COLLECTED_TSV` before grouping. The following standard-library
command emits only `timestamp<TAB>canonical-message` rows to
`$ACCEPTED_TSV`; invalid source values and source text are never printed.
The 200000-line bound prevents an unbounded analysis run.

```sh
python3 - "$COLLECTED_TSV" "$ACCEPTED_TSV" <<'PY'
from datetime import datetime
import re
import sys
from uuid import RFC_4122, UUID

MAX_LINES = 200_000
MAX_DURATION_MS = 86_400_000
EVENTS = {"transition", "stage", "terminal", "ui_limit"}
DOMAINS = {"job", "connector", "browser", "preview_handoff", "polling_ui", "concurrency"}
STATUSES = {"queued", "running", "succeeded", "failed", "expired", "rejected"}
STAGES = {
    "credentials", "browser", "login", "two_factor", "navigation", "export",
    "download", "cleanup", "preview", "connector", "queue", "poll", "ui",
    "handoff", "terminal", "concurrency", "unknown",
}
CODES = {
    "household_read_only", "ambiguous_profile", "unknown_profile", "controls_not_found",
    "timeout", "browser_failed", "failed", "authentication_unconfirmed", "empty_file",
    "file_failed", "launch_failed", "page_failed", "preview_failed", "browser_close_failed",
    "temporary_files_failed", "started", "transitioned", "local_limit_reached",
    "sync_in_progress", "success", "unknown",
}
UUID_SHAPE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
MESSAGE = re.compile(
    r"^myprofit_telemetry version=1 event=(\S+) job_id=(\S+) domain=(\S+) "
    r"status=(\S+) stage=(\S+) code=(\S+) duration_ms=(\S+) "
    r"total_duration_ms=(\S+)$"
)

def valid_uuid(value):
    if not UUID_SHAPE.fullmatch(value):
        return False
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        return False
    return parsed.variant == RFC_4122 and parsed.version in {1, 2, 3, 4, 5}

def valid_duration(value):
    return value == "na" or (
        re.fullmatch(r"[0-9]+", value) is not None
        and int(value) <= MAX_DURATION_MS
    )

accepted = invalid = duplicates = 0
seen = set()
with open(sys.argv[1], encoding="utf-8") as source, open(sys.argv[2], "w", encoding="utf-8") as dest:
    for line_number, raw in enumerate(source, 1):
        if line_number > MAX_LINES:
            print("insufficient-evidence: analysis input exceeded line bound", file=sys.stderr)
            raise SystemExit(2)
        line = raw.rstrip("\n")
        if line in seen:
            duplicates += 1
            continue
        seen.add(line)
        try:
            timestamp, message = line.split("\t", 1)
            parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            match = MESSAGE.fullmatch(message)
            if parsed_timestamp.tzinfo is None or match is None:
                raise ValueError
            event, job_id, domain, status, stage, code, duration, total = match.groups()
            if (
                not valid_uuid(job_id)
                or event not in EVENTS
                or domain not in DOMAINS
                or status not in STATUSES
                or stage not in STAGES
                or code not in CODES
                or not valid_duration(duration)
                or not valid_duration(total)
            ):
                raise ValueError
            normalized = job_id.lower()
            fixed = (
                f"myprofit_telemetry version=1 event={event} job_id={normalized} "
                f"domain={domain} status={status} stage={stage} code={code} "
                f"duration_ms={duration} total_duration_ms={total}"
            )
            dest.write(f"{timestamp}\t{fixed}\n")
            accepted += 1
        except (TypeError, ValueError, UnicodeError):
            invalid += 1

print(
    f"accepted={accepted} invalid_event_count={invalid} exact_duplicate_count={duplicates}",
    file=sys.stderr,
)
PY
```

Reject records with unknown fields/dimensions, malformed UUIDs, missing fixed
fields, non-integer/negative/out-of-bound durations, a non-null JSON
`exc_info`, or a malformed timestamp. Exact repeated source lines may be
deduplicated once and counted as `exact_duplicate_count`; near-duplicates,
conflicting values, and missing events are not merged. Never repair values by
guessing. If invalid records or duplicate/segment loss can affect the
window, the report status is `insufficient-evidence`.

After validation, derive earliest/latest coverage from the bounded safe copy,
not from an unfiltered segment. Empty output is a gap:

```sh
LC_ALL=C sort -k1,1 "$ACCEPTED_TSV" \
  | awk -F '\t' '
      NR == 1 { earliest = $1 }
      NR <= 200000 { latest = $1; count = NR; next }
      { exit 2 }
      END {
        if (count) printf "accepted_records=%d earliest_seen=%s latest_seen=%s\n", count, earliest, latest
        else print "insufficient-evidence: no accepted records"
      }'
```

Compare these bounds with each declared segment and requested window. Do not
interpret a continuous earliest/latest range as proof that intermediate lines
were retained; list independently observed rotation gaps.

### 2.4 One-job trace and bounded filters

Validate or select one exact UUID from `$ACCEPTED_TSV`, then trace only that
job. The filter is bounded by `--max-count`; it does not join on time, status,
profile label, filename, process, or request content:

```sh
JOB_ID='operator-selected-uuid'
rg --fixed-strings --max-count 200 "job_id=$JOB_ID " "$ACCEPTED_TSV" \
  | LC_ALL=C sort -k1,1
```

Read the ordered trace as observations: queued/running transitions, bounded
stage events, optional `ui_limit`, and terminal settlement. A missing
terminal event remains `incomplete_runs`; it is not converted to `failed` or
`expired`. A trace with more than one distinct terminal status for the same
job is a classification conflict and makes the affected report
`insufficient-evidence`.

For bounded dimension inspection, use exact fixed-value filters only:

```sh
rg --fixed-strings --max-count 200 'domain=connector ' "$ACCEPTED_TSV"
rg --fixed-strings --max-count 200 'stage=preview code=' "$ACCEPTED_TSV"
rg --fixed-strings --max-count 200 'domain=polling_ui stage=ui code=local_limit_reached' "$ACCEPTED_TSV"
rg --fixed-strings --max-count 200 'domain=concurrency stage=concurrency code=sync_in_progress' "$ACCEPTED_TSV"
```

Groups are always the bounded tuple `domain/stage/code`, with unique affected
`job_id` counts. Do not group by arbitrary text, profile name, request value,
filename, path, or timestamp proximity.

## 3. Read-only job correlation

### 3.1 Exact SQLite query

Use the exact selected `job_id` and the operator's already known active
`profile_id`. Open the SQLite database in read-only mode. The query returns
only lifecycle/error fields and a foreign-key existence check; it does not
return filenames, work paths, preview payloads, or profile labels.

```sh
sqlite3 -readonly "$SQLITE_DB" <<'SQL'
.headers on
.mode tabs
.parameter init
.parameter set :profile_id 0
.parameter set :job_id_1 'operator-selected-uuid'
.parameter set :job_id_2 NULL
.parameter set :job_id_3 NULL
SELECT
    j.job_id,
    j.profile_id,
    j.status,
    j.error_stage,
    j.error_code,
    j.created_at,
    j.started_at,
    j.finished_at,
    j.expires_at,
    j.retention_until,
    CASE WHEN EXISTS (
        SELECT 1 FROM profiles AS p WHERE p.id = j.profile_id
    ) THEN 1 ELSE 0 END AS profile_fk_present
FROM myprofit_sync_jobs AS j
WHERE j.profile_id = :profile_id
  AND j.job_id IN (:job_id_1, :job_id_2, :job_id_3)
ORDER BY j.created_at, j.job_id;
SQL
```

Replace only the parameter values with already selected identifiers. `0` and
`NULL` above are placeholders, not discovered production values. The only
valid join is exact `telemetry.job_id = myprofit_sync_jobs.job_id`, scoped by
the declared `profile_id` foreign key. Do not join by timestamp, status,
filename, profile label, source segment, or row order.

The stored `error_stage` and `error_code` are normalized fields. Compare them
to accepted bounded `stage`/`code` values; an unexpected stored value is an
invalid correlation record, not a value to repair. Compare terminal status to
`status`, and use lifecycle timestamps as descriptive context only. A missing
row, a row pruned after `retention_until`, or a missing profile FK is
`db-correlation-unavailable`; telemetry analysis may continue with that
limitation.

For PostgreSQL, use the same `SELECT` and bind parameters through an already
approved read-only operational client. Do not invent credentials, connection
details, or a DSN. If no read-only client is supplied, mark correlation
unavailable rather than changing deployment or querying through a write-capable
route.

### 3.2 Classification matrix

| Measure | Exact definition | Not allowed |
|---|---|---|
| `observed_runs` | unique valid `job_id` in at least one accepted event | counting lines as runs |
| `terminal_runs` | unique `job_id` with one accepted `event=terminal` | treating a status row alone as telemetry |
| `succeeded` | terminal event has `status=succeeded` | inferring success from missing errors |
| `failed` | terminal event has `status=failed` | classifying missing terminal evidence as failure |
| `expired` | terminal event has `status=expired` | classifying `ui_limit` or a late line as expiry |
| `incomplete_runs` | observed job without accepted terminal event | filling terminal status from elapsed time |
| `invalid_event_count` | rejected records from validation | silently dropping invalid records |
| `missing_event_count` | independently expected real runs minus observed runs | deriving expected runs from log volume |
| `ui_limit_count` | accepted `polling_ui/ui/local_limit_reached` observations | treating absence as proof limit was not reached |
| `concurrency_count` | accepted `concurrency/concurrency/sync_in_progress` observations | calling concurrency a connector failure |

The server status allowlist is `queued`, `running`, `succeeded`, `failed`,
`expired`; `rejected` exists in telemetry for bounded concurrency observation,
not as a `myprofit_sync_jobs.status` value. `failed` and `expired` are
terminal classifications only. `ui_limit` means the browser reached its
existing local `500 ms × 120` polling observation boundary before seeing
terminal status; it does not alter server status, expiry, or retry behavior.

Failure rate is **`failed / terminal_runs`**. Always print both
`observed_runs` and `terminal_runs` denominators. Publish the failure rate as
complete-window evidence only when every expected run is observed and
terminal, `missing_event_count == 0`, `invalid_event_count == 0`, and there
are no terminal-status conflicts. Otherwise print `insufficient-evidence`,
keep the arithmetic visibly provisional, and do not interpret missing
terminal or UI-limit evidence as a product outcome.

## 4. Repeatable weekly analysis

### 4.1 Worksheet and assignment rules

Run same worksheet for a minimum of **four weeks**. Target **4–8 real runs per
week**; extend to eight weeks if any week has fewer than four, retention is
partial, or validity/terminal coverage is incomplete. Use only real runs, not
fixtures, retries invented from a single trace, or line counts.

Use UTC Monday as week boundary. The report command first builds one record
per valid `job_id`, chooses its earliest accepted event timestamp as the
run-level anchor, and assigns that job to exactly one Monday bucket. Every
event, group, duration, UI-limit count, concurrency count, and terminal
classification for that job uses the anchor bucket; an event crossing Monday
never creates a second weekly run. If an anchor is missing or invalid, the job
is invalid evidence. A job with no terminal event stays in its anchor week and
is counted only as `incomplete_runs`; a job with multiple terminal records is
reported as `terminal_conflicts` and excluded from terminal-rate arithmetic.
Expected runs with no accepted event have no `job_id` anchor and contribute
only to independently measured `missing_event_count`. Keep the source segment
coverage worksheet beside, but not inside, shared telemetry output.

For each week and for the aggregate window, record:

1. expected real runs from an independent operator count, observed runs,
   terminal runs, and `missing_event_count`;
2. succeeded, failed, expired, and incomplete runs separately;
3. failure rate `failed / terminal_runs`, only under the complete-window rule;
4. `invalid_event_count`, exact duplicates, terminal conflicts, and
   `db-correlation-unavailable` count;
5. unique-run counts by `domain/stage/code`;
6. total duration p50/p95/p99 from terminal events with integer
   `total_duration_ms`;
7. stage duration p50/p95/p99 from stage events with integer `duration_ms`;
8. `ui_limit` event and unique-run counts;
9. concurrency event and unique-run counts; and
10. top factors among terminal-failed runs only, with denominator
    `terminal_failed_runs`.

Use one percentile method for every report: inclusive linear interpolation
(`PERCENTILE.INC`, equivalent to Hyndman–Fan type 7), calculated on sorted
integer values. For `n == 0`, report `not-available`; never substitute zero.
The factor denominator is unique jobs with exactly one accepted terminal event
whose status is `failed`. Extract factors only from accepted
`event=stage,status=failed` records belonging to those denominator jobs, and
count each eligible `job_id` once per normalized `stage/code` cluster. A failed
stage followed by terminal `succeeded` is excluded. Terminal `expired`,
incomplete, successful, and UI-limit-only jobs never enter failed factors;
expired and UI-limit observations remain separate descriptive measures.

### 4.2 Minimal bounded report command

The accepted copy is already fixed-shape and bounded. This command extracts
the fields needed for an analyst's worksheet without reading new sources:

```sh
python3 - "$ACCEPTED_TSV" <<'PY'
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import re
import sys

LINE = re.compile(
    r"^myprofit_telemetry version=1 event=(\S+) job_id=(\S+) domain=(\S+) "
    r"status=(\S+) stage=(\S+) code=(\S+) duration_ms=(\S+) total_duration_ms=(\S+)$"
)
MAX_LINES = 200_000
events = []
seen = set()
with open(sys.argv[1], encoding="utf-8") as source:
    for number, raw in enumerate(source, 1):
        if number > MAX_LINES:
            print("insufficient-evidence: report input exceeded line bound")
            raise SystemExit(2)
        timestamp, message = raw.rstrip("\n").split("\t", 1)
        match = LINE.fullmatch(message)
        if match is None:
            print("insufficient-evidence: accepted copy is malformed")
            raise SystemExit(2)
        key = timestamp + "\t" + message
        if key in seen:
            continue
        seen.add(key)
        event, job_id, domain, status, stage, code, duration, total = match.groups()
        when = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc)
        events.append((when, event, job_id, domain, status, stage, code, duration, total))

jobs = {}
for event_record in events:
    when, event, job_id, domain, status, stage, code, duration, total = event_record
    job = jobs.setdefault(job_id, {"anchor": when, "events": []})
    job["anchor"] = min(job["anchor"], when)
    job["events"].append(event_record)

weekly = defaultdict(lambda: {
    "jobs": set(), "terminal": {}, "terminal_conflicts": set(),
    "incomplete": set(), "factors": defaultdict(set),
    "groups": defaultdict(set), "durations": {"total": [], "stage": []},
    "ui": set(), "concurrency": set(),
})
for job_id, job in jobs.items():
    anchor = job["anchor"].astimezone(timezone.utc)
    monday = anchor.date() - timedelta(days=anchor.weekday())
    week = monday.isoformat()
    report = weekly[week]
    report["jobs"].add(job_id)
    job_events = job["events"]
    for _, event, _, domain, status, stage, code, duration, total in job_events:
        report["groups"][f"{domain}/{stage}/{code}"].add(job_id)
        if event == "stage" and duration != "na":
            report["durations"]["stage"].append(int(duration))
        if event == "ui_limit":
            report["ui"].add(job_id)
        if domain == "concurrency" and stage == "concurrency" and code == "sync_in_progress":
            report["concurrency"].add(job_id)
    terminal_records = [record for record in job_events if record[1] == "terminal"]
    if not terminal_records:
        report["incomplete"].add(job_id)
        continue
    if len(terminal_records) != 1:
        report["terminal_conflicts"].add(job_id)
        continue
    terminal_status = terminal_records[0][4]
    report["terminal"][job_id] = terminal_status
    total_duration = terminal_records[0][8]
    if total_duration != "na":
        report["durations"]["total"].append(int(total_duration))
    if terminal_status == "failed":
        for _, event, _, _, stage_status, stage, code, _, _ in job_events:
            if event == "stage" and stage_status == "failed":
                report["factors"][f"{stage}/{code}"].add(job_id)

for week in sorted(weekly):
    report = weekly[week]
    terminal = report["terminal"]
    failed = sum(status == "failed" for status in terminal.values())
    expired = sum(status == "expired" for status in terminal.values())
    succeeded = sum(status == "succeeded" for status in terminal.values())
    print(
        f"week_monday={week} observed_runs={len(report['jobs'])} "
        f"terminal_runs={len(terminal)} terminal_failed_runs={failed} "
        f"succeeded={succeeded} failed={failed} expired={expired} "
        f"incomplete_runs={len(report['incomplete'])} "
        f"terminal_conflicts={len(report['terminal_conflicts'])} "
        f"ui_limit_runs={len(report['ui'])} concurrency_runs={len(report['concurrency'])}"
    )
    for group, run_ids in sorted(report["groups"].items()):
        print(f"group={group} unique_runs={len(run_ids)}")
    for factor, run_ids in sorted(report["factors"].items(), key=lambda item: (-len(item[1]), item[0])):
        print(f"failed_factor={factor} failed_runs={len(run_ids)}")
    print(f"total_duration_values={len(report['durations']['total'])} stage_duration_values={len(report['durations']['stage'])}")
PY
```

The command prints run-level counts and factor candidates only. Add
independently collected expected-run counts, invalid/missing counts,
p50/p95/p99 values, and DB-correlation results to the worksheet. Its
`terminal_failed_runs` value is the denominator for every `failed_factor`; no
stage line creates a failed run by itself. If source coverage, independent
denominator, terminal completeness, or validity cannot be demonstrated, label
the week and aggregate report `insufficient-evidence`.

### 4.3 Diagnosis/escalation threshold

Open a separate future diagnosis proposal only when either condition holds:

- one normalized `stage/code` cluster appears in **at least three runs across
  at least two weeks** and represents **at least 50% of failed runs** (use
  failed terminal runs as denominator); or
- `ui_limit` occurs in **at least two runs**.

This is an escalation threshold for more evidence, not proof of root cause.
It authorizes no timeout, retry, external-service, F68, schema, or runtime
change. Expiry remains terminal `expired`; it is not folded into failed. If
no threshold is met, or evidence is incomplete, report
`insufficient-evidence` and continue collection.

### 4.4 Boundary reading labels

Use these labels in each worksheet so factors remain descriptive and
comparable:

| Label | Accepted evidence | Do not conclude |
|---|---|---|
| Connector | `connector` stage/code and connector terminal failures | browser or external-service cause from one code |
| Browser | `browser` navigation/launch/cleanup stages | timeout or external-service cause without recurrence |
| Polling/UI | `polling_ui/ui/local_limit_reached` | server timeout; local observation is not server classification |
| Preview/handoff | `preview_handoff` stages and handoff outcome | portfolio mutation; preview remains review-only |
| Concurrency | `concurrency/concurrency/sync_in_progress` | connector failure or profile leakage |
| Process | operator deployment evidence aligned to the same window | process identity from `job_id`; telemetry contains no PID/path |

## 5. Sanitization and prohibited actions

Retain/share only:

- source timestamp and fixed telemetry message fields;
- opaque selected `job_id` values and aggregate counts;
- bounded `domain/stage/code`, normalized status, durations, percentiles,
  coverage intervals, and evidence-gap labels; and
- for private correlation, `profile_id`, status, normalized error fields, and
  lifecycle timestamps returned by the read-only query.

Before sharing, redact or reject credentials, tokens, environment values,
profile labels, host/container/process identifiers, source paths, filenames,
CSV contents, URLs, page/request content, JSON envelope fields other than
`ts`/`msg`, non-null `exc_info`, and any exception payload. Do not paste raw
source lines that failed validation. Do not infer missing values from nearby
records.

Every command in this runbook is bounded by an explicit segment, time window,
line limit, or selected UUID. The SQLite operation is `-readonly` and
`SELECT` only. Do not run migrations, reset/seed/clear tasks, backup/export
tasks, import commit routes, deletes, updates, restarts, live connectors, or
cleanup against unrelated host resources for telemetry analysis.

## 6. Scope statement

This document changes operator procedure only. It does not add runtime code,
tests, schemas, migrations, database columns, telemetry storage, collectors,
retention, timeout, retry, F68 behavior, or changes to T38 artifacts. No
application database write is part of collection or analysis. A report that
cannot prove retained authoritative coverage, valid bounded records, complete
denominators, or exact job correlation must say `insufficient-evidence` rather
than inventing a failure factor or remediation.
