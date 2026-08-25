"""Run all canonical test lanes concurrently with failure-safe cleanup."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from scripts.test_governance import (
    current_blocking_candidates,
    load_policy,
    manifest_blocking_candidates,
    select_lowest_importance_cases,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "test-profile"
GRACE_SECONDS = 10.0
MAX_FULL_SUITE_SECONDS = 300.0
TIMEOUT_EXIT_CODE = 124
UNIX_SOCKET_PATH_MAX = 108
CHROMIUM_SINGLETON_SOCKET_SUFFIX = "/org.chromium.Chromium.XXXXXX/SingletonSocket"
SHORT_TEMP_ROOT_DIR = Path("/tmp")
SHORT_TEMP_ROOT_PREFIX = "o-"
LANES = (
    ("unit", "test-unit"),
    ("integration", "test-integration"),
    ("audit", "test-audit-integration"),
    ("e2e", "test-e2e"),
    ("bdd", "test-bdd"),
    ("visual", "test-visual"),
)
DIRECT_LANE_COMMANDS = {
    "test-unit": (
        "uv",
        "run",
        "pytest",
        "-m",
        "unit",
        "--ignore=tests/bdd",
        "--cov=src/omaha",
        "--cov-report=xml:reports/coverage.xml",
        "-vv",
    ),
    "test-integration": (
        "uv",
        "run",
        "pytest",
        "-m",
        "integration",
        "--ignore=tests/audit_integration",
        "--cov=src/omaha",
        "--cov-report=xml:reports/coverage.xml",
        "-vv",
    ),
    "test-audit-integration": ("uv", "run", "pytest", "tests/audit_integration", "-vv"),
    "test-e2e": ("uv", "run", "pytest", "tests/e2e", "-vv", "--no-cov"),
    "test-bdd": ("uv", "run", "pytest", "tests/bdd", "-vv", "--no-cov"),
    "test-visual": (
        "uv",
        "run",
        "pytest",
        "tests/visual",
        "-vv",
        "--no-cov",
        "-m",
        "not t32_pruned",
    ),
}
PORTS = (8765, 8766, 8767, 8768)
LANE_PORTS = {
    "unit": (),
    "integration": (),
    "audit": (),
    "e2e": (8765, 8767),
    "bdd": (8766,),
    "visual": (8768,),
}
LANE_DATABASES = {
    "unit": ("dynamic pytest temp DB",),
    "integration": ("dynamic pytest temp DB",),
    "audit": ("dynamic pytest temp DB",),
    "e2e": (REPO_ROOT / "data" / "test_e2e.db", REPO_ROOT / "data" / "test_e2e_short_ttl.db"),
    "bdd": (REPO_ROOT / "data" / "test_bdd.db",),
    "visual": (REPO_ROOT / "data" / "test_visual.db",),
}
E2E_DATABASE_PATHS = frozenset(
    {
        str(REPO_ROOT / "data" / "test_e2e.db"),
        str(REPO_ROOT / "data" / "test_e2e_short_ttl.db"),
    }
)
PROTECTED_DATABASE_PATH = str(REPO_ROOT / "data" / "portfolio.db")
KNOWN_DATABASES = {
    str(path.resolve())
    for targets in LANE_DATABASES.values()
    for path in targets
    if isinstance(path, Path)
}
CANONICAL_DATABASE_PATHS = frozenset(KNOWN_DATABASES)
BASELINE_AUDIT = REPO_ROOT / "tests" / "AUDIT.md"
MANIFEST_PATH = BASELINE_AUDIT
BASELINE_NODE_RE = re.compile(r"^\| `(tests/[^`]+)` \|")
OUTCOME_RE = re.compile(
    r"^\s*(tests/.*?)\s+(PASSED|SKIPPED|FAILED|ERROR)(?:\s+\[.*)?(?:\s+T29_PROFILE.*)?$"
)
TIMING_RE = re.compile(
    r"^T29_PROFILE\s+(?P<seconds>\d+\.\d+)s\s+"
    r"(?P<when>setup|call|teardown)\s+"
    r"(?:(?P<outcome>PASSED|SKIPPED|FAILED|ERROR)\s+)?"
    r"(?P<node>tests/.*?::.*)$"
)
DB_RE = re.compile(r"^T29_DB_TARGET=(.+)$", re.MULTILINE)
TEMP_ROOT_RE = re.compile(r"^T29_TEMP_ROOT=(.+)$", re.MULTILINE)
TEMP_ROOT_RUN_RE = re.compile(r"^T29_TEMP_ROOT_RUN_ID=(.+)$", re.MULTILINE)
TEMP_ROOT_LANE_RE = re.compile(r"^T29_TEMP_ROOT_LANE=(.+)$", re.MULTILINE)
SERVER_EVENT_RE = re.compile(r"^T29_SERVER_EVENT (?P<event>\{.*\})$", re.MULTILINE)
DB_RECREATE_RE = re.compile(r"^T29_DB_RECREATE=(?P<receipt>\{.*\})$", re.MULTILINE)
TEST_FAILURE_RE = re.compile(r"^T29_TEST_FAILURE (?P<failure>\{.*\})$", re.MULTILINE)
SUMMARY_RE = re.compile(
    r"(?P<passed>\d+) passed|(?P<failed>\d+) failed|"
    r"(?P<skipped>\d+) skipped|(?P<errors>\d+) errors?"
)
COLLECTION_RE = re.compile(
    r"collected (?P<collected>\d+) items(?: / (?P<deselected>\d+) deselected)?"
)
MANIFEST_RE = re.compile(r"^- \*\*Population:\*\* (?P<count>[\d,]+) nodes$")
CHECKSUM_RE = re.compile(r"^- \*\*Node checksum:\*\* `(?P<checksum>[0-9a-f]+)`$")
LANE_CHECKSUM_RE = re.compile(
    r"(?P<lane>unit|integration|audit|e2e|bdd|visual) `(?P<checksum>[0-9a-f]+)`"
)


@dataclass(frozen=True)
class Manifest:
    nodes: frozenset[str]
    checksum: str
    population: int
    lane_checksums: dict[str, str]
    skip_ids: tuple[str, ...]
    enforce_population: bool = True


EXPECTED_SKIPS = (
    "tests/test_dockerfile.py::test_docker_build_pro_image_succeeds",
    "tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user",
)


def _node_checksum(nodes: set[str] | frozenset[str]) -> str:
    return hashlib.sha256("\n".join(sorted(nodes)).encode()).hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> Manifest:
    """Load and validate committed T29 population metadata from AUDIT.md."""
    lines = path.read_text(encoding="utf-8").splitlines()
    nodes = frozenset(
        _normalize_node(match[1]) for line in lines if (match := BASELINE_NODE_RE.match(line))
    )
    population = next(
        (
            int(match["count"].replace(",", ""))
            for line in lines
            if (match := MANIFEST_RE.match(line))
        ),
        None,
    )
    checksum = next(
        (match["checksum"] for line in lines if (match := CHECKSUM_RE.match(line))), None
    )
    lane_line = next((line for line in lines if "**Lane checksums:**" in line), "")
    lane_checksums = {
        match["lane"]: match["checksum"] for match in LANE_CHECKSUM_RE.finditer(lane_line)
    }
    if population is None or checksum is None:
        raise RuntimeError(
            f"T29 manifest population mismatch: snapshot metadata missing; "
            f"population={population}, checksum={checksum}"
        )
    if _node_checksum(nodes) != checksum:
        raise RuntimeError("T29 manifest checksum mismatch")
    if set(lane_checksums) != {name for name, _ in LANES}:
        raise RuntimeError("T29 manifest lane checksums incomplete")
    # Audit population/checksum remain a transparent versioned snapshot. They
    # are not an immutable active-count contract; collection governance
    # classifies every current node independently.
    return Manifest(nodes, checksum, population, lane_checksums, EXPECTED_SKIPS, False)


def _lane_environment(
    name: str,
    *,
    run_id: str | None = None,
    temp_root: Path | None = None,
) -> dict[str, str]:
    """Return process environment carrying one lane's receipt scope."""
    environment = {**os.environ, "T29_DB_RECEIPT_LANE": name}
    if run_id is not None:
        environment["T29_RUN_ID"] = run_id
    if temp_root is not None:
        environment["T29_TEMP_ROOT_BOUNDARY"] = str(temp_root)
        # Keep tempfile-backed safe DBs inside the runner-registered lane
        # boundary. The emitted DB receipt remains the only dynamic path
        # eligible for reconciliation.
        environment["TMPDIR"] = str(temp_root)
        existing_pytest_opts = environment.get("PYTEST_ADDOPTS", "").strip()
        environment["PYTEST_ADDOPTS"] = f"{existing_pytest_opts} --basetemp={temp_root}".strip()
    return environment


def _create_lane_temp_root() -> Path:
    """Create a short, runner-owned pytest boundary for Chromium sockets."""
    temp_root = Path(tempfile.mkdtemp(prefix=SHORT_TEMP_ROOT_PREFIX, dir=SHORT_TEMP_ROOT_DIR))
    socket_path = f"{temp_root}{CHROMIUM_SINGLETON_SOCKET_SUFFIX}"
    if len(os.fsencode(socket_path)) >= UNIX_SOCKET_PATH_MAX:
        raise RuntimeError(
            f"runner temp boundary exceeds Unix Chromium socket path limit: {socket_path!r}"
        )
    return temp_root


def _runtime_child_command(task: str, selected: tuple[str, ...] = ()) -> list[str]:
    """Build runtime lane command with pre-run governance deselection."""
    try:
        command = [*DIRECT_LANE_COMMANDS[task], "-s", "-p", "test_profile_plugin"]
    except KeyError as exc:
        raise ValueError(f"unknown canonical lane task: {task}") from exc
    for nodeid in selected:
        command.extend(("--deselect", nodeid))
    return command


def _normalize_node(node: str) -> str:
    """Normalize pytest's BDD output without changing node identity."""
    node = node.replace("\\x3a", ":").strip()
    node = node.split(" <- ", 1)[0]
    if node.startswith("./"):
        node = node[2:]
    return node


def _baseline_nodes() -> set[str]:
    return set(load_manifest().nodes)


class PreflightError(RuntimeError):
    """Canonical resource collision with bounded inventory evidence."""

    def __init__(self, message: str, receipt: dict[str, object]) -> None:
        super().__init__(message)
        self.receipt = receipt


def _resource_path(resource_id: object) -> str:
    return str(Path(str(resource_id)).resolve())


def _canonical_resource_inventory(
    observations: tuple[dict[str, object], ...] = (),
    *,
    run_id: str | None = None,
    owned_resources: tuple[dict[str, object], ...] = (),
) -> dict[str, object]:
    """Classify only canonical resources; retain unrelated host observations."""
    canonical: list[dict[str, object]] = []
    for port in PORTS:
        canonical.append(
            {
                "resource_kind": "port",
                "resource_id": port,
                "relevant": True,
                "classification": "absent",
                "owner": run_id,
                "evidence": "canonical port declared; no host-wide scan",
                "cleanup_target": False,
                "adopted": False,
            }
        )
    for path in sorted(CANONICAL_DATABASE_PATHS):
        path_obj = Path(path)
        present = path_obj.exists()
        ephemeral = path in E2E_DATABASE_PATHS and present
        canonical.append(
            {
                "resource_kind": "test DB",
                "resource_id": path,
                "relevant": True,
                "classification": (
                    "ephemeral-preexisting"
                    if ephemeral
                    else ("pre-existing" if present else "absent")
                ),
                "owner": run_id,
                "evidence": (
                    "exact disposable E2E DB exists before run; recreate disposition required"
                    if ephemeral
                    else "exact canonical fixed test DB exists before run; no adoption"
                    if present
                    else "canonical fixed test DB declared absent by exact preflight stat"
                ),
                "cleanup_target": False,
                "adopted": False,
                "disposition": "recreate-before-launch" if ephemeral else "preserve-unless-owned",
            }
        )
    canonical.extend(
        {**resource, "adopted": False} for resource in owned_resources if isinstance(resource, dict)
    )

    def is_canonical(observation: dict[str, object]) -> bool:
        kind = str(observation.get("resource_kind", observation.get("kind", "")))
        resource_id = observation.get("resource_id", observation.get("id"))
        if kind == "port":
            try:
                return int(resource_id) in PORTS
            except (TypeError, ValueError):
                return False
        if kind in {"test DB", "database", "path", "temporary path", "log", "timings"}:
            return _resource_path(resource_id) in CANONICAL_DATABASE_PATHS or any(
                _resource_path(item.get("resource_id")) == _resource_path(resource_id)
                for item in owned_resources
                if item.get("resource_id") is not None
            )
        if kind in {"process_group", "pgid"}:
            return any(
                item.get("resource_kind") in {"process_group", "pgid"}
                and item.get("resource_id") == resource_id
                for item in owned_resources
            )
        return False

    resources = [*canonical]
    for raw in observations:
        relevant = is_canonical(raw)
        resource = {
            "resource_kind": raw.get("resource_kind", raw.get("kind", "unknown")),
            "resource_id": raw.get("resource_id", raw.get("id")),
            "relevant": relevant,
            "owner": raw.get("owner"),
            "evidence": raw.get("evidence", "controlled observation"),
            "cleanup_target": False,
            "preserved": True,
            "allowlisted": False,
            "adopted": False,
        }
        if not relevant:
            resource["classification"] = "pre-existing"
        elif raw.get("classification") in {
            "absent",
            "owned-current-run",
            "owned-cleaned",
            "ephemeral-preexisting",
            "pre-existing",
            "foreign",
            "unknown",
        }:
            resource["classification"] = raw["classification"]
        elif (
            isinstance(raw.get("evidence"), dict)
            and isinstance(raw["evidence"].get("listener"), dict)
            and raw["evidence"]["listener"].get("classification") == "foreign"
        ):
            resource["classification"] = "foreign"
        elif raw.get("owner") == run_id and run_id is not None:
            resource["classification"] = "owned-current-run"
        elif raw.get("owner"):
            resource["classification"] = "foreign"
        else:
            resource["classification"] = "unknown"
        resources.append(resource)

    relevant_observations = [item for item in resources if item["relevant"]]
    trusted = all(
        item["classification"]
        in {"absent", "owned-current-run", "owned-cleaned", "ephemeral-preexisting"}
        for item in relevant_observations
    )
    return {
        "ok": trusted,
        "canonical": {
            "ports": list(PORTS),
            "lane_ports": {lane: list(ports) for lane, ports in LANE_PORTS.items()},
            "fixed_test_db_paths": sorted(CANONICAL_DATABASE_PATHS),
            "runner_owned": list(owned_resources),
        },
        "resources": resources,
        "relevant_resources": relevant_observations,
        "untrusted_resources": [
            item
            for item in relevant_observations
            if item["classification"]
            not in {"absent", "owned-current-run", "owned-cleaned", "ephemeral-preexisting"}
        ],
    }


def _canonical_port_identity(port: int) -> dict[str, object]:
    """Collect bounded identity for one declared port, never a host-wide scan."""
    evidence: dict[str, object] = {
        "port": port,
        "source": "exact ss sport filter",
        "classification": "unknown",
    }
    try:
        result = subprocess.run(
            ["ss", "-ltnp", f"sport = :{port}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        evidence["error"] = f"{exc.__class__.__name__}: {exc}"
        return evidence
    output = result.stdout or result.stderr
    evidence["raw"] = output.strip()
    match = re.search(r"pid=(?P<pid>\d+)", output)
    if match is None:
        evidence["error"] = "listener identity unavailable"
        return evidence
    pid = int(match["pid"])
    evidence["pid"] = pid
    try:
        evidence["command"] = (
            Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode()
        )
        evidence["cwd"] = os.readlink(f"/proc/{pid}/cwd")
        evidence["pgid"] = os.getpgid(pid)
    except (OSError, UnicodeError) as exc:
        evidence["error"] = f"partial listener identity: {exc.__class__.__name__}: {exc}"
        return evidence
    evidence["classification"] = "foreign"
    return evidence


def _preflight(observations: tuple[dict[str, object], ...] = ()) -> dict[str, object]:
    """Probe canonical ports and return bounded, ownership-aware inventory."""
    inventory = _canonical_resource_inventory(observations)
    database_url = os.environ.get("DATABASE_URL", "")
    if PROTECTED_DATABASE_PATH in database_url or database_url.endswith("/data/portfolio.db"):
        raise RuntimeError("refusing full test run with production DATABASE_URL")
    for port in PORTS:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                collision = {
                    "resource_kind": "port",
                    "resource_id": port,
                    "owner": None,
                    "evidence": {
                        "bind_error": f"{exc.__class__.__name__}: {exc}",
                        "listener": _canonical_port_identity(port),
                    },
                }
                inventory = _canonical_resource_inventory((*observations, collision))
                raise PreflightError(f"test lane port {port} is unavailable", inventory) from exc
    for lane, targets in LANE_DATABASES.items():
        for target in targets:
            if isinstance(target, Path) and (
                target.parent != REPO_ROOT / "data" or target.name == "portfolio.db"
            ):
                raise RuntimeError(f"unrecognized {lane} database target: {target}")
    if not inventory["ok"]:
        raise PreflightError("canonical test resource is untrusted", inventory)
    return inventory


def _validate_db_targets(name: str, targets: list[str]) -> None:
    """Accept only complete, lane-owned test DB receipts."""
    resolved = [str(Path(target).resolve()) for target in targets]
    if not resolved:
        raise RuntimeError(f"{name} did not report its session test DB")
    if any(target.endswith("/data/portfolio.db") for target in resolved):
        raise RuntimeError(f"{name} reported production database: {targets!r}")
    expected = {str(path.resolve()) for path in LANE_DATABASES[name] if isinstance(path, Path)}
    dynamic = {target for target in resolved if "/omaha-conftest-safe-" in target}
    configured = set(resolved) - dynamic
    if name in {"unit", "integration", "audit"}:
        if not dynamic or configured:
            raise RuntimeError(f"{name} DB target mismatch: configured={targets!r}")
        return
    if dynamic or configured != expected:
        raise RuntimeError(
            f"{name} DB target mismatch: configured={targets!r}, expected={sorted(expected)!r}"
        )


def _is_lifecycle_race(exc: BaseException) -> bool:
    """Recognize only expected disappearance/write races at process boundary."""
    if isinstance(exc, (ProcessLookupError, BrokenPipeError)):
        return True
    if isinstance(exc, OSError) and exc.errno in {errno.ESRCH, errno.EPIPE}:
        return True
    return exc.__class__.__name__ == "NoSuchProcess"


def _race_evidence(exc: BaseException) -> dict[str, str]:
    return {
        "kind": exc.__class__.__name__,
        "message": str(exc),
    }


def _lane_metadata(
    name: str,
    task: str,
    run_id: str,
    log_path: Path,
    timing_path: Path,
    *,
    temp_root: Path | None = None,
) -> dict[str, object]:
    """Register complete lane evidence before any child is launched."""
    owner_evidence = {
        "run_id": run_id,
        "runner_pid": os.getpid(),
        "recorded_at": time.time(),
        "start_new_session": True,
    }
    resources = {
        "process_group": {
            "resource_kind": "process_group",
            "resource_id": None,
            "owner": run_id,
            "classification": "absent",
            "evidence": "PGID is assigned only after successful Popen",
        },
        "log": {
            "resource_kind": "log",
            "resource_id": str(log_path),
            "owner": run_id,
            "classification": "owned-current-run",
            "evidence": "path opened by current runner before child use",
        },
        "timings": {
            "resource_kind": "temporary path",
            "resource_id": str(timing_path),
            "owner": run_id,
            "classification": "owned-current-run",
            "evidence": "path registered by current runner before child use",
        },
        "pytest_temp": {
            "resource_kind": "temporary path",
            "resource_id": str(temp_root) if temp_root is not None else None,
            "owner": run_id,
            "classification": "owned-current-run" if temp_root is not None else "absent",
            "evidence": (
                "unique --basetemp boundary created by current runner"
                if temp_root is not None
                else "pytest temp boundary unavailable before launch"
            ),
        },
        "database": {
            "resource_kind": "test DB",
            "resource_id": [str(target) for target in LANE_DATABASES[name]],
            "owner": run_id,
            "classification": "absent",
            "evidence": "lane receipt required before ownership classification",
        },
        "ports": {
            "resource_kind": "port",
            "resource_id": list(LANE_PORTS[name]),
            "owner": run_id,
            "classification": "absent" if not LANE_PORTS[name] else "unknown",
            "evidence": (
                "lane has no canonical server port"
                if not LANE_PORTS[name]
                else "preflight availability is not ownership proof"
            ),
        },
    }
    return {
        "lane": name,
        "run_id": run_id,
        "task": task,
        "command": _runtime_child_command(task),
        "repo_cwd": str(REPO_ROOT),
        "parent_pid": owner_evidence["runner_pid"],
        "pid": None,
        "pgid": None,
        "log": str(log_path),
        "timings": str(timing_path),
        "temp_root_boundary": str(temp_root) if temp_root is not None else None,
        "temp_root_receipt": None,
        "temp_root_reconciliation": {
            "classification": "not-attempted",
            "cleanup_result": "not-attempted",
        },
        "server_lifecycle": [],
        "timing": {
            "registered_at": owner_evidence["recorded_at"],
            "phases": [],
            "launch_started_at": None,
            "launch_ended_at": None,
            "monitor_started_at": None,
            "monitor_ended_at": None,
            "cleanup_started_at": None,
            "cleanup_ended_at": None,
            "finalization_started_at": None,
            "finalization_ended_at": None,
        },
        "test_failures": [],
        "ports": list(LANE_PORTS[name]),
        "owned_resource_mapping": resources,
        "owner_evidence": owner_evidence,
        "process_identity": {
            "run_id": run_id,
            "lane": name,
            "parent_pid": owner_evidence["runner_pid"],
            "child_pid": None,
            "pgid": None,
            "command": _runtime_child_command(task),
            "cwd": str(REPO_ROOT),
            "ports": list(LANE_PORTS[name]),
            "db_paths": [str(target) for target in LANE_DATABASES[name]],
            "verdict": "registered; awaiting Popen identity",
        },
        "database_disposition": {
            "paths": [str(target) for target in LANE_DATABASES[name]],
            "classification": "absent",
            "disposition": "recreate-before-launch" if name == "e2e" else "preserve-unless-owned",
            "adopted": False,
            "receipt": None,
        },
        "adopted": False,
        "restart": {"phases": [], "signals": [], "diagnosis": None},
        "receipt_errors": [],
        "registered_at": owner_evidence["recorded_at"],
        "started_at": None,
        "ended_at": None,
        "status": "pending",
        "launch_status": "pending",
        "launch_error": None,
        "signal": None,
        "signals": [],
        "return_code": None,
        "exit_code": None,
        "sibling_stop_reason": None,
        "residue_classification": "absent",
        "residue": [],
        "cleanup_status": "not-attempted",
        "cleanup_result": "not-attempted",
        "lifecycle_races": [],
        "lifecycle": [],
        "timeout": {
            "deadline_triggered": False,
            "deadline": None,
            "duration_exceeded": False,
        },
        "receipt_error": None,
    }


def _record_lifecycle(entry: dict[str, object] | None, phase: str, **details: object) -> None:
    """Append one run/lane-bound lifecycle observation to a lane receipt."""
    if entry is None:
        return
    events = entry.setdefault("lifecycle", [])
    assert isinstance(events, list)
    event = {
        **details,
        "run_id": entry.get("run_id"),
        "lane": entry.get("lane"),
        "phase": phase,
        "recorded_at": time.time(),
    }
    events.append(event)
    if entry.get("restart") is not None and phase in {
        "teardown-start",
        "graceful-stop",
        "signal",
        "poll-after-grace",
        "wait",
        "exit",
        "port-free",
        "residue",
    }:
        restart = entry["restart"]
        if isinstance(restart, dict):
            restart.setdefault("phases", []).append(event)


def _record_lane_timing(
    entry: dict[str, object] | None,
    phase: str,
    started_monotonic: float,
    started_at: float,
    *,
    status: str = "complete",
) -> None:
    """Record bounded wall and monotonic timing for one lane phase."""
    if entry is None:
        return
    timing = entry.setdefault("timing", {"phases": []})
    assert isinstance(timing, dict)
    ended_at = time.time()
    timing.setdefault("phases", []).append(
        {
            "phase": phase,
            "started_at": started_at,
            "ended_at": ended_at,
            "elapsed_seconds": max(0.0, time.monotonic() - started_monotonic),
            "status": status,
        }
    )
    timing[f"{phase}_started_at"] = started_at
    timing[f"{phase}_ended_at"] = ended_at


def _record_run_timing(
    payload: dict[str, object],
    phase: str,
    started_monotonic: float,
    started_at: float,
    *,
    status: str = "complete",
) -> None:
    """Record one bounded run phase without changing its deadline policy."""
    timing = payload.setdefault("timing", {"phases": []})
    assert isinstance(timing, dict)
    ended_at = time.time()
    timing.setdefault("phases", []).append(
        {
            "phase": phase,
            "started_at": started_at,
            "ended_at": ended_at,
            "elapsed_seconds": max(0.0, time.monotonic() - started_monotonic),
            "status": status,
        }
    )
    timing["last_phase"] = phase
    timing["last_phase_ended_at"] = ended_at


def _record_receipt_error(
    payload: dict[str, object], stage: str, exc: BaseException, lane: str | None = None
) -> None:
    """Retain receipt failures without replacing earlier run telemetry."""
    error = {
        "stage": stage,
        "kind": exc.__class__.__name__,
        "message": str(exc),
    }
    errors = payload.setdefault("receipt_errors", [])
    assert isinstance(errors, list)
    errors.append(error)
    payload["receipt_error"] = error
    if lane is not None:
        lanes = payload.get("lanes", [])
        if isinstance(lanes, list):
            for entry in lanes:
                if isinstance(entry, dict) and entry.get("lane") == lane:
                    entry["receipt_error"] = f"{stage}: {exc}"
                    entry.setdefault("receipt_errors", []).append(error)
                    break


def _json_safe(value: object) -> object:
    """Convert final receipt values to JSON-safe diagnostics after serialization failure."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    try:
        return str(value)
    except Exception:
        return f"<{type(value).__name__} unavailable>"


def _atomic_write_receipt(path: Path, serialized: str) -> None:
    """Flush and atomically replace receipt so an interrupted write leaves prior receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory = os.open(path.parent, directory_flags)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        with suppress(OSError):
            os.unlink(temporary)
        raise


def _persist_receipt(
    payload: dict[str, object], path: Path, stage: str, lane: str | None = None
) -> bool:
    """Persist current ledger snapshot, retaining telemetry across serialization/write errors."""
    try:
        serialized = json.dumps(payload, indent=2) + "\n"
    except Exception as exc:
        _record_receipt_error(payload, stage + ":serialize", exc, lane)
        try:
            serialized = json.dumps(_json_safe(payload), indent=2) + "\n"
        except Exception as fallback_exc:
            _record_receipt_error(payload, stage + ":fallback-serialize", fallback_exc, lane)
            return False
    try:
        _atomic_write_receipt(path, serialized)
    except Exception as exc:
        _record_receipt_error(payload, stage + ":write", exc, lane)
        return False
    return True


def _write_preflight_blocked_receipt(
    started: float,
    run_started_at: float,
    preflight: dict[str, object],
    reason: str,
) -> None:
    """Persist six explicit lane receipts when canonical preflight blocks launch."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    run_id = f"{stamp}-{os.getpid()}"
    metadata = []
    for name, task in LANES:
        entry = _lane_metadata(
            name,
            task,
            run_id,
            REPORT_DIR / f"{stamp}-{name}.log",
            REPORT_DIR / f"{stamp}-{name}.timings",
        )
        entry.update(
            {
                "status": "preflight-blocked",
                "launch_status": "not-attempted",
                "cleanup_status": "not-attempted",
                "cleanup_result": "not-attempted",
                "receipt_error": reason,
                "ended_at": time.time(),
            }
        )
        metadata.append(entry)
    elapsed = time.monotonic() - started
    payload = {
        "run_id": run_id,
        "started_at": run_started_at,
        "ended_at": time.time(),
        "elapsed_seconds": elapsed,
        "duration_limit_seconds": MAX_FULL_SUITE_SECONDS,
        "duration_exceeded": _duration_exceeded(elapsed),
        "deadline_triggered": False,
        "lanes": metadata,
        "clean_children": True,
        "cleanup": {
            "verdict": "untrusted",
            "owned_only": True,
            "through_elapsed_seconds": elapsed,
            "residue": preflight.get("untrusted_resources", []),
        },
        "preflight": preflight,
        "preflight_reconciliation": {"ok": False, "reason": reason},
        "reconciliation": None,
        "first_failure": 2,
        "final_exit_code": 2,
    }
    _persist_receipt(payload, REPORT_DIR / f"{stamp}-run.json", "preflight-blocked")


def _entry_for(
    metadata: dict[str, dict[str, object]] | None, name: str
) -> dict[str, object] | None:
    return metadata.get(name) if metadata is not None else None


def _record_race(entry: dict[str, object] | None, phase: str, exc: BaseException) -> None:
    if entry is None:
        return
    races = entry.setdefault("lifecycle_races", [])
    assert isinstance(races, list)
    races.append({"phase": phase, **_race_evidence(exc)})
    entry["residue_classification"] = "absent"
    entry["residue"] = [{"phase": phase, **_race_evidence(exc)}]
    _record_lifecycle(entry, phase, race=_race_evidence(exc))


def _resource_is_untrusted(resource: object) -> bool:
    return (
        isinstance(resource, dict)
        and resource.get("relevant", True)
        and resource.get("classification")
        in {"foreign", "unknown", "pre-existing", "untrusted", "contradictory"}
    )


def _entry_has_untrusted_resource(entry: dict[str, object] | None) -> bool:
    if entry is None:
        return False
    resources = entry.get("owned_resource_mapping", {})
    return isinstance(resources, dict) and any(
        _resource_is_untrusted(resource) for resource in resources.values()
    )


def _resource_cleanup_verdict(
    metadata: dict[str, dict[str, object]],
) -> tuple[bool, list[dict[str, object]]]:
    """Return false when canonical foreign/unknown residue reached cleanup."""
    residue: list[dict[str, object]] = []
    for entry in metadata.values():
        resources = entry.get("owned_resource_mapping", {})
        if not isinstance(resources, dict):
            continue
        for resource_name, resource in resources.items():
            if _resource_is_untrusted(resource):
                assert isinstance(resource, dict)
                evidence = {
                    "lane": entry.get("lane"),
                    "resource": resource_name,
                    **resource,
                }
                residue.append(evidence)
                entry["residue_classification"] = str(resource["classification"])
                entry.setdefault("residue", []).append(evidence)
                entry["cleanup_result"] = "untrusted-resource"
    return not residue, residue


def _propagate_resource_inventory(
    metadata: dict[str, dict[str, object]], inventory: dict[str, object]
) -> bool:
    """Attach canonical observations to lane receipts; never adopt them."""
    trusted = True
    observations = inventory.get("untrusted_resources", [])
    if not isinstance(observations, list):
        return False
    for observation in observations:
        if not isinstance(observation, dict):
            trusted = False
            continue
        resource_id = observation.get("resource_id")
        lane_name = observation.get("lane")
        if lane_name not in metadata:
            for candidate, ports in LANE_PORTS.items():
                if resource_id in ports:
                    lane_name = candidate
                    break
        if lane_name not in metadata:
            for candidate, targets in LANE_DATABASES.items():
                if _resource_path(resource_id) in {_resource_path(target) for target in targets}:
                    lane_name = candidate
                    break
        if lane_name not in metadata:
            trusted = False
            continue
        entry = metadata[str(lane_name)]
        kind = str(observation.get("resource_kind", ""))
        mapping_name = {
            "port": "ports",
            "test DB": "database",
            "database": "database",
            "process_group": "process_group",
            "pgid": "process_group",
            "path": "timings",
            "temporary path": "timings",
            "log": "log",
            "timings": "timings",
        }.get(kind)
        if mapping_name is not None:
            resource = entry["owned_resource_mapping"][mapping_name]
            resource.update(
                {
                    "resource_id": observation["resource_id"],
                    "classification": observation["classification"],
                    "owner": observation.get("owner"),
                    "evidence": observation.get("evidence", "preflight observation"),
                    "relevant": observation["relevant"],
                }
            )
        entry["residue_classification"] = observation["classification"]
        entry.setdefault("residue", []).append(observation)
        entry["cleanup_result"] = "untrusted-resource"
        trusted = False
    return trusted


def _owned_process_group(entry: dict[str, object] | None, process: object) -> bool:
    """Require current-run process-group evidence before signaling or reaping."""
    if entry is None:
        return False
    resources = entry.get("owned_resource_mapping", {})
    resource = resources.get("process_group", {}) if isinstance(resources, dict) else {}
    if not isinstance(resource, dict):
        return False
    if resource.get("classification") != "owned-current-run":
        return False
    recorded_pgid = entry.get("pgid")
    resource_id = resource.get("resource_id")
    if not isinstance(recorded_pgid, int) or not isinstance(resource_id, int):
        return False
    if recorded_pgid != resource_id:
        return False
    recorded_pid = entry.get("pid")
    process_pid = getattr(process, "pid", None)
    if (
        isinstance(recorded_pid, int)
        and isinstance(process_pid, int)
        and recorded_pid != process_pid
    ):
        return False
    identity = entry.get("process_identity")
    if isinstance(identity, dict):
        expected_command = identity.get("command")
        expected_cwd = identity.get("cwd")
        if expected_command is not None and entry.get("command") != expected_command:
            return False
        if expected_cwd is not None and expected_cwd != str(REPO_ROOT):
            return False
    return True


def _mark_untrusted_process(entry: dict[str, object] | None, process: object) -> None:
    if entry is None:
        return
    resources = entry.get("owned_resource_mapping", {})
    resource = resources.get("process_group", {}) if isinstance(resources, dict) else {}
    if isinstance(resource, dict):
        resource.update(
            {
                "classification": "untrusted",
                "evidence": {
                    "recorded_pid": entry.get("pid"),
                    "observed_pid": getattr(process, "pid", None),
                    "recorded_pgid": entry.get("pgid"),
                    "resource_pgid": resource.get("resource_id"),
                    "command": entry.get("command"),
                    "cwd": entry.get("repo_cwd"),
                },
            }
        )
    entry["residue_classification"] = "untrusted"
    entry.setdefault("residue", []).append(
        {
            "resource": "process_group",
            "classification": "untrusted",
            "evidence": "recorded process identity did not match signal target",
        }
    )
    entry["cleanup_result"] = "untrusted-resource"
    restart = entry.get("restart")
    if isinstance(restart, dict):
        restart["diagnosis"] = "process identity mismatch"


def _recorded_pgid(entry: dict[str, object] | None) -> int | None:
    if entry is None:
        return None
    pgid = entry.get("pgid")
    return pgid if isinstance(pgid, int) else None


def _stop(
    processes: dict[str, subprocess.Popen[str]],
    sig: int,
    metadata: dict[str, dict[str, object]] | None = None,
    reason: str = "cleanup",
) -> bool:
    """Signal only launched current-run groups; report bounded lifecycle races."""
    clean = True
    for name, process in processes.items():
        entry = _entry_for(metadata, name)
        if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
            if entry is not None:
                _mark_untrusted_process(entry, process)
                entry.setdefault("residue", []).append(
                    {
                        "phase": "signal",
                        "resource": "process_group",
                        "classification": "foreign",
                        "resource_id": getattr(process, "pid", None),
                        "evidence": "process group is not current-run-owned",
                    }
                )
                _record_lifecycle(
                    entry,
                    "residue",
                    child_pid=getattr(process, "pid", None),
                    pgid=_recorded_pgid(entry),
                    classification=entry.get("residue_classification", "untrusted"),
                )
            clean = False
            continue
        try:
            running = process.poll() is None
            _record_lifecycle(
                entry,
                "poll-before-signal",
                child_pid=getattr(process, "pid", None),
                pgid=_recorded_pgid(entry),
                return_code=getattr(process, "returncode", None),
            )
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "poll-before-signal", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
                clean = False
                continue
            if entry is not None:
                entry["cleanup_result"] = f"error: {exc}"
            clean = False
            continue
        if not running:
            _record_lifecycle(
                entry,
                "exit-before-signal",
                child_pid=getattr(process, "pid", None),
                pgid=_recorded_pgid(entry),
                return_code=getattr(process, "returncode", None),
            )
            continue
        if entry is not None:
            entry["signal"] = signal.Signals(sig).name
            signals = entry.setdefault("signals", [])
            assert isinstance(signals, list)
            signals.append({"signal": signal.Signals(sig).name, "reason": reason})
            entry["sibling_stop_reason"] = reason
            _record_lifecycle(
                entry,
                "graceful-stop" if sig == signal.SIGTERM else "signal-requested",
                child_pid=getattr(process, "pid", None),
                pgid=_recorded_pgid(entry),
                signal=signal.Signals(sig).name,
                reason=reason,
            )
        try:
            pgid = _recorded_pgid(entry)
            if pgid is None:
                raise RuntimeError("current-run PGID was not recorded")
            os.killpg(pgid, sig)
            _record_lifecycle(
                entry,
                "signal",
                child_pid=getattr(process, "pid", None),
                pgid=pgid,
                signal=signal.Signals(sig).name,
                reason=reason,
            )
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "signal", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
    return clean


def _reap(
    processes: dict[str, subprocess.Popen[str]],
    metadata: dict[str, dict[str, object]] | None = None,
    reason: str = "cleanup",
) -> bool:
    """Reap launched children and escalate only recorded process groups."""
    clean = True
    deadline = time.monotonic() + GRACE_SECONDS
    while time.monotonic() < deadline:
        running = False
        for name, process in processes.items():
            entry = _entry_for(metadata, name)
            if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
                continue
            try:
                return_code = process.poll()
                _record_lifecycle(
                    entry,
                    "poll-before-reap",
                    child_pid=getattr(process, "pid", None),
                    pgid=_recorded_pgid(entry),
                    return_code=return_code,
                )
                if return_code is None:
                    running = True
            except Exception as exc:
                entry = _entry_for(metadata, name)
                if _is_lifecycle_race(exc):
                    _record_race(entry, "poll-before-reap", exc)
                    if entry is not None:
                        entry["cleanup_result"] = "vanished-child"
                    clean = False
                else:
                    if entry is not None:
                        entry["cleanup_result"] = f"error: {exc}"
                    clean = False
        if not running:
            break
        time.sleep(0.1)
    survivors: list[tuple[str, subprocess.Popen[str]]] = []
    for name, process in processes.items():
        entry = _entry_for(metadata, name)
        if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
            if entry is not None:
                entry["cleanup_result"] = "untrusted-resource"
                _mark_untrusted_process(entry, process)
            clean = False
            continue
        try:
            return_code = process.poll()
            _record_lifecycle(
                entry,
                "poll-after-grace",
                child_pid=getattr(process, "pid", None),
                pgid=_recorded_pgid(entry),
                return_code=return_code,
            )
            if return_code is None:
                survivors.append((name, process))
        except Exception as exc:
            entry = _entry_for(metadata, name)
            if _is_lifecycle_race(exc):
                _record_race(entry, "poll-after-grace", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
    for name, process in survivors:
        entry = _entry_for(metadata, name)
        if entry is not None:
            entry["cleanup_status"] = "escalated"
            entry["signal"] = signal.Signals(signal.SIGKILL).name
            entry["signals"] = [
                *entry.get("signals", []),
                {"signal": signal.Signals(signal.SIGKILL).name, "reason": reason},
            ]
            _record_lifecycle(
                entry,
                "escalation",
                child_pid=getattr(process, "pid", None),
                pgid=_recorded_pgid(entry),
                signal=signal.Signals(signal.SIGKILL).name,
                reason=reason,
            )
        try:
            pgid = _recorded_pgid(entry)
            if pgid is None:
                raise RuntimeError("current-run PGID was not recorded")
            os.killpg(pgid, signal.SIGKILL)
            _record_lifecycle(
                entry,
                "signal",
                child_pid=getattr(process, "pid", None),
                pgid=pgid,
                signal=signal.Signals(signal.SIGKILL).name,
                reason=reason,
            )
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "kill", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
    for name, process in processes.items():
        entry = _entry_for(metadata, name)
        if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
            continue
        try:
            waited = process.wait(timeout=GRACE_SECONDS)
            _record_lifecycle(
                entry,
                "wait",
                child_pid=getattr(process, "pid", None),
                pgid=_recorded_pgid(entry),
                return_code=waited,
            )
            if entry is not None and process.returncode is None:
                entry["return_code"] = waited
                entry["exit_code"] = waited
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "wait", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
        if entry is not None:
            entry["return_code"] = process.returncode
            entry["exit_code"] = process.returncode
            _record_lifecycle(
                entry,
                "exit",
                child_pid=getattr(process, "pid", None),
                pgid=_recorded_pgid(entry),
                return_code=process.returncode,
            )
            if entry["cleanup_result"] == "not-attempted":
                entry["cleanup_result"] = "owned-cleaned"
            if entry["cleanup_status"] == "not-attempted":
                entry["cleanup_status"] = "complete"
            if entry["cleanup_result"] == "owned-cleaned":
                entry["residue_classification"] = "owned-cleaned"
                entry["owned_resource_mapping"]["process_group"]["classification"] = "owned-cleaned"
    return clean and not survivors


def _summary(output: str) -> dict[str, int]:
    result = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    for match in SUMMARY_RE.finditer(output):
        for key, value in match.groupdict().items():
            if value is not None:
                result[key] += int(value)
    return result


def _timing_records(output: str) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for line in output.splitlines():
        match = TIMING_RE.match(line)
        if match:
            node = _normalize_node(match["node"])
            records[node] = {
                "duration": float(match["seconds"]),
                "when": match["when"],
                "outcome": (match["outcome"] or "PASSED").upper(),
            }
    return records


def _collection(output: str, timing_output: str = "") -> dict[str, object]:
    """Reconcile timing receipts; retain terminal output only as diagnostics."""
    records = _timing_records(timing_output)
    nodes = set(records)
    skipped = {node for node, record in records.items() if record["outcome"] == "SKIPPED"}
    outcomes = {node: str(record["outcome"]) for node, record in records.items()}
    terminal_outcomes: dict[str, str] = {}
    for line in output.splitlines():
        match = OUTCOME_RE.match(line)
        if match:
            node = _normalize_node(match[1])
            terminal_outcomes[node] = match[2]
    matches = list(COLLECTION_RE.finditer(output))
    result: dict[str, object] = {
        "collected": len(nodes),
        "nodes": sorted(nodes),
        "skipped": sorted(skipped),
        "node_checksum": hashlib.sha256("\n".join(sorted(nodes)).encode()).hexdigest(),
        "outcomes": outcomes,
        "terminal_outcomes": terminal_outcomes,
    }
    if matches and matches[-1]["deselected"] is not None:
        result["deselected"] = int(matches[-1]["deselected"])
    return result


def _server_events(output: str) -> list[dict[str, object]]:
    """Parse only run/lane-bound server events emitted by shared harness."""
    events: list[dict[str, object]] = []
    for match in SERVER_EVENT_RE.finditer(output):
        try:
            event = json.loads(match["event"])
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _db_recreate_receipts(output: str) -> list[dict[str, object]]:
    """Parse exact E2E recreate receipts; malformed receipts remain absent."""
    receipts: list[dict[str, object]] = []
    for match in DB_RECREATE_RE.finditer(output):
        try:
            receipt = json.loads(match["receipt"])
        except json.JSONDecodeError:
            continue
        if isinstance(receipt, dict):
            receipts.append(receipt)
    return receipts


def _test_failures(output: str) -> list[dict[str, object]]:
    """Parse run/lane-bound per-test traceback evidence from shared conftest."""
    failures: list[dict[str, object]] = []
    for match in TEST_FAILURE_RE.finditer(output):
        try:
            failure = json.loads(match["failure"])
        except json.JSONDecodeError:
            continue
        if isinstance(failure, dict):
            failures.append(failure)
    return failures


def _final_exit_code(
    interrupted: int | None,
    clean: bool,
    first_failure: int | None,
    processes: dict[str, subprocess.Popen[str]],
) -> int:
    """Choose parent result after every child has been reaped."""
    if interrupted is not None:
        return 128 + interrupted
    if not clean or any(process.returncode != 0 for process in processes.values()):
        if first_failure is not None:
            return first_failure
        return next(
            (
                process.returncode if process.returncode != 0 else 1
                for process in processes.values()
                if process.returncode != 0
            ),
            1,
        )
    return 0


def _duration_exceeded(elapsed_seconds: float) -> bool:
    """Return whether a full-suite run breached its hard wall-clock ceiling."""
    return elapsed_seconds > MAX_FULL_SUITE_SECONDS


def _stop_deadline(started: float) -> float:
    """Reserve cleanup margin so hard ceiling includes child teardown."""
    return started + MAX_FULL_SUITE_SECONDS - (2 * GRACE_SECONDS) - 1.0


def reconcile_population(
    manifest: Manifest,
    lane_nodes: dict[str, set[str]],
    skip_nodes: set[str],
    *,
    check_skips: bool = True,
) -> dict[str, object]:
    all_nodes = set().union(*lane_nodes.values()) if lane_nodes else set()
    duplicate_nodes = sorted(
        node for node in all_nodes if sum(node in values for values in lane_nodes.values()) > 1
    )
    expected_lanes = {name for name, _ in LANES}
    actual_lanes = set(lane_nodes)
    missing_lanes = sorted(expected_lanes - actual_lanes)
    unexpected_lanes = sorted(actual_lanes - expected_lanes)
    lane_checksums = {lane: _node_checksum(nodes) for lane, nodes in lane_nodes.items()}
    lane_mismatches = {}
    if manifest.enforce_population:
        for lane, _nodes in lane_nodes.items():
            actual_checksum = lane_checksums[lane]
            if actual_checksum != manifest.lane_checksums.get(lane):
                lane_mismatches[lane] = {
                    "expected": manifest.lane_checksums.get(lane),
                    "actual": actual_checksum,
                }
    result = {
        "expected_nodes": manifest.population if manifest.enforce_population else None,
        "manifest_snapshot_nodes": manifest.population,
        "actual_nodes": len(all_nodes),
        "lane_checksums": lane_checksums,
        "duplicate_nodes": duplicate_nodes,
        "missing_lanes": missing_lanes,
        "unexpected_lanes": unexpected_lanes,
        "missing_nodes": sorted(manifest.nodes - all_nodes) if manifest.enforce_population else [],
        "unexpected_nodes": (
            sorted(all_nodes - manifest.nodes) if manifest.enforce_population else []
        ),
        "lane_mismatches": lane_mismatches,
        "expected_skips": list(manifest.skip_ids),
        "actual_skips": sorted(skip_nodes),
        "skip_mismatch": check_skips and sorted(skip_nodes) != list(manifest.skip_ids),
    }
    result["ok"] = (
        actual_lanes == expected_lanes
        and (len(all_nodes) == manifest.population if manifest.enforce_population else True)
        and not result["duplicate_nodes"]
        and not result["missing_nodes"]
        and not result["unexpected_nodes"]
        and not result["lane_mismatches"]
        and not result["skip_mismatch"]
    )
    return result


def reconcile_preflight(manifest: Manifest, lane_nodes: dict[str, set[str]]) -> dict[str, object]:
    """Reconcile collection-only lane receipts before starting test children."""
    return reconcile_population(manifest, lane_nodes, set(), check_skips=False)


def _select_pre_run_cases(
    policy,
    manifest_or_preflight: set[str]
    | frozenset[str]
    | dict[str, tuple[set[str], set[str], list[str]]],
) -> tuple[tuple[object, ...], dict[str, tuple[str, ...]]]:
    """Select versioned blocking candidates before any runtime child launch."""
    if isinstance(manifest_or_preflight, dict):
        lane_nodes = {name: nodes for name, (nodes, _, _) in manifest_or_preflight.items()}
        candidates = current_blocking_candidates(lane_nodes)
    else:
        candidates = manifest_blocking_candidates(manifest_or_preflight)
    selected = select_lowest_importance_cases(
        policy.prior_known_seconds,
        candidates,
        ceiling_seconds=policy.ceiling_seconds,
        safety_margin_seconds=policy.safety_margin_seconds,
    )
    if isinstance(manifest_or_preflight, dict):
        selected_by_lane = {
            lane: tuple(case.nodeid for case in selected if case.nodeid in nodes)
            for lane, nodes in lane_nodes.items()
        }
    else:
        selected_by_lane = {}
        for case in selected:
            if case.lane is None:
                raise RuntimeError(f"selected case has no lane: {case.nodeid}")
            selected_by_lane.setdefault(case.lane, tuple())
            selected_by_lane[case.lane] += (case.nodeid,)
    return selected, selected_by_lane


def _reconcile_temp_root(entry: dict[str, object], output: str) -> bool:
    """Reconcile only the exact pytest base temp path declared by one lane."""
    expected_value = entry.get("temp_root_boundary")
    if not isinstance(expected_value, str) or not expected_value:
        entry["temp_root_reconciliation"] = {
            "classification": "unknown",
            "cleanup_result": "missing-boundary",
        }
        entry["owned_resource_mapping"]["pytest_temp"]["classification"] = "unknown"
        entry["cleanup_result"] = "untrusted-receipt"
        return False

    paths = TEMP_ROOT_RE.findall(output)
    run_ids = TEMP_ROOT_RUN_RE.findall(output)
    lanes = TEMP_ROOT_LANE_RE.findall(output)
    expected = Path(expected_value).resolve()
    evidence = {
        "expected": str(expected),
        "reported_paths": paths,
        "reported_run_ids": run_ids,
        "reported_lanes": lanes,
    }
    if len(paths) != 1 or run_ids != [str(entry["run_id"])] or lanes != [str(entry["lane"])]:
        entry["temp_root_reconciliation"] = {
            "classification": "unknown",
            "cleanup_result": "incomplete-or-contradictory-evidence",
            **evidence,
        }
        entry["owned_resource_mapping"]["pytest_temp"].update(
            {"classification": "unknown", "evidence": evidence}
        )
        entry["cleanup_result"] = "untrusted-receipt"
        return False

    reported = Path(paths[0]).resolve()
    if reported != expected:
        entry["temp_root_reconciliation"] = {
            "classification": "foreign",
            "cleanup_result": "path-mismatch",
            "reported": str(reported),
            **evidence,
        }
        entry["owned_resource_mapping"]["pytest_temp"].update(
            {"classification": "foreign", "evidence": evidence, "resource_id": str(reported)}
        )
        entry["residue_classification"] = "foreign"
        entry["residue"].append({"resource": "pytest_temp", **evidence})
        entry["cleanup_result"] = "untrusted-resource"
        return False

    resource = entry["owned_resource_mapping"]["pytest_temp"]
    if expected.is_symlink() or (expected.exists() and not expected.is_dir()):
        entry["temp_root_reconciliation"] = {
            "classification": "unknown",
            "cleanup_result": "contradictory-path-state",
            **evidence,
        }
        resource.update({"classification": "unknown", "evidence": evidence})
        entry["cleanup_result"] = "untrusted-receipt"
        return False
    try:
        if expected.exists():
            shutil.rmtree(expected)
            classification = "owned-cleaned"
            cleanup_result = "exact-root-removed"
        else:
            classification = "absent"
            cleanup_result = "idempotent-no-op; exact-root-absent"
    except OSError as exc:
        entry["temp_root_reconciliation"] = {
            "classification": "unknown",
            "cleanup_result": f"cleanup-failed: {exc.__class__.__name__}: {exc}",
            **evidence,
        }
        resource.update({"classification": "unknown", "evidence": evidence})
        entry["cleanup_result"] = "untrusted-receipt"
        return False
    entry["temp_root_receipt"] = {
        "run_id": entry["run_id"],
        "lane": entry["lane"],
        "path": str(reported),
        "owner": entry["run_id"],
        "owner_evidence": evidence,
    }
    entry["temp_root_reconciliation"] = {
        "classification": classification,
        "cleanup_result": cleanup_result,
        **evidence,
    }
    resource.update({"classification": classification, "evidence": evidence})
    return True


def _reconcile_fixed_db_targets(entry: dict[str, object], db_targets: list[str]) -> bool:
    """Reconcile exact fixed DBs, with an explicit disposable E2E exception."""
    resource = entry["owned_resource_mapping"]["database"]
    assert isinstance(resource, dict)
    expected = {
        str(path.resolve()) for path in LANE_DATABASES[str(entry["lane"])] if isinstance(path, Path)
    }
    fixed_targets = [target for target in db_targets if target in expected]
    if not fixed_targets:
        return True
    preflight_classification = resource.get("preflight_classification")
    is_e2e = str(entry["lane"]) == "e2e"
    allowed_preflight = {"absent", "ephemeral-preexisting"} if is_e2e else {"absent"}
    if preflight_classification not in allowed_preflight:
        resource.update(
            {
                "classification": preflight_classification or "unknown",
                "cleanup_result": "preserved; preflight ownership not absent",
            }
        )
        return False

    if is_e2e and any(target not in E2E_DATABASE_PATHS for target in fixed_targets):
        resource.update(
            {
                "classification": "contradictory",
                "cleanup_result": "preserved; E2E target outside disposable allowlist",
            }
        )
        return False

    for target in fixed_targets:
        path = Path(target)
        try:
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise OSError("fixed test DB path has contradictory type")
            if path.exists():
                path.unlink()
                cleanup_result = "exact-test-db-removed"
                classification = "owned-cleaned"
            else:
                cleanup_result = "idempotent-no-op; exact-test-db-absent"
                classification = "absent"
        except OSError as exc:
            resource.update(
                {
                    "classification": "unknown",
                    "cleanup_result": f"cleanup-failed: {exc.__class__.__name__}: {exc}",
                }
            )
            return False
        resource.update(
            {
                "classification": classification,
                "cleanup_result": cleanup_result,
                "resource_id": fixed_targets,
                "evidence": (
                    "exact disposable E2E path recreated without adoption"
                    if is_e2e
                    else "exact fixed DB path was absent at current-run preflight"
                ),
                "adopted": False,
            }
        )
    return True


def _reconcile_dynamic_db_targets(entry: dict[str, object], db_targets: list[str]) -> bool:
    """Reconcile only emitted dynamic DB files inside one lane boundary."""
    resource = entry["owned_resource_mapping"]["database"]
    assert isinstance(resource, dict)
    boundary_value = entry.get("temp_root_boundary")
    if not isinstance(boundary_value, str) or not boundary_value:
        resource.update({"classification": "unknown", "cleanup_result": "missing-boundary"})
        return False
    boundary = Path(boundary_value).resolve()
    dynamic_targets = [
        Path(target).resolve() for target in db_targets if "/omaha-conftest-safe-" in target
    ]
    if not dynamic_targets or any(
        target == boundary or boundary not in target.parents for target in dynamic_targets
    ):
        resource.update(
            {
                "classification": "unknown",
                "cleanup_result": "dynamic-path-outside-registered-boundary",
                "resource_id": [str(target) for target in dynamic_targets],
            }
        )
        return False

    classifications: list[str] = []
    for target in dynamic_targets:
        try:
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise OSError("dynamic test DB path has contradictory type")
            if target.exists():
                target.unlink()
                classifications.append("owned-cleaned")
            else:
                classifications.append("absent")
        except OSError as exc:
            resource.update(
                {
                    "classification": "unknown",
                    "cleanup_result": f"cleanup-failed: {exc.__class__.__name__}: {exc}",
                    "resource_id": [str(target) for target in dynamic_targets],
                }
            )
            return False
    classification = "owned-cleaned" if "owned-cleaned" in classifications else "absent"
    resource.update(
        {
            "resource_id": [str(target) for target in dynamic_targets],
            "classification": classification,
            "cleanup_result": "exact-dynamic-db-reconciled",
            "evidence": (
                "exact T29_DB_TARGET paths were emitted before collection and remained "
                "inside the registered lane temp boundary"
            ),
        }
    )
    return True


def _fixed_db_preflight_classification(preflight: dict[str, object], lane: str) -> str | None:
    """Return exact preflight state for one lane's fixed DB resources."""
    fixed_paths = {str(path.resolve()) for path in LANE_DATABASES[lane] if isinstance(path, Path)}
    if not fixed_paths:
        return None
    resources = preflight.get("resources", [])
    states = {
        str(item.get("resource_id")): str(item.get("classification"))
        for item in resources
        if isinstance(item, dict)
        and item.get("resource_kind") == "test DB"
        and str(item.get("resource_id")) in fixed_paths
    }
    if len(states) != len(fixed_paths):
        return "unknown"
    classifications = set(states.values())
    if len(classifications) == 1:
        return next(iter(classifications))
    # A split E2E state is contradictory: it cannot be safely recreated as one
    # lane disposition and must block before launch.
    return "unknown"


def main() -> int:
    started = time.monotonic()
    run_started_at = time.time()
    try:
        policy = load_policy()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"full-suite governance preflight failed: {exc}", file=sys.stderr)
        return 2
    try:
        preflight_receipt = _preflight() or _canonical_resource_inventory()
    except PreflightError as exc:
        try:
            _write_preflight_blocked_receipt(started, run_started_at, exc.receipt, str(exc))
        except OSError as receipt_exc:
            print(f"full-suite preflight receipt write failed: {receipt_exc}", file=sys.stderr)
        print(f"full-suite preflight failed: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"full-suite preflight failed: {exc}", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest()
        selected_before_run, selected_by_lane = _select_pre_run_cases(policy, manifest.nodes)
        if time.monotonic() - started >= MAX_FULL_SUITE_SECONDS:
            print(
                "full suite duration ceiling reached during preflight",
                file=sys.stderr,
            )
            return TIMEOUT_EXIT_CODE
    except RuntimeError as exc:
        print(f"full-suite lane preflight failed: {exc}", file=sys.stderr)
        return 2
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    run_id = f"{stamp}-{os.getpid()}"
    processes: dict[str, subprocess.Popen[str]] = {}
    metadata: list[dict[str, object]] = []
    metadata_by_lane: dict[str, dict[str, object]] = {}
    for name, task in LANES:
        log_path = REPORT_DIR / f"{stamp}-{name}.log"
        timing_path = REPORT_DIR / f"{stamp}-{name}.timings"
        temp_root = _create_lane_temp_root()
        entry = _lane_metadata(
            name,
            task,
            run_id,
            log_path,
            timing_path,
            temp_root=temp_root,
        )
        database_resource = entry["owned_resource_mapping"]["database"]
        assert isinstance(database_resource, dict)
        preflight_db_state = _fixed_db_preflight_classification(preflight_receipt, name)
        if preflight_db_state is not None:
            database_resource["preflight_classification"] = preflight_db_state
        _record_lifecycle(entry, "registered", parent_pid=os.getpid(), temp_root=str(temp_root))
        entry["owned_resources"] = entry["owned_resource_mapping"]
        metadata.append(entry)
        metadata_by_lane[name] = entry
    receipt_path = REPORT_DIR / f"{stamp}-run.json"
    payload: dict[str, object] = {
        "run_id": run_id,
        "started_at": run_started_at,
        "ended_at": None,
        "elapsed_seconds": None,
        "duration_limit_seconds": MAX_FULL_SUITE_SECONDS,
        "duration_exceeded": False,
        "deadline_triggered": False,
        "lanes": metadata,
        "clean_children": None,
        "cleanup": {
            "verdict": "not-attempted",
            "owned_only": True,
            "through_elapsed_seconds": None,
            "residue": [],
        },
        "preflight": {
            **preflight_receipt,
            "source": "canonical resource inventory plus versioned audit manifest",
            "manifest_snapshot_nodes": manifest.population,
            "manifest_checksum": manifest.checksum,
        },
        "preflight_reconciliation": {
            "ok": True,
            "source": "versioned audit manifest",
            "selected_before_child_launch": True,
        },
        "governance": {
            "policy_version": policy.version,
            "ceiling_seconds": policy.ceiling_seconds,
            "prior_known_seconds": policy.prior_known_seconds,
            "safety_margin_seconds": policy.safety_margin_seconds,
            "approved_outside_blocking_lane": [case.nodeid for case in policy.approved_disabled],
            "additional_pre_run_selection": [
                {
                    "nodeid": case.nodeid,
                    "importance": case.importance,
                    "estimated_seconds": case.estimated_seconds,
                }
                for case in selected_before_run
            ],
            "additional_pre_run_economy_seconds": sum(
                case.estimated_seconds for case in selected_before_run
            ),
            "blocking_command": policy.blocking_command,
            "expanded_command": policy.expanded_command,
        },
        "reconciliation": None,
        "first_failure": None,
        "first_failure_lane": None,
        "first_failure_reason": None,
        "final_exit_code": None,
        "receipt_errors": [],
        "receipt_error": None,
        "timing": {
            "run_started_at": run_started_at,
            "hard_ceiling_seconds": MAX_FULL_SUITE_SECONDS,
            "phases": [],
            "receipt_persistence": [],
        },
    }
    _record_run_timing(payload, "preflight", started, run_started_at)
    receipt_write_failed = False

    def persist(stage: str, lane: str | None = None) -> None:
        nonlocal receipt_write_failed
        timing = payload.get("timing")
        attempt_started = time.monotonic()
        attempt_started_at = time.time()
        if isinstance(timing, dict):
            persistence = timing.setdefault("receipt_persistence", [])
            assert isinstance(persistence, list)
            persistence.append(
                {
                    "stage": stage,
                    "lane": lane,
                    "started_at": attempt_started_at,
                    "status": "started",
                }
            )
        persisted = _persist_receipt(payload, receipt_path, stage, lane)
        if isinstance(timing, dict):
            persistence = timing.setdefault("receipt_persistence", [])
            assert isinstance(persistence, list)
            persistence[-1].update(
                {
                    "ended_at": time.time(),
                    "elapsed_seconds": max(0.0, time.monotonic() - attempt_started),
                    "status": "written" if persisted else "failed",
                }
            )
        if not persisted:
            receipt_write_failed = True

    persist("pre-launch")

    def record_error(stage: str, exc: BaseException, lane: str | None = None) -> None:
        _record_receipt_error(payload, stage, exc, lane)
        persist(stage + ":retained", lane)

    interrupted: int | None = None
    first_failure: int | None = None
    first_failure_lane: str | None = None
    first_failure_reason: str | None = None
    stopping = False
    duration_exceeded = False
    deadline_triggered = False

    def handle_signal(signum: int, _frame: object) -> None:
        nonlocal interrupted, stopping
        if stopping:
            return
        interrupted, stopping = signum, True
        try:
            _stop(processes, signum, metadata_by_lane, "parent-interrupt")
        except Exception as exc:
            record_error("parent-interrupt", exc)
        persist("parent-interrupt")

    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    def launch(name: str, task: str) -> bool:
        entry = metadata_by_lane[name]
        launch_started = time.monotonic()
        launch_started_at = time.time()
        entry_timing = entry["timing"]
        assert isinstance(entry_timing, dict)
        entry_timing["launch_started_at"] = launch_started_at
        log_path = Path(str(entry["log"]))
        timing_path = Path(str(entry["timings"]))
        log = None
        temp_root = Path(str(entry["temp_root_boundary"]))
        command = _runtime_child_command(task, selected_by_lane.get(name, ()))
        child_env = _lane_environment(name, run_id=run_id, temp_root=temp_root)
        child_env["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(REPO_ROOT / "scripts"), child_env.get("PYTHONPATH", "")])
        )
        child_env["T29_PROFILE_PATH"] = str(timing_path)
        child_env["T29_DB_RECEIPT_LANE"] = name
        child_env["T29_RUN_COMMAND"] = json.dumps(command)
        child_env["T29_RUN_CWD"] = str(REPO_ROOT)
        entry["command"] = command
        entry["launch_status"] = "starting"
        _record_lifecycle(
            entry,
            "launch-start",
            parent_pid=os.getpid(),
            child_pid=None,
            pgid=None,
            temp_root=str(temp_root),
        )
        try:
            log = log_path.open("w", encoding="utf-8")
            process = subprocess.Popen(
                command,
                cwd=REPO_ROOT,
                env=child_env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
        except Exception as exc:
            entry["launch_status"] = "failed"
            entry["status"] = "launch-failed"
            entry["launch_error"] = f"{exc.__class__.__name__}: {exc}"
            entry["residue_classification"] = "absent"
            entry["cleanup_status"] = "not-needed"
            entry["cleanup_result"] = "not-launched"
            if log is not None:
                log.close()
            _record_lane_timing(entry, "launch", launch_started, launch_started_at, status="failed")
            persist(f"launch:{name}", name)
            return False
        finally:
            if log is not None:
                log.close()
        processes[name] = process
        entry["pid"] = process.pid
        process_identity = entry["process_identity"]
        assert isinstance(process_identity, dict)
        process_identity["child_pid"] = process.pid
        try:
            actual_pgid = os.getpgid(process.pid)
        except Exception as exc:
            entry["launch_status"] = "untrusted"
            entry["status"] = "launch-untrusted"
            entry["receipt_error"] = f"actual PGID unavailable: {exc}"
            entry["owned_resource_mapping"]["process_group"].update(
                {
                    "classification": "unknown",
                    "evidence": f"os.getpgid failed: {exc.__class__.__name__}: {exc}",
                }
            )
            _record_lifecycle(
                entry,
                "launch-pgid-error",
                parent_pid=os.getpid(),
                child_pid=process.pid,
                pgid=None,
                error=f"{exc.__class__.__name__}: {exc}",
            )
            _record_lane_timing(entry, "launch", launch_started, launch_started_at, status="failed")
            persist(f"launch-pgid:{name}", name)
            return False
        entry["pgid"] = actual_pgid
        process_identity["pgid"] = actual_pgid
        process_identity["verdict"] = "owned-current-run"
        entry["started_at"] = time.time()
        entry["status"] = "launched"
        entry["launch_status"] = "launched"
        process_group = entry["owned_resource_mapping"]["process_group"]
        process_group.update(
            {
                "resource_id": actual_pgid,
                "child_pid": process.pid,
                "pgid": actual_pgid,
                "classification": "owned-current-run",
                "evidence": (
                    "Popen(start_new_session=True) plus os.getpgid returned current-run group"
                ),
            }
        )
        _record_lifecycle(
            entry,
            "launch-complete",
            parent_pid=os.getpid(),
            child_pid=process.pid,
            pgid=actual_pgid,
            return_code=process.poll(),
        )
        ports_resource = entry["owned_resource_mapping"]["ports"]
        ports_resource.update(
            {
                "classification": ("owned-current-run" if LANE_PORTS[name] else "absent"),
                "evidence": (
                    "Popen(start_new_session=True) plus canonical lane port mapping"
                    if LANE_PORTS[name]
                    else "lane has no canonical server port"
                ),
            }
        )
        _record_lane_timing(entry, "launch", launch_started, launch_started_at)
        persist(f"launch:{name}", name)
        return True

    def monitor(phase: tuple[str, ...]) -> bool:
        nonlocal \
            first_failure, \
            first_failure_lane, \
            first_failure_reason, \
            stopping, \
            deadline_triggered
        while True:
            running = False
            for name in phase:
                process = processes[name]
                entry = metadata_by_lane[name]
                try:
                    return_code = process.poll()
                    _record_lifecycle(
                        entry,
                        "monitor-poll",
                        parent_pid=os.getpid(),
                        child_pid=process.pid,
                        pgid=entry.get("pgid"),
                        return_code=return_code,
                    )
                    if return_code is None:
                        running = True
                except Exception as exc:
                    if _is_lifecycle_race(exc):
                        _record_race(entry, "monitor-poll", exc)
                        if first_failure is None:
                            first_failure = 1
                            first_failure_lane = name
                            first_failure_reason = "lane disappeared during monitor poll"
                    else:
                        entry["receipt_error"] = f"monitor poll: {exc}"
                        if first_failure is None:
                            first_failure = 2
                            first_failure_lane = name
                            first_failure_reason = "monitor poll failed"
                    stopping = True
                    _stop_reason = f"lane-disappeared:{name}"
                    try:
                        _stop(processes, signal.SIGTERM, metadata_by_lane, _stop_reason)
                    except Exception as exc:
                        record_error("monitor-stop", exc, name)
                    persist("monitor-lane-disappeared", name)
                    return False
            if interrupted is not None:
                return False
            if time.monotonic() >= _stop_deadline(started):
                deadline_triggered = True
                first_failure = TIMEOUT_EXIT_CODE
                stopping = True
                for entry in metadata:
                    entry["timeout"]["deadline_triggered"] = True
                    entry["timeout"]["deadline"] = _stop_deadline(started)
                try:
                    _stop(processes, signal.SIGTERM, metadata_by_lane, "deadline")
                except Exception as exc:
                    record_error("deadline-stop", exc)
                first_failure_lane = first_failure_lane or "deadline"
                first_failure_reason = first_failure_reason or "300-second deadline"
                persist("deadline-stop")
                return False
            failed = None
            for name in phase:
                process = processes[name]
                try:
                    returncode = process.poll()
                    _record_lifecycle(
                        metadata_by_lane[name],
                        "monitor-failure-poll",
                        parent_pid=os.getpid(),
                        child_pid=process.pid,
                        pgid=metadata_by_lane[name].get("pgid"),
                        return_code=returncode,
                    )
                except Exception as exc:
                    if _is_lifecycle_race(exc):
                        _record_race(metadata_by_lane[name], "monitor-failure-poll", exc)
                        returncode = 1
                    else:
                        metadata_by_lane[name]["receipt_error"] = f"monitor poll: {exc}"
                        returncode = 2
                if returncode not in (None, 0):
                    failed = name
                    break
            if failed is not None:
                first_failure = processes[failed].returncode
                if first_failure == 0 or first_failure is None:
                    first_failure = 1
                first_failure_lane = failed
                first_failure_reason = "lane exited nonzero; fail-fast sibling stop"
                stopping = True
                try:
                    _stop(
                        processes,
                        signal.SIGTERM,
                        metadata_by_lane,
                        f"fail-fast:{failed}",
                    )
                except Exception as exc:
                    record_error("fail-fast-stop", exc, failed)
                persist("fail-fast-stop", failed)
                return False
            if not running:
                return True
            time.sleep(0.2)

    clean = True
    launch_phase_started = time.monotonic()
    launch_phase_started_at = time.time()
    try:
        launch_failed = False
        failed_lane = None
        for index, (name, task) in enumerate(LANES):
            if not launch(name, task):
                launch_failed = True
                failed_lane = name
                for remaining_name, _ in LANES[index + 1 :]:
                    remaining = metadata_by_lane[remaining_name]
                    remaining["launch_status"] = "not-attempted"
                    remaining["status"] = "not-attempted"
                    remaining["launch_error"] = f"partial launch after {name} failed"
                    remaining["cleanup_status"] = "not-needed"
                    remaining["cleanup_result"] = "not-launched"
                break
        if launch_failed:
            first_failure = 2
            first_failure_lane = failed_lane
            first_failure_reason = f"partial launch failed for {failed_lane}"
            stopping = True
            try:
                _stop(
                    processes,
                    signal.SIGTERM,
                    metadata_by_lane,
                    f"partial-launch:{failed_lane}",
                )
            except Exception as exc:
                record_error("partial-launch-stop", exc, failed_lane)
            persist("partial-launch", failed_lane)
        elif processes:
            monitor_phase_started = time.monotonic()
            monitor_phase_started_at = time.time()
            for entry in metadata:
                if entry["lane"] in processes:
                    entry_timing = entry["timing"]
                    assert isinstance(entry_timing, dict)
                    entry_timing["monitor_started_at"] = monitor_phase_started_at
            try:
                monitor(tuple(name for name, _ in LANES))
            finally:
                for entry in metadata:
                    if entry["lane"] in processes:
                        _record_lane_timing(
                            entry,
                            "monitor",
                            monitor_phase_started,
                            monitor_phase_started_at,
                        )
                _record_run_timing(
                    payload,
                    "monitor",
                    monitor_phase_started,
                    monitor_phase_started_at,
                )
                persist("phase-monitor")
        _record_run_timing(payload, "launch", launch_phase_started, launch_phase_started_at)
        persist("phase-launch")
    except Exception as exc:
        if first_failure is None:
            first_failure = 2
            first_failure_lane = first_failure_lane or "runner"
            first_failure_reason = first_failure_reason or "runner lifecycle exception"
        record_error("launch-monitor", exc)
    finally:
        cleanup_phase_started = time.monotonic()
        cleanup_phase_started_at = time.time()
        for entry in metadata:
            entry_timing = entry["timing"]
            assert isinstance(entry_timing, dict)
            entry_timing["cleanup_started_at"] = cleanup_phase_started_at
        try:
            clean = _reap(processes, metadata_by_lane, "final-cleanup")
        except Exception as exc:
            clean = False
            if first_failure is None:
                first_failure = 2
                first_failure_lane = first_failure_lane or "runner"
                first_failure_reason = first_failure_reason or "cleanup exception"
            record_error("cleanup", exc)
        for entry in metadata:
            _record_lane_timing(
                entry,
                "cleanup",
                cleanup_phase_started,
                cleanup_phase_started_at,
                status="complete" if clean else "untrusted",
            )
        _record_run_timing(
            payload,
            "cleanup",
            cleanup_phase_started,
            cleanup_phase_started_at,
            status="complete" if clean else "untrusted",
        )
        payload["clean_children"] = clean
        payload["cleanup"]["through_elapsed_seconds"] = time.monotonic() - started
        payload["cleanup"]["verdict"] = "clean" if clean else "untrusted"
        persist("cleanup")
        for sig, handler in previous.items():
            try:
                signal.signal(sig, handler)
            except Exception as exc:
                record_error("signal-restore", exc)
    finalization_phase_started = time.monotonic()
    finalization_phase_started_at = time.time()
    empty_collection = {
        "collected": 0,
        "nodes": [],
        "skipped": [],
        "node_checksum": _node_checksum(set()),
        "outcomes": {},
        "terminal_outcomes": {},
    }
    for entry in metadata:
        lane = str(entry["lane"])
        lane_finalization_started = time.monotonic()
        lane_finalization_started_at = time.time()
        entry_timing = entry["timing"]
        assert isinstance(entry_timing, dict)
        entry_timing["finalization_started_at"] = lane_finalization_started_at
        process = processes.get(lane)
        output = ""
        timing_output = ""
        collection: dict[str, object] = dict(empty_collection)
        db_targets: list[str] = []
        db_recreate_receipts: list[dict[str, object]] = []
        try:
            try:
                output = Path(str(entry["log"])).read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                entry["residue_classification"] = "unknown"
                entry["cleanup_result"] = "untrusted-receipt"
                if first_failure is None:
                    first_failure = 2
                    first_failure_lane = lane
                    first_failure_reason = "lane log read failed"
                record_error("log-read", exc, lane)
            timing_path = Path(str(entry["timings"]))
            try:
                timing_output = (
                    timing_path.read_text(encoding="utf-8", errors="replace")
                    if timing_path.exists()
                    else ""
                )
            except OSError as exc:
                entry["residue_classification"] = "unknown"
                entry["cleanup_result"] = "untrusted-receipt"
                if first_failure is None:
                    first_failure = 2
                    first_failure_lane = lane
                    first_failure_reason = "lane timing read failed"
                record_error("timing-read", exc, lane)
            collection = _collection(output, timing_output)
            entry["server_lifecycle"] = _server_events(output)
            entry["test_failures"] = _test_failures(output)
            db_recreate_receipts = _db_recreate_receipts(output)
            entry["database_disposition"]["receipts"] = db_recreate_receipts
            matching_recreate = [
                receipt
                for receipt in db_recreate_receipts
                if receipt.get("run_id") == entry.get("run_id")
                and receipt.get("lane") == lane
                and receipt.get("adopted") is False
            ]
            if matching_recreate:
                entry["database_disposition"]["receipt"] = matching_recreate[-1]
                entry["database_disposition"]["classification"] = matching_recreate[-1].get(
                    "classification", "unknown"
                )
            db_targets = [str(Path(value).resolve()) for value in DB_RE.findall(output)]
            if process is not None:
                temp_trusted = _reconcile_temp_root(entry, output)
                if not temp_trusted and first_failure is None:
                    first_failure = 2
                    first_failure_lane = lane
                    first_failure_reason = "lane pytest temp receipt invalid"
                    record_error(
                        "temp-receipt",
                        RuntimeError("pytest temp ownership untrusted"),
                        lane,
                    )
                try:
                    _validate_db_targets(lane, db_targets)
                    database_resource = entry["owned_resource_mapping"]["database"]
                    database_resource.update(
                        {
                            "resource_id": db_targets,
                            "classification": "owned-current-run",
                            "evidence": "lane emitted matching T29_DB_TARGET receipt",
                        }
                    )
                    entry["database_disposition"].update(
                        {
                            "classification": database_resource["classification"],
                            "cleanup_result": database_resource.get("cleanup_result"),
                            "adopted": False,
                        }
                    )
                    if lane in {"unit", "integration", "audit"}:
                        if not _reconcile_dynamic_db_targets(entry, db_targets):
                            raise RuntimeError("dynamic test DB ownership or cleanup untrusted")
                    elif not _reconcile_fixed_db_targets(entry, db_targets):
                        raise RuntimeError("fixed test DB ownership or cleanup untrusted")
                    entry["database_disposition"].update(
                        {
                            "classification": database_resource.get("classification"),
                            "cleanup_result": database_resource.get("cleanup_result"),
                            "adopted": False,
                        }
                    )
                    if lane == "e2e":
                        if not matching_recreate:
                            raise RuntimeError("E2E DB recreate receipt missing or adopted")
                        receipt_paths = {
                            str(Path(str(item.get("path"))).resolve())
                            for item in matching_recreate
                            if item.get("path") is not None
                        }
                        if not receipt_paths.issubset(E2E_DATABASE_PATHS):
                            raise RuntimeError("E2E DB recreate receipt targets unregistered path")
                except RuntimeError as exc:
                    entry["residue_classification"] = "unknown"
                    entry["cleanup_result"] = "untrusted-receipt"
                    database_resource = entry["owned_resource_mapping"]["database"]
                    database_resource["resource_id"] = db_targets
                    database_resource["classification"] = "unknown"
                    if first_failure is None:
                        first_failure = 2
                        first_failure_lane = lane
                        first_failure_reason = "lane DB receipt invalid"
                    record_error("db-receipt", exc, lane)
            elif entry["launch_status"] != "failed":
                entry["receipt_error"] = entry["launch_error"] or "lane was not launched"
        except Exception as exc:
            entry["residue_classification"] = "unknown"
            entry["cleanup_result"] = "untrusted-receipt"
            if first_failure is None:
                first_failure = 2
                first_failure_lane = lane
                first_failure_reason = "lane finalization failed"
            record_error("lane-finalization", exc, lane)
        finally:
            try:
                return_code = process.returncode if process is not None else None
            except Exception as exc:
                return_code = None
                record_error("return-code-read", exc, lane)
            try:
                summary = _summary(output)
            except Exception as exc:
                summary = {}
                record_error("summary-read", exc, lane)
            try:
                entry.update(
                    {
                        "exit_code": return_code,
                        "return_code": return_code,
                        "ended_at": time.time(),
                        "summary": summary,
                        "collection": collection,
                        "db_targets": db_targets,
                    }
                )
                if process is not None:
                    entry["status"] = "failed" if return_code not in (0, None) else "completed"
                    if return_code not in (0, None) and first_failure is None:
                        first_failure = return_code
                        first_failure_lane = lane
                        first_failure_reason = "lane returned nonzero"
                if entry["timeout"]["deadline_triggered"]:
                    entry["timeout"]["duration_exceeded"] = True
            except Exception as exc:
                record_error("lane-finalization-update", exc, lane)
            _record_lane_timing(
                entry,
                "finalization",
                lane_finalization_started,
                lane_finalization_started_at,
                status="complete" if entry.get("receipt_error") is None else "untrusted",
            )
            persist("lane-finalization", lane)
            print(f"[{entry['lane']}] exit={entry['exit_code']} log={entry['log']}")
    _record_run_timing(
        payload,
        "finalization",
        finalization_phase_started,
        finalization_phase_started_at,
    )
    lane_nodes = {
        name: set(entry["collection"]["nodes"])
        for name, entry in ((str(entry["lane"]), entry) for entry in metadata)
    }
    skip_nodes = set().union(*(set(entry["collection"]["skipped"]) for entry in metadata))
    reconciliation_phase_started = time.monotonic()
    reconciliation_phase_started_at = time.time()
    try:
        reconciliation = reconcile_population(manifest, lane_nodes, skip_nodes)
    except Exception as exc:
        reconciliation = {
            "ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
            "lane_receipts": {name: sorted(nodes) for name, nodes in lane_nodes.items()},
        }
        if first_failure is None:
            first_failure = 2
            first_failure_lane = "runner"
            first_failure_reason = "population reconciliation failed"
        record_error("reconciliation", exc)
    _record_run_timing(
        payload,
        "reconciliation",
        reconciliation_phase_started,
        reconciliation_phase_started_at,
        status="complete" if reconciliation.get("ok") else "untrusted",
    )
    persist("reconciliation")
    through_elapsed_seconds = time.monotonic() - started
    try:
        duration_exceeded = duration_exceeded or _duration_exceeded(through_elapsed_seconds)
    except Exception as exc:
        duration_exceeded = True
        record_error("duration-classification", exc)
    for entry in metadata:
        entry["timeout"]["duration_exceeded"] = duration_exceeded
    if duration_exceeded:
        deadline_triggered = True
    try:
        resources_clean, resource_residue = _resource_cleanup_verdict(metadata_by_lane)
    except Exception as exc:
        resources_clean, resource_residue = False, []
        if first_failure is None:
            first_failure = 2
            first_failure_lane = "runner"
            first_failure_reason = "resource reconciliation failed"
        record_error("resource-reconciliation", exc)
    cleanup_ok = (
        clean
        and resources_clean
        and all(entry["cleanup_result"] in {"owned-cleaned", "not-launched"} for entry in metadata)
    )
    if not resources_clean and first_failure is None:
        first_failure = 2
        first_failure_lane = "runner"
        first_failure_reason = "untrusted resource residue"
    try:
        result = _final_exit_code(interrupted, clean and resources_clean, first_failure, processes)
    except Exception as exc:
        result = first_failure or 2
        if first_failure is None:
            first_failure = result
            first_failure_lane = "runner"
            first_failure_reason = "final exit selection failed"
        record_error("exit-selection", exc)
    if duration_exceeded:
        result = TIMEOUT_EXIT_CODE
    elif result == 0 and not reconciliation["ok"]:
        result = 3
    if receipt_write_failed and result == 0:
        result = 2
    elapsed_seconds = time.monotonic() - started
    duration_exceeded = duration_exceeded or _duration_exceeded(elapsed_seconds)
    if duration_exceeded:
        result = TIMEOUT_EXIT_CODE
    payload.update(
        {
            "ended_at": time.time(),
            "elapsed_seconds": elapsed_seconds,
            "duration_exceeded": duration_exceeded,
            "deadline_triggered": deadline_triggered or duration_exceeded,
            "clean_children": clean,
            "reconciliation": reconciliation,
            "first_failure": first_failure,
            "first_failure_lane": first_failure_lane,
            "first_failure_reason": first_failure_reason,
            "final_exit_code": result,
        }
    )
    timing = payload.get("timing")
    if isinstance(timing, dict):
        timing.update(
            {
                "run_ended_at": payload["ended_at"],
                "through_cleanup_seconds": through_elapsed_seconds,
                "elapsed_seconds": elapsed_seconds,
                "duration_exceeded": duration_exceeded,
            }
        )
    cleanup = payload["cleanup"]
    cleanup.update(
        {
            "verdict": "clean" if cleanup_ok else "untrusted",
            "through_elapsed_seconds": through_elapsed_seconds,
            "residue": resource_residue,
        }
    )
    persist("finalization")
    if receipt_write_failed and payload["final_exit_code"] == 0:
        payload["final_exit_code"] = 2
        result = 2
        persist("finalization-retry")
    if duration_exceeded:
        print(
            "full suite duration ceiling exceeded: "
            f"{elapsed_seconds:.2f}s > {MAX_FULL_SUITE_SECONDS:.2f}s",
            file=sys.stderr,
        )
        return TIMEOUT_EXIT_CODE
    if result:
        return result
    print(f"full suite passed in {elapsed_seconds:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
